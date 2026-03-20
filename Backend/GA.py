import numpy as np
import random
from scipy.signal import tf2ss, cont2discrete

def _as_scalar(value):
    arr = np.asarray(value)
    if arr.ndim == 0:
        return float(arr)
    return float(arr.reshape(-1)[0])

def genetic_algorithm(system, params, y0, generations, population_size, mutation_rate, controllerType):
    def simulate_and_score(Kp, Ki, Kd):
        # Načítáme pouze časové body a hodnoty setpointu
        t1, t2, t3, t4, t5, t6, t7, w1, w2 = params[:9]
        
        dt = t7 / 1500
        t_values = np.arange(0, t2 - dt, dt)
        w_values = np.zeros_like(t_values)

        for i, t in enumerate(t_values):
            if t < t1:
                w_values[i] = w1
            else:
                w_values[i] = w2

        num = np.atleast_1d(system.num[0][0])
        den = np.atleast_1d(system.den[0][0])
        A, B, C, D = tf2ss(num, den)
        sysd = cont2discrete((A, B, C, D), dt)
        A_d, B_d, C_d, D_d, _ = sysd

        x = np.linalg.pinv(C_d) @ np.array([y0])
        y = _as_scalar(y0)
        e_prev = 0.0
        integral = 0.0
        y_array = [y]

        for i in range(1, len(t_values)):
            w = w_values[i]
            e = w - y
            integral += e * dt
            # Anti-windup pro integrál
            integral = max(min(integral, 1e5), -1e5)

            derivative = (e - e_prev) / dt
            e_prev = e

            if controllerType == "P":
                u = Kp * e
            elif controllerType == "PI":
                u = Kp * e + Ki * integral
            elif controllerType == "PD":
                u = Kp * e + Kd * derivative
            else:  # PID
                u = Kp * e + Ki * integral + Kd * derivative

            # Omezení akční veličiny (bez poruchy)
            u = max(min(u, 1000), -1000)

            x = A_d @ x + B_d.flatten() * u
            y = _as_scalar(C_d @ x + D_d.flatten() * u)
            y_array.append(y)

        y_array = np.array(y_array)
        # Fitness funkce: Součet čtverců odchylek
        return np.sum(t_values *np.abs(w_values - y_array))

    # Inicializace populace
    population = []
    for _ in range(population_size):
        individual = {
            'Kp': random.uniform(0.0, 10.0),
            'Ki': random.uniform(0.0, 10.0),
            'Kd': random.uniform(0.0, 10.0),
        }
        population.append(individual)

    for generation in range(generations):
        scored_population = []
        for individual in population:
            score = simulate_and_score(individual['Kp'], individual['Ki'], individual['Kd'])
            scored_population.append((score, individual))

        # Elitismus: garantovaně zachováme 2 nejlepší jedince beze změn,
        # aby algoritmus nezapomněl povedené řešení
        scored_population.sort(key=lambda x: x[0])
        next_population = [ind for _, ind in scored_population[:2]]

        # Funkce turnajové selekce (Tournament Selection)
        def tournament_selection(scored_pop, k=3):
            # Vybereme k náhodných kandidátů a vezmeme vítěze (s nejmenší chybou)
            candidates = random.sample(scored_pop, k)
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]

        # Reprodukce a mutace
        while len(next_population) < population_size:
            # 1. Selekce
            parent1 = tournament_selection(scored_population)
            parent2 = tournament_selection(scored_population)

            # 2. Aritmetické křížení s váhovým koeficientem (BLX-crossover)
            # Na rozdíl od pevného průměru (p1+p2)/2 bereme náhodnou váhu alpha
            alpha = random.random()
            child = {
                'Kp': alpha * parent1['Kp'] + (1 - alpha) * parent2['Kp'],
                'Ki': alpha * parent1['Ki'] + (1 - alpha) * parent2['Ki'],
                'Kd': alpha * parent1['Kd'] + (1 - alpha) * parent2['Kd'],
            }

            # 3. Gaussova mutace (Gaussian Mutation) - standard pro reálné GA
            if random.random() < mutation_rate:
                # Přidáváme šum z normálního rozdělení (střední 0, směrodatná odchylka 0.5)
                # To umožňuje jemné ladění parametrů
                child['Kp'] += random.gauss(0.0, 0.5)
                child['Ki'] += random.gauss(0.0, 0.5)
                child['Kd'] += random.gauss(0.0, 0.5)

            # 4. Omezení fyzičnosti parametrů (Anti-windup pro samotné koeficienty)
            # Koeficienty nemohou být záporné a nastavujeme rozumný horní limit
            child['Kp'] = max(0.0, min(child['Kp'], 100.0))
            child['Ki'] = max(0.0, min(child['Ki'], 100.0))
            child['Kd'] = max(0.0, min(child['Kd'], 100.0))

            next_population.append(child)

        population = next_population

    # Nalezení nejlepšího jedince po ukončení cyklů
    best = min(population, key=lambda ind: simulate_and_score(ind['Kp'], ind['Ki'], ind['Kd']))
    
    Kp_P, Kp_PI, Ki_PI, Kp_PID, Ki_PID, Kd_PID, Kp_PD, Kd_PD = 0, 0, 0, 0, 0, 0, 0, 0
    
    if controllerType == "P":
        Kp_P = best['Kp']
    elif controllerType == "PI":
        Kp_PI = best['Kp']
        Ki_PI = best['Ki']
    elif controllerType == "PD":
        Kp_PD = best['Kp']
        Kd_PD = best['Kd']
    else:  
        Kp_PID = best['Kp']
        Ki_PID = best['Ki']
        Kd_PID = best['Kd']

    pid_coeffs = {
        'P':   {'Kp': Kp_P,   'Ki': None,   'Kd': None},
        'PI':  {'Kp': Kp_PI, 'Ki': Ki_PI,  'Kd': None},
        'PD':  {'Kp': Kp_PD, 'Ki': None,   'Kd': Kd_PD},
        'PID': {'Kp': Kp_PID,'Ki': Ki_PID, 'Kd': Kd_PID},
    } 
    return pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD
