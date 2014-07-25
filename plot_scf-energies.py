#!/usr/bin/python

import sys
from matplotlib import pyplot as plt


def read_qchem(filename):
    print 'Reading %s' % filename
    try:
        fin = open(filename, 'r')
    except IOError:
        print '%s not found.' % filename
        return None
    rl = fin.readline
    energies = []
    line = rl()
    while line:
        if 'Cycle       Energy' in line:
            scf = []
            rl() #  ----------------------------------------------------
            split = rl().split()
            while split and split[0].isdigit():
                i, energy, error = split
                scf.append(energy)
                split = rl().split()
            energies.append(scf)
        line = rl()
    return energies

def plot(energies):
    plt.figure()
    colors = ['b', 'r', 'y', 'g', 'c']
    offset = 1
    for i, scf in enumerate(energies):
        plt.plot(range(offset, len(scf)+1), scf, color=colors[i%len(colors)])
        offset += len(scf)
    plt.show()

def usage(cmd):
    print
    print 'Usage:'
    print ' ', cmd, 'qchem.out'
    print

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) != 1:
        usage(sys.argv[0])
        sys.exit(1)
    else:
        energies = read_qchem(args[0])
        plot(energies)
    sys.exit(0)