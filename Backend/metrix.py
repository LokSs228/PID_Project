import numpy as np

def metrix(t, y, w, e):
    t = np.asarray(t)
    y = np.asarray(y)
    w = np.asarray(w)
    e = np.asarray(e)
    w_final = w[-1]

    # ===== Overshoot (%) =====
    y_max = np.max(y)
    if w_final != 0:
        overshoot = max(0.0, (y_max - w_final) / abs(w_final) * 100)
    else:
        overshoot = 0.0

    # ===== Settling time (±5%) =====
    tol = 0.05 * abs(w_final)
    idx = np.where(np.abs(y - w_final) <= tol)[0]

    if len(idx) > 0:
        SettlingTime = t[idx[0]] - t[0]
    else:
        SettlingTime = None   # система не устоялась

    # ===== IAE =====
    IAE = float(np.trapezoid(np.abs(e), t))

    # ===== ITAE =====
    ITAE = float(np.trapezoid(t * np.abs(e), t))

    return overshoot, SettlingTime, IAE, ITAE