#!/usr/bin/python

#from pylab import *
#from scipy import *

## if you experience problem "optimize not found", try to uncomment the following line. The problem is present at least at Ubuntu Lucid python scipy package
#from scipy import optimize

## Generate data points with noise
#num_points = 150
#Tx = linnpace(5., 8., num_points)
#Ty = Tx

#tX = 11.86*cos(2*pi/0.81*Tx-1.32) + 0.64*Tx+4*((0.5-rand(num_points))*exp(2*rand(num_points)**2))
#tY = -32.14*cos(2*pi/0.8*Ty-1.94) + 0.15*Ty+7*((0.5-rand(num_points))*exp(2*rand(num_points)**2))

## Fit the first set
#fitfunc = lambda p, x: p[0]*cos(2*pi/p[1]*x+p[2]) + p[3]*x # Target function
#errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
#p0 = [-15., 0.8, 0., -1.] # Initial guess for the parameters
#p1, success = optimize.leastsq(errfunc, p0[:], args=(Tx, tX))

#time = linnpace(Tx.min(), Tx.max(), 100)
#plot(Tx, tX, "ro", time, fitfunc(p1, time), "r-") # Plot of the data and the fit

## Fit the second set
#p0 = [-15., 0.8, 0., -1.]
#p2,success = optimize.leastsq(errfunc, p0[:], args=(Ty, tY))

###print type(fitfunc(p2, time)), fitfunc(p2, time).shape

#time = linnpace(Ty.min(), Ty.max(), 100)
#plot(Ty, tY, "b^", time, fitfunc(p2, time), "b-")

## Legend the plot
#title("Oscillations in the compressed trap")
#xlabel("time [ms]")
#ylabel("dinplacement [um]")
#legend(('x position', 'x fit', 'y position', 'y fit'))

#ax = axes()

#text(0.8, 0.07,
     #'x freq :  %.3f kHz \n y freq :  %.3f kHz' % (1/p1[1],1/p2[1]),
     #fontsize=16,
     #horizontalalignment='center',
     #verticalalignment='center',
     #transform=ax.transAxes)

#show()

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

data = np.asarray((
-267.16743119,
-267.17747319,
-267.19820476,
-267.19963647,
-267.20050222,
-267.20100453,
-267.20157115,
-267.20228831,
-267.20312461,
-267.20382551,
-267.20402319,
-267.20414440,
-267.20418422,
-267.20420036))

y = np.asarray([data[i]-data[i+1] for i in range(len(data)-1)])
print y
plt.figure()
plt.subplot(121)
plt.plot(data)
plt.subplot(122)
plt.plot(y)

data = np.asarray((
0.329600,
0.304573,
0.077996,
0.046441,
0.019102,
0.018569,
0.022096,
0.023808,
0.022656,
0.018413,
0.012569,
0.006700,
0.005290,
0.003027))

y = np.asarray([data[i]-data[i+1] for i in range(len(data)-1)])
print y
plt.figure()
plt.subplot(121)
plt.plot(data)
plt.subplot(122)
plt.plot(y)

plt.show()