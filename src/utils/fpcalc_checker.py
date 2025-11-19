"""
fpcalc Checker - Verify Chromaprint availability

Purpose: Check if fpcalc (Chromaprint) is available for audio fingerprinting
Created: November 18, 2025
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class FpcalcChecker:
    """
    Utility to check fpcalc (Chromaprint) availability

    Checks multiple locations:
    1. Project tools/ directory
    2. System PATH
    3. Common installation paths
    """

    def __init__(self):
        """Initialize fpcalc checker"""
        self.fpcalc_path = None
        self.version = None
        self._locate_fpcalc()

    def _locate_fpcalc(self):
        """
        Locate fpcalc executable

        Priority order:
        1. tools/fpcalc.exe (project directory)
        2. Environment variable FPCALC
        3. System PATH
        4. Common Windows paths
        """
        # Check 1: Project tools directory
        project_root = Path(__file__).parent.parent.parent
        project_fpcalc = project_root / "tools" / "fpcalc.exe"

        if project_fpcalc.exists():
            self.fpcalc_path = str(project_fpcalc)
            logger.info(f"Found fpcalc in project: {self.fpcalc_path}")
            self._get_version()
            return

        # Check 2: Environment variable
        env_fpcalc = os.environ.get('FPCALC')
        if env_fpcalc and Path(env_fpcalc).exists():
            self.fpcalc_path = env_fpcalc
            logger.info(f"Found fpcalc from FPCALC env: {self.fpcalc_path}")
            self._get_version()
            return

        # Check 3: System PATH
        try:
            result = subprocess.run(
                ['fpcalc', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.fpcalc_path = 'fpcalc'  # In PATH
                logger.info("Found fpcalc in system PATH")
                self._get_version()
                return
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Check 4: Common Windows paths
        common_paths = [
            r"C:\Program Files\fpcalc\fpcalc.exe",
            r"C:\Program Files (x86)\fpcalc\fpcalc.exe",
            Path.home() / "fpcalc" / "fpcalc.exe"
        ]

        for path in common_paths:
            if Path(path).exists():
                self.fpcalc_path = str(path)
                logger.info(f"Found fpcalc in common path: {self.fpcalc_path}")
                self._get_version()
                return

        # Not found
        logger.warning("fpcalc not found in any location")
        self.fpcalc_path = None

    def _get_version(self):
        """Get fpcalc version"""
        if not self.fpcalc_path:
            return

        try:
            result = subprocess.run(
                [self.fpcalc_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Output format: "fpcalc version 1.5.1"
                output = result.stdout.strip()
                if 'version' in output:
                    self.version = output.split('version')[-1].strip()
                    logger.info(f"fpcalc version: {self.version}")
        except Exception as e:
            logger.warning(f"Could not get fpcalc version: {e}")

    def is_available(self) -> bool:
        """
        Check if fpcalc is available

        Returns:
            bool: True if fpcalc can be used
        """
        return self.fpcalc_path is not None

    def get_path(self) -> Optional[str]:
        """
        Get fpcalc executable path

        Returns:
            str or None: Path to fpcalc executable
        """
        return self.fpcalc_path

    def get_version(self) -> Optional[str]:
        """
        Get fpcalc version

        Returns:
            str or None: Version string (e.g., "1.5.1")
        """
        return self.version

    def get_install_instructions(self) -> str:
        """
        Get installation instructions for fpcalc

        Returns:
            str: Formatted instructions
        """
        instructions = """
🎵 AcoustID Audio Fingerprinting (fpcalc) Not Found

To enable audio fingerprinting for song identification:

1. Download Chromaprint:
   https://acoustid.org/chromaprint

2. Download this file:
   chromaprint-fpcalc-1.5.1-windows-x86_64.zip

3. Extract and copy fpcalc.exe to ONE of these locations:

   Option A (Recommended): Project directory
   {project_tools}

   Option B: System PATH
   C:\\Program Files\\fpcalc\\fpcalc.exe

   Option C: Set environment variable
   set FPCALC=C:\\path\\to\\fpcalc.exe

4. Restart the application

Benefits of AcoustID:
✨ Identify songs by analyzing audio (like Shazam)
✨ Works even with corrupted/missing metadata
✨ 95-100% accuracy (analyzes actual audio)
✨ Same technology used by MusicBrainz Picard
""".format(
            project_tools=Path(__file__).parent.parent.parent / "tools" / "fpcalc.exe"
        )

        return instructions.strip()

    def check_and_report(self) -> Tuple[bool, str]:
        """
        Check availability and return status message

        Returns:
            Tuple[bool, str]: (is_available, status_message)
        """
        if self.is_available():
            message = f"✅ fpcalc found: {self.fpcalc_path}"
            if self.version:
                message += f" (version {self.version})"
            return True, message
        else:
            return False, self.get_install_instructions()


# Global instance
_checker = None


def get_checker() -> FpcalcChecker:
    """
    Get global fpcalc checker instance

    Returns:
        FpcalcChecker: Global checker instance
    """
    global _checker
    if _checker is None:
        _checker = FpcalcChecker()
    return _checker


def is_fpcalc_available() -> bool:
    """
    Quick check if fpcalc is available

    Returns:
        bool: True if fpcalc can be used
    """
    return get_checker().is_available()


def get_fpcalc_path() -> Optional[str]:
    """
    Get path to fpcalc executable

    Returns:
        str or None: Path to fpcalc
    """
    return get_checker().get_path()
