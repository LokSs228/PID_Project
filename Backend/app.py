import numpy as np
from flask import Flask, request, jsonify
from control import tf, step_response, pade
from zn_method import zn_method
from Sim import simulate
from GA import genetic_algorithm
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
    population_size = data.get ('population_size')
    mutation_rate = data.get ('mutation_rate')
    
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

    # --- Расчёт по методу ---
    points, inflection_point, tangent_line, A_L_points, pid_coeffs = [], None, None, None, None

    if isinstance(model_type, int):
        if Method == "ZN":
            if model_type in [1, 2, 3, 4, 5]:
                points, inflection_point, tangent_line, A_L_points, pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID = zn_method(system)
            else:
                t, y = step_response(system)
                points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]
                return jsonify({'step_response': points, 'message': 'Too high model order for ZN method'}), 400
            
            sim_points = simulate(system, Kp_PID, Ki_PID, Kd_PID, Params, y0)

        elif Method == "GA":
            Kp_P = Kp_PI = Kp_PID = Ki_PI = Ki_PID = Kd_PID = 0.0
            Kp_PID, Ki_PID, Kd_PID = genetic_algorithm(system, Params, y0, generations, population_size, mutation_rate)
            sim_points = simulate(system, Kp_PID, Ki_PID, Kd_PID, Params, y0)
            pid_coeffs = {
            "P": {"Kp": Kp_P, "Ki": 0, "Kd": 0},
            "PI": {"Kp": Kp_PI, "Ki": Ki_PI, "Kd": 0},
            "PID": {"Kp": Kp_PID, "Ki": Ki_PID, "Kd": Kd_PID}
            }
            t, y = step_response(system)
            points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t, y)]

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

