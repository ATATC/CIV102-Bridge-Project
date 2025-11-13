import numpy as np
from matplotlib import pyplot as plt

from bridge import *

if __name__ == "__main__":
    graph = False
    # cross_section = ArbitraryCrossSection(418000, (50, 41.4), 100, 76.27, 0)
    cross_section = CIV102Beam()
    print(cross_section.moment_of_inertia() * 1e-6)
    print(cross_section.centroid())
    print(cross_section.d(1), cross_section.d(2))
    i = 1
    base = cross_section.basic_cross_sections[i][0]
    print(cross_section.d(i))
    print("I0", base.moment_of_inertia())
    print("Ix", base.moment_of_inertia() + base.area() * cross_section.d_squared(i))
    # bridge = Bridge(1200, 452, cross_section)
    bridge = Bridge(1200, 400, cross_section, mass_distribution=(1,) * 6)
    bridge.move_the_train(-bridge.wheel_positions[0])
    safe_stress = (6, 30)
    safety_factors_top = []
    safety_factors_bot = []
    shear_forces = []
    bending_moments = []
    x = bridge.x_linespace()
    for i in range(1200 - 960):
        shear_forces.append(bridge.expanded_shear_forces(x))
        bending_moments.append(bridge.expanded_bending_moments(x))
        sft, sfb = bridge.safety_factor((6, 30))
        safety_factors_top.append(sft)
        safety_factors_bot.append(sfb)
        if i == 172:
            print(bridge.safety_factor(safe_stress))
        bridge.move_the_train(1)
    shear_force_envelope = np.max(np.array(shear_forces), axis=0)
    bending_moment_envelope = np.max(np.array(bending_moments), axis=0)
    print(intervals(np.array(safety_factors_top) < 1))
    print(intervals(np.array(safety_factors_bot) < 1))
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
        plt.hlines(1, 0, 1200 - 960, "red")
        plt.grid(True)
        plt.title("Safety Factor on Various Positions")
        plt.xlabel("Position (mm)")
        plt.ylabel("Safety Factor")
        plt.legend(("Top", "Bottom", "Failure Threshold"))
        plt.savefig("safety_factors.png")
        plt.show()
