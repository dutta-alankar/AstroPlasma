# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 18:23:40 2022

@author: alankar
"""

# Built-in imports
from __future__ import annotations

from pathlib import Path
from typing import Callable

# Third party imports
import h5py
import numpy as np

from .datasift import DataSift
from .download_database import initialize_data
from .utils import LOCAL_DATA_PATH

# from typing import  Callable

# Local package imports

DEFAULT_BASE_DIR = LOCAL_DATA_PATH / "emission"
FILE_NAME_TEMPLATE = "emission.b_{:06d}.h5"


class EmissionSpectrum(DataSift):
    def __init__(self, base_dir: Path = DEFAULT_BASE_DIR):
        """
        Prepares the location to read data for generating emisson spectrum.

        Parameters
        ----------
        base_dir: Path
            Database directory
        """
        self._base_dir = base_dir
        initialize_data("emission")
        with h5py.File(self.base_dir / FILE_NAME_TEMPLATE.format(0)) as file:
            super().__init__(file)

        # FIXME: It should be iniitalized somewhere in the class
        self._energy = np.empty(10)

    @property
    def base_dir(self):
        return self._base_dir

    def _get_file_path(self, batch_id: int) -> Path:
        return self.base_dir / FILE_NAME_TEMPLATE.format(batch_id)

    def interpolate_spectrum(
        self,
        nH: int | float = 1.2e-4,
        temperature: int | float = 2.7e6,
        metallicity: int | float = 0.5,
        redshift: int | float = 0.2,
        mode="PIE",
        scaling_func: Callable = lambda x: x,
    ) -> np.ndarray:
        """
        Interpolate emission spectrum from pre-computed Cloudy table.

        Parameters
        ----------
        nH : float, optional
            Hydrogen number density
            (all hydrogen both neutral and ionized.)
            The default is 1.2e-4.
        temperature : float, optional
            Plasma temperature.
            The default is 2.7e6.
        metallicity : float, optional
            Plasma metallicity with respect to solar.
            The default is 0.5.
        redshift : float, optional
            Cosmological redshift of the universe.
            The default is 0.2.
        mode : str, optional
            ionization condition
            either CIE (collisional) or PIE (photo).
            The default is 'PIE'.
        scaling_func : callable function, optional
            function space in which intrepolation is
            carried out.
            The default is linear. log10 is another popular choice.

        Returns
        -------
        np.ndarray
            Returns the emitted spectrum
            as a 2d numpy array with two columns.
            Column 0: Energy in keV
            Column 1: spectral energy distribution (emissivity):
            4*pi*nu*j_nu (Unit: erg cm^-3 s^-1)

        """

        self.spectrum = np.zeros((self._energy.shape[0], 2))
        self.spectrum[:, 0] = self._energy

        _is_multiple = self._determine_multiple(nH, temperature, metallicity, redshift)

        if _is_multiple:
            spectrum, _ = super()._interpolate(
                nH,
                temperature,
                metallicity,
                redshift,
                mode,
                f"output/emission/{mode}/total",
                scaling_func,
                (self.spectrum.shape[0], None),
            )
            spectrum = spectrum.flatten().reshape((*self._input_shape, spectrum.shape[-1]))
            # noinspection PyAttributeOutsideInit
            self.spectrum = np.zeros((*spectrum.shape, 2), dtype=np.float64)
            for i in range(spectrum.shape[0]):
                self.spectrum[i, :, 0] = self._energy
            self.spectrum[:, :, 1] = spectrum
        else:
            self.spectrum[:, 1], _ = super()._interpolate(
                nH,
                temperature,
                metallicity,
                redshift,
                mode,
                f"output/emission/{mode}/total",
                scaling_func,
                (self.spectrum.shape[0], None),
            )
        return self.spectrum
