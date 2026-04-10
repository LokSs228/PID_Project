import numpy as np
from control import feedback, poles, tf

from discretization import get_discrete_state_space

RHP_STABILITY_TOL = 1e-5
UNIT_CIRCLE_TOL = 1e-6


def _is_nearly_zero(value, tol=1e-12):
    return abs(float(value)) <= tol


def build_pid_transfer_function(kp, ki, kd):
    kp = float(kp)
    ki = 0.0 if _is_nearly_zero(ki) else float(ki)
    kd = 0.0 if _is_nearly_zero(kd) else float(kd)

    if ki == 0 and kd == 0:
        return tf([kp], [1])
    if ki != 0 and kd == 0:
        return tf([kp, ki], [1, 0])
    if ki == 0 and kd != 0:
        return tf([kd, kp], [1])
    return tf([kd, kp, ki], [1, 0])


def closed_loop_poles(plant, kp, ki, kd):
    controller_tf = build_pid_transfer_function(kp, ki, kd)
    loop_tf = controller_tf * plant
    closed_loop_tf = feedback(loop_tf, 1)
    return np.asarray(poles(closed_loop_tf), dtype=complex).ravel()


def analyze_closed_loop_stability(plant, kp, ki, kd):
    pole_array = closed_loop_poles(plant, kp, ki, kd)
    pole_list = [{"re": float(np.real(pole)), "im": float(np.imag(pole))} for pole in pole_array]
    pole_list.sort(key=lambda item: (-item["re"], item["im"]))

    real_parts = [pole["re"] for pole in pole_list]
    is_stable = bool(max(real_parts) < RHP_STABILITY_TOL) if real_parts else True

    return {
        "stable": is_stable,
        "poles": pole_list,
        "pole_real_parts": real_parts,
    }


def _build_discrete_closed_loop_matrix(state_matrix, input_vector, output_vector, feedthrough, kp, ki, kd, sample_time):
    state_count = state_matrix.shape[0]
    input_column = np.asarray(input_vector, dtype=float).reshape(-1, 1)
    output_row = np.asarray(output_vector, dtype=float).reshape(1, -1)
    state_matrix = np.asarray(state_matrix, dtype=float)

    feedthrough = float(feedthrough)
    kp = float(kp)
    ki = 0.0 if _is_nearly_zero(ki) else float(ki)
    kd = 0.0 if _is_nearly_zero(kd) else float(kd)
    sample_time = float(sample_time)

    if ki == 0 and kd == 0:
        m11 = state_matrix - input_column @ (kp * output_row)
        m12 = -input_column * (kp * feedthrough)
        top_block = np.hstack([m11, m12])
        second_row = np.hstack([-kp * output_row, [[-kp * feedthrough]]])
        return np.vstack([top_block, second_row])

    if ki == 0:
        alpha = -(kp + kd / sample_time)
        beta = kd / sample_time

        m11 = state_matrix + input_column @ (alpha * output_row)
        m12 = input_column * (alpha * feedthrough)
        m13 = input_column * beta

        second_row = np.hstack([alpha * output_row, [[alpha * feedthrough]], [[beta]]])
        third_row = np.hstack([output_row, [[feedthrough]], [[0.0]]])
        return np.vstack([np.hstack([m11, m12, m13]), second_row, third_row])

    alpha = -(kp + ki * sample_time + kd / sample_time)
    beta = kd / sample_time

    m11 = state_matrix + input_column @ (alpha * output_row)
    m12 = input_column * (alpha * feedthrough)
    m13 = input_column * ki
    m14 = input_column * beta

    second_row = np.hstack([alpha * output_row, [[alpha * feedthrough]], [[ki]], [[beta]]])
    third_row = np.hstack([-sample_time * output_row, [[-sample_time * feedthrough]], [[1.0]], [[0.0]]])
    fourth_row = np.hstack([output_row, [[feedthrough]], [[0.0]], [[0.0]]])

    return np.vstack([np.hstack([m11, m12, m13, m14]), second_row, third_row, fourth_row])


def analyze_discrete_z_stability(plant, kp, ki, kd, dt):
    numerator_coeffs = np.atleast_1d(plant.num[0][0])
    denominator_coeffs = np.atleast_1d(plant.den[0][0])

    state_matrix, input_vector, output_vector, feedthrough = get_discrete_state_space(
        numerator_coeffs,
        denominator_coeffs,
        float(dt),
    )

    closed_loop_matrix = _build_discrete_closed_loop_matrix(
        state_matrix,
        input_vector,
        output_vector,
        feedthrough,
        kp,
        ki,
        kd,
        dt,
    )

    eigenvalues = np.linalg.eigvals(closed_loop_matrix)
    magnitudes = np.abs(eigenvalues)
    max_magnitude = float(np.max(magnitudes)) if magnitudes.size else 0.0
    is_stable = max_magnitude < 1.0 - UNIT_CIRCLE_TOL

    poles_z = [
        {
            "re": float(np.real(pole)),
            "im": float(np.imag(pole)),
            "abs": float(np.abs(pole)),
        }
        for pole in eigenvalues
    ]
    poles_z.sort(key=lambda item: (-item["abs"], -item["re"], item["im"]))

    return {
        "stable": bool(is_stable),
        "dt": float(dt),
        "poles_z": poles_z,
        "max_modulus": max_magnitude,
    }


def full_stability_report(plant, kp, ki, kd, dt):
    continuous_report = analyze_closed_loop_stability(plant, kp, ki, kd)
    discrete_report = analyze_discrete_z_stability(plant, kp, ki, kd, dt)

    return {
        "stable": discrete_report["stable"],
        "discrete_stable": discrete_report["stable"],
        "continuous_poles_stable": continuous_report["stable"],
        "simulation_indicates_unstable": False,
        "discrete": discrete_report,
        "continuous": {
            "stable": continuous_report["stable"],
            "poles": continuous_report["poles"],
            "pole_real_parts": continuous_report["pole_real_parts"],
        },
    }
