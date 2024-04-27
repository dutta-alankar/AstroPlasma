# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 20:37:04 2023

@author: alankar
"""
from __future__ import annotations

import logging

# Built-in imports
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

# Third party imports
import requests

# Local package imports
from .utils import LOCAL_DATA_PATH, DB_BASE_URL, CHUNK_SIZE, PARALLEL_JOBS, verify_checksum, prepare_onedrive_link, save_hash_to_file

log = logging.getLogger(__name__)


def download_datafiles(filename_format: str, download_links_url: str, download_dir: Path, **kwargs):
    """
    Fetch the datafiles and save them to the ``download_location``.

    Parameters
    ----------
    filename_format: str
        Format string syntax to create file names
    download_links_url: str
        URL to fetch the links for all the files
    download_dir: Path
        Base path to download the files
    kwargs: dict
        Extra configuration

    References
    ----------
    https://docs.python.org/3/library/string.html#format-string-syntax

    """
    initialize = kwargs.get("initialize", False)
    generate_hashes = kwargs.get("generate_hashes", False)
    hash_list_url = kwargs.get("hash_list_file_url")
    file_ids = [0] if initialize else kwargs.get("file_ids", [])
    if file_ids and type(file_ids) is not list:  # noqa: E721
        file_ids = list(file_ids)
    links_response = requests.get(download_links_url)
    download_links = np.array(re.split(r"\r?\n", links_response.text.strip()))
    n_download_links = download_links.shape[0]

    if file_ids:
        download_links = map(prepare_onedrive_link, download_links[file_ids])
    else:
        download_links = map(prepare_onedrive_link, download_links)

    if hash_list_url:
        hashes_response = requests.get(hash_list_url)
        hashes = np.array(re.split(r"\r?\n", hashes_response.text.strip()))
        if file_ids:
            hashes = hashes[file_ids]
    else:
        hashes = [None] * n_download_links

    file_names = map(lambda file_id: filename_format.format(file_id), file_ids or range(n_download_links))

    if not download_dir.exists():
        download_dir.mkdir(mode=0o766, parents=True)

    def download_job(target_url: str, save_path: Path, generate_hash: bool, checksum: str = None):
        # noinspection PyShadowingNames
        file_content_response = requests.get(target_url, stream=True)
        if save_path.exists() and verify_checksum(save_path, checksum):
            log.debug("Target file already exists")
        else:
            log.info("Downloading %s", save_path.name)
            with open(save_path, "wb") as file:
                for data in file_content_response.iter_content(chunk_size=CHUNK_SIZE):
                    file.write(data)
                file_content_response.close()

        if generate_hash:
            save_hash_to_file(download_dir / "hashes.json", save_path, checksum)

    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as pool:
        for url, file_name, pre_computed_checksum in zip(download_links, file_names, hashes):
            log.debug("Submitting %s to downloader pool", url)
            pool.submit(download_job, url, download_dir / file_name, generate_hashes, pre_computed_checksum)


def download_ionization_data(initialize=False, hashgen=False, file_ids: list[int] = None):
    ionization_links_url = prepare_onedrive_link(f"{DB_BASE_URL}/EYnSBoTNOmdPqs3GPE0PDW0BDafcR78jbGCUM8tFqW8UAw?e=cCFbse")
    ionization_hash_url = prepare_onedrive_link(f"{DB_BASE_URL}/ETCJ1CWIJOlAkcuj3WNxtG8Bjwt0Y3ctul8kffzafB84tQ?e=0nmRdf")
    download_datafiles(
        "ionization.b_{:06d}.h5",
        ionization_links_url,
        LOCAL_DATA_PATH / "ionization",
        initialize=initialize,
        generate_hashes=hashgen,
        hash_list_file_url=ionization_hash_url,
        file_ids=file_ids,
    )


def download_emission_data(initialize: bool = False, hashgen: bool = False, file_ids: list[int] = None):
    emission_links_url = prepare_onedrive_link(f"{DB_BASE_URL}/EWJuOmWHwAVEnEtziAV5kg8BXtFp_44-0smofLpr_f_2Pg?e=7sreMC")
    emission_hash_url = prepare_onedrive_link(f"{DB_BASE_URL}/EZbmBm1BL_hEmKMyYXYsOZIBMIBxr3mJazjGvL53T5ZoAw?e=7bMW2B")
    download_datafiles(
        "emission.b_{:06d}.h5",
        emission_links_url,
        LOCAL_DATA_PATH / "emission",
        initialize=initialize,
        generate_hashes=hashgen,
        hash_list_file_url=emission_hash_url,
        file_ids=file_ids,
    )


def download_all() -> None:
    download_ionization_data()
    download_emission_data()


def hash_all() -> None:
    download_ionization_data(hashgen=True)
    download_emission_data(hashgen=True)


def initialize_data(predicate: str):
    if predicate == "ionization":
        download_ionization_data(initialize=True)
    elif predicate == "emission":
        download_emission_data(initialize=True)
    else:
        raise ValueError(f"Predicate {predicate} is not allowed.")
