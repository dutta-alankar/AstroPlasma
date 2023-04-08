# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 14:19:12 2022

@author: Alankar
"""

import numpy as np
from typing import Union, List

## useful constants
yr = 365 * 24 * 60**2
Myr = 1e6 * yr
pi = np.pi
pc = 3.0856775807e18
kpc = 1e3 * pc
Mpc = 1e3 * kpc
s = 1
cm = 1
K = 1
km = 1e5 * cm
mp = 1.67262192369e-24
me = 9.1093837e-28
mH = 1.6735e-24
kB = 1.3806505e-16
G = 6.6726e-8
H0 = 67.4
H0cgs = H0 * ((km / s) / Mpc)
dcrit0 = 3 * H0cgs**2 / (8.0 * pi * G)
MSun = 2.0e33
X_solar = 0.7154
Y_solar = 0.2703
Z_solar = 0.0143


def Xp(
    metallicity: Union[float, int, List[Union[int, float]], np.ndarray]
) -> Union[float, np.ndarray]:
    if isinstance(metallicity, list):
        metallicity = np.array(metallicity)
    return X_solar * (1 - metallicity * Z_solar) / (X_solar + Y_solar)


def Yp(
    metallicity: Union[float, int, List[Union[int, float]], np.ndarray]
) -> Union[float, np.ndarray]:
    if isinstance(metallicity, list):
        metallicity = np.array(metallicity)
    return Y_solar * (1 - metallicity * Z_solar) / (X_solar + Y_solar)


def Zp(
    metallicity: Union[float, int, List[Union[int, float]], np.ndarray]
) -> Union[float, np.ndarray]:
    if isinstance(metallicity, list):
        metallicity = np.array(metallicity)
    return metallicity * Z_solar
