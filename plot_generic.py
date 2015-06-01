#!/usr/bin/python
'''
takes a generic two column file and plots the data
'''

import sys
import getopt
import scipy as sp
from scipy.optimize import curve_fit
from matplotlib import pyplot as plt
import re

from myconstants import *

def plot_figure(data,
                title='',
                subtitles=[],
                xlabel='',
                ylabel='',
                xunit=1.0,
                yunit=1.0,
                normalize=False,
                offset=0.0,
                fit='',
                subplot='',
                colors=['b', 'r', 'y', 'g', 'c'],
                xlim=[],
                ylim=[],
                legendloc=1,
                linestyle='-',
                fitstyle='-',
                constant=None):
    
    plt.figure()
    if title != '':
        plt.suptitle(title, fontsize='x-large')
    
    if xlim != []:
        xmin = xlim[0]
        xmax = xlim[1]
    if ylim != []:
        ymin = ylim[0]
        ymax = ylim[1]
    
    if subplot:
        try:
            rows, cols = map(int, subplot.split('x'))
            if rows*cols < len(data):
                print 'Not enough subplots:'
                print 'You specified {0} sets of data, but only {1} = {2} subplots.'.format(len(data), subplot, rows*cols)
                print 'Exiting.'
                sys.exit(1)
        except ValueError, e:
            print 'Wrong subplot argument.'
            print 'Example: 2x3 (= 2 rows, 3 columns).'
            print
            print '(%s)' % e
            print 'Exiting.'
            sys.exit(1)
    else:
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
    
    # start plotting at the top (so that the legend has the same order
    zero = offset*len(data)
    
    # assign correct fit function to func
    if fit:
        guess = None
        parameters = 'abcdefghijklmnopqrstuvwxyz'
        if fit == 1 or fit == '1':
            #print 'Linear fit'
            func = lambda x, a, b: a*x + b
        elif fit == 2 or fit == '2':
            #print 'Quadratic fit'
            func = lambda x, a, b, c: a*x*x + b*x + c
            #guess = (1.0 , 0.0, min(xy[:,1]))
        elif fit == 3 or fit == '3':
            #print 'Cubic fit'
            func = lambda x, a, b, c, d: a*x*x*x + b*x*x + c*x + d
        else:
            fitsplit = map(str.strip, fit.split(','))
            func_str = fitsplit[0]
            parameters = fitsplit[1:]
            for p in parameters:
                if not p in func_str:
                    print 'Parameter %s given is not in function %s' % (p, func_str)
                    print 'Exiting.'
                    sys.exit(1)
                
            lambda_str = 'lambda x, {0}: {1}'.format(', '.join(parameters), func_str)
            print 'Fit function:'
            print lambda_str
            check = raw_input('Is that correct? [Y/n] ')
            if check in ('', 'Y', 'y', 'J', 'j'):
                func = eval(lambda_str)
            else:
                print 'Exiting.'
                sys.exit(0)
    
    for i, (label, xy) in enumerate(data):
        # multiply with unit
        xy[:,0] *= xunit
        xy[:,1] *= yunit
        
        if subplot:
            plt.subplot(rows, cols, i+1)
            try:
                plt.title(subtitles[i])
            except IndexError:
                pass
            if xlabel != '':
                plt.xlabel(xlabel)#, fontsize=afont)
            if ylabel != '':
                plt.ylabel(ylabel)#, fontsize=afont)
        
        print '-'*76
        print label
        if normalize:
            xy[:,1] = xy[:,1]/max(xy[:,1])
        
        plt.plot(xy[:,0], xy[:,1]+zero, linestyle,
                 label=label, color=colors[i%len(colors)])
        
        #plot constant
        #if constant != None and subplot:
        
        
        if fit:
            # Sometimes the curve_fit will not be able to calculate the variance
            # Instead it returns inf as the var_matrix. In this case, scaling
            # the y-values can help.
            scale = 1.0
            while True:
                try:
                    coeff, var_matrix = curve_fit(func, xy[:,0], scale*xy[:,1])
                    coeff = coeff/scale
                    variance = sp.diagonal(var_matrix)
                    SE = sp.sqrt(variance)
                    SE = SE/scale
                    results = {}
                    for k in range(len(SE)):
                        results[parameters[k]] = [coeff[k], SE[k]]
                    print
                    print '{0:>5}  {1:>12}  {2:>12}'.format('Coeff', 'Value', 'Error')
                    for v,c in results.iteritems():
                        print '{0:>5}  {1:>12.5f}  {2:>12.5f}'.format(v, c[0], c[1])
                    break
                    
                except ValueError, e:
                    scale *= 10
                    if scale == 1000000:
                        print 'No errors to fit parameters available. Check input data and code.'
                        break
            
            fit_x = sp.linspace(min(xy[:,0]), max(xy[:,0]), 10000)
            fit_y = func(fit_x, *coeff)
            plt.plot(fit_x, fit_y+zero, fitstyle,
                     label='fit ({0})'.format({'1': 'linear',
                                               '2': 'quadratic',
                                               '3': 'cubic',
                                               }.get(str(fit), fit)),
                     color=colors[i%len(colors)])
            
            sq_sum = 0
            max_dy = 0
            for l in range(len(xy[:,1])):
                #print func(xy[l:,0], *coeff)
                dy = xy[l,1] - func(xy[l,0], *coeff)
                if abs(dy) > max_dy:
                    max_dy = abs(dy)
                sq_sum += dy*dy
            error = sq_sum / len(xy[:,1])
            print
            print 'fit error ( sqrt( sum_i^k( (y_i - f(x))^2 / k )) ):'
            print '   ', error
            print
            print 'max deviation:'
            print '   ', max_dy
            
        zero -= offset
        if subplot:
            if constant != None:
                try:
                    plt.plot(xy[:,0], sp.ones(len(xy[:,0]))*constant[0], label=constant[1])
                except (TypeError, IndexError):
                    plt.plot(xy[:,0], sp.ones(len(xy[:,0]))*constant)
    
            plt.legend(loc=legendloc)
            if xlim:
                plt.xlim(xmin, xmax)
            if ylim:
                plt.ylim(ymin, ymax)
            
    
    if not subplot:
        if constant != None:
            try:
                plt.plot(xy[:,0], sp.ones(len(xy[:,0]))*constant[0], label=constant[1])
            except (TypeError, IndexError):
                plt.plot(xy[:,0], sp.ones(len(xy[:,0]))*constant)
    
        
        plt.legend(loc=legendloc)
        if xlim:
            plt.xlim(xmin, xmax)
        if ylim:
            plt.ylim(ymin, ymax)


def usage():
    print
    print 'Plot data from two column file. Polynomial fits possible.'
    print
    print 'Usage: plot_generic.py [-txynhl...] filenames'
    print
    print 'Options [default]'
    print '(s=string, n=int, f=float)'
    print
    print 'Labels and titles:'
    print '  -t, --title "s"         main title of figure ['']'
    print '      --subtitles "[s,]"  list of titles for subplots'
    print '      --legend "[s,]"     legend labels (same order as file names) [same as filenames]'
    print '  -x, --xlabel "s"        label on x-axis ['']'
    print '  -y, --ylabel "s"        label on y-axis ['']'
    print
    print 'Data manipulation:'
    print '      --xunit f           factor to multiply the x-values with',
    print '      --yunit f           factor to multiply the y-values with',
    print '  -n, --normalize         normalize all plots'
    print '  -o, --offset f          shift each data set by offset on the y-axis [0]'
    print '  -f  --fit n             degree of polynomial fit to plot along data'
    print '  -f  --fit "f(x),p0"     or manual fit function and parameters (e.g. "a*x*x + b, a, b")'
    print '      --xlim f,f          range of x=axis (e.g. -2.0,3) [automatic]'
    print '      --ylim f,f          range of y=axis (e.g. -2.0,3) [automatic]'
    print
    print 'Layout:'
    print '  -l, --linewidth f       width of plot lines [1]'
    print '      --linestyle s       style to draw lines ["-"]'
    print '      --fitstyle s        style to draw fit lines ["-"]'
    print '      --subplot nxn       plot each set of data in subplot (e.g. 2x3=2 rows, 3 columns)'
    print '      --fontsize n        general font size [12]'
    print '      --tfont n|s         size of title font [large]'
    print '      --afont n|s         size of axes label font [medium]'
    print '      --lfont n|s         size of legend font [same as afont]'
    print '      --colors "[s,]"     list of colors for plots'
    print '      --legendloc s|n     location of legend [upper right|1]'
    print
    print '  -h, --help              show this help and exit'
    print
    
if __name__ == '__main__':
    argv = sys.argv[1:]
    
    # default options
    title = ''
    subtitles = []
    legend = []
    xlabel = ''
    ylabel = ''
    
    yunit = 1.0
    xunit = 1.0
    normalize = False
    offset = 0.0
    fit = ''
    xlim = []
    ylim = []
    linewidth = 1
    linestyle = '-'
    fitstyle = '-'
    subplot = ''
    fontsize = 12
    tfont = 'large'
    afont = 'medium'
    lfont = afont
    colors = ['b', 'r', 'y', 'g', 'c']
    legendloc = 1
        #upper right     1
        #upper left  2
        #lower left  3
        #lower right     4
        #right   5
        #center left     6
        #center right    7
        #lower center    8
        #upper center    9
        #center  10
    
    options = 't:x:y:no:f:l:eh'
    long_options = [
                    'title=',
                    'subtitles=',
                    'legend=',
                    'xlabel=',
                    'ylabel=',
                    'xunit=',
                    'yunit=',
                    'normalize',
                    'offset=',
                    'fit=',
                    'xlim=',
                    'ylim=',
                    'linewidth=',
                    'linestyle=',
                    'fitstyle=',
                    'subplot=',
                    'fontsize=',
                    'tfont=',
                    'afont=',
                    'lfont=',
                    'colors=',
                    'legendloc',
                    'help',
                    ]
    try:
        opts, args = getopt.getopt(argv, options, long_options)
    except getopt.GetoptError, e:
        print
        print e
        usage()
        sys.exit(2)
    
    if len(args) == 0:
        print 'You must specify at least one input file.'
        usage()
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-t', '--title'):
            title = arg
        elif opt in ('--subtitles',):
            subtitles = eval(arg)
        elif opt in ('--legend',):
            legend = eval(arg)
        elif opt in ('-x', '--xlabel'):
            xlabel = arg
        elif opt in ('-y', '--ylabel'):
            ylabel = arg
        elif opt in ('--xunit',):
            xunit = float(arg)
        elif opt in ('--yunit',):
            yunit = float(arg)
        elif opt in ('-n', '--normalize'):
            normalize = True
        elif opt in ('-o', '--offset'):
            offset = float(arg)
        elif opt in ('-f', '--fit'):
            fit = arg
        elif opt in ('--xlim',):
            xlim = map(float, arg.split(','))
        elif opt in ('--ylim',):
            ylim = map(float, arg.split(','))
        elif opt in ('-l', '--linewidth'):
            linewidth = float(arg)
        elif opt in ('--linestyle',):
            linestyle = arg
        elif opt in ('--fitstyle',):
            fitstyle = arg
        elif opt in ('--subplot',):
            subplot = arg
        elif opt in ('--fontsize',):
            fontsize = int(arg)
        elif opt in ('--tfont',):
            tfont = int(arg)
        elif opt in ('--afont',):
            afont = int(arg)
        elif opt in ('--lfont',):
            lfont = int(arg)
        elif opt in ('--colors',):
            colors = eval(arg)
        elif opt in ('--legendloc',):
            legendloc = arg
        
    data = []
    
    for i, fn in enumerate(args):
        xy = sp.loadtxt(fn)
        try:
            label = legend[i]
        except IndexError:
            # make filenames latex-save
            label = re.sub('_', '\_', fn)
        data.append((label, xy))
    
    params = {'lines.linewidth': linewidth,
              
              'font.family': 'serif',       # or 'sans-serif'
              'font.serif': 'computer modern roman',
              'font.size': fontsize,
              
              'text.usetex': True,
              
              'axes.titlesize': tfont,      # fontsize of the axes title
              'axes.labelsize': afont,      # fontsize of the x any y labels
              
              'legend.fontsize': lfont,
              'legend.linewidth': linewidth,
              'legend.numpoints' : 1,
              
              'figure.figsize': (8, 6),     # figure size in inches
              'figure.dpi': 90,
              'figure.subplot.wspace': 0.3, # the amount of width reserved for blank space between subplots
              'figure.subplot.hspace': 0.3, # the amount of height reserved for white space between subplots
              
              #'xtick.labelsize': medium # fontsize of the tick labels
              #'ytick.labelsize': medium # fontsize of the tick labels
              #'font.style': normal
              #'font.serif': Bitstream Vera Serif, New Century Schoolbook, Century Schoolbook L, Utopia, ITC Bookman, Bookman, Nimbus Roman No9 L, Times New Roman, Times, Palatino, Charter, serif
              #'font.sans-serif': Bitstream Vera Sans, Lucida Grande, Verdana, Geneva, Lucid, Arial, Helvetica, Avant Garde, sans-serif
                           }
    plt.rcParams.update(params)
    
    
    plot_figure(data,
                title=title,
                subtitles=subtitles,
                xlabel=xlabel,
                ylabel=ylabel,
                xunit=xunit,
                yunit=yunit,
                normalize=normalize,
                offset=offset,
                fit=fit,
                subplot=subplot,
                colors=colors,
                xlim=xlim,
                ylim=ylim,
                legendloc=legendloc,
                linestyle=linestyle,
                fitstyle=fitstyle)
    plt.show()
