from abc import ABCMeta, abstractmethod
from typing import override


class CrossSection(object, metaclass=ABCMeta):
    @abstractmethod
    def moment_of_inertia(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def centroid(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def height(self) -> float:
        raise NotImplementedError


class ArbitraryCrossSection(CrossSection):
    def __init__(self, moment_of_inertia: float, centroid: float, height: float) -> None:
        self._moment_of_inertia: float = moment_of_inertia
        self._centroid: float = centroid
        self._height: float = height

    @override
    def moment_of_inertia(self) -> float:
        return self._moment_of_inertia

    @override
    def centroid(self) -> float:
        return self._centroid

    @override
    def height(self) -> float:
        return self._height


class RectangularCrossSection(CrossSection):
    def __init__(self, b: float, h: float) -> None:
        self.b: float = b
        self.h: float = h

    @override
    def moment_of_inertia(self) -> float:
        return self.b * self.h ** 3 / 12

    @override
    def centroid(self) -> float:
        return self.b / 2

    @override
    def height(self) -> float:
        return self.h
