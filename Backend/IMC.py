def IMC (K, T, L, alpha):
    if K <= 0 or T <= 0 or L <= 0:
        return None
    ratio = L / T
    if 0.5 <= ratio <= 2:
        base_lambda = T
    elif ratio > 2:
        base_lambda = L
    else:
        base_lambda = 0.5 * T
    lambda_ = alpha * base_lambda
# Regulátor P
    Kp_P = T / (K * (lambda_ + L))    
# Regulátor PI
    Kp_PI = T / (K * (lambda_ + L))
    Ki_PI = Kp_PI / T
# Regulátor PD
    Kp_PD = T / (K * (lambda_ + L))
    Td = (T * L) / (T + L)
    Kd_PD = Kp_PD * Td
    
# Regulátor PID
    Kp_PID = (T + 0.5 * L) / (K * (lambda_ + 0.5 * L))
    Ti = T + 0.5 * L
    Ki_PID = Kp_PID / Ti
    Td = (T * L) / (2 * T + L)
    Kd_PID = Kp_PID * Td
    pid_coeffs ={
        'P':   {'Kp': Kp_P,  'Ki': None,   'Kd': None},
        'PI':  {'Kp': Kp_PI, 'Ki': Ki_PI,  'Kd': None},
        'PD':  {'Kp': Kp_PD, 'Ki': None,   'Kd': Kd_PD},
        'PID': {'Kp': Kp_PID,'Ki': Ki_PID, 'Kd': Kd_PID},
    }

    return  pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD
