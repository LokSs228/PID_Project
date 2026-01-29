import numpy as np
from control.matlab import lsim
from scipy.signal import cont2discrete, tf2ss

def simulate(system, Kp_PID, Ki_PID, Kd_PID, Params, y0):
    Kp = Kp_PID
    Ki = Ki_PID
    Kd = Kd_PID
    step_t=[]
    step_y=[]
    step_w=[]
    step_e=[]
    t1, t2, t3, t4, t5, t6, t7, w1, w2 = Params

    dt = t7/ 1500

    t_values = np.arange(0, t7 + dt, dt)
    w_values = np.zeros_like(t_values)

    for i, t in enumerate(t_values):
        if t < t1:
            w_values[i] = w1
        elif t < t2:
            w_values[i] = w2
        elif t < t3:
            w_values[i] = w1
        elif t < t4:
            w_values[i] = w1 + (w2 - w1) * ((t - t3) / (t4 - t3))
        elif t < t5:
            w_values[i] = w2
        elif t < t6:
            w_values[i] = w2 - (w2 - w1) * ((t - t5) / (t6 - t5))
        else:
            w_values[i] = w1

    num = np.atleast_1d(system.num[0][0])
    den = np.atleast_1d(system.den[0][0])

    A, B, C, D = tf2ss(num, den)
    sysd = cont2discrete((A, B, C, D), dt)
    A_d, B_d, C_d, D_d, _ = sysd

    # Инициализируем состояние x так, чтобы C_d @ x = y0 (при u=0)
    x = np.linalg.pinv(C_d) @ np.array([y0])

    y = float(y0)
    e_prev = 0.0
    integral = 0.0

    y_array = [y]
    u_array = [0.0]

    for i in range(1, len(t_values)):
        t = t_values[i]
        w = w_values[i]
        e = w - y
        integral += e * dt
        integral = max(min(integral, 1e5), -1e5)

        derivative = (e - e_prev) / dt
        e_prev = e

        u = Kp * e + Ki * integral + Kd * derivative
        u = max(min(u, 1000), -1000)

        x = A_d @ x + B_d.flatten() * u
        y = float(C_d @ x + D_d.flatten() * u)

        y_array.append(y)
        u_array.append(u)
        if t1 <= t <= t2:
            step_t.append(t)
            step_y.append(y)
            step_w.append(w)
            step_e.append(e)
    sim_points = [
        {
            't': round(float(t), 4),
            'w': float(w_values[i]),
            'y': float(y_array[i]),
            'u': float(u_array[i])
        }
        for i, t in enumerate(t_values)
    ]

    return {
        "sim_points": sim_points,
        "step": {
            "t": step_t,
            "y": step_y,
            "w": step_w,
            "e": step_e
        }
    }    