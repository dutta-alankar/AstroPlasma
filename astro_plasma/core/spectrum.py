# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 18:23:40 2022

@author: alankar
"""

import numpy as np
import h5py
from itertools import product
from pathlib import Path
from astro_plasma.core.utils import fetch
from typing import Optional, Callable

warn = False

DEFAULT_BASE_DIR = Path(".cache") / "astro_plasma" / "data" / "spectrum"
FILE_NAME_TEMPLATE = "emission.b_{:06d}.h5"
BASE_URL_TEMPLATE = "emission/download/{:d}/"
DOWNLOAD_IN_INIT = [
    (BASE_URL_TEMPLATE.format(0), FILE_NAME_TEMPLATE.format(0)),
]


class EmissionSpectrum:
    def __init__(self, base_dir: Optional[Path | str] = None):
        """
        Prepares the location to read data for generating emisson spectrum.

        Returns
        -------
        None.

        """

        self.base_dir = DEFAULT_BASE_DIR if base_dir is None else base_dir
        if type(base_dir) == str:
            self.base_dir = Path(base_dir)

        if not self.base_dir.exists():
            self.base_dir.mkdir(mode=0o755, parents=True)

        fetch(urls=DOWNLOAD_IN_INIT, base_dir=self.base_dir)

        data = h5py.File(self.base_dir / DOWNLOAD_IN_INIT[0][1], "r")
        self.nH_data = np.array(data["params/nH"])
        self.T_data = np.array(data["params/temperature"])
        self.Z_data = np.array(data["params/metallicity"])
        self.red_data = np.array(data["params/redshift"])
        self.energy = np.array(data["output/energy"])

        self.batch_size = np.prod(np.array(data["header/batch_dim"]))
        self.total_size = np.prod(np.array(data["header/total_size"]))
        data.close()

    def _findBatches(self, nH, temperature, metallicity, redshift):
        """
        Find the batches needed from the data files.

        Parameters
        ----------
        nH : float, optional
            Hydrogen number density (all hydrogen both neutral and ionized.
        temperature : float, optional
            Plasma temperature.
        metallicity : float, optional
            Plasma metallicity with respect to solar.
        redshift : float, optional
            Cosmological redshift of the universe.

        Returns
        -------
        batch_ids : set
            Set of all the unique batch ids.

        """
        i_vals, j_vals, k_vals, m_vals = None, None, None, None
        if np.sum(nH == self.nH_data) == 1:
            i_vals = [
                np.where(nH == self.nH_data)[0][0],
                np.where(nH == self.nH_data)[0][0],
            ]
        else:
            i_vals = [np.sum(nH > self.nH_data) - 1, np.sum(nH > self.nH_data)]

        if np.sum(temperature == self.T_data) == 1:
            j_vals = [
                np.where(temperature == self.T_data)[0][0],
                np.where(temperature == self.T_data)[0][0],
            ]
        else:
            j_vals = [
                np.sum(temperature > self.T_data) - 1,
                np.sum(temperature > self.T_data),
            ]

        if np.sum(metallicity == self.Z_data) == 1:
            k_vals = [
                np.where(metallicity == self.Z_data)[0][0],
                np.where(metallicity == self.Z_data)[0][0],
            ]
        else:
            k_vals = [
                np.sum(metallicity > self.Z_data) - 1,
                np.sum(metallicity > self.Z_data),
            ]

        if np.sum(redshift == self.red_data) == 1:
            m_vals = [
                np.where(redshift == self.red_data)[0][0],
                np.where(redshift == self.red_data)[0][0],
            ]
        else:
            m_vals = [
                np.sum(redshift > self.red_data) - 1,
                np.sum(redshift > self.red_data),
            ]

        batch_ids = set()
        # identify unique batches
        for i, j, k, m in product(i_vals, j_vals, k_vals, m_vals):
            if i == self.nH_data.shape[0]:
                if warn:
                    print("Problem: nH", nH)
                i = i - 1
            if i == -1:
                if warn:
                    print("Problem: nH", nH)
                i = i + 1
            if j == self.T_data.shape[0]:
                if warn:
                    print("Problem: T", temperature)
                j = j - 1
            if j == -1:
                if warn:
                    print("Problem: T", temperature)
                j = j + 1
            if k == self.Z_data.shape[0]:
                if warn:
                    print("Problem: met", metallicity)
                k = k - 1
            if k == -1:
                if warn:
                    print("Problem: met", metallicity)
                k = k + 1
            if m == self.red_data.shape[0]:
                if warn:
                    print("Problem: red", redshift)
                m = m - 1
            if m == -1:
                if warn:
                    print("Problem: red", redshift)
                m = m + 1
            counter = (
                (m)
                * self.Z_data.shape[0]
                * self.T_data.shape[0]
                * self.nH_data.shape[0]
                + (k) * self.T_data.shape[0] * self.nH_data.shape[0]
                + (j) * self.nH_data.shape[0]
                + (i)
            )
            batch_id = counter // self.batch_size
            batch_ids.add(batch_id)
        batch_ids = set(batch_ids)
        # print("Batches involved: ", batch_ids)
        # later use this logic to fetch batches from cloud if not present
        self.i_vals = i_vals
        self.j_vals = j_vals
        self.k_vals = k_vals
        self.m_vals = m_vals

        urls = []
        for batch_id in batch_ids:
            urls.append(
                (
                    BASE_URL_TEMPLATE.format(batch_id),
                    FILE_NAME_TEMPLATE.format(batch_id),
                )
            )

        fetch(urls=urls, base_dir=self.base_dir)

        return batch_ids

    def interpolate(self, nH=1.2e-4, temperature=2.7e6, metallicity=0.5, redshift=0.2, mode='PIE', scaling_func: Callable = lambda x: x):
        '''
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

        Returns
        -------
        spectrum : numpy array 2d
            returns the emitted spectrum
            as a 2d numpy array with two columns.
            Column 0: Energy in keV
            Column 1: spectral energy distribution (emissivity):
            4*pi*nu*j_nu (Unit: erg cm^-3 s^-1)

        '''
        if mode != "PIE" and mode != "CIE":
            print("Problem! Invalid mode: %s." % mode)
            return None

        spectrum = np.zeros((self.energy.shape[0], 2))
        spectrum[:, 0] = self.energy

        batch_ids = self._findBatches(nH, temperature, metallicity, redshift)
        i_vals = self.i_vals
        j_vals = self.j_vals
        k_vals = self.k_vals
        m_vals = self.m_vals

        inv_weight = 0.0
        # print(i_vals, j_vals, k_vals, m_vals)

        data = []
        for batch_id in batch_ids:
            file = self.base_dir / FILE_NAME_TEMPLATE.format(batch_id)
            hdf = h5py.File(file, "r")
            data.append([batch_id, hdf])

        for i, j, k, m in product(i_vals, j_vals, k_vals, m_vals):
            if i == self.nH_data.shape[0]:
                if warn:
                    print("Problem: nH", nH)
                i = i - 1
            if i == -1:
                if warn:
                    print("Problem: nH", nH)
                i = i + 1
            if j == self.T_data.shape[0]:
                if warn:
                    print("Problem: T", temperature)
                j = j - 1
            if j == -1:
                if warn:
                    print("Problem: T", temperature)
                j = j + 1
            if k == self.Z_data.shape[0]:
                if warn:
                    print("Problem: met", metallicity)
                k = k - 1
            if k == -1:
                if warn:
                    print("Problem: met", metallicity)
                k = k + 1
            if m == self.red_data.shape[0]:
                if warn:
                    print("Problem: red", redshift)
                m = m - 1
            if m == -1:
                if warn:
                    print("Problem: red", redshift)
                m = m + 1

            epsilon = 1e-6
            d_i = np.abs(scaling_func(self.nH_data[i])-scaling_func(nH))
            d_j = np.abs(scaling_func(
                self.T_data[j])-scaling_func(temperature))
            d_k = np.abs(scaling_func(
                self.Z_data[k])-scaling_func(metallicity))
            d_m = np.abs(scaling_func(
                epsilon+self.red_data[m])-scaling_func(epsilon+redshift))

            # print('Data vals: ', self.nH_data[i], self.T_data[j], self.Z_data[k], self.red_data[l] )
            # print(i, j, k, l)
            weight = np.sqrt(d_i**2 + d_j**2 + d_k**2 + d_m**2 + epsilon)
            # nearest neighbour interpolation
            counter = (
                (m)
                * self.Z_data.shape[0]
                * self.T_data.shape[0]
                * self.nH_data.shape[0]
                + (k) * self.T_data.shape[0] * self.nH_data.shape[0]
                + (j) * self.nH_data.shape[0]
                + (i)
            )
            batch_id = counter // self.batch_size

            for id_data in data:
                if id_data[0] == batch_id:
                    hdf = id_data[1]
                    local_pos = counter % self.batch_size - 1
                    spectrum[:, 1] += (
                        np.array(
                            hdf[f"output/emission/{mode}/total"])[local_pos, :]
                    ) / weight

            inv_weight += 1 / weight

        spectrum[:, 1] = spectrum[:, 1] / inv_weight

        for id_data in data:
            id_data[1].close()

        return spectrum
