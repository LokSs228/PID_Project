import numpy as np
from scipy.signal import cont2discrete, tf2ss

def simulate (system, Kp_PID, Ki_PID, Kd_PID, Params, y0):
    Kp, Ki, Kd = Kp_PID, Ki_PID, Kd_PID
    t1, t2, t3, t4, t5, t6, t7, w1, w2 = Params

    dt = t7 / 1500
    t_values = np.arange(0, t7 + dt, dt)
    w_values = np.zeros_like(t_values)

    # 1. Формирование входного сигнала (задания)
    for i, t in enumerate(t_values):
        if t < t1: w_values[i] = w1
        elif t < t2: w_values[i] = w2
        elif t < t3: w_values[i] = w1
        elif t < t4: w_values[i] = w1 + (w2 - w1) * ((t - t3) / (t4 - t3))
        elif t < t5: w_values[i] = w2
        elif t < t6: w_values[i] = w2 - (w2 - w1) * ((t - t5) / (t6 - t5))
        else: w_values[i] = w1

    # 2. Подготовка модели системы
    num = np.atleast_1d(system.num[0][0])
    den = np.atleast_1d(system.den[0][0])
    A, B, C, D = tf2ss(num, den)
    A_d, B_d, C_d, D_d, _ = cont2discrete((A, B, C, D), dt)

    n = A_d.shape[0]
    x = np.zeros((n, 1))
    y = float(y0)
    y_prev = y
    integral = 0.0

    sim_points = []
    step_t, step_y, step_w, step_e = [], [], [], []

    # 3. Основной цикл симуляции
    for i in range(len(t_values)):
        t, w = t_values[i], w_values[i]
        e = w - y

        # PID логика
        integral = np.clip(integral + e * dt, -1e5, 1e5)
        derivative = -(y - y_prev) / dt
        u = np.clip(Kp * e + Ki * integral + Kd * derivative, -1000, 1000)

        # Сохранение данных
        sim_points.append({'t': round(float(t), 4), 'w': float(w), 'y': float(y), 'u': float(u)})

        # Выделение участка для расчета метрик (переход процесса t1 -> t2)
        if t1 <= t <= (t2-dt):
            step_t.append(t); step_y.append(y); step_w.append(w); step_e.append(e)

        # Шаг системы
        x = A_d @ x + B_d * u
        y_prev = y
        y = float(C_d @ x + D_d * u)

    # 4. Расчет метрик (внутренний блок metrix)
    metrics = {"overshoot": 0, "settling_time": 0, "IAE": 0, "ITAE": 0}
    
    if len(step_t) > 1:
        st_t, st_y, st_w, st_e = map(np.asarray, [step_t, step_y, step_w, step_e])
        w_final = st_w[-1]

        # Overshoot
        y_max = np.max(st_y)
        if w_final != 0:
            metrics["overshoot"] = max(0.0, (y_max - w_final) / abs(w_final) * 100)

        # Settling time (±5%)
        tol = 0.05 * abs(w_final)
        outside_indices = np.where(np.abs(st_y - w_final) > tol)[0]
        if len(outside_indices) > 0:
            last_idx = outside_indices[-1]
            metrics["settling_time"] = st_t[last_idx + 1]- t1 if last_idx < len(st_t) - 1 else st_t[-1]

        # Интегральные критерии
        metrics["IAE"] = float(np.trapezoid(np.abs(st_e), st_t))
        metrics["ITAE"] = float(np.trapezoid(st_t * np.abs(st_e), st_t))

    return {
        "sim_points": sim_points,
        "metrics": metrics,
        "step_data": {"t": step_t, "y": step_y, "w": step_w}
    }