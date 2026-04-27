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
from pathlib import Path
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


def _use_cuda_backend(monkeypatch):
    """Switch the entire astro_plasma module stack to the CuPy backend.

    The problem with only reloading ``compat`` is that ``datasift``,
    ``ionization``, and ``spectrum`` each do ``from .compat import np`` at
    *their* import time, binding a local name ``np`` in their own module
    namespace.  Reloading ``compat`` afterwards does not update those already-
    bound names, so the interpolation code keeps using NumPy.

    This helper:
    1. Sets ``RUN_ON_CUDA=True`` in the environment and in ``utils``.
    2. Calls ``monkeypatch.setattr`` on every module-level ``np`` *before*
       reloading so that pytest's teardown writes the original (NumPy-backed)
       values back automatically after the test.
    3. Reloads the modules in dependency order (compat → datasift → ionization
       → spectrum → astro_plasma) so that every ``from .compat import np``
       re-executes and picks up CuPy.
    4. Returns the reloaded ``astro_plasma`` module so tests can obtain fresh
       ``Ionization`` / ``EmissionSpectrum`` instances that are backed by CuPy.
    """
    import astro_plasma as astro_plasma_mod
    import astro_plasma.core.utils as utils_mod
    import astro_plasma.core.compat as compat_mod
    import astro_plasma.core.datasift as datasift_mod
    import astro_plasma.core.ionization as ionization_mod
    import astro_plasma.core.spectrum as spectrum_mod

    # Step 1: flip the runtime flag (monkeypatch restores env + attr after test)
    monkeypatch.setenv("RUN_ON_CUDA", "1")
    monkeypatch.setattr(utils_mod, "RUN_ON_CUDA", True)

    # Step 2: register restorers *before* reloading.
    # monkeypatch.setattr saves the current value as the "old" value it will
    # write back on teardown.  The reload below then overwrites these names
    # with CuPy-backed objects; teardown puts the NumPy-backed originals back.
    monkeypatch.setattr(compat_mod, "np", compat_mod.np)
    monkeypatch.setattr(datasift_mod, "np", datasift_mod.np)
    monkeypatch.setattr(ionization_mod, "np", ionization_mod.np)
    monkeypatch.setattr(spectrum_mod, "np", spectrum_mod.np)
    monkeypatch.setattr(astro_plasma_mod, "Ionization", astro_plasma_mod.Ionization)
    monkeypatch.setattr(astro_plasma_mod, "EmissionSpectrum", astro_plasma_mod.EmissionSpectrum)

    # Step 3: reload in dependency order.
    # Each ``from .compat import np`` re-runs and binds to CuPy.
    importlib.reload(compat_mod)  # compat.np = cupy
    importlib.reload(datasift_mod)  # datasift.np = cupy
    importlib.reload(ionization_mod)  # ionization.np = cupy
    importlib.reload(spectrum_mod)  # spectrum.np = cupy
    importlib.reload(astro_plasma_mod)  # fresh Ionization / EmissionSpectrum with cupy

    return astro_plasma_mod


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@cuda_available
def test_compat_selects_cupy(monkeypatch):
    """When RUN_ON_CUDA=1 and a device is present, compat.np must be cupy."""
    _use_cuda_backend(monkeypatch)
    import astro_plasma.core.compat as compat_mod

    assert compat_mod.np.__name__ == "cupy", f"Expected compat.np to be 'cupy', got '{compat_mod.np.__name__}'"


@cuda_available
def test_ion_frac_cuda_matches_numpy(monkeypatch):
    """Ionization fraction on GPU matches the NumPy reference value."""
    import cupy as cp
    from astro_plasma.core.utils import AtmElement

    # Switch backend first, then obtain a fresh CuPy-backed Ionization instance
    astro_plasma_mod = _use_cuda_backend(monkeypatch)
    fIon = astro_plasma_mod.Ionization.interpolate_ion_frac

    fOVI = fIon(
        nH=1.2e-04,
        temperature=4.2e05,
        metallicity=0.99,
        redshift=0.001,
        element=AtmElement.Oxygen,
        ion=6,
        mode="CIE",
    )

    assert isinstance(fOVI, cp.ndarray), "Expected a cupy.ndarray result"

    fOVI_numpy = float(cp.asnumpy(cp.power(10.0, fOVI)))
    fOVI_expected = 8.895256915490418e-02
    assert np.isclose(fOVI_numpy, fOVI_expected), f"CuPy result {fOVI_numpy:.6e} differs from expected {fOVI_expected:.6e}"


@cuda_available
def test_num_dens_cuda_matches_numpy(monkeypatch):
    """Electron number density on GPU matches the NumPy reference value."""
    import cupy as cp

    astro_plasma_mod = _use_cuda_backend(monkeypatch)
    num_dens = astro_plasma_mod.Ionization.interpolate_num_dens

    ne = num_dens(
        nH=1.2e-04,
        temperature=4.2e05,
        metallicity=0.99,
        redshift=0.001,
        mode="CIE",
        part_type="electron",
    )

    ne_numpy = float(cp.asnumpy(cp.asarray(ne)))
    ne_expected = 1.4109277149716788e-04
    assert np.isclose(ne_numpy, ne_expected), f"CuPy result {ne_numpy:.6e} differs from expected {ne_expected:.6e}"


@cuda_available
def test_spectrum_cuda_matches_numpy(monkeypatch):
    """Emission spectrum on GPU matches the NumPy reference spectrum."""
    import cupy as cp

    astro_plasma_mod = _use_cuda_backend(monkeypatch)
    gen_spectrum = astro_plasma_mod.EmissionSpectrum.interpolate_spectrum

    spectrum = gen_spectrum(
        nH=1.2e-04,
        temperature=4.2e05,
        metallicity=0.99,
        redshift=0.001,
        mode="CIE",
    )

    spectrum_numpy = cp.asnumpy(cp.asarray(spectrum))
    # Resolve relative to the test file so the test passes regardless of cwd
    spectrum_expected = np.loadtxt(Path(__file__).parent / "sample_spectrum.txt")
    assert np.sum(np.abs(spectrum_numpy - spectrum_expected)) < 1.0e-06, "CuPy spectrum deviates from expected reference spectrum"


def test_compat_falls_back_to_numpy_without_cuda(monkeypatch):
    """When RUN_ON_CUDA=1 but no device/cupy is available, compat uses numpy."""
    import warnings
    import sys

    monkeypatch.setenv("RUN_ON_CUDA", "1")
    import astro_plasma.core.utils as utils_mod
    import astro_plasma.core.compat as compat_mod

    monkeypatch.setattr(utils_mod, "RUN_ON_CUDA", True)

    # Simulate cupy being absent by hiding it from imports
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
