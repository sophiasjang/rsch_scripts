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

def read_file_qchem(filename, print_freqs=True):
    f = open(filename, 'r')
    rl = f.readline
    
    all_modes = []
    
    line = rl()
    while line and not 'VIBRATIONAL ANALYSIS' in line:
        line = rl()
    
    while line:
        while line and not 'Mode:' in line:
            line = rl()
        ids = map(int, line[15:].split())
        line = rl()
        freqs = map(float, line[15:].split())
        line = rl()
        force_const = map(float, line[15:].split())
        line = rl()
        red_mass = map(float, line[15:].split())
        line = rl()
        IR_active = [(True if i == 'YES' else False) for i in line[15:].split()]
        line = rl()
        IR_intens = map(float, line[15:].split())
        line = rl()
        Raman_active = [(True if i == 'YES' else False) for i in line[15:].split()]
        
        all_modes.extend(zip(freqs, IR_intens, IR_active, Raman_active, force_const))
        
        line = rl()
    f.close()
    
    if print_freqs:
        print
        print filename
        print_frequencies(all_modes)
        
    
    return all_modes

def read_file_molden(filename, print_freqs=True):
    f = open(filename, 'r')
    rl = f.readline
    
    freqs = []
    IR_intens = []
    IR_active = []
    force_const = []
    
    line = rl()
    while line and not '[Molden Format]' in line:
        line = rl()
    
    while line and not '[FREQ]' in line:
        line = rl()
    
    line = rl()
    while not '[' in line:
        freqs.append(float(line.strip()))
        line = rl()
    
    while not '[INT]' in line:
        line = rl()
    
    for i in range(len(freqs)):
        line = rl()
        IR_intens.append(float(line.strip()))
    
    # no IR active keyword in molden format
    IR_active = [True]*len(freqs)
    Raman_active = [False]*len(freqs)
    force_const = [0]*len(freqs)
    
    
    f.close()
    all_modes = zip(freqs, IR_intens, IR_active, Raman_active, force_const)
    
    if print_freqs:
        print
        print filename
        print_frequencies(all_modes)
    
    return all_modes

def print_frequencies(all_modes):
    print '[freq/cm^-1, I/km/mol., IR/R/IA, force const./mdyn/A]'
    for freq, IR_intens, IR_active, Raman_active, force_const in all_modes:
            if IR_active or Raman_active:
                if not Raman_active:
                    active = 'IR'
                elif not IR_active:
                    active = 'R'
                else:
                    active = 'IR/R'
            else:
                active = 'IA'
            print '{0:7.2f}  {1:10.6f}  {2:<4}  {3:7.4f}'.format(freq, 
                    IR_intens, active, force_const)
    
def get_spectrum(modes, gamma=20, x=None, normalize=False, shape='Lorentzian'):
    '''
    takes a list of (freq, Intensity) lists and returns x,y-data with
    Lorentzian or Gaussian lineshapes
    '''
    
    if x is not None:
        # if x is a 2D array
        if len(x.shape) == 2:
            # and has one row
            if x.shape[0] == 1:
                x = x[0,:]
            # or has one column
            if  x.shape[1] == 1:
                x = x[:,0]
        if len(x.shape) > 2:
            print 'x array has wrong dimensions, using default.'
            x = None
    
    if x is None:
        x = sp.linspace(0, 3500, 100000)
    
    y = sp.zeros(len(x))
    
    if shape == 'Lorentzian':
        for freq, IR_intens in modes:
            x2 = (x-freq)*(x-freq)
            g2 = gamma*gamma
            y += IR_intens*gamma/(sp.pi*(x2+g2))
    if shape == 'Gaussian':
        print 'Not implemented yet. Sorry.'
    if normalize:
        y = y/max(y)
    
    return sp.vstack((x,y)).transpose()

    
def plot_figure(data, spectr='IR'):
    
    plt.figure()
    plt.xlabel(r'Frequency ($cm^{-1}$)', fontsize=afont)
    plt.ylabel(r'Intensity ($a.u.$)', fontsize=afont)
    
    x = sp.linspace(0, 3500, 100000)
    gamma = 20
        
    for i, title in enumerate(data):
        # IR spectrum
        # get Lorentzian line shape for each frequency
        if spectr == 'IR':
            index = 2
        elif spectr == 'Raman':
            index = 3
            print 'WARNING: Raman spectrum will have IR intensities.'
        else:
            print 'spectr parameter "{0}" not understood.'.format(spectr)
            sys.exit(1)
        freq_intens = [(d[0], d[1]) for d in data[title] if d[index]]
        xy = get_spectrum(freq_intens, gamma, x)
        plt.plot(xy[:,0], xy[:,1], label=title, color=colors[i%len(colors)])
    
    plt.legend()
    plt.show()
        
if __name__ == '__main__':
    files = sys.argv[1:]
    data = {}
    for f in files:
        data[f] = read_file_qchem(f)
    plot_figure(data)
