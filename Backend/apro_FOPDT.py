import numpy as np
from collections import OrderedDict
from threading import Lock
from control import step_response
from scipy.optimize import least_squares

FOPDT_CACHE_MAX = 256
fopdt_cache = OrderedDict()
fopdt_cache_lock = Lock()
L_ZERO_THRESHOLD_SAMPLES = 0.5
FOPDT_ULTRA_VERSION = 5


def _coeff_signature(polynomial, ndigits=12):
    coefficient_array = np.asarray(polynomial, dtype=complex).ravel()
    coefficient_array = np.real_if_close(coefficient_array, tol=1000)

    if np.iscomplexobj(coefficient_array):
        return tuple(
            (round(float(value.real), ndigits), round(float(value.imag), ndigits))
            for value in coefficient_array
        )

    return tuple(round(float(value), ndigits) for value in coefficient_array)


def _system_signature(system):
    numerator_coeffs = system.num[0][0]
    denominator_coeffs = system.den[0][0]
    return _coeff_signature(numerator_coeffs), _coeff_signature(denominator_coeffs)


def _cache_get(cache_key):
    with fopdt_cache_lock:
        cached_value = fopdt_cache.get(cache_key)
        if cached_value is not None:
            fopdt_cache.move_to_end(cache_key)
        return cached_value


def _cache_set(cache_key, value):
    with fopdt_cache_lock:
        fopdt_cache[cache_key] = value
        fopdt_cache.move_to_end(cache_key)
        while len(fopdt_cache) > FOPDT_CACHE_MAX:
            fopdt_cache.popitem(last=False)


def _run_rls(output_values, input_values, delay_samples, forgetting_factor=1.0, covariance_scale=1e6):
    """
    RLS estimation for ARX model:
    y[k] = -a1*y[k-1] + b1*u[k-delay] + b2*u[k-delay-1]
    """
    parameter_vector = np.zeros(3, dtype=float)
    covariance_matrix = np.eye(3, dtype=float) * covariance_scale
    valid_samples = 0

    for sample_index in range(1, len(output_values)):
        input_delayed = input_values[sample_index - delay_samples] if 0 <= (sample_index - delay_samples) < len(input_values) else 0.0
        input_delayed_prev = (
            input_values[sample_index - delay_samples - 1]
            if 0 <= (sample_index - delay_samples - 1) < len(input_values)
            else 0.0
        )

        regressor = np.array([-output_values[sample_index - 1], input_delayed, input_delayed_prev], dtype=float)

        denominator = forgetting_factor + regressor @ covariance_matrix @ regressor
        if denominator <= 1e-12:
            continue

        kalman_gain = (covariance_matrix @ regressor) / denominator
        prediction_error = output_values[sample_index] - regressor @ parameter_vector

        parameter_vector = parameter_vector + kalman_gain * prediction_error
        covariance_matrix = (covariance_matrix - np.outer(kalman_gain, regressor) @ covariance_matrix) / forgetting_factor

        valid_samples += 1

    if valid_samples < 3:
        return None, np.inf

    predicted_output = np.zeros_like(output_values, dtype=float)

    for sample_index in range(1, len(output_values)):
        input_delayed = input_values[sample_index - delay_samples] if 0 <= (sample_index - delay_samples) < len(input_values) else 0.0
        input_delayed_prev = (
            input_values[sample_index - delay_samples - 1]
            if 0 <= (sample_index - delay_samples - 1) < len(input_values)
            else 0.0
        )

        predicted_output[sample_index] = (
            -parameter_vector[0] * output_values[sample_index - 1]
            + parameter_vector[1] * input_delayed
            + parameter_vector[2] * input_delayed_prev
        )

    mse_value = float(np.mean((output_values[1:] - predicted_output[1:]) ** 2))
    return parameter_vector, mse_value


def _fopdt_step_response(time_values, process_gain, time_constant, delay_time):
    time_values = np.asarray(time_values, dtype=float)
    shifted_time = np.maximum(time_values - delay_time, 0.0)
    output_values = process_gain * (1.0 - np.exp(-shifted_time / time_constant))
    output_values[time_values < delay_time] = 0.0
    return output_values


def _first_crossing_time(time_values, output_values, target_value):
    time_values = np.asarray(time_values, dtype=float)
    output_values = np.asarray(output_values, dtype=float)

    if len(time_values) < 2:
        return None

    if target_value >= output_values[0]:
        crossing_indices = np.where(output_values >= target_value)[0]
    else:
        crossing_indices = np.where(output_values <= target_value)[0]

    if len(crossing_indices) == 0:
        return None

    crossing_index = int(crossing_indices[0])
    if crossing_index <= 0:
        return float(time_values[0])

    t0, t1 = float(time_values[crossing_index - 1]), float(time_values[crossing_index])
    y0, y1 = float(output_values[crossing_index - 1]), float(output_values[crossing_index])

    if np.isclose(y1, y0):
        return t1

    interpolation_factor = (target_value - y0) / (y1 - y0)
    interpolation_factor = float(np.clip(interpolation_factor, 0.0, 1.0))
    return t0 + interpolation_factor * (t1 - t0)


def _estimate_fixed_gain(output_values):
    output_values = np.asarray(output_values, dtype=float)

    if len(output_values) == 0:
        raise ValueError("Empty response for gain estimation.")

    tail_size = max(6, len(output_values) // 10)
    tail_gain = float(np.median(output_values[-tail_size:]))
    if np.isfinite(tail_gain) and abs(tail_gain) > 1e-10:
        return tail_gain

    last_gain = float(output_values[-1])
    if np.isfinite(last_gain) and abs(last_gain) > 1e-10:
        return last_gain

    peak_index = int(np.argmax(np.abs(output_values)))
    peak_gain = float(output_values[peak_index])
    if np.isfinite(peak_gain) and abs(peak_gain) > 1e-10:
        return peak_gain

    raise ValueError("Unable to estimate non-zero static gain K.")


def _fraction_seeds(time_values, output_values, fixed_gain):
    """
    Generate initial (T, L) guesses using response-level crossings.
    For FOPDT: t_f = L - T*ln(1-f).
    """
    time_values = np.asarray(time_values, dtype=float)
    output_values = np.asarray(output_values, dtype=float)

    if len(output_values) < 8:
        return []
    if not np.isfinite(fixed_gain) or abs(fixed_gain) < 1e-12:
        return []

    fraction_pairs = [
        (0.10, 0.63),
        (0.20, 0.80),
        (0.28, 0.63),
    ]

    seed_points = []
    for first_fraction, second_fraction in fraction_pairs:
        first_target = fixed_gain * first_fraction
        second_target = fixed_gain * second_fraction

        first_time = _first_crossing_time(time_values, output_values, first_target)
        second_time = _first_crossing_time(time_values, output_values, second_target)
        if first_time is None or second_time is None or not (second_time > first_time):
            continue

        denominator = np.log((1.0 - first_fraction) / (1.0 - second_fraction))
        if np.isclose(denominator, 0.0):
            continue

        time_constant_estimate = (second_time - first_time) / denominator
        delay_estimate = first_time + time_constant_estimate * np.log(1.0 - first_fraction)

        if np.isfinite(time_constant_estimate) and time_constant_estimate > 0 and np.isfinite(delay_estimate):
            seed_points.append(np.array([time_constant_estimate, max(0.0, delay_estimate)], dtype=float))

    return seed_points


def _refine_t_only(time_values, output_values, fixed_gain, fixed_delay, sample_step):
    time_values = np.asarray(time_values, dtype=float)
    output_values = np.asarray(output_values, dtype=float)

    end_time = max(float(time_values[-1]), sample_step)
    time_after_delay = time_values[time_values > (fixed_delay + sample_step)]

    start_points = []
    if len(time_after_delay) > 0:
        start_points.append(max(sample_step * 0.1, float(np.median(time_after_delay - fixed_delay))))

    time_at_63 = _first_crossing_time(time_values, output_values, fixed_gain * (1.0 - np.exp(-1.0)))
    if time_at_63 is not None:
        start_points.append(max(sample_step * 0.1, float(time_at_63 - fixed_delay)))

    shifted_time = time_values - fixed_delay
    normalized_output = 1.0 - (output_values / fixed_gain)
    fit_mask = (shifted_time > sample_step) & (normalized_output > 1e-6) & (normalized_output < 0.98)

    if np.count_nonzero(fit_mask) >= 4:
        fit_x = shifted_time[fit_mask]
        fit_y = np.log(normalized_output[fit_mask])
        try:
            slope, _ = np.polyfit(fit_x, fit_y, 1)
            if slope < 0:
                start_points.append(max(sample_step * 0.1, float(-1.0 / slope)))
        except Exception:
            pass

    start_points.extend([sample_step * 0.5, end_time * 0.08, end_time * 0.2, end_time * 0.5, end_time * 1.2])
    start_points = [float(value) for value in start_points if np.isfinite(value) and value > 0]

    if not start_points:
        start_points = [max(sample_step * 0.1, end_time * 0.2)]

    lower_bound = max(1e-9, sample_step * 0.05)
    upper_bound = max(80.0 * end_time, sample_step * 10.0)

    best_candidate = None

    def residuals(parameters):
        time_constant = float(parameters[0])
        return _fopdt_step_response(time_values, fixed_gain, time_constant, fixed_delay) - output_values

    tried_start_points = set()
    for start_time_constant in start_points:
        start_time_constant = float(np.clip(start_time_constant, lower_bound, upper_bound))
        point_key = round(start_time_constant, 10)
        if point_key in tried_start_points:
            continue
        tried_start_points.add(point_key)

        try:
            robust_result = least_squares(
                residuals,
                x0=np.array([start_time_constant], dtype=float),
                bounds=(np.array([lower_bound], dtype=float), np.array([upper_bound], dtype=float)),
                method="trf",
                loss="soft_l1",
                f_scale=0.08,
                max_nfev=30000,
                xtol=1e-12,
                ftol=1e-12,
                gtol=1e-12,
            )
        except Exception:
            continue

        if not robust_result.success:
            continue

        mid_time_constant = float(robust_result.x[0])

        try:
            mse_result = least_squares(
                residuals,
                x0=np.array([mid_time_constant], dtype=float),
                bounds=(np.array([lower_bound], dtype=float), np.array([upper_bound], dtype=float)),
                method="trf",
                loss="linear",
                max_nfev=15000,
                xtol=1e-13,
                ftol=1e-13,
                gtol=1e-13,
            )
            optimized_time_constant = float(mse_result.x[0]) if mse_result.success else mid_time_constant
        except Exception:
            optimized_time_constant = mid_time_constant

        optimized_output = _fopdt_step_response(time_values, fixed_gain, optimized_time_constant, fixed_delay)
        mse_value = float(np.mean((output_values - optimized_output) ** 2))

        candidate = (mse_value, optimized_time_constant)
        if best_candidate is None or candidate[0] < best_candidate[0]:
            best_candidate = candidate

    return best_candidate


def _ultra_refine_fopdt(time_values, output_values, fixed_gain, initial_time_constant, initial_delay, sample_step):
    """
    Deep nonlinear refinement of T and L with fixed K.
    """
    time_values = np.asarray(time_values, dtype=float)
    output_values = np.asarray(output_values, dtype=float)

    output_scale = max(float(np.max(np.abs(output_values))), 1.0)
    end_time = max(float(time_values[-1]), sample_step)

    output_derivative = np.gradient(output_values, time_values, edge_order=1)
    derivative_scale = max(float(np.max(np.abs(output_derivative))), output_scale / max(end_time, sample_step), 1e-6)
    time_weights = 0.45 + 0.55 * np.exp(-time_values / max(0.2 * end_time, sample_step))

    lower_bounds = np.array([max(1e-9, sample_step * 0.05), 0.0], dtype=float)
    upper_bounds = np.array([max(80.0 * end_time, sample_step * 10.0), max(2.0 * end_time, sample_step)], dtype=float)

    start_points = []
    seen_points = set()

    def add_start(candidate_vector):
        clipped_vector = np.clip(np.asarray(candidate_vector, dtype=float), lower_bounds, upper_bounds)
        point_key = tuple(round(float(value), 10) for value in clipped_vector)
        if point_key in seen_points:
            return
        seen_points.add(point_key)
        start_points.append(clipped_vector)

    add_start([initial_time_constant, initial_delay])
    add_start([initial_time_constant * 0.8, initial_delay])
    add_start([initial_time_constant * 1.2, initial_delay])
    add_start([initial_time_constant * 0.6, max(0.0, initial_delay - sample_step)])
    add_start([initial_time_constant * 1.6, initial_delay + sample_step])
    add_start([initial_time_constant * 0.45, max(0.0, initial_delay - 3.0 * sample_step)])
    add_start([initial_time_constant * 2.1, initial_delay + 3.0 * sample_step])

    for seed in _fraction_seeds(time_values, output_values, fixed_gain):
        add_start(seed)

    best_candidate = None

    def focused_residuals(parameters):
        time_constant, delay_time = parameters
        model_output = _fopdt_step_response(time_values, fixed_gain, time_constant, delay_time)
        model_derivative = np.gradient(model_output, time_values, edge_order=1)

        output_residual = (model_output - output_values) / output_scale
        derivative_residual = (model_derivative - output_derivative) / derivative_scale
        return np.concatenate((time_weights * output_residual, 0.35 * time_weights * derivative_residual))

    def mse_residuals(parameters):
        time_constant, delay_time = parameters
        return _fopdt_step_response(time_values, fixed_gain, time_constant, delay_time) - output_values

    for start_vector in start_points:
        try:
            focused_result = least_squares(
                focused_residuals,
                start_vector,
                bounds=(lower_bounds, upper_bounds),
                method="trf",
                loss="soft_l1",
                f_scale=0.08,
                max_nfev=45000,
                xtol=1e-12,
                ftol=1e-12,
                gtol=1e-12,
            )
        except Exception:
            continue

        if not focused_result.success:
            continue

        mid_vector = np.clip(np.asarray(focused_result.x, dtype=float), lower_bounds, upper_bounds)

        try:
            mse_result = least_squares(
                mse_residuals,
                mid_vector,
                bounds=(lower_bounds, upper_bounds),
                method="trf",
                loss="linear",
                max_nfev=25000,
                xtol=1e-13,
                ftol=1e-13,
                gtol=1e-13,
            )
            final_vector = np.asarray(mse_result.x, dtype=float) if mse_result.success else mid_vector
        except Exception:
            final_vector = mid_vector

        optimized_time_constant, optimized_delay = map(float, final_vector)
        if not (np.isfinite(optimized_time_constant) and np.isfinite(optimized_delay)):
            continue

        optimized_output = _fopdt_step_response(time_values, fixed_gain, optimized_time_constant, optimized_delay)
        mse_value = float(np.mean((output_values - optimized_output) ** 2))

        candidate = (mse_value, optimized_time_constant, optimized_delay)
        if best_candidate is None or candidate[0] < best_candidate[0]:
            best_candidate = candidate

    return best_candidate


def apro_FOPDT(system, downsample=1, max_delay_samples=300, fixed_k=None, fixed_l=None):
    downsample = int(downsample)
    if downsample < 1:
        raise ValueError("Parameter downsample must be >= 1.")

    delay_key = None if max_delay_samples is None else int(max_delay_samples)
    fixed_gain_key = None if fixed_k is None else round(float(fixed_k), 12)
    fixed_delay_key = None if fixed_l is None else round(float(fixed_l), 12)

    cache_key = (
        FOPDT_ULTRA_VERSION,
        _system_signature(system),
        downsample,
        delay_key,
        fixed_gain_key,
        fixed_delay_key,
    )

    cached_result = _cache_get(cache_key)
    if cached_result is not None:
        return cached_result

    time_values, output_values = step_response(system)
    time_values = np.asarray(time_values, dtype=float)
    output_values = np.asarray(output_values, dtype=float)

    if downsample > 1:
        time_values = time_values[::downsample]
        output_values = output_values[::downsample]

    if len(time_values) < 6:
        raise ValueError("Not enough response samples for FOPDT identification.")

    sample_intervals = np.diff(time_values)
    positive_intervals = sample_intervals[sample_intervals > 0]

    if len(positive_intervals) == 0:
        raise ValueError("Unable to determine discretization step from response timeline.")

    sample_step = float(np.median(positive_intervals))

    if fixed_k is None:
        fixed_gain = _estimate_fixed_gain(output_values)
    else:
        fixed_gain = float(fixed_k)
        if not np.isfinite(fixed_gain) or abs(fixed_gain) < 1e-12:
            raise ValueError("fixed_k must be finite and non-zero.")

    if fixed_l is not None:
        fixed_delay = float(fixed_l)
        if not np.isfinite(fixed_delay) or fixed_delay < 0:
            raise ValueError("fixed_l must be finite and >= 0.")

        refined_time_result = _refine_t_only(time_values, output_values, fixed_gain, fixed_delay, sample_step)
        if refined_time_result is None:
            raise ValueError("FOPDT identification did not converge for fixed L.")

        _, optimized_time_constant = refined_time_result
        result = (float(fixed_gain), float(optimized_time_constant), float(fixed_delay))
        _cache_set(cache_key, result)
        return result

    input_values = np.ones_like(output_values)
    if max_delay_samples is None:
        max_delay_samples = len(output_values) // 3

    max_delay = max(1, min(int(max_delay_samples), int(time_values[-1] / sample_step)))
    best_coarse_candidate = None

    for delay_samples in range(max_delay + 1):
        arx_params, _ = _run_rls(output_values, input_values, delay_samples)
        if arx_params is None:
            continue

        a1, b1, b2 = map(float, arx_params)

        if -a1 <= 0 or np.isclose(1.0 + a1, 0.0):
            continue

        time_constant = -sample_step / np.log(-a1)
        if not np.isfinite(time_constant) or time_constant <= 0:
            continue

        denominator = b1 + b2
        fractional_delay = (b2 / denominator) if not np.isclose(denominator, 0.0) else 0.0

        delay_time = (delay_samples + fractional_delay) * sample_step
        if not np.isfinite(delay_time) or delay_time < 0:
            continue

        coarse_output = _fopdt_step_response(time_values, fixed_gain, time_constant, delay_time)
        coarse_mse = float(np.mean((output_values - coarse_output) ** 2))

        candidate = (coarse_mse, time_constant, delay_time)
        if best_coarse_candidate is None or candidate[0] < best_coarse_candidate[0]:
            best_coarse_candidate = candidate

    if best_coarse_candidate is None:
        raise ValueError("FOPDT identification did not converge.")

    coarse_mse, coarse_time_constant, coarse_delay = best_coarse_candidate

    refined_candidate = _ultra_refine_fopdt(
        time_values,
        output_values,
        fixed_gain,
        coarse_time_constant,
        coarse_delay,
        sample_step,
    )

    if refined_candidate is not None:
        refined_mse, refined_time_constant, refined_delay = refined_candidate
        if refined_mse <= coarse_mse:
            coarse_time_constant, coarse_delay = refined_time_constant, refined_delay

    if coarse_delay < (L_ZERO_THRESHOLD_SAMPLES * sample_step):
        coarse_delay = 0.0

    result = (float(fixed_gain), float(coarse_time_constant), float(coarse_delay))
    _cache_set(cache_key, result)
    return result
