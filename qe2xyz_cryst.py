#!/usr/bin/python

import sys
import scipy as sp

def get_old_coordinates(fnin):
    with open (fnin, "r") as fin:
        for line in fin:
            if "nat" in line:
                n = int(line.split('=')[-1].strip().strip(","))
                break
        for line in fin:
            if "ATOMIC_POSITIONS" in line:
                unit = line
                break
        
        xyz = sp.zeros((3,n))
        atoms = []
        for i, line in enumerate(fin):
            if i < n:
                ls = line.split()
                atoms.append(ls[0])
                xyz[:,i] = map(float, ls[1:])
            else:
                break
    return atoms, xyz, unit
    
def get_axes(fnin):
    axes = sp.zeros((3,3))
    with open (fnin, "r") as fin:
        for line in fin:
            if "CELL_PARAMETERS" in line:
                if "cubic" or "bohr" in line:
                    fac = 0.529177249
                else: fac = 1.
                break
        axes[:,0] = map(float, next(fin).split())
        axes[:,1] = map(float, next(fin).split())
        axes[:,2] = map(float, next(fin).split())
        axes = axes * fac
    return axes
    
    
def write_new_coordinates(fnin, fnout, repeat):
    
    axes = get_axes(fnin)
    atoms, xyz, unit = get_old_coordinates(fnin)
    
    # convert to Angstrom
    if 'bohr' in unit.lower():
        xyz *= 0.529177249
    elif 'crystal' in unit.lower():
        xyz = axes.dot(xyz)
    
    n_atoms = xyz.shape[1]
    # number of new unit cells
    #N_cells = reduce(lambda x, y: x*y, repeat)
    dim = [3, n_atoms] + repeat
    new = sp.zeros(dim)
    
    for i in range(repeat[0]):
        for j in range(repeat[1]):
            for k in range(repeat[2]):
                new[:,:,i,j,k] = xyz + (i*axes[:,0] + j*axes[:,1] + k*axes[:,2]).reshape(3,1)
    with open(fnout, 'w') as fout:
        # comment next two lines if you want to write every unit cell as one frame
        fout.write('{0}\n'.format(n_atoms*reduce(lambda x, y: x*y, repeat)))
        fout.write('unit cell {0}x{1}x{2}\n'.format(*repeat))
        for i in range(repeat[0]):
            for j in range(repeat[1]):
                for k in range(repeat[2]):
                    # uncomment next two lines to write every unit cell as one frame
                    #fout.write('{0}\n'.format(n_atoms))
                    #fout.write('unit cell {0}x{1}x{2}\n'.format(i+1, j+1, k+1))
                    for a, atom in enumerate(atoms):
                        #x, y, z = xyz[a,:,i,j,k]
                        fout.write('{0:<2} {1:>13.8f} {2:>13.8f} {3:>13.8f}\n'.format(atom, *new[:,a,i,j,k]))


def usage():
    
    print 'Syntax: qe2xyz_cryst.py pwscf.in output.xyz axbxc]'
    print
    print 'Creates xyz file with repeated unit cell based on Quantum Espresso PW input.'

if __name__ == '__main__':
    args = sys.argv[1:]
    in_out = []
    if len(args) != 3:
        usage()
        sys.exit(1)
    #elif len(args) == 2 and args[0].endswith('.xyz') and args[1].endswith('.pdb'):
        #in_out.append((args[0], args[1]))
    else:
        fnin = args[0]
        fnout = args[1]
        repeat = map(int, args[2].split('x'))
        if len(repeat) != 3:
            usage()
            sys.exit(1)
        write_new_coordinates(fnin, fnout, repeat)
        
    sys.exit(0)
