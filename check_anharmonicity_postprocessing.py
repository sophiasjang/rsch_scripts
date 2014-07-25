#!/usr/bin/python
'''
reads energies from anharmonicity check claculations and writes them to a two
column file *_EvA.dat
'''
import sys
import getopt
import os
import re
def read_energies(directory, mode_n):
    print
    print 'Mode {0}:'.format(mode_n)
    root = os.getcwd()
    # create directory for mode
    mode_dir = os.path.join(root, directory)
    
    os.chdir(mode_dir)
    
    fn_base = ''
    scale_vs_energy = []
    all_scales = [d[5:] for d in os.listdir(os.getcwd()) if os.path.isdir(d) and d.startswith('scale')]
    for s in all_scales:
        scale_dir = './scale{0}'.format(s)
        all_files = [fn for fn in os.listdir(scale_dir) if os.path.isfile(os.path.join(scale_dir, fn))]
        for fn in all_files:
            m = re.match(r'(.+?)_mode{0}_scale{1}(\.[a-zA-Z]+)?\.out$'.format(mode_n, s), fn)
            if m:
                fn_base = m.group(1)
                fin = open(os.path.join(scale_dir, fn), 'r')
                for line in fin:
                    if line.startswith('!'):
                        totE = float(line.split()[-2])
                        scale_vs_energy.append((float(s), totE))
                        break
                else:
                    print '  No convergence for scale {0}.'.format(s)
                break
        else:
            print '  Warning: No matching .out file found in ./scale{0}'.format(s)
    
    os.chdir(root)
    
    if scale_vs_energy:
        fn_out = os.path.join(mode_dir, fn_base + '_EvA.dat')
        print '  Writing {0}.'.format(os.path.basename(fn_out))
        f = open(fn_out, 'w')
        for s, totE in sorted(scale_vs_energy):
            f.write('{0}  {1}\n'.format(s, totE))
        return os.path.relpath(fn_out)
    else:
        print '  No energies read.'
        return ''
    
     

def usage():
    print
    print 'Reads energies from anharmonicity check calculations and writes'\
           + ' them to a two\ncolumn file *_EvA.dat'
    print
    print 'syntax: %s [-m <list of modes>]' % sys.argv[0]

if __name__ == '__main__':
    
    short_options = 'm:'
    long_options = ['modes=', # comma separated list of modes to calculate
                    ]
    
    argv = sys.argv[1:]
    
    # default options
    modes = []
    
    try:
        opts, args = getopt.getopt(argv, short_options, long_options)
    except getopt.GetoptError, e:
        print
        print e
        usage()
        sys.exit(2)
    
    if args:
        print 'Undefined arguments(s):'
        print ' ', ', '.join([a for a in args])
        usage()
        sys.exit(2)
            
    for opt, arg in opts:
        if opt in ('-m', '--modes'):
            modes = map(int, arg.split(','))
    done = []
    files = []
    for d in os.listdir(os.getcwd()):
        if os.path.isdir(d) and d.startswith('mode'):
            mode = int(re.match(r'mode([0-9]+)[^0-9]*', d).group(1))
            if modes == [] or mode in modes:
                files.append(read_energies(d, mode))
                done.append(mode)
    # check if all modes where found
    for i in modes:
        if not i in done:
            print 'Warning: Mode %d not found.' % i
    print
    print 'Plot all files with:'
    print 'plot_generic.py {0}'.format(' '.join(files))
    
    sys.exit(0)

