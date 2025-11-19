from abc import ABCMeta, abstractmethod
from math import pi
from typing import override, Literal, Sequence, Self

from bridger.material import Material


class CrossSection(object, metaclass=ABCMeta):
    def __init__(self, **kwargs: float) -> None:
        self._kwargs: dict[str, float] = kwargs

    @abstractmethod
    @override
    def __str__(self) -> str:
        raise NotImplementedError

    @override
    def __repr__(self) -> str:
        return str(self)

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

    @abstractmethod
    def safe_flexural_buckling_stress(self, material: Material, *, horizontal: bool = False) -> float | None:
        raise NotImplementedError

    @abstractmethod
    def safe_shear_buckling_stress(self, material: Material) -> float:
        raise NotImplementedError


class RectangularCrossSection(CrossSection):
    def __init__(self, b: float, h: float) -> None:
        super().__init__(b=b, h=h)
        self.b: float = b
        self.h: float = h

    @override
    def __str__(self) -> str:
        return f"RectangularCrossSection({self.b}x{self.h})"

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
        return .5 * self.b * (self.h - y) * (self.h - self.centroid()[1])

    @override
    def sub_above(self, y: float) -> Self:
        self.check_y(y)
        return RectangularCrossSection(self.b, self.h - y)

    @override
    def safe_flexural_buckling_stress(self, material: Material, *, horizontal: bool = False) -> float | None:
        return 4 * pi ** 2 * material.modulus / 12 / (1 - material.poisson_ratio ** 2) * ((
                self.b / self.h) ** 2 if horizontal else (self.h / self.b) ** 2)

    @override
    def safe_shear_buckling_stress(self, material: Material) -> float:
        return 5 * pi ** 2 * material.modulus / 12 / (1 - material.poisson_ratio ** 2) * (
                    (self.b / self.h) ** 2 + (self.b / material.length_between_stiffeners) ** 2)


class CircularCrossSection(CrossSection):
    def __init__(self, r: float) -> None:
        super().__init__(r=r)
        self.r: float = r
        self.d: float = 2 * r

    @override
    def __str__(self) -> str:
        return f"CircularCrossSection(radius {self.r})"

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
        return self.r ** 2 * pi

    @override
    def q(self, y: float) -> float:
        self.check_y(y)
        area = self.area_above(y)
        centroid_y = (self.d + y) / 2
        return area * (centroid_y - y)

    @override
    def sub_above(self, y: float) -> Self:
        raise NotImplementedError

    @override
    def safe_flexural_buckling_stress(self, material: Material, *, horizontal: bool = False) -> float | None:
        raise NotImplementedError

    @override
    def safe_shear_buckling_stress(self, material: Material) -> float:
        raise NotImplementedError


type CrossSectionComponent = tuple[CrossSection, float, float]


class ComplexCrossSection(CrossSection):
    def __init__(self, basic_cross_sections: Sequence[CrossSectionComponent]) -> None:
        """
        :param basic_cross_sections: [(cross_section, x_offset, y_offset)]
        """
        kwargs = {}
        for cs, x_offset, y_offset in basic_cross_sections:
            kwargs.update({f"{k}({x_offset}, {y_offset})": v for k, v in cs.kwargs().items()})
        super().__init__(**kwargs)
        self.basic_cross_sections: list[CrossSectionComponent] = list(basic_cross_sections)
        self.top_csc: CrossSectionComponent = max(basic_cross_sections, key=lambda x: x[0].height() + x[2])
        self.vcp_bottom: list[CrossSectionComponent | None] = [self.top_csc]
        self.vcp_top: list[CrossSectionComponent | None] = [None]
        for i, (cs1, x1, y1) in enumerate(basic_cross_sections):
            if isinstance(cs1, ComplexCrossSection):
                raise ValueError("ComplexCrossSection must consist of only simple cross-sections")
            if y1 == 0:
                self.vcp_bottom.append(None)
                self.vcp_top.append((cs1, x1, y1))
                continue
            h1 = cs1.height()
            for cs2, x2, y2 in basic_cross_sections[i + 1:]:
                if x1 > x2 + cs2.width() or x2 > x1 + cs1.width():
                    continue
                if abs((y1 + h1) - y2) < 1e-6:
                    self.vcp_bottom.append((cs1, x1, y1))
                    self.vcp_top.append((cs2, x2, y2))
                elif abs((y2 + cs2.height()) - y1) < 1e-6:
                    self.vcp_bottom.append((cs2, x2, y2))
                    self.vcp_top.append((cs1, x1, y1))

    @override
    def __str__(self) -> str:
        return f"ComplexCrossSection({tuple(self.basic_cross_sections)})"

    @override
    def width(self) -> float:
        return max(cs.width() + x_offset for cs, x_offset, _ in self.basic_cross_sections)

    @override
    def min_width(self) -> float:
        return min(cs.min_width() for cs, _, _ in self.basic_cross_sections)

    @override
    def height(self) -> float:
        return self.top_csc[0].height() + self.top_csc[2]

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

    def select_components_above(self, y: float) -> list[CrossSectionComponent]:
        self.check_y(y)
        return [
            (cs, x_offset, y_offset) for cs, x_offset, y_offset in self.basic_cross_sections
            if y < y_offset + cs.height()
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
        y_bar = self.centroid()[1]
        for cs, x_offset, y_offset in components:
            relative_y = y - y_offset
            if relative_y <= 0:
                q += cs.area() * (cs.centroid()[1] + y_offset - y_bar)
                continue
            sub = cs.sub_above(relative_y)
            q += sub.area() * (sub.centroid()[1] + y - y_bar)
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

    def free_widths(self) -> tuple[float, float]:
        top_cs = self.top_csc[0]
        min_free_width = float('inf')
        max_free_width = 0
        support_points = []
        for i, csc in enumerate(self.vcp_bottom):
            if csc and self.vcp_top[i] == self.top_csc:
                support_points.append((csc[1], csc[1] + csc[0].width()))
        if not support_points:
            max_free_width = min_free_width = top_cs.width()
        else:
            support_points.sort()
            if support_points[0][0] > self.top_csc[1]:
                width = support_points[0][0] - self.top_csc[1]
                min_free_width = min(min_free_width, width)
                max_free_width = width
            top_right = self.top_csc[1] + top_cs.width()
            if support_points[-1][1] < top_right:
                width = top_right - support_points[-1][1]
                min_free_width = min(min_free_width, width)
                max_free_width = max(max_free_width, width)
            for i in range(len(support_points) - 1):
                gap = support_points[i + 1][0] - support_points[i][1]
                if gap > 0:
                    min_free_width = min(min_free_width, gap)
                    max_free_width = max(max_free_width, gap)
        return min_free_width, max_free_width

    @override
    def safe_flexural_buckling_stress(self, material: Material, *, horizontal: bool = False) -> float | None:
        if horizontal:
            raise NotImplementedError("Calculation of horizontal safe flexural buckling stress is not supported yet")
        top_cs = self.top_csc[0]
        min_free_width, max_free_width = self.free_widths()
        top_safe_stress = top_cs.safe_flexural_buckling_stress(material)
        if not min_free_width or not top_safe_stress:
            return None
        case1 = top_safe_stress * (top_cs.width() / max_free_width) ** 2
        c1 = pi ** 2 * material.modulus / 12 / (1 - material.poisson_ratio ** 2)
        case2 = .425 * c1 * (top_cs.height() / min_free_width) ** 2
        case3 = 24 * c1 * (top_cs.height() / top_cs.width()) ** 2
        return min(case1, case2, case3)

    @override
    def safe_shear_buckling_stress(self, material: Material) -> float:
        return min(csc[0].safe_shear_buckling_stress(material) for csc in self.basic_cross_sections
                   if csc in self.vcp_bottom and csc in self.vcp_top)


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
        self._kwargs = {
            "top": top, "bottom": bottom, "height": height, "thickness": thickness, "outreach": outreach
        }
        if glue:
            self._kwargs["glue_y"] = height
            self._kwargs["glue_b"] = 2 * (thickness + outreach)

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
