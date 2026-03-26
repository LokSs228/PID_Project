import numpy as np
from control import step_response


def _infer_delay_search_limit(y, max_n):
    """
    Estimate a practical upper bound for delay search from the first
    significant output change.
    """
    y = np.asarray(y, dtype=float)
    if y.size < 3:
        return max_n

    y0 = float(y[0])
    span = float(np.max(np.abs(y - y0)))
    if not np.isfinite(span) or span <= 1e-12:
        return max_n

    threshold = max(0.01 * span, 1e-9)
    change_indices = np.flatnonzero(np.abs(y - y0) >= threshold)
    if change_indices.size == 0:
        return max_n

    first_change = int(change_indices[0])
    guard = max(3, min(40, y.size // 25))
    return max(1, min(max_n, first_change + guard))


def _is_physical_input_coeffs(b1, b2, tol=1e-12):
    """
    Physical plausibility filter for ARX input coefficients.
    For a FOPDT-like step response both coefficients should affect output
    in the same direction (same sign as their sum).
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


def apro_FOPDT(system, downsample=4, max_delay_samples=300):
    """
    Approximation of system by FOPDT model
    G(s) = K / (T*s + 1) * exp(-L*s)

    Parameters
    ----------
    downsample : int
        Decimation factor for response arrays before identification.
        1 keeps original resolution.
    max_delay_samples : int | None
        Maximum tested delay index n. If None, uses len(y)//3.
        The effective search range can be reduced automatically based on
        the first significant output change to avoid overestimated delay.
    """

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
    max_n = _infer_delay_search_limit(y, max_n)

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

        candidate = (mse, L, K, T, a1, b1, b2)

        if best is None:
            best = candidate
            continue

        best_mse = best[0]
        mse_tol = max(1e-12, 0.02 * best_mse)

        if candidate[0] < best_mse - mse_tol:
            best = candidate
        elif abs(candidate[0] - best_mse) <= mse_tol and candidate[1] < best[1]:
            best = candidate

    if best is None:
        raise ValueError("FOPDT identification did not converge.")

    _, L, K, T, _, _, _ = best

    return float(K), float(T), float(L)
