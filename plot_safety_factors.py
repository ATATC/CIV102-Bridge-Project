from bridger import *
from initialization import *


def plot_safety_factors() -> None:
    evaluator = Evaluator(bridge, material)
    max_load, causes = evaluator.maximum_load()
    print(f"Maximum load: {max_load} N due to {causes}")
    evaluator.dead_zones(*evaluator.pass_the_train())
    if GRAPH:
        evaluator.plot_safety_factors(save_as="safety_factors.png")


if __name__ == "__main__":
    plot_safety_factors()
