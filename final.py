from bridger import *

material = Material(length_between_stiffeners=125)
cross_section1 = CIV102Beam(**{'top': 100.0, 'bottom': 61.0, 'height': 160, 'thickness': 1.27, 'outreach': 5})
cross_section2 = CIV102Beam(**{'top': 100.0, 'bottom': 61.0, 'height': 180, 'thickness': 1.27, 'outreach': 5})

def cross_section(x: float) -> CrossSection:
    return cross_section2 if 400 < x < 800 else cross_section1

uniform_bridge = BeamBridge(1000, cross_section1, length=1250, load_distribution=(1.518, 1.518, 1, 1, 1.1, 1.1))
uniform_bridge

bridge = NonUniformBeamBridge(1000, cross_section, length=1250, load_distribution=(1.518, 1.518, 1, 1, 1.1, 1.1))
evaluator = Evaluator(bridge, material)
print(evaluator.maximum_load())
evaluator.plot_safety_factors()
