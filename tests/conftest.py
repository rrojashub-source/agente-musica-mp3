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
from unittest.mock import MagicMock

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

# ---------------------------------------------------------------------------
# Snapshot PySide6 mock module dicts IMMEDIATELY after install, before any
# test file can modify them.  Phase-2 GUI test files replace QWidget etc. at
# module-import time; the snapshot lets us restore the originals after each
# such module finishes.
# ---------------------------------------------------------------------------
_PYSIDE6_SNAPSHOT = {}
for _mod_key in ("PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtOpenGLWidgets"):
    _mod = sys.modules.get(_mod_key)
    if _mod is not None:
        _PYSIDE6_SNAPSHOT[_mod_key] = dict(vars(_mod))

import pytest


def restore_pyside6_mocks():
    """Restore PySide6 mock modules to their state right after install().

    Call this in module-scoped fixture teardown of any test file that
    replaces PySide6 classes at module level.
    """
    for mod_key, orig_dict in _PYSIDE6_SNAPSHOT.items():
        mod = sys.modules.get(mod_key)
        if mod is None:
            continue
        # Remove keys that were added after the snapshot
        current_keys = set(vars(mod).keys())
        orig_keys = set(orig_dict.keys())
        for k in current_keys - orig_keys:
            try:
                delattr(mod, k)
            except (AttributeError, TypeError):
                pass
        # Restore original values for keys that existed in the snapshot
        for k, v in orig_dict.items():
            try:
                setattr(mod, k, v)
            except (AttributeError, TypeError):
                pass

    # Restore BaseWorker.is_cancelled property if it was deleted by
    # test_gui_tabs_phase2 at module scope.
    bw_mod = sys.modules.get("gui.base.base_worker")
    if bw_mod is not None:
        bw_cls = getattr(bw_mod, "BaseWorker", None)
        if bw_cls is not None and "is_cancelled" not in bw_cls.__dict__:
            bw_cls.is_cancelled = property(lambda self: self._cancelled)


# ---------------------------------------------------------------------------
# Restore PySide6 mocks before each test MODULE is collected.
# Phase-2 GUI test files modify PySide6.QtWidgets/QtCore/QtGui at module-level
# import time.  Without this hook, a phase-2 file imported earlier during
# collection would contaminate modules imported by later test files.
# ---------------------------------------------------------------------------
_PHASE2_GUI_FILES = {
    "test_gui_base_phase2",
    "test_gui_dialogs_phase2",
    "test_gui_tabs_phase2",
    "test_gui_visualizers_phase2",
    "test_gui_widgets_phase2",
}


_phase2_seen_during_collection = False
_PYSIDE6_CONTAMINATED_SNAPSHOT = {}  # Saved after all phase2 files imported


def _save_contaminated_state():
    """Save current (contaminated) PySide6 state for later re-application."""
    for mod_key in ("PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtOpenGLWidgets"):
        mod = sys.modules.get(mod_key)
        if mod is not None:
            _PYSIDE6_CONTAMINATED_SNAPSHOT[mod_key] = dict(vars(mod))


def _apply_contaminated_state():
    """Re-apply the contaminated PySide6 state (for phase2 test execution)."""
    for mod_key, cont_dict in _PYSIDE6_CONTAMINATED_SNAPSHOT.items():
        mod = sys.modules.get(mod_key)
        if mod is None:
            continue
        current_keys = set(vars(mod).keys())
        cont_keys = set(cont_dict.keys())
        for k in current_keys - cont_keys:
            try:
                delattr(mod, k)
            except (AttributeError, TypeError):
                pass
        for k, v in cont_dict.items():
            try:
                setattr(mod, k, v)
            except (AttributeError, TypeError):
                pass


def pytest_collectstart(collector):
    """Restore PySide6 state before importing non-phase2 test modules.

    Phase-2 GUI test files modify PySide6.QtWidgets/QtCore/QtGui at module-level
    import time.  This hook:
    1. Lets phase2 files accumulate their contamination
    2. After the last phase2 file, saves the contaminated state
    3. Restores clean PySide6 before each non-phase2 module import

    The saved contaminated state is re-applied before phase2 tests run.
    """
    global _phase2_seen_during_collection
    # Only act on Module collectors (test files)
    if type(collector).__name__ != "Module":
        return
    fspath = getattr(collector, "fspath", None)
    if fspath is None:
        return
    name = os.path.splitext(os.path.basename(str(fspath)))[0]
    if name in _PHASE2_GUI_FILES:
        _phase2_seen_during_collection = True
        return
    # Save contaminated state once (after all phase2 files imported)
    if _phase2_seen_during_collection and not _PYSIDE6_CONTAMINATED_SNAPSHOT:
        _save_contaminated_state()
    # Restore before non-phase2 modules (only after phase2 files seen)
    if _phase2_seen_during_collection:
        restore_pyside6_mocks()


_in_phase2_module = False


def pytest_runtest_setup(item):
    """Toggle PySide6 state between contaminated (for phase2) and clean (for others).

    Before phase2 tests: re-apply contaminated state so lazy re-imports work.
    Before non-phase2 tests: restore clean state.
    """
    global _in_phase2_module
    mod_base = item.module.__name__.rsplit(".", 1)[-1]

    if mod_base in _PHASE2_GUI_FILES:
        if not _in_phase2_module:
            _in_phase2_module = True
            if _PYSIDE6_CONTAMINATED_SNAPSHOT:
                _apply_contaminated_state()
    else:
        if _in_phase2_module:
            _in_phase2_module = False
            restore_pyside6_mocks()


# Check if real PySide6 is available (not our mock).
# The mock module's __getattr__ returns MagicMock for any attribute including
# __version__, so we must verify __version__ is a real string.
_HAS_REAL_PYSIDE6 = False
try:
    import PySide6 as _pyside6_check

    if isinstance(getattr(_pyside6_check, "__version__", None), str):
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


_GUI_TEST_PREFIXES = (
    "test_api_settings_dialog",
    "test_base_tab",
    "test_download_integration",
    "test_duplicates_tab",
    "test_e2e_complete_flow",
    "test_e2e_gui",
    "test_keyboard_shortcuts",
    "test_now_playing_widget",
    "test_organize_tab",
    "test_playback_integration",
    "test_playlist_widget",
    "test_production_polish",
    "test_queue_widget",
    "test_rename_tab",
    "test_search_tab",
    "test_search_tab_ui",
    "test_visualizer_widget",
)


def pytest_collection_modifyitems(config, items):
    """Skip GUI-heavy tests when real PySide6 is not available."""
    if _HAS_REAL_PYSIDE6:
        return
    skip_marker = pytest.mark.skip(reason="Requires real PySide6")
    for item in items:
        module_name = item.module.__name__.rsplit(".", 1)[-1]
        if module_name.startswith(_GUI_TEST_PREFIXES):
            item.add_marker(skip_marker)


@pytest.fixture(autouse=True)
def _skip_gui_tests_without_pyside6(request):
    """Auto-skip GUI tests that need real PySide6 when only mock is available."""
    if _HAS_REAL_PYSIDE6:
        return
    # Skip tests that use qapp fixture
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
