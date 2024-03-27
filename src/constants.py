import numpy as np
from numpy.typing import NDArray

CHESS_SQUARE_SIZE: float = 38 / 1000

# Get the magnitude of the given vector
def magnitude(vec):
    return np.sqrt(np.sum(vec ** 2))

# Get the component of the given B field vector oriented towards the center
def centering_strength(
    pos,
    field,
    center
):
    return magnitude(field.dot(normalized(center - pos)))

# Normalize a numpy vector
def normalized(v) -> NDArray:
    v = np.asarray(v)
    denom = np.sqrt(np.sum(v ** 2))
    return v / denom if denom != 0 else np.empty_like(v)
