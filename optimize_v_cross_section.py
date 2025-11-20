from typing import override

from bridger import *
from final import bridge, material


class VaryingBeamOptimizer(BeamOptimizer):
    @override
    def load_criterion(self, params: dict[str, float]) -> float:
        if not isinstance(self._bridge, VaryingBeamBridge):
            raise ValueError("Expecting a varying beam bridge")
        params1 = params.copy()
        params1.pop("height2")
        params1["height"] = params.pop("height1")
        params2 = params.copy()
        params2.pop("height1")
        params2["height"] = params.pop("height2")
        self._bridge.v_cross_section(v_cross_section=lambda x: CIV102Beam(**params2) if 400 < x < 800 else CIV102Beam(**params1))
        return self._evaluator.maximum_load()[0]


MATBOARD_WIDTH: float = 395


def constraint(kwargs: dict[str, float]) -> dict[str, float] | None:
    top, bottom, height1, height2 = kwargs["top"], kwargs["bottom"], kwargs["height1"], kwargs["height2"]
    kwargs["thickness"] = 1.27
    kwargs["outreach"] = 5
    used1 = top + bottom + 2 * (height1 - 2.54) + 10
    used2 = top + bottom + 2 * (height2 - 2.54) + 10
    return kwargs if used1 <= MATBOARD_WIDTH and used2 < MATBOARD_WIDTH and top > bottom else None


def optimize_cross_section() -> None:
    evaluator = Evaluator(bridge, material)
    optimizer = VaryingBeamOptimizer(evaluator)
    params, load = optimizer.optimize_cross_section({
        "top": (100, MATBOARD_WIDTH, 1),
        "bottom": (10, MATBOARD_WIDTH, 1),
        "height1": (100, 200, 20),
        "height2": (140, 200, 1),
    }, constraint=constraint)
    print(params, load)


if __name__ == "__main__":
    optimize_cross_section()
