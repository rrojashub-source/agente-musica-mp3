"""
Subprocess Patch - Hide console windows on Windows

This module patches subprocess.Popen to automatically add CREATE_NO_WINDOW
flag on Windows, preventing black terminal windows from flashing.

Must be imported BEFORE any other module that uses subprocess.

Usage:
    import utils.subprocess_patch  # At the very top of main.py

Created: December 18, 2025
"""

import subprocess
import sys
from typing import Any

if sys.platform == "win32":
    # Store original Popen
    _original_popen = subprocess.Popen

    class _PatchedPopen(_original_popen):  # type: ignore[misc]
        """Popen wrapper that hides console window on Windows"""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            # Add CREATE_NO_WINDOW if not explicitly set
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)

    # Replace Popen globally
    subprocess.Popen = _PatchedPopen  # type: ignore[misc]

    # Also patch subprocess.run since it uses Popen internally
    _original_run = subprocess.run

    def _patched_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        """subprocess.run wrapper that hides console window on Windows"""
        if "creationflags" not in kwargs:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return _original_run(*args, **kwargs)

    subprocess.run = _patched_run  # type: ignore[assignment]
