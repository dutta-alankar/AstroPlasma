# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 20:28:15 2023

@author: alankar
"""

# Built-in imports
import os
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Tuple, Union, Optional
from urllib.parse import urljoin

# Third party imports
import requests
from dotenv import load_dotenv
from tqdm import tqdm
from enum import Enum

LOCAL_DATA_PATH = Path(__file__).parent.parent / "data"
ROMAN_DICT = {"I": 1, "V": 5, "X": 10}

# load env file to os.environ and can be access from os.getenv()
load_dotenv()

# download chunk size, # bytes to download at a time
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "4096"))
BASE_URL = os.getenv("ASTROPLASMA_SERVER", "http://localhost:8000")
PARALLEL_JOBS = int(os.getenv("PARALLEL_DOWNLOAD_JOBS", "4"))


class AtmElement(Enum):
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
    def parse(predicate: Union[str, int]) -> "AtmElement":
        idx = int(type(predicate) == int)
        error_label = "atomic number" if idx == 1 else "symbol"

        for element in AtmElement:
            if element.value[idx] == predicate:
                return element

        raise ValueError(f"Invalid {error_label} {predicate}.")

    def to_atm_no(self) -> int:
        return self.value[1]


def roman_to_int(s):
    result = 0
    prev_val = 0
    for c in s[::-1]:
        val = ROMAN_DICT[c]
        if val < prev_val:
            result -= val
        else:
            result += val
        prev_val = val
    return result


def parse_atomic_ion_no(
    element: Union[int, AtmElement, str],
    ion: Optional[int] = None,
) -> Tuple[int, int]:
    if not isinstance(element, AtmElement):
        ielem: re.Match = re.match(r"^([A-Z][a-z]?)([IVX]+)$", str(element))
        if ielem:
            element = AtmElement.parse(ielem.group(1))
            ion = roman_to_int(ielem.group(2))
        else:
            element = AtmElement.parse(element)
    elem_atm_no = element.to_atm_no()
    return (elem_atm_no, ion)


def element_indices(
    element: Union[int, AtmElement, str],
    ion: Optional[int] = None,
) -> Tuple[int, int]:
    _element, _ion = parse_atomic_ion_no(element, ion)

    # _element = 1: H, 2: He, 3: Li, ... 30: Zn
    # _ion = 1 : neutral, 2: +, 3: ++ .... (_element+1): (++++... _element times)
    if _ion < 0 or _ion > _element + 1:
        raise ValueError(f"Problem! Invalid ion {_ion} for element {_element}.")
    if _element < 0 or _element > 30:
        raise ValueError(f"Problem! Invalid element {_element}.")

    # Select only the ions for the requested _element
    slice_start = int((_element - 1) * (_element + 2) / 2)
    slice_stop = int(_element * (_element + 3) / 2)
    return (slice_start, slice_stop)


def fetch(urls: List[Tuple[str, Path]], base_dir: Path):
    # ([(link, filename)], save_location)
    base_dir.mkdir(mode=0o766, parents=True, exist_ok=True)

    # unit job of downloading and saving file
    def download_job(url: str, save_path: Path):
        response = requests.get(url, stream=True)
        file_size = int(response.headers.get("content-length", 0))

        progress = tqdm(
            desc=save_path.name,
            total=file_size,
            ascii=True,
            unit_scale=True,
            unit="iB",
            leave=False,
        )

        if save_path.exists() and save_path.stat().st_size == file_size:
            progress.update(file_size)
            return

        with open(save_path, "wb") as file:
            for data in response.iter_content(chunk_size=CHUNK_SIZE):
                progress.update(len(data))
                file.write(data)
            progress.close()
            response.close()

    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS, thread_name_prefix="cloudy_dnldr") as pool:
        # iterative download and show progress bar using tqdm
        for url_path, file_name in urls:
            url = urljoin(BASE_URL, url_path)
            pool.submit(download_job, url, base_dir / file_name)


# Taken from: https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
def blake2bsum(filename: Union[str, Path]) -> str:
    chunk_size = 8192
    with open(filename, "rb") as f:
        file_hash = hashlib.blake2b()
        while chunk := f.read(chunk_size):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def checksum(filename: Union[str, Path], reference_sum: str) -> bool:
    sum_val = blake2bsum(filename)
    return sum_val == reference_sum


def prepare_onedrive_link(link: str) -> str:
    return link.split("?")[0] + "?download=1"
