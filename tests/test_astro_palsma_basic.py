# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 18:27:11 2023

@author: alankar
"""


def test_files_hashes():
    from astro_plasma.core.utils import LOCAL_DATA_PATH, DB_BASE_URL, prepare_onedrive_link, generate_blake2b_hash
    from astro_plasma.core.download_database import download_ionization_data, download_emission_data
    from astro_plasma.core import ionization, spectrum

    import random
    import requests
    import re

    ionization_file_hashes_resopnse = requests.get(prepare_onedrive_link(f"{DB_BASE_URL}/ETCJ1CWIJOlAkcuj3WNxtG8Bjwt0Y3ctul8kffzafB84tQ?e=0nmRdf"))
    ionization_file_hashes = re.split(r"\r?\n", ionization_file_hashes_resopnse.text.strip())

    random_file_index = random.randint(0, len(ionization_file_hashes) - 1)
    ionization_file_expected_hash = ionization_file_hashes[random_file_index]

    download_ionization_data(file_ids=[random_file_index])

    ionization_file_computed_hash = generate_blake2b_hash(LOCAL_DATA_PATH / "ionization" / ionization.FILE_NAME_TEMPLATE.format(random_file_index))
    assert ionization_file_computed_hash == ionization_file_expected_hash

    emission_file_hashes_resopnse = requests.get(prepare_onedrive_link(f"{DB_BASE_URL}/EZbmBm1BL_hEmKMyYXYsOZIBMIBxr3mJazjGvL53T5ZoAw?e=7bMW2B"))
    emission_file_hashes = re.split(r"\r?\n", emission_file_hashes_resopnse.text.strip())
    random_file_index = random.randint(0, len(emission_file_hashes) - 1)
    emission_file_expected_hash = emission_file_hashes[random_file_index]

    download_emission_data(file_ids=[random_file_index])

    emission_file_computed_hash = generate_blake2b_hash(LOCAL_DATA_PATH / "emission" / spectrum.FILE_NAME_TEMPLATE.format(random_file_index))
    assert emission_file_computed_hash == emission_file_expected_hash


def test_dimension():
    # Import AstroPlasma Ionization module
    from astro_plasma import Ionization
    import numpy as np
    import random

    f_ion = Ionization.interpolate_ion_frac

    hydrogen_num_density = np.power(10.0, random.uniform(-5.0, -2.0))  # Hydrogen number density in cm^-3
    temperature = np.power(10.0, random.uniform(3.8, 6.5))  # Temperature of the plasma in kelvin
    metallicity = random.uniform(0.2, 0.9)  # Metallicity of plasma with respect to solar
    redshift = random.uniform(0.1, 1.2)  # Cosmological redshift
    mode = "PIE"

    element = random.randint(1, 31)
    ion = random.randint(1, element + 1)

    frac = f_ion(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).ndim == 0

    frac = f_ion(
        nH=hydrogen_num_density,
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

    hydrogen_num_density = np.power(10.0, random.uniform(-5.0, -2.0))  # Hydrogen number density in cm^-3
    temperature = np.power(10.0, np.linspace(3.8, 6.5, 5))  # Temperature of the plasma in kelvin
    metallicity = random.uniform(0.2, 0.9)  # Metallicity of plasma with respect to solar
    redshift = random.uniform(0.1, 1.2)  # Cosmological redshift

    frac = f_ion(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).shape == temperature.shape

    hydrogen_num_density = np.logspace(-5.0, -2.0, 2)  # Hydrogen number density in cm^-3
    temperature = np.logspace(3.8, 6.5, 5)  # Temperature of the plasma in kelvin
    hydrogen_num_density, temperature = np.meshgrid(hydrogen_num_density, temperature)
    metallicity = random.uniform(0.2, 0.9)  # Metallicity of plasma with respect to solar
    redshift = random.uniform(0.1, 1.2)  # Cosmological redshift

    frac = f_ion(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).shape == temperature.shape

    # all ions of any one element
    frac = f_ion(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        mode=mode,
    )  # This value is in log10
    assert np.array(frac).shape == (*temperature.shape, element + 1)

    # all ions of all elements
    frac = f_ion(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        all_ions=True,
    )  # This value is in log10
    assert np.array(frac).shape == (*temperature.shape, 495)
