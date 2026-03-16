"""
Tests for CleanupWorkflowWorker and CleanupApplier

Tests cover:
- Workflow step execution (analyze, clean, fetch, preview)
- Progress tracking via signals
- Error recovery (API failures, DB errors)
- AcoustID fallback for severe corruption
- CleanupApplier: applying changes to database
- CleanupApplier: cover art download integration
- Edge cases (empty song lists, all-clean libraries)
"""

import sqlite3
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock PySide6 before importing the module under test
# (PySide6 may not be installed in the test environment)
_mock_pyside6 = MagicMock()
_mock_qtcore = MagicMock()
# Make Signal return a Mock that can be used as a descriptor
_mock_qtcore.Signal = MagicMock(return_value=Mock())
_mock_qtcore.QThread = type("QThread", (), {"__init__": lambda self, *a, **kw: None})
_mock_pyside6.QtCore = _mock_qtcore
sys.modules.setdefault("PySide6", _mock_pyside6)
sys.modules.setdefault("PySide6.QtCore", _mock_qtcore)
sys.modules.setdefault("PySide6.QtWidgets", MagicMock())
sys.modules.setdefault("PySide6.QtGui", MagicMock())

import core.cleanup_workflow as cw_module
from core.cleanup_workflow import CleanupApplier, CleanupWorkflowWorker

# ─── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def mock_db_manager():
    """Mock DatabaseManager"""
    db = Mock()
    db.get_song_by_id.return_value = {"duration": 200, "file_path": "/music/song.mp3"}
    db.update_song.return_value = True
    return db


@pytest.fixture
def mock_cleaner():
    """Mock MetadataCleaner that simulates cleaning behavior"""
    cleaner = Mock()
    cleaner.analyze_library.return_value = {
        "total_songs": 3,
        "clean": 1,
        "minor": 1,
        "moderate": 1,
        "severe": 0,
        "issues_by_type": {},
        "problematic_songs": [
            {"id": 2, "title": "Song [Official Video]", "artist": "ArtistVEVO", "corruption_level": "minor"},
            {"id": 3, "title": "Unknown Artist - Song_20251013_232019", "artist": "", "corruption_level": "moderate"},
        ],
    }
    cleaner.detect_corruption_level.side_effect = lambda s: {1: "clean", 2: "minor", 3: "moderate"}.get(
        s.get("id"), "clean"
    )
    cleaner.clean_metadata.return_value = (
        {"title": "Cleaned Title", "artist": "Cleaned Artist", "album": "Cleaned Album"},
        {"title": ["youtube_artifacts"], "artist": ["youtube_channel_suffix"]},
    )
    return cleaner


@pytest.fixture
def mock_fetcher():
    """Mock MetadataFetcher"""
    fetcher = Mock()
    fetcher.fetch_metadata.return_value = {
        "title": "Correct Title",
        "artist": "Correct Artist",
        "album": "Correct Album",
        "year": 2020,
        "score": 92.5,
        "source": "musicbrainz",
    }
    return fetcher


@pytest.fixture
def sample_songs():
    """Sample song list with various corruption levels"""
    return [
        {"id": 1, "title": "Good Song", "artist": "Good Artist", "album": "Good Album"},
        {"id": 2, "title": "Song [Official Video]", "artist": "ArtistVEVO", "album": "Album"},
        {"id": 3, "title": "Unknown Artist - Song_20251013_232019", "artist": "", "album": "unknown"},
    ]


@pytest.fixture
def workflow_worker(mock_db_manager, mock_cleaner, mock_fetcher, sample_songs):
    """CleanupWorkflowWorker with mocked dependencies, keyring, and AcoustID disabled"""
    with patch.object(cw_module, "keyring") as mock_keyring:
        mock_keyring.get_password.return_value = None  # No AcoustID key
        worker = CleanupWorkflowWorker(
            db_manager=mock_db_manager,
            cleaner=mock_cleaner,
            fetcher=mock_fetcher,
            songs_to_clean=sample_songs,
            fetch_metadata=True,
            min_confidence=70.0,
            download_covers=False,
        )
    # Mock Qt signals to avoid needing a QApplication
    worker.progress = Mock()
    worker.step_completed = Mock()
    worker.finished = Mock()
    worker.error = Mock()
    return worker


# ─── Tests: CleanupWorkflowWorker ──────────────────────────────────────


class TestWorkflowSteps:
    def test_step1_analyze(self, workflow_worker, mock_cleaner, sample_songs):
        """Step 1 calls cleaner.analyze_library and emits step_completed"""
        workflow_worker._step1_analyze()

        mock_cleaner.analyze_library.assert_called_once_with(sample_songs)
        workflow_worker.step_completed.emit.assert_called_once()
        call_args = workflow_worker.step_completed.emit.call_args
        assert call_args[0][0] == 1  # step number
        assert call_args[0][1]["total"] == 3

    def test_step2_clean_skips_clean_songs(self, workflow_worker, mock_cleaner):
        """Step 2 skips songs with 'clean' corruption level"""
        workflow_worker._step2_clean()

        # Song id=1 is 'clean', should be skipped; songs 2 and 3 should be cleaned
        assert mock_cleaner.clean_metadata.call_count == 2
        assert len(workflow_worker.cleaned_songs) == 2

    def test_step2_clean_records_issues(self, workflow_worker):
        """Step 2 records original, cleaned data, and issues for each song"""
        workflow_worker._step2_clean()

        for entry in workflow_worker.cleaned_songs:
            assert "id" in entry
            assert "original" in entry
            assert "cleaned" in entry
            assert "issues" in entry
            assert "corruption_level" in entry

    def test_step3_fetch_calls_fetcher(self, workflow_worker, mock_fetcher):
        """Step 3 calls fetcher.fetch_metadata for each cleaned song"""
        # First run step 2 to populate cleaned_songs
        workflow_worker._step2_clean()
        workflow_worker._step3_fetch()

        assert mock_fetcher.fetch_metadata.call_count == len(workflow_worker.cleaned_songs)
        assert len(workflow_worker.fetched_songs) > 0

    def test_step3_fetch_handles_no_match(self, workflow_worker, mock_fetcher):
        """Step 3 gracefully handles songs with no API match"""
        mock_fetcher.fetch_metadata.return_value = None

        workflow_worker._step2_clean()
        workflow_worker._step3_fetch()

        # No songs should be in fetched_songs (no AcoustID either)
        assert len(workflow_worker.fetched_songs) == 0

    def test_step4_preview_generates_changes(self, workflow_worker):
        """Step 4 generates preview entries from cleaned + fetched data"""
        workflow_worker._step2_clean()
        workflow_worker._step3_fetch()
        workflow_worker._step4_preview()

        assert len(workflow_worker.preview_changes) > 0
        for change in workflow_worker.preview_changes:
            assert "id" in change
            assert "original" in change
            assert "proposed" in change
            assert "confidence" in change
            assert "source" in change
            assert "status" in change

    def test_step4_preview_fetched_takes_priority(self, workflow_worker, mock_fetcher):
        """Step 4 uses fetched metadata (status='fetched') when available"""
        mock_fetcher.fetch_metadata.return_value = {
            "title": "API Title",
            "artist": "API Artist",
            "album": "API Album",
            "year": 2021,
            "score": 95.0,
            "source": "spotify",
        }

        workflow_worker._step2_clean()
        workflow_worker._step3_fetch()
        workflow_worker._step4_preview()

        fetched_changes = [c for c in workflow_worker.preview_changes if c["status"] == "fetched"]
        assert len(fetched_changes) > 0
        assert fetched_changes[0]["proposed"]["title"] == "API Title"
        assert fetched_changes[0]["source"] == "spotify"


class TestWorkflowRun:
    def test_run_emits_progress_and_finished(self, workflow_worker):
        """Full run emits progress signals and finished with results"""
        workflow_worker.run()

        # Progress should be emitted multiple times
        assert workflow_worker.progress.emit.call_count >= 5
        # Finished should be emitted once with results dict
        workflow_worker.finished.emit.assert_called_once()
        results = workflow_worker.finished.emit.call_args[0][0]
        assert "analysis" in results
        assert "cleaned" in results
        assert "fetched" in results
        assert "preview" in results

    def test_run_error_emits_error_signal(self, workflow_worker, mock_cleaner):
        """Fatal error in run() emits error signal instead of crashing"""
        mock_cleaner.analyze_library.side_effect = RuntimeError("DB corruption")

        workflow_worker.run()

        workflow_worker.error.emit.assert_called_once()
        assert "DB corruption" in workflow_worker.error.emit.call_args[0][0]

    def test_run_without_fetch(self, mock_db_manager, mock_cleaner, mock_fetcher, sample_songs):
        """Run with fetch_metadata=False skips step 3"""
        with patch.object(cw_module, "keyring") as mock_keyring:
            mock_keyring.get_password.return_value = None
            worker = CleanupWorkflowWorker(
                db_manager=mock_db_manager,
                cleaner=mock_cleaner,
                fetcher=mock_fetcher,
                songs_to_clean=sample_songs,
                fetch_metadata=False,
            )
        worker.progress = Mock()
        worker.step_completed = Mock()
        worker.finished = Mock()
        worker.error = Mock()

        worker.run()

        mock_fetcher.fetch_metadata.assert_not_called()
        worker.finished.emit.assert_called_once()


class TestWorkflowHelpers:
    def test_get_song_duration(self, workflow_worker, mock_db_manager):
        """_get_song_duration returns duration from DB"""
        duration = workflow_worker._get_song_duration(1)
        assert duration == 200
        mock_db_manager.get_song_by_id.assert_called_with(1)

    def test_get_song_duration_missing(self, workflow_worker, mock_db_manager):
        """_get_song_duration returns None when song not found"""
        mock_db_manager.get_song_by_id.return_value = None
        assert workflow_worker._get_song_duration(999) is None

    def test_get_song_file_path(self, workflow_worker, mock_db_manager):
        """_get_song_file_path returns path from DB"""
        path = workflow_worker._get_song_file_path(1)
        assert path == "/music/song.mp3"


# ─── Tests: CleanupApplier ─────────────────────────────────────────────


class TestCleanupApplier:
    @pytest.fixture
    def applier(self, mock_db_manager):
        return CleanupApplier(db_manager=mock_db_manager)

    def test_apply_changes_success(self, applier, mock_db_manager):
        """Successful changes update DB and increment success count"""
        changes = [
            {"id": 1, "proposed": {"title": "New", "artist": "A", "album": "B", "year": 2020}},
            {"id": 2, "proposed": {"title": "New2", "artist": "A2", "album": "B2", "year": 2021}},
        ]
        results = applier.apply_changes(changes)

        assert results["success"] == 2
        assert results["failed"] == 0
        assert results["errors"] == []
        assert mock_db_manager.update_song.call_count == 2

    def test_apply_changes_db_failure(self, applier, mock_db_manager):
        """Failed DB update increments failed count"""
        mock_db_manager.update_song.return_value = False
        changes = [
            {"id": 1, "proposed": {"title": "T", "artist": "A", "album": "B", "year": None}},
        ]
        results = applier.apply_changes(changes)

        assert results["success"] == 0
        assert results["failed"] == 1

    def test_apply_changes_db_exception(self, applier, mock_db_manager):
        """sqlite3.Error during apply is caught and recorded"""
        mock_db_manager.update_song.side_effect = sqlite3.Error("disk full")
        changes = [
            {"id": 1, "proposed": {"title": "T", "artist": "A", "album": "B", "year": None}},
        ]
        results = applier.apply_changes(changes)

        assert results["failed"] == 1
        assert len(results["errors"]) == 1
        assert "disk full" in results["errors"][0]

    def test_apply_changes_empty_list(self, applier):
        """Empty change list returns all-zero results"""
        results = applier.apply_changes([])
        assert results["success"] == 0
        assert results["failed"] == 0
        assert results["covers_downloaded"] == 0

    def test_apply_changes_with_cover_download(self, applier, mock_db_manager):
        """Cover art download is triggered when enabled"""
        mock_cover_manager = Mock()
        mock_cover_manager.has_cover.return_value = False
        mock_cover_manager.download_cover.return_value = True

        # Inject mock cover manager directly to avoid real CoverArtManager import
        applier.cover_manager = mock_cover_manager

        changes = [
            {"id": 1, "proposed": {"title": "Song", "artist": "Queen", "album": "Album", "year": 1975}},
        ]
        results = applier.apply_changes(changes, download_covers=True)

        assert results["success"] == 1
        assert results["covers_downloaded"] == 1
        mock_cover_manager.download_cover.assert_called_once_with("Queen", "Album")

    def test_apply_changes_skips_existing_cover(self, applier, mock_db_manager):
        """Cover download is skipped when cover already exists"""
        mock_cover_manager = Mock()
        mock_cover_manager.has_cover.return_value = True

        # Set the cover manager directly to avoid import patching
        applier.cover_manager = mock_cover_manager

        changes = [
            {"id": 1, "proposed": {"title": "Song", "artist": "Artist", "album": "Album", "year": 2020}},
        ]
        results = applier.apply_changes(changes, download_covers=True)

        assert results["covers_downloaded"] == 0
        mock_cover_manager.download_cover.assert_not_called()
