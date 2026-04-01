"""
Stabilita uzavřené smyčky:

- Spojitý ideální PID a G(s): póly v s-rovině (1 + G_r G_s = 0).
- Diskretní model odpovídající Sim.py: ZOH diskrétizace objektu (stejně jako get_discrete_state_space)
  a PID se stejným pořadím výpočtu (Eulerovo integrační člen, derivace z odhadu -(y_k - y_{k-1})/T).
  Stabilita v z: všechny vlastní čísla uzavřené smyčky musí ležet uvnitř jednotkové kružnice |z| < 1.
"""

import numpy as np
from control import feedback, poles, tf

from discretization import get_discrete_state_space

# Otevřená levá polovina s (numerická tolerance)
_RHP_EPS = 1e-5
# Jednotkový kruh v z (přísně uvnitř)
_Z_UNIT_TOL = 1e-6


def _nearly_zero(x, tol=1e-12):
    return abs(float(x)) <= tol


def build_pid_transfer_function(Kp, Ki, Kd):
    """
    Ideální spojitý regulátor odpovídající diskrétní simulaci v Sim.py:
    u = Kp·e + Ki·∫e + Kd·de/dt  →  G_r(s) = Kd·s + Kp + Ki/s (s příslušnými nulami).
    """
    Kp = float(Kp)
    Ki = 0.0 if _nearly_zero(Ki) else float(Ki)
    Kd = 0.0 if _nearly_zero(Kd) else float(Kd)

    if Ki == 0 and Kd == 0:
        return tf([Kp], [1])
    if Ki != 0 and Kd == 0:
        return tf([Kp, Ki], [1, 0])
    if Ki == 0 and Kd != 0:
        return tf([Kd, Kp], [1])
    return tf([Kd, Kp, Ki], [1, 0])


def closed_loop_poles(plant, Kp, Ki, Kd):
    """Vrací póly uzavřené smyčky (minimal realizace feedback(L, 1))."""
    gr = build_pid_transfer_function(Kp, Ki, Kd)
    loop = gr * plant
    closed = feedback(loop, 1)
    p = poles(closed)
    arr = np.asarray(p, dtype=complex).ravel()
    return arr


def analyze_closed_loop_stability(plant, Kp, Ki, Kd):
    """
    Spojitá uzavřená smyčka (ideální G_r(s), záporná jednotková ZV).
    """
    pole_arr = closed_loop_poles(plant, Kp, Ki, Kd)
    pole_list = [
        {"re": float(np.real(z)), "im": float(np.imag(z))}
        for z in pole_arr
    ]
    pole_list.sort(key=lambda d: (-d["re"], d["im"]))
    reals = [p["re"] for p in pole_list]
    stable = bool(max(reals) < _RHP_EPS) if reals else True
    return {
        "stable": stable,
        "poles": pole_list,
        "pole_real_parts": reals,
    }


def _build_closed_loop_z_state_matrix(A_d, B_vec, C_vec, D_s, Kp, Ki, Kd, T):
    """
    Jednokroková mapa [x_{k+1}; u_k; I_k; y_k] = M [x_k; u_{k-1}; I_{k-1}; y_{k-1}]
    pro Ki > 0 odpovídající Sim.py (r=0 pro vlastní čísla).

    y_k = C x_k + D u_{k-1},  I_k = I_{k-1} - T y_k,
    u_k = α y_k + Ki I_{k-1} + β y_{k-1},  α = -(Kp + Ki*T + Kd/T),  β = Kd/T.
    """
    n = A_d.shape[0]
    B = np.asarray(B_vec, dtype=float).reshape(-1, 1)
    C = np.asarray(C_vec, dtype=float).reshape(1, -1)
    A_d = np.asarray(A_d, dtype=float)
    D_s = float(D_s)
    Kp = float(Kp)
    Ki = 0.0 if _nearly_zero(Ki) else float(Ki)
    Kd = 0.0 if _nearly_zero(Kd) else float(Kd)
    T = float(T)

    if Ki == 0 and Kd == 0:
        # Pouze P: z = [x_k; u_{k-1}]
        kp = Kp
        M11 = A_d - B @ (kp * C)
        M12 = -B * (kp * D_s)
        top = np.hstack([M11, M12])
        row2 = np.hstack([-kp * C, [[-kp * D_s]]])
        return np.vstack([top, row2])

    if Ki == 0:
        # PD nebo P+D bez integrátoru v řízení
        alpha = -(Kp + Kd / T)
        beta = Kd / T
        M11 = A_d + B @ (alpha * C)
        M12 = B * (alpha * D_s)
        M13 = B * beta
        row2 = np.hstack([alpha * C, [[alpha * D_s]], [[beta]]])
        row3 = np.hstack([C, [[D_s]], [[0.0]]])
        return np.vstack([np.hstack([M11, M12, M13]), row2, row3])

    alpha = -(Kp + Ki * T + Kd / T)
    beta = Kd / T
    M11 = A_d + B @ (alpha * C)
    M12 = B * (alpha * D_s)
    M13 = B * Ki
    M14 = B * beta
    row2 = np.hstack([alpha * C, [[alpha * D_s]], [[Ki]], [[beta]]])
    row3 = np.hstack([-T * C, [[-T * D_s]], [[1.0]], [[0.0]]])
    row4 = np.hstack([C, [[D_s]], [[0.0]], [[0.0]]])
    return np.vstack([np.hstack([M11, M12, M13, M14]), row2, row3, row4])


def analyze_discrete_z_stability(plant, Kp, Ki, Kd, dt):
    """
    Stabilita podle z-rovině konzistentní se Sim.py (T = dt).
    """
    num = np.atleast_1d(plant.num[0][0])
    den = np.atleast_1d(plant.den[0][0])
    A_d, B_vec, C_vec, D_s = get_discrete_state_space(num, den, float(dt))
    M = _build_closed_loop_z_state_matrix(A_d, B_vec, C_vec, D_s, Kp, Ki, Kd, dt)
    eig = np.linalg.eigvals(M)
    mags = np.abs(eig)
    max_mag = float(np.max(mags)) if mags.size else 0.0
    stable = max_mag < 1.0 - _Z_UNIT_TOL

    pole_list = [
        {
            "re": float(np.real(z)),
            "im": float(np.imag(z)),
            "abs": float(np.abs(z)),
        }
        for z in eig
    ]
    pole_list.sort(key=lambda d: (-d["abs"], -d["re"], d["im"]))

    return {
        "stable": bool(stable),
        "dt": float(dt),
        "poles_z": pole_list,
        "max_modulus": max_mag,
    }


def full_stability_report(plant, Kp, Ki, Kd, dt):
    """
    Hlavní závěr: diskrétní |z| < 1. Spojitý model je informativní.
    """
    continuous = analyze_closed_loop_stability(plant, Kp, Ki, Kd)
    discrete = analyze_discrete_z_stability(plant, Kp, Ki, Kd, dt)
    return {
        "stable": discrete["stable"],
        "discrete_stable": discrete["stable"],
        "continuous_poles_stable": continuous["stable"],
        "simulation_indicates_unstable": False,
        "discrete": discrete,
        "continuous": {
            "stable": continuous["stable"],
            "poles": continuous["poles"],
            "pole_real_parts": continuous["pole_real_parts"],
        },
    }
