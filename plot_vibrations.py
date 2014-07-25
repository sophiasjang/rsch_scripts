#!/usr/bin/python
'''
takes qchem output and plots the vibrational frequencies 
'''

import sys
import getopt
import scipy as sp
from matplotlib import pyplot as plt
import re
import os

afont = 20
tfont = 22
colors = ['r', 'y', 'g', 'c', 'b']

eV_per_cm = 0.000123984187

## read input files ##

'''
functions read file and return a list tuples containing
(freqs, IR_intens, IR_active, Raman_active, force_const)

print found frequencies to stdout if print_freqs is True
'''

def read_file_list(filename):
    ret = []
    fin = open(filename, 'r')
    for line in fin:
        if line.strip() and not line.strip().startswith('#'):
            lst = re.split('(.+)( -e | -m | -q | -g | -a | --espresso | --aims | --molden | --qchem | --generic | --exp)(.+)', line)
            try:
                title, typ, filename = map(str.strip, lst[1:4])
            except (ValueError, KeyError):
                print
                print 'ERROR in', filename
                print 'Format of lines in list should be:'
                print '  title  -q|e|m|a|g|--qchem|espresso|molden|aims|generic  filename'
                print 'Comment lines start with a #.'
                print 'Aborting.'
                sys.exit(1)
            ret.append((title, typ, filename))
    return ret

def read_file_2col(filename, print_freqs=True):
    # reads 2-column file with frequencies in the 1st and intensities in the 2nd
    data = sp.loadtxt(filename)
    
    # append two columns of 1's for compatibility (IR_active and Raman_active)
    data = sp.append(data, sp.ones((len(data), 2)), axis=1)
    # append one column of 0's for compatibility (force_const)
    all_modes = sp.append(data, sp.zeros((len(data), 1)), axis=1)
    if print_freqs and len(all_modes) != 0:
        print_frequencies(filename, all_modes)
    
    return all_modes

def read_file_espresso(filename, print_freqs=True):
    # read outdput from Quantum ESPRESSO
    f = open(filename, 'r')
    rl = f.readline
    
    all_modes = []
    
    line = rl()
    while not (line.startswith('#') and 'mode' in line) and line:
        line = rl()
    
    data = []
    line = rl()
    while line.strip():
        i, freq, freq_THz, IR_intens = map(float, line.strip().split())
        data.append((freq, IR_intens))
        line = rl()
    f.close()
    
    # append two columns of 1's for compatibility (IR_active and Raman_active)
    data = sp.append(data, sp.ones((len(data), 2)), axis=1)
    # append one column of 0's for compatibility (force_const)
    all_modes = sp.append(data, sp.zeros((len(data), 1)), axis=1)
    if print_freqs and len(all_modes) != 0:
        print_frequencies(filename, all_modes)
    
    return all_modes

def read_file_aims(filename, print_freqs=True):
    # read outdput from Quantum ESPRESSO
    f = open(filename, 'r')
    rl = f.readline
    
    all_modes = []
    
    line = rl()
    while not ('frequencies found:') in line and line:
        line = rl()
    rl() # dump
    
    data = []
    line = rl()
    while line.strip():
        i, freq, zero_point_E, IR_intens = map(float, line.strip().split())
        data.append((freq, IR_intens))
        line = rl()
    f.close()
    
    # append two columns of 1's for compatibility (IR_active and Raman_active)
    data = sp.append(data, sp.ones((len(data), 2)), axis=1)
    # append one column of 0's for compatibility (force_const)
    all_modes = sp.append(data, sp.zeros((len(data), 1)), axis=1)
    if print_freqs and len(all_modes) != 0:
        print_frequencies(filename, all_modes)
    
    return all_modes

    
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
    
    if print_freqs and len(all_modes) != 0:
        print_frequencies(filename, all_modes)
        
    
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
    while line and not '[' in line:
        freqs.append(float(line.strip()))
        line = rl()
    
    while line and not '[INT]' in line:
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
    
    if print_freqs and len(all_modes) != 0:
        print_frequencies(all_modes)
    
    return all_modes

def print_frequencies(filename, all_modes):
    print
    print filename
    print '[freq/cm^-1, I, IR/R/IA, force const./mdyn/A]'
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

def get_spectrum(modes, gamma=20, x=None, normalize=False, shape='lorentzian'):
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
    
    if shape.lower() not in ('lorentzian', 'gaussian'):
        shape = 'lorentzian'
        print 'Lineshape argument not understood. Changed to Lorentzian.'
    
    if shape.lower() == 'lorentzian':
        for freq, intens in modes:
            x2 = (x-freq)*(x-freq)
            g2 = gamma*gamma
            #y += intens*gamma/(sp.pi*(x2+g2))
            y += intens*g2/(x2+g2)
    elif shape.lower() == 'gaussian':
        for freq, intens in modes:
            x2 = (x-freq)*(x-freq)
            g2 = gamma*gamma
            tmpy = sp.exp(-x2/(2*g2))
            y += intens*tmpy/max(tmpy)
    
    if normalize:
        y = y/max(y)
    
    return sp.vstack((x,y)).transpose()

    
    
def get_text_positions(x_data, y_data, txt_width, txt_height):
    a = zip(y_data, x_data)
    text_positions = y_data.copy()
    for index, (y, x) in enumerate(a):
        local_text_positions = [i for i in a if i[0] > (y - txt_height) 
                            and (abs(i[1] - x) < txt_width * 2) and i != (y,x)]
        if local_text_positions:
            sorted_ltp = sorted(local_text_positions)
            if abs(sorted_ltp[0][0] - y) < txt_height: #True == collision
                differ = sp.diff(sorted_ltp, axis=0)
                a[index] = (sorted_ltp[-1][0] + txt_height, a[index][1])
                text_positions[index] = sorted_ltp[-1][0] + txt_height
                for k, (j, m) in enumerate(differ):
                    #j is the vertical distance between words
                    if j > txt_height * 2: #if True then room to fit a word in
                        a[index] = (sorted_ltp[k][0] + txt_height, a[index][1])
                        text_positions[index] = sorted_ltp[k][0] + txt_height
                        break
    return text_positions

def text_plotter(x_data, y_data, text_positions, offset, axis,txt_width,txt_height, color):
    for x,y,t in zip(x_data, y_data, text_positions):
        
        plt.annotate(str(x), xy=(x, y+offset), xycoords='data', 
                     xytext=(x-txt_width, t+offset), textcoords='data',
                     #ha='right', va='bottom',
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', alpha=0.3, color='k') if y != t else None,
                     color=color)
        
        #axis.text(x - txt_width, 1.01*t, '%d'%int(x),rotation=90, color=color)
        #if y != t:
            #axis.arrow(x, t,0,y-t, color='red',alpha=0.3, width=1, 
                       #head_width=0.2*txt_width, head_length=txt_height*0.3, 
                       #zorder=0,length_includes_head=True)

                       
                       
def plot_figure(data,
                spectr='IR',
                plot_all_modes=False,
                show_table=False,
                normalize=False,
                shape='lorentzian',
                linewidth=10.0,
                offset=0.0,
                xlim=[0, 4000],
                ylim=[],
                legendloc="upper right",
                saveas=''):
    
    fig = plt.figure()
    if show_table:
        plt.subplot2grid((1, 3), (0,0), colspan=2)
    plt.xlabel('Frequency (cm$^{-1}$)')#, fontsize=afont)
    plt.ylabel(r'Intensity (a.u.)')#, fontsize=afont)
    plt.xlim(*xlim)
    if ylim:
        plt.ylim(*ylim)
    x = sp.linspace(xlim[0], xlim[1], 100000)
    
    if spectr.lower() not in ('ir', 'raman'):
        spectr = 'ir'
        print 'Spectrum type not understood. Changed to IR.'
    
    if spectr.lower() == 'ir':
        index = 2
    elif spectr.lower() == 'raman':
        index = 3
        print 'WARNING: Raman spectrum will have IR intensities.'
    
    zero = offset*(len(data)-1)
    for i, (title, numbers) in enumerate(data):
        # make sure title is latex proof
        title = title.replace('_', '\_')
        
        # list with freq, IR_intens, IR_active, Raman_active, force_const
        if len(numbers[0]) == 5:
            # get Lorentzian line shape for each frequency
            freq_intens = [(d[0], d[1]) for d in numbers if d[index]]
            xy = get_spectrum(freq_intens, linewidth, x, normalize=normalize, shape=shape)
            plt.plot(xy[:,0], xy[:,1]+zero, label=title, color=colors[i%len(colors)], linewidth=2.0)
            if plot_all_modes:
                #txt_height = 0.1*(plt.ylim()[1] - plt.ylim()[0])
                #txt_width = 0.05*(plt.xlim()[1] - plt.xlim()[0])
                #Get the corrected text positions, then write the text.
                #text_positions = get_text_positions(numbers[:,0], numbers[:,1], txt_width, txt_height)
                #text_plotter(numbers[:,0], numbers[:,1], text_positions, zero, plt.gca(), txt_width, txt_height, colors[i%len(colors)])

                #plt.ylim(0, max(text_positions)+2*txt_height)
                if normalize:
                    N = max(numbers[:,1])
                else:
                    N = 1
                plt.vlines(numbers[:,0], 0+zero, max(numbers[:,1])/N+zero, color=colors[i%len(colors)], linestyles='dotted')
                plt.vlines(numbers[:,0], sp.zeros(numbers[:,1].shape)+zero, numbers[:,1]/N+zero, color=colors[i%len(colors)])
                #for i in range(len(numbers[:,0])):
                    #print numbers[i,0:1]
                    #plt.annotate(str(numbers[i,0]), xy=(numbers[i,0], numbers[i,1]), xytext=(-20, 20),
                                #textcoords='offset points', ha='right', va='bottom',
                                #arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
                
        # list with freq, Abs (normal spectrum)
        elif len(numbers[0]) == 2:
            if normalize:
                numbers[:,1] = numbers[:,1]/max(numbers[:,1])
            plt.plot(numbers[:,0], numbers[:,1]+zero, label=title, color=colors[i%len(colors)], linewidth=2.0)
        
        zero -= offset
        
    # extra plots
    # plot vertical lines:
    #for x_val in (687.2, 1055.5, 1509.4, 3199.7):
        #plt.axvline(x_val, ymin=0, ymax=1)
        
    plt.legend(loc=legendloc)
    
    if show_table:
        plt.subplot2grid((1, 3), (0,2))
        titles, numbers = zip(*[d for d in data if len(d[1][0]) == 5])
        table = r"\begin{{tabular}}{{ {} }} ".format("|".join(['rr'] * len(titles)))
        table += r" {} \\\hline ".format(" & ".join([r'\multicolumn{{2}}{{c}}{{\textbf{{ {} }} }}'.format(title.replace('_', '\_')) for title in titles]))
        table += r" {} \\\hline ".format(" & ".join([r'freq/cm$^{-1}$ & $I$/a.u.'] * len(titles)))
        
        for i in range(max([len(d) for d in numbers])):
            line = []
            for d in numbers:
                if len(d) <= i:
                    freq = ''
                    intens = ''
                else:
                    freq = d[i][0]
                    intens = d[i][1]
                line.append("{:>6.3f} & {:>6.3f}".format(freq, intens))
            line = r" & ".join(line)
            line += r" \\\hline "
            table += line
        
        table += r"\end{tabular}"
        ax = plt.gca()
        ax.text(0.15,0,table,size=12)
        ax.axis("off")
    
    #plt.twiny()
    #eV_range = sp.arange(min(x)*eV_per_cm, max(x)*eV_per_cm, 0.05)
    #plt.xticks(eV_range/(max(x)*eV_per_cm), eV_range)
    #plt.xlabel('Frequency (eV)')#, fontsize=afont)
    if saveas:
        plt.savefig(saveas, dpi=150, facecolor='w', edgecolor='w',
                    orientation='portrait', papertype=None, format=None,
                    transparent=False, bbox_inches=None, pad_inches=0.1,
                    frameon=None)
    else:
        plt.show()
    
def usage():
    print
    print 'Usage: plot_vibrations.py [-n] -q|-m|-e|--exp filename'
    print
    print 'Specify input formats'
    print '  -q, --qchem       file is Q-Chem output'
    print '  -m, --molden      file is in MolDen format'
    print '  -e, --espresso    file is Quantum ESPRESSO output'
    print '  -a, --aims        file is FHI-aims output'
    print '  -g, --generic     file with two colums of frequnecies and Intensities'
    print '  -f, --file        read file with list of titles and input file names'
    print '      --exp         file with experimental spectrum in two columns'
    print
    print 'Options'
    print '  -n, --normalize   normalize spectrum'
    print '  -l, --lineshape   Lorentzian (default) or Gaussian [Lorentzian]'
    print '  -w, --linewidth   linewidth to apply to shape [10.0]'
    print '  -s, --spectrum    IR or Raman spectrum [IR]'
    print '      --all_modes   plot all modes as vertical lines and label with frequency'
    print '      --show_table  generate table with all modes'
    print '  -o, --offset      shift each spectrum by offset on the y-axis [0.0]'
    print '      --xlim        set limits of x-axis ["0, 4000"]'
    print '      --ylim        set limits of y-axis [automatic]'
    print '  -v, --verbose     print found frequencies to stdout'
    print '      --legendloc   specify location of legend ["upper right"]'
    print '      --saveas      specify filename to save figure as image'
    print '  -h, --help        show this help and exit'
    print
    
if __name__ == '__main__':
    argv = sys.argv[1:]
    data = []
    
    # default options
    norm = False
    ls = 'lorentzian'
    lw = 10.0
    spec = 'IR'
    offset = 0.0
    pf = False
    xlim = [0, 4000]
    ylim = []
    legendloc = "upper right"
    plot_all_modes = False
    show_table = False
    saveas = ''
    figsize = (12,8)
    
    options = 'f:q:a:m:e:g:nl:w:s:o:vh'
    long_options = ['file=',
                    'qchem=',
                    'aims=',
                    'molden=',
                    'espresso=',
                    'generic=',
                    'exp=',
                    'normalize',
                    'lineshape=',
                    'linewidth=',
                    'spectrum=',
                    'all_modes',
                    'show_table',
                    'offset=',
                    'xlim=',
                    'ylim=',
                    'figsize=',
                    'verbose',
                    'legendloc=',
                    'saveas=',
                    'help',
                    ]
    
    try:
        opts, args = getopt.getopt(argv, options, long_options)
    except getopt.GetoptError, e:
        print
        print e
        usage()
        sys.exit(2)
    d = None
    
    # easier access with numpy arrays
    opts = sp.asarray(opts)
    
    if '-h' in opts or '--help' in opts:
        usage()
        sys.exit()
    if args:
        print 'Undefined arguments(s):'
        print ' ', ', '.join([a for a in args])
        usage()
        sys.exit(2)
    elif len(opts) == 0:
        print 'You must specify at least one input file.'
        usage()
        sys.exit(2)
    
    if '-v' in opts or '--verbose' in opts:
        #print 'ut'
        pf = True
        
    for opt, arg in opts:
        if opt in ('-q', '--qchem'):
            data.append((arg, read_file_qchem(arg, print_freqs=pf)))
        elif opt in ('-m', '--molden'):
            data.append((arg, read_file_molden(arg, print_freqs=pf)))
        elif opt in ('-e', '--espresso'):
            data.append((arg, read_file_espresso(arg, print_freqs=pf)))
        elif opt in ('-a', '--aims'):
            data.append((arg, read_file_aims(arg, print_freqs=pf)))
        elif opt in ('-g', '--generic'):
            data.append((arg, read_file_2col(arg, print_freqs=pf)))
        elif opt in ('--exp', ):
            data.append((arg, sp.loadtxt(arg)))
    
        elif opt in ('-f', '--file'):
            fl = read_file_list(arg)
            for title, typ, filename in fl:
                if typ in ('-q', '--qchem'):
                    data.append((title, read_file_qchem(filename, print_freqs=pf)))
                elif typ in ('-m', '--molden'):
                    data.append((title, read_file_molden(filename, print_freqs=pf)))
                elif typ in ('-e', '--espresso'):
                    data.append((title, read_file_espresso(filename, print_freqs=pf)))
                elif typ in ('-a', '--aims'):
                    data.append((title, read_file_aims(filename, print_freqs=pf)))
                elif typ in ('-g', '--generic'):
                    data.append((title, read_file_2col(filename, print_freqs=pf)))
                elif typ in ('--exp', ):
                    data.append((title, sp.loadtxt(filename)))
    
        elif opt in ('-n', '--normalize'):
            norm = True
        elif opt in ('-l', '--lineshape'):
            ls = arg
        elif opt in ('-w', '--linewidth'):
            try:
                lw = float(arg)
            except ValueError, e:
                print
                print 'ERROR:', arg, 'is not a valid argument for --lineshape.'
                print 'Please provide a float or integer number.'
                sys.exit(1)
        elif opt in ('-s', '--spectrum'):
            spec = arg
        elif opt in ('--all_modes'):
            plot_all_modes = True
        elif opt in ('--show_table'):
            show_table = True
        elif opt in ('-o', '--offset'):
            offset = float(arg)
        elif opt in ('--xlim',):
            xlim = map(float, arg.split(','))
        elif opt in ('--ylim',):
            ylim = map(float, arg.split(','))
        elif opt in ('--figsize',):
            figsize = map(float, arg.split(','))
        elif opt in ('--legendloc',):
            legendloc = arg
        elif opt in ('--saveas',):
            saveas = arg
        
    if not data:
        print 'No input file read. Exiting.'
        print
        usage()
        sys.exit(1)
    
    params = {#'lines.linewidth': linewidth,
            
            'font.family': 'serif',       # or 'sans-serif'
            'font.serif': 'computer modern roman',
            'font.size': 18,
            
            'text.usetex': True,
            
            'axes.titlesize': 'large',      # fontsize of the axes title
            'axes.labelsize': 'medium',      # fontsize of the x any y labels
            
            'legend.fontsize': 'medium',
            #'legend.linewidth': linewidth,
            #'legend.numpoints' : 1,
            
            'figure.figsize': figsize,     # figure size (w,h) in inches
            #'figure.dpi': 90,
            #'figure.subplot.wspace': 0.3, # the amount of width reserved for blank space between subplots
            #'figure.subplot.hspace': 0.3, # the amount of height reserved for white space between subplots
            
            'xtick.labelsize': 'small', # fontsize of the tick labels
            'ytick.labelsize': 'small', # fontsize of the tick labels
            #'font.style': normal
            #'font.serif': Bitstream Vera Serif, New Century Schoolbook, Century Schoolbook L, Utopia, ITC Bookman, Bookman, Nimbus Roman No9 L, Times New Roman, Times, Palatino, Charter, serif
            #'font.sans-serif': Bitstream Vera Sans, Lucida Grande, Verdana, Geneva, Lucid, Arial, Helvetica, Avant Garde, sans-serif
                        }
    plt.rcParams.update(params)

    
    plot_figure(data,
                spectr=spec,
                plot_all_modes=plot_all_modes,
                show_table=show_table,
                normalize=norm,
                shape=ls,
                linewidth=lw,
                offset=offset,
                xlim=xlim,
                ylim=ylim,
                legendloc=legendloc,
                saveas=saveas)
