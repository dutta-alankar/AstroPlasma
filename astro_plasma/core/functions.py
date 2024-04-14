# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 10:31:29 2022

@author: alankar
"""
from __future__ import annotations

from typing import Type

import numpy as np
from scipy.interpolate import interp1d

from utils import LOCAL_DATA_PATH

NumericOrArrayType = Type[float | int | list[int | float] | np.ndarray]


def cooling_approx(temperature: NumericOrArrayType, metallicity: NumericOrArrayType) -> NumericOrArrayType:
    """
    Cooling function of an Astrophysical plasma.
    Generated with a HM12 Xray-UV background.
    Currently, this doesn't take into account CIE vs PIE differences.
    I plan to add this feature shortly.

    Parameters
    ----------
    temperature : NumericOrArrayType
        Temperature of the plasma.
    metallicity : NumericOrArrayType
        Metallicity of the plasma with respect to Solar.

    Returns
    -------
    cool_curve: NumericOrArrayType
        Plasma cooling function normalized by nH^2.

    """
    if temperature is list:
        temperature = np.array(temperature)
    if metallicity is list:
        metallicity = np.array(metallicity)

    if temperature is np.ndarray and temperature.ndim > 1:
        raise ValueError("Temperature ndarray dimension should be 1.")

    if metallicity is np.ndarray and metallicity.ndim > 1:
        raise ValueError("Metallicity ndarray dimension should be 1.")

    slope1 = -1 / (np.log10(8.7e3) - np.log10(1.2e4))
    slope2 = 1 / (np.log10(1.2e4) - np.log10(7e4))
    slope3 = -1 / (np.log10(2e6) - np.log10(8e7))

    factor = np.piecewise(
        temperature,
        [
            temperature < 8.7e3,
            np.logical_and(temperature >= 8.7e3, temperature <= 1.2e4),
            np.logical_and(temperature > 1.2e4, temperature <= 7e4),
            np.logical_and(temperature > 7e4, temperature <= 2e6),
            np.logical_and(temperature > 2e6, temperature <= 8e7),
            temperature > 8e7,
        ],
        [
            lambda x: 0,
            lambda x: slope1 * (np.log10(x) - np.log10(8.7e3)),
            lambda x: slope2 * (np.log10(x) - np.log10(1.2e4)) + 1,
            lambda x: 0,
            lambda x: slope3 * (np.log10(x) - np.log10(2e6)),
            lambda x: 1,
        ],
    )

    cooling = np.loadtxt(LOCAL_DATA_PATH / "cooltable.dat")
    cooling_interp = interp1d(cooling[:, 0], cooling[:, 1], fill_value="extrapolate")
    cool_curve = cooling_interp(temperature)

    return (factor + (1 - factor) * metallicity) * cool_curve
