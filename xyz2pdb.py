#!/usr/bin/python

import sys
import scipy as sp

#work in progress

def read_xyz(filename):
    print 'Reading %s' % filename
    try:
        fin = open(filename, 'r')
    except IOError:
        print '%s not found.' % filename
        sys.exit(2)
    frames = []
    
    n_atoms = 0
    n_frames = 0
    
    rl = fin.readline
    # first line is n_atoms
    n_atoms = int(rl())
    # second line is comment/title
    
    DONE = False
    while not DONE:
        n_frames += 1
        frame_title = rl().strip()
        frame_atoms = []
        for i in range(n_atoms):
            element, x, y, z = rl().split()
            frame_atoms.append((element, map(float, (x, y, z))))
        frames.append((frame_title, frame_atoms))
        
        line = rl()
        # if empty line, we're done
        if not line.strip():
            DONE = True
        else:
            # check that number of atoms is the same
            if int(line) != n_atoms:
                print 'Different number of atoms in frame %d. Exiting.' % n_frames
                fin.close()
                sys.exit(1)
            #otherwise just continue with the loop
    return frames
    
            
def write_pdb(filename, frames):
    print 'Writing %s' % filename
    res_name = 'UNK'
    
    
    try:
        fout = open(filename, 'w')
    except IOError:
        print 'Could not write to %s.' % filename
        sys.exit(2)
    w = fout.write
    #w('REMARK   1 \n')
    w('REMARK   1 File created with xyz2pdb.py by FA\n')
    w('REMARK   2 \n')
    w('REMARK   2 Frametitles\n')
    
    for i, (frame_title, dump) in enumerate(frames):
        w('REMARK   2 Frame %d: "%s"\n' % (i, frame_title))
    
    for i, (frame_title, atoms) in enumerate(frames):
        w('MODEL      {i:>3}\n'.format(i=i+1))
        for j, (name, coords) in enumerate(atoms):
            w('HETATM{ID:>5}  {name:<3} {res}     1    {c[0]:8.3f}{c[1]:8.3f}{c[2]:8.3f}  1.00  0.00          {element:>2}\n'.format(ID=j+1, name=name, res=res_name, c=coords, element=name))
        w('ENDMDL\n')
    
    # guess chemical bonds
    d_min = 0.6
    d_max = 2.0
    
    dump, atoms = frames[0]
    
    conect = []
    for i, (n1, c1) in enumerate(atoms):
        current = []
        for j, (n2, c2) in enumerate(atoms):
            d2 = 0
            for di in range(3):
                x = c2[di] - c1[di]
                d2 += x*x
            d = sp.sqrt(d2)
            if d >= d_min and d <= d_max:
                current.append(j+1)
        if current:
            w('CONECT{0:>5}'.format(i+1))
            for j, id2 in enumerate(current):
                if j > 0 and j % 4 == 0:
                    w('\nCONECT{0:>5}'.format(i+1))
                w('{0:>5}'.format(id2))
            w('\n')

def usage(cmd):
    
    print 'Syntax: ', cmd, 'input1.xyz [input2.xyz [input3.xyz [...]]]'
    print
    print 'Converts a input.xyz file in input.pdb and guesses valence bonds.'

if __name__ == '__main__':
    args = sys.argv[1:]
    in_out = []
    if len(args) == 0:
        usage(sys.argv[0])
        sys.exit(1)
    #elif len(args) == 2 and args[0].endswith('.xyz') and args[1].endswith('.pdb'):
        #in_out.append((args[0], args[1]))
    else:
        for fin in args:
            if not fin.endswith('.xyz'):
                usage(sys.argv[0])
                sys.exit(1)
            else:
                frames = read_xyz(fin)
                write_pdb('%s.pdb' % fin[:-4], frames)
    sys.exit(0)
