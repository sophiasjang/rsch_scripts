#!/usr/bin/python3

import sys

bohr_per_angstrom = 1.889725989
dist = 10 # in angstrom

for fn in sys.argv[1:]:
    all_coords = []
    with open(fn, 'r') as fin:
        n_atoms = int(fin.readline())
        comment = fin.readline()
        line = fin.readline()
        while line and len(all_coords) < n_atoms:
            coords = map(float, line.split()[1:])
            all_coords.append(coords)
            line = fin.readline()
            
    
    xyz = list(zip(*all_coords))
    #print(xyz)
    delta_x = (max(xyz[0]) - min(xyz[0]) + dist)# * bohr_per_angstrom
    delta_y = (max(xyz[1]) - min(xyz[1]) + dist)# * bohr_per_angstrom
    delta_z = (max(xyz[2]) - min(xyz[2]) + dist)# * bohr_per_angstrom
    
    print
    print(fn)
    print('CELL_PARAMETERS in angstrom')
    print('{:>7.3f}    0.000    0.000'.format(delta_x))
    print('  0.000  {:>7.3f}    0.000'.format(delta_y))
    print('  0.000    0.000  {:>7.3f}'.format(delta_z))
    