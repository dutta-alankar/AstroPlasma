#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  6 17:55:34 2023

@author: alankar
"""

import sys
sys.path.append('..')
import numpy as np
from scipy import interpolate
from astro_plasma import Ionization
import matplotlib.pyplot as plt
import matplotlib

## Plot Styling
matplotlib.rcParams['xtick.direction'] = 'in'
matplotlib.rcParams['ytick.direction'] = 'in'
matplotlib.rcParams['xtick.top'] = True
matplotlib.rcParams['ytick.right'] = True
matplotlib.rcParams['xtick.minor.visible'] = True
matplotlib.rcParams['ytick.minor.visible'] = True
matplotlib.rcParams['axes.grid'] = True
matplotlib.rcParams['lines.dash_capstyle'] = "round"
matplotlib.rcParams['lines.solid_capstyle'] = "round"
matplotlib.rcParams['legend.handletextpad'] = 0.4
matplotlib.rcParams['axes.linewidth'] = 0.8
matplotlib.rcParams['lines.linewidth'] = 3.0
matplotlib.rcParams['ytick.major.width'] = 0.6
matplotlib.rcParams['xtick.major.width'] = 0.6
matplotlib.rcParams['ytick.minor.width'] = 0.45
matplotlib.rcParams['xtick.minor.width'] = 0.45
matplotlib.rcParams['ytick.major.size'] = 4.0
matplotlib.rcParams['xtick.major.size'] = 4.0
matplotlib.rcParams['ytick.minor.size'] = 2.0
matplotlib.rcParams['xtick.minor.size'] = 2.0
matplotlib.rcParams['legend.handlelength'] = 2
matplotlib.rcParams["figure.dpi"] = 200
matplotlib.rcParams['axes.axisbelow'] = True

# Cloudy data
element = 8
frac = np.loadtxt('ion-frac-Oxygen.txt', skiprows=1, 
                  converters={i+1: lambda x: -30 if x==b'--' else x for i in range(element+1)})

do_isothermal, do_isentropic = True, True

fIon = Ionization().interpolate_ion_frac   
element = 8 
fig = plt.figure()
ax = fig.add_subplot(111)
Temp = np.logspace(4.2,7.2,500)

ion = 5
p = plt.loglog(Temp, 10.**np.array([fIon(temperature = T, metallicity = 0.99,
                          redshift = 0.001, element = element, ion = ion,
                          mode = "CIE") for T in Temp]), label=r'$f_{OV}$',
                          alpha = 0.6 )
fOV = interpolate.interp1d(frac[:,0], frac[:,ion]) # temperature and ion fraction in log10 
plt.loglog(Temp, 10.**fOV(np.log10(Temp)), linestyle='--', color=p[0].get_color(),
           linewidth=1.5 )

ion = 6
p = plt.loglog(Temp, 10.**np.array([fIon(nH=1.2e-4, temperature = T, metallicity = 0.99,
                          redshift = 0.01, element = element, ion = ion,
                          mode = "CIE") for T in Temp]), label=r'$f_{OVI}$',
                          alpha = 0.6 )
fOVI = interpolate.interp1d(frac[:,0], frac[:,ion]) # temperature and ion fraction in log10 
plt.loglog(Temp, 10.**fOVI(np.log10(Temp)), linestyle='--', color=p[0].get_color(),
           linewidth=1.5 )

ion = 7
p = plt.loglog(Temp, 10.**np.array([fIon(temperature = T, metallicity = 0.99,
                          redshift = 0.001, element = element, ion = ion,
                          mode = "CIE") for T in Temp]), label=r'$f_{OVII}$',
                          alpha = 0.6 )
fOVII = interpolate.interp1d(frac[:,0], frac[:,ion]) # temperature and ion fraction in log10 
p = plt.loglog(Temp, 10.**fOVII(np.log10(Temp)), linestyle='--', color=p[0].get_color(),
           linewidth=1.5 )

ion = 8
p = plt.loglog(Temp, 10.**np.array([fIon(temperature = T, metallicity = 0.99,
                          redshift = 0.001, element = element, ion = ion,
                          mode = "CIE") for T in Temp]), label=r'$f_{OVIII}$',
                          alpha = 0.6 )
fOVIII = interpolate.interp1d(frac[:,0], frac[:,ion]) # temperature and ion fraction in log10 
plt.loglog(Temp, 10.**fOVIII(np.log10(Temp)), linestyle='--', color=p[0].get_color(),
           linewidth=1.5 )

plt.title('Broken: Cloudy provided vs Solid: Our interpolator')
plt.ylabel(r'Ionization fraction')
plt.xlabel('Temperature [K]')
plt.legend(loc='upper left')
ax.yaxis.set_ticks_position('both')
ax.set_ylim(ymin=1e-10, ymax=1.3)
ax.set_xlim(xmin=4e4)
plt.savefig('ionization-test.png', transparent=True)
plt.show()