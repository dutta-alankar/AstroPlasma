"""
Created on Tue Apr 11 11:09:17 2023

@author: alankar
"""

from typing import Optional, Protocol
from pathlib import Path


# For now this class is redundant, but can be useful later!
class DataDir(Protocol):
    @property
    def base_dir(self: "DataDir"):
        pass


def set_base_dir(DEFAULT_BASE_DIR: Path, base_dir: Optional[Path] = None) -> Path:
    if base_dir is None:
        _base_dir = DEFAULT_BASE_DIR
    else:
        _base_dir = Path(base_dir)

    if not _base_dir.exists():
        _base_dir.mkdir(mode=0o755, parents=True)

    return _base_dir
