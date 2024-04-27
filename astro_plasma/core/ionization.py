"""Created on Wed Nov 30 12:06:18 2022.

@author: alankar
"""

# Built-in imports
from __future__ import annotations

from pathlib import Path

# Third party imports
import h5py
import numpy as np

# Local package imports
from .constants import mH, mp, X_solar, Y_solar, Z_solar, Xp, Yp, Zp
from .datasift import DataSift
from .download_database import initialize_data
from .utils import LOCAL_DATA_PATH, AtmElement, parse_atomic_number_and_ion

DEFAULT_BASE_DIR = LOCAL_DATA_PATH / "ionization"
FILE_NAME_TEMPLATE = "ionization.b_{:06d}.h5"


class Ionization(DataSift):
    def __init__(self, base_dir: Path = DEFAULT_BASE_DIR):
        """
        Prepares the location to read data for generating ionization calculations.

        Parameters
        ----------
        base_dir: Path
            Base directory to initialize the database directory.

        """
        self._base_dir = base_dir
        initialize_data("ionization")
        with h5py.File(self._base_dir / FILE_NAME_TEMPLATE.format(0)) as file:
            super().__init__(file)

    @property
    def base_dir(self):
        return self._base_dir

    def _get_file_path(self, batch_id: int) -> Path:
        return self.base_dir / FILE_NAME_TEMPLATE.format(batch_id)

    def _interpolate_ion_frac_all(
        self,
        nH: int | float = 1.2e-4,
        temperature: int | float = 2.7e6,
        metallicity: int | float = 0.5,
        redshift: int | float = 0.2,
        mode="PIE",
    ) -> np.ndarray:
        """
        Interpolates the ionization fraction of the plasma
        from pre-computed Cloudy models of ion networks.
        This fraction is with respect to the total number density
        of element to which the ion belongs to in the plasma.
        To get number fraction of the species, one must need to
        multiply with the abundance fraction of the element.
        Solar values are provided in a table in this repo.
        Other metallicities with respect to Solar can be simply scaled.
        This function calculates the ionization fraction of all species.

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

        Returns
        -------
        np.ndarray
            ionization fraction
            of the requested ion species
            of the requested element.
            The value is in log10.

        """
        ion_count = 0
        for i in range(30):  # Till Zn
            for j in range(i + 2):
                ion_count += 1

        # element = 1: H, 2: He, 3: Li, ... 30: Zn
        # ion = 1 : neutral, 2: +, 3: ++ .... (element+1): (++++... element times)

        frac_ion, self._is_multiple = self._interpolate(
            nH,
            temperature,
            metallicity,
            redshift,
            mode,
            f"output/fracIon/{mode}",
            lambda x: x,
            (None, None),
        )
        return frac_ion

    def interpolate_ion_frac(
        self,
        nH: int | float = 1.2e-4,
        temperature: int | float = 2.7e6,
        metallicity: int | float = 0.5,
        redshift: int | float = 0.2,
        element: int | AtmElement | str = AtmElement.Helium,
        ion: int | None = None,
        mode="PIE",
        all_ions=False,
    ) -> np.ndarray:
        """
        Interpolates the ionization fraction of the plasma
        from pre-computed Cloudy models of ion networks.
        This fraction is with respect to the total number density
        of element to which the ion belongs to in the plasma.
        To get number fraction of the species, one must need to
        multiply with the abundance fraction of the element.
        Solar values are provided in a table in this repo.
        Other metallicities with respect to Solar can be simply scaled.

        Parameters
        ----------
        nH : float, list, np.ndarray, optional
            Hydrogen number density
            (all hydrogen both neutral and ionized)
            The default is 1.2e-4.
        temperature : float, list, np.ndarray, optional
            Plasma temperature.
            The default is 2.7e6.
        metallicity : float, list, np.ndarray, optional
            Plasma metallicity with respect to solar.
            The default is 0.5.
        redshift : float, list, np.ndarray, optional
            Cosmological redshift of the universe.
            The default is 0.2.
        element : int, optional
            Atomic number of the element. The default is 2.
        ion : int, optional
            Ionization species of the element.
            Must between 1 and element+1.
            The default is None.
            1:neutral, 2:+, 3:++, ...
        mode : str, optional
            ionization condition
            either CIE (collisional) or PIE (photo).
            The default is 'PIE'.
        all_ions: bool, optional
            Output the ionization state of all ions
            The default is False

        Returns
        -------
        float
            ionization fraction
            of the requested ion species
            of the requested element.
            The value is in log10.

        """

        _is_multiple = self._determine_multiple(nH, temperature, metallicity, redshift)

        if all_ions:
            frac_ion = self._interpolate_ion_frac_all(nH, temperature, metallicity, redshift, mode)
            if _is_multiple:
                return frac_ion.flatten().reshape((*self._input_shape, frac_ion.shape[-1]))
            else:
                return frac_ion.flatten()

        _element, _ion = parse_atomic_number_and_ion(element, ion)

        # _element = 1: H, 2: He, 3: Li, ... 30: Zn
        # _ion = 1 : neutral, 2: +, 3: ++ .... (_element+1): (++++... _element times)
        if _ion is not None and _ion not in range(1, _element + 1):
            raise ValueError(f"Invalid ion {_ion} for element {_element}.")
        if _element not in range(1, AtmElement.Zinc.atomic_number + 1):
            raise ValueError(f"Invalid element {_element}.")

        # Select only the ions for the requested _element
        slice_start = int((_element - 1) * (_element + 2) / 2)
        slice_stop = int(_element * (_element + 3) / 2)

        if _is_multiple:
            frac_ion = self._interpolate_ion_frac_all(nH, temperature, metallicity, redshift, mode)
            slices = [slice(None)] * (frac_ion.ndim - 1)
            slices.append(slice(slice_start, slice_stop))  # slice to select only ions of one element
            frac_ion = frac_ion[tuple(slices)]
            if _ion is not None:
                # Array starts from 0 but ion from 1
                slices = slices[:-1]
                slices.append(slice(_ion - 1, _ion))  # slice to select a particular ion
                return frac_ion[tuple(slices)].flatten().reshape(self._input_shape)  # This is in log10
            else:
                return frac_ion.flatten().reshape((*self._input_shape, _element + 1))
        else:
            frac_ion = self._interpolate_ion_frac_all(nH, temperature, metallicity, redshift, mode).flatten()[slice_start:slice_stop]
            # Array starts from 0 but _ion from 1
            return frac_ion[_ion - 1] if _ion is not None else frac_ion  # This is in log10

    def interpolate_num_dens(
        self,
        nH: int | float = 1.2e-4,
        temperature: int | float = 2.7e6,
        metallicity: int | float = 0.5,
        redshift: int | float = 0.2,
        mode: str = "PIE",
        part_type: str = None,
        element: int | AtmElement | str = None,
        ion: int = None,
    ) -> float:
        """
        Interpolates the number density of different species
        or the total number density of the plasma
        from pre-computed Cloudy models of ion networks.

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
        part_type : str, optional
            The type of the particle requested.
            Currently available options: all, electron, ion, neutral
            The default is 'electron'.
        element : int, optional
            Atomic number of the element. The default is 2.
        ion : int, optional
            Ionization species of the element.
            Must between 1 and element+1.
            The default is 1.
            1:neutral, 2:+, 3:++, ...

        Returns
        -------
        float
            Number density of the requested species.

        """
        abn_file = LOCAL_DATA_PATH / "solar_GASS10.abn"
        with abn_file.open() as file:
            abn = np.array([float(element.split()[-1]) for element in file.readlines()[2:32]])  # Till Zinc
        # element = 1: H, 2: He, 3: Li, ... 30: Zn
        # ion = 1 : neutral, 2: +, 3: ++ .... (element+1): (++++... element times)

        _is_multiple = self._determine_multiple(nH, temperature, metallicity, redshift)
        frac_ion = np.power(10.0, self._interpolate_ion_frac_all(nH, temperature, metallicity, redshift, mode))

        slices = [slice(None)] * (frac_ion.ndim - 1)
        if part_type == "all" and element is None:
            ndens = 0
            ion_count = 0
            for element in range(30):
                for ion in range(element + 2):
                    slices.append(slice(ion_count, ion_count + 1))
                    _ion_fraction = frac_ion[tuple(slices)].flatten().reshape(self._input_shape) if _is_multiple else frac_ion.flatten()[ion_count]
                    slices = slices[:-1]
                    if element + 1 == 1:  # H
                        ndens += (ion + 1) * (Xp(metallicity) / X_solar) * abn[element] * _ion_fraction * nH
                    elif element + 1 == 2:  # He
                        ndens += (ion + 1) * (Yp(metallicity) / Y_solar) * abn[element] * _ion_fraction * nH
                    else:
                        ndens += (ion + 1) * (Zp(metallicity) / Z_solar) * abn[element] * _ion_fraction * nH
                    ion_count += 1
            return ndens

        elif part_type == "electron" and element is None:
            ne = 0
            ion_count = 0
            for element in range(30):
                for ion in range(element + 2):
                    slices.append(slice(ion_count, ion_count + 1))
                    _ion_fraction = frac_ion[tuple(slices)].flatten().reshape(self._input_shape) if _is_multiple else frac_ion.flatten()[ion_count]
                    slices = slices[:-1]
                    if element + 1 == 1:  # H
                        ne += ion * (Xp(metallicity) / X_solar) * nH * abn[element] * _ion_fraction
                    elif element + 1 == 2:  # He
                        ne += ion * (Yp(metallicity) / Y_solar) * nH * abn[element] * _ion_fraction
                    else:
                        ne += ion * (Zp(metallicity) / Z_solar) * nH * abn[element] * _ion_fraction
                    ion_count += 1
            return ne

        elif part_type == "neutral" and element is None:
            n_neutral = 0
            ion_count = 0
            for element in range(30):
                for ion in range(element + 2):
                    slices.append(slice(ion_count, ion_count + 1))
                    _ion_fraction = frac_ion[tuple(slices)].flatten().reshape(self._input_shape) if _is_multiple else frac_ion.flatten()[ion_count]
                    slices = slices[:-1]
                    if ion == 0:
                        if element + 1 == 1:  # H
                            n_neutral += (Xp(metallicity) / X_solar) * nH * abn[element] * _ion_fraction
                        elif element + 1 == 2:  # He
                            n_neutral += (Yp(metallicity) / Y_solar) * nH * abn[element] * _ion_fraction
                        else:
                            n_neutral += (Zp(metallicity) / Z_solar) * nH * abn[element] * _ion_fraction
                    ion_count += 1
            return n_neutral

        elif part_type == "ion" and element is None:
            nion = 0
            ion_count = 0
            for element in range(30):
                ion_count += 1  # neglects the neutral species
                for ion in range(1, element + 2):
                    slices.append(slice(ion_count, ion_count + 1))
                    _ion_fraction = frac_ion[tuple(slices)].flatten().reshape(self._input_shape) if _is_multiple else frac_ion.flatten()[ion_count]
                    slices = slices[:-1]
                    if element + 1 == 1:  # H
                        nion += (Xp(metallicity) / X_solar) * nH * abn[element] * _ion_fraction
                    elif element + 1 == 2:  # He
                        nion += (Yp(metallicity) / Y_solar) * nH * abn[element] * _ion_fraction
                    else:
                        nion += ion * (Zp(metallicity) / Z_solar) * nH * abn[element] * _ion_fraction
                    ion_count += 1
            return nion

        elif element is None and part_type is None:
            raise ValueError(f"Invalid part_type: {part_type} and invalid element: {element}.")
        elif element is not None and part_type is not None:
            raise ValueError(f"Both part_type: {part_type} and element: {element} cannot be specified simultaneously.")
        else:
            _element, _ion = parse_atomic_number_and_ion(element, ion)
            f_ion = np.power(10.0, self.interpolate_ion_frac(nH, temperature, metallicity, redshift, _element, _ion, mode))
            abundance = abn[_element - 1]
            n_ion = abundance * (Zp(metallicity) / Z_solar) * f_ion * nH
            return n_ion

    def interpolate_mu(
        self,
        nH: int | float = 1.2e-4,
        temperature: int | float = 2.7e6,
        metallicity: int | float = 0.5,
        redshift: int | float = 0.2,
        mode: str = "PIE",
        part_type: str = "all",
    ) -> float:
        """
        Interpolates the mean particle mass of the plasma
        from pre-computed Cloudy models of ion networks.
        This mean particle mass changes as the ionization
        of the palsma changes the number of free electrons
        in the plasma.
        Greater the ionization, hence the number of free electrons,
        lower the mean particle mass.

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
        part_type : str, optional
            The type of the particle requested.
            Currently available options: all, electron, ion, neutral
            The default is 'all'.

        Returns
        -------
        float
            mean particle mass of the plasma.

        """
        ndens = self.interpolate_num_dens(nH, temperature, metallicity, redshift, mode, part_type)
        return (nH / ndens) * (mH / mp) / float(Xp(metallicity))
