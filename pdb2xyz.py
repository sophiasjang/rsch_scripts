#!/usr/bin/python

import sys
import scipy as sp
import re

def pdb2xyz(file_in, file_out, metal=False):
    try:
        fin = open(file_in, 'r')
    except IOError:
        print 'Could not read %s.' % filename
        sys.exit(2)
    
    frames = []
    current = []
    for line in fin:
        record = line[:6].strip()
        #if record in ('ATOM', 'HETATM', 'END', 'MODEL', 'TER'):
        if record in ('ATOM', 'HETATM'):
            x = line[30:38]
            y = line[38:46]
            z = line[46:54]
            coords = map(float, (x, y, z))
            element = line[76:78].strip()
            
            # guess element from atom name
            if not element:
                element = re.sub("[0-9]", "", line[12:16])[:2].upper()
                if len(element) > 1:
                    if element[0] == 'C':
                        if element[1] in ("A", "L", "R", "O", "U", "D", "S", "E"):
                            if not metal:
                                print "INFO: %s found and replaced with C (index %s)." % (element, line[6:11].strip()) 
                                element = "C"
                        else:
                            element = "C"
                            
                    elif element[0] == 'H':
                        if element[1] in ("E", "F", "G"):
                            if not metal:
                                print "INFO: %s found and replaced with H (index %s)." % (element, line[6:11].strip()) 
                                element = "H"
                        else:
                            element = "H"
                    
                    elif element[0] == 'N':
                        if element[1] in ("E", "A", "I", "B"):
                            if not metal:
                                print "INFO: %s found and replaced with N (index %s)." % (element, line[6:11].strip()) 
                                element = "N"
                        else:
                            element = "N"
            
            current.append((element, coords))
        
        elif record == 'END':
            frames.append(current)
            current = []
    else:
        if current:
            frames.append(current)
    
    # check if all frames have the same number of atoms
    n_atoms = len(frames[0])
    if len(frames) > 1:
        if [n_atoms]*len(frames) != map(len, frames):
            print "WARNING: Models in pdb have different number of atoms."
    try:
        fout = open(file_out, 'w')
    except IOError:
        print 'Could not write to %s.' % filename
        sys.exit(2)
    w = fout.write
    w(str(n_atoms))
    w('\n')
    w('%s translated with pdb2xyz.py by FA\n' % re.sub('.*/', '', file_in))
    for frame in frames:
        for element, (x, y, z) in frame:
            w("{0}  {1:>8.3f}  {2:>8.3f}  {3:>8.3f}\n".format(element, x, y, z))
        w('\n')
    
    fout.close()
    
def usage(cmd):
    print
    print 'Converts a input.pdb file in input.xyz.'
    print
    print 'Syntax:  pdb2xyz input1.pdb [input2.pdb [input3.pdb [...]]]'
    print
    
if __name__ == '__main__':
    args = sys.argv[1:]
    in_out = []
    if len(args) == 0:
        print 'You need to specify at least one input file (.pdb).'
        usage(sys.argv[0])
        sys.exit(1)
    #elif len(args) == 2 and args[0].endswith('.xyz') and args[1].endswith('.pdb'):
        #in_out.append((args[0], args[1]))
    else:
        for fin in args:
            if not fin.endswith('.pdb'):
                print 'Wrong extension in %s' % fin
            else:
                fout = '%s.xyz' % fin[:-4]
                print 'Writing %s.' % fout
                frames = pdb2xyz(fin, fout)
    sys.exit(0)
