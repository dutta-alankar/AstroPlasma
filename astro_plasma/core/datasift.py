# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 21:30:23 2023

@author: alankar
"""

from abc import ABC, abstractmethod
from itertools import product
import math
from pathlib import Path
from typing import Protocol, Callable, Optional, Union, Tuple, List, Set
import h5py
import numpy as _numpy  # always CPU numpy — used for small lookup tables in __init__
from .compat import np
from .utils import should_check_or_download_data

_warn = False


class inherited_from_DataSift(Protocol):
    # This must be compulsorily implemented by any class inheriting from DataSift
    _check_and_download: Callable


class DataSift(ABC):
    def __init__(
        self: "DataSift",
        child_obj: "inherited_from_DataSift",
        data: h5py.File,
    ) -> None:
        """
        Prepares the location to read data for interpolation.

        Returns
        -------
        None.

        """
        # Use plain NumPy for these small parameter lookup arrays.  They are
        # loaded once at __init__ time (before any MPI rank sets its CuPy device)
        # and are only used for scalar index searches — not GPU vectorisation.
        # Storing them as CuPy arrays would pin them to GPU 0 and trigger
        # cross-device peer-access warnings on every other rank.
        self.nH_data = _numpy.asarray(data["params/nH"][()])
        self.T_data = _numpy.asarray(data["params/temperature"][()])
        self.Z_data = _numpy.asarray(data["params/metallicity"][()])
        self.red_data = _numpy.asarray(data["params/redshift"][()])

        self.batch_size = int(_numpy.prod(_numpy.asarray(data["header/batch_dim"][()])))
        self.total_size = int(_numpy.prod(_numpy.asarray(data["header/total_size"][()])))
        self._check_and_download = child_obj._check_and_download

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
    ) -> Tuple[List[bool], List[bool]]:
        """
        Determine if multiple datapoints are requested. Flags if
        some of the arguments are arrays. Also flags if any array
        is of size 1 which is a dummy array.

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
        # _argument_type = ["nH", "temperature", "metallicity", "redshift"]
        _array_argument = [True, True, True, True]  # array to flag which arguments are arrays
        _array_argument[0] = isinstance(nH, list) or (isinstance(nH, np.ndarray) and np.array(nH).ndim > 0)
        _array_argument[1] = isinstance(temperature, list) or (isinstance(temperature, np.ndarray) and np.array(temperature).ndim > 0)
        _array_argument[2] = isinstance(metallicity, list) or (isinstance(metallicity, np.ndarray) and np.array(metallicity).ndim > 0)
        _array_argument[3] = isinstance(redshift, list) or (isinstance(redshift, np.ndarray) and np.array(redshift).ndim > 0)

        _dummy_array = [False, False, False, False]  # array to flag which arguments are length 1 array
        if _array_argument[0]:
            _dummy_array[0] = np.array(nH).shape[0] == 1
        if _array_argument[1]:
            _dummy_array[1] = np.array(temperature).shape[0] == 1
        if _array_argument[2]:
            _dummy_array[2] = np.array(metallicity).shape[0] == 1
        if _array_argument[3]:
            _dummy_array[3] = np.array(redshift).shape[0] == 1

        return (_array_argument, _dummy_array)

    def _prepare_arguments(
        self: "DataSift",
        nH: Union[int, float, List, np.ndarray],
        temperature: Union[int, float, List, np.ndarray],
        metallicity: Union[int, float, List, np.ndarray],
        redshift: Union[int, float, List, np.ndarray],
        _array_argument: List[bool],
        _dummy_array: List[bool],
    ) -> Tuple[Optional[Tuple[int]], List[np.ndarray]]:
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
        _input_shape: Optional[Tuple[int]] = None
        argument_collection = [np.array(nH), np.array(temperature), np.array(metallicity), np.array(redshift)]
        for indx, _if_this_is_arr in enumerate(_array_argument):
            if not (_if_this_is_arr):
                argument_collection[indx] = np.array(
                    [
                        argument_collection[indx],
                    ]
                )
            else:
                if _input_shape is None:
                    _input_shape = argument_collection[indx].shape
                else:
                    if _input_shape != argument_collection[indx].shape:
                        print("Error: ", argument_collection[indx].shape, _input_shape)
                        print("Argument: ", argument_collection[indx])
                        raise ValueError("Check needed from user: Invalid input arguments which are not in compliance with each other! Code Aborted!")
            argument_collection[indx] = argument_collection[indx].flatten()
        if sum(_dummy_array) == 4 or sum(_array_argument) == 0:
            _input_shape = (1,)  # default only one datapoint is requested
        if _input_shape is None:
            raise ValueError("Check needed from user: Invalid input arguments which are not in compliance with each other! Code Aborted!")
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

        _array_argument, _dummy_array = self._array_argument, self._dummy_array
        _input_shape, argument_collection = self._input_shape, self.argument_collection

        if sum(_dummy_array) == 4 or sum(_array_argument) == 0:
            _argument = [argument[0] for argument in argument_collection]
            return self._find_all_batches_single(*_argument)

        _all_batches_all_data: Set[int] = set()
        for indx in range(math.prod(_input_shape)):
            _argument = []
            for arg_pos, _dummy in enumerate(_dummy_array):
                if _dummy or not (_array_argument[arg_pos]):
                    _argument.append(argument_collection[arg_pos][0])
                else:
                    _argument.append(argument_collection[arg_pos][indx])
            nH_val, temp_val, met_val, red_val = _argument
            _all_batches_all_data = _all_batches_all_data.union(self._find_all_batches_single(nH_val, temp_val, met_val, red_val))
        if _all_batches_all_data == set():
            raise ValueError("Problem identifying batches! Code Aborted!")
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

    def _identify_pos_in_each_dim(
        self: "DataSift",
        nH: Union[int, float],
        temperature: Union[int, float],
        metallicity: Union[int, float],
        redshift: Union[int, float],
    ) -> Tuple[List[int], List[int], List[int], List[int]]:
        # This function receives scalar values extracted element-by-element from
        # the argument arrays.  When RUN_ON_CUDA=1 those scalars are CuPy 0-d
        # arrays and self.*_data are plain NumPy arrays (by design in __init__).
        # CuPy refuses mixed-type comparisons (cupy_0d == numpy_array), so we
        # force everything to plain Python floats before the comparisons.
        nH = float(nH)
        temperature = float(temperature)
        metallicity = float(metallicity)
        redshift = float(redshift)
        # positions in each data just around the requested value for any variable
        # NOTE: self.*_data are plain NumPy arrays and the scalars are Python
        # floats, so all comparisons/reductions here must use _numpy (plain
        # NumPy) rather than np (which equals CuPy when RUN_ON_CUDA=1).
        # CuPy's where/sum routines explicitly reject non-CuPy array inputs.
        i_vals, j_vals, k_vals, m_vals = None, None, None, None
        if int(_numpy.sum(nH == self.nH_data)) == 1:
            eq = int(_numpy.where(nH == self.nH_data)[0][0])
            i_vals = [eq - 1, eq, eq + 1]
        else:
            _s = int(_numpy.sum(nH > self.nH_data))
            i_vals = [_s - 1, _s]

        if int(_numpy.sum(temperature == self.T_data)) == 1:
            eq = int(_numpy.where(temperature == self.T_data)[0][0])
            j_vals = [eq - 1, eq, eq + 1]
        else:
            _s = int(_numpy.sum(temperature > self.T_data))
            j_vals = [_s - 1, _s]

        if int(_numpy.sum(metallicity == self.Z_data)) == 1:
            eq = int(_numpy.where(metallicity == self.Z_data)[0][0])
            k_vals = [eq - 1, eq, eq + 1]
        else:
            _s = int(_numpy.sum(metallicity > self.Z_data))
            k_vals = [_s - 1, _s]

        if int(_numpy.sum(redshift == self.red_data)) == 1:
            eq = int(_numpy.where(redshift == self.red_data)[0][0])
            m_vals = [eq - 1, eq, eq + 1]
        else:
            _s = int(_numpy.sum(redshift > self.red_data))
            m_vals = [_s - 1, _s]

        return (i_vals, j_vals, k_vals, m_vals)

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
        i_vals, j_vals, k_vals, m_vals = self._identify_pos_in_each_dim(nH, temperature, metallicity, redshift)

        batch_ids = set()
        # identify unique batches
        for i, j, k, m in product(i_vals, j_vals, k_vals, m_vals):
            i, j, k, m = self._transform_edges(i, j, k, m)
            batch_id = self._identify_batch(i, j, k, m)
            batch_ids.add(batch_id)

        # print("Batches involved: ", batch_ids)

        # self._fetch_data(batch_ids)

        return batch_ids

    """
    @abstractmethod
    def _fetch_data(self: "DataSift", batch_ids: Set[int]) -> None:
        pass
    """

    @abstractmethod
    def _get_file_path(self: "DataSift", batch_id: int) -> Path:
        pass

    def _interpolate(
        self: "DataSift",
        nH: Union[int, float, list, np.ndarray],
        temperature: Union[int, float, list, np.ndarray],
        metallicity: Union[int, float, list, np.ndarray],
        redshift: Union[int, float, list, np.ndarray],
        mode: str,
        interp_data: str,
        interp_value_shape: Union[Tuple[int], List[int]],
        scaling_func: Callable = lambda x: x,
        cut: Tuple[Optional[Union[float, int]], Optional[Union[float, int]]] = (
            None,
            None,
        ),
    ) -> Tuple[np.ndarray, bool]:
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
        interp_data : str
            data location within HDF5 file
        scaling_func : callable function, optional
            function space in which intrepolation is
            carried out.
            The default is linear. log10 is another popular choice.
        cut : upper and lower bound on  data
            The default is (None, None)

        Returns
        -------
        (interp_value, if_multiple_output) : (np.ndarray, bool)
            The interpolated result.
        """

        self._array_argument, self._dummy_array = self._process_arguments_flags(nH, temperature, metallicity, redshift)
        self._input_shape, self.argument_collection = self._prepare_arguments(nH, temperature, metallicity, redshift, self._array_argument, self._dummy_array)

        _array_argument = self._array_argument
        _dummy_array = self._dummy_array
        _input_shape = self._input_shape
        argument_collection = self.argument_collection

        if not (mode == "PIE" or mode == "CIE"):
            raise ValueError("Problem! Invalid mode: %s." % mode)

        batch_ids = self._find_all_batches(nH, temperature, metallicity, redshift)
        # Download files on demand if absent locally
        if should_check_or_download_data():
            self._check_and_download(specific_file_ids=batch_ids)

        # ── Grid dimensions (plain CPU numpy) ────────────────────────────────
        N_nH = self.nH_data.shape[0]
        N_T = self.T_data.shape[0]
        N_Z = self.Z_data.shape[0]
        N_red = self.red_data.shape[0]

        # ── Determine N_ions from a sample batch file ─────────────────────────
        _sample_id = next(iter(sorted(batch_ids)))
        with h5py.File(self._get_file_path(_sample_id), "r") as _h:
            N_ions = _h[interp_data].shape[1]

        # ── Load only the needed HDF5 batches into a compact CPU array ────────
        #
        # self.total_size = N_nH * N_T * N_Z * N_red can be ~1M rows × 465 ions
        # = 3.9 GB — far too large to allocate in full.  We only ever need the
        # few batches that cover the corners of the requested cells.
        #
        # Strategy:
        #   1. Build a compact table_cpu containing only rows from batch_ids.
        #   2. Build a remap_cpu[global_counter] → compact_row index array
        #      (size = total_size; for ionization: 1M × int64 = 8 MB — fine).
        #   3. Use remap[flat_idx] to index into the compact table on GPU.
        #
        # Original per-cell access:  local_pos = counter % batch_size - 1
        #   counter % batch_size == k  →  local_pos = k - 1  (raw row k-1)
        #   k == 0                     →  local_pos = -1      (raw row bs-1)
        # Equivalently: compact_row = roll(raw, +1) so compact[k] = raw[(k-1)%bs]
        #
        total_grid = N_nH * N_T * N_Z * N_red  # == self.total_size
        remap_cpu = _numpy.full(total_grid, -1, dtype=_numpy.int64)
        compact_rows = 0
        for batch_id in sorted(batch_ids):
            start = batch_id * self.batch_size
            bs = min(self.batch_size, total_grid - start)
            if bs <= 0:
                continue
            remap_cpu[start : start + bs] = _numpy.arange(compact_rows, compact_rows + bs, dtype=_numpy.int64)
            compact_rows += bs

        table_cpu = _numpy.zeros((compact_rows, N_ions), dtype=_numpy.float64)
        for batch_id in sorted(batch_ids):
            start = batch_id * self.batch_size
            bs = min(self.batch_size, total_grid - start)
            if bs <= 0:
                continue
            compact_start = int(remap_cpu[start])
            with h5py.File(self._get_file_path(batch_id), "r") as hdf:
                raw = _numpy.asarray(hdf[interp_data][:bs], dtype=_numpy.float64)
            table_cpu[compact_start : compact_start + bs] = _numpy.roll(raw, shift=1, axis=0)

        # Apply value bounds on CPU before GPU transfer
        if cut[0] is not None:
            _numpy.clip(table_cpu, a_min=cut[0], a_max=None, out=table_cpu)
        if cut[1] is not None:
            _numpy.clip(table_cpu, a_min=None, a_max=cut[1], out=table_cpu)

        # ── Transfer compact table + remap to GPU (no-op when RUN_ON_CUDA=0) ──
        remap = np.asarray(remap_cpu)  # (total_grid,) int64 index map
        table = np.asarray(table_cpu)  # (compact_rows, N_ions)
        nH_grid = np.asarray(self.nH_data)  # (N_nH,)
        T_grid = np.asarray(self.T_data)  # (N_T,)
        Z_grid = np.asarray(self.Z_data)  # (N_Z,)
        red_grid = np.asarray(self.red_data)  # (N_red,)

        # ── Build flat (N_cells,) input vectors on GPU ────────────────────────
        N_cells = math.prod(_input_shape)

        def _expand(coll, is_arr, is_dummy):
            # argument_collection entries are already flattened (N_cells,) arrays
            # when is_arr=True and is_dummy=False; otherwise length-1.
            if is_arr and not is_dummy:
                return coll
            return np.full((N_cells,), float(coll[0]))

        nH_v = _expand(argument_collection[0], _array_argument[0], _dummy_array[0])
        T_v = _expand(argument_collection[1], _array_argument[1], _dummy_array[1])
        Z_v = _expand(argument_collection[2], _array_argument[2], _dummy_array[2])
        red_v = _expand(argument_collection[3], _array_argument[3], _dummy_array[3])

        # ── Apply scaling function to grids and query values ──────────────────
        sc_nH_g = scaling_func(nH_grid)  # (N_nH,)
        sc_T_g = scaling_func(T_grid)  # (N_T,)
        sc_Z_g = scaling_func(Z_grid)  # (N_Z,)
        sc_red_g = scaling_func(red_grid)  # (N_red,)

        sc_nH_v = scaling_func(nH_v)  # (N_cells,)
        sc_T_v = scaling_func(T_v)
        sc_Z_v = scaling_func(Z_v)
        sc_red_v = scaling_func(red_v)

        # ── Floor-index via searchsorted (vectorised over all N_cells) ─────────
        # searchsorted(a, v, side='right') - 1  →  last grid index with a[i] <= v
        i_f = np.searchsorted(sc_nH_g, sc_nH_v, side="right") - 1
        j_f = np.searchsorted(sc_T_g, sc_T_v, side="right") - 1
        k_f = np.searchsorted(sc_Z_g, sc_Z_v, side="right") - 1
        m_f = np.searchsorted(sc_red_g, sc_red_v, side="right") - 1

        i_f = np.clip(i_f, 0, N_nH - 2).astype(np.int64)
        j_f = np.clip(j_f, 0, N_T - 2).astype(np.int64)
        k_f = np.clip(k_f, 0, N_Z - 2).astype(np.int64)
        m_f = np.clip(m_f, 0, N_red - 2).astype(np.int64)

        # ── Vectorised IDW over 2^4 = 16 corners, all N_cells simultaneously ──
        stride_T = N_nH
        stride_Z = N_nH * N_T
        stride_red = N_nH * N_T * N_Z
        epsilon = 1e-15

        corner_vals_list = []  # each: (N_cells, N_ions)
        corner_weights_list = []  # each: (N_cells,)

        for di, dj, dk, dm in product(range(2), range(2), range(2), range(2)):
            ic = np.clip(i_f + di, 0, N_nH - 1)  # (N_cells,)
            jc = np.clip(j_f + dj, 0, N_T - 1)
            kc = np.clip(k_f + dk, 0, N_Z - 1)
            mc = np.clip(m_f + dm, 0, N_red - 1)

            # Flat table index for each cell's corner → remap to compact table
            flat_idx = mc * stride_red + kc * stride_Z + jc * stride_T + ic  # (N_cells,)
            corner_vals_list.append(table[remap[flat_idx]])  # GPU gather → (N_cells, N_ions)

            # L2 distance in scaled parameter space
            d_i = np.abs(sc_nH_g[ic] - sc_nH_v)  # (N_cells,)
            d_j = np.abs(sc_T_g[jc] - sc_T_v)
            d_k = np.abs(sc_Z_g[kc] - sc_Z_v)
            d_m = np.abs(sc_red_g[mc] - sc_red_v)

            dist = np.sqrt(d_i**2 + d_j**2 + d_k**2 + d_m**2)
            dist = np.where(dist == 0.0, epsilon, dist)
            corner_weights_list.append(1.0 / dist)  # (N_cells,)

        all_values = np.stack(corner_vals_list, axis=0)  # (16, N_cells, N_ions)
        all_weights = np.stack(corner_weights_list, axis=0)  # (16, N_cells)

        # Outlier filter: zero out corners whose value deviates > 2σ from mean
        mean_v = np.mean(all_values, axis=0)  # (N_cells, N_ions)
        std_v = np.std(all_values, axis=0)
        outlier = np.abs(all_values - mean_v[None]) > 2.0 * std_v[None]  # (16, N_cells, N_ions)
        all_values = np.where(outlier, 0.0, all_values)

        # Weighted sum over the 16 corners
        numer = np.sum(all_weights[:, :, None] * all_values, axis=0)  # (N_cells, N_ions)
        denom = np.sum(all_weights, axis=0)  # (N_cells,)
        result = numer / denom[:, None]  # (N_cells, N_ions)

        # ── Return ────────────────────────────────────────────────────────────
        if sum(_dummy_array) == 4 or sum(_array_argument) == 0:
            return (result[0], False)
        else:
            _tmp = result.reshape((*_input_shape, N_ions))
            return (_tmp, True)

    def _determine_multiple(
        self: "DataSift",
        nH: Union[int, float, list, np.ndarray],
        temperature: Union[int, float, list, np.ndarray],
        metallicity: Union[int, float, list, np.ndarray],
        redshift: Union[int, float, list, np.ndarray],
        mode: str,
    ) -> bool:
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
        interp_data : str
            data location within HDF5 file
        scaling_func : callable function, optional
            function space in which intrepolation is
            carried out.
            The default is linear. log10 is another popular choice.
        cut : upper and lower bound on  data
            The default is (None, None)

        Returns
        -------
        _multiple_output) : bool
            If multiple input is passed.
        """
        _is_multiple = (isinstance(nH, list) or isinstance(nH, np.ndarray)) and np.array(nH).flatten().shape[0] > 1
        _is_multiple = _is_multiple or (isinstance(temperature, list) or isinstance(temperature, np.ndarray)) and np.array(temperature).flatten().shape[0] > 1
        _is_multiple = _is_multiple or (isinstance(metallicity, list) or isinstance(metallicity, np.ndarray)) and np.array(metallicity).flatten().shape[0] > 1
        _is_multiple = _is_multiple or (isinstance(redshift, list) or isinstance(redshift, np.ndarray)) and np.array(redshift).flatten().shape[0] > 1

        return _is_multiple
