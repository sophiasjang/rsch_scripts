#!/usr/bin/python
'''
takes qchem output and plots the vibrational frequencies 
'''

import sys
import scipy as sp
from matplotlib import pyplot as plt

afont = 16
tfont = 18
colors = ['b', 'r', 'y', 'g', 'c']

def read(filename, print_freqs=True):
    f = open(filename, 'r')
    rl = f.readline
    
    all_modes = []
    
    line = rl()
    while line and not 'VIBRATIONAL ANALYSIS' in line:
        line = rl()
    
    while line:
        while line and not 'Mode:' in line:
            line = rl()
        print line
        ids = map(int, line[15:].split()[1:])
        print 'ids', ids
        line = rl()
        print line
        freqs = map(float, line[15:].split()[1:])
        print 'freqs', freqs
        line = rl()
        print line
        force_const = map(float, line[15:].split()[1:])
        print 'force constants', force_const
        line = rl()
        print line
        red_mass = map(float, line[15:].split()[1:])
        print 'red mass', red_mass
        line = rl()
        print line
        IR_active = [(True if i == 'YES' else False) for i in line[15:].split()[1:]]
        print 'IR active', IR_active
        line = rl()
        print line
        IR_intens = map(float, line[15:].split()[1:])
        print 'IR intens', IR_intens
        line = rl()
        print line
        Raman_active = [(True if i == 'YES' else False) for i in line[15:].split()[1:]]
        print 'Raman active', Raman_active
        all_modes.extend(zip(freqs, IR_intens, IR_active))
        
        line = rl()
    f.close()
    
    if print_freqs:
        print
        print filename
        print '[freq/cm^-1, I/a.u.]'
        for freq, IR_intens, IR_active in all_modes:
            if IR_active:
                print freq, IR_intens
    
    return all_modes

def get_spectrum(modes, gamma=20, x=None, normalize=False, shape='Lorentzian'):
    '''
    takes a list of (freq, Intensity, active) lists and returns x,y-data with
    Lorentzian or Gaussian lineshapes
    '''
    # if x is a 2D array and has one row
    if x and len(x.shape) == 2 and x.shape[0] == 1:
        x = x[0,:]
    # if x is a 2D array and has one column
    elif x and len(x.shape) == 2 and  x.shape[1] == 1:
        x = x[:,0]
    else:
        if x:
            print 'x array has wrong dimensions, using default.'
        x = sp.linspace(0, 3500, 100000)
    
    y = sp.zeros(len(x))
    
    if shape == 'Lorentzian':
        for freq, IR_intens, IR_active in modes:
            if IR_active:
                x2 = (x-freq)*(x-freq)
                g2 = gamma*gamma
                y += IR_intens*gamma/(sp.pi*(x2+g2))
    if shape == 'Gaussian':
        print 'Not implemented yet. Sorry.'
    if normalize:
        y = y/max(y)
    
    return sp.vstack((x,y)).transpose()

    
def plot_figure(data):
    
    plt.figure()
    plt.xlabel(r'Frequency ($cm^{-1}$)', fontsize=afont)
    plt.ylabel(r'Intensity ($a.u.$)', fontsize=afont)
    
    x = sp.linspace(0, 3500, 100000)
    gamma = 20
        
    for i, title in enumerate(data):
        # IR spectrum
        # get Lorentzian line shape for each frequency
        xy = get_spectrum(data[title], gamma, x)
        plt.plot(xy[:,0], xy[:,1], label=title, color=colors[i%len(colors)])
    
    plt.legend()
    plt.show()
        
if __name__ == '__main__':
    files = sys.argv[1:]
    data = {}
    for f in files:
        data[f] = read(f)
    plot_figure(data)
