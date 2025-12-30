# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 20:28:15 2023

@author: alankar
"""

# Built-in imports
import os
import re
import hashlib
import time
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Tuple, Union, Optional, Sequence

# Third party imports
from webdav4.client import Client
from dotenv import load_dotenv
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TextColumn,
)
from enum import Enum

LOCAL_DATA_PATH = Path(__file__).parent.parent / "data"
ROMAN_DICT = {"I": 1, "V": 5, "X": 10}
WEBDAV_MPCDF_URL = "https://datashare.mpcdf.mpg.de/public.php/webdav/"

# load env file to os.environ and can be access from os.getenv()
load_dotenv()

# download chunk size, # bytes to download at a time
CHUNK_SIZE_MIN = int(os.getenv("CHUNK_SIZE_MIN", "128")) * 1024
CHUNK_SIZE_MAX = int(os.getenv("CHUNK_SIZE_MAX", "8192")) * 1024
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
TARGET_UPDATE_INTERVAL = float(os.getenv("TARGET_UPDATE_INTERVAL", "0.1"))
BASE_URL = os.getenv("ASTROPLASMA_SERVER", "http://localhost:8000")
PARALLEL_JOBS = int(os.getenv("PARALLEL_DOWNLOAD_JOBS", "4"))
RETAIN_BARS = False


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
        idx = int(isinstance(predicate, int))
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


def fetch_webdav(token: str, files: Sequence[Tuple[Union[str, Path], int]], base_dir: Union[str, Path]) -> None:
    # ([(remote_file_location, file_id)], save_directory)

    if not (isinstance(base_dir, Path)):
        base_dir = Path(base_dir)
    base_dir.mkdir(mode=0o766, parents=True, exist_ok=True)
    client = Client(WEBDAV_MPCDF_URL, auth=(token, ""))

    progress = Progress(
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None, complete_style="blue", finished_style="green"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    )

    def download_job(remote_path: Union[str, Path], task_id: int) -> None:
        local_filename = Path(os.path.basename(remote_path))
        local_path = base_dir / local_filename
        temp_path = local_path.with_suffix(local_path.suffix + ".part")

        try:
            progress.update(task_id, visible=True)
            file_size = client.content_length(str(remote_path))
            progress.update(task_id, total=file_size)

            # 1. Skip if already exists
            if local_path.exists() and local_path.stat().st_size == file_size:
                # Force bar to 100% before removing
                progress.update(task_id, completed=file_size, description=f"[green]Done: {local_filename}")
                # time.sleep(0.1)
                progress.remove_task(task_id)
                return

            # 2. Retry Loop
            for attempt in range(MAX_RETRIES):
                current_chunk_size = 256 * 1024
                try:
                    progress.update(task_id, description=f"Att {attempt+1}: {local_filename}", completed=0)

                    with client.open(str(remote_path), "rb") as remote_file:
                        with open(temp_path, "wb") as local_file:
                            while True:
                                start_time = time.perf_counter()
                                chunk = remote_file.read(current_chunk_size)
                                if not chunk:
                                    break

                                local_file.write(chunk)
                                elapsed = time.perf_counter() - start_time
                                progress.update(task_id, advance=len(chunk))

                                if elapsed > 0:
                                    ideal_size = int(current_chunk_size * (TARGET_UPDATE_INTERVAL / elapsed))
                                    current_chunk_size = max(CHUNK_SIZE_MIN, min(ideal_size, CHUNK_SIZE_MAX))

                    # Verify and Finalize
                    if temp_path.stat().st_size == file_size:
                        temp_path.replace(local_path)
                        # --- THE FIX: Explicitly set 100% and refresh UI ---
                        progress.update(task_id, completed=file_size, description=f"[green]Done: {local_filename}")
                        if not RETAIN_BARS:
                            time.sleep(0.2)  # Give the user a moment to see the 100%
                            progress.remove_task(task_id)
                        return

                except Exception as e:
                    wait_time = (2**attempt) + random.random()
                    progress.console.print(f"[yellow]Error on {local_filename}: {e}. Retrying...")
                    time.sleep(wait_time)

            progress.console.print(f"[red]CRITICAL: Failed {local_filename}")
            progress.remove_task(task_id)

        except Exception as e:
            progress.console.print(f"[red]Setup error for {local_filename}: {e}")
            progress.remove_task(task_id)

    with progress:
        # ThreadPoolExecutor's 'with' block ensures we wait for all threads to finish
        # before 'progress' (the outer block) stops.
        with ThreadPoolExecutor(max_workers=min(PARALLEL_JOBS, len(files))) as pool:
            for remote_path, _ in files:
                task_id = progress.add_task(description=os.path.basename(remote_path), total=None, visible=False)
                pool.submit(download_job, remote_path, task_id)


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
