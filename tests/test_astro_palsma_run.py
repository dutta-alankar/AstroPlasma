# -*- coding: utf-8 -*-
"""
Created on Sat Dec  9 19:50:11 2023

@author: alankar
"""


def test_ion_frac():
    # Import AstroPlasma Ionization module
    from astro_plasma import Ionization
    from astro_plasma.core.utils import AtmElement  # for element naming using symbols (optional)
    import numpy as np

    f_ion = Ionization.interpolate_ion_frac

    hydrogen_num_density = 1.2e-04  # Hydrogen number density in cm^-3
    temperature = 4.2e05  # Temperature of the plasma in kelvin
    metallicity = 0.99  # Metallicity of plasma with respect to solar
    redshift = 0.001  # Cosmological redshift
    mode = "CIE"

    # Let's get the ionization of OVI
    element = AtmElement.Oxygen
    ion = 6
    f_ovi = f_ion(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )  # This value is in log10
    f_ovi = np.power(10.0, f_ovi)
    f_ovi_expected = 8.895256915490418e-02
    assert np.isclose(f_ovi, f_ovi_expected)


def test_num_dens():
    # Import AstroPlasma Ionization module
    from astro_plasma import Ionization
    import numpy as np

    num_dens = Ionization.interpolate_num_dens

    hydrogen_num_density = 1.2e-04  # Hydrogen number density in cm^-3
    temperature = 4.2e05  # Temperature of the plasma in kelvin
    metallicity = 0.99  # Metallicity of plasma with respect to solar
    redshift = 0.001  # Cosmological redshift
    mode = "CIE"

    ne = num_dens(
        nH=hydrogen_num_density,
        temperature=[temperature],
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        part_type="electron",
    )
    assert np.array(ne).ndim == 0
    ne_expected = 1.4109277149716788e-04
    assert np.isclose(ne, ne_expected)

    n = num_dens(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        part_type="all",
    )
    n_expected = 2.714495226687527e-04
    assert np.isclose(n, n_expected)

    ni = num_dens(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        part_type="ion",
    )
    ni_expected = 1.3087928999569684e-04
    assert np.isclose(ni, ni_expected)

    nn = num_dens(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        part_type="neutral",
    )
    nn_expected = 1.0861042185130847e-10
    assert np.isclose(nn, nn_expected)

    n_hi = num_dens(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        element="HI",
    )
    n_hi_expected = 1.0731159716825104e-10
    assert np.isclose(n_hi, n_hi_expected)


def test_mu():
    # Import AstroPlasma Ionization module
    from astro_plasma import Ionization
    import numpy as np

    mean_mass = Ionization.interpolate_mu

    hydrogen_num_density = 1.2e-04  # Hydrogen number density in cm^-3
    temperature = 4.2e05  # Temperature of the plasma in kelvin
    metallicity = 0.99  # Metallicity of plasma with respect to solar
    redshift = 0.001  # Cosmological redshift
    mode = "CIE"

    mu = mean_mass(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        part_type="all",
    )
    mu_expected = 0.6181703336141905
    assert np.isclose(mu, mu_expected)

    mu_e = mean_mass(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        part_type="electron",
    )
    mu_e_expected = 1.1893028977102762
    assert np.isclose(mu_e, mu_e_expected)

    mu_i = mean_mass(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        part_type="ion",
    )
    mu_i_expected = 1.2821130218010255
    assert np.isclose(mu_i, mu_i_expected)


def test_spectrum():
    # Import AstroPlasma EmissionSpectrum module
    from astro_plasma import EmissionSpectrum
    import numpy as np

    gen_spectrum = EmissionSpectrum.interpolate_spectrum

    hydrogen_num_density = 1.2e-04  # Hydrogen number density in cm^-3
    temperature = 4.2e05  # Temperature of the plasma in kelvin
    metallicity = 0.99  # Metallicity of plasma with respect to solar
    redshift = 0.001  # Cosmological redshift
    mode = "CIE"

    # Generate spectrum
    spectrum = gen_spectrum(
        nH=hydrogen_num_density,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
    )

    spectrum_expected = np.loadtxt("tests/sample_spectrum.txt")
    assert np.sum(np.abs(spectrum - spectrum_expected)) < 1.0e-06
