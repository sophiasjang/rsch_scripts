#!/usr/bin/python
'''
convert from jcamp-dx format to x-y
might be unstable as the format is not 100% clear
'''
import sys
import scipy as sp

def readwrite(filename):
    fin = open(filename, 'r')
    fout = open(filename + '.dat', 'w')
    rl = fin.readline
    w = fout.write
    
    line = rl()
    while line and not '##XYDATA' in line:
        if '##XFACTOR' in line:
            xfactor = float(line.split('=')[-1])
        if '##YFACTOR' in line:
            yfactor = float(line.split('=')[-1])
        if '##LASTX' in line:
            lastx = float(line.split('=')[-1])
        if '##FIRSTX' in line:
            firstx = float(line.split('=')[-1])
        if '##NPOINTS' in line:
            npoints = float(line.split('=')[-1])
        line = rl()
    ### assuming that the above values are always defined
    deltax = (lastx-firstx)/(npoints-1)
    line = rl()
    x_check = None
    while not '##END' in line:
        lsplit = map(float, line.split())
        if x_check != None and x_check != lsplit[0]:
            #print 'ERROR'
            print 'old x - new x =', x_check - lsplit[0]
            #fin.close()
            #fout.close()
            #sys.exit(1)
        x0 = lsplit.pop(0)
        for i in range(len(lsplit)):
            w('{0:f} {1:f}\n'.format(xfactor*x0+i*deltax, yfactor*lsplit[i]))
        x_check = x0 + deltax*len(lsplit)
        line = rl()
    
    ### in case values are not defined
    #old_data = []
    #new_data = []
    #x = []
    #y = []
    
    #line = rl()
    #while line:
        #if old_data:
            #x_old = old_data.pop(0)
        #new_data = line.split()
        #x_new = new_data.pop(0)
        #x_range = sp.linrange(x_old, x_new, len(old_data)+1)
        #sp.append(x, x_range)
        #sp.append(y, old_data)
        #line = rl()

if __name__ == '__main__':
    files = sys.argv[1:]
    for f in files:
        readwrite(f)