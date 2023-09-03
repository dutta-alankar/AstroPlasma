from .core.ionization import Ionization as ion
from .core.spectrum import EmissionSpectrum as emm

try:
    Ionization = ion()
except FileNotFoundError:
    print("Ionization data unavailable!")
try:
    EmissionSpectrum = emm()
except FileNotFoundError:
    print("Emission data unavailable!")
