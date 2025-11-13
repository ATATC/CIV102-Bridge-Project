import numpy as np
from matplotlib import pyplot as plt

from bridge import *

if __name__ == "__main__":
    graph = True
    safety_factor_threshold = 1
    cross_section = CIV102Beam()
    # bridge = BeamBridge(1200, 400, cross_section, mass_distribution=(1,) * 6) # load case 1
    # bridge = BeamBridge(1200, 452, cross_section) # load case 2 - first pass
    bridge = BeamBridge(
        1200, 1000, cross_section, mass_distribution=(1.518, 1.518, 1, 1, 1.1, 1.1)
    ) # load case 2 - subsequent passes
    bridge.move_the_train(-bridge.wheel_positions[0])
    safe_stress = (6, 30)
    safe_shear_stress = 4
    safety_factors_top = []
    safety_factors_bot = []
    safety_factors_shear = []
    shear_forces = []
    bending_moments = []
    x = bridge.x_linespace()
    n = 1200 - 960 + 104
    for i in range(n):
        shear_forces.append(bridge.expanded_shear_forces(x))
        bending_moments.append(bridge.expanded_bending_moments(x))
        sft, sfb = bridge.safety_factor((6, 30))
        safety_factors_top.append(sft)
        safety_factors_bot.append(sfb)
        safety_factors_shear.append(bridge.shear_safety_factor(safe_shear_stress))
        if i == 172:
            print("Safety factors when the train is centered:", bridge.safety_factor(safe_stress),
                  bridge.shear_safety_factor(safe_shear_stress))
        bridge.move_the_train(1)
    shear_force_envelope = np.max(np.array(shear_forces), axis=0)
    bending_moment_envelope = np.max(np.array(bending_moments), axis=0)
    print("Intervals (inclusive) where the top fails:", intervals(np.array(safety_factors_top) < safety_factor_threshold))
    print("Intervals (inclusive) where the bottom fails:", intervals(np.array(safety_factors_bot) < safety_factor_threshold))
    if graph:
        plt.figure(figsize=(12, 6))
        plt.plot(x, shear_force_envelope)
        plt.grid(True)
        plt.title("Shear Force Envelope")
        plt.xlabel("Position (mm)")
        plt.ylabel("Max Shear Force (N)")
        plt.savefig("shear_force_envelope.png")
        plt.show()
        plt.close()
        plt.figure(figsize=(12, 6))
        plt.plot(x, bending_moment_envelope * 1e-3)
        plt.grid(True)
        plt.title("Bending Moment Envelope")
        plt.xlabel("Position (mm)")
        plt.ylabel("Max Bending Moment (Nm)")
        plt.savefig("bending_moment_envelope.png")
        plt.show()
        plt.close()
        plt.figure(figsize=(12, 6))
        plt.plot(safety_factors_top, "orange")
        plt.plot(safety_factors_bot, "purple")
        plt.plot(safety_factors_shear, "blue")
        plt.hlines(safety_factor_threshold, 0, n, "red")
        plt.grid(True)
        plt.title("Safety Factor on Various Positions")
        plt.xlabel("Train Position (mm)")
        plt.ylabel("Safety Factor")
        plt.legend(("Compressive", "Tensile", "Shear", "Failure Threshold"))
        plt.savefig("safety_factors.png")
        plt.show()
