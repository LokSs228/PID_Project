def CHR_20 (K, T, L):
    if K <= 0 or T <= 0 or L <= 0:
        return None
    Kp_P = 0.7 * T / (K * L)

    Kp_PI = 0.7 * T / (K * L)
    Ki_PI = Kp_PI / (2.3 * L)

    Kp_PID = 1.2 * T / (K * L)
    Ki_PID = Kp_PID / (2 * L)
    Kd_PID = Kp_PID * (0.42 * L)

    Kp_PD = Kp_PID
    Kd_PD = Kp_PD * (0.42 * L)
    pid_coeffs ={
        'P':   {'Kp': Kp_P,  'Ki': None,   'Kd': None},
        'PI':  {'Kp': Kp_PI, 'Ki': Ki_PI,  'Kd': None},
        'PD':  {'Kp': Kp_PD, 'Ki': None,   'Kd': Kd_PD},
        'PID': {'Kp': Kp_PID,'Ki': Ki_PID, 'Kd': Kd_PID},
    }

    return  pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD