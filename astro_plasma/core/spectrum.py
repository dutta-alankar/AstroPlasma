# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 18:23:40 2022

@author: alankar
"""

import numpy as np
import h5py
from pathlib import Path
from .utils import fetch, LOCAL_DATA_PATH
from typing import Optional, Callable, Union, Set
from .datasift import DataSift

DEFAULT_BASE_DIR = LOCAL_DATA_PATH / "emission"
FILE_NAME_TEMPLATE = "emission.b_{:06d}.h5"
BASE_URL_TEMPLATE = "emission/download/{:d}/"
DOWNLOAD_IN_INIT = [
    (BASE_URL_TEMPLATE.format(0), Path(FILE_NAME_TEMPLATE.format(0))),
]


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
        self.base_url_template = BASE_URL_TEMPLATE
        self.file_name_template = FILE_NAME_TEMPLATE
        if base_dir is None:
            self.base_dir = DEFAULT_BASE_DIR
        else:
            self.base_dir = Path(base_dir)

        if not self.base_dir.exists():
            self.base_dir.mkdir(mode=0o755, parents=True)

        fetch(urls=DOWNLOAD_IN_INIT, base_dir=self.base_dir)

        data = h5py.File(self.base_dir / DOWNLOAD_IN_INIT[0][1], "r")
        super().__init__(data)
        self.energy = np.array(data["output/energy"])
        data.close()

    def _fetch_data(self: "EmissionSpectrum", batch_ids: Set[int]) -> None:
        urls = []
        for batch_id in batch_ids:
            urls.append(
                (
                    self.base_url_template.format(batch_id),
                    Path(self.file_name_template.format(batch_id)),
                )
            )

        fetch(urls=urls, base_dir=self.base_dir)

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

        self.spectrum = np.zeros((self.energy.shape[0], 2))
        self.spectrum[:, 0] = self.energy

        self.spectrum[:, 1] = super()._interpolate(
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
