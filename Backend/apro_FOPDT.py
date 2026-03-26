import numpy as np
from collections import OrderedDict
from threading import Lock
from control import step_response
from scipy.optimize import least_squares

_FOPDT_CACHE_MAX = 256
_fopdt_cache = OrderedDict()
_fopdt_cache_lock = Lock()
_L_ZERO_THRESHOLD_SAMPLES = 0.5
_FOPDT_ULTRA_VERSION = 5


def _coeff_signature(poly, ndigits=12):
    arr = np.asarray(poly, dtype=complex).ravel()
    arr = np.real_if_close(arr, tol=1000)
    if np.iscomplexobj(arr):
        return tuple((round(float(v.real), ndigits), round(float(v.imag), ndigits)) for v in arr)
    return tuple(round(float(v), ndigits) for v in arr)


def _system_signature(system):
    # Project uses SISO transfer functions.
    num = system.num[0][0]
    den = system.den[0][0]
    return _coeff_signature(num), _coeff_signature(den)


def _cache_get(cache_key):
    with _fopdt_cache_lock:
        value = _fopdt_cache.get(cache_key)
        if value is not None:
            _fopdt_cache.move_to_end(cache_key)
        return value


def _cache_set(cache_key, value):
    with _fopdt_cache_lock:
        _fopdt_cache[cache_key] = value
        _fopdt_cache.move_to_end(cache_key)
        while len(_fopdt_cache) > _FOPDT_CACHE_MAX:
            _fopdt_cache.popitem(last=False)


def _run_rls(y, u, n, lam=1.0, delta=1e6):
    """
    RLS estimation for ARX model:
    y[k] = -a1*y[k-1] + b1*u[k-n] + b2*u[k-n-1]
    """
    theta = np.zeros(3, dtype=float)
    p_mat = np.eye(3, dtype=float) * delta
    valid_samples = 0

    for k in range(1, len(y)):
        u_kn = u[k - n] if 0 <= (k - n) < len(u) else 0.0
        u_kn1 = u[k - n - 1] if 0 <= (k - n - 1) < len(u) else 0.0

        phi = np.array([-y[k - 1], u_kn, u_kn1], dtype=float)

        denom = lam + phi @ p_mat @ phi
        if denom <= 1e-12:
            continue

        gain = (p_mat @ phi) / denom
        err = y[k] - phi @ theta

        theta = theta + gain * err
        p_mat = (p_mat - np.outer(gain, phi) @ p_mat) / lam

        valid_samples += 1

    if valid_samples < 3:
        return None, np.inf

    y_hat = np.zeros_like(y, dtype=float)

    for k in range(1, len(y)):
        u_kn = u[k - n] if 0 <= (k - n) < len(u) else 0.0
        u_kn1 = u[k - n - 1] if 0 <= (k - n - 1) < len(u) else 0.0

        y_hat[k] = -theta[0] * y[k - 1] + theta[1] * u_kn + theta[2] * u_kn1

    mse = float(np.mean((y[1:] - y_hat[1:]) ** 2))
    return theta, mse


def _fopdt_step_response(t, K, T, L):
    """Step response of FOPDT model."""
    t = np.asarray(t, dtype=float)
    tau = np.maximum(t - L, 0.0)
    y = K * (1.0 - np.exp(-tau / T))
    y[t < L] = 0.0
    return y


def _first_crossing_time(t, y, target):
    """Return first crossing time of y(t) with interpolation."""
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    if len(t) < 2:
        return None

    if target >= y[0]:
        idx = np.where(y >= target)[0]
    else:
        idx = np.where(y <= target)[0]

    if len(idx) == 0:
        return None

    i = int(idx[0])
    if i <= 0:
        return float(t[0])

    t0, t1 = float(t[i - 1]), float(t[i])
    y0, y1 = float(y[i - 1]), float(y[i])

    if np.isclose(y1, y0):
        return t1

    alpha = (target - y0) / (y1 - y0)
    alpha = float(np.clip(alpha, 0.0, 1.0))
    return t0 + alpha * (t1 - t0)


def _estimate_fixed_gain(y):
    """Estimate fixed static gain K from tail of the step response."""
    y = np.asarray(y, dtype=float)

    if len(y) == 0:
        raise ValueError("Prázdná odezva pro odhad zesílení.")

    tail_n = max(6, len(y) // 10)
    k_tail = float(np.median(y[-tail_n:]))
    if np.isfinite(k_tail) and abs(k_tail) > 1e-10:
        return k_tail

    k_last = float(y[-1])
    if np.isfinite(k_last) and abs(k_last) > 1e-10:
        return k_last

    peak_idx = int(np.argmax(np.abs(y)))
    k_peak = float(y[peak_idx])
    if np.isfinite(k_peak) and abs(k_peak) > 1e-10:
        return k_peak

    raise ValueError("Nelze odhadnout nenulové statické zesílení K.")


def _fraction_seeds(t, y, K_fixed):
    """
    Generate initial (T, L) guesses using response-level crossings.
    For FOPDT: t_f = L - T*ln(1-f).
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    if len(y) < 8:
        return []
    if not np.isfinite(K_fixed) or abs(K_fixed) < 1e-12:
        return []

    frac_pairs = [
        (0.10, 0.63),
        (0.20, 0.80),
        (0.28, 0.63),
    ]

    seeds = []
    for f1, f2 in frac_pairs:
        y1 = K_fixed * f1
        y2 = K_fixed * f2
        t1 = _first_crossing_time(t, y, y1)
        t2 = _first_crossing_time(t, y, y2)
        if t1 is None or t2 is None or not (t2 > t1):
            continue

        denom = np.log((1.0 - f1) / (1.0 - f2))
        if np.isclose(denom, 0.0):
            continue

        T_est = (t2 - t1) / denom
        L_est = t1 + T_est * np.log(1.0 - f1)

        if np.isfinite(T_est) and T_est > 0 and np.isfinite(L_est):
            seeds.append(np.array([T_est, max(0.0, L_est)], dtype=float))

    return seeds


def _refine_t_only(t, y, K_fixed, L_fixed, h):
    """Refine only T for fixed K and fixed L."""
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    t_end = max(float(t[-1]), h)
    t_after_l = t[t > (L_fixed + h)]

    starts = []
    if len(t_after_l) > 0:
        starts.append(max(h * 0.1, float(np.median(t_after_l - L_fixed))))

    t63 = _first_crossing_time(t, y, K_fixed * (1.0 - np.exp(-1.0)))
    if t63 is not None:
        starts.append(max(h * 0.1, float(t63 - L_fixed)))

    x_lin = t - L_fixed
    z_lin = 1.0 - (y / K_fixed)
    mask = (x_lin > h) & (z_lin > 1e-6) & (z_lin < 0.98)
    if np.count_nonzero(mask) >= 4:
        x_fit = x_lin[mask]
        y_fit = np.log(z_lin[mask])
        try:
            slope, _ = np.polyfit(x_fit, y_fit, 1)
            if slope < 0:
                starts.append(max(h * 0.1, float(-1.0 / slope)))
        except Exception:
            pass

    starts.extend([h * 0.5, t_end * 0.08, t_end * 0.2, t_end * 0.5, t_end * 1.2])
    starts = [float(v) for v in starts if np.isfinite(v) and v > 0]

    if not starts:
        starts = [max(h * 0.1, t_end * 0.2)]

    lb = max(1e-9, h * 0.05)
    ub = max(80.0 * t_end, h * 10.0)

    best = None

    def residuals(params):
        T = float(params[0])
        return _fopdt_step_response(t, K_fixed, T, L_fixed) - y

    seen = set()
    for t0 in starts:
        t0 = float(np.clip(t0, lb, ub))
        key = round(t0, 10)
        if key in seen:
            continue
        seen.add(key)

        try:
            result = least_squares(
                residuals,
                x0=np.array([t0], dtype=float),
                bounds=(np.array([lb], dtype=float), np.array([ub], dtype=float)),
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

        if not result.success:
            continue

        t_mid = float(result.x[0])
        try:
            result_lin = least_squares(
                residuals,
                x0=np.array([t_mid], dtype=float),
                bounds=(np.array([lb], dtype=float), np.array([ub], dtype=float)),
                method="trf",
                loss="linear",
                max_nfev=15000,
                xtol=1e-13,
                ftol=1e-13,
                gtol=1e-13,
            )
            if result_lin.success:
                t_opt = float(result_lin.x[0])
            else:
                t_opt = t_mid
        except Exception:
            t_opt = t_mid

        y_opt = _fopdt_step_response(t, K_fixed, t_opt, L_fixed)
        mse_opt = float(np.mean((y - y_opt) ** 2))

        candidate = (mse_opt, t_opt)
        if best is None or candidate[0] < best[0]:
            best = candidate

    return best


def _ultra_refine_fopdt(t, y, K_fixed, T0, L0, h):
    """
    Deep nonlinear refinement of T, L with fixed K.
    This stage is intentionally slower, but usually more accurate.
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    y_scale = max(float(np.max(np.abs(y))), 1.0)
    t_end = max(float(t[-1]), h)
    dy = np.gradient(y, t, edge_order=1)
    dy_scale = max(float(np.max(np.abs(dy))), y_scale / max(t_end, h), 1e-6)
    w_time = 0.45 + 0.55 * np.exp(-t / max(0.2 * t_end, h))

    lb = np.array([max(1e-9, h * 0.05), 0.0], dtype=float)
    ub = np.array([max(80.0 * t_end, h * 10.0), max(2.0 * t_end, h)], dtype=float)

    starts = []
    seen = set()

    def add_start(vec):
        clipped = np.clip(np.asarray(vec, dtype=float), lb, ub)
        key = tuple(round(float(v), 10) for v in clipped)
        if key in seen:
            return
        seen.add(key)
        starts.append(clipped)

    add_start([T0, L0])
    add_start([T0 * 0.8, L0])
    add_start([T0 * 1.2, L0])
    add_start([T0 * 0.6, max(0.0, L0 - h)])
    add_start([T0 * 1.6, L0 + h])
    add_start([T0 * 0.45, max(0.0, L0 - 3.0 * h)])
    add_start([T0 * 2.1, L0 + 3.0 * h])

    for seed in _fraction_seeds(t, y, K_fixed):
        add_start(seed)

    best = None

    def residuals_focus(params):
        T, L = params
        y_model = _fopdt_step_response(t, K_fixed, T, L)
        dy_model = np.gradient(y_model, t, edge_order=1)
        r_y = (y_model - y) / y_scale
        r_d = (dy_model - dy) / dy_scale
        return np.concatenate((w_time * r_y, 0.35 * w_time * r_d))

    def residuals_mse(params):
        T, L = params
        return _fopdt_step_response(t, K_fixed, T, L) - y

    for x0 in starts:
        try:
            result_focus = least_squares(
                residuals_focus,
                x0,
                bounds=(lb, ub),
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

        if not result_focus.success:
            continue

        x_mid = np.clip(np.asarray(result_focus.x, dtype=float), lb, ub)

        try:
            result_mse = least_squares(
                residuals_mse,
                x_mid,
                bounds=(lb, ub),
                method="trf",
                loss="linear",
                max_nfev=25000,
                xtol=1e-13,
                ftol=1e-13,
                gtol=1e-13,
            )
            if result_mse.success:
                x_final = np.asarray(result_mse.x, dtype=float)
            else:
                x_final = x_mid
        except Exception:
            x_final = x_mid

        T_opt, L_opt = map(float, x_final)
        if not (np.isfinite(T_opt) and np.isfinite(L_opt)):
            continue

        y_opt = _fopdt_step_response(t, K_fixed, T_opt, L_opt)
        mse_opt = float(np.mean((y - y_opt) ** 2))

        candidate = (mse_opt, T_opt, L_opt)
        if best is None or candidate[0] < best[0]:
            best = candidate

    return best


def apro_FOPDT(system, downsample=1, max_delay_samples=300, fixed_k=None, fixed_l=None):
    downsample = int(downsample)
    if downsample < 1:
        raise ValueError("Parametr downsample musí být >= 1.")

    delay_key = None if max_delay_samples is None else int(max_delay_samples)
    fixed_k_key = None if fixed_k is None else round(float(fixed_k), 12)
    fixed_l_key = None if fixed_l is None else round(float(fixed_l), 12)
    cache_key = (_FOPDT_ULTRA_VERSION, _system_signature(system), downsample, delay_key, fixed_k_key, fixed_l_key)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    t, y = step_response(system)

    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    if downsample > 1:
        t = t[::downsample]
        y = y[::downsample]

    if len(t) < 6:
        raise ValueError("Nedostatek bodů odezvy pro identifikaci FOPDT.")

    dt = np.diff(t)
    positive_dt = dt[dt > 0]

    if len(positive_dt) == 0:
        raise ValueError("Nelze určit krok diskretizace z časové osy odezvy.")

    h = float(np.median(positive_dt))
    if fixed_k is None:
        K_fixed = _estimate_fixed_gain(y)
    else:
        K_fixed = float(fixed_k)
        if not np.isfinite(K_fixed) or abs(K_fixed) < 1e-12:
            raise ValueError("fixed_k musí být konečné a nenulové číslo.")

    if fixed_l is not None:
        L_fixed = float(fixed_l)
        if not np.isfinite(L_fixed) or L_fixed < 0:
            raise ValueError("fixed_l musí být konečné číslo a >= 0.")

        best_t = _refine_t_only(t, y, K_fixed, L_fixed, h)
        if best_t is None:
            raise ValueError("Identifikace FOPDT pro fixní L nekonvergovala.")

        _, T = best_t
        result = (float(K_fixed), float(T), float(L_fixed))
        _cache_set(cache_key, result)
        return result

    u = np.ones_like(y)
    if max_delay_samples is None:
        max_delay_samples = len(y) // 3

    max_n = max(1, min(int(max_delay_samples), int(t[-1] / h)))

    best = None

    for n in range(max_n + 1):
        theta, _ = _run_rls(y, u, n)
        if theta is None:
            continue

        a1, b1, b2 = float(theta[0]), float(theta[1]), float(theta[2])

        if -a1 <= 0 or np.isclose(1.0 + a1, 0.0):
            continue

        T = -h / np.log(-a1)
        if not np.isfinite(T) or T <= 0:
            continue

        denom = b1 + b2
        frac = (b2 / denom) if not np.isclose(denom, 0.0) else 0.0

        L = (n + frac) * h
        if not np.isfinite(L) or L < 0:
            continue

        y_model = _fopdt_step_response(t, K_fixed, T, L)
        mse_model = float(np.mean((y - y_model) ** 2))
        candidate = (mse_model, T, L)
        if best is None or candidate[0] < best[0]:
            best = candidate

    if best is None:
        raise ValueError("Identifikace FOPDT nekonvergovala.")

    mse_coarse, T, L = best

    # Ultra mode by default: refine only T, L while keeping K fixed.
    refined = _ultra_refine_fopdt(t, y, K_fixed, T, L, h)
    if refined is not None:
        mse_ref, T_ref, L_ref = refined
        if mse_ref <= mse_coarse:
            T, L = T_ref, L_ref

    # Delays smaller than half of one identified sampling step are treated as zero.
    if L < (_L_ZERO_THRESHOLD_SAMPLES * h):
        L = 0.0

    result = (float(K_fixed), float(T), float(L))
    _cache_set(cache_key, result)
    return result
