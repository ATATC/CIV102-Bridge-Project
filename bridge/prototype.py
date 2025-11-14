from typing import Sequence, override
from abc import ABCMeta, abstractmethod

import numpy as np
from matplotlib import pyplot as plt

from bridge.cross_section import CrossSection


class Bridge(object, metaclass=ABCMeta):
    def __init__(self, train_mass: float, wheel_positions: Sequence[float], mass_distribution: Sequence[float]) -> None:
        self._train_mass: float = train_mass
        self._wheel_positions: np.ndarray = np.array(wheel_positions)
        self._mass_distribution: np.ndarray = np.array(mass_distribution) / sum(mass_distribution)
        self._loads: np.ndarray = self._mass_distribution * train_mass

    @abstractmethod
    def length(self) -> float:
        raise NotImplementedError

    def train_mass(self, *, train_mass: float | None = None) -> float | None:
        if train_mass is None:
            return self._train_mass
        self._train_mass = train_mass
        self._loads = self._mass_distribution * train_mass

    def wheel_positions(self) -> list[float]:
        return list(self._wheel_positions)

    def mass_distribution(self) -> list[float]:
        return list(self._mass_distribution)

    def loads(self) -> list[float]:
        return list(self._loads)

    def move_the_train(self, step_size: float) -> None:
        self._wheel_positions += step_size

    def add_train_mass(self, delta_mass: float) -> None:
        self._train_mass += delta_mass

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
    def __init__(self, train_mass: float, cross_section: CrossSection, *, length: float = 1200,
                 wheel_positions: Sequence[float] = (172, 348, 512, 688, 852, 1028),
                 mass_distribution: Sequence[float] = (1.35, 1.35, 1, 1, 1, 1)) -> None:
        super().__init__(train_mass, wheel_positions, mass_distribution)
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
        return self._train_mass - r_end, r_end

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

    def sfd(self, *, dx: float = 1) -> None:
        x = self.x_linespace(dx=dx)
        v = self.expanded_shear_forces(x)
        plt.figure(figsize=(12, 6))
        plt.plot(x, v)
        plt.grid(True)
        plt.title("Shear Force Diagram")
        plt.xlabel("Position (mm)")
        plt.ylabel("Shear Force (N)")
        plt.show()

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

    def bmd(self, *, dx: float = 1) -> None:
        x = self.x_linespace(dx=dx)
        v = self.expanded_bending_moments(x) * 1e-3
        plt.figure(figsize=(12, 6))
        plt.plot(x, v)
        plt.grid(True)
        plt.title("Bending Moment Diagram")
        plt.xlabel("Position (mm)")
        plt.ylabel("Bending Moment (Nm)")
        plt.show()

    @override
    def ultimate_stress(self) -> tuple[float, float]:
        m = self.bending_moments()
        m_max = max(max(m), -min(m))
        i = self._cross_section.moment_of_inertia()
        h = self._cross_section.height()
        return m_max * (h - self._cross_section.centroid()[1]) / i, m_max * self._cross_section.centroid()[1] / i

    @override
    def ultimate_shear_stress(self) -> float:
        cs = self._cross_section
        return max(self.shear_forces()) * cs.q_max() / cs.moment_of_inertia() / cs.min_width()
