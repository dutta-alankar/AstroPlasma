#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 10:31:29 2022

@author: alankar
"""

import numpy as np
from scipy.interpolate import interp1d
import os

def cooling_approx(temperature, metallicity):
    '''
    Cooling function of an Astrophysical plasma. 
    Generated with a HM12 Xray-UV background.
    Currently, this doesn't take into account CIE vs PIE differences. I plan to add this feature shortly.

    Parameters
    ----------
    temperature : float/int/numpy array 1d
        Temperature of the plasma.
    metallicity : float/int/numpy array 1d
        Metallicity of the plasma with respect to Solar.

    Returns
    -------
    coolcurve : float/int/numpy array 1d
        Plasma cooling function normalized by nH^2.

    '''
    if type(temperature)==list: temperature = np.array(temperature)
    if type(metallicity)==list: metallicity = np.array(metallicity)
    file_path = os.path.realpath(__file__)
    dir_loc   = os.path.split(file_path)[:-1]
    cooling = np.loadtxt(os.path.join(*dir_loc,'cooltable.dat'))
    cooling = interp1d(cooling[:,0], cooling[:,1], fill_value='extrapolate')

    slope1 = -1/(np.log10(8.7e3)-np.log10(1.2e4))
    slope2 = 1/(np.log10(1.2e4)-np.log10(7e4))
    slope3 = -1/(np.log10(2e6)-np.log10(8e7))
    coolcurve = cooling(temperature)
    factor = np.piecewise(temperature, 
                          [temperature<8.7e3,
                           np.logical_and(temperature>=8.7e3,temperature<=1.2e4),
                           np.logical_and(temperature>1.2e4,temperature<=7e4),
                           np.logical_and(temperature>7e4,temperature<=2e6),
                           np.logical_and(temperature>2e6,temperature<=8e7),
                           temperature>8e7],
                          [lambda x: 0,
                           lambda x: slope1*(np.log10(x)-np.log10(8.7e3)),
                           lambda x: slope2*(np.log10(x)-np.log10(1.2e4))+1,
                           lambda x: 0,
                           lambda x: slope3*(np.log10(x)-np.log10(2e6)),
                           lambda x: 1
                           ])
    coolcurve = (factor+(1-factor)*metallicity)*coolcurve
    
    return coolcurve
    
