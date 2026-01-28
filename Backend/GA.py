import numpy as np
import random
from scipy.signal import tf2ss, cont2discrete

def genetic_algorithm(system, params, y0, generations, population_size, mutation_rate, controllerType):
    def simulate_and_score(Kp, Ki, Kd):
        t1, t2, t3, t4, t5, t6, t7, w1, w2 = params
        dt = t7 / 1500
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

        x = np.linalg.pinv(C_d) @ np.array([y0])
        y = float(y0)
        e_prev = 0.0
        integral = 0.0
        y_array = [y]

        for i in range(1, len(t_values)):
            w = w_values[i]
            e = w - y
            integral += e * dt
            integral = max(min(integral, 1e5), -1e5)

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

            u = max(min(u, 1000), -1000)

            x = A_d @ x + B_d.flatten() * u
            y = float(C_d @ x + D_d.flatten() * u)
            y_array.append(y)

        y_array = np.array(y_array)
        return np.sum((w_values - y_array)**2)

    
    population = []
    for _ in range(population_size):
        individual = {
            'Kp': random.uniform(0.0, 5.0),
            'Ki': random.uniform(0.0, 5.0),
            'Kd': random.uniform(0.0, 5.0),
        }
        population.append(individual)

    for generation in range(generations):
        scored_population = []
        for individual in population:
            score = simulate_and_score(individual['Kp'], individual['Ki'], individual['Kd'])
            scored_population.append((score, individual))

        scored_population.sort(key=lambda x: x[0])
        population = [ind for _, ind in scored_population[:population_size // 2]]

        while len(population) < population_size:
            parent1, parent2 = random.sample(population[:10], 2)
            child = {
                'Kp': (parent1['Kp'] + parent2['Kp']) / 2,
                'Ki': (parent1['Ki'] + parent2['Ki']) / 2,
                'Kd': (parent1['Kd'] + parent2['Kd']) / 2,
            }

            if random.random() < mutation_rate:
                child['Kp'] += random.uniform(-0.5, 0.5)
                child['Ki'] += random.uniform(-0.5, 0.5)
                child['Kd'] += random.uniform(-0.5, 0.5)

            child['Kp'] = max(0, child['Kp'])
            child['Ki'] = max(0, child['Ki'])
            child['Kd'] = max(0, child['Kd'])

            population.append(child)

    best = min(population, key=lambda ind: simulate_and_score(ind['Kp'], ind['Ki'], ind['Kd']))

    if controllerType == "P":
        return best['Kp'], 0.0, 0.0
    elif controllerType == "PI":
        return best['Kp'], best['Ki'], 0.0
    elif controllerType == "PD":
        return best['Kp'], 0.0, best['Kd']
    else:  # PID
        return best['Kp'], best['Ki'], best['Kd']

