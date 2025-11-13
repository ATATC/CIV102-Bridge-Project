from typing import Sequence

import numpy as np
from matplotlib import pyplot as plt

from bridge.cross_section import CrossSection


class Bridge(object):
    def __init__(self, length: float, train_mass: float, cross_section: CrossSection, *, num_cars: int = 3,
                 wheel_positions: Sequence[float] = (172, 348, 512, 688, 852, 1028),
                 mass_distribution: Sequence[float] = (1.35, 1.35, 1, 1, 1, 1)) -> None:
        self.length: float = length
        self.train_mass: float = train_mass
        self.cross_section: CrossSection = cross_section
        self.num_cars: int = num_cars
        self.wheel_positions: np.ndarray = np.array(wheel_positions)
        self.mass_distribution: np.ndarray = np.array(mass_distribution) / sum(mass_distribution)
        self.loads: np.ndarray = self.mass_distribution * train_mass

    def x_linespace(self, *, dx: float = 1) -> np.ndarray:
        n = self.length / dx
        int_n = int(n)
        if int_n != n:
            raise ValueError("dx must divide length evenly")
        return np.linspace(0, self.length, int_n)

    def reaction_forces(self) -> tuple[float, float]:
        r_end = float((self.wheel_positions * self.loads).sum()) / self.length
        return self.train_mass - r_end, r_end

    def shear_forces(self) -> list[float]:
        r_start, r_end = self.reaction_forces()
        v = [r_start]
        for p in self.loads:
            v.append(v[-1] - p)
        v.append(v[-1] + r_end)
        return v

    def expanded_shear_forces(self, x: np.ndarray) -> np.ndarray:
        v = np.zeros_like(x)
        v0 = self.shear_forces()
        v[:] = v0[0]
        for i, pos in enumerate(self.wheel_positions):
            v[x > pos] = v0[i + 1]
        v[x > self.length] = v0[-1]
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
        positions = [0, *self.wheel_positions, self.length]
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

    def ultimate_stress(self) -> tuple[float, float]:
        """
        :return: (sigma_top, sigma_bot)
        """
        m = self.bending_moments()
        m_max = max(max(m), -min(m))
        i = self.cross_section.moment_of_inertia()
        h = self.cross_section.height()
        return m_max * (h - self.cross_section.centroid()) / i, m_max * self.cross_section.centroid() / i

    def safety_factor(self, safe_stress: tuple[float, float]) -> tuple[float, float]:
        sigma_top, sigma_bot = self.ultimate_stress()
        return safe_stress[0] / sigma_top, safe_stress[1] / sigma_bot

    def move_the_train(self, step_size: float) -> None:
        self.wheel_positions += step_size
