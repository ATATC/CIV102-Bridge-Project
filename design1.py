from bridger import *

material = Material(length_between_stiffeners=140)
cross_section1 = CIV102Beam(**{'top': 100.2, 'bottom': 60.7, 'height': 160, 'thickness': 1.27, 'outreach': 28})
cross_section1.visualize()
cross_section2 = CIV102Beam(**{'top': 100.2, 'bottom': 60.7, 'height': 161.27, 'thickness': 1.27, 'outreach': 28})


def cross_section(x: float) -> CrossSection:
    return cross_section2 if 416 < x < 833 else cross_section1


uniform_bridge = BeamBridge(1000, cross_section1, length=1250, load_distribution=(1,) * 6)
bridge = VaryingBeamBridge(1000, cross_section, length=1250, load_distribution=(1,) * 6)

if __name__ == "__main__":
    uniform_bridge.plot_displaced_shape(material)
    uniform_evaluator = Evaluator(uniform_bridge, material)
    print(uniform_evaluator.maximum_load())
    uniform_evaluator.plot_safety_factors(colors=("blue", "purple", "cyan", None, "yellow", "green"))

    bridge.plot_displaced_shape(material)
    evaluator = Evaluator(bridge, material)
    print(evaluator.maximum_load())
    evaluator.plot_safety_factors()
