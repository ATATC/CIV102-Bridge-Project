import numpy as np
from matplotlib import pyplot as plt

from bridge import Bridge, ArbitraryCrossSection, intervals

if __name__ == "__main__":
    # bridge = Bridge(1200, 452, ArbitraryCrossSection(418000, 41.4, 76.27))
    bridge = Bridge(1200, 400, ArbitraryCrossSection(418000, 41.4, 76.27), mass_distribution=(1,) * 6)
    bridge.move_the_train(-bridge.wheel_positions[0])
    safe_stress = (6, 30)
    safety_factors_top = []
    safety_factors_bot = []
    for i in range(1200 - 960):
        bridge.move_the_train(1)
        sft, sfb = bridge.safety_factor((6, 30))
        safety_factors_top.append(sft)
        safety_factors_bot.append(sfb)
        if i == 172:
            print(bridge.safety_factor(safe_stress))
    print(intervals(np.array(safety_factors_top) < 1))
    print(intervals(np.array(safety_factors_bot) < 1))
    plt.plot(safety_factors_top, "orange")
    plt.plot(safety_factors_bot, "purple")
    plt.hlines(1, 0, 1200 - 960, "red")
    plt.xlabel("Position (mm)")
    plt.ylabel("Safety Factor")
    plt.show()
