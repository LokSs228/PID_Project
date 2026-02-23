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
    K_in = data.get('K')
    T_num = data.get('T_num', [])
    T_den = data.get('T_den', [])
    L_in = data.get('L', 0)
    Method = data.get('Method')
    Params = data.get('timeParams', [])
    y0 = data.get('y0', 0)

    generations = data.get('generations')
    population_size = data.get('population_size')
    mutation_rate = data.get('mutation_rate')
    controllerType = data.get('controllerType', 'PID') 
    
    alpha = data.get('lambdaAlpha', 2) 
    try:
        alpha = float(alpha)
    except (TypeError, ValueError):
        alpha = 2.0

    if len(Params) < 9:
        return jsonify({'error': 'Not enough timeParams'}), 400

    if K_in is None or not T_den:
        return jsonify({'error': 'Missing parameters K or T'}), 400

    try:
        K_val = float(K_in)
        T_den_vals = [float(Ti) for Ti in T_den]
        T_num_vals = [float(Ti) for Ti in T_num]
        L_val = float(L_in)
    except ValueError:
        return jsonify({'error': 'Некорректные числовые значения'}), 400

    model_type = len(T_den_vals)
    num = [1]
    for ti in T_num_vals:
        num = np.polymul(num, [ti, 1])
    den = [1]
    for ti in T_den_vals:
        den = np.polymul(den, [ti, 1])

    base_system = tf([K_val], [1]) * tf(num, den)
    system = base_system

    # Добавление задержки (Padé approximation)
    if L_val > 0:
        num_delay, den_delay = pade(L_val, 4) # 3-й порядок аппроксимации
        delay = tf(num_delay, den_delay)
        system = base_system * delay

    # --- 3. Инициализация переменных для результата ---
    points = []
    inflection_point = None
    tangent_line = None
    A_L_points = None
    pid_coeffs = {}
    
    # Инициализируем нулями
    Kp_P = Kp_PI = Kp_PID = Ki_PI = Ki_PID = Kd_PID = Kp_PD = Kd_PD = 0
    
    # Переменные для аппроксимированной модели (FOPDT)
    K_fopdt, T_fopdt, L_fopdt = K_val, 0, L_val 
    apro_FOPDT_system = None
    apro_points = []

    # --- 4. Выбор метода настройки ---
    
    # Если метод НЕ генетический, нам почти всегда нужна аппроксимация FOPDT
    if Method != "GA":
        try:
            inflection_point, tangent_line, A_L_points, K_ap, T_ap, L_ap = apro_FOPDT(system)
            # Обновляем переменные, которые пойдут в методы расчета PID
            K_fopdt, T_fopdt, L_fopdt = K_ap, T_ap, L_ap
        except Exception as e:
            return jsonify({'error': f'Ошибка аппроксимации FOPDT: {str(e)}'}), 500

    # Расчет коэффициентов
    if Method == "ZN":
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = zn_method(K_fopdt, T_fopdt, L_fopdt)

    elif Method == "CHR_0":
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_0(K_fopdt, T_fopdt, L_fopdt)

    elif Method == "CHR_20":
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_20(K_fopdt, T_fopdt, L_fopdt)

    elif Method == "IMC":
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = IMC(K_fopdt, T_fopdt, L_fopdt, alpha)

    elif Method == "GA":
        try:
            pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = genetic_algorithm(
                system, Params, y0,
                generations, population_size, mutation_rate, controllerType
            )
            T_fopdt = 0 
        except Exception as e:
             return jsonify({'error': f'Ошибка Genetic Algorithm: {str(e)}'}), 500

    else:
        return jsonify({'error': f'Method "{Method}" not supported'}), 400
    if T_fopdt > 0:
        apro_FOPDT_system = tf([K_fopdt], [T_fopdt, 1])
        if L_fopdt > 0:
            apro_num_delay, apro_den_delay = pade(L_fopdt, 4)
            apro_FOPDT_system *= tf(apro_num_delay, apro_den_delay)
        try:
            t_apro_resp, y_apro_resp = step_response(apro_FOPDT_system)
            apro_points = [
                {'t': float(ti), 'y': float(yi)}
                for ti, yi in zip(t_apro_resp, y_apro_resp)
            ]
        except Exception:
            apro_points = []
    # --- 5. Выбор итоговых коэффициентов и Симуляция ---
    Kp, Ki, Kd = select_pid(
        controllerType,
        Kp_P, Kp_PI, Kp_PID,
        Ki_PI, Ki_PID,
        Kd_PID, Kp_PD, Kd_PD
    )
    try:
        # Теперь simulate возвращает словарь, содержащий и sim_points, и metrics, и step_data
        sim_results = simulate(system, Kp, Ki, Kd, Params, y0)
        sim_points = sim_results["sim_points"]
        metrics = sim_results["metrics"]
        step_data = sim_results["step_data"]
        
    except Exception as e:
        return jsonify({'error': f'Ошибка симуляции: {str(e)}'}), 500
    # Опеределение реакции разомкнутой системы (Open Loop)
    try:
        t_resp, y_resp = step_response(system)
        points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t_resp, y_resp)]
    except Exception:
        points = []

    # --- 6. Формирование ответа ---
    return jsonify({
        'step_response': points,
        'inflection_point': inflection_point,
        'apro_step_response': apro_points,
        'tangent_line': tangent_line,
        'pid': pid_coeffs,
        'A_L_points': A_L_points,
        'model_type': model_type,
        'y0': y0,
        'sim_points': sim_points,
        # Данные из словаря metrics (рассчитанные внутри simulate)
        'overshoot': metrics["overshoot"],
        'settlingtime': metrics["settling_time"],
        'IAE': metrics["IAE"],
        'ITAE': metrics["ITAE"],
        # Параметры модели
        'K': K_fopdt, 
        'T': T_fopdt,
        'L': L_fopdt,
        # Данные для детального графика переходного процесса
        'step w': step_data["w"],
        'step t': step_data["t"],
        'step y': step_data["y"]
    })

if __name__ == '__main__':
    app.run(debug=True)

