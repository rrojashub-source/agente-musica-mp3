"""
Pytest configuration for AGENTE_MUSICA_MP3 tests
Adds project root to Python path so imports work correctly.

Shared fixtures:
- temp_db: Temporary SQLite database with WAL/SHM cleanup
- temp_music_folder: Temp directory with fake MP3 files
- mock_db_manager: Pre-configured Mock of DatabaseManager
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

# Add project root and src/ to Python path BEFORE any project imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Install PySide6 mock early so test files that import PySide6 at module
# level can be collected even when PySide6 is not installed (CI headless).
import _mock_pyside6

_mock_pyside6.install()

import pytest

# Check if real PySide6 is available (not our mock)
_HAS_REAL_PYSIDE6 = False
try:
    import PySide6 as _pyside6_check

    if hasattr(_pyside6_check, "__version__"):
        _HAS_REAL_PYSIDE6 = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Shared fixture: qapp (QApplication singleton for GUI tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    """
    Ensure a QApplication exists for the entire test session.

    PySide6 requires exactly one QApplication instance.  This fixture is
    session-scoped so it is created once and reused by all GUI tests.
    Skips automatically when PySide6 is not installed (CI headless).
    """
    if not _HAS_REAL_PYSIDE6:
        pytest.skip("PySide6 not available (mock installed)")

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture(autouse=True)
def _skip_gui_tests_without_pyside6(request):
    """Auto-skip GUI tests that need real PySide6 when only mock is available."""
    if _HAS_REAL_PYSIDE6:
        return
    # Skip tests that use qapp fixture or are in GUI-heavy test files
    if "qapp" in request.fixturenames:
        pytest.skip("Requires real PySide6")


# ---------------------------------------------------------------------------
# Shared fixture: temp_db
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_db():
    """
    Create a temporary SQLite database managed by DatabaseManager with proper cleanup.

    Yields a DatabaseManager instance backed by a temp file.
    On teardown, closes the connection and removes .db, -wal, and -shm files.
    """
    from src.database.manager import DatabaseManager

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = DatabaseManager(db_path)
    yield db

    # Proper cleanup: close connection and remove all WAL files
    db.close()

    for ext in ["", "-wal", "-shm"]:
        file_path = db_path + ext
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Shared fixture: temp_music_folder
# ---------------------------------------------------------------------------

# Minimal MP3 frame — valid MPEG audio frame header + padding (silent)
_FAKE_MP3_BYTES = (
    b"\xff\xfb\x90\x00"  # MPEG1 Layer3 128kbps 44100Hz stereo
    + b"\x00" * 413  # Padding to complete frame (417 bytes total)
)


@pytest.fixture
def temp_music_folder(tmp_path):
    """
    Create a temporary directory containing a handful of fake .mp3 files.

    Returns a pathlib.Path to the directory. The directory contains:
        song_01.mp3, song_02.mp3, song_03.mp3

    Each file is a minimal valid-header MP3 frame so that code checking
    file extensions or doing very basic header sniffing will accept them.
    """
    files = ["song_01.mp3", "song_02.mp3", "song_03.mp3"]
    for name in files:
        (tmp_path / name).write_bytes(_FAKE_MP3_BYTES)
    return tmp_path


# ---------------------------------------------------------------------------
# Shared fixture: mock_db_manager
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db_manager():
    """
    Pre-configured Mock of DatabaseManager with common methods stubbed out.

    Default behaviours (override per-test as needed):
        - add_song(data)       -> returns 1
        - get_song_by_id(id)   -> returns a sample song dict
        - get_all_songs()      -> returns a list with one sample song
        - get_song_count()     -> returns 1
        - song_exists(path)    -> returns False
        - update_song(id, upd) -> returns True
        - delete_song(id)      -> returns True
        - search_songs(q)      -> returns []
        - close()              -> None
    """
    sample_song = {
        "id": 1,
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "year": 2024,
        "genre": "Rock",
        "duration": 210,
        "bitrate": 192000,
        "sample_rate": 44100,
        "file_path": "/music/test.mp3",
        "file_size": 5000000,
    }

    mock = MagicMock()
    mock.add_song.return_value = 1
    mock.get_song_by_id.return_value = sample_song.copy()
    mock.get_all_songs.return_value = [sample_song.copy()]
    mock.get_song_count.return_value = 1
    mock.song_exists.return_value = False
    mock.update_song.return_value = True
    mock.delete_song.return_value = True
    mock.search_songs.return_value = []
    mock.close.return_value = None
    return mock
