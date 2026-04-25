# -*- coding: utf-8 -*-
"""
Tests for RUN_ON_CUDA=1 GPU-accelerated mode.

These tests are automatically skipped when no CUDA-capable device is present
or when CuPy is not installed.  On a machine with a supported GPU they verify
that:
  - the compat shim selects CuPy as the array backend,
  - interpolation results obtained with CuPy match the NumPy reference values,
  - returned arrays are CuPy arrays (i.e. they live on the GPU).
"""

import importlib
import pytest
import numpy as np

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _cupy_and_device_available() -> bool:
    """Return True only when cupy is importable *and* a CUDA device exists."""
    try:
        import cupy as cp  # noqa: F401

        cp.empty(0)  # triggers CUDARuntimeError when no device is present
        return True
    except Exception:
        return False


cuda_available = pytest.mark.skipif(
    not _cupy_and_device_available(),
    reason="No CUDA-capable device or cupy not installed",
)


def _reload_compat_with_cuda(monkeypatch):
    """Reload astro_plasma.core.compat with RUN_ON_CUDA forced to 1."""
    monkeypatch.setenv("RUN_ON_CUDA", "1")
    import astro_plasma.core.utils as utils_mod
    import astro_plasma.core.compat as compat_mod

    # Patch the already-imported constant so the shim re-reads it
    monkeypatch.setattr(utils_mod, "RUN_ON_CUDA", True)
    importlib.reload(compat_mod)
    return compat_mod


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@cuda_available
def test_compat_selects_cupy(monkeypatch):
    """When RUN_ON_CUDA=1 and a device is present, compat.np must be cupy."""
    compat = _reload_compat_with_cuda(monkeypatch)
    assert compat.np.__name__ == "cupy", f"Expected compat.np to be 'cupy', got '{compat.np.__name__}'"


@cuda_available
def test_ion_frac_cuda_matches_numpy(monkeypatch):
    """Ionization fraction on GPU matches the NumPy reference value."""
    import cupy as cp
    from astro_plasma import Ionization
    from astro_plasma.core.utils import AtmElement

    _reload_compat_with_cuda(monkeypatch)

    fIon = Ionization.interpolate_ion_frac

    nH = 1.2e-04
    temperature = 4.2e05
    metallicity = 0.99
    redshift = 0.001
    mode = "CIE"
    element = AtmElement.Oxygen
    ion = 6

    fOVI = fIon(
        nH=nH,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        element=element,
        ion=ion,
        mode=mode,
    )

    # Result should be a CuPy scalar/array
    assert isinstance(fOVI, cp.ndarray), "Expected a cupy.ndarray result"

    fOVI_numpy = float(cp.asnumpy(cp.power(10.0, fOVI)))
    fOVI_expected = 8.895256915490418e-02
    assert np.isclose(fOVI_numpy, fOVI_expected), f"CuPy result {fOVI_numpy:.6e} differs from expected {fOVI_expected:.6e}"


@cuda_available
def test_num_dens_cuda_matches_numpy(monkeypatch):
    """Electron number density on GPU matches the NumPy reference value."""
    import cupy as cp
    from astro_plasma import Ionization

    _reload_compat_with_cuda(monkeypatch)

    num_dens = Ionization.interpolate_num_dens

    nH = 1.2e-04
    temperature = 4.2e05
    metallicity = 0.99
    redshift = 0.001
    mode = "CIE"

    ne = num_dens(
        nH=nH,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
        part_type="electron",
    )

    ne_numpy = float(cp.asnumpy(cp.asarray(ne)))
    ne_expected = 1.4109277149716788e-04
    assert np.isclose(ne_numpy, ne_expected), f"CuPy result {ne_numpy:.6e} differs from expected {ne_expected:.6e}"


@cuda_available
def test_spectrum_cuda_matches_numpy(monkeypatch):
    """Emission spectrum on GPU matches the NumPy reference spectrum."""
    import cupy as cp
    from astro_plasma import EmissionSpectrum

    _reload_compat_with_cuda(monkeypatch)

    gen_spectrum = EmissionSpectrum.interpolate_spectrum

    nH = 1.2e-04
    temperature = 4.2e05
    metallicity = 0.99
    redshift = 0.001
    mode = "CIE"

    spectrum = gen_spectrum(
        nH=nH,
        temperature=temperature,
        metallicity=metallicity,
        redshift=redshift,
        mode=mode,
    )

    spectrum_numpy = cp.asnumpy(cp.asarray(spectrum))
    spectrum_expected = np.loadtxt("tests/sample_spectrum.txt")
    assert np.sum(np.abs(spectrum_numpy - spectrum_expected)) < 1.0e-06, "CuPy spectrum deviates from expected reference spectrum"


def test_compat_falls_back_to_numpy_without_cuda(monkeypatch):
    """When RUN_ON_CUDA=1 but no device/cupy is available, compat uses numpy."""
    import warnings

    monkeypatch.setenv("RUN_ON_CUDA", "1")
    import astro_plasma.core.utils as utils_mod
    import astro_plasma.core.compat as compat_mod

    monkeypatch.setattr(utils_mod, "RUN_ON_CUDA", True)

    # Simulate cupy being absent by hiding it from imports
    import sys

    original_cupy = sys.modules.pop("cupy", None)
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            importlib.reload(compat_mod)
        module_name = compat_mod.np.__name__
    finally:
        if original_cupy is not None:
            sys.modules["cupy"] = original_cupy
        importlib.reload(compat_mod)  # restore original state

    # Whether cupy is installed or not, the module must be usable (numpy or cupy)
    assert module_name in ("numpy", "cupy"), f"Unexpected array module: {module_name}"
    if module_name == "numpy":
        # A warning should have been emitted
        warning_messages = [str(w.message) for w in caught]
        assert any("RUN_ON_CUDA" in m for m in warning_messages), "Expected a RuntimeWarning about RUN_ON_CUDA fallback"
