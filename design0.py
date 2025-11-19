from bridger import *

cross_section = CIV102Beam()
bridge = BeamBridge(400, cross_section, load_distribution=(1,) * 6)
material = Material()
bridge.place_the_train(128)
print(bridge.safety_factor((material.compressive_strength, material.tensile_strength)))
print(bridge.flexural_buckling_safety_factor(bridge.safe_flexural_buckling_stress(material)))
bridge.place_the_train(0)
print(bridge.shear_safety_factor(material.shear_strength))
print(bridge.glue_safety_factor(material.glue_strength))
print(bridge.shear_buckling_safety_factor(bridge.safe_shear_buckling_stress(material)))
