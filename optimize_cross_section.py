from bridger import *
from initialization import *


def constraint(kwargs: dict[str, float]) -> dict[str, float] | None:
    top, bottom, height = kwargs["top"], kwargs["bottom"], kwargs["height"]
    kwargs["thickness"] = 1.27
    used = top + bottom + 2 * (height - 2.54)
    if used > 406.5 or top < bottom:
        return None
    kwargs["outreach"] = .5 * (406.5 - used)
    return kwargs if 2 * kwargs["outreach"] < bottom else None


def optimize_cross_section() -> None:
    evaluator = Evaluator(bridge, Material())
    optimizer = BeamOptimizer(evaluator)
    cs, load = optimizer.optimize_cross_section({
        "top": (10, 406.5, 4),
        "bottom": (10, 406.5, 4),
        "height": (10, 406.5, 4),
    }, independent_params=("top", "bottom", "height"), constraint=constraint)
    print(cs.kwargs(), load)


if __name__ == "__main__":
    optimize_cross_section()
