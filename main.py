from bridge import *
from initialization import *

if __name__ == "__main__":
    evaluator = Evaluator(bridge, Material())
    max_load, causes = evaluator.maximum_load()
    print(f"Maximum load: {max_load} N due to {causes}")
    evaluator.dead_zones(*evaluator.pass_the_train())
    if GRAPH:
        evaluator.plot_safety_factors()
