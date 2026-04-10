import random

import numpy as np

from discretization import get_discrete_state_space

INTEGRAL_LIMIT = 1e5
CONTROL_SIGNAL_LIMIT = 1000.0
GENE_EXPONENT_MIN = -2.0
GENE_EXPONENT_MAX = 2.0
MUTATION_STD_FACTOR = 0.2
MIN_MUTATION_SCALE = 1e-9


def _as_scalar(value):
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return float(arr)
    return float(arr.reshape(-1)[0])


def genetic_algorithm(
    system,
    params,
    y0,
    generations,
    population_size,
    mutation_rate,
    controller_type=None,
    controllerType=None,
):
    if controller_type is None:
        controller_type = controllerType if controllerType is not None else "PID"

    (
        step_change_time,
        simulation_end_time,
        _,
        _,
        _,
        _,
        sample_window,
        setpoint_before_step,
        setpoint_after_step,
    ) = params[:9]

    step_change_time = float(step_change_time)
    simulation_end_time = float(simulation_end_time)
    sample_window = float(sample_window)
    setpoint_before_step = float(setpoint_before_step)
    setpoint_after_step = float(setpoint_after_step)

    if sample_window <= 0:
        raise ValueError("Parameter t7 must be > 0.")

    sample_time = sample_window / 1500.0
    time_grid = np.arange(0.0, simulation_end_time - sample_time, sample_time, dtype=float)
    if time_grid.size < 2:
        raise ValueError("Not enough simulation samples for genetic algorithm.")

    setpoint_grid = np.where(time_grid < step_change_time, setpoint_before_step, setpoint_after_step).astype(float)

    numerator_coeffs = np.atleast_1d(system.num[0][0])
    denominator_coeffs = np.atleast_1d(system.den[0][0])

    # Estimate process gain sign from the transfer function.
    # Prefer DC gain when available, fallback to leading-coefficient ratio.
    dc_gain_denominator = float(np.polyval(denominator_coeffs, 0.0))
    if abs(dc_gain_denominator) > 1e-12:
        process_gain = float(np.polyval(numerator_coeffs, 0.0) / dc_gain_denominator)
    else:
        process_gain = float(numerator_coeffs[0] / denominator_coeffs[0])

    process_gain_sign = -1.0 if process_gain < 0.0 else 1.0
    coeff_min, coeff_max = (-100.0, 0.0) if process_gain < 0.0 else (0.0, 100.0)
    a_matrix, b_vector, c_vector, d_scalar = get_discrete_state_space(
        numerator_coeffs,
        denominator_coeffs,
        sample_time,
    )

    initial_output = _as_scalar(y0)
    output_row = c_vector.reshape(1, -1)
    output_row_pseudo_inverse = np.linalg.pinv(output_row)
    initial_state = (output_row_pseudo_inverse @ np.array([initial_output], dtype=float)).reshape(-1)

    def simulate_and_score(kp, ki, kd):
        state = initial_state.copy()
        output = initial_output
        previous_error = 0.0
        error_integral = 0.0
        weighted_absolute_error = 0.0

        for index in range(1, time_grid.size):
            setpoint = setpoint_grid[index]
            error = setpoint - output
            error_integral = np.clip(error_integral + error * sample_time, -INTEGRAL_LIMIT, INTEGRAL_LIMIT)
            error_derivative = (error - previous_error) / sample_time
            previous_error = error

            if controller_type == "P":
                control_signal = kp * error
            elif controller_type == "PI":
                control_signal = kp * error + ki * error_integral
            elif controller_type == "PD":
                control_signal = kp * error + kd * error_derivative
            else:
                control_signal = kp * error + ki * error_integral + kd * error_derivative

            control_signal = float(np.clip(control_signal, -CONTROL_SIGNAL_LIMIT, CONTROL_SIGNAL_LIMIT))
            state = a_matrix @ state + b_vector * control_signal
            output = _as_scalar(c_vector @ state + d_scalar * control_signal)

            weighted_absolute_error += time_grid[index] * abs(setpoint_grid[index] - output)

        return weighted_absolute_error

    population = []
    for _ in range(population_size):
        population.append(
            {
                "kp": process_gain_sign * (10 ** random.uniform(GENE_EXPONENT_MIN, GENE_EXPONENT_MAX)),
                "ki": process_gain_sign * (10 ** random.uniform(GENE_EXPONENT_MIN, GENE_EXPONENT_MAX)),
                "kd": process_gain_sign * (10 ** random.uniform(GENE_EXPONENT_MIN, GENE_EXPONENT_MAX)),
            }
        )

    for _ in range(generations):
        scored_population = []
        for candidate in population:
            score = simulate_and_score(candidate["kp"], candidate["ki"], candidate["kd"])
            scored_population.append((score, candidate))

        scored_population.sort(key=lambda scored_item: scored_item[0])
        next_population = [candidate for _, candidate in scored_population[:2]]

        def tournament_selection(scored_candidates, tournament_size=3):
            sampled_candidates = random.sample(scored_candidates, tournament_size)
            sampled_candidates.sort(key=lambda scored_item: scored_item[0])
            return sampled_candidates[0][1]

        while len(next_population) < population_size:
            parent_a = tournament_selection(scored_population)
            parent_b = tournament_selection(scored_population)

            alpha = random.random()
            child_candidate = {
                "kp": alpha * parent_a["kp"] + (1.0 - alpha) * parent_b["kp"],
                "ki": alpha * parent_a["ki"] + (1.0 - alpha) * parent_b["ki"],
                "kd": alpha * parent_a["kd"] + (1.0 - alpha) * parent_b["kd"],
            }

            if random.random() < mutation_rate:
                kp_scale = max(abs(child_candidate["kp"]), MIN_MUTATION_SCALE)
                ki_scale = max(abs(child_candidate["ki"]), MIN_MUTATION_SCALE)
                kd_scale = max(abs(child_candidate["kd"]), MIN_MUTATION_SCALE)
                child_candidate["kp"] += random.gauss(0.0, MUTATION_STD_FACTOR * kp_scale)
                child_candidate["ki"] += random.gauss(0.0, MUTATION_STD_FACTOR * ki_scale)
                child_candidate["kd"] += random.gauss(0.0, MUTATION_STD_FACTOR * kd_scale)

            child_candidate["kp"] = max(coeff_min, min(child_candidate["kp"], coeff_max))
            child_candidate["ki"] = max(coeff_min, min(child_candidate["ki"], coeff_max))
            child_candidate["kd"] = max(coeff_min, min(child_candidate["kd"], coeff_max))
            next_population.append(child_candidate)

        population = next_population

    best_candidate = min(
        population,
        key=lambda candidate: simulate_and_score(candidate["kp"], candidate["ki"], candidate["kd"]),
    )

    p_kp = pi_kp = pi_ki = pid_kp = pid_ki = pid_kd = pd_kp = pd_kd = 0.0

    if controller_type == "P":
        p_kp = best_candidate["kp"]
    elif controller_type == "PI":
        pi_kp = best_candidate["kp"]
        pi_ki = best_candidate["ki"]
    elif controller_type == "PD":
        pd_kp = best_candidate["kp"]
        pd_kd = best_candidate["kd"]
    else:
        pid_kp = best_candidate["kp"]
        pid_ki = best_candidate["ki"]
        pid_kd = best_candidate["kd"]

    pid_coeffs = {
        "P": {"Kp": p_kp, "Ki": None, "Kd": None},
        "PI": {"Kp": pi_kp, "Ki": pi_ki, "Kd": None},
        "PD": {"Kp": pd_kp, "Ki": None, "Kd": pd_kd},
        "PID": {"Kp": pid_kp, "Ki": pid_ki, "Kd": pid_kd},
    }
    return pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd
