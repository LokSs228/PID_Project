import numpy as np
from control import step_response


def _is_physical_input_coeffs(b1, b2, tol=1e-12):
    """
    Plausibility filter for ARX input coefficients.
    Both coefficients must act in the same direction as their sum.
    """
    denom = b1 + b2
    if not np.isfinite(denom) or abs(denom) <= tol:
        return False

    if b1 * denom < -tol:
        return False
    if b2 * denom < -tol:
        return False

    return True


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


def apro_FOPDT(system, downsample=2, max_delay_samples=300, delay_weight=0.03):
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
    response_horizon = max(float(t[-1]), h)
    y_span = max(float(np.max(np.abs(y - y[0]))), 1e-12)
    mse_scale = y_span * y_span

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

        if not _is_physical_input_coeffs(b1, b2):
            continue

        denom = b1 + b2

        frac = (b2 / denom) if not np.isclose(denom, 0.0) else 0.0
        frac = float(np.clip(frac, 0.0, 1.0))

        L = (n + frac) * h

        if not np.isfinite(L) or L < 0:
            continue

        # Soft regularization: do not penalize realistic delays,
        # penalize only excessively large delays relative to horizon.
        delay_ratio = L / response_horizon
        excess_delay = max(0.0, delay_ratio - 0.15)
        score = (mse / mse_scale) + float(delay_weight) * excess_delay
        candidate = (score, mse, L, K, T, a1, b1, b2)

        if best is None:
            best = candidate
            continue

        if candidate[0] < best[0]:
            best = candidate
            continue

        best_mse = best[1]
        mse_tol = max(1e-12, 0.05 * best_mse)
        if abs(candidate[1] - best_mse) <= mse_tol and candidate[2] < best[2]:
            best = candidate

    if best is None:
        raise ValueError("FOPDT identification did not converge.")

    _, _, L, K, T, _, _, _ = best

    return float(K), float(T), float(L)
