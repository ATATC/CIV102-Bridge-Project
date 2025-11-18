from os import PathLike
from typing import Sequence

import numpy as np
from matplotlib import pyplot as plt

from bridger.material import Material
from bridger.prototype import Bridge
from bridger.utils import intervals


class Evaluator(object):
    def __init__(self, bridge: Bridge, material: Material, *, safety_factor_threshold: float = 1) -> None:
        self._bridge: Bridge = bridge
        self._material: Material = material
        self._safety_factor_threshold: float = safety_factor_threshold
        self._real_train_load: float = bridge.train_load()
        self._real_train_position: float = bridge.wheel_positions()[0]

    def bridge(self) -> Bridge:
        return self._bridge

    def clear_train_position(self) -> None:
        self._bridge.place_the_train(0)

    def clear_train_load(self) -> None:
        self._bridge.train_load(train_load=1)

    def reset_train_position(self) -> None:
        self._bridge.place_the_train(self._real_train_position)

    def reset_train_load(self) -> None:
        self._bridge.train_load(train_load=self._real_train_load)

    def n(self, *, dx: float = 1) -> int:
        wp = self._bridge.wheel_positions()
        return int((self._bridge.length() + wp[0] - wp[-1] / dx))

    def pass_the_train(self, *, dx: float = 1) -> tuple[list[float], list[float], list[float], list[float], list[
        float], list[float]]:
        self.clear_train_position()
        sfc, sft, sfs, sfg, sffb, sfsb = [], [], [], [], [], []
        for _ in range(self.n(dx=dx)):
            c, t = self._bridge.safety_factor((self._material.compressive_strength, self._material.tensile_strength))
            sfc.append(c)
            sft.append(t)
            sfs.append(self._bridge.shear_safety_factor(self._material.shear_strength))
            sfg.append(self._bridge.glue_safety_factor(self._material.glue_strength))
            sffb.append(self._bridge.flexural_buckling_safety_factor(self._bridge.safe_flexural_buckling_stress(
                self._material
            )))
            sfsb.append(self._bridge.shear_buckling_safety_factor(self._bridge.safe_shear_buckling_stress(
                self._material
            )))
            self._bridge.move_the_train(dx)
        self.reset_train_position()
        return sfc, sft, sfs, sfg, sffb, sfsb

    def dead_zones(self, c: list[float], t: list[float], s: list[float], g: list[float], fb: list[float],
                   sb: list[float], *, dx: float = 1) -> list[tuple[
        float, float]]:
        c, t, s, g, fb, sb = (
            np.array(c), np.array(t), np.array(s), np.array(g), np.array(fb), np.array(sb)
        )
        sft = self._safety_factor_threshold
        return intervals((c < sft) | (t < sft) | (s < sft) | (g < sft) | (fb < sft) | (sb < sft), dx=dx)

    def plot_safety_factors(self, *, dx: float = 1, save_as: str | PathLike[str] | None = None,
                            colors: Sequence[str | None] = ("blue", "purple", "cyan", "pink")) -> None:
        safety_factors = self.pass_the_train(dx=dx)
        plt.figure(figsize=(12, 6))
        names = ("Compression", "Tension", "Shear", "Glue")
        legends = []
        for i, color in enumerate(colors):
            if not color:
                continue
            legends.append(names[i])
            plt.plot(safety_factors[i], color)
        plt.hlines(self._safety_factor_threshold, 0, self.n(dx=dx), "red")
        plt.grid(True)
        plt.title("Safety Factor on Various Positions")
        plt.xlabel("Train Position (mm)")
        plt.ylabel("Safety Factor")
        legends.append("Failure Threshold")
        plt.legend(legends)
        if save_as:
            plt.savefig(save_as)
        plt.show()
        plt.close()

    def maximum_load(self, *, dx: float = 1) -> tuple[float, str]:
        """
        Assuming that safety factors are inversely proportional to the load, define a linear system FOS(P)=1/f(P). We
        want to find P_max that gives FOS_min, which is 1: FOS(P_max)=1/f(P_max)=1 and FOS(1)=1/f(1). Since
        df(P)/dP is a constant, we have f(P_max)/P_max=f(1)/1. Substitute f(P_max)=1 and f(1)=1/FOS(1) into it:
        1/P_max=1/FOS(1) -> P_max=FOS(1). Therefore, the maximum load is just the smallest safety factor when we apply
        a virtual load of one Newton.
        :return: (maximum load, cause)
        """
        self.clear_train_load()
        c, t, s, g, fb, sb = self.pass_the_train(dx=dx)
        safety_factors = {
            "compression": min(c), "tension": min(t), "shear": min(s), "glue": min(g), "flexural buckling": min(fb),
            "shear buckling": min(sb)
        }
        cause = min(safety_factors.keys(), key=lambda x: safety_factors[x])
        self.reset_train_load()
        return safety_factors[cause], cause
