#!/usr/bin/python
'''
copy coordinates from relaxed geometry into dynmat.mold
MolDen's [FR-COORD] needs coordinates in bohr!
'''

import sys
import scipy as sp
from myconstants import *

def read_rlx(filename):
    fin = open(filename, 'r')
    all_coords = []
    while True:
        line = fin.readline()
        if not line: break
        elif 'Begin final coordinates' in line:
            break
    if not line:
        fin.seek(0)
        
    unit = ''
    unit_vectors = sp.zeros((3,3))
    
    FLAG = True
    while FLAG:
        line = fin.readline()
        if not line:
            FLAG == False
        elif 'ATOMIC_POSITIONS' in line:
            if 'angstrom' in line.lower():
                unit = 'angstrom'
                FLAG = False
            elif "bohr" in line.lower():
                unit = 'bohr'
                FLAG = False
            elif "crystal" in line.lower():
                unit = 'crystal'
                # get unit vectors
                fin.seek(0)
                
                line = fin.readline()
                while line:
                    if "CELL_PARAMETERS" in line:
                        # TODO include alat units etc.
                        crystal_unit = 1.0 if "bohr" in line else BOHR_PER_ANGSTROM
                        for i in range(3):
                            line = fin.readline()
                            unit_vectors[:,i] = list(map(float, line.split()))
                            unit_vectors[:,i] *= crystal_unit
                        break
                    line = fin.readline()
                fin.seek(0)
                
                line = fin.readline()
                while line:
                    if "ATOMIC_POSITIONS" in line:
                        FLAG = False
                        break
                    line = fin.readline()
            else:
                raise Exception('Fix unit conversion in script.')
    while True:
        line = fin.readline()
        if not line: break
        elif 'End final coordinates' in line or "K_POINTS" in line:
            break
        else:
            ls = line.split()
            atom = ls.pop(0)
            coords = sp.asarray(map(float, ls))
            if unit == 'angstrom':
                # convert to bohr
                coords *= BOHR_PER_ANGSTROM
            elif unit == 'bohr':
                pass
            elif unit == 'crystal':
                coords = unit_vectors.dot(coords)
            else:
                raise Exception('Fix unit conversion in script.')
            all_coords.append((atom, coords))
    fin.close()
    return all_coords

def write_mold(filename, xyz_bohr):
    fin = open(filename, 'r')
    fout = open(filename + '_bohr', 'w')
    
    i = 0
    while True:
        line = fin.readline()
        if not line: break
        fout.write(line)
        if '[FR-COORD]' in line:
            break
    
        #else:
            #print i
            #atom, coords = xyz_bohr[i]
            #fout.write('{0}  {1:>8.5f}  {2:>8.5f}  {3:>8.5f}\n'.format(
                       #atom, coords[0], coords[1], coords[2]))
            #i += 1
            
            ## check if input file has the same number of coordinates
            #ls = line.split()
            #old_atom = ls.pop(0)
            #old_coords = map(float, ls)
            #CHECK = False
            #if old_atom != atom:
                #print 'Atom names are different. Will continue.'
                #CHECK = True
            #if len(old_coords) != 3:
                #print 'Replacing something else than coordinates.'
                #CHECK = True
            #if CHECK:
                #print line
            
        #if '[FR-COORD]' in line:
            #OVERWRITE = True
        #elif '[' in line:
            #OVERWRITE = False
    
    
    for atom, coords in xyz_bohr:
        line = fin.readline()
        ls = line.split()
        # check if input file has the same number of coordinates
        old_atom = ls.pop(0)
        old_coords = map(float, ls)
        CHECK = False
        if old_atom != atom:
            print 'Atom names are different. Will continue.'
            CHECK = True
        if len(old_coords) != 3:
            print 'Replacing something else than coordinates.'
            CHECK = True
        if CHECK:
            print line
            
        fout.write('   {0:<2}         {1:>8.5f}       {2:>8.5f}       {3:>8.5f}\n'.format(
                   atom, coords[0], coords[1], coords[2]))
    while True:
        line = fin.readline()
        if not line: break
        fout.write(line)
    fin.close()
    fout.close()
    print 'Done.'
    
def usage(cmd):
    print
    print 'Usage: qe_coords2mold.py rlx.out (or scf.in) dynmat.mold'
    print

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) != 2:
        usage(sys.argv[0])
        sys.exit(1)
    else:
        xyz_bohr = read_rlx(args[0])
        write_mold(args[1], xyz_bohr)
    sys.exit(0)