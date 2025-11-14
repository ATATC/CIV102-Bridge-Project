import numpy as np
from matplotlib import pyplot as plt

from bridge.prototype import Bridge
from bridge.utils import intervals


class Evaluator(object):
    def __init__(self, bridge: Bridge, safe_compressive_stress: float, safe_tensile_stress: float,
                 safe_shear_stress: float, *, safety_factor_threshold: float = 1) -> None:
        self._bridge: Bridge = bridge
        self._safe_compressive_stress: float = safe_compressive_stress
        self._safe_tensile_stress: float = safe_tensile_stress
        self._safe_shear_stress: float = safe_shear_stress
        self._safety_factor_threshold: float = safety_factor_threshold
        self._real_train_mass: float = bridge.train_mass()
        self._real_train_position: float = bridge.wheel_positions()[0]

    def bridge(self) -> Bridge:
        return self._bridge

    def set_to_minimal(self) -> None:
        self._bridge.train_mass(train_mass=1)
        self._bridge.move_the_train(-self._real_train_position)

    def reset(self) -> None:
        self._bridge.train_mass(train_mass=self._real_train_mass)
        self._bridge.move_the_train(self._real_train_position)

    def n(self, *, dx: float = 1) -> int:
        return int((self._bridge.length() - self._bridge.wheel_positions()[-1] / dx))

    def pass_the_train(self, *, dx: float = 1) -> tuple[list[float], list[float], list[float]]:
        safety_factors_compressive, safety_factors_tensile, safety_factors_shear = [], [], []
        for p in range(self.n(dx=dx)):
            self._bridge.move_the_train(dx)
            c, t = self._bridge.safety_factor((self._safe_compressive_stress, self._safe_tensile_stress))
            safety_factors_compressive.append(c)
            safety_factors_tensile.append(t)
            s = self._bridge.shear_safety_factor(self._safe_shear_stress)
            safety_factors_shear.append(s)
        return safety_factors_compressive, safety_factors_tensile, safety_factors_shear

    def dead_zones(self, *, dx: float = 1) -> list[tuple[float, float]]:
        c, t, s = self.pass_the_train(dx=dx)
        c, t, s = np.array(c), np.array(t), np.array(s)
        return intervals((c < self._safety_factor_threshold) | (t < self._safety_factor_threshold) | (
                s < self._safety_factor_threshold), dx=dx)

    def plot_safety_factors(self, *, safety_factor_threshold: float = 1, dx: float = 1) -> None:
        c, t, s = self.pass_the_train(dx=dx)
        plt.plot(c, "orange")
        plt.plot(t, "purple")
        plt.plot(s, "blue")
        plt.hlines(safety_factor_threshold, 0, self.n(dx=dx), "red")
        plt.grid(True)
        plt.title("Safety Factor on Various Positions")
        plt.xlabel("Train Position (mm)")
        plt.ylabel("Safety Factor")
        plt.legend(("Compressive", "Tensile", "Shear", "Failure Threshold"))
        plt.savefig("safety_factors.png")
        plt.show()
        plt.close()

    def maximum_load(self, *, dx: float = 1) -> float:
        self.set_to_minimal()
        delta_mass = 1000
        while delta_mass > 10:
            print(self._bridge.train_mass())
            dead_zones = self.dead_zones(dx=dx)
            if len(dead_zones) > 0:
                if self._bridge.train_mass() < delta_mass:
                    return 0
                delta_mass *= .5
                self._bridge.add_train_mass(-delta_mass)
            else:
                delta_mass *= 2
                self._bridge.add_train_mass(delta_mass)
        try:
            return self._bridge.train_mass()
        finally:
            self.reset()
