#!/usr/bin/python
'''
phonon_fd.py

workflow

- have well converged equilibrium geometry.

36 displacement vectors u_ia
    where i = atom index
          a = x, y, z
u_1x = u0 * ( 1 0 0 0 ...)
u_1y = u0 * ( 0 1 0 0 ...)
u_1z = u0 * ( 0 0 1 0 ...)
u_2x = u0 * ( 0 0 0 1 ...)

for i' in range(n_atoms):
    for a' in (x, y, z):
        displace eq_geometry by u_i'a' (== move atom i' in direction a' by u0)
        calculate forces
        for i in range(n_atoms):
            for a in (x, y, z):
                get F_ia == force on atom i in direction a
        
        i*a_th column of force constant matrix with matrix elements
        k_ia,i'a' = F_ia / u0

average symmetric elements:
for i in range(n_atoms):
    for a in (x, y, z):
        k_ia,i'a' = k_i'a',ia = (k_ia,i'a' + k_i'a',ia) / 2

calculate dynamical matrix:
D_ia,i'a' = 1/sqrt(m_ia * m_i'a') k_ia,i'a'

diagolanize dynamical Matrix to get e'vectors (normal modes) and e'values (= frequencies)
'''
import sys
import os
import re
from subprocess import PIPE, Popen


infile = 'input.pwscf.in'
u0 = 0.025 # Angstrom


def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


# read template
f_template = open(infile, 'r')
lines = {'before': [], 'coords': [], 'after': []}
FLAG = 'before'
for line in f_template:
    if FLAG == 'coords' and len(line.strip().split()) != 4:
        FLAG = 'after'
    lines[FLAG].append(line)
    if line.startswith('ATOMIC_POSITIONS'):
        FLAG = 'coords'

# write files where one coordinate of one atom is displaced by u0
n_atoms = len(lines['coords'])
with open('mymatrix', 'w') as mat_file:
    for i in range(n_atoms):
        print 'Working on atom {0}'.format(i)
        for di in range(3):
            calc_fn = '{0}_atom{1}-{2}.pwscf.in'.format(infile, i+1, di+1)
            out_fn = '{0}_atom{1}-{2}.pwscf.out'.format(infile, i+1, di+1)
            with open(calc_fn, 'w') as calc_file:
                for line in lines['before']:
                    calc_file.write(line)
                for j, line in enumerate(lines['coords']):
                    if j != i:
                        calc_file.write(line)
                    else:
                        # add u0 to specified coordinate
                        calc_file.write(
                            re.sub('( *[^ ]+( +[^ ]+){%d}) +[^ ]+' % (di), 
                                    r'\1 %f' % (float(line.strip().split()[di+1]) + u0,), 
                                    line, count=1)
                                    )
                for line in lines['after']:
                    calc_file.write(line)
            
            # calculate forces
            print 'cat < {0} > {1}'.format(calc_fn, out_fn)
            p = Popen('cat < {0} > {1}'.format(calc_fn, out_fn), stderr=PIPE, shell=True)
            (stdout, stderr) = p.communicate()
            if stderr:
                print stderr
            #sys.exit(0)
    
            with open(out_fn, 'r') as out_file:
                line = out_file.readline()
                while line and not 'Forces acting on atoms' in line:
                    line = out_file.readline()
                out_file.readline() # dump             
                line = out_file.readline()
                while line.strip():
                    fx, fy, fz = map(float, line.strip().split()[-3:])
                    mat_file.write('{0}  {1}  {2} '.format(fx, fy, fz))
                    line = out_file.readline()
                mat_file.write('\n')
            
            # remove temporary files
            os.remove(out_fn)
            os.remove(calc_fn)
            
