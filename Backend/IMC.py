def IMC(process_gain, time_constant, delay_time, lambda_alpha):
    if process_gain == 0 or time_constant <= 0:
        return None

    delay_ratio = delay_time / time_constant
    if 0 <= delay_ratio <= 2:
        base_lambda = time_constant
    elif delay_ratio > 2:
        base_lambda = delay_time
    else:
        base_lambda = 0.5 * time_constant

    lambda_value = lambda_alpha * base_lambda

    p_kp = time_constant / (process_gain * (lambda_value + delay_time))

    pi_kp = time_constant / (process_gain * (lambda_value + delay_time))
    pi_ki = pi_kp / time_constant

    pd_kp = time_constant / (process_gain * (lambda_value + delay_time))
    derivative_time_pd = (time_constant * delay_time) / (time_constant + delay_time)
    pd_kd = pd_kp * derivative_time_pd

    pid_kp = (time_constant + 0.5 * delay_time) / (process_gain * (lambda_value + 0.5 * delay_time))
    integral_time_pid = time_constant + 0.5 * delay_time
    pid_ki = pid_kp / integral_time_pid
    derivative_time_pid = (time_constant * delay_time) / (2 * time_constant + delay_time)
    pid_kd = pid_kp * derivative_time_pid

    pid_coeffs = {
        "P": {"Kp": p_kp, "Ki": None, "Kd": None},
        "PI": {"Kp": pi_kp, "Ki": pi_ki, "Kd": None},
        "PD": {"Kp": pd_kp, "Ki": None, "Kd": pd_kd},
        "PID": {"Kp": pid_kp, "Ki": pid_ki, "Kd": pid_kd},
    }

    return pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd
