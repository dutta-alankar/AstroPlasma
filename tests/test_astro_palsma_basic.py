# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 18:27:11 2023

@author: alankar
"""

import traceback
import logging


def test_import():
    try:
        pass
    except Exception:
        logging.error(traceback.format_exc())
        raise AssertionError


def test_hash():
    import astro_plasma
    from pathlib import Path
    import numpy as np
    import os

    LOCAL_DATA_PATH = astro_plasma.core.utils.LOCAL_DATA_PATH

    ionization_token = "EzYYrEgXdQscQJo"
    directory = LOCAL_DATA_PATH / Path("ionization")
    if not((directory / Path("hashlist.txt")).is_file()):
        astro_plasma.core.download_database.fetch_hashlist_from_url(ionization_token, directory / Path("hashlist.txt"))
    with open(directory / Path("hashlist.txt"), "r") as file:
        hash_list = [line.split("\n")[0] for line in file.readlines()]
    file_id = int(np.random.randint(0, len(hash_list) - 1, 1)[0])
    hash_ionization_expect = hash_list[file_id]
    ionization_filename_list = astro_plasma.core.download_database.fetch_filelist_from_url(ionization_token)
    ionization_filename = os.path.basename(ionization_filename_list[file_id])
    if not (Path(directory / ionization_filename).is_file()):
        astro_plasma.core.download_database.download_datafiles(files_link_token=ionization_token, 
                                                               download_location=directory, 
                                                               specific_file_ids=[file_id,])
    # check the hash of the datafile <filenumber>
    hash_ionization_found = astro_plasma.core.utils.blake2bsum(LOCAL_DATA_PATH / Path("ionization") / Path(ionization_filename))
    assert hash_ionization_found == hash_ionization_expect

    emission_token = "3Edp5YzJqWnXYWq"
    directory = LOCAL_DATA_PATH / Path("emission")
    if not((directory / Path("hashlist.txt")).is_file()):
        astro_plasma.core.download_database.fetch_hashlist_from_url(emission_token, directory / Path("hashlist.txt"))
    with open(directory / Path("hashlist.txt"), "r") as file:
        hash_list = [line.split("\n")[0] for line in file.readlines()]
    file_id = int(np.random.randint(0, len(hash_list) - 1, 1)[0])
    hash_emission_expect = hash_list[file_id]
    emission_filename_list = astro_plasma.core.download_database.fetch_filelist_from_url(emission_token)
    emission_filename = os.path.basename(emission_filename_list[file_id])
    if not (Path(directory / emission_filename).is_file()):
        astro_plasma.core.download_database.download_datafiles(files_link_token=emission_token, 
                                                               download_location=directory, 
                                                               specific_file_ids=[file_id,])
    # check the hash of the datafile <filenumber>
    hash_emission_found = astro_plasma.core.utils.blake2bsum(LOCAL_DATA_PATH / Path("emission") / Path(emission_filename))
    assert hash_emission_found == hash_emission_expect


def test_dimension():
    # Import AstroPlasma Ionization module
    from astro_plasma import Ionization
    import numpy as np

    fIon = Ionization.interpolate_ion_frac

    nH = np.power(10.0, np.random.uniform(low=-5.0, high=-2.0))  # Hydrogen number density in cm^-3
    temperature = np.power(10.0, np.random.uniform(low=3.8, high=6.5))  # Temperature of the plasma in kelvin
    metallicity = np.random.uniform(low=0.2, high=0.9)  # Metallicity of plasma with respect to solar
    redshift = np.random.uniform(low=0.1, high=1.2)  # Cosmological redshift
    mode = "PIE"

    element = np.random.randint(low=1, high=32)
    ion = np.random.randint(low=1, high=element + 1)

    frac = fIon(
        nH=nH,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).ndim == 0

    frac = fIon(
        nH=nH,
        temperature=[
            temperature,
        ],
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).ndim == 0

    nH = np.power(10.0, np.random.uniform(low=-5.0, high=-2.0))  # Hydrogen number density in cm^-3
    temperature = np.power(10.0, np.linspace(3.8, 6.5, 5))  # Temperature of the plasma in kelvin
    metallicity = np.random.uniform(low=0.2, high=0.9)  # Metallicity of plasma with respect to solar
    redshift = np.random.uniform(low=0.1, high=1.2)  # Cosmological redshift

    frac = fIon(
        nH=nH,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).shape == temperature.shape

    nH = np.logspace(-5.0, -2.0, 2)  # Hydrogen number density in cm^-3
    temperature = np.logspace(3.8, 6.5, 5)  # Temperature of the plasma in kelvin
    nH, temperature = np.meshgrid(nH, temperature)
    metallicity = np.random.uniform(low=0.2, high=0.9)  # Metallicity of plasma with respect to solar
    redshift = np.random.uniform(low=0.1, high=1.2)  # Cosmological redshift

    frac = fIon(
        nH=nH,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).shape == temperature.shape

    # all ions of any one element
    frac = fIon(
        nH=nH,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).shape == (*temperature.shape, element + 1)

    # all ions of all elements
    frac = fIon(
        nH=nH,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        all_ions=True,
    )  # This value is in log10
    assert np.array(frac).shape == (*temperature.shape, 495)
