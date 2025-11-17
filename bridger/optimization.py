from typing import Callable, TypedDict

import numpy as np

from bridger.cross_section import CrossSection
from bridger.prototype import BeamBridge
from bridger.evaluation import Evaluator


def grid_search(param_ranges: dict[str, tuple[float, float, float]], criterion: Callable[
    [dict[str, float]], float]) -> tuple[dict[str, float], float]:
    best_params = {}
    best_score = 0
    param_values = []
    param_names = []
    for name, (start, end, step) in param_ranges.items():
        param_names.append(name)
        param_values.append(np.arange(start, end + step, step))
    for params in np.array(np.meshgrid(*param_values)).T.reshape(-1, len(param_names)):
        current_params = dict(zip(param_names, params))
        score = criterion(**current_params)
        if score > best_score:
            best_score = score
            best_params = current_params
    return best_params, best_score


class BeamOptimizer(object):
    def __init__(self, evaluator: Evaluator) -> None:
        self._evaluator: Evaluator = evaluator
        bridge = evaluator.bridge()
        if not isinstance(bridge, BeamBridge):
            raise ValueError("Expecting a beam bridge")
        self._bridge: BeamBridge = bridge
        self._cs_type: type[CrossSection] = bridge.cross_section().__class__

    def load_criterion(self, params: dict[str, float]) -> float:
        self._bridge.cross_section(cross_section=self._cs_type(**params))
        return self._evaluator.maximum_load()[0]

    def optimize_cross_section(self) -> tuple[CrossSection, float]:
        cs = self._bridge.cross_section()
        kwargs = cs.kwargs()
        param_ranges = {name: (val * 0.5, val * 1.5, val * 0.1) for name, val in kwargs.items()}
        best_params, best_load = grid_search(param_ranges, lambda x: self.load_criterion(x))
        return self._cs_type(**best_params), best_load
