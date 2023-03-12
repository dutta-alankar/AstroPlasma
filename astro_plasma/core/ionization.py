#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 12:06:18 2022

@author: alankar
"""

import numpy as np
import h5py
from itertools import product
import os
from .constants import *
from pathlib import Path
from typing import Optional
from .utils import fetch, LOCAL_DATA_PATH

warn = False

DEFAULT_BASE_DIR = Path('.cache') / 'astro_plasma' / 'data' / 'ionization'
FILE_NAME_TEMPLATE = 'ionization.b_{:06d}.h5'
BASE_URL_TEMPLATE = 'ionization/download/{:d}/'
DOWNLOAD_IN_INIT = [
    (BASE_URL_TEMPLATE.format(0), FILE_NAME_TEMPLATE.format(0)),
]


class Ionization:

    def __init__(self, base_dir: Optional[Path | str] = None):
        '''
        Prepares the location to read data for generating emisson spectrum.

        Returns
        -------
        None.

        '''

        self.base_dir = DEFAULT_BASE_DIR if base_dir is None else base_dir
        if type(base_dir) == str:
            self.base_dir = Path(base_dir)

        if not self.base_dir.exists():
            self.base_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

        fetch(urls=DOWNLOAD_IN_INIT, base_dir=self.base_dir)
        data = h5py.File(self.base_dir/DOWNLOAD_IN_INIT[0][1], 'r')
        self.nH_data = np.array(data['params/nH'])
        self.T_data = np.array(data['params/temperature'])
        self.Z_data = np.array(data['params/metallicity'])
        self.red_data = np.array(data['params/redshift'])

        self.batch_size = np.prod(np.array(data['header/batch_dim']))
        self.total_size = np.prod(np.array(data['header/total_size']))
        data.close()

    def _findBatches(self, nH, temperature, metallicity, redshift):
        '''
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
            List of all the unique batch ids.

        '''
        i_vals, j_vals, k_vals, l_vals = None, None, None, None
        if (np.sum(nH == self.nH_data) == 1):
            i_vals = [np.where(nH == self.nH_data)[0][0],
                      np.where(nH == self.nH_data)[0][0]]
        else:
            i_vals = [np.sum(nH > self.nH_data)-1, np.sum(nH > self.nH_data)]

        if (np.sum(temperature == self.T_data) == 1):
            j_vals = [np.where(temperature == self.T_data)[
                0][0], np.where(temperature == self.T_data)[0][0]]
        else:
            j_vals = [np.sum(temperature > self.T_data)-1,
                      np.sum(temperature > self.T_data)]

        if (np.sum(metallicity == self.Z_data) == 1):
            k_vals = [np.where(metallicity == self.Z_data)[
                0][0], np.where(metallicity == self.Z_data)[0][0]]
        else:
            k_vals = [np.sum(metallicity > self.Z_data)-1,
                      np.sum(metallicity > self.Z_data)]

        if (np.sum(redshift == self.red_data) == 1):
            l_vals = [np.where(redshift == self.red_data)[0]
                      [0], np.where(redshift == self.red_data)[0][0]]
        else:
            l_vals = [np.sum(redshift > self.red_data)-1,
                      np.sum(redshift > self.red_data)]

        batch_ids = set()
        # identify unique batches
        for i, j, k, l in product(i_vals, j_vals, k_vals, l_vals):
            if (i == self.nH_data.shape[0]):
                if (warn):
                    print("Problem: nH", nH)
                i = i-1
            if (i == -1):
                if (warn):
                    print("Problem: nH", nH)
                i = i+1
            if (j == self.T_data.shape[0]):
                if (warn):
                    print("Problem: T", temperature)
                j = j-1
            if (j == -1):
                if (warn):
                    print("Problem: T", temperature)
                j = j+1
            if (k == self.Z_data.shape[0]):
                if (warn):
                    print("Problem: met", metallicity)
                k = k-1
            if (k == -1):
                if (warn):
                    print("Problem: met", metallicity)
                k = k+1
            if (l == self.red_data.shape[0]):
                if (warn):
                    print("Problem: red", redshift)
                l = l-1
            if (l == -1):
                if (warn):
                    print("Problem: red", redshift)
                l = l+1
            counter = (l)*self.Z_data.shape[0]*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (k)*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (j)*self.nH_data.shape[0] + \
                      (i)
            batch_id = counter//self.batch_size
            batch_ids.add(batch_id)

        # print("Batches involved: ", batch_ids)
        # later use this logic to fetch batches from cloud if not present
        self.i_vals = i_vals
        self.j_vals = j_vals
        self.k_vals = k_vals
        self.l_vals = l_vals

        urls = []
        for batch_id in batch_ids:
            urls.append((BASE_URL_TEMPLATE.format(batch_id),
                        FILE_NAME_TEMPLATE.format(batch_id)))

        fetch(urls=urls, base_dir=self.base_dir)
        return batch_ids

    def interpolateIonFrac(self, nH=1.2e-4, temperature=2.7e6, metallicity=0.5, redshift=0.2, element=2, ion=1, mode='PIE'):
        '''
        Interpolates the ionization fraction of the plasma from pre-computed Cloudy models of ion networks.
        This fraction is with respect to the total number density of element to which the ion belongs to in the plasma. 
        To get number fraction of the species, one must need to multiply with the abundance fraction of the element. 
        Solar values are provided in a table in this repo. Other metallicities with respect to Solar can be simply scaled.

        Parameters
        ----------
        nH : float, optional
            Hydrogen number density (all hydrogen both neutral and ionized. The default is 1.2e-4.
        temperature : float, optional
            Plasma temperature. The default is 2.7e6.
        metallicity : float, optional
            Plasma metallicity with respect to solar. The default is 0.5.
        redshift : float, optional
            Cosmological redshift of the universe. The default is 0.2.
        element : int, optional
            Atomic number of the element. The default is 2.
        ion : int, optional
            Ionization species of the element. Must between 1 and element+1. The default is 1.
            1:neutral, 2:+, 3:++, ...
        mode : str, optional
            ionization condition either CIE (collisional) or PIE (photo). The default is 'PIE'.

        Returns
        -------
        float
            ionization fraction of the requested ion species of the requested element.

        '''
        # element = 1: H, 2: He, 3: Li, ... 30: Zn
        # ion = 1 : neutral, 2: +, 3: ++ .... (element+1): (++++... element times)
        if (mode != 'PIE' and mode != 'CIE'):
            print('Problem! Invalid mode: %s.' % mode)
            return None
        if (ion < 0 or ion > element+1):
            print('Problem! Invalid ion %d for element %d.' % (ion, element))
            return None
        if (element < 0 or element > 30):
            print('Problem! Invalid element %d.' % element)
            return None

        fracIon = np.zeros((element+1,), dtype=np.float64)

        batch_ids = self._findBatches(nH, temperature, metallicity, redshift)
        i_vals = self.i_vals
        j_vals = self.j_vals
        k_vals = self.k_vals
        l_vals = self.l_vals

        inv_weight = 0.
        # print(i_vals, j_vals, k_vals, l_vals)

        data = []
        for batch_id in batch_ids:
            file = self.base_dir / FILE_NAME_TEMPLATE.format(batch_id)
            hdf = h5py.File(file, 'r')
            data.append([batch_id, hdf])

        for i, j, k, l in product(i_vals, j_vals, k_vals, l_vals):
            if (i == self.nH_data.shape[0]):
                if (warn):
                    print("Problem: nH", nH)
                i = i-1
            if (i == -1):
                if (warn):
                    print("Problem: nH", nH)
                i = i+1
            if (j == self.T_data.shape[0]):
                if (warn):
                    print("Problem: T", temperature)
                j = j-1
            if (j == -1):
                if (warn):
                    print("Problem: T", temperature)
                j = j+1
            if (k == self.Z_data.shape[0]):
                if (warn):
                    print("Problem: met", metallicity)
                k = k-1
            if (k == -1):
                if (warn):
                    print("Problem: met", metallicity)
                k = k+1
            if (l == self.red_data.shape[0]):
                if (warn):
                    print("Problem: red", redshift)
                l = l-1
            if (l == -1):
                if (warn):
                    print("Problem: red", redshift)
                l = l+1

            d_i = np.abs(self.nH_data[i]-nH)
            d_j = np.abs(self.T_data[j]-temperature)
            d_k = np.abs(self.Z_data[k]-metallicity)
            d_l = np.abs(self.red_data[l]-redshift)

            # print('Data vals: ', self.nH_data[i], self.T_data[j], self.Z_data[k], self.red_data[l] )
            # print(i, j, k, l)
            epsilon = 1e-6
            weight = np.sqrt(d_i**2 + d_j**2 + d_k**2 + d_l**2 + epsilon)

            counter = (l)*self.Z_data.shape[0]*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (k)*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (j)*self.nH_data.shape[0] + \
                      (i)
            batch_id = counter//self.batch_size

            for id_data in data:
                if id_data[0] == batch_id:
                    hdf = id_data[1]
                    local_pos = counter % self.batch_size - 1
                    slice_start, slice_stop = int(
                        (element-1)*(element+2)/2), int(element*(element+3)/2)
                    fracIon += ((np.array(hdf['output/fracIon/%s' % mode])
                                [local_pos, slice_start:slice_stop]) / weight)

            inv_weight += 1/weight

        fracIon = fracIon/inv_weight

        for id_data in data:
            id_data[1].close()

        # array starts from 0 but ion from 1
        return fracIon[ion-1]

    def interpolateNumDens(self, nH=1.2e-4, temperature=2.7e6, metallicity=0.5, redshift=0.2, mode='PIE', part_type='electron'):
        '''
        Interpolates the number density of different species or the total number density of the plasma 
        from pre-computed Cloudy models of ion networks.

        Parameters
        ----------
        nH : float, optional
            Hydrogen number density (all hydrogen both neutral and ionized. The default is 1.2e-4.
        temperature : float, optional
            Plasma temperature. The default is 2.7e6.
        metallicity : float, optional
            Plasma metallicity with respect to solar. The default is 0.5.
        redshift : float, optional
            Cosmological redshift of the universe. The default is 0.2.
        mode : str, optional
            ionization condition either CIE (collisional) or PIE (photo). The default is 'PIE'.
        part_type : str, optional
            DESCRIPTION. The default is 'electron'.

        Returns
        -------
        float
            number density of the requested species.

        '''
        # print(nH, temperature, metallicity, redshift, mode, part_type)
        abn_file = LOCAL_DATA_PATH / 'solar_GASS10.abn'
        with abn_file.open() as file:
            abn = np.array([float(element.split()[-1])
                            for element in file.readlines()[2:32]])  # till Zinc

        ion_count = 0

        for i in range(30):  # till Zn
            for j in range(i+2):
                ion_count += 1

        X_solar = 0.7154
        Y_solar = 0.2703
        Z_solar = 0.0143

        Xp = X_solar*(1-metallicity*Z_solar)/(X_solar+Y_solar)
        Yp = Y_solar*(1-metallicity*Z_solar)/(X_solar+Y_solar)
        Zp = metallicity*Z_solar  # Z varied independent of nH and nHe

        # element = 1: H, 2: He, 3: Li, ... 30: Zn
        # ion = 1 : neutral, 2: +, 3: ++ .... (element+1): (++++... element times)
        if (mode != 'PIE' and mode != 'CIE'):
            print('Problem! Invalid mode: %s.' % mode)
            return None

        batch_ids = self._findBatches(nH, temperature, metallicity, redshift)
        i_vals = self.i_vals
        j_vals = self.j_vals
        k_vals = self.k_vals
        l_vals = self.l_vals

        fracIon = np.zeros((ion_count,), dtype=np.float64)
        inv_weight = 0
        # print(i_vals, j_vals, k_vals, l_vals)

        data = []
        for batch_id in batch_ids:
            file = self.base_dir / FILE_NAME_TEMPLATE.format(batch_id)
            hdf = h5py.File(file, 'r')
            data.append([batch_id, hdf])

        for i, j, k, l in product(i_vals, j_vals, k_vals, l_vals):
            if (i == self.nH_data.shape[0]):
                if (warn):
                    print("Problem: nH", nH)
                i = i-1
            if (i == -1):
                if (warn):
                    print("Problem: nH", nH)
                i = i+1
            if (j == self.T_data.shape[0]):
                if (warn):
                    print("Problem: T", temperature)
                j = j-1
            if (j == -1):
                if (warn):
                    print("Problem: T", temperature)
                j = j+1
            if (k == self.Z_data.shape[0]):
                if (warn):
                    print("Problem: met", metallicity)
                k = k-1
            if (k == -1):
                if (warn):
                    print("Problem: met", metallicity)
                k = k+1
            if (l == self.red_data.shape[0]):
                if (warn):
                    print("Problem: red", redshift)
                l = l-1
            if (l == -1):
                if (warn):
                    print("Problem: red", redshift)
                l = l+1

            d_i = np.abs(self.nH_data[i]-nH)
            d_j = np.abs(self.T_data[j]-temperature)
            d_k = np.abs(self.Z_data[k]-metallicity)
            d_l = np.abs(self.red_data[l]-redshift)

            # print('Data vals: ', self.nH_data[i], self.T_data[j], self.Z_data[k], self.red_data[l] )
            # print(i, j, k, l)
            epsilon = 1e-6
            weight = np.sqrt(d_i**2 + d_j**2 + d_k**2 + d_l**2 + epsilon)
            # nearest neighbour interpolation
            counter = (l)*self.Z_data.shape[0]*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (k)*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (j)*self.nH_data.shape[0] + \
                      (i)
            batch_id = counter//self.batch_size

            for id_data in data:
                if id_data[0] == batch_id:
                    hdf = id_data[1]
                    local_pos = counter % self.batch_size - 1
                    fracIon += ((np.array(hdf['output/fracIon/%s' %
                                mode])[local_pos, :]) / weight)

            inv_weight += 1/weight

        fracIon = fracIon/inv_weight
        fracIon = 10.**fracIon

        for id_data in data:
            id_data[1].close()

        if (part_type == 'all'):
            ndens = 0
            ion_count = 0
            for element in range(30):
                for ion in range(element+2):
                    if (element+1 == 1):  # H
                        ndens += (ion+1)*(Xp/X_solar) * \
                            abn[element]*fracIon[ion_count]*nH
                    elif (element+1 == 2):  # He
                        ndens += (ion+1)*(Yp/Y_solar) * \
                            abn[element]*fracIon[ion_count]*nH
                    else:
                        ndens += (ion+1)*(Zp/Z_solar) * \
                            abn[element]*fracIon[ion_count]*nH
                    ion_count += 1
            return ndens

        elif (part_type == 'electron'):
            ne = 0
            ion_count = 0
            for element in range(30):
                for ion in range(element+2):
                    if (element+1 == 1):  # H
                        ne += ion*(Xp/X_solar)*nH * \
                            abn[element]*fracIon[ion_count]
                    elif (element+1 == 2):  # He
                        ne += ion*(Yp/Y_solar)*nH * \
                            abn[element]*fracIon[ion_count]
                    else:
                        ne += ion*(Zp/Z_solar)*nH * \
                            abn[element]*fracIon[ion_count]
                    ion_count += 1
            return ne

        elif (part_type == 'ion'):
            nion = 0
            ion_count = 0
            for element in range(30):
                for ion in range(1, element+2):
                    if (element+1 == 1):  # H
                        nion += (Xp/X_solar)*nH*abn[element]*fracIon[ion_count]
                    elif (element+1 == 2):  # He
                        nion += (Yp/Y_solar)*nH*abn[element]*fracIon[ion_count]
                    else:
                        nion += ion*(Zp/Z_solar)*nH * \
                            abn[element]*fracIon[ion_count]
                    ion_count += 1
            return nion

        else:
            print(f'Invalid part_type: {part_type}')
        return None

    def interpolateMu(self, nH=1.2e-4, temperature=2.7e6, metallicity=0.5, redshift=0.2, mode='PIE'):
        '''
        Interpolates the mean particle mass of the plasma from pre-computed Cloudy models of ion networks.
        This mean particle mass changes as the ionization of the palsma changes the number of free electrons
        in the plasma. Greater the ionization, hence the number of free electrons, lower the mean particle mass.

        Parameters
        ----------
        nH : float, optional
            Hydrogen number density (all hydrogen both neutral and ionized. The default is 1.2e-4.
        temperature : float, optional
            Plasma temperature. The default is 2.7e6.
        metallicity : float, optional
            Plasma metallicity with respect to solar. The default is 0.5.
        redshift : float, optional
            Cosmological redshift of the universe. The default is 0.2.
        mode : str, optional
            ionization condition either CIE (collisional) or PIE (photo). The default is 'PIE'.

        Returns
        -------
        float
            mean particle mass of the plasma.

        '''
        abn_file = LOCAL_DATA_PATH / 'solar_GASS10.abn'
        with abn_file.open() as file:
            abn = np.array([float(element.split()[-1])
                            for element in file.readlines()[2:32]])  # till Zinc

        ion_count = 0

        for i in range(30):  # till Zn
            for j in range(i+2):
                ion_count += 1

        X_solar = 0.7154
        Y_solar = 0.2703
        Z_solar = 0.0143

        Xp = X_solar*(1-metallicity*Z_solar)/(X_solar+Y_solar)
        Yp = Y_solar*(1-metallicity*Z_solar)/(X_solar+Y_solar)
        Zp = metallicity*Z_solar  # Z varied independent of nH and nHe

        # element = 1: H, 2: He, 3: Li, ... 30: Zn
        # ion = 1 : neutral, 2: +, 3: ++ .... (element+1): (++++... element times)
        if (mode != 'PIE' and mode != 'CIE'):
            print('Problem! Invalid mode: %s.' % mode)
            return None

        batch_ids = self._findBatches(nH, temperature, metallicity, redshift)
        i_vals = self.i_vals
        j_vals = self.j_vals
        k_vals = self.k_vals
        l_vals = self.l_vals

        fracIon = np.zeros((ion_count,), dtype=np.float64)
        inv_weight = 0
        # print(i_vals, j_vals, k_vals, l_vals)

        # print("Batches involved: ", batch_ids)
        data = []
        for batch_id in batch_ids:
            file = self.base_dir / FILE_NAME_TEMPLATE.format(batch_id)
            hdf = h5py.File(file, 'r')
            data.append([batch_id, hdf])

        for i, j, k, l in product(i_vals, j_vals, k_vals, l_vals):
            if (i == self.nH_data.shape[0]):
                if (warn):
                    print("Problem: nH", nH)
                i = i-1
            if (i == -1):
                if (warn):
                    print("Problem: nH", nH)
                i = i+1
            if (j == self.T_data.shape[0]):
                if (warn):
                    print("Problem: T", temperature)
                j = j-1
            if (j == -1):
                if (warn):
                    print("Problem: T", temperature)
                j = j+1
            if (k == self.Z_data.shape[0]):
                if (warn):
                    print("Problem: met", metallicity)
                k = k-1
            if (k == -1):
                if (warn):
                    print("Problem: met", metallicity)
                k = k+1
            if (l == self.red_data.shape[0]):
                if (warn):
                    print("Problem: red", redshift)
                l = l-1
            if (l == -1):
                if (warn):
                    print("Problem: red", redshift)
                l = l+1
            d_i = np.abs(self.nH_data[i]-nH)
            d_j = np.abs(self.T_data[j]-temperature)
            d_k = np.abs(self.Z_data[k]-metallicity)
            d_l = np.abs(self.red_data[l]-redshift)

            # print('Data vals: ', self.nH_data[i], self.T_data[j], self.Z_data[k], self.red_data[l] )
            # print(i, j, k, l)
            epsilon = 1e-6
            weight = np.sqrt(d_i**2 + d_j**2 + d_k**2 + d_l**2 + epsilon)

            counter = (l)*self.Z_data.shape[0]*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (k)*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (j)*self.nH_data.shape[0] + \
                      (i)
            batch_id = counter//self.batch_size

            for id_data in data:
                if id_data[0] == batch_id:
                    hdf = id_data[1]
                    local_pos = counter % self.batch_size - 1
                    fracIon += ((np.array(hdf['output/fracIon/%s' %
                                mode])[local_pos, :]) / weight)

            inv_weight += 1/weight

        fracIon = fracIon/inv_weight
        fracIon = 10.**fracIon

        for id_data in data:
            id_data[1].close()

        ndens = 0
        ion_count = 0
        for element in range(30):
            for ion in range(element+2):
                if (element+1 == 1):  # H
                    ndens += (ion+1)*(Xp/X_solar) * \
                        abn[element]*fracIon[ion_count]*nH
                elif (element+1 == 2):  # He
                    ndens += (ion+1)*(Yp/Y_solar) * \
                        abn[element]*fracIon[ion_count]*nH
                else:
                    ndens += (ion+1)*(Zp/Z_solar) * \
                        abn[element]*fracIon[ion_count]*nH
                ion_count += 1
        # print("abn ", abn)
        # print("fracIon ", fracIon)
        # print("ndens ", ndens)
        return (nH/ndens)*(mH/mp)/Xp
