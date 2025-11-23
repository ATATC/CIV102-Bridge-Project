from bridger import *
from initialization import *

MATBOARD_WIDTH: float = 450


def constraint(kwargs: dict[str, float]) -> dict[str, float] | None:
    kwargs["thickness"] = 1.27
    kwargs["outreach"] = 28
    used = kwargs["bottom"] + 2 * (kwargs["height"] - 2.54) + 2 * kwargs["outreach"]
    return kwargs if used <= MATBOARD_WIDTH and kwargs["top"] > kwargs["bottom"] else None


def optimize_cross_section() -> None:
    evaluator = Evaluator(bridge, material)
    optimizer = BeamOptimizer(evaluator)
    params, load = optimizer.optimize_cross_section({
        "top": (100, MATBOARD_WIDTH, .1),
        "bottom": (10, MATBOARD_WIDTH, .1),
        "height": (20, 200, 20)
    }, constraint=constraint)
    print(params, load)


if __name__ == "__main__":
    optimize_cross_section()
