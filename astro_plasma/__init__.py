import logging
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if os.getenv("ASTRO_PLASMA_DEBUG", "false") == "true" else logging.INFO,
)


from .core import ionization, spectrum  # noqa
from .core.download_database import initialize_data  # noqa


log = logging.getLogger(__name__)

__all__ = ["Ionization", "EmissionSpectrum"]


Ionization = ionization.Ionization()
EmissionSpectrum = spectrum.EmissionSpectrum()
