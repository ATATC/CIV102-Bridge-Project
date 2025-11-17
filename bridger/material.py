from dataclasses import dataclass


@dataclass
class Material(object):
    tensile_strength: float = 30
    compressive_strength: float = 6
    shear_strength: float = 4
    density: float = 7.14946079338653e-7
    modulus: float = 4000
    glue_strength: float = 2
