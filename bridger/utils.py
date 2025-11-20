import weakref
from functools import wraps, lru_cache as _lru_cache

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


def lru_cache(*lru_args, **lru_kwargs):
    def wrapper(func):
        @_lru_cache(*lru_args, **lru_kwargs)
        def _func(_self, *args, **kwargs):
            return func(_self(), *args, **kwargs)

        @wraps(func)
        def inner(self, *args, **kwargs):
            return _func(weakref.ref(self), *args, **kwargs)

        inner.cache_clear = _func.cache_clear
        inner.cache_info = _func.cache_info
        inner._cached_func = _func
        return inner

    return wrapper
