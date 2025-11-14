from abc import ABCMeta, abstractmethod
from os import PathLike
from typing import Sequence, override

import numpy as np
from matplotlib import pyplot as plt

from bridger.cross_section import CrossSection


class Bridge(object, metaclass=ABCMeta):
    def __init__(self, train_load: float, wheel_positions: Sequence[float], load_distribution: Sequence[float]) -> None:
        self._train_load: float = train_load
        self._wheel_positions: np.ndarray = np.array(wheel_positions)
        self._load_distribution: np.ndarray = np.array(load_distribution) / sum(load_distribution)
        self._loads: np.ndarray = self._load_distribution * train_load

    @abstractmethod
    def length(self) -> float:
        raise NotImplementedError

    def train_load(self, *, train_load: float | None = None) -> float | None:
        if train_load is None:
            return self._train_load
        self._train_load = train_load
        self._loads = self._load_distribution * train_load

    def wheel_positions(self) -> list[float]:
        return list(self._wheel_positions)

    def load_distribution(self) -> list[float]:
        return list(self._load_distribution)

    def loads(self) -> list[float]:
        return list(self._loads)

    def place_the_train(self, start: float) -> None:
        self.move_the_train(start - self._wheel_positions[0])

    def move_the_train(self, step_size: float) -> None:
        self._wheel_positions += step_size

    def add_train_load(self, delta_load: float) -> None:
        self.train_load(train_load=self._train_load + delta_load)

    @abstractmethod
    def ultimate_stress(self) -> tuple[float, float]:
        """
        :return: (compressive, tensile)
        """
        raise NotImplementedError

    @abstractmethod
    def ultimate_shear_stress(self) -> float:
        raise NotImplementedError

    def safety_factor(self, safe_stress: tuple[float, float]) -> tuple[float, float]:
        """
        :param safe_stress: (compressive, tensile)
        :return: (compressive, tensile)
        """
        compressive, tensile = self.ultimate_stress()
        return safe_stress[0] / compressive, safe_stress[1] / tensile

    def shear_safety_factor(self, safe_stress: float) -> float:
        return safe_stress / self.ultimate_shear_stress()


class BeamBridge(Bridge):
    def __init__(self, train_load: float, cross_section: CrossSection, *, length: float = 1200,
                 wheel_positions: Sequence[float] = (172, 348, 512, 688, 852, 1028),
                 load_distribution: Sequence[float] = (1.35, 1.35, 1, 1, 1, 1)) -> None:
        super().__init__(train_load, wheel_positions, load_distribution)
        self._length: float = length
        self._cross_section: CrossSection = cross_section

    @override
    def length(self) -> float:
        return self._length

    def x_linespace(self, *, dx: float = 1) -> np.ndarray:
        n = self._length / dx
        int_n = int(n)
        if int_n != n:
            raise ValueError("dx must divide length evenly")
        return np.linspace(0, self._length, int_n)

    def reaction_forces(self) -> tuple[float, float]:
        r_end = float((self._wheel_positions * self._loads).sum()) / self._length
        return self._train_load - r_end, r_end

    def shear_forces(self) -> list[float]:
        r_start, r_end = self.reaction_forces()
        v = [r_start]
        for p in self._loads:
            v.append(v[-1] - p)
        v.append(v[-1] + r_end)
        return v

    def expanded_shear_forces(self, x: np.ndarray) -> np.ndarray:
        v = np.zeros_like(x)
        v0 = self.shear_forces()
        v[:] = v0[0]
        for i, pos in enumerate(self._wheel_positions):
            v[x > pos] = v0[i + 1]
        v[x > self._length] = v0[-1]
        return v

    def plot_sfd(self, *, dx: float = 1, save_as: str | PathLike[str] | None = None) -> None:
        x = self.x_linespace(dx=dx)
        v = self.expanded_shear_forces(x)
        plt.figure(figsize=(12, 6))
        plt.plot(x, v)
        plt.grid(True)
        plt.title("Shear Force Diagram")
        plt.xlabel("Position (mm)")
        plt.ylabel("Shear Force (N)")
        if save_as:
            plt.savefig(save_as)
        plt.show()
        plt.close()

    def bending_moments(self) -> list[float]:
        v = self.shear_forces()
        m = [0]
        positions = [0, *self._wheel_positions, self._length]
        for i in range(1, len(v)):
            m.append(m[-1] + v[i - 1] * (positions[i] - positions[i - 1]))
        return m

    def expanded_bending_moments(self, x: np.ndarray) -> np.ndarray:
        v = self.expanded_shear_forces(x)
        m = np.zeros_like(x)
        for i in range(1, len(x)):
            m[i] = m[i - 1] + v[i - 1] * (x[i] - x[i - 1])
        return m

    def plot_bmd(self, *, dx: float = 1, save_as: str | PathLike[str] | None = None) -> None:
        x = self.x_linespace(dx=dx)
        v = self.expanded_bending_moments(x) * 1e-3
        plt.figure(figsize=(12, 6))
        plt.plot(x, v)
        plt.grid(True)
        plt.title("Bending Moment Diagram")
        plt.xlabel("Position (mm)")
        plt.ylabel("Bending Moment (Nm)")
        if save_as:
            plt.savefig(save_as)
        plt.show()
        plt.close()

    @override
    def ultimate_stress(self) -> tuple[float, float]:
        m = self.bending_moments()
        m_max = max(abs(max(m)), abs(min(m)))
        i = self._cross_section.moment_of_inertia()
        h = self._cross_section.height()
        return m_max * (h - self._cross_section.centroid()[1]) / i, m_max * self._cross_section.centroid()[1] / i

    @override
    def ultimate_shear_stress(self) -> float:
        cs = self._cross_section
        v = self.shear_forces()
        v_max = max(abs(max(v)), abs(min(v)))
        return v_max * cs.q_max() / cs.moment_of_inertia() / cs.min_width()
