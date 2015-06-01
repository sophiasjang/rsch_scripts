'''
Created on September 10, 2013
@author: Qimin
'''
import sys
import pymatgen
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core.structure import IStructure

file = str(sys.argv[1])

s = IStructure.from_file(path)

prec = float(sys.argv[2])

print SpacegroupAnalyzer(s,symprec=prec).get_spacegroup_number()
print SpacegroupAnalyzer(s,symprec=prec).get_spacegroup_symbol()
print SpacegroupAnalyzer(s,symprec=prec).get_symmetry_dataset()['wyckoffs']
#print SpacegroupAnalyzer(s).get_primitive_standard_structure()

wyckoff = open("POSCAR_symm_wyckoff","w")

wyckoff.write(str(SpacegroupAnalyzer(s,symprec=prec).get_spacegroup_number())+'\n')
wyckoff.write(SpacegroupAnalyzer(s,symprec=prec).get_spacegroup_symbol()+'\n')
wyckoff.write(str(SpacegroupAnalyzer(s,symprec=prec).get_symmetry_dataset()['wyckoffs']))
wyckoff.close()