#!/usr/bin/python

import sys

def read_qchem(filename):
    print 'Reading %s' % filename
    try:
        fin = open(filename, 'r')
    except IOError:
        print '%s not found.' % filename
        return None
    rl = fin.readline
    confs = []
    line = rl()
    while line:
        if 'Standard Nuclear Orientation (Angstroms)' in line:
            rl() #     I     Atom         X            Y            Z
            rl() #  ----------------------------------------------------
            
            names = []
            coords = []
            
            split = rl().split()
            while split and split[0].isdigit():
                i, name, x, y, z = split
                names.append(name)
                coords.append(map(float, (x, y, z)))
                split = rl().split()
            confs.append({'names': names, 'coords': coords})
        line = rl()
    return confs
    
def write_pdb(filename, confs):
    print 'Writing %s' % filename
    res_name = 'UNK'
    
    
    try:
        fout = open(filename, 'w')
    except IOError:
        print 'Could not write to %s.' % filename
        return
    w = fout.write
    w('REMARK   File created with qchem2pdb.py by FA\n')
    w('\n')
    for i, conf in enumerate(confs):
        names = conf['names']
        coords = conf['coords']
        w('MODEL      {i:>3}\n'.format(i=i+1))
        for j in range(len(conf['names'])):
            w('HETATM{ID:>5}  {name:<3} {res}     1    {c[0]:8.3f}{c[1]:8.3f}{c[2]:8.3f}  1.00  0.00          {element:>2}\n'.format(ID=j, name=names[j], res=res_name, c=coords[j], element=names[j]))
        w('ENDMDL\n')

def usage(cmd):
    print cmd, 'input.out output.pdb'
    print ' OR'
    print cmd, 'input1.out [input2.out [input3.out [...]]]'
    print

if __name__ == '__main__':
    args = sys.argv[1:]
    in_out = []
    if len(args) == 0:
        usage(sys.argv[0])
        sys.exit(1)
    elif len(args) == 2 and args[0].endswith('.out') and args[1].endswith('.pdb'):
        in_out.append((args[0], args[1]))
    else:
        for fin in args:
            if not fin.endswith('.out'):
                usage(sys.argv[0])
                sys.exit(1)
            else:
                in_out.append((fin, '%s.pdb' % fin[:-4]))
    for fout, fpdb in in_out:
        confs = read_qchem(fout)
        write_pdb(fpdb, confs)
    sys.exit(0)