import numpy as np
import os
from flask import Flask, request, jsonify
from control import tf, step_response, pade
from zn_method import zn_method
from Sim import simulate
from GA import genetic_algorithm
from apro_FOPDT import apro_FOPDT 
from CHR_0_POZ_H import CHR_0 as CHR_0_POZ_H
from CHR_20_POZ_H import CHR_20 as CHR_20_POZ_H
from CHR_0_POT_P import CHR_0_POT_P
from CHR_20_POT_P import CHR_20_POT_P
from IMC import IMC

app = Flask(__name__)

def normalize_origin(origin):
    if origin is None:
        return None
    origin = origin.strip()
    if origin == "*":
        return "*"
    return origin.rstrip("/")

def parse_allowed_origins():
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    return [normalize_origin(origin) for origin in raw.split(",") if origin.strip()]

ALLOWED_ORIGINS = parse_allowed_origins()

def resolve_cors_origin(request_origin):
    request_origin_normalized = normalize_origin(request_origin)
    if "*" in ALLOWED_ORIGINS:
        return "*"
    if request_origin_normalized and request_origin_normalized in ALLOWED_ORIGINS:
        return request_origin_normalized
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

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

def select_pid(controllerType, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD):
    if controllerType == "P":
        return Kp_P, 0, 0
    elif controllerType == "PI":
        return Kp_PI, Ki_PI, 0
    elif controllerType == "PD":
        return Kp_PD, 0, Kd_PD
    else: 
        return Kp_PID, Ki_PID, Kd_PID

def parse_complex(value, field_name):
    if value is None:
        return None
    if isinstance(value, (int, float, complex)):
        return complex(value)
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        text = text.replace("i", "j").replace("I", "j").replace("J", "j")
        text = text.replace(" ", "")
        try:
            return complex(text)
        except ValueError:
            raise ValueError(f'Neplatná komplexní hodnota pro {field_name}: "{value}"')
    raise ValueError(f'Neplatný datový typ pro {field_name}')

def parse_real(value, field_name, tol=1e-9):
    z = parse_complex(value, field_name)
    if z is None:
        return None
    if abs(z.imag) <= tol:
        return float(z.real)
    raise ValueError(f'{field_name} musí být reálné číslo')

def parse_complex_list(values, field_name):
    if values is None:
        return []
    result = []
    for i, v in enumerate(values):
        z = parse_complex(v, f"{field_name}[{i}]")
        if z is not None:
            result.append(z)
    return result

def to_real_array_if_close(arr, field_name, tol=1e-9):
    arr = np.asarray(arr, dtype=complex)
    if np.any(np.abs(arr.imag) > tol):
        raise ValueError(
            f'{field_name} obsahuje nereálné koeficienty. Zadejte sdružené dvojice, aby výsledný polynom byl reálný.'
        )
    return np.asarray(arr.real, dtype=float)

def parse_nonneg_int(value, field_name):
    if value is None or value == "":
        return 0
    try:
        iv = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} musí být nezáporné celé číslo')
    if iv < 0:
        raise ValueError(f'{field_name} musí být nezáporné celé číslo')
    return iv


@app.route('/calculate', methods=['POST', 'OPTIONS'])
def calculate():
    if request.method == 'OPTIONS':
        return ('', 204)

    data = request.json
    K_in = data.get('K')
    T_num = data.get('T_num', [])
    T_den = data.get('T_den', [])
    L_in = data.get('L', 0)
    diff_order_in = data.get('diffOrder', 0)
    int_order_in = data.get('intOrder', 0)
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

    if len(Params) < 11:
        return jsonify({'error': 'Nedostatek parametrů timeParams.'}), 400

    if K_in is None or not T_den:
        return jsonify({'error': 'Chybí vstupní parametry K nebo T.'}), 400

    try:
        K_val = parse_real(K_in, "K")
        T_den_vals = parse_complex_list(T_den, "T_den")
        T_num_vals = parse_complex_list(T_num, "T_num")
        L_val = parse_real(L_in, "L")
        diff_order = parse_nonneg_int(diff_order_in, "diffOrder")
        int_order = parse_nonneg_int(int_order_in, "intOrder")
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


    model_type = len(T_den_vals)
    num = [1]
    for ti in T_num_vals:
        num = np.polymul(num, [ti, 1])
    den = [1]
    for ti in T_den_vals:
        den = np.polymul(den, [ti, 1])

    try:
        num = to_real_array_if_close(num, "Čitatel")
        den = to_real_array_if_close(den, "Jmenovatel")
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if diff_order > 0:
        num = np.append(num, np.zeros(diff_order))
    if int_order > 0:
        den = np.append(den, np.zeros(int_order))

    base_system = tf([K_val], [1]) * tf(num, den)
    system = base_system

    # Přidání zpoždění (Padé aproximace)
    if L_val > 0:
        num_delay, den_delay = pade(L_val, 6) # aproximace 6. řádu
        delay = tf(num_delay, den_delay)
        system = base_system * delay

    # --- 3. Inicializace proměnných pro výsledek ---
    t_resp = None
    try:
        t_resp, y_resp = step_response(system)
        points = [{'t': float(ti), 'y': float(yi)} for ti, yi in zip(t_resp, y_resp)]
    except Exception:
        points = []
    pid_coeffs = {}
    
    # Inicializujeme nulami
    Kp_P = Kp_PI = Kp_PID = Ki_PI = Ki_PID = Kd_PID = Kp_PD = Kd_PD = 0
    
    # Proměnné pro aproximovaný model (FOPDT)
    # Pokud je vstupní přenos už FOPDT:
    # G(s) = K / (T*s + 1) * e^(-L*s)
    is_fopdt_system = (
        len(T_den_vals) == 1
        and len(T_num_vals) == 0
        and diff_order == 0
        and int_order == 0
    )
    T_input_fopdt = float(np.real(T_den_vals[0])) if is_fopdt_system else 0.0

    K_fopdt, T_fopdt, L_fopdt = K_val, T_input_fopdt, L_val 
    apro_FOPDT_system = None
    apro_points = []
    used_fopdt_approximation = False

    # --- 4. Volba metody ladění ---
    
    # Volba aproximace FOPDT podle typu systému.
    # FOPDT vstup neaproximujeme, ostatní systémy ano (mimo GA).
    if Method != "GA" and not is_fopdt_system:
        try:
            K_ap, T_ap, L_ap = apro_FOPDT(system, fixed_k=K_val)
            # Aktualizujeme proměnné, které půjdou do metod výpočtu PID
            K_fopdt, T_fopdt, L_fopdt = K_ap, T_ap, L_ap
            used_fopdt_approximation = True
        except Exception as e:
            return jsonify({'error': f'Chyba při aproximaci FOPDT: {str(e)}'}), 500

    if Method in ("ZN", "CHR_0", "CHR_0_POZ_H", "CHR_20", "CHR_20_POZ_H", "CHR_0_POT_P", "CHR_20_POT_P"):
        if L_fopdt is None or float(L_fopdt) <= 0:
            return jsonify({
                'error': 'Metody Ziegler-Nichols a CHR nelze použít bez dopravního zpoždění (L > 0).'
            }), 400

    # Výpočet koeficientů
    if Method == "ZN":
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = zn_method(K_fopdt, T_fopdt, L_fopdt)

    elif Method in ("CHR_0", "CHR_0_POZ_H"):
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_0_POZ_H(K_fopdt, T_fopdt, L_fopdt)

    elif Method in ("CHR_20", "CHR_20_POZ_H"):
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_20_POZ_H(K_fopdt, T_fopdt, L_fopdt)

    elif Method == "CHR_0_POT_P":
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_0_POT_P(K_fopdt, T_fopdt, L_fopdt)

    elif Method == "CHR_20_POT_P":
        pid_coeffs, Kp_P, Kp_PI, Kp_PID, Ki_PI, Ki_PID, Kd_PID, Kp_PD, Kd_PD = CHR_20_POT_P(K_fopdt, T_fopdt, L_fopdt)

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
             return jsonify({'error': f'Chyba genetického algoritmu: {str(e)}'}), 500

    else:
        return jsonify({'error': f'Metoda "{Method}" není podporována.'}), 400
    if used_fopdt_approximation and T_fopdt > 0:
        apro_FOPDT_system = tf([K_fopdt], [T_fopdt, 1])
        if L_fopdt > 0:
            apro_num_delay, apro_den_delay = pade(L_fopdt, 6)
            apro_FOPDT_system *= tf(apro_num_delay, apro_den_delay)
        try:
            if t_resp is not None and len(t_resp) > 1:
                t_apro_resp, y_apro_resp = step_response(apro_FOPDT_system, T=t_resp)
            else:
                t_apro_resp, y_apro_resp = step_response(apro_FOPDT_system)
            apro_points = [
                {'t': float(ti), 'y': float(yi)}
                for ti, yi in zip(t_apro_resp, y_apro_resp)
            ]
        except Exception:
            apro_points = []
    # --- 5. Volba výsledných koeficientů a simulace ---
    Kp, Ki, Kd = select_pid(
        controllerType,
        Kp_P, Kp_PI, Kp_PID,
        Ki_PI, Ki_PID,
        Kd_PID, Kp_PD, Kd_PD
    )
    try:
        # Funkce simulate nyní vrací slovník se sim_points, metrics a step_data
        sim_results = simulate(system, Kp, Ki, Kd, Params, y0)
        sim_points = sim_results["sim_points"]
        metrics = sim_results["metrics"]
        step_data = sim_results["step_data"]
        
    except Exception as e:
        return jsonify({'error': f'Chyba simulace: {str(e)}'}), 500

    # --- 6. Sestavení odpovědi ---
    response_payload = {
        'step_response': points,
        'apro_step_response': apro_points,
        'pid': pid_coeffs,
        'model_type': model_type,
        'y0': y0,
        'sim_points': sim_points,
        # Data ze slovníku metrics (vypočítaná uvnitř simulate)
        'overshoot': metrics["overshoot"],
        'settlingtime': metrics["settling_time"],
        'settling_status': metrics.get("settling_status"),
        'IAE': metrics["IAE"],
        'ITAE': metrics["ITAE"],
        # Data pro detailní graf přechodového děje
        'step w': step_data["w"],
        'step t': step_data["t"],
        'step y': step_data["y"]
    }

    if used_fopdt_approximation:
        response_payload['K'] = K_fopdt
        response_payload['T'] = T_fopdt
        response_payload['L'] = L_fopdt

    return jsonify(response_payload)

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host='0.0.0.0', port=port, debug=debug)

