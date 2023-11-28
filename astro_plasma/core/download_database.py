# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 20:37:04 2023

@author: alankar
"""

# Built-in imports
import os
from pathlib import Path
from typing import Union, Tuple, Optional, List

# Third party imports
import requests
from urllib.parse import urlparse
import werkzeug

# Local package imports
from .utils import LOCAL_DATA_PATH, fetch, checksum, blake2bsum, prepare_onedrive_link


def fetch_list_from_url(link_list_url: str) -> List[str]:
    response = requests.get(link_list_url, stream=True)
    links = response.content.decode("utf-8").split("\n")
    return links


# Taken from: https://stackoverflow.com/questions/31804799/how-to-get-pdf-filename-with-python-requests
def get_filename(url: str) -> str:
    try:
        with requests.get(url, stream=True) as req:
            if content_disposition := req.headers.get("Content-Disposition"):
                param, options = werkzeug.http.parse_options_header(content_disposition)
                if param == "attachment" and (filename := options.get("filename")):
                    return filename
            path = urlparse(req.url).path
            name = path[path.rfind("/") + 1 :]
            return name
    except requests.exceptions.RequestException as e:
        raise e


def check_files(link_list_url: str) -> None:
    links = fetch_list_from_url(link_list_url)
    links = [prepare_onedrive_link(link) for link in links]
    for link in links:
        print(get_filename(link))


def check_hashes_and_trim(
    links_and_names: List[Tuple[str, Path]],
    download_location: Path,
    hash_list_url: Optional[str] = None,
) -> List[Tuple[str, Path]]:
    _local_hashlist = True if hash_list_url is None else False
    if _local_hashlist:
        with open(download_location / "hashlist.txt", "r") as f:
            hash_list = [line.split("\n")[0] for line in f.readlines()]
    else:
        hash_list = fetch_list_from_url(hash_list_url)
    links_and_names_trimmed = []
    for indx, (_, filename) in enumerate(links_and_names):
        if not (os.path.isfile(download_location / filename) and checksum(download_location / filename, hash_list[indx])):
            links_and_names_trimmed.append(links_and_names[indx])
    return links_and_names_trimmed


def generate_hashes(links_and_names: List[Tuple[str, Path]], download_location: Path) -> None:
    hashlist = []
    for _, filename in links_and_names:
        if os.path.isfile(download_location / filename):
            file_hash = blake2bsum(download_location / filename)
            hashlist.append(file_hash)
    with open(download_location / "hashlist.txt", "w") as f:
        for indx, hash_val in enumerate(hashlist):
            f.write(hash_val + "\n" if (indx + 1) < len(hashlist) else hash_val)


def download_datafiles(
    link_list_url: str,
    download_location: Union[str, Path],
    initialize: bool = False,
    hashgen: bool = False,
    hash_list_url: Optional[str] = None,
) -> None:
    links = fetch_list_from_url(link_list_url)
    links = [prepare_onedrive_link(link) for link in links]
    links_and_names = [(link, Path(get_filename(link))) for link in links]
    if initialize:
        links_and_names = [links_and_names[0]]
    if hashgen:
        generate_hashes(
            links_and_names,
            Path(download_location) if not (isinstance(download_location, Path)) else download_location,
        )
        return None
    links_and_names = check_hashes_and_trim(
        links_and_names,
        Path(download_location) if not (isinstance(download_location, Path)) else download_location,
        hash_list_url,
    )
    if len(links_and_names) == 0:
        return None
    fetch(links_and_names, Path(download_location) if not (isinstance(download_location, Path)) else download_location)


def download_ionization_data(
    initialize: bool = False,
    hashgen: bool = False,
) -> None:
    ionization_links_url = prepare_onedrive_link(
        "https://indianinstituteofscience-my.sharepoint.com/:u:/g/personal/alankardutta_iisc_ac_in/EYnSBoTNOmdPqs3GPE0PDW0BDafcR78jbGCUM8tFqW8UAw?e=cCFbse"
    )
    ionization_hash_url = prepare_onedrive_link(
        "https://indianinstituteofscience-my.sharepoint.com/:t:/g/personal/alankardutta_iisc_ac_in/EbK_KzUA5lVChnpsJFu2pAcBzVnjX6CEHUQp9e9Yi83-Yw?e=9WAi2b"
    )
    download_datafiles(ionization_links_url, LOCAL_DATA_PATH / "ionization", initialize, hashgen, ionization_hash_url)


def download_emission_data(
    initialize: bool = False,
    hashgen: bool = False,
) -> None:
    emission_links_url = prepare_onedrive_link(
        "https://indianinstituteofscience-my.sharepoint.com/:u:/g/personal/alankardutta_iisc_ac_in/EWJuOmWHwAVEnEtziAV5kg8BXtFp_44-0smofLpr_f_2Pg?e=7sreMC"
    )
    emission_hash_url = prepare_onedrive_link(
        "https://indianinstituteofscience-my.sharepoint.com/:t:/g/personal/alankardutta_iisc_ac_in/EZbmBm1BL_hEmKMyYXYsOZIBMIBxr3mJazjGvL53T5ZoAw?e=7bMW2B"
    )
    download_datafiles(emission_links_url, LOCAL_DATA_PATH / "emission", initialize, hashgen, emission_hash_url)


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
