from functools import lru_cache

import numpy as np
from scipy.signal import cont2discrete, tf2ss


def _to_tuple(values):
    arr = np.asarray(values, dtype=float).reshape(-1)
    return tuple(float(v) for v in arr)


@lru_cache(maxsize=256)
def _discretize_cached(num_tuple, den_tuple, dt):
    num = np.asarray(num_tuple, dtype=float)
    den = np.asarray(den_tuple, dtype=float)
    A, B, C, D = tf2ss(num, den)
    A_d, B_d, C_d, D_d, _ = cont2discrete((A, B, C, D), dt)

    B_vec = np.asarray(B_d, dtype=float).reshape(-1)
    C_vec = np.asarray(C_d, dtype=float).reshape(-1)
    D_scalar = float(np.asarray(D_d, dtype=float).reshape(-1)[0])

    return A_d, B_vec, C_vec, D_scalar


def get_discrete_state_space(num, den, dt):
    A_d, B_vec, C_vec, D_scalar = _discretize_cached(_to_tuple(num), _to_tuple(den), float(dt))
    return A_d.copy(), B_vec.copy(), C_vec.copy(), D_scalar
