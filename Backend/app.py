import numpy as np
from flask import Flask, request, jsonify
from control import tf, step_response, pade
from zn_method import zn_method
from Sim import simulate
from GA import genetic_algorithm
from apro_FOPDT import apro_FOPDT 
from CHR_0 import CHR_0
from CHR_20 import CHR_20
from IMC import IMC
from metrix import metrix

app = Flask(__name__)


def select_pid(controllerType, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD):
    if controllerType == "P":
        return Kp_P, 0, 0
    elif controllerType == "PI":
        return Kp_PI, Ki_PI, 0
    elif controllerType == "PD":
        return Kp_PD, 0, Kd_PD
    else:
        return Kp_PID, Ki_PID, Kd_PID


@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json

    K = data.get('K')
    T_num = data.get('T_num', [])
    T_den = data.get('T_den', [])
    L = data.get('L', 0)
    Method = data.get('Method')

    Params = data.get('timeParams', [])
    y0 = data.get('y0')

    generations = data.get('generations')
    population_size = data.get('population_size')
    mutation_rate = data.get('mutation_rate')
    controllerType = data.get('controllerType', 'PID') 
    alpha = data.get('lambdaAlpha', 2) 
    alpha = float(alpha)
    if len(Params) < 9:
        return jsonify({'error': 'Not enough timeParams'}), 400

    if K is None or not T_den:
        return jsonify({'error': 'Missing parameters K or T'}), 400

    try:
        K = float(K)
        T_den = [float(Ti) for Ti in T_den]
        T_num = [float(Ti) for Ti in T_num]
        L = float(L)
    except ValueError:
        return jsonify({'error': 'Некорректные числовые значения'}), 400

    model_type = len(T_den)

    num = [1]
    for T in T_num:
        num = np.polymul(num, [T, 1])

    den = [1]
    for T in T_den:
        den = np.polymul(den, [T, 1])

    system = tf([K], [1]) * tf(num, den)

    if L > 0:
        num_delay, den_delay = pade(L, 3)
        delay = tf(num_delay, den_delay)
        system *= delay

    points, inflection_point, tangent_line, A_L_points, pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = [], None, None, None, None, 0, 0 ,0 ,0 , 0, 0, 0, 0
    


    if isinstance(model_type, int):

        if Method == "ZN":
            inflection_point, tangent_line, A_L_points, K, T, L = apro_FOPDT(system)
            pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = zn_method(K, T, L)

        elif Method == "CHR_0":
            inflection_point, tangent_line, A_L_points, K, T, L = apro_FOPDT(system)
            pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_0(K, T, L)

        elif Method == "CHR_20":
            inflection_point, tangent_line, A_L_points, K, T, L = apro_FOPDT(system)
            pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_20(K, T, L)

        elif Method == "IMC":
            inflection_point, tangent_line, A_L_points, K, T, L = apro_FOPDT(system)
            pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = IMC(K, T, L, alpha)
        elif Method == "GA":

            Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = genetic_algorithm(
                system, Params, y0,
                generations, population_size, mutation_rate, controllerType
            )
        Kp, Ki, Kd = select_pid(
            controllerType,
            Kp_P, Kp_PI, Kp_PID,
            Ki_PI, Ki_PID,
            Kd_PID, Kp_PD, Kd_PD
        )
        sim_points = simulate(system, Kp, Ki, Kd, Params, y0)
        step = sim_points["step"]
        overshoot, SettlingTime, IAE, ITAE = metrix(
             step["t"], step["y"], step["w"], step["e"]
         )

        t, y = step_response(system)
        points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]

    else:
        return jsonify({'error': f'Method "{Method}" not supported'}), 400

    return jsonify({
        'step_response': points,
        'inflection_point': inflection_point,
        'tangent_line': tangent_line,
        'pid': pid_coeffs,
        'A_L_points': A_L_points,
        'model_type': model_type,
        'y0': y0,
        'sim_points': sim_points["sim_points"],
        'overshoot': overshoot,
        'settlingtime': SettlingTime,
        'IAE': IAE,
        'ITAE': ITAE
    })


if __name__ == '__main__':
    app.run(debug=True)

