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
import argparse

afont = 20
tfont = 22

eV_per_cm = 0.000123984187

## read input files ##

'''
functions read file and return a list tuples containing
(freqs, IR_intens, IR_active, Raman_active, force_const)
'''


def read_file_2col(filename):
        # reads 2-column file with frequencies in the 1st and intensities in the 2nd
    data = sp.loadtxt(filename)
    
    all_modes = sp.ones((len(data), 6))
    all_modes[:,0] = data[:,0] # freq
    #all_modes[:,1] = sp.ones((len(data), 1)) # IR_active
    all_modes[:,2] = data[:,1] # IR_intens
    #all_modes[:,3] = sp.ones((len(data), 1)) # Raman_active
    #all_modes[:,4] = sp.ones((len(data), 1)) # Raman_intens
    all_modes[:,5] = sp.zeros(len(data)) # force_const
    
    return all_modes

def read_file_espresso(filename):
        # read outdput from Quantum ESPRESSO
    asr = False
    with open(filename, 'r') as f:
        rl = f.readline
        
        all_modes = []
        
        line = rl()
        while not (line.startswith('#') and 'mode' in line) and line:
            line = rl()
            if "Acoustic Sum Rule" in line:
                asr = True
        
        data = []
        line = rl()
        while line.strip():
            i, freq, freq_THz, IR_intens = map(float, line.strip().split())
            data.append((freq, IR_intens))
            line = rl()
    
    activities = []
    # try to read phg.out file to get I/R mode activities
    ### TODO currently only useful if ASR has not been enforced.
    if not asr:
        dirname = os.path.dirname(filename)
        fn_phg = os.path.join(dirname, "phG.out")
        if not os.path.exists(fn_phg):
            for fn in os.listdir(dirname):
                if os.path.isfile(os.path.join(dirname, fn)):
                    filepath = os.path.join(dirname, fn)
                    with open(filepath, 'r') as fin:
                        fin.readline() # dump
                        if fin.readline().strip().startswith("Program PHONON"):
                            fn_phg = filepath
                            break
        try:
            with open(fn_phg, 'r') as f:
                rl = f.readline
                line = rl()
                while line:
                    if "Mode symmetry" in line:
                        break
                    line = rl()
                rl() # dump
                # read IR/Raman activities for all relevant modes (acoustic modes not included)
                activities = [(0, 0)] * 6
                for i in range(len(data) - 6):
                    line = rl()
                    IR = Ra = False
                    if "I" in line[-5:]:
                        IR = True
                    if "R" in line[-5:]:
                        Ra = True
                    activities.append((IR, Ra))
            activities = sp.asarray(activities)
        except IOError as e:
            print
            print "No espresso ph.x output file found in {} to read IR/Raman activities from.".format(os.path.dirname(filename))
            # append two columns of 1's for compatibility (IR_active and Raman_active)
    
    if activities == []:
        activities = sp.ones((len(data), 2))
    else:
        activities = sp.asarray(activities)
    
    data = sp.asarray(data)
    
    all_modes = sp.zeros((len(data), 6))
    all_modes[:,0] = data[:,0] # freq
    all_modes[:,1] = activities[:,0] # IR_active
    all_modes[:,2] = data[:,1] # IR_intens
    all_modes[:,3] = activities[:,1] # Raman_active
    all_modes[:,4] = sp.ones((len(data), 1)).reshape(all_modes[:,4].shape) # Raman_intens
    all_modes[:,5] = sp.zeros((len(data), 1)).reshape(all_modes[:,4].shape) # force_const
    
    return all_modes

def read_file_aims(filename):
    # read outdput from AIMS
    with open(filename, 'r') as f:
        rl = f.readline
        
        all_modes = []
        
        line = rl()
        while not ('frequencies found:') in line and line:
            line = rl()
        rl() # dump
        
        line = rl()
        while line.strip():
            i, freq, zero_point_E, IR_intens = map(float, line.strip().split())
            # freqs, IR_active, IR_intens, Raman_active, Raman_intens, force_const
            all_modes.append((freq, True, IR_intens, True, 1.0, 0.0))
            line = rl()
    
    return sp.asarray(all_modes)
    
def read_file_qchem(filename):
    with open(filename, 'r') as f:
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
            Raman_intens = [1] * len(Raman_active)
            all_modes.extend(zip(freqs, IR_active, IR_intens, Raman_active, Raman_intens, force_const))
            
            line = rl()
    
    return sp.asarray(all_modes)

def read_file_molden(filename):
    with open(filename, 'r') as f:
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
        Raman_intens = [1.0]*len(freqs)
        force_const = [0.0]*len(freqs)
    
    all_modes = zip(freqs, IR_active, IR_intens, Raman_active, Raman_intens, force_const)
    
    return sp.asarray(all_modes)

def print_frequencies(filename, all_modes):
    print
    print filename
    print '[freq/cm^-1, I, I/R/N, force const./mdyn/A]'
    for freq, IR_active, IR_intens, Raman_active, Raman_intens, force_const in all_modes:
            if IR_active or Raman_active:
                if not Raman_active:
                    active = 'I'
                elif not IR_active:
                    active = 'R'
                else:
                    active = 'I/R'
            else:
                active = 'N'
            print '{0:7.2f}  {1:10.6f}  {2:<4}  {3:7.4f}'.format(freq, 
                    IR_intens, active, force_const)

def convolve_spectrum(modes, gamma=10, x=None, normalize=False, convolve='lorentzian'):
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
    
    if convolve.lower() not in ('lorentzian', 'gaussian'):
        convolve = 'lorentzian'
        print 'Convolve argument not understood. Changed to Lorentzian.'
    
    if convolve.lower() == 'lorentzian':
        for freq, intens in modes:
            if intens > 0.0:
                x2 = (x-freq)*(x-freq)
                g2 = gamma*gamma
                #y += intens*gamma/(sp.pi*(x2+g2))
                new_y = intens*g2/(x2+g2)
                y += new_y
    elif convolve.lower() == 'gaussian':
        for freq, intens in modes:
            if intens > 0.0:
                x2 = (x-freq)*(x-freq)
                g2 = gamma*gamma
                tmpy = sp.exp(-x2/(2*g2))
                if max(tmpy) > 0.0:
                    y += intens*tmpy/max(tmpy)
    
    if normalize and max(y) > 0.0:
        y = y/max(y)
    
    return sp.vstack((x,y)).transpose()

    
    
#def get_text_positions(x_data, y_data, txt_width, txt_height):
    #a = zip(y_data, x_data)
    #text_positions = y_data.copy()
    #for index, (y, x) in enumerate(a):
        #local_text_positions = [i for i in a if i[0] > (y - txt_height) 
                            #and (abs(i[1] - x) < txt_width * 2) and i != (y,x)]
        #if local_text_positions:
            #sorted_ltp = sorted(local_text_positions)
            #if abs(sorted_ltp[0][0] - y) < txt_height: #True == collision
                #differ = sp.diff(sorted_ltp, axis=0)
                #a[index] = (sorted_ltp[-1][0] + txt_height, a[index][1])
                #text_positions[index] = sorted_ltp[-1][0] + txt_height
                #for k, (j, m) in enumerate(differ):
                    ##j is the vertical distance between words
                    #if j > txt_height * 2: #if True then room to fit a word in
                        #a[index] = (sorted_ltp[k][0] + txt_height, a[index][1])
                        #text_positions[index] = sorted_ltp[k][0] + txt_height
                        #break
    #return text_positions

#def text_plotter(x_data, y_data, text_positions, offset, axis,txt_width,txt_height, color):
    #for x,y,t in zip(x_data, y_data, text_positions):
        
        #plt.annotate(str(x), xy=(x, y+offset), xycoords='data', 
                     #xytext=(x-txt_width, t+offset), textcoords='data',
                     ##ha='right', va='bottom',
                     #arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', alpha=0.3, color='k') if y != t else None,
                     #color=color)
        
        #axis.text(x - txt_width, 1.01*t, '%d'%int(x),rotation=90, color=color)
        #if y != t:
            #axis.arrow(x, t,0,y-t, color='red',alpha=0.3, width=1, 
                       #head_width=0.2*txt_width, head_length=txt_height*0.3, 
                       #zorder=0,length_includes_head=True)

def plot_figure(data,
                spectrum='I',
                plot_all_modes=False,
                show_table=False,
                normalize=False,
                convolve='lorentzian',
                fwhm=10.0,
                offset=0.0,
                xlim=[0, 4000],
                ylim=[],
                legendloc="upper right",
                colors="rygcb",
                saveas=''):

    if show_table:
        plt.subplot2grid((1, 3), (0,0), colspan=2)
    plt.xlabel('Frequency (cm$^{-1}$)')#, fontsize=afont)
    plt.ylabel(r'Intensity (a.u.)')#, fontsize=afont)
    plt.xlim(*xlim)
    if ylim:
        plt.ylim(*ylim)
    x = sp.linspace(xlim[0], xlim[1], 100000)
    
    if spectrum.lower() not in ('i', 'r'):
        spectrum = 'i'
        print 'Spectrum type not understood. Changed to I (=Infrared).'
    
    if spectrum.lower() == 'i':
        activity = 1
    elif spectrum.lower() == 'r':
        activity = 3
        print 'WARNING: Raman spectrum will have IR intensities.'
    
    zero = offset*(len(data)-1)
    for i, (title, numbers) in enumerate(data):
        # make sure title is latex proof
        title = title.replace('_', '\_')
        
        # list with freq, IR_active, IR_intens, Raman_active, Raman_intens, force_const
        if len(numbers[0]) == 6:
            # get Lorentzian line shape for each frequency
            freq_intens = [(d[0], d[activity+1]) for d in numbers if d[activity]]
            xy = convolve_spectrum(freq_intens, fwhm, x, normalize=normalize, convolve=convolve)
            plt.plot(xy[:,0], xy[:,1]+zero, label=title, color=colors[i%len(colors)], linewidth=2.0)
            if plot_all_modes:
                #txt_height = 0.1*(plt.ylim()[1] - plt.ylim()[0])
                #txt_width = 0.05*(plt.xlim()[1] - plt.xlim()[0])
                #Get the corrected text positions, then write the text.
                #text_positions = get_text_positions(numbers[:,0], numbers[:,1], txt_width, txt_height)
                #text_plotter(numbers[:,0], numbers[:,1], text_positions, zero, plt.gca(), txt_width, txt_height, colors[i%len(colors)])

                #plt.ylim(0, max(text_positions)+2*txt_height)
                if plot_all_modes == "I":
                    freqs = [d[0] for d in numbers if d[1]]
                elif plot_all_modes == "R":
                    freqs = [d[0] for d in numbers if d[3]]
                else:
                    freqs = numbers[:,0]
                plt.vlines(freqs, 0+zero, max(xy[:,1])+zero, color=colors[i%len(colors)], linestyles='dotted')
        
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
        # get all titles and all numbers
        titles, numbers = zip(*[d for d in data if len(d[1][0]) == 6])
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
                    freq = "{:>6.3f}".format(d[i][0])
                    intens = "{:>6.3f}".format(d[i][activity+1])
                line.append("{} & {}".format(freq, intens))
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


############################################################################33
#def usage():
    #print
    #print 'Usage: plot_vibrations.py [-n] -q|-m|-e|--exp filename'
    #print
    #print 'Specify input formats'
    #print '  -q, --qchem       file is Q-Chem output'
    #print '  -m, --molden      file is in MolDen format'
    #print '  -e, --espresso    file is Quantum ESPRESSO output'
    #print '  -a, --aims        file is FHI-aims output'
    #print '  -g, --generic     file with two colums of frequnecies and Intensities'
    #print '  -f, --file        read file with list of titles and input file names'
    #print '      --exp         file with experimental spectrum in two columns'
    #print
    #print 'Options'
    #print '  -n, --normalize   normalize spectrum'
    #print '  -c, --convolve    Lorentzian (default) or Gaussian [Lorentzian]'
    #print '  -w, --fwhm        linewidth to apply to shape [10.0]'
    #print '  -s, --spectrum    IR or Raman spectrum [IR]'
    #print '      --all_modes   plot all modes as vertical lines and label with frequency'
    #print '      --show_table  generate table with all modes'
    #print '  -o, --offset      shift each spectrum by offset on the y-axis [0.0]'
    #print '      --xlim        set limits of x-axis ["0, 4000"]'
    #print '      --ylim        set limits of y-axis [automatic]'
    #print '  -v, --verbose     print found frequencies to stdout'
    #print '      --legendloc   specify location of legend ["upper right"]'
    #print '      --colors      specify order of the colors to use ["rygcb"]'
    #print '      --saveas      specify filename to save figure as image'
    #print '  -h, --help        show this help and exit'
    #print

class read_file(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        if not 'data' in namespace:
            setattr(namespace, 'data', [])
        data = namespace.data
        data.append((value, file_functions[option_string](value)))
        setattr(namespace, 'data', data)

class read_file_list(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        if not 'data' in namespace:
            setattr(namespace, 'data', [])
        data = namespace.data
        
        with open(value, 'r') as fin:
            for line in fin:
                if line.strip() and not line.strip().startswith('#'):
                    lst = re.split('(.+)( {} )(.+)'.format(" | ".join(file_functions.keys())), line)
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
                    data.append((title, file_functions[typ](filename)))

class get_lim(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if option_string == "--ylim" and values == 'automatic':
            setattr(namespace, self.dest, [])
        else:
            try:
                lim = map(float, values.split(','))
                if not len(lim) == 2:
                    raise ValueError
            except ValueError, e:
                print
                print 'ERROR: {} is not a valid argument for {}.'.format(values, option_string)
                print 'Please use following format: "xmin, xmax", e.g. "0, 4000".'
                sys.exit(1)
            setattr(namespace, self.dest, lim)

class check_colors(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # if values is a valid sequence of single letters
        m = re.search("[bgrcmykw]+", values)
        if m and m.group(0) == values:
            setattr(namespace, self.dest, values)
        else:
            # split comma separated list. Keeps tuples of RGB values intact. Doesn't check if value is a valid color!
            color_list = map(str.strip, re.split(",(?![ .0-9]+,[ .0-9]+\)|[ .0-9]+\)|[ .0-9]+,[ .0-9]+\]|[ .0-9]+\])", values))
            # replace RGB strings with actual tuples
            for i, c in enumerate(color_list):
                if re.match('\(|\[', c):
                    color_list[i] = tuple(float(f) for f in re.findall("[.0-9]+", c))
            setattr(namespace, self.dest, color_list)

# dict that maps file format option to corresponding read_file function
# each function takes as argument the filename and returns the frequency data
file_functions = {'-q': read_file_qchem,
                  '--qchem': read_file_qchem,
                  '-a': read_file_aims,
                  '--aims': read_file_aims,
                  '-m': read_file_molden,
                  '--molden': read_file_molden,
                  '-e': read_file_espresso,
                  '--espresso': read_file_espresso,
                  '-g': read_file_2col,
                  '--generic': read_file_2col,
                  '-x': sp.loadtxt,
                  '--exp': sp.loadtxt}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plot IR and Raman spectra from different file formats")
    
    legendloc_choices = ('best', 0,
                         'upper right', 1,
                         'upper left', 2,
                         'lower left', 3,
                         'lower right', 4,
                         'right', 5,
                         'center left', 6,
                         'center right', 7,
                         'lower center', 8,
                         'upper center', 9,
                         'center', 0)
    convolve_choices = ("Lorentzian", "Gaussian")
    
    # Specify file formats and paths to read vibrational frequencies from.
    files = parser.add_argument_group("Input Files")
    files.add_argument('-q', '--qchem', action=read_file, metavar='F', help='file is Q-Chem output')
    files.add_argument('-m', '--molden', action=read_file, metavar='F', help='file is in MolDen format')
    files.add_argument('-e', '--espresso', action=read_file, metavar='F', help='file is Quantum ESPRESSO output (diag.out)')
    files.add_argument('-a', '--aims', action=read_file, metavar='F', help='file is FHI-aims output')
    files.add_argument('-g', '--generic', action=read_file, metavar='F', help='file has two columns, frequencies and intensities')
    files.add_argument('-x', '--exp', action=read_file, metavar='F', help='file has two columns with full spectrum')
    
    files.add_argument('-f', '--file', action=read_file_list, metavar='F', help='read file with list of titles, format and file names')
    
    # Parameters to change appearance of the graphs.
    spectrum = parser.add_argument_group("Spectrum")
    spectrum.add_argument('-n', '--normalize', action='store_true', help='normalize spectrum')
    spectrum.add_argument('-s', '--spectrum', default='I', choices=("I", "R"), metavar="S", help='IR (I) or Raman (R) spectrum [%(default)s]')
    spectrum.add_argument('-c', '--convolve', default='Lorentzian', choices=("Lorentzian", "Gaussian"), metavar="C", help='Lorentzian or Gaussian [%(default)s]')
    spectrum.add_argument('-w', '--fwhm', type=float, default=10.0, metavar="W", help='full-width-at-half-maximum [%(default)s]')
    spectrum.add_argument('-o', '--offset', type=float, default=0.0, metavar='O', help='shift each spectrum by offset on the y-axis [%(default)s]')
    spectrum.add_argument('--all-modes', nargs='?', default=None, const='IR', metavar="I/R/IR", help='plot all modes as vertical lines [%(default)s]')
    
    #Parameters to change appearance of the plot.
    plot = parser.add_argument_group("Plot")
    plot.add_argument('--xlim', default=[0, 4000], action=get_lim, metavar='MIN,MAX', help='set limits of x-axis %(default)s')
    plot.add_argument('--ylim', default=[], action=get_lim, metavar='MIN,MAX', help='set limits of y-axis [%(default)s]')
    plot.add_argument('--legendloc', default='upper right', choices=legendloc_choices, metavar="LOC", help='specify location of legend ["%(default)s"]')
    plot.add_argument('--colors', default='rygcbm', action=check_colors, help='string or comma-separated list of colors [%(default)s]')
    plot.add_argument('--figsize', default=[12,8], action=get_lim, metavar='W,H', help='specify size of plot in inches %(default)s')
    plot.add_argument('--show-table', action='store_true', help='generate table with all modes')
    
    other = parser.add_argument_group("Other")
    other.add_argument('--saveas', metavar='F', help='specify filename to save figure as image')
    other.add_argument('-p', '--print', action='store_true', dest='print_freqs', help='print found frequencies to stdout')
    
    args = parser.parse_args(sys.argv[1:])
    
    if args.print_freqs:
        for fn, modes in args.data:
            if len(modes[0]) > 2:
                print_frequencies(fn, modes)
    #try:
        #opts, args = getopt.getopt(argv, options, long_options)
    #except getopt.GetoptError, e:
        #print
        #print e
        #usage()
        #sys.exit(2)
    #d = None
    
    ## easier access with numpy arrays
    #opts = sp.asarray(opts)
    
    #if '-h' in opts or '--help' in opts:
        #usage()
        #sys.exit()
    #if args:
        #print 'Undefined arguments(s):'
        #print ' ', ', '.join([a for a in args])
        #usage()
        #sys.exit(2)
    #elif len(opts) == 0:
        #print 'You must specify at least one input file.'
        #usage()
        #sys.exit(2)
    
    #if '-v' in opts or '--verbose' in opts:
        ##print 'ut'
        #pf = True
    
    #for opt, arg in opts:
        #if opt in ('-q', '--qchem'):
            #data.append((arg, read_file_qchem(arg, print_freqs=pf)))
        #elif opt in ('-m', '--molden'):
            #data.append((arg, read_file_molden(arg, print_freqs=pf)))
        #elif opt in ('-e', '--espresso'):
            #data.append((arg, read_file_espresso(arg, print_freqs=pf)))
        #elif opt in ('-a', '--aims'):
            #data.append((arg, read_file_aims(arg, print_freqs=pf)))
        #elif opt in ('-g', '--generic'):
            #data.append((arg, read_file_2col(arg, print_freqs=pf)))
        #elif opt in ('--exp', ):
            #data.append((arg, sp.loadtxt(arg)))
    
        #elif opt in ('-f', '--file'):
            #fl = read_file_list(arg)
            #for title, typ, filename in fl:
                #if typ in ('-q', '--qchem'):
                    #data.append((title, read_file_qchem(filename, print_freqs=pf)))
                #elif typ in ('-m', '--molden'):
                    #data.append((title, read_file_molden(filename, print_freqs=pf)))
                #elif typ in ('-e', '--espresso'):
                    #data.append((title, read_file_espresso(filename, print_freqs=pf)))
                #elif typ in ('-a', '--aims'):
                    #data.append((title, read_file_aims(filename, print_freqs=pf)))
                #elif typ in ('-g', '--generic'):
                    #data.append((title, read_file_2col(filename, print_freqs=pf)))
                #elif typ in ('--exp', ):
                    #data.append((title, sp.loadtxt(filename)))
    
        #elif opt in ('-l', '--lineshape'):
            #ls = arg
        #elif opt in ('-w', '--linewidth'):
            #try:
                #lw = float(arg)
            #except ValueError, e:
                #print
                #print 'ERROR:', arg, 'is not a valid argument for --lineshape.'
                #print 'Please provide a float or integer number.'
                #sys.exit(1)
        #elif opt in ('-s', '--spectrum'):
            #spec = arg
        #elif opt in ('--all_modes'):
            #plot_all_modes = True
        #elif opt in ('--show_table'):
            #show_table = True
        #elif opt in ('-o', '--offset'):
            #offset = float(arg)
        #elif opt in ('--xlim',):
            #xlim = map(float, arg.split(','))
        #elif opt in ('--ylim',):
            #ylim = map(float, arg.split(','))
        #elif opt in ('--figsize',):
            #figsize = map(float, arg.split(','))
        #elif opt in ('--legendloc',):
            #legendloc = arg
        #elif opt in ('--colors',):
            #colors = arg
        #elif opt in ('--saveas',):
            #saveas = arg
    if not args.data:
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
            
            'figure.figsize': args.figsize,     # figure size (w,h) in inches
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

    
    plot_figure(args.data,
                spectrum=args.spectrum,
                plot_all_modes=args.all_modes,
                show_table=args.show_table,
                normalize=args.normalize,
                convolve=args.convolve,
                fwhm=args.fwhm,
                offset=args.offset,
                xlim=args.xlim,
                ylim=args.ylim,
                legendloc=args.legendloc,
                colors=args.colors,
                saveas=args.saveas)
