#!/usr/bin/python

### USE MAYAVI !!! ###

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
import numpy as np

#style = 'wireframe'
style = 'surface'

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

X = np.arange(-2, 2, 0.25)
Y = np.arange(-2, 2, 0.25)
X, Y = np.meshgrid(X, Y)
#R = np.sqrt(X**2 + Y**2)
#Z = np.sin(R)
Z = X**2 + Y**2

ax.set_zlim(-1.01, 1.01)


if style == 'wireframe':
# wireframe
    ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)

elif style == 'surface':
    # surface
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
            linewidth=0, antialiased=False)


    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

    fig.colorbar(surf, shrink=0.5, aspect=5)

Z = X + Y
surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
        linewidth=0, antialiased=False)

    
plt.show()

