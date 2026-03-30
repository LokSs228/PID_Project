import random

import numpy as np

from discretization import get_discrete_state_space


def _as_scalar(value):
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return float(arr)
    return float(arr.reshape(-1)[0])


def genetic_algorithm(system, params, y0, generations, population_size, mutation_rate, controllerType):
    t1, t2, _, _, _, _, t7, w1, w2 = params[:9]
    t1 = float(t1)
    t2 = float(t2)
    t7 = float(t7)
    w1 = float(w1)
    w2 = float(w2)

    if t7 <= 0:
        raise ValueError("Parametr t7 musí být > 0.")

    dt = t7 / 1500.0
    t_values = np.arange(0.0, t2 - dt, dt, dtype=float)
    if t_values.size < 2:
        raise ValueError("Nedostatek simulačních vzorků pro genetický algoritmus.")

    w_values = np.where(t_values < t1, w1, w2).astype(float)

    num = np.atleast_1d(system.num[0][0])
    den = np.atleast_1d(system.den[0][0])

    # Estimate process gain sign from the transfer function.
    # Prefer DC gain when available, fallback to leading-coefficient ratio.
    dc_den = float(np.polyval(den, 0.0))
    if abs(dc_den) > 1e-12:
        system_gain = float(np.polyval(num, 0.0) / dc_den)
    else:
        system_gain = float(num[0] / den[0])

    init_low, init_high = (0.0, -10.0) if system_gain < 0.0 else (0.0, 10.0)
    coeff_min, coeff_max = (-100.0, 0.0) if system_gain < 0.0 else (0.0, 100.0)
    A_d, B_vec, C_vec, D_scalar = get_discrete_state_space(num, den, dt)

    y0_scalar = _as_scalar(y0)
    c_row = C_vec.reshape(1, -1)
    pinv_c = np.linalg.pinv(c_row)
    x0 = (pinv_c @ np.array([y0_scalar], dtype=float)).reshape(-1)

    def simulate_and_score(Kp, Ki, Kd):
        x = x0.copy()
        y = y0_scalar
        e_prev = 0.0
        integral = 0.0
        score = 0.0

        for i in range(1, t_values.size):
            w = w_values[i]
            e = w - y
            integral = np.clip(integral + e * dt, -1e5, 1e5)
            derivative = (e - e_prev) / dt
            e_prev = e

            if controllerType == "P":
                u = Kp * e
            elif controllerType == "PI":
                u = Kp * e + Ki * integral
            elif controllerType == "PD":
                u = Kp * e + Kd * derivative
            else:
                u = Kp * e + Ki * integral + Kd * derivative

            u = float(np.clip(u, -1000, 1000))
            x = A_d @ x + B_vec * u
            y = _as_scalar(C_vec @ x + D_scalar * u)

            score += t_values[i] * abs(w_values[i] - y)

        return score

    population = []
    for _ in range(population_size):
        population.append(
            {
                "Kp": random.uniform(init_low, init_high),
                "Ki": random.uniform(init_low, init_high),
                "Kd": random.uniform(init_low, init_high),
            }
        )

    for _ in range(generations):
        scored_population = []
        for individual in population:
            score = simulate_and_score(individual["Kp"], individual["Ki"], individual["Kd"])
            scored_population.append((score, individual))

        scored_population.sort(key=lambda x: x[0])
        next_population = [ind for _, ind in scored_population[:2]]

        def tournament_selection(scored_pop, k=3):
            candidates = random.sample(scored_pop, k)
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]

        while len(next_population) < population_size:
            parent1 = tournament_selection(scored_population)
            parent2 = tournament_selection(scored_population)

            alpha = random.random()
            child = {
                "Kp": alpha * parent1["Kp"] + (1.0 - alpha) * parent2["Kp"],
                "Ki": alpha * parent1["Ki"] + (1.0 - alpha) * parent2["Ki"],
                "Kd": alpha * parent1["Kd"] + (1.0 - alpha) * parent2["Kd"],
            }

            if random.random() < mutation_rate:
                child["Kp"] += random.gauss(0.0, 0.2 * abs(child["Kp"]))
                child["Ki"] += random.gauss(0.0, 0.2 * abs(child["Ki"]))
                child["Kd"] += random.gauss(0.0, 0.2 * abs(child["Kd"]))

            child["Kp"] = max(coeff_min, min(child["Kp"], coeff_max))
            child["Ki"] = max(coeff_min, min(child["Ki"], coeff_max))
            child["Kd"] = max(coeff_min, min(child["Kd"], coeff_max))
            next_population.append(child)

        population = next_population

    best = min(population, key=lambda ind: simulate_and_score(ind["Kp"], ind["Ki"], ind["Kd"]))

    Kp_P, Kp_PI, Ki_PI, Kp_PID, Ki_PID, Kd_PID, Kp_PD, Kd_PD = 0, 0, 0, 0, 0, 0, 0, 0

    if controllerType == "P":
        Kp_P = best["Kp"]
    elif controllerType == "PI":
        Kp_PI = best["Kp"]
        Ki_PI = best["Ki"]
    elif controllerType == "PD":
        Kp_PD = best["Kp"]
        Kd_PD = best["Kd"]
    else:
        Kp_PID = best["Kp"]
        Ki_PID = best["Ki"]
        Kd_PID = best["Kd"]

    pid_coeffs = {
        "P": {"Kp": Kp_P, "Ki": None, "Kd": None},
        "PI": {"Kp": Kp_PI, "Ki": Ki_PI, "Kd": None},
        "PD": {"Kp": Kp_PD, "Ki": None, "Kd": Kd_PD},
        "PID": {"Kp": Kp_PID, "Ki": Ki_PID, "Kd": Kd_PID},
    }
    return pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD
