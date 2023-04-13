![image](https://user-images.githubusercontent.com/39578361/210923881-79133580-b2b7-4e4c-8e0d-dc0b4dd4a691.png)

<img src="https://user-images.githubusercontent.com/39578361/231562510-64469727-9527-4955-b0ce-17a6699ce762.gif"  width="25%" height="20%">

> A *Cloudy* database with functions to quickly interpolate physical state of astrophysical plasma without detailed Plasma modelling

Running Cloudy models on the fly, escpecially when there are lot of models to run with different parameters can become extremely expensive. `AstroPlasma` aims to provide a workaround by using a library of pre-computed cloudy models to generate most of the common plasma properties for a large range of parameter space by interpolation. Owing to a simple and easy to use interface, `AstroPlasma` also provides an abstraction layer enabling the user to get the plasma properties without worrying much about the details of plasma modelling. We find this extremely useful while building models and predicting observables like column densities in different kinds of astrophysical systems.

[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/dutta-alankar/AstroPlasma)

[![PyPI](https://img.shields.io/badge/requires-Python%20≥%203.8-blue?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3811/)

<!--- Tests and style --->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/dutta-alankar/AstroPlasma/main.svg)](https://results.pre-commit.ci/latest/github/dutta-alankar/AstroPlasma/main)

[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://user-images.githubusercontent.com/39578361/230400627-bf897098-c182-4de4-ae79-add645215ad4.png">
  <img alt="" src="https://user-images.githubusercontent.com/39578361/230400616-3b6d7f1a-6520-4a39-b695-c9d99bf214a8.png">
</picture>

## Install
This is just a one-time process.

1. Get the AstroPlasma code:
```
git clone https://github.com/dutta-alankar/AstroPlasma.git
```
2. Change to the code directory
```
cd AstroPlasma
```
3. Use a virtual envinronment (named `venv` here) and install AstroPlasma:
```
python -m venv venv
source venv/bin/activate
python -m pip install --editable .
```
4. Install the dependencies:
For user,
```
python -m pip install -r requirements/requirements.txt
```
For developer,
```
python -m pip install -r requirements/requirements-dev.txt
```
At any point later, in order to use AstroPlasma, just activate this virtual environment:
```
source venv/bin/activate
```
5. Download the data provided in the link at the end and place it inside the `data` directory in the repo. ALternatively, one can use custom data location as well. Please see the relevant *Note* provided near the end of this README.

# User Guide

## This is a notebook that demonstrates the basic usage of `AstroPlasma`
>  **Info**: A `jupyter-notebook` of this User guide can be found in the `tests` directory.

### Ionization modeling

This is how one would use astro_plasma for calculating ionization state of any typical astrophysical plasma. This would be useful in any modeling that depends on calculating the ionization of the plasma. Determining temperautre from density, calculating the free electron density in the plasma are few such examples where `AstroPlasma` can find application.


```python
# Import AstroPlasma Ionization module
from astro_plasma import Ionization
from astro_plasma.core.utils import AtmElement # for element naming using symbols (optional)
```

#### Let us calculate ionization fraction of $\bf{OVI\ (O^{5+}})$

In `AstroPlasma` elements are labelled by their atomic number.
- Atomic number of the desired element is passed to the `element` argument in several functions of `AstroPlasma`. For example, Oxygen corresponds to `element=8`.
- For the ionization state, `AstroPlasma` labels them according to the value passed to the `ion` argument. For example, ionization state III, corresponds to `ion=3`.
- Summarizing, to know the ionization state of $\bf{OVI}$, one needs to pass `element=8` and `ion=6`.


```python
fIon = Ionization.interpolate_ion_frac
```

Now we are going to define typical physical values that characterizes an astrophysical plasma.


```python
nH = 1.2e-04 # Hydrogen number density in cm^-3
temperature = 4.2e+05 # Temperature of the plasma in kelvin
metallicity = 0.99 # Metallicity of plasma with respect to solar
redshift = 0.001 # Cosmological redshift
mode = "CIE"
```

**Note**: The mode passed in the above code refers to the equilibrium state of the plasma. Right now, `AstroPlasma` only supports two equilibrium conditions, namely, *collisional ionization equilibrium* (`CIE` in code) and *photo-ionization equilibrium* (`PIE` in code).

For *photo-ionization equilibrium*, the photo-ionizing backgrounds that are used in the calculation of the *Cloudy* interpolation tables are *Haardt-Madau (2012)* extra-galactic UV/X-ray diffuse background and *Cosmic Microwave Background (CMB)* at any given redshift.


```python
# Lets get the ionization of OVI
element = AtmElement.Oxygen
ion = 6
fOVI = fIon(nH = nH,
            temperature = temperature,
            metallicity = metallicity,
            redshift = redshift,
            element = element,
            ion = ion,
            mode = mode,
            ) # This value is in log10
fOVI = pow(10, fOVI)
print(f"f_OVI = {fOVI:.3e}")
```

    f_OVI = 9.463e-02


**Note**:
- Ionization fraction returned by `AstroPlasma` is in **log10** scale.
- As of now, we **do not** support vectorization of these functions and indivdual values must be passed and **not** arrays. This can lead to errors or un-defined behavior.
- You can provide element and ions in 4 ways
  ```python
  # Using atomic number and ion count (int version of roman)
  fIon(element=8, ion=6) # OVI

  # Using symbol of the element
  fIon(element='O', ion=6) # OVI

  # Using AtmElement for element
  fIon(element=AtmElement.Oxygen, ion=6)  # OVI

  # Using element and ion in one string
  # In this case explicit value of ion will be ignored
  fIon(element='OVI')
  ```
   > **Note** *We recommend using the last two methods as we think it is the most convenient to use and read.*

One can also caluculate other plasma quantities as follows

#### The total free electron density


```python
num_dens = Ionization.interpolate_num_dens

ne = num_dens(nH = nH,
              temperature = temperature,
              metallicity = metallicity,
              redshift = redshift,
              mode = mode,
              part_type = "electron",
              )
print(f"Free electron density = {ne:.3e} cm^-3")
```

    Free electron density = 1.410e-04 cm^-3


In order to get **total particle number density**, use `part_type = "all"` and to get **total ion density**, use `part_type = "ion"`


```python
num_dens = Ionization.interpolate_num_dens

n = num_dens(nH = nH,
              temperature = temperature,
              metallicity = metallicity,
              redshift = redshift,
              mode = mode,
              part_type = "all",
              )
ni = num_dens(nH = nH,
              temperature = temperature,
              metallicity = metallicity,
              redshift = redshift,
              mode = mode,
              part_type = "ion",
              )
print(f"Total particle density = {n:.3e} cm^-3")
print(f"Total ion density = {ni:.3e} cm^-3")
```

    Total particle density = 2.714e-04 cm^-3
    Total ion density = 1.072e-05 cm^-3


Although it is straightforward to obtain mean particle mass, we provide functions to so for the convenience of the user. We use the following relation for calculating these quantities.

$$\rho = n \mu m_p = n_e \mu_e m_p = n_i \mu_i m_p = n_H m_H X^{-1}$$


```python
mean_mass = Ionization.interpolate_mu

mu = mean_mass(nH = nH,
               temperature = temperature,
               metallicity = metallicity,
               redshift = redshift,
               mode = mode,
               part_type = "all",
               )
mu_e = mean_mass(nH = nH,
               temperature = temperature,
               metallicity = metallicity,
               redshift = redshift,
               mode = mode,
               part_type = "electron",
               )
mu_i = mean_mass(nH = nH,
               temperature = temperature,
               metallicity = metallicity,
               redshift = redshift,
               mode = mode,
               part_type = "ion",
               )
print(f"Mean particle mass = {mu:.2f} mp")
print(f"Mean free electron mass = {mu_e:.2f} mp")
print(f"Mean ion mass = {mu_i:.2f} mp")
```

    Mean particle mass = 0.62 mp
    Mean free electron mass = 1.19 mp
    Mean ion mass = 15.65 mp


### Emission spectrum

`AstroPlasma` can be used in determing the emission spectrum emitted from a *one-zone* plasma. Here's the code that does that. This can be used as a starting point for modeling plasma emission from astrophysical objects like the *circumgalactic medium* or *galaxy clusters* by stacking emission from multiple such one-zones.


```python
# Import AstroPlasma EmissionSpectrum module
from astro_plasma import EmissionSpectrum
```


```python
gen_spectrum = EmissionSpectrum.interpolate_spectrum

# Generate spectrum
spectrum = gen_spectrum(nH = nH,
               temperature = temperature,
               metallicity = metallicity,
               redshift = redshift,
               mode = mode
               )
```

Let us plot the spectrum generated by `AstroPlasma`


```python
import matplotlib
import matplotlib.pyplot as plt

plt.loglog(spectrum[:,0], spectrum[:,1])
plt.xlabel(r"Energy (keV)")
plt.ylabel(r"Emissivity $4 \pi \nu j_{\nu}$ ($erg\ cm^{-3} s^{-1}$)")
plt.xlim(xmin = 1.0e-10, xmax=3.2)
plt.show()
```
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://user-images.githubusercontent.com/39578361/230588683-814f6f71-c74c-4ea1-8c9d-fac36e4cf449.png">
  <img alt="" src="https://user-images.githubusercontent.com/39578361/230584140-22f3b235-e117-4247-8483-afd6e2280d0c.png">
</picture>

> **Note**: `AstroPlasma` assumes by default that the data is located at `<module_location>/data/<ionization/emission>`.
The user can change this to something else by using `Ionization.base_dir = "<new_ionization_data_location_dir>"` or `EmissionSpectrum.base_dir = "<new_emission_data_location_dir>"`, where these new directories must contain the valid `hdf5` data files.

> **Note**: One can also use the `pypoetry` tool to install and create an `in-place` virtual environment for this repo.

> **Note**: We haven't made the server online yet. As a temporary measure, please download and use the data hosted [here](https://indianinstituteofscience-my.sharepoint.com/:f:/g/personal/alankardutta_iisc_ac_in/EhdL9SYY45FOq7zjrWGD0NQBcy3pn6oTP2B9pGhxPwLnkQ?e=E956ug):

```
https://indianinstituteofscience-my.sharepoint.com/:f:/g/personal/alankardutta_iisc_ac_in/EhdL9SYY45FOq7zjrWGD0NQBcy3pn6oTP2B9pGhxPwLnkQ?e=E956ug
```

## Note to contributors

If you wish to contribute, fork this repo and open pull requests to the `dev` branch of this repo. Once everything gets tested and is found working, the new code will be merged with the `master` branch.

For a successful merge, the code must atleast pass all the pre-existing tests. It is recommended to run `pre-commit` locally before pushing your changes to the repo for a proposed PR. To do so just run `pre-commit run --all-files`.

> **Note** It is recommended to install the git pre-commit hook using `pre-commit install` to check all the staged files.
