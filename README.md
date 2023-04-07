![image](https://user-images.githubusercontent.com/39578361/210923881-79133580-b2b7-4e4c-8e0d-dc0b4dd4a691.png)

#### A *Cloudy* database with functions to quickly interpolate physical state of astrophysical plasma without detailed Plasma modelling. ####

Running Cloudy models on the fly, escpecially when there are lot of models to run with different parameters can become extremely expensive. `AstroPlasma` aims to provide a workaround by using a library of pre-computed cloudy models to generate most of the common plasma properties for a large range of parameter space by interpolation. Owing to a simple and easy to use interface, `AstroPlasma` also provides an abstraction layer enabling the user to get the plasma properties without worrying much about the details of plasma modelling. We find this extremely useful while building models and predicting observables like column densities in different kinds of astrophysical systems.

[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/dutta-alankar/AstroPlasma)

[![PyPI](https://img.shields.io/badge/requires-Python%20≥%203.10-blue?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3100/)

<!--- Tests and style --->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
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
```
python -m pip install -r requirements.txt
```
At any point later, in order to use AstroPlasma, just activate this virtual environment:
```
source venv/bin/activate
```
# User Guide

## This is a notebook that demonstrates the basic usage of `AstroPlasma`
>  **Info**: A `jupyter-notebook` of this User guide can be found in the `tests` directory.

### Ionization modeling

This is how one would use astro_plasma for calculating ionization state of any typical astrophysical plasma. This would be useful in any modeling that depends on calculating the ionization of the plasma. Determining temperautre from density, calculating the free electron density in the plasma are few such examples where `AstroPlasma` can find application.


```python
# Import AstroPlasma Ionization module
from astro_plasma import Ionization
```

#### Let us calculate ionization fraction of $\bf{OVI\ (O^{5+}})$

In `AstroPlasma` elements are labelled by their atomic number.
- Atomic number of the desired element is passed to the `element` argument in several functions of `AstroPlasma`. For example, Oxygen corresponds to `element=8`.
- For the ionization state, `AstroPlasma` labels them according to the value passed to the `ion` argument. For example, ionization state III, corresponds to `ion=3`.
- Summarizing, to know the ionization state of $\bf{OVI}$, one needs to pass `element=8` and `ion=6`.


```python
fIon = Ionization().interpolate_ion_frac
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
element = 8
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

One can also caluculate other plasma quantities as follows

#### The total free electron density


```python
num_dens = Ionization().interpolate_num_dens

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
num_dens = Ionization().interpolate_num_dens

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
mean_mass = Ionization().interpolate_mu

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
gen_spectrum = EmissionSpectrum().interpolate_spectrum

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

> **Note** Use the pypoetry tool to install directly from the server

<!-- ## Setup

1. Clone the repository

   ```sh
   git clone git@github.com:dutta-alankar/AstroPlasma.git
   cd AstroPlasma
   ```

2. Create and source a virtual environment (recommonded, but optional)

   ```sh
   virtualenv .venv
   source .venv/bin/activate
   ```

3. Upgrade pip and install dependencies

   ```sh
   pip install -U pip
   pip install -r requirements.txt
   ```

   > **Note** If you are maintaining or into development of this repository, please consider using [poetry](https://python-poetry.org/).

4. Configure the environment file in the `.env` if you intent to change the behaviour. Check [Environment Variable Config](#environment-variable-config) for more information.

5. Configure the web server in the `server/` directory and continue the setup instruction as described in the `server/README.md` starting from 3<sup>rd</sup> step.

   > **Note** The `.env` file mentioned in the `server/README.md` file must be created in the `server/.env` file

6. In a separate terminal session, run the webserver. Check out **Getting Started** section in the `server/README.md`

## Getting Started

Once you have performed the steps from the [Setup](#setup), you are good to go.

![](https://i.imgur.com/uaQktlP.png)

> **Note** This is the example usage intended for a quick demo. Do not use it from the python shell, rather import `ionization.py` and `spectrum.py` files in your application.

## Environment Variable Config

|    Variable Name    | Description |
| :-----------------: | :---------- |
|     CHUNK_SIZE      | (_Optional_) Amount of bytes of the file content to be downloaded and saved at a time. It should be adjusted based on the network bandwidth. Default is `4096` (aka 4 kB) |
| WEB_SERVER_BASE_URL | (_Optional_) Base url of the downloader webserver (running from `server/` directory). It should only be set when that server is deployed on some remote web server or the default port is changed. Default is `http://localhost:8000` |
| PARALLEL_DOWNLOAD_JOBS | (_Optional_) Number of file download jobs to run parallely. Default is `3` |  -->

Note: We haven't made the server online yet. As a temporary measure, please download and use the data hosted [here](https://indianinstituteofscience-my.sharepoint.com/:f:/g/personal/alankardutta_iisc_ac_in/EhdL9SYY45FOq7zjrWGD0NQBcy3pn6oTP2B9pGhxPwLnkQ?e=E956ug):

```
https://indianinstituteofscience-my.sharepoint.com/:f:/g/personal/alankardutta_iisc_ac_in/EhdL9SYY45FOq7zjrWGD0NQBcy3pn6oTP2B9pGhxPwLnkQ?e=E956ug
```

## Note to contributors

If you wish to contribute, fork this repo and open pull requests to the `dev` branch of this repo. Once everything gets tested and is found working, the new code will be merged with the `master` branch.

For a successful merge, the code must atleast pass all the pre-existing tests. It is recommended to run `pre-commit` locally before pushing your changes to the repo for a proposed PR. To do so just run `pre-commit run --all-files`.

> **Note** It is recommended to install the git pre-commit hook using `pre-commit install` to check all the staged files.
