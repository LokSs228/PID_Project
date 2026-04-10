def CHR_20(process_gain, time_constant, delay_time):
    if process_gain == 0 or time_constant <= 0 or delay_time <= 0:
        return None

    p_kp = 0.7 * time_constant / (process_gain * delay_time)

    pi_kp = 0.6 * time_constant / (process_gain * delay_time)
    pi_ki = pi_kp / time_constant

    pid_kp = 0.95 * time_constant / (process_gain * delay_time)
    pid_ki = pid_kp / (1.4 * time_constant)
    pid_kd = pid_kp * (0.47 * delay_time)

    pd_kp = pid_kp
    pd_kd = pd_kp * (0.47 * delay_time)

    pid_coeffs = {
        "P": {"Kp": p_kp, "Ki": None, "Kd": None},
        "PI": {"Kp": pi_kp, "Ki": pi_ki, "Kd": None},
        "PD": {"Kp": pd_kp, "Ki": None, "Kd": pd_kd},
        "PID": {"Kp": pid_kp, "Ki": pid_ki, "Kd": pid_kd},
    }

    return pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd
