
'''
Created on September 10, 2013
@author: Qimin
'''

import pymatgen
from pymatgen.symmetry.finder import SpacegroupAnalyzer
from pymatgen.core.structure import IStructure

s = IStructure.from_file('POSCAR')

print SpacegroupAnalyzer(s).get_spacegroup_number()
print SpacegroupAnalyzer(s).get_spacegroup_symbol()
print SpacegroupAnalyzer(s).get_symmetry_dataset()['wyckoffs']
#print SpacegroupAnalyzer(s).get_primitive_standard_structure()