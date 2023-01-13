![image](https://user-images.githubusercontent.com/39578361/210923881-79133580-b2b7-4e4c-8e0d-dc0b4dd4a691.png)

A Cloudy database with functions to quickly interpolate physical state of astrophysical plasma without detailed Plasma modelling.

## Setup

1. Clone the repository

   ```sh
   git clone git@github.com:dutta-alankar/AstroPlasma.git --recurse-submodules
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

|    Variable Name    | Description                                                                                                                                                                                                                          |
| :-----------------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|     CHUNK_SIZE      | (_Optional_) Amount of bytes of the file content to be downloaded and saved at a time. It should be adjusted based on the network bandwidth. Default is `4096` (aka 4 kB)                                                            |
| WEB_SERVER_BASE_URL | (_Optional_) Base url of the downloader webserver (running from `server/` directory). It should only be set when that server is deployed on some remote web server or the default port is changed.Default is `http://localhost:8000` |
