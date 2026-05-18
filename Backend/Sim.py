import numpy as np

from discretization import get_discrete_state_space

INTEGRAL_LIMIT = 1e5
CONTROL_SIGNAL_LIMIT = 1000.0


def _as_scalar(value):
    value_array = np.asarray(value, dtype=float)
    if value_array.ndim == 0:
        return float(value_array)
    return float(value_array.reshape(-1)[0])


def _build_reference_profile(time_grid, t1, t2, t3, t4, t5, t6, w1, w2):
    use_simple_profile = (
        t3 is None
        or t4 is None
        or t5 is None
        or t6 is None
        or t4 <= t3
        or t6 <= t5
    )

    if use_simple_profile:
        return np.where(time_grid < t1, w1, w2).astype(float)

    reference_grid = np.full_like(time_grid, w1, dtype=float)

    mask = (time_grid >= t1) & (time_grid < t2)
    reference_grid[mask] = w2

    mask = (time_grid >= t2) & (time_grid < t3)
    reference_grid[mask] = w1

    mask = (time_grid >= t3) & (time_grid < t4)
    reference_grid[mask] = w1 + (w2 - w1) * ((time_grid[mask] - t3) / (t4 - t3))

    mask = (time_grid >= t4) & (time_grid < t5)
    reference_grid[mask] = w2

    mask = (time_grid >= t5) & (time_grid < t6)
    reference_grid[mask] = w2 - (w2 - w1) * ((time_grid[mask] - t5) / (t6 - t5))

    return reference_grid


def _to_float_or_none(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_pid_arguments(kp_pid, ki_pid, kd_pid, params, Kp_PID, Ki_PID, Kd_PID, Params):
    if kp_pid is None:
        kp_pid = Kp_PID
    if ki_pid is None:
        ki_pid = Ki_PID
    if kd_pid is None:
        kd_pid = Kd_PID
    if params is None:
        params = Params
    if params is None:
        raise ValueError("params must be provided")

    return float(kp_pid), float(ki_pid), float(kd_pid), params


def _parse_simulation_profile(params):
    if len(params) < 9:
        raise ValueError("params must contain at least 9 values.")

    t1, t2, t3, t4, t5, t6, t7, w1, w2 = params[:9]
    disturbance_time = params[9] if len(params) > 9 else np.inf
    disturbance_value = params[10] if len(params) > 10 else 0.0

    t1 = _to_float_or_none(t1)
    t2 = _to_float_or_none(t2)
    t3 = _to_float_or_none(t3)
    t4 = _to_float_or_none(t4)
    t5 = _to_float_or_none(t5)
    t6 = _to_float_or_none(t6)
    t7 = _to_float_or_none(t7)
    w1 = _to_float_or_none(w1)
    w2 = _to_float_or_none(w2)
    disturbance_time = _to_float_or_none(disturbance_time)
    disturbance_value = _to_float_or_none(disturbance_value)

    if disturbance_time is None:
        disturbance_time = np.inf
    if disturbance_value is None:
        disturbance_value = 0.0

    if t1 is None or t2 is None or t7 is None or w1 is None or w2 is None:
        raise ValueError("Invalid time parameters: t1, t2, t7, w1, w2 must be numeric.")
    if t7 <= 0:
        raise ValueError("Invalid time parameters: t7 must be > 0.")

    return t1, t2, t3, t4, t5, t6, t7, w1, w2, disturbance_time, disturbance_value


def _resolve_sample_time(t7, dt):
    if dt is None:
        sample_time = t7 / 1500.0
    else:
        sample_time = float(dt)

    if sample_time <= 0:
        raise ValueError("Discretization step dt must be > 0.")

    return sample_time


def _build_step_window_info(time_grid, t1, t2, sample_time, reference_grid):
    step_mask = (time_grid >= t1) & (time_grid <= (t2 - sample_time))
    step_indices = np.flatnonzero(step_mask)

    has_step_window = step_indices.size > 1
    step_first_index = int(step_indices[0]) if has_step_window else -1
    step_last_index = int(step_indices[-1]) if has_step_window else -1
    final_step_reference = float(reference_grid[step_last_index]) if has_step_window else 0.0
    settling_tolerance = 0.05 * abs(final_step_reference) if has_step_window else 0.0

    return {
        "indices": step_indices,
        "has_window": has_step_window,
        "first_index": step_first_index,
        "last_index": step_last_index,
        "final_reference": final_step_reference,
        "settling_tolerance": settling_tolerance,
    }


def _finalize_step_metrics(metrics_state, step_window, time_grid, t1, output_history):
    metrics = {
        "overshoot": 0,
        "settling_time": None,
        "IAE": 0,
        "ITAE": 0,
        "settling_status": None,
    }

    if not step_window["has_window"]:
        return metrics

    first_index = step_window["first_index"]
    last_index = step_window["last_index"]
    final_reference = step_window["final_reference"]

    step_output_window = output_history[first_index : last_index + 1]
    has_non_finite = not np.all(np.isfinite(step_output_window))

    max_output = metrics_state["max_output"]
    if final_reference != 0 and np.isfinite(max_output):
        metrics["overshoot"] = max(0.0, (max_output - final_reference) / abs(final_reference) * 100.0)

    last_out_of_band_index = metrics_state["last_out_of_band_index"]
    if has_non_finite:
        metrics["settling_time"] = None
        metrics["settling_status"] = "unstable_or_not_settled"
    elif last_out_of_band_index >= 0:
        if last_out_of_band_index < last_index:
            metrics["settling_time"] = time_grid[last_out_of_band_index + 1] - t1
        else:
            metrics["settling_time"] = None
            metrics["settling_status"] = "unstable_or_not_settled"
    else:
        metrics["settling_time"] = 0.0

    metrics["IAE"] = float(metrics_state["iae"])
    metrics["ITAE"] = float(metrics_state["itae"])
    return metrics


def simulate(
    system,
    kp_pid=None,
    ki_pid=None,
    kd_pid=None,
    params=None,
    y0=0,
    dt=None,
    Kp_PID=None,
    Ki_PID=None,
    Kd_PID=None,
    Params=None,
):
    kp, ki, kd, params = _resolve_pid_arguments(
        kp_pid,
        ki_pid,
        kd_pid,
        params,
        Kp_PID,
        Ki_PID,
        Kd_PID,
        Params,
    )

    t1, t2, t3, t4, t5, t6, t7, w1, w2, disturbance_time, disturbance_value = _parse_simulation_profile(params)
    sample_time = _resolve_sample_time(t7, dt)

    time_grid = np.arange(0.0, t7 + sample_time, sample_time, dtype=float)
    reference_grid = _build_reference_profile(time_grid, t1, t2, t3, t4, t5, t6, w1, w2)

    numerator_coeffs = np.atleast_1d(system.num[0][0])
    denominator_coeffs = np.atleast_1d(system.den[0][0])
    state_matrix, input_vector, output_vector, feedthrough_scalar = get_discrete_state_space(
        numerator_coeffs,
        denominator_coeffs,
        sample_time,
    )

    sample_count = time_grid.size
    state = np.zeros(state_matrix.shape[0], dtype=float)
    output = _as_scalar(y0)
    previous_output = output
    error_integral = 0.0

    output_history = np.empty(sample_count, dtype=float)
    simulation_points = [None] * sample_count

    step_window = _build_step_window_info(time_grid, t1, t2, sample_time, reference_grid)
    metrics_state = {
        "max_output": -np.inf,
        "last_out_of_band_index": -1,
        "iae": 0.0,
        "itae": 0.0,
        "previous_abs_error": None,
        "previous_time": None,
    }

    for index in range(sample_count):
        current_time = time_grid[index]
        reference_value = reference_grid[index]
        error = reference_value - output

        error_integral = np.clip(error_integral + error * sample_time, -INTEGRAL_LIMIT, INTEGRAL_LIMIT)
        error_derivative = -(output - previous_output) / sample_time

        pid_signal = np.clip(kp * error + ki * error_integral + kd * error_derivative, -CONTROL_SIGNAL_LIMIT, CONTROL_SIGNAL_LIMIT)
        disturbance_signal = disturbance_value if current_time >= disturbance_time else 0.0
        control_signal = np.clip(pid_signal + disturbance_signal, -CONTROL_SIGNAL_LIMIT, CONTROL_SIGNAL_LIMIT)

        output_history[index] = output
        simulation_points[index] = {
            "t": round(float(current_time), 4),
            "w": float(reference_value),
            "y": float(output),
            "u": float(control_signal),
        }

        if step_window["has_window"] and step_window["first_index"] <= index <= step_window["last_index"]:
            if output > metrics_state["max_output"]:
                metrics_state["max_output"] = output

            if abs(output - step_window["final_reference"]) > step_window["settling_tolerance"]:
                metrics_state["last_out_of_band_index"] = index

            abs_error = abs(error)
            previous_abs_error = metrics_state["previous_abs_error"]
            previous_time = metrics_state["previous_time"]
            if previous_abs_error is not None:
                segment_dt = current_time - previous_time
                metrics_state["iae"] += 0.5 * (previous_abs_error + abs_error) * segment_dt
                metrics_state["itae"] += 0.5 * ((previous_time * previous_abs_error) + (current_time * abs_error)) * segment_dt

            metrics_state["previous_abs_error"] = abs_error
            metrics_state["previous_time"] = current_time

        state = state_matrix @ state + input_vector * control_signal
        previous_output = output
        output = _as_scalar(output_vector @ state + feedthrough_scalar * control_signal)

    metrics = _finalize_step_metrics(metrics_state, step_window, time_grid, t1, output_history)

    step_indices = step_window["indices"]
    step_times = time_grid[step_indices]
    step_outputs = output_history[step_indices]
    step_references = reference_grid[step_indices]

    return {
        "sim_points": simulation_points,
        "metrics": metrics,
        "step_data": {
            "t": step_times.tolist(),
            "y": step_outputs.tolist(),
            "w": step_references.tolist(),
        },
    }


def simulation_indicates_instability(sim_results):
    metrics = sim_results.get("metrics") or {}
    if metrics.get("settling_status") == "unstable_or_not_settled":
        return True

    for point in sim_results.get("sim_points") or []:
        for key in ("y", "u", "w"):
            value = point.get(key)
            if value is None or not np.isfinite(float(value)):
                return True

    return False
