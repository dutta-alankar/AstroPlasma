# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 21:30:23 2023

@author: alankar
"""

from abc import ABC, abstractmethod
import numpy as np
from itertools import product
from pathlib import Path
from typing import Callable, Optional, Union, Tuple, List, Set
import h5py
import sys

_warn = False


class DataSift(ABC):
    def __init__(
        self: "DataSift",
        data: h5py.File,
    ) -> None:
        """
        Prepares the location to read data for interpolation.

        Returns
        -------
        None.

        """
        self.nH_data = np.array(data["params/nH"])
        self.T_data = np.array(data["params/temperature"])
        self.Z_data = np.array(data["params/metallicity"])
        self.red_data = np.array(data["params/redshift"])

        self.batch_size = np.prod(np.array(data["header/batch_dim"]))
        self.total_size = np.prod(np.array(data["header/total_size"]))

    def _identify_batch(self: "DataSift", i: int, j: int, k: int, m: int) -> int:
        batch_id = self._get_counter(i, j, k, m) // self.batch_size
        return batch_id

    def _get_counter(self: "DataSift", i: int, j: int, k: int, m: int) -> int:
        counter = (
            (m) * self.Z_data.shape[0] * self.T_data.shape[0] * self.nH_data.shape[0]
            + (k) * self.T_data.shape[0] * self.nH_data.shape[0]
            + (j) * self.nH_data.shape[0]
            + (i)
        )
        return counter

    def _determine_multiple_input(
        self: "DataSift",
        nH: Union[int, float, List, np.ndarray],
        temperature: Union[int, float, List, np.ndarray],
        metallicity: Union[int, float, List, np.ndarray],
        redshift: Union[int, float, List, np.ndarray],
    ) -> bool:
        """
        Determine if multiple datapoints are requested.

        Parameters
        ----------
        nH : float
            Hydrogen number density (all hydrogen both neutral and ionized.
        temperature : float, array, list
            Plasma temperature.
        metallicity : float, array, list
            Plasma metallicity with respect to solar.
        redshift : float, array, list
            Cosmological redshift of the universe.

        Returns
        -------
        condition : bool
            True if multiple data is requested

        """
        condition = isinstance(nH, list) or isinstance(nH, np.ndarray)
        condition = condition and (isinstance(temperature, list) or isinstance(temperature, np.ndarray))
        condition = condition and (isinstance(metallicity, list) or isinstance(metallicity, np.ndarray))
        condition = condition and (isinstance(redshift, list) or isinstance(redshift, np.ndarray))

        return condition
        
    def _process_arguments_flags(
        self: "DataSift",
        nH: Union[int, float, List, np.ndarray],
        temperature: Union[int, float, List, np.ndarray],
        metallicity: Union[int, float, List, np.ndarray],
        redshift: Union[int, float, List, np.ndarray],
    ) -> Tuple[List[bool]]:
        """
        Determine if multiple datapoints are requested.

        Parameters
        ----------
        nH : float
            Hydrogen number density (all hydrogen both neutral and ionized.
        temperature : float, array, list
            Plasma temperature.
        metallicity : float, array, list
            Plasma metallicity with respect to solar.
        redshift : float, array, list
            Cosmological redshift of the universe.

        Returns
        -------
        flags tuple : tuple
            flags.

        """
        _argument_type = ["nH", "temperature", "metallicity", "redshift"]
        _array_argument = [True, True, True, True] # array to flag which arguments are arrays
        _array_argument[0] = isinstance(nH, list) or isinstance(nH, np.ndarray)
        _array_argument[1] = isinstance(temperature, list) or isinstance(temperature, np.ndarray) 
        _array_argument[2] = isinstance(metallicity, list) or isinstance(metallicity, np.ndarray)
        _array_argument[3] = isinstance(redshift, list) or isinstance(redshift, np.ndarray)
        
        _dummy_array = [False, False, False, False] # array to flag which arguments are length 1 array
        if _array_argument[0]:
            _dummy_array[0] = len(nH)==1
        if _array_argument[1]:
            _dummy_array[1] = len(temperature)==1
        if _array_argument[2]:
            _dummy_array[2] = len(metallicity)==1
        if _array_argument[3]:
            _dummy_array[3] = len(redshift)==1
            
        return (_array_argument, _dummy_array)
        
    def _prepare_arguments(
        self: "DataSift",
        nH: Union[int, float, List, np.ndarray],
        temperature: Union[int, float, List, np.ndarray],
        metallicity: Union[int, float, List, np.ndarray],
        redshift: Union[int, float, List, np.ndarray],
        _array_argument: List[bool],
        _dummy_array: List[bool],
    ) -> Tuple[Tuple[int], List[np.ndarray]]:
        """
        Determine if multiple datapoints are requested.

        Parameters
        ----------
        nH : float
            Hydrogen number density (all hydrogen both neutral and ionized.
        temperature : float, array, list
            Plasma temperature.
        metallicity : float, array, list
            Plasma metallicity with respect to solar.
        redshift : float, array, list
            Cosmological redshift of the universe.

        Returns
        -------
        input data tuple : tuple
            prepared input data.

        """    
        _input_shape: Optional[Tuple] = None
        argument_collection = [nH, temperature, metallicity, redshift]
        for indx, _if_this_is_arr in enumerate(_array_argument):
            if not(_if_this_is_arr):
                argument_collection[indx] = np.array([argument_collection[indx],])
            else:
               argument_collection[indx] = np.array(argument_collection[indx])
               if _input_shape is None:
                   _input_shape = argument_collection[indx].shape
               else:
                   if (_input_shape != argument_collection[indx].shape):
                       raise ValueError(f"Check needed from user: Invalid input arguments which are not in compliance with each other! Code Aborted!")
            argument_collection[indx] = argument_collection[indx].flatten()
        if np.sum(_dummy_array) == 4 or np.sum(_array_argument) == 0:
            _input_shape = (1,) # default only one datapoint is requested
        return (_input_shape, argument_collection)

    def _find_all_batches(
        self: "DataSift",
        nH: Union[int, float, List, np.ndarray],
        temperature: Union[int, float, List, np.ndarray],
        metallicity: Union[int, float, List, np.ndarray],
        redshift: Union[int, float, List, np.ndarray],
    ) -> Set[int]:
        """
        Determine if multiple datapoints are requested.

        Parameters
        ----------
        nH : float
            Hydrogen number density (all hydrogen both neutral and ionized.
        temperature : float, array, list
            Plasma temperature.
        metallicity : float, array, list
            Plasma metallicity with respect to solar.
        redshift : float, array, list
            Cosmological redshift of the universe.

        Returns
        -------
        batch_ids : set
            Set of all the unique batch ids from the entire requested data.

        """
        _array_argument, _dummy_array = self._process_arguments_flags(nH, temperature, metallicity, redshift)
        _input_shape, argument_collection = self._prepare_arguments(nH, temperature, metallicity, redshift, _array_argument, _dummy_array)
        
        if np.sum(_dummy_array) == 4 or np.sum(_array_argument) == 0:
            _argument = [argument[0] for argument in argument_collection]
            return self._find_all_batches_single(*_argument)
        
        _all_batches_all_data = set()
        for indx in range(np.product(_input_shape)):
            _argument = []
            for arg_pos, _dummy in enumerate(_dummy_array):
                if _dummy or not(_array_argument[arg_pos]):
                    _argument.append(argument_collection[arg_pos][0])
                else:
                    _argument.append(argument_collection[arg_pos][indx])
            # print("Debug: ", _argument)
            _all_batches_all_data = _all_batches_all_data.union(self._find_all_batches_single(*_argument))
        if _all_batches_all_data == set():
            raise ValueError(f"Problem identifying batches! Code Aborted!")
        # print("Debug: ", _all_batches_all_data)
        return _all_batches_all_data

    def _transform_edges(self: "DataSift", i: int, j: int, k: int, m: int) -> Tuple[int, int, int, int]:
        # Detect the edge cases
        if i == self.nH_data.shape[0]:
            if _warn:
                print("Problem: nH")
            i = i - 1
        if i == -1:
            if _warn:
                print("Problem: nH")
            i = i + 1
        if j == self.T_data.shape[0]:
            if _warn:
                print("Problem: T")
            j = j - 1
        if j == -1:
            if _warn:
                print("Problem: T")
            j = j + 1
        if k == self.Z_data.shape[0]:
            if _warn:
                print("Problem: met")
            k = k - 1
        if k == -1:
            if _warn:
                print("Problem: met")
            k = k + 1
        if m == self.red_data.shape[0]:
            if _warn:
                print("Problem: red")
            m = m - 1
        if m == -1:
            if _warn:
                print("Problem: red")
            m = m + 1
        return (i, j, k, m)

    def _find_all_batches_single(
        self: "DataSift",
        nH: Union[int, float],
        temperature: Union[int, float],
        metallicity: Union[int, float],
        redshift: Union[int, float],
    ) -> Set[int]:
        """
        Find the batches needed from the data files.

        Parameters
        ----------
        nH : float
            Hydrogen number density (all hydrogen both neutral and ionized.
        temperature : float
            Plasma temperature.
        metallicity : float
            Plasma metallicity with respect to solar.
        redshift : float
            Cosmological redshift of the universe.

        Returns
        -------
        batch_ids : set
            Set of all the unique batch ids.

        """
        i_vals, j_vals, k_vals, m_vals = None, None, None, None
        if np.sum(nH == self.nH_data) == 1:
            eq = np.where(nH == self.nH_data)[0][0]
            i_vals = [eq - 1, eq, eq + 1]
        else:
            i_vals = [
                np.sum(nH > self.nH_data) - 1,
                np.sum(nH > self.nH_data),
            ]

        if np.sum(temperature == self.T_data) == 1:
            eq = np.where(temperature == self.T_data)[0][0]
            j_vals = [eq - 1, eq, eq + 1]
        else:
            j_vals = [
                np.sum(temperature > self.T_data) - 1,
                np.sum(temperature > self.T_data),
            ]

        if np.sum(metallicity == self.Z_data) == 1:
            eq = np.where(metallicity == self.Z_data)[0][0]
            k_vals = [eq - 1, eq, eq + 1]
        else:
            k_vals = [
                np.sum(metallicity > self.Z_data) - 1,
                np.sum(metallicity > self.Z_data),
            ]

        if np.sum(redshift == self.red_data) == 1:
            eq = np.where(redshift == self.red_data)[0][0]
            m_vals = [eq - 1, eq, eq + 1]
        else:
            m_vals = [
                np.sum(redshift > self.red_data) - 1,
                np.sum(redshift > self.red_data),
            ]

        self.i_vals = i_vals
        self.j_vals = j_vals
        self.k_vals = k_vals
        self.m_vals = m_vals

        batch_ids = set()
        # identify unique batches
        for i, j, k, m in product(i_vals, j_vals, k_vals, m_vals):
            i, j, k, m = self._transform_edges(i, j, k, m)
            batch_id = self._identify_batch(i, j, k, m)
            batch_ids.add(batch_id)
        # batch_ids = set(batch_ids)
        # print("Batches involved: ", batch_ids)
        # later use this logic to fetch batches from cloud if not present

        self._fetch_data(batch_ids)

        return batch_ids

    @abstractmethod
    def _fetch_data(self: "DataSift", batch_ids: Set[int]) -> None:
        pass

    @abstractmethod
    def _get_file_path(self: "DataSift", batch_id: int) -> Path:
        pass

    def _interpolate(
        self: "DataSift",
        nH: Union[int, float],
        temperature: Union[int, float],
        metallicity: Union[int, float],
        redshift: Union[int, float],
        mode: str,
        interp_data: str,
        interp_value_shape: Union[Tuple[int], List[int]],
        scaling_func: Callable = lambda x: x,
        cut: Tuple[Optional[Union[float, int]], Optional[Union[float, int]]] = (
            None,
            None,
        ),
    ) -> np.ndarray:
        """
        Interpolate from pre-computed Cloudy table.

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
        interpField : str
            ionization condition
            either CIE (collisional) or PIE (photo).
            The default is 'PIE'.
        scaling_func : callable function, optional
            function space in which intrepolation is
            carried out.
            The default is linear. log10 is another popular choice.
        cut : upper and lower bound on  data
            The default is (None, None)

        Returns
        -------
        interp_value : np.ndarray
            The interpolated result.
        """

        _array_argument, _dummy_array = self._process_arguments_flags(nH, temperature, metallicity, redshift)
        
        if mode != "PIE" and mode != "CIE":
            print("Problem! Invalid mode: %s." % mode)
            return None

        batch_ids = self._find_all_batches(nH, temperature, metallicity, redshift)
        self._check_and_download(specific_file_ids=batch_ids)
        i_vals = self.i_vals
        j_vals = self.j_vals
        k_vals = self.k_vals
        m_vals = self.m_vals

        data = []
        for batch_id in batch_ids:
            filename = self._get_file_path(batch_id)
            hdf = h5py.File(filename, "r")
            data.append({"batch_id": batch_id, "file": hdf})

        """
        The trick is to take the floor value for interpolation only if it is the
        most frequent value in all the nearest neighbor. If not, then simply ignore
        the contribution of the floor value in interpolation.
        """
        epsilon = 1e-15
        _all_values = []
        _all_weights = []
        for i, j, k, m in product(i_vals, j_vals, k_vals, m_vals):
            i, j, k, m = self._transform_edges(i, j, k, m)
            # nearest neighbour interpolation
            d_i = np.abs(scaling_func(self.nH_data[i]) - scaling_func(float(nH)))
            d_j = np.abs(scaling_func(self.T_data[j]) - scaling_func(float(temperature)))
            d_k = np.abs(scaling_func(self.Z_data[k]) - scaling_func(float(metallicity)))
            d_m = np.abs(scaling_func(self.red_data[m]) - scaling_func(float(redshift)))
            distL2 = np.sqrt(d_i**2 + d_j**2 + d_k**2 + d_m**2)
            if distL2 <= 0.0:
                distL2 = epsilon
            _all_weights.append(1 / distL2)

            batch_id = self._identify_batch(i, j, k, m)

            for id_data in data:
                if id_data["batch_id"] == batch_id:
                    hdf = id_data["file"]
                    local_pos = self._get_counter(i, j, k, m) % self.batch_size - 1
            try:
                value = np.array(hdf[interp_data])[local_pos, :]
            except UnboundLocalError as e:
                print("Error: HDF5 files not properly loaded/initialized! Code Aborted!")
                sys.exit(1)

            if cut[0] is not None:
                value = np.piecewise(value, [value <= cut[0]], [cut[0], lambda x: x])
            if cut[1] is not None:
                value = np.piecewise(value, [value >= cut[1]], [cut[1], lambda x: x])
            _all_values.append(value)

        all_values = np.array(_all_values)
        all_weights = np.array(_all_weights)
        # Filter the outliers (deviation from mean across column is large)
        all_values[(np.abs(all_values - np.mean(all_values, axis=0)) > 2.0 * np.std(all_values, axis=0))] = 0.0

        # _median_value = np.median(_all_values, axis=0)
        interp_value = all_weights.T @ all_values / np.sum(all_weights)
        # if (len(interp_value.shape)==2):
        #     interp_value = interp_value[0]

        for id_data in data:
            id_data["file"].close()
        return interp_value
