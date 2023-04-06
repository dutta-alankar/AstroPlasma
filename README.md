![image](https://user-images.githubusercontent.com/39578361/210923881-79133580-b2b7-4e4c-8e0d-dc0b4dd4a691.png)

A Cloudy database with functions to quickly interpolate physical state of astrophysical plasma without detailed Plasma modelling.

[![PyPI](https://img.shields.io/badge/requires-Python%20≥%203.10-blue?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3100/)

<!--- Tests and style --->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://user-images.githubusercontent.com/39578361/230400627-bf897098-c182-4de4-ae79-add645215ad4.png">
  <img alt="" src="https://user-images.githubusercontent.com/39578361/230400616-3b6d7f1a-6520-4a39-b695-c9d99bf214a8.png">
</picture>

## Install


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
