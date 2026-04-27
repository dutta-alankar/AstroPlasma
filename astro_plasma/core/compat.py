# -*- coding: utf-8 -*-
"""
Numpy/CuPy compatibility shim.

Set the environment variable ``RUN_ON_CUDA=1`` to use CuPy (GPU-accelerated)
instead of NumPy (CPU).  When CuPy is not installed and ``RUN_ON_CUDA=1`` a
``RuntimeWarning`` is emitted and the code falls back to NumPy automatically.

Usage in other modules::

    from .compat import np

All subsequent ``np.*`` calls will then transparently dispatch to either
NumPy or CuPy depending on the runtime flag.

Note
----
``scipy``-dependent code (e.g. ``functions.py``) is intentionally kept on
plain NumPy because SciPy does not accept CuPy arrays.
"""

import warnings

from .utils import RUN_ON_CUDA

if RUN_ON_CUDA:
    try:
        import cupy as np  # type: ignore[import-untyped]

        np.empty(0)  # probe: raises if no CUDA-capable device is present
    except Exception as e:
        warnings.warn(
            f"RUN_ON_CUDA=1 but CuPy is unavailable or no CUDA device detected " f"({type(e).__name__}: {e}). Falling back to numpy.",
            RuntimeWarning,
            stacklevel=2,
        )
        import numpy as np
else:
    import numpy as np

__all__ = ["np"]
