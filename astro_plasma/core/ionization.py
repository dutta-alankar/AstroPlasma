"""Created on Wed Nov 30 12:06:18 2022.

@author: alankar
"""

# Built-in imports
from pathlib import Path
from typing import Optional, Union, Set

# Third party imports
import h5py
import numpy as np

# Local package imports
from .constants import mH, mp, X_solar, Y_solar, Z_solar, Xp, Yp, Zp
from .datasift import DataSift
from .utils import fetch, LOCAL_DATA_PATH, AtmElement, parse_atomic_ion_no
from .data_dir import set_base_dir

DEFAULT_BASE_DIR = LOCAL_DATA_PATH / "ionization"
FILE_NAME_TEMPLATE = "ionization.b_{:06d}.h5"
BASE_URL_TEMPLATE = "ionization/download/{:d}/"
DOWNLOAD_IN_INIT = [
    (BASE_URL_TEMPLATE.format(0), Path(FILE_NAME_TEMPLATE.format(0))),
]


class Ionization(DataSift):
    def __init__(
        self: "Ionization",
        base_dir: Optional[Path] = None,
    ):
        """
        Prepares the location to read data for generating ionization calculations.

        Returns
        -------
        None.

        """
        self.base_url_template = BASE_URL_TEMPLATE
        self.file_name_template = FILE_NAME_TEMPLATE
        self.base_dir = base_dir

    @property
    def base_dir(self):
        return self._base_dir

    @base_dir.setter
    def base_dir(
        self,
        base_dir: Optional[Path] = None,
    ):
        self._base_dir = set_base_dir(DEFAULT_BASE_DIR, base_dir)

        fetch(urls=DOWNLOAD_IN_INIT, base_dir=self._base_dir)
        data = h5py.File(self._base_dir / DOWNLOAD_IN_INIT[0][1], "r")
        super().__init__(data)
        data.close()

    def _fetch_data(self: "Ionization", batch_ids: Set[int]) -> None:
        urls = []
        for batch_id in batch_ids:
            urls.append(
                (
                    self.base_url_template.format(batch_id),
                    Path(self.file_name_template.format(batch_id)),
                )
            )

        fetch(urls=urls, base_dir=self.base_dir)

    def _get_file_path(self: "Ionization", batch_id: int) -> Path:
        return self.base_dir / self.file_name_template.format(batch_id)

    def _interpolate_ion_frac_all(
        self: "Ionization",
        nH: Union[int, float] = 1.2e-4,
        temperature: Union[int, float] = 2.7e6,
        metallicity: Union[int, float] = 0.5,
        redshift: Union[int, float] = 0.2,
        mode: str = "PIE",
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
        float
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

        fracIon = super()._interpolate(
            nH,
            temperature,
            metallicity,
            redshift,
            mode,
            f"output/fracIon/{mode}",
            (ion_count,),
            lambda x: x,
            (None, None),
        )
        return fracIon

    def interpolate_ion_frac(
        self: "Ionization",
        nH: Union[int, float] = 1.2e-4,
        temperature: Union[int, float] = 2.7e6,
        metallicity: Union[int, float] = 0.5,
        redshift: Union[int, float] = 0.2,
        element: Union[int, AtmElement, str] = AtmElement.Helium,
        ion: Union[int, None] = 1,
        mode: str = "PIE",
    ) -> float:
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
        element : int, optional
            Atomic number of the element. The default is 2.
        ion : int, optional
            Ionization species of the element.
            Must between 1 and element+1.
            The default is 1.
            1:neutral, 2:+, 3:++, ...
        mode : str, optional
            ionization condition
            either CIE (collisional) or PIE (photo).
            The default is 'PIE'.

        Returns
        -------
        float
            ionization fraction
            of the requested ion species
            of the requested element.
            The value is in log10.

        """

        element, ion = parse_atomic_ion_no(element, ion)

        # element = 1: H, 2: He, 3: Li, ... 30: Zn
        # ion = 1 : neutral, 2: +, 3: ++ .... (element+1): (++++... element times)
        if ion < 0 or ion > element + 1:
            raise ValueError(f"Problem! Invalid ion {ion} for element {element}.")
        if element < 0 or element > 30:
            raise ValueError(f"Problem! Invalid element {element}.")

        # Select only the ions for the requested element
        slice_start = int((element - 1) * (element + 2) / 2)
        slice_stop = int(element * (element + 3) / 2)
        fracIon = self._interpolate_ion_frac_all(nH, temperature, metallicity, redshift, mode)[slice_start:slice_stop]

        # Array starts from 0 but ion from 1
        return fracIon[ion - 1]  # This is in log10

    def interpolate_num_dens(
        self: "Ionization",
        nH: Union[int, float] = 1.2e-4,
        temperature: Union[int, float] = 2.7e6,
        metallicity: Union[int, float] = 0.5,
        redshift: Union[int, float] = 0.2,
        mode: str = "PIE",
        part_type: Optional[str] = None,
        element: Optional[Union[int, AtmElement, str]] = None,
        ion: Optional[int] = None,
    ) -> float:
        """
        Interpolates the number density of different species
        or the total number density of the plasma
        from pre-computed Cloudy models of ion networks.

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
        part_type : str, optional
            The type of the particle requested.
            Currently available options: all, electron, ion
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
            number density of the requested species.

        """
        abn_file = LOCAL_DATA_PATH / "solar_GASS10.abn"
        with abn_file.open() as file:
            abn = np.array([float(element.split()[-1]) for element in file.readlines()[2:32]])  # Till Zinc
        # element = 1: H, 2: He, 3: Li, ... 30: Zn
        # ion = 1 : neutral, 2: +, 3: ++ .... (element+1): (++++... element times)
        fracIon = 10.0 ** self._interpolate_ion_frac_all(nH, temperature, metallicity, redshift, mode)

        if part_type == "all" and element is None:
            ndens = 0
            ion_count = 0
            for element in range(30):
                for ion in range(element + 2):
                    if element + 1 == 1:  # H
                        ndens += (ion + 1) * (Xp(metallicity) / X_solar) * abn[element] * fracIon[ion_count] * nH
                    elif element + 1 == 2:  # He
                        ndens += (ion + 1) * (Yp(metallicity) / Y_solar) * abn[element] * fracIon[ion_count] * nH
                    else:
                        ndens += (ion + 1) * (Zp(metallicity) / Z_solar) * abn[element] * fracIon[ion_count] * nH
                    ion_count += 1
            return ndens

        elif part_type == "electron" and element is None:
            ne = 0
            ion_count = 0
            for element in range(30):
                for ion in range(element + 2):
                    if element + 1 == 1:  # H
                        ne += ion * (Xp(metallicity) / X_solar) * nH * abn[element] * fracIon[ion_count]
                    elif element + 1 == 2:  # He
                        ne += ion * (Yp(metallicity) / Y_solar) * nH * abn[element] * fracIon[ion_count]
                    else:
                        ne += ion * (Zp(metallicity) / Z_solar) * nH * abn[element] * fracIon[ion_count]
                    ion_count += 1
            return ne

        elif part_type == "ion" and element is None:
            nion = 0
            ion_count = 0
            for element in range(30):
                for ion in range(1, element + 2):
                    if element + 1 == 1:  # H
                        nion += (Xp(metallicity) / X_solar) * nH * abn[element] * fracIon[ion_count]
                    elif element + 1 == 2:  # He
                        nion += (Yp(metallicity) / Y_solar) * nH * abn[element] * fracIon[ion_count]
                    else:
                        nion += ion * (Zp(metallicity) / Z_solar) * nH * abn[element] * fracIon[ion_count]
                    ion_count += 1
            return nion

        elif element is None and part_type is None:
            raise ValueError(f"Invalid part_type: {part_type} and invalid element: {element}.")
        elif element is not None and part_type is not None:
            raise ValueError(f"Both part_type: {part_type} and element: {element} cannot be specified simultaneously.")
        else:
            fIon = 10.0 ** self.interpolate_ion_frac(nH, temperature, metallicity, redshift, element, ion, mode)
            _element, _ion = parse_atomic_ion_no(element, ion)
            abundance = abn[_element - 1]
            nIon = abundance * (Zp(metallicity) / Z_solar) * fIon * nH
            return nIon

    def interpolate_mu(
        self: "Ionization",
        nH: Union[int, float] = 1.2e-4,
        temperature: Union[int, float] = 2.7e6,
        metallicity: Union[int, float] = 0.5,
        redshift: Union[int, float] = 0.2,
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
        part_type : str, optional
            The type of the particle requested.
            Currently available options: all, electron, ion
            The default is 'all'.

        Returns
        -------
        float
            mean particle mass of the plasma.

        """
        ndens = self.interpolate_num_dens(nH, temperature, metallicity, redshift, mode, part_type)
        return (nH / ndens) * (mH / mp) / float(Xp(metallicity))
