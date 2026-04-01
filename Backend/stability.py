"""
Analýza stability uzavřené regulační smyčky se zápornou jednotkovou zpětnou vazbou.

Pro ideální PID regulátor G_r(s) a řízený systém G_s(s) jsou póly uzavřené smyčky
kořeny rovnice 1 + G_r(s)·G_s(s) = 0 (charakteristický polynom jmenovatele T(s)=L/(1+L),
kde L = G_r·G_s).
"""

import numpy as np
from control import feedback, poles, tf

_STRICT_NEG_TOL = 1e-7


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
    Vrací slovník vhodný pro JSON:
      stable — všechny Re(p) < -_STRICT_NEG_TOL
      poles — seřazené podle -Re(p), Im(p)
      pole_real_parts — reálné části ve stejném pořadí
    """
    pole_arr = closed_loop_poles(plant, Kp, Ki, Kd)
    pole_list = [
        {"re": float(np.real(z)), "im": float(np.imag(z))}
        for z in pole_arr
    ]
    pole_list.sort(key=lambda d: (-d["re"], d["im"]))
    reals = [p["re"] for p in pole_list]
    stable = all(r < -_STRICT_NEG_TOL for r in reals)
    return {
        "stable": stable,
        "poles": pole_list,
        "pole_real_parts": reals,
    }
