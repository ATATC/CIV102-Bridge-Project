from bridger import *

material = Material(length_between_stiffeners=125)
params = {'top': 100.2, 'bottom': 60.7, 'thickness': 1.27, 'outreach': 28}

max_height = 180
min_height = 160
margin = 60


def cross_section(x: float) -> CrossSection:
    if x <= margin or x >= 1250 - margin:
        return CIV102Beam(**params, height=min_height)
    return CIV102Beam(**params, height=max_height - ((max_height - min_height) / 625) * abs(x - 625 - margin))
    # return CIV102Beam(**params, height=max_height - ((max_height - min_height) / 625 ** 2) * (x - 625 - 60) ** 2)


bridge = VaryingBeamBridge(1500, cross_section, length=1250, load_distribution=(1,) * 6)

if __name__ == "__main__":
    bridge.plot_curvature_diagram(material)
    evaluator = Evaluator(bridge, material)
    print(evaluator.maximum_load())
    evaluator.plot_safety_factors()
