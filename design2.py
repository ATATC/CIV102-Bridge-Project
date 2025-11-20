from bridger import *

material = Material(length_between_stiffeners=125)
params = {'top': 100.0, 'bottom': 61.0, 'thickness': 1.27, 'outreach': 5}

max_height = 200
min_height = 140


def cross_section(x: float) -> CrossSection:
    return CIV102Beam(**params, height=max_height - ((max_height - min_height) / 625 ** 2) * (x - 625) ** 2)


bridge = VaryingBeamBridge(1000, cross_section, length=1250, load_distribution=(1.518, 1.518, 1, 1, 1.1, 1.1))

if __name__ == "__main__":
    bridge.plot_curvature_diagram(material)
    evaluator = Evaluator(bridge, material)
    print(evaluator.maximum_load())
    evaluator.plot_safety_factors()
