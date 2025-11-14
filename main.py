from bridge import *
from initialization import *

if __name__ == "__main__":
    evaluator = Evaluator(bridge, 6, 30, 4)
    print(evaluator.dead_zones())
    print(evaluator.maximum_load())
    if GRAPH:
        evaluator.plot_safety_factors()
