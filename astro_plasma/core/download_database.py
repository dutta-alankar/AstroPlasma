# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 20:37:04 2023

@author: alankar
"""

# Built-in imports
import os
import sys
import re
import inspect
from pathlib import Path
from typing import Union, Tuple, Optional, List

# Third party imports
from webdav4.client import Client

# Local package imports
from .utils import LOCAL_DATA_PATH, WEBDAV_MPCDF_URL, fetch_webdav, checksum, blake2bsum


def download_from_server_small(
    files_link_token: str,
    download_location: Union[str, Path],
    filename: Union[str, Path],
) -> None:
    try:
        client = Client(WEBDAV_MPCDF_URL, auth=(files_link_token, ""))
        client.download_file(from_path=os.path.basename(filename), to_path=download_location / Path(os.path.basename(filename)))
    except Exception as error:
        sys.exit(f"Problem communicating with dataserver! (error: {error})")


def fetch_filelist_from_url(files_link_token: str) -> List[str]:
    links = []
    try:
        client = Client(WEBDAV_MPCDF_URL, auth=(files_link_token, ""))
        items = client.ls(path="/", detail=True)
        for item in items:
            if item["name"].endswith(".h5"):
                links.append(item["name"])
    except Exception as error:
        sys.exit(f"Problem communicating with dataserver! (error: {error})")
    # print(response)
    return links


def fetch_hashlist_from_url(
    files_link_token: str,
    download_location: Union[str, Path],
) -> None:
    if not isinstance(download_location, Path):
        download_location = Path(download_location)
    filename = download_location / Path("hashlist.txt")
    download_from_server_small(files_link_token, download_location, filename)


def check_hashes_and_trim(
    directory: Union[str, Path],
    links_and_ids: List[Tuple[Path, int]],
    files_link_token: str = None,
) -> List[Tuple[Path, int]]:
    if not (isinstance(directory, Path)):
        directory = Path(directory)
    _local_hashlist = os.path.isfile(directory / Path("hashlist.txt"))
    if not (_local_hashlist):
        try:
            fetch_hashlist_from_url(files_link_token, directory)
        except Exception as error:
            print(f"Problem downloading data! Most likely internet connection issue! Code Aborted!\nError: {error}")
            sys.exit(1)
    with open(directory / Path("hashlist.txt"), "r") as file:
        hash_list = [line.split("\n")[0] for line in file.readlines()]

    links_and_names_trimmed = []
    for filename, id in links_and_ids:
        filename = Path(os.path.basename(filename))
        if not (os.path.isfile(directory / filename) and checksum(directory / filename, hash_list[id])):
            links_and_names_trimmed.append(next((item for item in links_and_ids if item[1] == id), None))
    return links_and_names_trimmed


def generate_hashes(directory: Union[str, Path], filenames: List[Union[str, Path]]) -> None:
    hash_list = []
    if not (isinstance(directory, Path)):
        directory = Path(directory)
    for filename in map(lambda f: Path(os.path.basename(f)), filenames):
        if not (isinstance(filename, Path)):
            filename = Path(filename)
        if os.path.isfile(directory / filename):
            file_hash = blake2bsum(directory / filename)
            hash_list.append(file_hash)
    with open("hashlist.txt", "w") as f:
        for indx, hash_val in enumerate(hash_list):
            f.write(hash_val + "\n" if (indx + 1) < len(hash_list) else hash_val)


# should always be called from either `download_ionization_data` or `download_emission_data`
def download_datafiles(
    files_link_token: str,
    download_location: Union[str, Path],
    initialize: bool = False,
    hashgen: bool = False,
    specific_file_ids: Optional[List[int]] = None,
    force_online: bool = False,
) -> None:
    # print("Debug: ", "Inside download datafiles! ", initialize)
    # set the following to True if you believe some files on disk got corrupted
    _always_hashcheck = False  # check hashes of files already downloaded
    caller_name = inspect.stack()[1].code_context[0]
    if initialize:
        specific_file_ids = [
            0,
        ]
    if specific_file_ids is not None:
        # This %06d might needs changing according to the specifics of the database
        if "ionization" in caller_name:
            names = list(map(lambda id_val: f"ionization.b_{id_val:06d}.h5", specific_file_ids))
        elif "emission" in caller_name:
            names = list(map(lambda id_val: f"emission.b_{id_val:06d}.h5", specific_file_ids))
        else:
            print("Invalid call to `download_datafiles`:", end=" ")
            print("Undefined usage/some recursive call happened! Code Aborted!")
            sys.exit(1)

        _offline_avail = False not in [os.path.isfile(Path(download_location) / Path(name)) for name in names]
        if not (_offline_avail):
            force_online = True
    else:
        _offline_avail = False
    try:
        if force_online or not (_offline_avail):
            links = fetch_filelist_from_url(files_link_token)
            # [(remote_file_location, file_number)] this is the same here
            links_and_ids = [(Path(link), int(re.search(r"_(\d+)\.", os.path.basename(link)).group(1))) for link in links]
        else:
            links_and_ids = [(Path(name), int(re.search(r"_(\d+)\.", os.path.basename(name)).group(1))) for name in names]
    except Exception as error:
        if not (_offline_avail):
            print(f"Problem downloading data! Most likely internet connection issue! Code Aborted!\nError: {error}")
            sys.exit(1)

    # print("Debug: ", links_and_ids)
    # if initialize:
    #     links_and_ids = [links_and_ids[0]]
    if specific_file_ids is not None and (not (_offline_avail) or force_online):
        links_and_ids = [item for item in links_and_ids if item[1] in specific_file_ids]
    if hashgen:
        generate_hashes(
            Path(download_location) if not (isinstance(download_location, Path)) else download_location,
            [Path(os.path.basename(item[0])) for item in links_and_ids],
        )
        return None
    if (force_online or not (_offline_avail)) or _always_hashcheck:
        links_and_ids = check_hashes_and_trim(
            Path(download_location) if not (isinstance(download_location, Path)) else download_location, links_and_ids, files_link_token
        )  # needed to download hashlist
    if len(links_and_ids) == 0:
        return None
    fetch_webdav(files_link_token, links_and_ids, Path(download_location) if not (isinstance(download_location, Path)) else download_location)


def download_ionization_data(
    initialize: bool = False,
    hashgen: bool = False,
    specific_file_ids: Optional[List[int]] = None,
) -> None:
    ionization_files_link_token = "EzYYrEgXdQscQJo"
    download_datafiles(ionization_files_link_token, LOCAL_DATA_PATH / "ionization", initialize, hashgen, specific_file_ids)


def download_emission_data(
    initialize: bool = False,
    hashgen: bool = False,
    specific_file_ids: Optional[List[int]] = None,
) -> None:
    emission_files_link_token = "3Edp5YzJqWnXYWq"
    download_datafiles(emission_files_link_token, LOCAL_DATA_PATH / "emission", initialize, hashgen, specific_file_ids)


def download_all() -> None:
    download_ionization_data()
    download_emission_data()


def hash_all() -> None:
    download_ionization_data(hashgen=True)
    download_emission_data(hashgen=True)


def initialize_data(data_type: str) -> None:
    if data_type == "ionization":
        download_ionization_data(initialize=True)
    elif data_type == "emission":
        download_emission_data(initialize=True)
    else:
        raise Exception("Invalid choice!\nAbort!")
