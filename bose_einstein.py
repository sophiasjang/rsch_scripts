#!/usr/bin/python

from matplotlib import pyplot as plt
import scipy as sp

e = sp.linspace(0,10, 100)

for kT in sp.linspace(1,2,10):
    n = 2./(sp.exp((e/kT)) + 1)
    plt.plot(e, n)
    n = 2./(sp.exp((e/kT)) - 1)
    plt.plot(e, n)

plt.show()