from typing import Callable, Sequence

import numpy as np
from scipy.optimize import differential_evolution
from rich.progress import Progress, SpinnerColumn

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
                progress.update(task, description=f"[green]Searching... ({best_score:.2f} N)")
            progress.update(task, advance=1)
        progress.update(task, description="Finished")
    return best_params, best_score


def advanced_grid_search(param_ranges: dict[str, tuple[float, float, float]],
                         criterion: Callable[[dict[str, float]], float], constraint: Constraint | None, *,
                         levels: int = 4, refinement: int = 4) -> tuple[dict[str, float], float]:
    if levels < 1:
        raise ValueError("levels must be >= 1")
    if refinement < 2:
        raise ValueError("refinement must be >= 2")
    global_ranges = param_ranges
    overall_best_params: dict[str, float] = {}
    overall_best_score: float = float("-inf")
    for level in range(levels):
        level_param_ranges: dict[str, tuple[float, float, float]] = {}
        for name, (g_start, g_end, final_step) in global_ranges.items():
            if level == levels - 1:
                step = final_step
            else:
                power = (levels - 1) - level
                step = final_step * (refinement ** power)
            if not overall_best_params:
                start = g_start
                end = g_end
            else:
                center = overall_best_params[name]
                span = refinement * step
                start = max(g_start, center - span)
                end = min(g_end, center + span)
                if start >= end:
                    start = max(g_start, min(center, g_end))
                    end = start
            level_param_ranges[name] = (start, end, step)
        best_params_level, best_score_level = grid_search(level_param_ranges, criterion, constraint)
        if best_score_level > overall_best_score:
            overall_best_score = best_score_level
            overall_best_params = best_params_level
    return overall_best_params, overall_best_score


def de_search(param_ranges: dict[str, tuple[float, float, float]], criterion: Callable[[dict[str, float]], float],
              constraint: Constraint | None, **kwargs) -> tuple[dict[str, float], float]:
    param_names: list[str] = list(param_ranges.keys())
    grids: list[np.ndarray] = []
    bounds: list[tuple[float, float]] = []
    for (start, end, step) in param_ranges.values():
        values = np.arange(start, end + step, step, dtype=float)
        grids.append(values)
        bounds.append((0, len(values) - 1))

    def vector_to_params(x: np.ndarray) -> dict[str, float]:
        indices = []
        for i, xi in enumerate(x):
            grid = grids[i]
            idx = int(np.round(xi))
            if idx < 0:
                idx = 0
            elif idx >= len(grid):
                idx = len(grid) - 1
            indices.append(idx)
        return dict(zip(param_names, [grids[i][idx] for i, idx in enumerate(indices)]))

    def objective(x: np.ndarray) -> float:
        current_params = vector_to_params(x)
        if constraint:
            current_params = constraint(current_params)
            if current_params is None:
                return float("inf")
        return -criterion(current_params)

    result = differential_evolution(objective, bounds=bounds, polish=True, **kwargs)
    best_params = vector_to_params(result.x)
    if constraint:
        constrained = constraint(best_params)
        if constrained is not None:
            best_params = constrained
    best_score = criterion(best_params)
    return best_params, best_score


class BeamOptimizer(object):
    def __init__(self, evaluator: Evaluator) -> None:
        self._evaluator: Evaluator = evaluator
        bridge = evaluator.bridge()
        if not isinstance(bridge, BeamBridge):
            raise ValueError("Expecting a beam bridge")
        self._bridge: BeamBridge = bridge

    def load_criterion(self, params: dict[str, float]) -> float:
        self._bridge.cross_section(cross_section=self._bridge.cross_section().__class__(**params))
        return self._evaluator.maximum_load()[0]

    def optimize_cross_section(self, param_ranges: dict[str, tuple[float, float, float]], *,
                               constraint: Constraint | None = None, use_grid_search: bool = False, **kwargs) -> tuple[
        dict[str, float], float]:
        """
        :param param_ranges: parameter ranges like (start, end, step)
        :param constraint: a function that fills the dependent variables or returns None if the parameters are not valid
        :param use_grid_search: whether to use a grid search instead of differential evolution search
        :return: (best params, maximum load)
        """
        return (advanced_grid_search if use_grid_search else de_search)(
            param_ranges, self.load_criterion, constraint, **kwargs
        )
