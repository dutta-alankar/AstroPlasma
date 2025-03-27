# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 20:28:15 2023

@author: alankar
"""
from __future__ import annotations

import hashlib
import json
import logging

# Built-in imports
import os
import re
import warnings
from enum import Enum
from pathlib import Path

# Third party imports

log = logging.getLogger(__name__)

if database_dir := os.getenv("ASTRO_PLASMA_DATA_DIR"):
    LOCAL_DATA_PATH = Path(database_dir)
    if not LOCAL_DATA_PATH.exists():
        LOCAL_DATA_PATH.mkdir(0o766, parents=True)
    elif not LOCAL_DATA_PATH.is_dir():
        raise ValueError("Database path is not a directory")
else:
    LOCAL_DATA_PATH = Path(__file__).parent.parent / "data"
ROMAN_WEIGHTS = {"I": 1, "V": 5, "X": 10}
# Using 4KB is standard and considered optimal
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1 << 12))
DB_BASE_URL = os.getenv("ASTRO_PLASMA_DB_BASE_URL", "https://indianinstituteofscience-my.sharepoint.com/:u:/g/personal/alankardutta_iisc_ac_in")
PARALLEL_JOBS = int(os.getenv("PARALLEL_DOWNLOAD_JOBS", 4))


class AtmElement(Enum):
    """
    Represents the atomic element class upto Zinc for this project.

    The first value in the tuple is the atomic element and second element corresponds to atomic number for the element.
    """

    Hydrogen = ("H", 1)
    Helium = ("He", 2)
    Lithium = ("Li", 3)
    Beryllium = ("Be", 4)
    Boron = ("B", 5)
    Carbon = ("C", 6)
    Nitrogen = ("N", 7)
    Oxygen = ("O", 8)
    Fluorine = ("F", 9)
    Neon = ("Ne", 10)
    Sodium = ("Na", 11)
    Magnesium = ("Mg", 12)
    Aluminum = ("Al", 13)
    Silicon = ("Si", 14)
    Phosphorus = ("P", 15)
    Sulfur = ("S", 16)
    Chlorine = ("Cl", 17)
    Argon = ("Ar", 18)
    Potassium = ("K", 19)
    Calcium = ("Ca", 20)
    Scandium = ("Sc", 21)
    Titanium = ("Ti", 22)
    Vanadium = ("V", 23)
    Chromium = ("Cr", 24)
    Manganese = ("Mn", 25)
    Iron = ("Fe", 26)
    Cobalt = ("Co", 27)
    Nickel = ("Ni", 28)
    Copper = ("Cu", 29)
    Zinc = ("Zn", 30)

    @staticmethod
    def parse(predicate: str | int | AtmElement) -> "AtmElement":
        if type(predicate) is AtmElement:
            return predicate

        # TODO: Use function overloads in this case for better documentation
        # When the type of the predicate is int, then it means user has passed the atomic number of the element
        value_index = int(type(predicate) is int)  # noqa: E721
        error_label = "atomic number" if value_index == 1 else "symbol"

        for element in AtmElement:
            if element.value[value_index] == predicate:
                return element

        raise ValueError(f"Invalid {error_label} {predicate}.")

    @property
    def atomic_number(self):
        return self.value[1]

    @property
    def symbol(self):
        return self.value[0]

    def to_atm_no(self) -> int:
        warnings.warn("Use atomic_number property instead.", DeprecationWarning, stacklevel=2)
        return self.atomic_number


def roman_to_int(predicate: str) -> int:
    """
    Take the roman digits and return the decimal number

    Parameters
    ----------
    predicate: int
        Roman number string

    Returns
    -------
    int:
        Integer representing decimal for that roman number
    """

    result = 0
    prev_val = 0
    for tok in predicate[::-1]:
        val = ROMAN_WEIGHTS[tok]
        if val < prev_val:
            result -= val
        else:
            result += val
        prev_val = val
    return result


def parse_atomic_number_and_ion(element: int | AtmElement | str, ion=1) -> tuple[int, int]:
    """
    Parse the atomic number with ion or string representation of element and ion (HeII) to numeric form.

    Parameters
    ----------
    element: int | AtmElement | str
        Atomic number or symbol of the element or AtmElement instance
    ion: int
        Ion of associated with the element

    Returns
    -------
     tuple:
        Tuple with the atomic number and ion associated with it.
        Ion is calculated from ``1`` to ``element + 1``
    """

    # _element = 1: H, 2: He, 3: Li, ... 30: Zn
    if type(element) is int and element not in range(1, AtmElement.Zinc.atomic_number + 1):  # noqa: E721
        raise ValueError(f"Invalid atomic number {element}.")

    def validate_ion(_ion, _atm_no: int):
        # _ion = 1 : neutral, 2: +, 3: ++ .... (element+1): (++++... _element times)
        if type(_ion) is not int:  # noqa: E721
            return 1
        elif _ion in range(1, _atm_no + 1):
            return _ion

        raise ValueError(f"Invalid ion {_ion}.")

    if type(element) is AtmElement:
        return element.atomic_number, validate_ion(ion, element.atomic_number)

    # str() adds the tolerance when int is passed to element
    if el_match := re.match(r"^([A-Z][a-z]?)([IVX]+)$", str(element)):
        element_symbol, roman_ion = el_match.groups()
        element = AtmElement.parse(element_symbol)
        ion = roman_to_int(roman_ion)
    else:
        element = AtmElement.parse(element)

    return element.atomic_number, validate_ion(ion, element.atomic_number)


def element_indices(element: int | AtmElement | str, ion: int = None) -> tuple[int, int]:
    parsed_element = parse_atomic_number_and_ion(element, ion)[0]

    # Select only the ions for the requested _element
    slice_start = int((parsed_element - 1) * (parsed_element + 2) / 2)
    slice_stop = int(parsed_element * (parsed_element + 3) / 2)
    return slice_start, slice_stop


def generate_blake2b_hash(target_file: Path) -> str:
    """
    Get the blake2b hash of the target file in hex digits.

    Parameters
    ----------
    target_file: Path
        The target file you want to get the hash of

    References
    ----------
    https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python

    Returns
    -------
    str:
        Hex digest of the target file
    """
    with target_file.open("rb") as file:
        file_hash = hashlib.blake2b()

        while chunk := file.read(CHUNK_SIZE):
            file_hash.update(chunk)

        return file_hash.hexdigest()


def verify_checksum(target_file: Path, reference_sum: str) -> bool:
    """
    Tests if the checksum of target_file is same as reference_sum

    Parameters
    ----------
    target_file: Path
        The target file to open and compute checksum
    reference_sum: str
        Checksum to compare

    Returns
    -------
    bool:
        ``True`` when checksum of target_file is same as reference_sum
    """
    return generate_blake2b_hash(target_file) == reference_sum


def prepare_onedrive_link(link: str) -> str:
    """
    Prepares the download link for the sharepoint urls. Basically it will add ``download=1`` in the query parameter

    Parameters
    ----------
    link: str
        One drive link to download

    Returns
    -------
    str:
        The same link but with ``download=1`` query parameter

    """
    return link.split("?")[0] + "?download=1"


def save_hash_to_file(save_path: Path, target_file: Path, checksum: str = None):
    """
    If the checksum is not ``None``, it is saved; otherwise, the hash is computed for the ``target_file`` and then save to ``save_path``.

    Parameters
    ----------
    save_path: Path
        The JSON file name to save the computed hashes for the filenames.
    target_file: Path
        The target file whose checksum you want to save.
    checksum: str | None
        If the checksum is pre-calculated then use this instead of recomputing.
    """
    if save_path.exists():
        with save_path.open("r") as file:
            checksum_map = json.load(file)
    else:
        checksum_map = {}

    checksum_map[target_file.name] = checksum or generate_blake2b_hash(target_file)

    with save_path.open("w") as file:
        json.dump(checksum_map, file, indent=3)
