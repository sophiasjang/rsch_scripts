#!/usr/bin/python

# read mode vectors

# read geometry

# for several times
    # shift geometry by a certain amount along evector

# print shifted geometry to file

import sys
import os
import re
import getopt

def read_evectors(dynmat_file):
    f = open(dynmat_file, 'r')
    all_evecs = {}
    current = []
    for line in f:
        lstrip = line.strip()
        # new mode
        if lstrip.startswith('omega('):
            m = re.search('omega\(([ 0-9]+)\)', lstrip)
            i = int(m.group(1))
            current = []
            all_evecs[i] = current
        elif lstrip.startswith('('):
            lsplit = lstrip.split()
            current.append(map(float, lsplit[1:-1:2]))
    f.close()
    return all_evecs

def read_rlx_coords(filename):
    f = open(filename, 'r')
    
    line = f.readline()
    while line and not 'Begin final coordinates' in line:
        line = f.readline()
    while line and not line.startswith('ATOMIC_POSITIONS'):
        line = f.readline()
    m = re.search('ATOMIC_POSITIONS \((.+)\)', line)
    unit = m.group(1)
    
    # read coordinates
    eq_coords = []
    line = f.readline()
    while line and not line.startswith('End final coordinates'):
        ls = line.strip().split()
        atom = ls.pop(0)
        xyz = map(float, ls)
        # TODO convert to angstrom if not already
        if unit != 'angstrom':
            raise Exception('Can not handle unit. Please check script.')
        eq_coords.append((atom, xyz))
        line = f.readline()
    return eq_coords
    
def write_run_files(fn_prefix, fn_rlx, fileformat, eq_xyz, evecs, mode_n, nsteps, max_scale, min_scale, samefile):
    #'''
    #write all files for one node
    #'''
    
    ##width = max([len(str(n)) for n in range(nsteps+1)])
    # open only one file and write all scaled geometry as trajectory
    if samefile:
        fn_out = '{0}_scaled{1}-{2}_{3}.{4}'.format(fn_prefix, min_scale, max_scale, nsteps, fileformat)
        fout = open(fn_out, 'w')
    
    for n in range(nsteps):
        scale = 1.0*n/(nsteps-1)*(max_scale - min_scale) + min_scale
        # write a single file for each scale
        if not samefile:
            fn_out = '{0}_scaled{1}.{2}'.format(fn_prefix, scale, fileformat)
            fout = open(fn_out, 'w')
        w = fout.write
        if fileformat == 'xyz':
            w('{0}\n'.format(len(eq_xyz)))
            w('Geometry from {0} stretched along mode {1} with factor {2}\n'.format(
                        fn_rlx, mode_n, scale))
            for i, (atom, coords) in enumerate(eq_xyz):
                displaced = [c[0] + scale*c[1] for c in zip(coords, evecs[i])]
                w('{0} {1:>13.9f} {2:>13.9f} {3:>13.9f}\n'.format(atom, displaced[0], displaced[1], displaced[2]))
            w('\n')
        else:
            raise Exception('%s format has not been implemented yet.')
        if not samefile:
            fout.close()
    if samefile:
        fout.close()
    
def usage():
    print
    print 'syntax: shift_geometry.py -d dynmat -r rlx.out [-hpfnmx ... ]'
    print
    print 'Options [default arguments]'
    print '  -d, --dynmat      specify dynmat.out file with e\'vectors'
    print '  -r, --rlx         specify input file with relaxed coordinates'
    print '  -p, --prefix      specify prefix for output files [same as rlx file]'
    print '  -f, --fileformat  specify output file format [xyz]'
    print '  -n, --nsteps      number of different scaled geometries to calculate [1]'
    print '  -m, --modes       comma separated list of modes to calculate (1,2,3 or "1, 2, 3") [all]'
    print '  -x, --max         maximum scale applied to e\'vectors [1.0]'
    print '      --min         minimum scale applied to e\'vectors (can be negative) [1.0]'
    print '      --samefile    print all coordinates for one mode in one file (trajectory)'
    print '  -h, --help        print this information and exit'
    print

if __name__ == '__main__':
    
    short_options = 'd:r:p:f:n:m:x:h'
    long_options = ['dynmat=', # specify dynmat.out file with e'vectors
                    'rlx=', # specify input file with relaxed coordinates
                    'prefix=', # specify prefix for output files
                    'fileformat=', # specify output file format
                    'nsteps=', # number of different scaled geometries to calculate (4)
                    'modes=', # comma separated list of modes to calculate (all)
                    'max=', # max scale of e'vec added to geometry (2.0)
                    'min=', # min scale of e'vec added to geometry (0.0)
                    'samefile', # print all coordinates in one file (trajectory)
                    'help', # display usage and exit
                    ]
    
    argv = sys.argv[1:]
    
    # default options
    fn_dynmat = ''
    fn_rlx = ''
    fn_prefix = ''
    nsteps = 1
    max_scale = 1.0
    min_scale = 1.0
    modes = ''
    samefile = False
    fileformat = 'xyz'
    
    try:
        opts, args = getopt.getopt(argv, short_options, long_options)
    except getopt.GetoptError, e:
        print
        print e
        print
        #usage()
        sys.exit(2)
    
    if args:
        print 'Undefined arguments(s):'
        print ' ', ', '.join([a for a in args])
        print
        #usage()
        sys.exit(2)
            
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-d', '--dynmat'):
            fn_dynmat = os.path.abspath(arg)
            if not os.path.isfile(fn_dynmat):
                raise IOError('dynmat: File not found: ' + arg)
        elif opt in ('-r', '--rlx'):
            fn_rlx = os.path.abspath(arg)
            if not os.path.isfile(fn_rlx):
                raise IOError('rlx: File not found: ' + arg)
        elif opt in ('-p', '--prefix'):
            fn_prefix = arg
        elif opt in ('-f', '--fileformat'):
            fileformat = arg
        elif opt in ('-n', '--nsteps'):
            nsteps = int(arg)
        elif opt in ('-x', '--max'):
            max_scale = float(arg)
        elif opt in ('--min', ):
            min_scale = float(arg)
        elif opt in ('--samefile', ):
            samefile = True
        elif opt in ('-m', '--modes'):
            modes = map(int, arg.split(','))
    
    if not fn_dynmat or not fn_rlx:
        print 'You must specify the dynmat.out and rlx.out files (-d and -r).'
        #usage()
        sys.exit(2)
    
    # read files
    evecs = read_evectors(fn_dynmat)
    eq_xyz = read_rlx_coords(fn_rlx)
    if not fn_prefix:
        fn_prefix = os.path.basename(fn_rlx.split('.')[0])
        
    # if modes are not given, take all modes
    if not modes:
        modes = sorted(evecs.keys())
    
    # write run files
    for i in modes:
        try:
            write_run_files(fn_prefix, fn_rlx, fileformat, eq_xyz, evecs[i], i, nsteps, max_scale, min_scale, samefile)
        except KeyError:
            print 'Mode index not found in file: %d' % i
    sys.exit(0)

#------------------------------------------------------------------------------#
