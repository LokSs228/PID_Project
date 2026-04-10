from functools import lru_cache

import numpy as np
from scipy.signal import cont2discrete, tf2ss


def _as_float_tuple(values):
    values_array = np.asarray(values, dtype=float).reshape(-1)
    return tuple(float(value) for value in values_array)


@lru_cache(maxsize=256)
def _discretize_cached(numerator_tuple, denominator_tuple, sample_time):
    numerator_coeffs = np.asarray(numerator_tuple, dtype=float)
    denominator_coeffs = np.asarray(denominator_tuple, dtype=float)

    state_matrix, input_matrix, output_matrix, feedthrough_matrix = tf2ss(
        numerator_coeffs,
        denominator_coeffs,
    )

    (
        discrete_state_matrix,
        discrete_input_matrix,
        discrete_output_matrix,
        discrete_feedthrough_matrix,
        _,
    ) = cont2discrete((state_matrix, input_matrix, output_matrix, feedthrough_matrix), sample_time)

    input_vector = np.asarray(discrete_input_matrix, dtype=float).reshape(-1)
    output_vector = np.asarray(discrete_output_matrix, dtype=float).reshape(-1)
    feedthrough_scalar = float(np.asarray(discrete_feedthrough_matrix, dtype=float).reshape(-1)[0])

    return discrete_state_matrix, input_vector, output_vector, feedthrough_scalar


def get_discrete_state_space(num, den, dt):
    discrete_state_matrix, input_vector, output_vector, feedthrough_scalar = _discretize_cached(
        _as_float_tuple(num),
        _as_float_tuple(den),
        float(dt),
    )
    return (
        discrete_state_matrix.copy(),
        input_vector.copy(),
        output_vector.copy(),
        feedthrough_scalar,
    )
