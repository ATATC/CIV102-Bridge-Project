from abc import ABCMeta, abstractmethod
from os import PathLike
from typing import Sequence, override, Callable

import numpy as np
from matplotlib import pyplot as plt

from bridger.material import Material
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
        return None

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

    @abstractmethod
    def ultimate_glue_stress(self) -> float | None:
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

    def glue_safety_factor(self, safe_stress: float) -> float:
        applied_stress = self.ultimate_glue_stress()
        return safe_stress / applied_stress if applied_stress else float("inf")

    @abstractmethod
    def safe_flexural_buckling_stress(self, material: Material, *, horizontal: bool = False) -> float:
        raise NotImplementedError

    @abstractmethod
    def safe_shear_buckling_stress(self, material: Material) -> float:
        raise NotImplementedError

    def flexural_buckling_safety_factor(self, safe_stress: float) -> float:
        return safe_stress / self.ultimate_stress()[0]

    def shear_buckling_safety_factor(self, safe_stress: float) -> float:
        return safe_stress / self.ultimate_shear_stress()


class BeamBridge(Bridge):
    def __init__(self, train_load: float, cross_section: CrossSection, *, length: float = 1200,
                 wheel_positions: Sequence[float] = (172, 348, 512, 688, 852, 1028),
                 load_distribution: Sequence[float] = (1.35, 1.35, 1, 1, 1, 1)) -> None:
        if length < max(wheel_positions):
            raise ValueError("Length must be at least the length of the train")
        super().__init__(train_load, wheel_positions, load_distribution)
        self._length: float = length
        self._v_cross_section: CrossSection = cross_section

    def cross_section(self, *, cross_section: CrossSection | None = None) -> CrossSection | None:
        if cross_section is None:
            return self._v_cross_section
        self._v_cross_section = cross_section
        return None

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
            v.append(float(v[-1] - p))
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
        positions = [0, *self._wheel_positions, self._length]
        m = [positions[0]]
        for i in range(1, len(v)):
            m.append(float(m[-1] + v[i - 1] * (positions[i] - positions[i - 1])))
        return m

    def expanded_bending_moments(self, x: np.ndarray) -> np.ndarray:
        v = self.expanded_shear_forces(x)
        m = np.zeros_like(x)
        for i in range(1, len(x)):
            m[i] = m[i - 1] + v[i - 1] * (x[i] - x[i - 1])
        return m

    def plot_bmd(self, *, dx: float = 1, save_as: str | PathLike[str] | None = None) -> None:
        x = self.x_linespace(dx=dx)
        m = self.expanded_bending_moments(x) * 1e-3
        plt.figure(figsize=(12, 6))
        plt.plot(x, m)
        plt.grid(True)
        plt.title("Bending Moment Diagram")
        plt.xlabel("Position (mm)")
        plt.ylabel("Bending Moment (Nm)")
        if save_as:
            plt.savefig(save_as)
        plt.show()
        plt.close()

    def plot_curvature_diagram(self, material: Material, *, dx: float = 1,
                               save_as: str | PathLike[str] | None = None) -> None:
        x = self.x_linespace(dx=dx)
        m = self.expanded_bending_moments(x) * 1e-3
        phi = m / material.modulus / self._v_cross_section.moment_of_inertia()
        plt.figure(figsize=(12, 6))
        plt.plot(x, phi)
        plt.grid(True)
        plt.title("Curvature Diagram")
        plt.xlabel("Position (mm)")
        plt.ylabel("Curvature (mm-1)")
        if save_as:
            plt.savefig(save_as)
        plt.show()
        plt.close()

    @override
    def ultimate_stress(self) -> tuple[float, float]:
        m = self.bending_moments()
        m_max = max(abs(max(m)), abs(min(m)))
        i = self._v_cross_section.moment_of_inertia()
        h = self._v_cross_section.height()
        y_bar = self._v_cross_section.centroid()[1]
        return m_max * (h - y_bar) / i, m_max * y_bar / i

    @override
    def ultimate_shear_stress(self) -> float:
        cs = self._v_cross_section
        v = self.shear_forces()
        v_max = max(abs(max(v)), abs(min(v)))
        return v_max * cs.q_max() / cs.moment_of_inertia() / cs.min_width()

    @override
    def ultimate_glue_stress(self) -> float | None:
        cs = self._v_cross_section
        v = self.shear_forces()
        v_max = max(abs(max(v)), abs(min(v)))
        kwargs = cs.kwargs()
        if "glue_y" in kwargs and "glue_b" in kwargs:
            return v_max * cs.q(kwargs["glue_y"]) / cs.moment_of_inertia() / kwargs["glue_b"]
        return None

    @override
    def safe_flexural_buckling_stress(self, material: Material, *, horizontal: bool = False) -> float:
        return self._v_cross_section.safe_flexural_buckling_stress(material, horizontal=horizontal)

    @override
    def safe_shear_buckling_stress(self, material: Material) -> float:
        return self._v_cross_section.safe_shear_buckling_stress(material)


type VaryingCrossSection = Callable[[float], CrossSection]


class NonUniformBeamBridge(BeamBridge):
    def __init__(self, train_load: float, v_cross_section: VaryingCrossSection, *, length: float = 1200,
                 wheel_positions: Sequence[float] = (172, 348, 512, 688, 852, 1028),
                 load_distribution: Sequence[float] = (1.35, 1.35, 1, 1, 1, 1)) -> None:
        super().__init__(train_load, v_cross_section(0), length=length, wheel_positions=wheel_positions,
                         load_distribution=load_distribution)
        self._v_cross_section: VaryingCrossSection = v_cross_section

    @override
    def cross_section(self, *, cross_section: CrossSection | None = None) -> CrossSection | None:
        raise NotImplementedError

    def v_cross_section(self, *, v_cross_section: VaryingCrossSection | None = None) -> VaryingCrossSection | None:
        if v_cross_section is None:
            return self._v_cross_section
        self._v_cross_section = v_cross_section
        return None

    def cross_section_at(self, x: float) -> CrossSection:
        return self._v_cross_section(x)

    @override
    def ultimate_stress(self) -> tuple[float, float]:
        x = self.x_linespace()
        m = self.expanded_bending_moments(x)
        max_comp = 0
        max_tens = 0
        for xi, mi in zip(x, m):
            cs = self.cross_section_at(xi)
            i = cs.moment_of_inertia()
            h = cs.height()
            y_bar = cs.centroid()[1]
            sigma_top = abs(mi) * (h - y_bar) / i
            sigma_bottom = abs(mi) * y_bar / i
            if sigma_top > max_comp:
                max_comp = sigma_top
            if sigma_bottom > max_tens:
                max_tens = sigma_bottom
        return max_comp, max_tens

    @override
    def ultimate_shear_stress(self) -> float:
        x = self.x_linespace()
        v = self.expanded_shear_forces(x)
        tau_max = 0
        for xi, vi in zip(x, v):
            cs = self.cross_section_at(xi)
            tau = abs(vi) * cs.q_max() / cs.moment_of_inertia() / cs.min_width()
            if tau > tau_max:
                tau_max = tau
        return tau_max

    @override
    def ultimate_glue_stress(self) -> float | None:
        x = self.x_linespace(dx=1)
        v = self.expanded_shear_forces(x)
        tau_glue_max: float | None = None
        for xi, vi in zip(x, v):
            cs = self.cross_section_at(xi)
            kwargs = cs.kwargs()
            if "glue_y" in kwargs and "glue_b" in kwargs:
                tau = abs(vi) * cs.q(kwargs["glue_y"]) / cs.moment_of_inertia() / kwargs["glue_b"]
                if tau_glue_max is None or tau > tau_glue_max:
                    tau_glue_max = tau
        return tau_glue_max

    @override
    def safe_flexural_buckling_stress(self, material: Material, *, horizontal: bool = False) -> float:
        x = self.x_linespace(dx=1)
        safe_values = [
            self.cross_section_at(xi).safe_flexural_buckling_stress(material, horizontal=horizontal)
            for xi in x
        ]
        return min(safe_values)

    @override
    def safe_shear_buckling_stress(self, material: Material) -> float:
        x = self.x_linespace(dx=1)
        safe_values = [
            self.cross_section_at(xi).safe_shear_buckling_stress(material)
            for xi in x
        ]
        return min(safe_values)
