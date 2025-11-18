from abc import ABCMeta, abstractmethod
from math import pi
from typing import override, Literal, Sequence, Self


class CrossSection(object, metaclass=ABCMeta):
    def __init__(self, **kwargs: float) -> None:
        self._kwargs: dict[str, float] = kwargs

    def kwargs(self) -> dict[str, float]:
        return self._kwargs

    @abstractmethod
    def moment_of_inertia(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def centroid(self) -> tuple[float, float]:
        """
        :return: (x_bar, y_bar)
        """
        raise NotImplementedError

    @abstractmethod
    def width(self) -> float:
        raise NotImplementedError

    def min_width(self) -> float:
        return self.width()

    @abstractmethod
    def height(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def area(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def area_above(self, y: float) -> float:
        raise NotImplementedError

    @abstractmethod
    def q(self, y: float) -> float:
        raise NotImplementedError

    def q_max(self) -> float:
        return self.q(self.centroid()[1])

    @abstractmethod
    def sub_above(self, y: float) -> Self:
        raise NotImplementedError


class RectangularCrossSection(CrossSection):
    def __init__(self, b: float, h: float) -> None:
        super().__init__(b=b, h=h)
        self.b: float = b
        self.h: float = h

    @override
    def moment_of_inertia(self) -> float:
        return self.b * self.h ** 3 / 12

    @override
    def centroid(self) -> tuple[float, float]:
        return self.b * .5, self.h * .5

    @override
    def width(self) -> float:
        return self.b

    @override
    def height(self) -> float:
        return self.h

    @override
    def area(self) -> float:
        return self.b * self.h

    def check_y(self, y: float) -> None:
        if not 0 <= y < self.h:
            raise ValueError(f"y={y} must be between 0 and {self.h}")

    @override
    def area_above(self, y: float) -> float:
        self.check_y(y)
        return self.b * (self.h - y)

    @override
    def q(self, y: float) -> float:
        self.check_y(y)
        return .5 * self.b * (self.h - y) ** 2

    @override
    def sub_above(self, y: float) -> Self:
        self.check_y(y)
        return RectangularCrossSection(self.b, self.h - y)


class CircularCrossSection(CrossSection):
    def __init__(self, r: float) -> None:
        super().__init__(r=r)
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

    def check_y(self, y: float) -> None:
        if not 0 <= y < self.d:
            raise ValueError(f"y={y} must be between 0 and {self.d}")

    @override
    def area_above(self, y: float) -> float:
        self.check_y(y)
        theta = 2 * pi - 2 * (pi - pi * (self.d - y) / self.d)
        return self.r ** 2 * (theta - 2 * (theta - pi) / 2)

    @override
    def q(self, y: float) -> float:
        self.check_y(y)
        area = self.area_above(y)
        centroid_y = (self.d + y) / 2
        return area * (centroid_y - y)

    @override
    def sub_above(self, y: float) -> Self:
        raise NotImplementedError


class ComplexCrossSection(CrossSection):
    def __init__(self, basic_cross_sections: Sequence[tuple[CrossSection, float, float]]) -> None:
        """
        :param basic_cross_sections: [(cross_section, x_offset, y_offset)]
        """
        kwargs = {}
        for cs, x_offset, y_offset in basic_cross_sections:
            kwargs.update({f"{k}({x_offset}, {y_offset})": v for k, v in cs.kwargs().items()})
        super().__init__(**kwargs)
        self.basic_cross_sections: list[tuple[CrossSection, float, float]] = list(basic_cross_sections)

    @override
    def width(self) -> float:
        return max(cs.width() + x_offset for cs, x_offset, _ in self.basic_cross_sections)

    @override
    def min_width(self) -> float:
        return min(cs.min_width() for cs, _, _ in self.basic_cross_sections)

    @override
    def height(self) -> float:
        return max(cs.height() + y_offset for cs, _, y_offset in self.basic_cross_sections)

    def d_squared(self, i: int) -> float:
        x_bar, y_bar = self.centroid()
        cs, x_offset, y_offset = self.basic_cross_sections[i]
        cx, cy = cs.centroid()
        return (y_bar - y_offset - cy) ** 2

    def d(self, i: int) -> float:
        return self.d_squared(i) ** .5

    @override
    def moment_of_inertia(self) -> float:
        return sum(cs.moment_of_inertia() + cs.area() * self.d_squared(i) for i, (cs, x_offset, y_offset) in enumerate(
            self.basic_cross_sections))

    @override
    def area(self) -> float:
        return sum(cs[0].area() for cs in self.basic_cross_sections)

    def check_y(self, y: float) -> None:
        if not 0 <= y < self.height():
            raise ValueError(f"y={y} must be between 0 and {self.height()}")

    def select_components_above(self, y: float) -> list[tuple[CrossSection, float, float]]:
        self.check_y(y)
        return [
            (cs, x_offset, y_offset) for cs, x_offset, y_offset in self.basic_cross_sections
            if y_offset <= y < y_offset + cs.height()
        ]

    @override
    def area_above(self, y: float) -> float:
        self.check_y(y)
        components = self.select_components_above(y)
        return sum(cs.area_above(max(y - y_offset, 0)) for cs, x_offset, y_offset in components)

    def centroid_along(self, axis: Literal[0, 1]) -> float:
        total = 0
        for cs, x_offset, y_offset in self.basic_cross_sections:
            offsets = (x_offset, y_offset)
            total += cs.area() * (cs.centroid()[axis] + offsets[axis])
        return total / self.area()

    @override
    def centroid(self) -> tuple[float, float]:
        return self.centroid_along(0), self.centroid_along(1)

    @override
    def q(self, y: float) -> float:
        self.check_y(y)
        components = self.select_components_above(y)
        q = 0
        for cs, x_offset, y_offset in components:
            relative_y = y - y_offset
            if relative_y < 0:
                q += cs.area() * (cs.centroid()[1] + y_offset - y)
                continue
            sub = cs.sub_above(relative_y)
            q += sub.area() * sub.centroid()[1]
        return q

    @override
    def sub_above(self, y: float) -> Self:
        components = self.select_components_above(y)
        r = []
        for cs, x_offset, y_offset in components:
            relative_y = y - y_offset
            if relative_y < 0:
                r.append((cs, x_offset, y_offset - y))
                continue
            sub = cs.sub_above(relative_y)
            r.append((sub, x_offset, 0))
        return self.__class__(r)


class HollowBeam(ComplexCrossSection):
    def __init__(self, b: float, h: float, thickness: float) -> None:
        """
                b
        |---------------|
        ================= ---
        =================  |
        []             []  |
        []             []  |
        []             []  | h
        []             []  |
        []             []  |
        =================  |
        ================= ---
        """
        super().__init__([
            (RectangularCrossSection(b, thickness), 0, 0),  # bottom beam
            (RectangularCrossSection(thickness, h - 2 * thickness), 0, thickness),
            (RectangularCrossSection(thickness, h - 2 * thickness), b - thickness, thickness),
            (RectangularCrossSection(b, thickness), 0, h - thickness)  # top beam
        ])
        self._kwargs = {"b": b, "h": h, "thickness": thickness}

    @override
    def min_width(self) -> float:
        return 2 * self._kwargs["thickness"]


class IBeam(ComplexCrossSection):
    def __init__(self, d: float, bf: float, t: float, bw: float) -> None:
        super().__init__([
            (RectangularCrossSection(bf, t), 0, 0),  # bottom beam
            (RectangularCrossSection(bw, d - 2 * t), .5 * (bf - bw), t),
            (RectangularCrossSection(bf, t), 0, d - t)  # top beam
        ])
        self._kwargs = {"d": d, "bf": bf, "t": t, "bw": bw}

    @override
    def min_width(self) -> float:
        return self._kwargs["bw"]


class CIV102Beam(ComplexCrossSection):
    def __init__(self, *, top: float = 100, bottom: float = 80, height: float = 75, thickness: float = 1.27,
                 outreach: float = 5, glue: bool = True) -> None:
        """
        ============================== ---
        [            top             ]  | thickness
        ============================== ---
          [   ][ out-]  [reach][   ]    | thickness
          [   ]=======  =======[   ]   ---
          [   ]                [   ]    |
          [   ]                [   ]    | height - 2 * thickness
          [   ]                [   ]    |
          ==========================   ---
          [         bottom         ]    | thickness
          ==========================   ---
          |---| thickness
        """
        left, right = (top - bottom) * .5, (top + bottom) * .5
        super().__init__([
            (RectangularCrossSection(100, 1.27), 0, height),  # top beam
            (RectangularCrossSection(outreach, thickness), left + thickness, height - thickness),
            (RectangularCrossSection(outreach, thickness), right - thickness - outreach, height - thickness),
            (RectangularCrossSection(thickness, height - thickness), left, thickness),
            (RectangularCrossSection(thickness, height - thickness), right - thickness, thickness),
            (RectangularCrossSection(bottom, thickness), left, 0)  # bottom beam
        ])
        self._kwargs = {"top": top, "bottom": bottom, "height": height, "thickness": thickness, "outreach": outreach}
        if glue:
            self._kwargs["glue_y"] = height

    @override
    def min_width(self) -> float:
        return 2 * self._kwargs["thickness"]


if __name__ == "__main__":
    cross_section = ComplexCrossSection([
        (RectangularCrossSection(423, 43), 0, 0),
        (RectangularCrossSection(24, 847), 199.5, 43),
        (RectangularCrossSection(423, 43), 0, 890)
    ])
    # cross_section = IBeam(933, 423, 43, 24)
    print(cross_section.centroid())
    print(cross_section.area())
    print(cross_section.width())
    print(cross_section.height())
    print(cross_section.moment_of_inertia() * 1e-6)
    print(cross_section.q_max())
