from bridge import *
from initialization import *

if __name__ == "__main__":
    evaluator = Evaluator(bridge, Material())
    print("Maximum load (N):", evaluator.maximum_load())
    if GRAPH:
        evaluator.plot_safety_factors()
