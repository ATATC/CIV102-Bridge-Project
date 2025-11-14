from bridge import CIV102Beam, BeamBridge

GRAPH = False
cross_section = CIV102Beam(top=800)
bridge = BeamBridge(400, cross_section, load_distribution=(1,) * 6)  # load case 1
# bridge = BeamBridge(452, cross_section) # load case 2 - first pass
# bridge = BeamBridge(
#     1000, cross_section, load_distribution=(1.518, 1.518, 1, 1, 1.1, 1.1)
# ) # load case 2 - subsequent passes
