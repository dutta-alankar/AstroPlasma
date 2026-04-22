from .core.ionization import Ionization as ion
from .core.spectrum import EmissionSpectrum as emm
from .core.download_database import download_emission_data, download_ionization_data, download_all, initialize_data, hash_all
from .core.utils import CHECK_OR_DOWNLOAD_APLASMA_DATA

try:
    Ionization = ion()
except (FileNotFoundError,):
    if CHECK_OR_DOWNLOAD_APLASMA_DATA:
        print("Ionization data unavailable!")
        print("Trying to download just one ionization data file for initialization ...")
        initialize_data("ionization")
        try:
            Ionization = ion()
        except Exception as e:
            print("Error downloading ionization file!")
            print(e)
try:
    EmissionSpectrum = emm()
except (FileNotFoundError,):
    if CHECK_OR_DOWNLOAD_APLASMA_DATA:
        print("Emission data unavailable!")
        print("Trying to download just one emission data file for initialization ...")
        initialize_data("emission")
        try:
            EmissionSpectrum = emm()
        except Exception as e:
            print("Error downloading emission file!")
            print(e)
