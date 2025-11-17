from typing import Callable, Sequence

import numpy as np
from rich.progress import Progress, SpinnerColumn

from bridger.cross_section import CrossSection
from bridger.prototype import BeamBridge
from bridger.evaluation import Evaluator


type Constraint = Callable[[dict[str, float]], dict[str, float] | None]


def grid_search(param_ranges: dict[str, tuple[float, float, float]],
                criterion: Callable[[dict[str, float]], float],
                constraint: Constraint | None) -> tuple[dict[str, float], float]:
    best_params = {}
    best_score = 0
    param_values = []
    param_names = []
    for name, (start, end, step) in param_ranges.items():
        param_names.append(name)
        param_values.append(np.arange(start, end + step, step))
    with Progress(*Progress.get_default_columns(), SpinnerColumn()) as progress:
        param_space = np.array(np.meshgrid(*param_values)).T.reshape(-1, len(param_names))
        task = progress.add_task("[green]Searching...", total=len(param_space))
        for params in param_space:
            current_params = dict(zip(param_names, params))
            if constraint:
                current_params = constraint(current_params)
                if current_params is None:
                    progress.update(task, advance=1)
                    continue
            score = criterion(current_params)
            if score > best_score:
                best_score = score
                best_params = current_params
                progress.update(task, description=f"[green]Best score: {best_score:.2f}")
            progress.update(task, advance=1)
        progress.update(task, description="Finished")
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

    def optimize_cross_section(self, param_ranges: dict[str, tuple[float, float, float]], *,
                               independent_params: Sequence[str] | None = None,
                               constraint: Constraint | None = None) -> tuple[CrossSection, float]:
        """
        :param param_ranges: parameter ranges like (start, end, step)
        :param independent_params: names of the independent variables
        :param constraint: a function that fills the dependent variables or returns None if the parameters are not valid
        :return: (best cross-section, maximum load)
        """
        cs = self._bridge.cross_section()
        kwargs = cs.kwargs()
        if independent_params:
            for key in kwargs.copy().keys():
                if key not in independent_params:
                    kwargs.pop(key)
        best_params, best_load = grid_search(param_ranges, lambda x: self.load_criterion(x), constraint)
        return self._cs_type(**best_params), best_load
