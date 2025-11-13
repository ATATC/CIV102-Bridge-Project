from abc import ABCMeta, abstractmethod
from math import pi
from typing import override, Literal, Sequence


class CrossSection(object, metaclass=ABCMeta):
    @abstractmethod
    def moment_of_inertia(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def centroid(self) -> tuple[float, float]:
        raise NotImplementedError

    @abstractmethod
    def width(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def height(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def area(self) -> float:
        raise NotImplementedError


class ArbitraryCrossSection(CrossSection):
    def __init__(self, moment_of_inertia: float, centroid: tuple[float, float], width: float, height: float,
                 area: float) -> None:
        self._moment_of_inertia: float = moment_of_inertia
        self._centroid: tuple[float, float] = centroid
        self._width: float = width
        self._height: float = height
        self._area: float = area

    @override
    def moment_of_inertia(self) -> float:
        return self._moment_of_inertia

    @override
    def centroid(self) -> tuple[float, float]:
        return self._centroid

    @override
    def width(self) -> float:
        return self._width

    @override
    def height(self) -> float:
        return self._height

    @override
    def area(self) -> float:
        return self._area


class RectangularCrossSection(CrossSection):
    def __init__(self, b: float, h: float) -> None:
        self.b: float = b
        self.h: float = h

    @override
    def moment_of_inertia(self) -> float:
        return self.b * self.h ** 3 / 12

    @override
    def centroid(self) -> tuple[float, float]:
        return self.b / 2, self.h / 2

    @override
    def width(self) -> float:
        return self.b

    @override
    def height(self) -> float:
        return self.h

    @override
    def area(self) -> float:
        return self.b * self.h


class CircularCrossSection(CrossSection):
    def __init__(self, r: float) -> None:
        self.r: float = r
        self.d: float = 2 * r

    @override
    def moment_of_inertia(self) -> float:
        return pi * self.d ** 4 / 64

    @override
    def centroid(self) -> tuple[float, float]:
        return self.r, self.r

    @override
    def width(self) -> float:
        return self.d

    @override
    def height(self) -> float:
        return self.d

    @override
    def area(self) -> float:
        return pi * self.r ** 2


class ComplexCrossSection(CrossSection):
    def __init__(self, basic_cross_sections: Sequence[tuple[CrossSection, float, float]]) -> None:
        """
        :param basic_cross_sections: [(cross_section, x_offset, y_offset)]
        """
        self.basic_cross_sections: list[tuple[CrossSection, float, float]] = list(basic_cross_sections)

    @override
    def width(self) -> float:
        farthest_cross_section = max(self.basic_cross_sections, key=lambda cs: cs[0].width() + cs[1])
        return farthest_cross_section[0].width() + farthest_cross_section[1]

    @override
    def height(self) -> float:
        farthest_cross_section = max(self.basic_cross_sections, key=lambda cs: cs[0].height() + cs[2])
        return farthest_cross_section[0].height() + farthest_cross_section[2]

    @override
    def moment_of_inertia(self) -> float:
        x_hat, y_hat = self.centroid()
        total_moment_of_inertia = 0
        for cs, x_offset, y_offset in self.basic_cross_sections:
            cx, cy = cs.centroid()
            d_squared = (x_hat - x_offset - cx) ** 2 + (y_hat - y_offset - cy) ** 2
            total_moment_of_inertia += cs.moment_of_inertia() + cs.area() * d_squared
        return total_moment_of_inertia

    @override
    def area(self) -> float:
        return sum(cs[0].area() for cs in self.basic_cross_sections)

    def centroid_along(self, axis: Literal[0, 1]) -> float:
        total = 0
        for cs, x_offset, y_offset in self.basic_cross_sections:
            offsets = (x_offset, y_offset)
            total += cs.area() * (cs.centroid()[axis] + offsets[axis])
        return total / self.area()

    @override
    def centroid(self) -> tuple[float, float]:
        return self.centroid_along(0), self.centroid_along(1)


class IBeam(ComplexCrossSection):
    def __init__(self, d: float, bf: float, t: float, bw: float) -> None:
        super().__init__([
            (RectangularCrossSection(bf, t), 0, 0),
            (RectangularCrossSection(bw, d - 2 * t), .5 * (bf - bw), t),
            (RectangularCrossSection(bf, t), 0, d - t),
        ])


if __name__ == "__main__":
    cross_section = ComplexCrossSection([
        (RectangularCrossSection(423, 43), 0, 0),
        (RectangularCrossSection(24, 847), 199.5, 43),
        (RectangularCrossSection(423, 43), 0, 890),
    ])
    # cross_section = IBeam(933, 423, 43, 24)
    print(cross_section.centroid())
    print(cross_section.area())
    print(cross_section.width())
    print(cross_section.height())
    print(cross_section.moment_of_inertia() * 1e-6)
