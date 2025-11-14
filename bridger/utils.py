import numpy as np


def intervals(x: np.ndarray, *, dx: float = 1) -> list[tuple[float, float]]:
    r = []
    start = None
    for i in range(len(x)):
        if x[i] and start is None:
            start = i
        elif not x[i] and start is not None:
            r.append((start * dx, (i - 1) * dx))
            start = None
    if start is not None:
        r.append((start * dx, (len(x) - 1) * dx))
    return r