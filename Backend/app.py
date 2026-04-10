import os

import numpy as np
from control import pade, poles, step_response, tf
from flask import Flask, jsonify, request

from apro_FOPDT import apro_FOPDT
from CHR_0_POZ_H import CHR_0 as CHR_0_POZ_H
from CHR_0_POT_P import CHR_0_POT_P
from CHR_20_POZ_H import CHR_20 as CHR_20_POZ_H
from CHR_20_POT_P import CHR_20_POT_P
from GA import genetic_algorithm
from IMC import IMC
from Sim import simulate, simulation_indicates_instability
from stability import full_stability_report
from zn_method import zn_method

app = Flask(__name__)

TAU_EPS = 1e-9
SAMPLES_PER_TAU = 30.0
PLOT_POINT_STRIDE = 30


def normalize_origin(origin):
    if origin is None:
        return None
    normalized_origin = origin.strip()
    if normalized_origin == "*":
        return "*"
    return normalized_origin.rstrip("/")


def parse_allowed_origins():
    raw_value = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    return [normalize_origin(origin) for origin in raw_value.split(",") if origin.strip()]


ALLOWED_ORIGINS = parse_allowed_origins()


def resolve_cors_origin(request_origin):
    normalized_request_origin = normalize_origin(request_origin)
    if "*" in ALLOWED_ORIGINS:
        return "*"
    if normalized_request_origin and normalized_request_origin in ALLOWED_ORIGINS:
        return normalized_request_origin
    if ALLOWED_ORIGINS:
        return ALLOWED_ORIGINS[0]
    return "http://localhost:3000"


@app.after_request
def add_cors_headers(response):
    allowed_origin = resolve_cors_origin(request.headers.get("Origin"))
    response.headers["Access-Control-Allow-Origin"] = allowed_origin
    if allowed_origin != "*":
        response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


def select_pid_coefficients(
    controller_type,
    p_kp,
    pi_kp,
    pid_kp,
    pi_ki,
    pid_ki,
    pid_kd,
    pd_kp,
    pd_kd,
):
    if controller_type == "P":
        return p_kp, 0, 0
    if controller_type == "PI":
        return pi_kp, pi_ki, 0
    if controller_type == "PD":
        return pd_kp, 0, pd_kd
    return pid_kp, pid_ki, pid_kd


def parse_complex(value, field_name):
    if value is None:
        return None

    if isinstance(value, (int, float, complex)):
        return complex(value)

    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        normalized_text = text.replace("i", "j").replace("I", "j").replace("J", "j").replace(" ", "")
        try:
            return complex(normalized_text)
        except ValueError as exc:
            raise ValueError(f'Invalid complex value for {field_name}: "{value}"') from exc

    raise ValueError(f"Invalid data type for {field_name}")


def parse_real(value, field_name, tol=1e-9):
    complex_value = parse_complex(value, field_name)
    if complex_value is None:
        return None
    if abs(complex_value.imag) <= tol:
        return float(complex_value.real)
    raise ValueError(f"{field_name} must be a real number")


def parse_complex_list(values, field_name):
    if values is None:
        return []

    parsed_values = []
    for index, value in enumerate(values):
        parsed_value = parse_complex(value, f"{field_name}[{index}]")
        if parsed_value is not None:
            parsed_values.append(parsed_value)

    return parsed_values


def to_real_array_if_close(values, field_name, tol=1e-9):
    complex_array = np.asarray(values, dtype=complex)
    if np.any(np.abs(complex_array.imag) > tol):
        raise ValueError(
            f"{field_name} contains non-real coefficients. Use complex-conjugate pairs so the final polynomial is real."
        )
    return np.asarray(complex_array.real, dtype=float)


def parse_nonneg_int(value, field_name):
    if value is None or value == "":
        return 0

    try:
        int_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a non-negative integer") from exc

    if int_value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")

    return int_value


def estimate_tau_min(denominator_time_constants, base_system):
    tau_candidates = []

    for time_constant in denominator_time_constants:
        complex_value = complex(time_constant)
        if abs(complex_value.imag) <= TAU_EPS and float(complex_value.real) > TAU_EPS:
            tau_candidates.append(float(complex_value.real))

    if not tau_candidates:
        try:
            pole_array = np.asarray(poles(base_system), dtype=complex).ravel()
            for pole_value in pole_array:
                real_part_abs = abs(float(np.real(pole_value)))
                if real_part_abs > TAU_EPS:
                    tau_candidates.append(1.0 / real_part_abs)
        except Exception:
            pass

    if not tau_candidates:
        return 1.0

    return float(min(tau_candidates))


def choose_dt_and_steps(simulation_horizon, tau_min, samples_per_tau=SAMPLES_PER_TAU):
    simulation_horizon = float(simulation_horizon)
    tau_min = float(tau_min)

    if simulation_horizon <= 0:
        raise ValueError("t7 must be > 0.")

    if tau_min <= TAU_EPS or not np.isfinite(tau_min):
        target_dt = simulation_horizon / 1500.0
    else:
        target_dt = tau_min / float(samples_per_tau)

    if target_dt <= 0 or not np.isfinite(target_dt):
        target_dt = simulation_horizon / 1500.0

    simulation_steps = max(2, int(np.ceil(simulation_horizon / target_dt)))
    simulation_dt = simulation_horizon / float(simulation_steps)
    return float(simulation_dt), int(simulation_steps)


def downsample_sim_points_for_plot(points, stride=PLOT_POINT_STRIDE):
    if not points:
        return []

    point_list = list(points)
    stride = int(stride)
    if stride <= 1:
        return point_list

    sampled_points = [point_list[index] for index in range(0, len(point_list), stride)]
    if (len(point_list) - 1) % stride != 0:
        sampled_points.append(point_list[-1])

    return sampled_points


@app.route("/calculate", methods=["POST", "OPTIONS"])
def calculate():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.json or {}

    process_gain_raw = payload.get("K")
    numerator_time_constants_raw = payload.get("T_num", [])
    denominator_time_constants_raw = payload.get("T_den", [])
    delay_time_raw = payload.get("L", 0)
    derivative_order_raw = payload.get("diffOrder", 0)
    integrator_order_raw = payload.get("intOrder", 0)

    tuning_method = payload.get("Method")
    time_params = payload.get("timeParams", [])
    initial_output = payload.get("y0", 0)

    ga_generations = payload.get("generations")
    ga_population_size = payload.get("population_size")
    ga_mutation_rate = payload.get("mutation_rate")
    controller_type = payload.get("controllerType", "PID")

    lambda_alpha_raw = payload.get("lambdaAlpha", 2)
    try:
        lambda_alpha = float(lambda_alpha_raw)
    except (TypeError, ValueError):
        lambda_alpha = 2.0

    if len(time_params) < 11:
        return jsonify({"error": "Not enough timeParams values."}), 400

    if process_gain_raw is None or not denominator_time_constants_raw:
        return jsonify({"error": "Missing required inputs K or T_den."}), 400

    try:
        process_gain = parse_real(process_gain_raw, "K")
        denominator_time_constants = parse_complex_list(denominator_time_constants_raw, "T_den")
        numerator_time_constants = parse_complex_list(numerator_time_constants_raw, "T_num")
        delay_time = parse_real(delay_time_raw, "L")
        derivative_order = parse_nonneg_int(derivative_order_raw, "diffOrder")
        integrator_order = parse_nonneg_int(integrator_order_raw, "intOrder")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    model_order = len(denominator_time_constants)

    numerator_poly = [1]
    for time_constant in numerator_time_constants:
        numerator_poly = np.polymul(numerator_poly, [time_constant, 1])

    denominator_poly = [1]
    for time_constant in denominator_time_constants:
        denominator_poly = np.polymul(denominator_poly, [time_constant, 1])

    try:
        numerator_poly = to_real_array_if_close(numerator_poly, "Numerator")
        denominator_poly = to_real_array_if_close(denominator_poly, "Denominator")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if derivative_order > 0:
        numerator_poly = np.append(numerator_poly, np.zeros(derivative_order))
    if integrator_order > 0:
        denominator_poly = np.append(denominator_poly, np.zeros(integrator_order))

    base_system = tf([process_gain], [1]) * tf(numerator_poly, denominator_poly)
    system = base_system

    if delay_time > 0:
        delay_num, delay_den = pade(delay_time, 6)
        delay_tf = tf(delay_num, delay_den)
        system = base_system * delay_tf

    response_time = None
    try:
        response_time, response_output = step_response(system)
        response_points = [{"t": float(time_value), "y": float(output_value)} for time_value, output_value in zip(response_time, response_output)]
    except Exception:
        response_points = []

    pid_coeffs = {}
    p_kp = pi_kp = pid_kp = pi_ki = pid_ki = pid_kd = pd_kp = pd_kd = 0.0

    is_fopdt_input = (
        len(denominator_time_constants) == 1
        and len(numerator_time_constants) == 0
        and derivative_order == 0
        and integrator_order == 0
    )

    input_time_constant = float(np.real(denominator_time_constants[0])) if is_fopdt_input else 0.0

    fopdt_gain = process_gain
    fopdt_time_constant = input_time_constant
    fopdt_delay = delay_time
    approx_fopdt_system = None
    approx_response_points = []
    used_fopdt_approximation = False

    if tuning_method != "GA" and not is_fopdt_input:
        try:
            identified_gain, identified_time_constant, identified_delay = apro_FOPDT(system, fixed_k=process_gain)
            fopdt_gain = identified_gain
            fopdt_time_constant = identified_time_constant
            fopdt_delay = identified_delay
            used_fopdt_approximation = True
        except Exception as exc:
            return jsonify({"error": f"FOPDT approximation failed: {str(exc)}"}), 500

    if tuning_method in ("ZN", "CHR_0", "CHR_0_POZ_H", "CHR_20", "CHR_20_POZ_H", "CHR_0_POT_P", "CHR_20_POT_P"):
        if fopdt_delay is None or float(fopdt_delay) <= 0:
            return jsonify({"error": "Ziegler-Nichols and CHR methods require transport delay (L > 0)."}), 400

    if tuning_method == "ZN":
        pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd = zn_method(
            fopdt_gain,
            fopdt_time_constant,
            fopdt_delay,
        )
    elif tuning_method in ("CHR_0", "CHR_0_POZ_H"):
        pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd = CHR_0_POZ_H(
            fopdt_gain,
            fopdt_time_constant,
            fopdt_delay,
        )
    elif tuning_method in ("CHR_20", "CHR_20_POZ_H"):
        pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd = CHR_20_POZ_H(
            fopdt_gain,
            fopdt_time_constant,
            fopdt_delay,
        )
    elif tuning_method == "CHR_0_POT_P":
        pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd = CHR_0_POT_P(
            fopdt_gain,
            fopdt_time_constant,
            fopdt_delay,
        )
    elif tuning_method == "CHR_20_POT_P":
        pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd = CHR_20_POT_P(
            fopdt_gain,
            fopdt_time_constant,
            fopdt_delay,
        )
    elif tuning_method == "IMC":
        pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd = IMC(
            fopdt_gain,
            fopdt_time_constant,
            fopdt_delay,
            lambda_alpha,
        )
    elif tuning_method == "GA":
        try:
            pid_coeffs, p_kp, pi_kp, pid_kp, pi_ki, pid_ki, pid_kd, pd_kp, pd_kd = genetic_algorithm(
                system,
                time_params,
                initial_output,
                ga_generations,
                ga_population_size,
                ga_mutation_rate,
                controller_type,
            )
            fopdt_time_constant = 0
        except Exception as exc:
            return jsonify({"error": f"Genetic algorithm failed: {str(exc)}"}), 500
    else:
        return jsonify({"error": f'Method "{tuning_method}" is not supported.'}), 400

    if used_fopdt_approximation and fopdt_time_constant > 0:
        approx_fopdt_system = tf([fopdt_gain], [fopdt_time_constant, 1])
        if fopdt_delay > 0:
            approx_delay_num, approx_delay_den = pade(fopdt_delay, 6)
            approx_fopdt_system *= tf(approx_delay_num, approx_delay_den)

        try:
            if response_time is not None and len(response_time) > 1:
                approx_time, approx_output = step_response(approx_fopdt_system, T=response_time)
            else:
                approx_time, approx_output = step_response(approx_fopdt_system)

            approx_response_points = [
                {"t": float(time_value), "y": float(output_value)}
                for time_value, output_value in zip(approx_time, approx_output)
            ]
        except Exception:
            approx_response_points = []

    kp, ki, kd = select_pid_coefficients(
        controller_type,
        p_kp,
        pi_kp,
        pid_kp,
        pi_ki,
        pid_ki,
        pid_kd,
        pd_kp,
        pd_kd,
    )

    try:
        simulation_horizon = float(time_params[6])
    except (TypeError, ValueError, IndexError):
        return jsonify({"error": "Invalid t7 value in timeParams."}), 400

    tau_min = estimate_tau_min(denominator_time_constants, base_system)
    simulation_dt, simulation_steps = choose_dt_and_steps(simulation_horizon, tau_min)

    try:
        stability_report = full_stability_report(system, kp, ki, kd, simulation_dt)
    except Exception as exc:
        return jsonify({"error": f"Stability analysis failed: {str(exc)}"}), 500

    stability_report["discrete"]["t7"] = float(simulation_horizon)
    stability_report["discrete"]["steps_per_sim"] = int(simulation_steps)
    stability_report["discrete"]["tau_min"] = float(tau_min)

    closed_loop_stable = stability_report["discrete_stable"]
    sim_points = []
    sim_points_total = 0
    metrics = {
        "overshoot": 0,
        "settling_time": None,
        "IAE": 0,
        "ITAE": 0,
        "settling_status": None,
    }
    step_data = {"w": [], "t": [], "y": []}

    if closed_loop_stable:
        try:
            sim_results = simulate(system, kp, ki, kd, time_params, initial_output, dt=simulation_dt)
            sim_points_total = len(sim_results["sim_points"])
            sim_points = downsample_sim_points_for_plot(sim_results["sim_points"])
            metrics = sim_results["metrics"]
            step_data = sim_results["step_data"]

            if simulation_indicates_instability(sim_results):
                stability_report["stable"] = False
                stability_report["simulation_indicates_unstable"] = True
        except Exception as exc:
            return jsonify({"error": f"Simulation failed: {str(exc)}"}), 500

    response_payload = {
        "step_response": response_points,
        "apro_step_response": approx_response_points,
        "pid": pid_coeffs,
        "model_type": model_order,
        "y0": initial_output,
        "closed_loop_stable": closed_loop_stable,
        "stability": stability_report,
        "sim_points": sim_points,
        "sim_points_total": sim_points_total,
        "sim_points_plot": len(sim_points),
        "sim_points_stride": int(PLOT_POINT_STRIDE),
        "overshoot": metrics["overshoot"],
        "settlingtime": metrics["settling_time"],
        "settling_status": metrics.get("settling_status"),
        "IAE": metrics["IAE"],
        "ITAE": metrics["ITAE"],
        "step w": step_data["w"],
        "step t": step_data["t"],
        "step y": step_data["y"],
    }

    if used_fopdt_approximation:
        response_payload["K"] = fopdt_gain
        response_payload["T"] = fopdt_time_constant
        response_payload["L"] = fopdt_delay

    return jsonify(response_payload)


if __name__ == "__main__":
    app_port = int(os.getenv("PORT", "5000"))
    is_debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=app_port, debug=is_debug)
