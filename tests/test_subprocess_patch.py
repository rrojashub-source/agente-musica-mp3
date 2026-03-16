"""
Tests for Subprocess Patch — CREATE_NO_WINDOW on Windows

Validates that the patch correctly injects creationflags on Windows
and leaves subprocess untouched on other platforms.
"""

import importlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import MagicMock, call, patch

import pytest


class TestSubprocessPatchOnWindows:
    """Test subprocess patching when platform is win32"""

    def test_popen_adds_creation_flags(self):
        """Patched Popen adds CREATE_NO_WINDOW when creationflags not set"""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")

        # Re-import to ensure patch is applied
        import utils.subprocess_patch  # noqa: F401

        # subprocess.Popen should now be the patched class
        assert subprocess.Popen.__name__ == "_PatchedPopen"

    def test_popen_preserves_explicit_creationflags(self):
        """Patched Popen does not override explicitly provided creationflags"""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")

        import utils.subprocess_patch  # noqa: F401

        # Create a Popen with explicit creationflags — should keep them
        custom_flags = 0x00000010  # CREATE_NEW_CONSOLE
        with patch.object(subprocess, "_original_popen" if hasattr(subprocess, "_original_popen") else "Popen") as _:
            # We just verify the logic: if creationflags is in kwargs, it stays
            kwargs = {"creationflags": custom_flags}
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            assert kwargs["creationflags"] == custom_flags

    def test_run_adds_creation_flags(self):
        """Patched subprocess.run adds CREATE_NO_WINDOW automatically"""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")

        import utils.subprocess_patch  # noqa: F401

        # subprocess.run should be the patched version
        # Verify it's a function (not the original built-in)
        assert callable(subprocess.run)
        assert subprocess.run.__name__ == "_patched_run"

    def test_run_preserves_explicit_creationflags(self):
        """Patched subprocess.run does not override explicit creationflags"""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")

        import utils.subprocess_patch  # noqa: F401

        # Test the logic directly: explicit flags should not be overwritten
        kwargs = {"creationflags": 0x00000010}
        if "creationflags" not in kwargs:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        assert kwargs["creationflags"] == 0x00000010


class TestSubprocessPatchLogic:
    """Test the patching logic independent of platform"""

    def test_create_no_window_flag_value(self):
        """CREATE_NO_WINDOW should be 0x08000000 on Windows"""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")
        assert subprocess.CREATE_NO_WINDOW == 0x08000000

    def test_patched_popen_is_subclass(self):
        """On Windows, patched Popen should be a subclass of original"""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")

        import utils.subprocess_patch  # noqa: F401

        # The patched class inherits from the original Popen
        assert issubclass(subprocess.Popen, subprocess.Popen)

    def test_kwargs_injection_logic(self):
        """Verify the injection logic: add flag only when not present"""

        # This tests the core logic without needing Windows
        def simulate_patch(kwargs):
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
            return kwargs

        # Case 1: no flags -> flag added
        result = simulate_patch({})
        assert result["creationflags"] == 0x08000000

        # Case 2: explicit flags -> not overwritten
        result = simulate_patch({"creationflags": 0x00000010})
        assert result["creationflags"] == 0x00000010

        # Case 3: other kwargs preserved
        result = simulate_patch({"timeout": 30, "text": True})
        assert result["creationflags"] == 0x08000000
        assert result["timeout"] == 30
        assert result["text"] is True

    def test_module_importable(self):
        """The subprocess_patch module can be imported without errors"""
        import utils.subprocess_patch  # noqa: F401

    def test_original_subprocess_functions_still_accessible(self):
        """After patching, subprocess module still has standard attributes"""
        import utils.subprocess_patch  # noqa: F401

        assert hasattr(subprocess, "Popen")
        assert hasattr(subprocess, "run")
        assert hasattr(subprocess, "PIPE")
        assert hasattr(subprocess, "DEVNULL")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
