# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 18:23:40 2022

@author: alankar
"""

# Built-in imports
from pathlib import Path
from typing import Union, Optional, Callable
import os

# Third party imports
import h5py
import numpy as np

# Local package imports

from .datasift import DataSift
from .utils import LOCAL_DATA_PATH
from .data_dir import set_base_dir
from .download_database import download_emission_data

DEFAULT_BASE_DIR = LOCAL_DATA_PATH / "emission"
FILE_NAME_TEMPLATE = "emission.b_{:06d}.h5"
DOWNLOAD_IN_INIT = (Path(os.path.basename(FILE_NAME_TEMPLATE.format(0))), 0)


class EmissionSpectrum(DataSift):
    def __init__(
        self: "EmissionSpectrum",
        base_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Prepares the location to read data for generating emisson spectrum.

        Returns
        -------
        None.

        """
        self._check_and_download = download_emission_data
        self.file_name_template = FILE_NAME_TEMPLATE
        self.base_dir = Path(base_dir) if base_dir is not None else base_dir

    @property
    def base_dir(self):
        return self._base_dir

    @base_dir.setter
    def base_dir(
        self,
        base_dir: Optional[Path] = None,
    ):
        self._base_dir = set_base_dir(DEFAULT_BASE_DIR, base_dir)

        self._check_and_download(initialize=True)
        with h5py.File(self._base_dir / DOWNLOAD_IN_INIT[0], "r") as data:
            super().__init__(self, data)
            self._energy = np.array(data["output/energy"])

    def _get_file_path(self: "EmissionSpectrum", batch_id: int) -> Path:
        return self.base_dir / self.file_name_template.format(batch_id)

    def interpolate_spectrum(
        self: "EmissionSpectrum",
        nH: Union[int, float] = 1.2e-4,
        temperature: Union[int, float] = 2.7e6,
        metallicity: Union[int, float] = 0.5,
        redshift: Union[int, float] = 0.2,
        mode: str = "PIE",
        scaling_func: Callable = lambda x: x,
    ) -> np.ndarray:
        """
        Interpolate emission spectrum from pre-computed Cloudy table.

        Parameters
        ----------
        nH : float, optional
            Hydrogen number density
            (all hydrogen both neutral and ionized.
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
        spectrum : numpy array 2d
            returns the emitted spectrum
            as a 2d numpy array with two columns.
            Column 0: Energy in keV
            Column 1: spectral energy distribution (emissivity):
            4*pi*nu*j_nu (Unit: erg cm^-3 s^-1)

        """

        self.spectrum = np.zeros((self._energy.shape[0], 2))
        self.spectrum[:, 0] = self._energy

        _is_multiple = self._determine_multiple(nH, temperature, metallicity, redshift, mode)

        if _is_multiple:
            spectrum, _ = super()._interpolate(
                nH,
                temperature,
                metallicity,
                redshift,
                mode,
                f"output/emission/{mode}/total",
                (self.spectrum.shape[0],),
                scaling_func,
                (None, None),  # threshold cuts
            )
            spectrum = spectrum.flatten().reshape((*self._input_shape, spectrum.shape[-1]))
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
                (self.spectrum.shape[0],),
                scaling_func,
                (None, None),  # threshold cuts
            )
        return self.spectrum
