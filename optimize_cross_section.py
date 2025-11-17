from bridger import *
from initialization import *


def optimize_cross_section() -> None:
    evaluator = Evaluator(bridge, Material())
    optimizer = BeamOptimizer(evaluator)
    print(optimizer.optimize_cross_section())


if __name__ == "__main__":
    optimize_cross_section()
