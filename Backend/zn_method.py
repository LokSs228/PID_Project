# zn_method.py

from control import step_response

def zn_method(system):
    Kp_P = Kp_PI = Kp_PID = Ki_PI = Ki_PID = Kd_PID = 0.0
    pid_coeffs = []
    points = []
    inflection_point = None
    tangent_line = None
    A_L_points = None
    
    t, y = step_response(system)
    points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]

    # Поиск точки перегиба
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

    # Касательная и A, L
    k = max_slope
    tangent_line = {'slope': k, 'point': inflection_point}
    A = k * (0 - t0) + y0
    L = t0 - y0 / k if k != 0 else None

    A_L_points = {
        'A': float(A),
        'L': float(L) if L is not None else None
    }

    # PID по Ziegler-Nichols, если возможно
    abs_A = abs(A) if A else None
    abs_L = abs(L) if L else None
    if not abs_A or not abs_L:
        pid_coeffs = {
            'P':   {'Kp': None, 'Ki': None, 'Kd': None},
            'PI':  {'Kp': None, 'Ki': None, 'Kd': None},
            'PID': {'Kp': None, 'Ki': None, 'Kd': None},
        }
    else:
        Kp_P   = 1.0 / abs_A
        Kp_PI  = 0.9 / abs_A
        Kp_PID = 1.2 / abs_A
        Ki_PI = Kp_PI / (3 * abs_L)
        Ki_PID = Kp_PID / (2 * abs_L)
        Kd_PID = Kp_PID * (0.5 * abs_L)
        pid_coeffs = {
            'P':   {'Kp': Kp_P, 'Ki': None, 'Kd': None},
            'PI':  {'Kp': Kp_PI, 'Ki': Kp_PI / (3 * abs_L), 'Kd': None},
            'PID': {'Kp': Kp_PID, 'Ki': Kp_PID / (2 * abs_L), 'Kd': Kp_PID * (0.5 * abs_L)},
        }

    return points, inflection_point, tangent_line, A_L_points, pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID 
