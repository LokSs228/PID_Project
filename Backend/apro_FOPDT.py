import numpy as np
from control import step_response
from scipy.optimize import least_squares


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


def _ultra_refine_fopdt(t, y, K0, T0, L0, h):
    """
    Deep nonlinear refinement of K, T, L.
    This stage is intentionally slower, but usually more accurate.
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    y_scale = max(float(np.max(np.abs(y))), 1.0)
    t_end = max(float(t[-1]), h)

    # Broad bounds (not restrictive for practical cases)
    k_span = max(20.0 * y_scale, abs(float(K0)) * 8.0 + 1.0)
    lb = np.array([-k_span, max(1e-9, h * 0.05), 0.0], dtype=float)
    ub = np.array([k_span, max(80.0 * t_end, h * 10.0), max(2.0 * t_end, h)], dtype=float)

    starts = [
        np.array([K0, T0, L0], dtype=float),
        np.array([K0 * 0.8, T0 * 0.8, L0], dtype=float),
        np.array([K0 * 1.2, T0 * 1.2, L0], dtype=float),
        np.array([K0, T0 * 0.6, max(0.0, L0 - h)], dtype=float),
        np.array([K0, T0 * 1.6, L0 + h], dtype=float),
        np.array([K0 * 0.6, T0 * 1.4, max(0.0, L0 - 2.0 * h)], dtype=float),
        np.array([K0 * 1.4, T0 * 0.7, L0 + 2.0 * h], dtype=float),
    ]

    best = None

    def residuals(params):
        K, T, L = params
        return _fopdt_step_response(t, K, T, L) - y

    for x0 in starts:
        x0 = np.clip(x0, lb, ub)
        try:
            result = least_squares(
                residuals,
                x0,
                bounds=(lb, ub),
                method="trf",
                loss="soft_l1",
                f_scale=max(1e-6, 0.005 * y_scale),
                max_nfev=25000,
                xtol=1e-11,
                ftol=1e-11,
                gtol=1e-11,
            )
        except Exception:
            continue

        if not result.success:
            continue

        K_opt, T_opt, L_opt = map(float, result.x)
        if not (np.isfinite(K_opt) and np.isfinite(T_opt) and np.isfinite(L_opt)):
            continue

        y_opt = _fopdt_step_response(t, K_opt, T_opt, L_opt)
        mse_opt = float(np.mean((y - y_opt) ** 2))

        candidate = (mse_opt, K_opt, T_opt, L_opt)
        if best is None or candidate[0] < best[0]:
            best = candidate

    return best


def apro_FOPDT(system, downsample=1, max_delay_samples=300):
    t, y = step_response(system)

    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    downsample = int(downsample)
    if downsample < 1:
        raise ValueError("downsample must be >= 1.")

    if downsample > 1:
        t = t[::downsample]
        y = y[::downsample]

    if len(t) < 6:
        raise ValueError("Not enough response points for FOPDT identification.")

    dt = np.diff(t)
    positive_dt = dt[dt > 0]

    if len(positive_dt) == 0:
        raise ValueError("Unable to infer discretization step from response time axis.")

    h = float(np.median(positive_dt))
    u = np.ones_like(y)

    if max_delay_samples is None:
        max_delay_samples = len(y) // 3

    max_n = max(1, min(int(max_delay_samples), int(t[-1] / h)))

    best = None

    for n in range(max_n + 1):
        theta, mse = _run_rls(y, u, n)
        if theta is None:
            continue

        a1, b1, b2 = float(theta[0]), float(theta[1]), float(theta[2])

        if -a1 <= 0 or np.isclose(1.0 + a1, 0.0):
            continue

        T = -h / np.log(-a1)
        if not np.isfinite(T) or T <= 0:
            continue

        K = (b1 + b2) / (1.0 + a1)
        if not np.isfinite(K):
            continue

        denom = b1 + b2
        frac = (b2 / denom) if not np.isclose(denom, 0.0) else 0.0

        L = (n + frac) * h
        if not np.isfinite(L) or L < 0:
            continue

        candidate = (mse, K, T, L)
        if best is None or candidate[0] < best[0]:
            best = candidate

    if best is None:
        raise ValueError("FOPDT identification did not converge.")

    mse_coarse, K, T, L = best

    # Ultra mode by default: always run deep nonlinear refinement.
    refined = _ultra_refine_fopdt(t, y, K, T, L, h)
    if refined is not None:
        mse_ref, K_ref, T_ref, L_ref = refined
        if mse_ref <= mse_coarse:
            K, T, L = K_ref, T_ref, L_ref

    return float(K), float(T), float(L)
