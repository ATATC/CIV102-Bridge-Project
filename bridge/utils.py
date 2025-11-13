import numpy as np


def intervals(x: np.ndarray) -> list[tuple[float, float]]:
    r = []
    start = None
    for i in range(len(x)):
        if x[i] and start is None:
            start = i
        elif not x[i] and start is not None:
            r.append((start, i - 1))
            start = None
    if start is not None:
        r.append((start, len(x) - 1))
    return r