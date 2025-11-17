import numpy as np
from matplotlib import pyplot as plt

from initialization import *

def plot_envelopes() -> None:
    bridge.move_the_train(-bridge.wheel_positions()[0])
    shear_forces = []
    bending_moments = []
    x = bridge.x_linespace()
    n = 1200 - 960 + 104
    for i in range(n):
        shear_forces.append(bridge.expanded_shear_forces(x))
        bending_moments.append(bridge.expanded_bending_moments(x))
        bridge.move_the_train(1)
    shear_force_envelope = np.max(np.array(shear_forces), axis=0)
    bending_moment_envelope = np.max(np.array(bending_moments), axis=0)
    if GRAPH:
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


if __name__ == "__main__":
    plot_envelopes()
