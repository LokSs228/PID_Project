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

app = Flask(__name__)

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

    points, inflection_point, tangent_line, A_L_points, pid_coeffs = [], None, None, None, None
    


    if isinstance(model_type, int):
        if Method == "ZN":
            inflection_point, tangent_line, A_L_points, K, T, L = apro_FOPDT (system)
            pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = zn_method(K, T, L)
            t, y = step_response(system)
            points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]
            if controllerType == "P":
                 sim_points = simulate(system, Kp_P, 0, 0, Params, y0)
            elif controllerType == "PI":
                 sim_points = simulate(system, Kp_PI, Ki_PI, 0, Params, y0)
            elif controllerType == "PD":    
                sim_points = simulate(system, Kp_PD, 0, Kd_PD, Params, y0) 
            else:
                 sim_points = simulate(system, Kp_PID, Ki_PID, Kd_PID, Params, y0)

        elif Method == "GA":
            Kp, Ki, Kd = genetic_algorithm(system, Params, y0, generations, population_size, mutation_rate, controllerType)

            pid_coeffs = {
                "P": {"Kp": Kp if controllerType == "P" else 0, "Ki": 0, "Kd": 0},
                "PI": {"Kp": Kp if controllerType == "PI" else 0, "Ki": Ki if controllerType == "PI" else 0, "Kd": 0},
                "PD": {"Kp": Kp if controllerType == "PD" else 0, "Ki": 0, "Kd": Kd if controllerType == "PD" else 0},
                "PID": {"Kp": Kp if controllerType == "PID" else 0, "Ki": Ki if controllerType == "PID" else 0, "Kd": Kd if controllerType == "PID" else 0},
            }

            sim_points = simulate(system, Kp, Ki, Kd, Params, y0)
            t, y = step_response(system)
            points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]

        elif Method == "CHR_0":
             inflection_point, tangent_line, A_L_points, K, T, L = apro_FOPDT (system)
             pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_0(K, T, L)
             t, y = step_response(system)
             points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]
             if controllerType == "P":
                 sim_points = simulate(system, Kp_P, 0, 0, Params, y0)
             elif controllerType == "PI":
                 sim_points = simulate(system, Kp_PI, Ki_PI, 0, Params, y0)
             elif controllerType == "PD":    
                sim_points = simulate(system, Kp_PD, 0, Kd_PD, Params, y0) 
             else:
                 sim_points = simulate(system, Kp_PID, Ki_PID, Kd_PID, Params, y0)

        elif Method == "CHR_20":
             inflection_point, tangent_line, A_L_points, K, T, L = apro_FOPDT (system)
             pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_20(K, T, L)
             t, y = step_response(system)
             points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]
             if controllerType == "P":
                 sim_points = simulate(system, Kp_P, 0, 0, Params, y0)
             elif controllerType == "PI":
                 sim_points = simulate(system, Kp_PI, Ki_PI, 0, Params, y0)
             elif controllerType == "PD":    
                sim_points = simulate(system, Kp_PD, 0, Kd_PD, Params, y0) 
             else:
                 sim_points = simulate(system, Kp_PID, Ki_PID, Kd_PID, Params, y0)
        elif Method == "IMC":
             inflection_point, tangent_line, A_L_points, K, T, L = apro_FOPDT (system)
             pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = IMC(K, T, L, alpha)
             t, y = step_response(system)
             points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]
             if controllerType == "P":
                 sim_points = simulate(system, Kp_P, 0, 0, Params, y0)
             elif controllerType == "PI":
                 sim_points = simulate(system, Kp_PI, Ki_PI, 0, Params, y0)
             elif controllerType == "PD":    
                sim_points = simulate(system, Kp_PD, 0, Kd_PD, Params, y0) 
             else:
                 sim_points = simulate(system, Kp_PID, Ki_PID, Kd_PID, Params, y0)                     



        else:
            return jsonify({'error': f'Method "{Method}" not supported'}), 400
    else:
        return jsonify({'error': 'Invalid model_type value'}), 400

    return jsonify({
        'step_response': points,
        'inflection_point': inflection_point,
        'tangent_line': tangent_line,
        'pid': pid_coeffs,
        'A_L_points': A_L_points,
        'model_type': model_type,
        'y0': y0,
        'sim_points': sim_points
    })

if __name__ == '__main__':
    app.run(debug=True)
