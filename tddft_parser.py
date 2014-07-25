#!/usr/bin/python

#This is a script that will extract data
#from a Qchem TDDFT output file. 


import sys
import scipy as sp
from matplotlib import pyplot as plt

colors = ['r', 'y', 'g', 'c', 'b']

def read_file(inFile):
    data = []

    with open(inFile, 'r') as fin:
        for line in fin:
            if line.startswith(" Excited state") and "(eV)" in line:
                ls = line.split()
                n = int(ls[2].strip(":")) # number of excited state
                excitation = float(ls[-1]) # excitation energy in eV
                
                # read next line with Total energy
                # next(fin) advances the "iterator" fin and returns the next line, similar to fin.readline(). However, readline() clashes with the for loop.
                line = next(fin) 
                ls = line.split()
                total = float(ls[-1])
                
                # read next line with Multiplicity
                line = next(fin)
                ls = line.split()
                multiplicity = ls[-1]
                # or alternatively, convert into a number (but number needs to be string for the join() method further below to work)
                #if "Singlet" in line:
                #    m = "0" # or "1"
                #elif "Triplet" in line:
                #    m = "1" # or "3"
                
                # read next line with Trans. Mom.
                line = next(fin)
                ls = line.split()
                tm_x, tm_y, tm_z = map(float, ls[2:7:2])
                
                # read next line with Strength
                line = next(fin)
                ls = line.split()
                strength = float(ls[-1])
                
                # read next line with PBHT overlap
                line = next(fin)
                ls = line.split()
                pbht = float(ls[-1])
                
                data.append([n, excitation, total, multiplicity, tm_x,  tm_y, tm_z, strength, pbht])
    return data

def write_file(outFile, data):
    with open(outFile, "w") as fout:
        # write title line
        fout.write("State,Excitation energy,Total energy,Multiplicity,x_TDM,y_TDM,z_TDM,Strength,PBHT overlap\n")
        for state in data:
            fout.write(",".join(state) + "\n")

def generate_spectrum(data, x=sp.linspace(0, 10, 1000), gamma=.1, normalize=True):
    
    y = sp.zeros(len(x))
    
    for state in data:
        energy = state[1]
        intens = state[7]
        #print energy, intens
        x2 = (x-energy)*(x-energy)
        g2 = gamma*gamma
        tmpy = sp.exp(-x2/(2*g2))
        y += intens*tmpy/max(tmpy)
        
    if normalize:
        y = y/max(y)
    return sp.vstack((x,y)).transpose()

if __name__ == '__main__':
    argv = sys.argv[1:]
    
    offset = 1.0
    normalize=False
    zero = offset*(len(argv))
    i = 0
    for i, filename in enumerate(argv):
        data = read_file(filename)
        for state in data:
            energy = state[1]
            intens = state[7]
            plt.plot([energy, energy], [0+zero, intens+zero], color=colors[i%len(colors)], linewidth=2.0)
        
        xy = generate_spectrum(data, normalize=False)
        plt.plot(xy[:,0], xy[:,1]+zero, label=filename, color=colors[i%len(colors)], linewidth=2.0)
        zero -= offset
    
    i += 1
    fn_exp = '../AF594_exp.dat'
    xy = sp.loadtxt(fn_exp)
    # convert from nm to eV
    xy[:,0] = 1239.84187/xy[:,0]
    #xy[:,1] = xy[:,1]/max(xy[:,1])
    plt.plot(xy[:,0], xy[:,1]+zero, label="exp", color=colors[i%len(colors)], linewidth=2.0)
    
    plt.xlim((0.0,8.0))
    plt.legend(loc="upper left")
    plt.show()