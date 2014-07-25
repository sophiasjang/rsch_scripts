#!/usr/bin/python
'''
write run files to check anharmonicity of modes
'''

# read mode vectors

# read geometry

# for several times
    # shift geometry by a certain amount along evector

    # run espresso single point energy and get total energy

# plot shift vs energy -> should be parabolic

import sys
import os
import re
import getopt
from subprocess import Popen, PIPE

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

def read_pwscf_coords(filename):
    f = open(filename, 'r')
    # find # of atoms
    while True:
        line = f.readline().strip()
        if not line:
            break
        elif line.startswith('nat'):
            m = re.search('nat += +([0-9]+)', line)
            n_atoms = int(m.group(1))
            break
    # find atomic positions
    eq_coords = []
    while True:
        line = f.readline().strip()
        if not line:
            break
        elif line.startswith('ATOMIC_POSITIONS'):
            unit = line.split()[-1]
            for i in range(n_atoms):
                ls = f.readline().split()
                atom = ls.pop(0)
                xyz = map(float, ls)
                # TODO convert to angstrom if not already
                if unit != 'angstrom':
                    raise Exception('Can not handle unit. Please check script.')
                eq_coords.append([atom, xyz])
    return eq_coords

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
    
def write_run_files(fn_template, eq_xyz, evecs, mode_n, nsteps, max_scale, min_scale):
    '''
    write all necessary files to run job for one mode
    '''
    # read template and prepare for modification
    
    root = os.getcwd()
    # create directory for mode
    mode_dir = os.path.join(root, 'mode{0}_{1}-{2}'.format(mode_n, min_scale, max_scale))
    if not os.path.isdir(mode_dir):
        os.mkdir(mode_dir)
    # go into mode directory
    os.chdir(mode_dir)
    
    #width = max([len(str(n)) for n in range(nsteps+1)])
    jobs = []
    
    for n in range(nsteps):
        if nsteps == 1:
            # try to find the non-default value
            if max_scale != 1.0:
                scale = max_scale
            elif min_scale != 0.0:
                scale = min_scale
            else:
                scale = max_scale
        else:
            scale = 1.0*n/(nsteps-1)*(max_scale - min_scale) + min_scale
        scale_dir = './scale{0:0>6.4f}'.format(scale)
        # create subdirectories for each displacement
        if not os.path.isdir(scale_dir):
            os.mkdir(scale_dir)
        fin = open(fn_template, 'r')
        # new filename for input file with displacement
        # remove .in extension if present
        fn_base = re.sub(r'((\.[^.]+))(\.in$)?',
                        r'_mode{0}_scale{1:0>6.4f}\1'.format(mode_n,
                                                        scale),
                        os.path.basename(fn_template))
        fn_out = os.path.join(scale_dir, fn_base)
        jobs.append(fn_out)
        fout = open(fn_out + '.in', 'w')
        while True:
            line = fin.readline()
            if not line:
                break
            elif 'prefix' in line:
                prefix = re.sub(r'(\.[a-zA-Z]+)+$', '', fn_base)
                line = "   prefix = '{0}'\n".format(prefix)
            elif 'outdir' in line:
                line = "   outdir = '{0}'\n".format(scale_dir)
            elif 'wfcdir' in line:
                line = "   wfcdir = '{0}'\n".format(scale_dir)
            fout.write(line)
            if 'ATOMIC_POSITIONS' in line:
                for i, (atom, coords) in enumerate(eq_xyz):
                    fin.readline() # dump old coordinates
                    displaced = [c[0] + scale*c[1] for c in zip(coords, evecs[i])]
                    fout.write('{0} {1:>13.9f} {2:>13.9f} {3:>13.9f}\n'.format(atom, displaced[0], displaced[1], displaced[2]))
        fin.close()
        fout.close()
    
    # write run script in mode directory, that can be submitted to qsub and will
    #    run all displacement step calculations in turn
    fn_run = 'run_mode{0}.sh'.format(mode_n)
    frun = open(fn_run, 'w')
    w = frun.write
    w('#PBS -N mode_{0}\n'.format(mode_n))
    w('#PBS -l nodes=1:ppn=8:vulcan\n')
    w('#PBS -q vulcan_batch\n')
    w('#PBS -o job.out\n')
    w('#PBS -e job.err\n')
    w('#PBS -l walltime=12:00:00\n')
    w('#PBS -m e -M altvater@berkeley.edu\n')
    w('\n')
    w('export MODULEPATH=/global/software/sl-6.x86_64/modfiles/langs:/global/software/sl-6.x86_64/modfiles/tools\n')
    w('module load openmpi\n')
    w('module load intel\n')
    w('module load mkl\n')
    w('module load fftw\n')
    w('\n')
    w('filenames=(\n')
    for fn in jobs:
        w('           "{0}"\n'.format(fn))
    w('          )\n')
    w('\n')
    w('cd $PBS_O_WORKDIR\n')
    w('for i in {0}\n'.format(' '.join(map(str, range(len(jobs))))))
    w('do\n')
    w('    mpirun /global/home/users/altvater/espresso-5.0/bin/pw.x < ${filenames[i]}.in > ${filenames[i]}.out\n')
    w('done\n')
    w('check_anharmonicity_postprocessing.py -m {0} > job_post.log'.format(mode_n))
    
    os.chdir(root)
    
def usage():
    print
    print 'Writes run files to check anharmonicity of modes.'
    print
    print 'syntax: check_anharmonicity.py -d dynmat -p pwscf.in [-hrmnx]'
    print
    print 'Options'
    print '  -d, --dynmat    specify dynmat.out file with e\'vectors'
    print '  -p, --pwscf     specify pwscf input file to run calculation with'
    print '  -r, --rlx       specify input file with relaxed coordinates'
    print '  -n, --nsteps    number of different scaled geometries to calculate'
    print '  -m, --modes     comma separated list of modes to calculate (1,2,3 or "1, 2, 3")'
    print '  -x, --max       maximum scale applied to e\'vectors'
    print '      --min       maximum scale applied to e\'vectors (can be negative)'
    print '  -h, --help      print this information and exit'
    print

if __name__ == '__main__':
    
    short_options = 'd:p:r:n:m:x:h'
    long_options = ['dynmat=', # specify dynmat.out file with e'vectors
                    'pwscf=', # specify pwscf input file to run calculation with
                    'rlx=', # specify input file with relaxed coordinates
                    'nsteps=', # number of different scaled geometries to calculate (4)
                    'modes=', # comma separated list of modes to calculate (all)
                    'max=', # max scale of e'vec added to geometry (2.0)
                    'min=', # min scale of e'vec added to geometry (0.0)
                    'help', # display usage and exit
                    ]
    
    argv = sys.argv[1:]
    
    # default options
    fn_dynmat = ''
    fn_pwscf = ''
    fn_rlx = ''
    nsteps = 4
    max_scale = 1.0
    min_scale = 0.0
    modes = ''
    
    
    try:
        opts, args = getopt.getopt(argv, short_options, long_options)
    except getopt.GetoptError, e:
        print
        print e
        #usage()
        sys.exit(2)
    
    if args:
        print 'Undefined arguments(s):'
        print ' ', ', '.join([a for a in args])
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
        elif opt in ('-p', '--pwscf'):
            fn_pwscf = os.path.abspath(arg)
            if not os.path.isfile(fn_pwscf):
                raise IOError('pwscf: File not found: ' + arg)
        elif opt in ('-r', '--rlx'):
            fn_rlx = os.path.abspath(arg)
            if not os.path.isfile(fn_rlx):
                raise IOError('rlx: File not found: ' + arg)
        elif opt in ('-n', '--nsteps'):
            nsteps = int(arg)
        elif opt in ('-x', '--max'):
            max_scale = float(arg)
        elif opt in ('--min', ):
            min_scale = float(arg)
        elif opt in ('-m', '--modes'):
            modes = map(int, arg.split(','))
    
    if not fn_dynmat or not fn_pwscf:
        print 'You must specify the dynmat.out and pwscf.in files (-d and -p).'
        #usage()
        sys.exit(2)
    
    
    # read files
    evecs = read_evectors(fn_dynmat)
    if fn_rlx:
        eq_xyz = read_rlx_coords(fn_rlx)
    else:
        eq_xyz = read_pwscf_coords(fn_pwscf)
        print 'Coordinates read from pwscf input file.'
    
    # if modes are not given, take all modes
    if not modes:
        modes = sorted(evecs.keys())
    
    # write run files
    for i in modes:
        try:
            write_run_files(fn_pwscf, eq_xyz, evecs[i], i, nsteps, max_scale, min_scale)
        except KeyError:
            print 'Mode index not found in file: %d' % i
    sys.exit(0)

#------------------------------------------------------------------------------#
