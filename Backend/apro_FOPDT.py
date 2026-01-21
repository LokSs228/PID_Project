import numpy as np
from control import step_response
def apro_FOPDT (system):
    inflection_point = None
    tangent_line = None
    t, y = step_response (system)
    #hledani K
    K = np.mean(y[-10:]) 
    #hledani L
    max_slope = -float('inf')
    inflection_index = 0
    for i in range(len(t) - 1):
        dt = t[i+1] - t[i]
        if dt == 0:
            continue
        slope = (y[i+1] - y[i]) / dt
        if slope > max_slope:
            max_slope = slope
            inflection_index = i

    t0 = float(t[inflection_index])
    y0 = float(y[inflection_index])
    inflection_point = {'t': t0, 'y': y0}
    k = max_slope
    if k <= 0:
        return None
    tangent_line = {'slope': k, 'point': inflection_point}

    A = k * (0 - t0) + y0
    L = t0 - y0 / k if k != 0 else None

    A_L_points = {
        'A': float(A),
        'L': float(L) if L is not None else None
    }
    L = t0 - y0 / k if k != 0 else None
    #hledani T
    t_K = t0 + (K - y0) / k
    T = t_K - L
    if T <= 0 or L < 0:
        return None
    return inflection_point, tangent_line, A_L_points, K, T, L  