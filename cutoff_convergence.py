#!/usr/bin/python
import sys
from subprocess import Popen, PIPE
import scipy as sp
from matplotlib import pyplot as plt

tfont = 18
afont = 16

plot = False
if '-p' in sys.argv[1:]:
    plot = True
    sys.argv.remove('-p')

files = sys.argv[1:]
tot = []
n_atoms = 0
for f in files:
    fin = open(f, 'r')
    line = fin.readline()
    
    while line and not 'number of atoms/cell' in line:
        line = fin.readline()
    # check if we reached end of file
    if not line:
        print "Ignoring", f
        print "Seems not to be a QE output file."
        continue

    if not n_atoms:
        n_atoms = int(line.split()[-1])
    elif not n_atoms == int(line.split()[-1]):
        print
        print 'ERROR: input files have different number of atoms/cell. Exiting.'
        sys.exit(1)

    while line and not 'kinetic-energy cutoff' in line:
        line = fin.readline()
    cutoff = float(line.split()[-2])

    while line and not line.startswith('!'):
        line = fin.readline()
    # check if end of file reached (= calculation didn't converge)
    if not line:
        print "No convergence for cutoff", cutoff
        continue
    # got total energy
    ls = line.split()
    E_ry = float(ls[-2])
    unit = ls[-1]
    # convert to eV
    if unit == 'Ry':
        E_eV = E_ry * 13.605692
    tot.append((cutoff, E_eV))

data = sp.asarray(sorted(tot))
diff = sp.zeros((data.shape[0]-1, data.shape[1]))
rel_diff = sp.zeros((data.shape[0]-1, data.shape[1]))
for i in range(len(data)-1):
    diff[i,0] = data[i+1,0]
    diff[i,1] = (data[i,1]-data[i+1,1]) * 1000 # convert to meV
    rel_diff[i,0] = diff[i,0]
    rel_diff[i,1] = diff[i,1] / n_atoms # convert to meV

print
print 'Total energies (eV)'
print data
print
print 'Absolute differences (meV)'
print diff
print 
print 'Difference per atom (# of atoms = %d) (meV)' % n_atoms
print rel_diff

if plot:
    xmin = min(data[:,0])
    xmax = max(data[:,0])

    plt.subplot(121)
    plt.title('Total Energies', fontsize=tfont)
    plt.xlabel('Cutoff (Ry)', fontsize=afont)
    plt.ylabel(r'$E_{tot}$ (eV)', fontsize=afont)
    plt.xlim((xmin, xmax))
    plt.plot(data[:,0], data[:,1], linewidth=2.0)
    plt.plot(data[:,0], data[:,1], 'o')
    # plot differences
    plt.subplot(122)
    plt.title('Differences', fontsize=tfont)
    plt.xlabel('Cutoff (Ry)', fontsize=afont)
    plt.ylabel(r'$\Delta E$ (meV)', fontsize=afont)
    plt.xlim((xmin, xmax))
    plt.plot(rel_diff[:,0], rel_diff[:,1], linewidth=2.0)
    plt.plot(rel_diff[:,0], rel_diff[:,1], 'o')
    plt.plot(rel_diff[:,0], sp.ones(len(rel_diff[:,0])), linewidth=2.0)
    
    plt.show()
