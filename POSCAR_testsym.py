'''
Created on September 10, 2013
@author: Qimin
'''
import sys
import pymatgen
from math import *
from pymatgen.symmetry.finder import SpacegroupAnalyzer
from pymatgen.core.structure import IStructure

file = str(sys.argv[1])
spacegroup = str(sys.argv[2])
max = float(sys.argv[3])
min = float(sys.argv[4])
iter = float(sys.argv[5])

s = IStructure.from_file(file)

def getLowSymPrec(s,max,min,spacegroup,iter):
    SG = str(spacegroup)
    if SG!=str(SpacegroupAnalyzer(s,symprec=max).get_spacegroup_number()):
        print "Not reasonable spacegroup or max too large"
        return -1
    elif SG==str(SpacegroupAnalyzer(s,symprec=min).get_spacegroup_number()):
        return min
    else:
        upperbound = max
        lowerbound = min
        i=0
        while i<iter:
            trial = 10**((log(upperbound,10)+log(lowerbound,10))/2)
            if SG==str(SpacegroupAnalyzer(s,symprec=trial).get_spacegroup_number()):
                upperbound=trial
            elif SG!=str(SpacegroupAnalyzer(s,symprec=trial).get_spacegroup_number()):
                lowerbound=trial
            i+=1
        return upperbound

def round_up_to_3(x):
    y = round(x, -int(ceil(log10(x)))+3)
        if x - y > 0:
        return y + 10**(int(ceil(log10(x)))-3)
        else:
        return y
prec = getLowSymPrec(s,max,min,spacegroup,iter)
prec=round_up_to_3(prec)
print prec
s=SpacegroupAnalyzer(s,symprec=prec).get_refined_structure()
structure =  SpacegroupAnalyzer(s).get_conventional_standard_structure()

structure.to(filename="POSCAR2", fmt="poscar")