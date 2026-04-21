import numpy as np
from collections import OrderedDict
from threading import Lock
from control import step_response as control_step_response

FOPDT_CACHE_MAX = 256
fopdt_cache = OrderedDict()
fopdt_cache_lock = Lock()
L_ZERO_THRESHOLD_SAMPLES = 0.5
FOPDT_ULTRA_VERSION = 6


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
    """Генерирует сигнатуру (хеш) системы для ключа кэша."""
    try:
        if isinstance(system, tuple):
            return hash(str([arr.shape for arr in system if hasattr(arr, 'shape')]))
        numerator_coeffs = system.num[0][0]
        denominator_coeffs = system.den[0][0]
        return _coeff_signature(numerator_coeffs), _coeff_signature(denominator_coeffs)
    except Exception:
        return hash(str(system))


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


def get_step_response(system):
    """
    Извлекает массивы времени и выхода.
    Адаптировано для работы 'из коробки', если передать кортеж (time, output)
    Или использует control.step_response для передаточных функций.
    """
    if isinstance(system, tuple) and len(system) == 2:
        return system[0], system[1]
    
    return control_step_response(system)


def _run_rls(output_values, input_values, delay_samples):
    """
    Полноценная реализация рекурсивного метода наименьших квадратов (RLS) для ARX.
    Модель: y(t) = -a1*y(t-1) + b1*u(t-1-d) + b2*u(t-2-d)
    """
    N = len(output_values)
    if N < 3 + delay_samples:
        return None, None

    # Инициализация параметров RLS
    theta = np.zeros((3, 1))
    P = np.eye(3) * 1e6

    y = np.asarray(output_values).reshape(-1, 1)
    u = np.asarray(input_values).reshape(-1, 1)

    for t in range(2 + delay_samples, N):
        phi = np.array([
            [-y[t-1, 0]],
            [u[t-1-delay_samples, 0]],
            [u[t-2-delay_samples, 0]]
        ])
        
        # Обновление RLS
        K_gain = (P @ phi) / (1.0 + phi.T @ P @ phi)
        theta = theta + K_gain @ (y[t, 0] - phi.T @ theta)
        P = (np.eye(3) - K_gain @ phi.T) @ P

    return (float(theta[0, 0]), float(theta[1, 0]), float(theta[2, 0])), P


def _fopdt_step_response(time_values, K, T, L):
    """Генерирует step response для модели FOPDT для расчета MSE."""
    time_values = np.asarray(time_values, dtype=float)
    y = np.zeros_like(time_values)
    idx = time_values >= L
    if T > 0:
        y[idx] = K * (1.0 - np.exp(-(time_values[idx] - L) / T))
    else:
        y[idx] = K
    return y




def apro_FOPDT(system, downsample=1, max_delay_samples=300, fixed_k=None, fixed_l=None):
    downsample = int(downsample)
    if downsample < 1:
        raise ValueError("Parameter downsample must be >= 1.")

    delay_key = None if max_delay_samples is None else int(max_delay_samples)
    fixed_delay_key = None if fixed_l is None else round(float(fixed_l), 12)

    cache_key = (
        FOPDT_ULTRA_VERSION,
        _system_signature(system),
        downsample,
        delay_key,
        fixed_delay_key,
    )

    cached_result = _cache_get(cache_key)
    if cached_result is not None:
        return cached_result

    time_values, output_values = get_step_response(system)
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

    input_values = np.ones_like(output_values)

    if max_delay_samples is None:
        max_delay_samples = len(output_values) // 3

    max_delay = max(1, min(int(max_delay_samples), int(time_values[-1] / sample_step)))

    best_candidate = None

    # === RLS + ARX ===
    for delay_samples in range(max_delay + 1):
        arx_params, _ = _run_rls(output_values, input_values, delay_samples)
        if arx_params is None:
            continue

        a1, b1, b2 = map(float, arx_params)

        if -a1 <= 0 or np.isclose(1.0 + a1, 0.0):
            continue

        try:
            time_constant = -sample_step / np.log(-a1)

            gain_est = (b1 + b2) / (1.0 + a1)

            frac = (b2 / (b1 + b2)) if not np.isclose(b1 + b2, 0.0) else 0.0
            delay_time = (delay_samples + frac) * sample_step

        except Exception:
            continue

        if not (np.isfinite(time_constant) and time_constant > 0):
            continue

        if not (np.isfinite(delay_time) and delay_time >= 0):
            continue
            
        if fixed_l is not None:
            delay_time = float(fixed_l)

        model_output = _fopdt_step_response(time_values, gain_est, time_constant, delay_time)
        mse = float(np.mean((output_values - model_output) ** 2))

        candidate = (mse, gain_est, time_constant, delay_time)
        if best_candidate is None or candidate[0] < best_candidate[0]:
            best_candidate = candidate

    if best_candidate is None:
        raise ValueError("FOPDT identification did not converge.")

    _, K, T, L = best_candidate

    if L < (L_ZERO_THRESHOLD_SAMPLES * sample_step):
        L = 0.0

    result = (float(K), float(T), float(L))
    _cache_set(cache_key, result)
    return result
