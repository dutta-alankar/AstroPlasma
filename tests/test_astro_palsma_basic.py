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

    LOCAL_DATA_PATH = astro_plasma.core.utils.LOCAL_DATA_PATH
    ionization_hash_url = astro_plasma.core.utils.prepare_onedrive_link(
        "https://indianinstituteofscience-my.sharepoint.com/:t:/g/personal/alankardutta_iisc_ac_in/EbK_KzUA5lVChnpsJFu2pAcBzVnjX6CEHUQp9e9Yi83-Yw?e=9WAi2b"
    )
    ionization_links_url = astro_plasma.core.utils.prepare_onedrive_link(
        "https://indianinstituteofscience-my.sharepoint.com/:u:/g/personal/alankardutta_iisc_ac_in/EYnSBoTNOmdPqs3GPE0PDW0BDafcR78jbGCUM8tFqW8UAw?e=cCFbse"
    )
    all_urls = astro_plasma.core.download_database.fetch_list_from_url(ionization_links_url)
    filenumber = int(np.random.randint(0, len(all_urls) - 1, 1)[0])
    ionization_file_url = astro_plasma.core.utils.prepare_onedrive_link(all_urls[filenumber])
    hash_ionization_expect = astro_plasma.core.download_database.fetch_list_from_url(ionization_hash_url)[filenumber]
    ionization_filename = astro_plasma.core.download_database.get_filename(ionization_file_url)
    if not (Path(LOCAL_DATA_PATH / "ionization" / ionization_filename).is_file()):
        astro_plasma.core.utils.fetch([(ionization_file_url, Path(ionization_filename))], LOCAL_DATA_PATH / "ionization")
    # check the hash of the datafile <filenumber>
    hash_ionization_found = astro_plasma.core.utils.blake2bsum(LOCAL_DATA_PATH / "ionization" / ionization_filename)
    assert hash_ionization_found == hash_ionization_expect

    filenumber = int(np.random.randint(0, len(all_urls) - 1, 1)[0])
    emission_hash_url = astro_plasma.core.utils.prepare_onedrive_link(
        "https://indianinstituteofscience-my.sharepoint.com/:t:/g/personal/alankardutta_iisc_ac_in/EZbmBm1BL_hEmKMyYXYsOZIBMIBxr3mJazjGvL53T5ZoAw?e=7bMW2B"
    )
    emission_links_url = astro_plasma.core.utils.prepare_onedrive_link(
        "https://indianinstituteofscience-my.sharepoint.com/:u:/g/personal/alankardutta_iisc_ac_in/EWJuOmWHwAVEnEtziAV5kg8BXtFp_44-0smofLpr_f_2Pg?e=7sreMC"
    )
    all_urls = astro_plasma.core.download_database.fetch_list_from_url(emission_links_url)
    filenumber = int(np.random.randint(0, len(all_urls) - 1, 1)[0])
    hash_emission_expect = astro_plasma.core.download_database.fetch_list_from_url(emission_hash_url)[filenumber]
    emission_file_url = astro_plasma.core.utils.prepare_onedrive_link(all_urls[filenumber])
    emission_filename = astro_plasma.core.download_database.get_filename(emission_file_url)
    if not (Path(LOCAL_DATA_PATH / "emission" / emission_filename).is_file()):
        astro_plasma.core.utils.fetch([(emission_file_url, Path(emission_filename))], LOCAL_DATA_PATH / "emission")
    # check the hash of the datafile <filenumber>
    hash_emission_found = astro_plasma.core.utils.blake2bsum(LOCAL_DATA_PATH / "emission" / emission_filename)
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
