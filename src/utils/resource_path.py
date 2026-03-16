"""
Centralized resource path resolver for dev, PyInstaller, and Nuitka builds.

All paths are relative to src/ (the project source root).
"""

import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller/Nuitka bundle.

    Args:
        relative_path: Path relative to src/ directory (e.g. "gui/themes", "database/migrations")

    Returns:
        Absolute path to the resource.
    """
    if hasattr(sys, "_MEIPASS"):
        # Running from PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    elif "__compiled__" in globals():
        # Running from Nuitka build
        base_path = Path(__file__).parent.parent  # utils -> src
    else:
        # Running from source
        base_path = Path(__file__).parent.parent  # utils -> src
    return base_path / relative_path
