from os import PathLike

import numpy as np
import torch
from matplotlib import pyplot as plt

from bridger.material import Material
from bridger.prototype import Bridge
from bridger.utils import intervals


class Evaluator(object):
    def __init__(self, bridge: Bridge, material: Material, *, safety_factor_threshold: float = 1) -> None:
        self._bridge: Bridge = bridge
        self._safe_compressive_stress: float = material.compressive_strength
        self._safe_tensile_stress: float = material.tensile_strength
        self._safe_shear_stress: float = material.shear_strength
        self._safety_factor_threshold: float = safety_factor_threshold
        self._real_train_load: float = bridge.train_load()
        self._real_train_position: float = bridge.wheel_positions()[0]

    def bridge(self) -> Bridge:
        return self._bridge

    def clear_position(self) -> None:
        self._bridge.place_the_train(0)

    def clear_train_load(self) -> None:
        self._bridge.train_load(train_load=1)

    def reset_position(self) -> None:
        self._bridge.place_the_train(self._real_train_position)

    def reset_train_load(self) -> None:
        self._bridge.train_load(train_load=self._real_train_load)

    def n(self, *, dx: float = 1) -> int:
        wp = self._bridge.wheel_positions()
        return int((self._bridge.length() + wp[0] - wp[-1] / dx))

    def pass_the_train(self, *, dx: float = 1) -> tuple[list[float], list[float], list[float]]:
        self.clear_position()
        safety_factors_compression = []
        safety_factors_tension = []
        safety_factors_shear = []
        for _ in range(self.n(dx=dx)):
            c, t = self._bridge.safety_factor((self._safe_compressive_stress, self._safe_tensile_stress))
            safety_factors_compression.append(c)
            safety_factors_tension.append(t)
            s = self._bridge.shear_safety_factor(self._safe_shear_stress)
            safety_factors_shear.append(s)
            self._bridge.move_the_train(dx)
        self.reset_position()
        return safety_factors_compression, safety_factors_tension, safety_factors_shear

    def dead_zones(self, safety_factors_compression: list[float], safety_factors_tension: list[float],
                   safety_factors_shear: list[float], *, dx: float = 1) -> list[tuple[float, float]]:
        c, t, s = np.array(safety_factors_compression), np.array(safety_factors_tension), np.array(safety_factors_shear)
        return intervals((c < self._safety_factor_threshold) | (t < self._safety_factor_threshold) | (
                s < self._safety_factor_threshold), dx=dx)

    def plot_safety_factors(self, *, dx: float = 1, save_as: str | PathLike[str] | None = None) -> None:
        c, t, s = self.pass_the_train(dx=dx)
        plt.figure(figsize=(12, 6))
        plt.plot(c, "orange")
        plt.plot(t, "purple")
        plt.plot(s, "blue")
        plt.hlines(self._safety_factor_threshold, 0, self.n(dx=dx), "red")
        plt.grid(True)
        plt.title("Safety Factor on Various Positions")
        plt.xlabel("Train Position (mm)")
        plt.ylabel("Safety Factor")
        plt.legend(("Compressive", "Tensile", "Shear", "Failure Threshold"))
        if save_as:
            plt.savefig(save_as)
        plt.show()
        plt.close()

    def maximum_load(self) -> tuple[float, str]:
        self.clear_train_load()
        c, t = self._bridge.safety_factor((self._safe_compressive_stress, self._safe_tensile_stress))
        s = self._bridge.shear_safety_factor(self._safe_shear_stress)
        safety_factors = {"compression": c, "tension": t, "shear": s}
        cause = min(safety_factors.keys(), key=lambda x: safety_factors[x])
        return safety_factors[cause], cause
