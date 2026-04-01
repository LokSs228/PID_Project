import numpy as np

from discretization import get_discrete_state_space


def _as_scalar(value):
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return float(arr)
    return float(arr.reshape(-1)[0])


def _build_reference_profile(t_values, t1, t2, t3, t4, t5, t6, w1, w2):
    use_simple_profile = (
        t3 is None
        or t4 is None
        or t5 is None
        or t6 is None
        or t4 <= t3
        or t6 <= t5
    )

    if use_simple_profile:
        return np.where(t_values < t1, w1, w2).astype(float)

    w_values = np.full_like(t_values, w1, dtype=float)

    mask = (t_values >= t1) & (t_values < t2)
    w_values[mask] = w2

    mask = (t_values >= t2) & (t_values < t3)
    w_values[mask] = w1

    mask = (t_values >= t3) & (t_values < t4)
    w_values[mask] = w1 + (w2 - w1) * ((t_values[mask] - t3) / (t4 - t3))

    mask = (t_values >= t4) & (t_values < t5)
    w_values[mask] = w2

    mask = (t_values >= t5) & (t_values < t6)
    w_values[mask] = w2 - (w2 - w1) * ((t_values[mask] - t5) / (t6 - t5))

    return w_values


def simulate(system, Kp_PID, Ki_PID, Kd_PID, Params, y0, dt=None):
    Kp, Ki, Kd = Kp_PID, Ki_PID, Kd_PID
    t1, t2, t3, t4, t5, t6, t7, w1, w2 = Params[:9]
    disturbance_time = Params[9] if len(Params) > 9 else np.inf
    disturbance_value = Params[10] if len(Params) > 10 else 0.0

    def to_float_or_none(value):
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    t1 = to_float_or_none(t1)
    t2 = to_float_or_none(t2)
    t3 = to_float_or_none(t3)
    t4 = to_float_or_none(t4)
    t5 = to_float_or_none(t5)
    t6 = to_float_or_none(t6)
    t7 = to_float_or_none(t7)
    w1 = to_float_or_none(w1)
    w2 = to_float_or_none(w2)

    if t1 is None or t2 is None or t7 is None or w1 is None or w2 is None:
        raise ValueError("Neplatné časové parametry: t1, t2, t7, w1, w2 musí být číselné.")
    if t7 <= 0:
        raise ValueError("Neplatné časové parametry: t7 musí být > 0.")

    if dt is None:
        dt = t7 / 1500.0
    else:
        dt = float(dt)
    if dt <= 0:
        raise ValueError("DiskretizaДЌnГ­ krok dt musГ­ bГЅt > 0.")
    t_values = np.arange(0.0, t7 + dt, dt, dtype=float)
    w_values = _build_reference_profile(t_values, t1, t2, t3, t4, t5, t6, w1, w2)

    num = np.atleast_1d(system.num[0][0])
    den = np.atleast_1d(system.den[0][0])
    A_d, B_vec, C_vec, D_scalar = get_discrete_state_space(num, den, dt)

    sample_count = t_values.size
    x = np.zeros(A_d.shape[0], dtype=float)
    y = _as_scalar(y0)
    y_prev = y
    integral = 0.0

    y_values = np.empty(sample_count, dtype=float)
    sim_points = [None] * sample_count

    step_mask = (t_values >= t1) & (t_values <= (t2 - dt))
    step_indices = np.flatnonzero(step_mask)

    has_step_window = step_indices.size > 1
    step_first_idx = int(step_indices[0]) if has_step_window else -1
    step_last_idx = int(step_indices[-1]) if has_step_window else -1
    w_final = float(w_values[step_last_idx]) if has_step_window else 0.0
    tol = 0.05 * abs(w_final) if has_step_window else 0.0

    y_max = -np.inf
    last_outside_idx = -1
    iae = 0.0
    itae = 0.0
    prev_abs_e = None
    prev_t = None

    for i in range(sample_count):
        t = t_values[i]
        w = w_values[i]
        e = w - y

        integral = np.clip(integral + e * dt, -1e5, 1e5)
        derivative = -(y - y_prev) / dt
        u_pid = np.clip(Kp * e + Ki * integral + Kd * derivative, -1000, 1000)
        disturbance = disturbance_value if t >= disturbance_time else 0.0
        u = np.clip(u_pid + disturbance, -1000, 1000)

        y_values[i] = y
        sim_points[i] = {
            "t": round(float(t), 4),
            "w": float(w),
            "y": float(y),
            "u": float(u),
        }

        if has_step_window and step_first_idx <= i <= step_last_idx:
            if y > y_max:
                y_max = y

            if abs(y - w_final) > tol:
                last_outside_idx = i

            abs_e = abs(e)
            if prev_abs_e is not None:
                dt_seg = t - prev_t
                iae += 0.5 * (prev_abs_e + abs_e) * dt_seg
                itae += 0.5 * ((prev_t * prev_abs_e) + (t * abs_e)) * dt_seg
            prev_abs_e = abs_e
            prev_t = t

        x = A_d @ x + B_vec * u
        y_prev = y
        y = _as_scalar(C_vec @ x + D_scalar * u)

    metrics = {"overshoot": 0, "settling_time": None, "IAE": 0, "ITAE": 0, "settling_status": None}
    if has_step_window:
        step_y_window = y_values[step_first_idx : step_last_idx + 1]
        has_nonfinite = not np.all(np.isfinite(step_y_window))

        if w_final != 0 and np.isfinite(y_max):
            metrics["overshoot"] = max(0.0, (y_max - w_final) / abs(w_final) * 100.0)

        if has_nonfinite:
            metrics["settling_time"] = None
            metrics["settling_status"] = "unstable_or_not_settled"
        elif last_outside_idx >= 0:
            if last_outside_idx < step_last_idx:
                metrics["settling_time"] = t_values[last_outside_idx + 1] - t1
            else:
                metrics["settling_time"] = None
                metrics["settling_status"] = "unstable_or_not_settled"
        else:
            metrics["settling_time"] = 0.0

        metrics["IAE"] = float(iae)
        metrics["ITAE"] = float(itae)

    step_t = t_values[step_indices]
    step_y = y_values[step_indices]
    step_w = w_values[step_indices]

    return {
        "sim_points": sim_points,
        "metrics": metrics,
        "step_data": {"t": step_t.tolist(), "y": step_y.tolist(), "w": step_w.tolist()},
    }


def simulation_indicates_instability(sim_results):
    """
    Diskretní simulace v simulate() používá jinak numericky PID než spojitý G_r(s)
    u analýzy pólů; pokud odezva diverguje / neudrží toleranci, výsledek má přednost
    před čistě spojitou LHP kontrolou.
    """
    metrics = sim_results.get("metrics") or {}
    if metrics.get("settling_status") == "unstable_or_not_settled":
        return True
    for pt in sim_results.get("sim_points") or []:
        for key in ("y", "u", "w"):
            val = pt.get(key)
            if val is None or not np.isfinite(float(val)):
                return True
    return False
