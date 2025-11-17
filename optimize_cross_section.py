from bridger import *
from initialization import *

MATBOARD_WIDTH: float = 508


def constraint(kwargs: dict[str, float]) -> dict[str, float] | None:
    top, bottom, height = kwargs["top"], kwargs["bottom"], kwargs["height"]
    kwargs["thickness"] = 1.27
    used = top + bottom + 2 * (height - 2.54)
    if used > MATBOARD_WIDTH or top < bottom:
        return None
    kwargs["outreach"] = .5 * (MATBOARD_WIDTH - used)
    return kwargs if 2 * kwargs["outreach"] < bottom else None


def optimize_cross_section() -> None:
    evaluator = Evaluator(bridge, Material())
    optimizer = BeamOptimizer(evaluator)
    cross_section, load = optimizer.optimize_cross_section({
        "top": (100, MATBOARD_WIDTH, 1),
        "bottom": (10, MATBOARD_WIDTH, 1),
        "height": (20, 200, 20),
    }, independent_params=("top", "bottom", "height"), constraint=constraint)
    print(cross_section.kwargs(), load)


if __name__ == "__main__":
    optimize_cross_section()
