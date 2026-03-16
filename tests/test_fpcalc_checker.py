"""
Tests for fpcalc Checker — Chromaprint binary detection

All subprocess and filesystem calls are mocked to avoid
requiring fpcalc to be installed on the test machine.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from utils.fpcalc_checker import FpcalcChecker


class TestFpcalcCheckerAvailable:
    """Test behavior when fpcalc IS found"""

    @patch("utils.fpcalc_checker.subprocess.run")
    @patch("utils.fpcalc_checker.Path.exists", return_value=True)
    def test_found_in_project_tools(self, mock_exists, mock_run):
        """fpcalc found in project tools/ directory sets path and is_available"""
        mock_run.return_value = MagicMock(returncode=0, stdout="fpcalc version 1.5.1")
        checker = FpcalcChecker()
        assert checker.is_available() is True
        assert checker.fpcalc_path is not None
        assert "fpcalc" in checker.fpcalc_path.lower() or checker.fpcalc_path == "fpcalc"

    @patch("utils.fpcalc_checker.subprocess.run")
    @patch("utils.fpcalc_checker.Path.exists", return_value=True)
    def test_version_parsed_correctly(self, mock_exists, mock_run):
        """Version string is extracted from 'fpcalc version X.Y.Z' output"""
        mock_run.return_value = MagicMock(returncode=0, stdout="fpcalc version 1.5.1")
        checker = FpcalcChecker()
        assert checker.version == "1.5.1"

    @patch("utils.fpcalc_checker.subprocess.run")
    @patch("utils.fpcalc_checker.Path.exists", return_value=True)
    def test_get_path_returns_path(self, mock_exists, mock_run):
        """get_path() returns the discovered path"""
        mock_run.return_value = MagicMock(returncode=0, stdout="fpcalc version 1.5.1")
        checker = FpcalcChecker()
        assert checker.get_path() is not None

    @patch("utils.fpcalc_checker.subprocess.run")
    @patch("utils.fpcalc_checker.Path.exists", return_value=True)
    def test_check_and_report_available(self, mock_exists, mock_run):
        """check_and_report returns (True, message) when available"""
        mock_run.return_value = MagicMock(returncode=0, stdout="fpcalc version 1.5.1")
        checker = FpcalcChecker()
        available, message = checker.check_and_report()
        assert available is True
        assert "fpcalc" in message.lower() or "fpcalc" in message


class TestFpcalcCheckerMissing:
    """Test behavior when fpcalc is NOT found"""

    @patch("utils.fpcalc_checker.subprocess.run", side_effect=FileNotFoundError)
    @patch("utils.fpcalc_checker.Path.exists", return_value=False)
    def test_not_found_anywhere(self, mock_exists, mock_run):
        """When fpcalc is absent from all locations, is_available is False"""
        checker = FpcalcChecker()
        assert checker.is_available() is False
        assert checker.fpcalc_path is None
        assert checker.version is None

    @patch("utils.fpcalc_checker.subprocess.run", side_effect=FileNotFoundError)
    @patch("utils.fpcalc_checker.Path.exists", return_value=False)
    def test_get_path_returns_none(self, mock_exists, mock_run):
        """get_path() returns None when not found"""
        checker = FpcalcChecker()
        assert checker.get_path() is None

    @patch("utils.fpcalc_checker.subprocess.run", side_effect=FileNotFoundError)
    @patch("utils.fpcalc_checker.Path.exists", return_value=False)
    def test_get_version_returns_none(self, mock_exists, mock_run):
        """get_version() returns None when not found"""
        checker = FpcalcChecker()
        assert checker.get_version() is None

    @patch("utils.fpcalc_checker.subprocess.run", side_effect=FileNotFoundError)
    @patch("utils.fpcalc_checker.Path.exists", return_value=False)
    def test_check_and_report_unavailable(self, mock_exists, mock_run):
        """check_and_report returns (False, instructions) when missing"""
        checker = FpcalcChecker()
        available, message = checker.check_and_report()
        assert available is False
        assert "chromaprint" in message.lower() or "fpcalc" in message.lower()

    @patch("utils.fpcalc_checker.subprocess.run", side_effect=FileNotFoundError)
    @patch("utils.fpcalc_checker.Path.exists", return_value=False)
    def test_install_instructions_contain_url(self, mock_exists, mock_run):
        """Install instructions include the download URL"""
        checker = FpcalcChecker()
        instructions = checker.get_install_instructions()
        assert "acoustid.org" in instructions


class TestFpcalcCheckerEdgeCases:
    """Test edge cases in fpcalc detection"""

    @patch("utils.fpcalc_checker.subprocess.run")
    @patch("utils.fpcalc_checker.Path.exists", return_value=False)
    def test_found_in_system_path(self, mock_exists, mock_run):
        """fpcalc found in system PATH when project tools/ is absent"""
        mock_run.return_value = MagicMock(returncode=0, stdout="fpcalc version 1.4.3")
        checker = FpcalcChecker()
        assert checker.is_available() is True
        assert checker.fpcalc_path == "fpcalc"

    @patch("utils.fpcalc_checker.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="fpcalc", timeout=5))
    @patch("utils.fpcalc_checker.Path.exists", return_value=False)
    def test_subprocess_timeout_handled(self, mock_exists, mock_run):
        """Subprocess timeout is handled gracefully"""
        checker = FpcalcChecker()
        assert checker.is_available() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
