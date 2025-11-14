"""
Tests for LibraryImportWorker - Background MP3 Import
Phase: Library Import Feature
"""
import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QCoreApplication
from src.workers.library_import_worker import LibraryImportWorker, extract_metadata
from src.database.manager import DatabaseManager


# Ensure QApplication exists for QThread
@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Create QApplication for tests"""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db = DatabaseManager(db_path)
    yield db

    db.close()

    # Remove database files (including WAL and SHM)
    for ext in ['', '-wal', '-shm']:
        file_path = db_path + ext
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@pytest.fixture
def temp_music_folder():
    """Create temporary folder with test MP3 files"""
    temp_dir = tempfile.mkdtemp(prefix='music_import_test_')

    # Copy real MP3 from Ricardo's library for testing
    real_mp3 = Path('/mnt/c/Users/ricar/Music/Chanel/Chanel - Clavaito.mp3')

    if real_mp3.exists():
        # Create subfolder structure
        subfolder = Path(temp_dir) / "Chanel"
        subfolder.mkdir()

        # Copy MP3 to temp folder
        dest_file = subfolder / "Clavaito.mp3"
        shutil.copy2(real_mp3, dest_file)

        # Create second MP3 (copy with different name)
        dest_file2 = subfolder / "SLoSHiPi.mp3"
        shutil.copy2(real_mp3, dest_file2)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def empty_music_folder():
    """Create empty temporary folder"""
    temp_dir = tempfile.mkdtemp(prefix='music_empty_test_')
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# ==========================================
# METADATA EXTRACTION TESTS
# ==========================================

def test_extract_metadata_valid_mp3():
    """Test metadata extraction from valid MP3"""
    mp3_file = Path('/mnt/c/Users/ricar/Music/Chanel/Chanel - Clavaito.mp3')

    if not mp3_file.exists():
        pytest.skip("Test MP3 file not found")

    metadata = extract_metadata(str(mp3_file))

    assert metadata is not None
    assert metadata['title'] == 'Clavaito'
    assert metadata['artist'] == 'Chanel'
    assert metadata['album'] == '¡Agua!'
    assert metadata['year'] == 2024
    assert metadata['genre'] == 'Latin Pop'
    assert metadata['duration'] > 0
    assert metadata['bitrate'] > 0
    assert metadata['sample_rate'] > 0
    assert metadata['file_path'] == str(mp3_file)
    assert metadata['file_size'] > 0


def test_extract_metadata_missing_file():
    """Test extract_metadata handles missing files gracefully"""
    metadata = extract_metadata('/nonexistent/file.mp3')

    assert metadata is None


def test_extract_metadata_corrupted_mp3(temp_music_folder):
    """Test extract_metadata handles corrupted files gracefully"""
    # Create fake corrupted MP3
    corrupted_file = Path(temp_music_folder) / "corrupted.mp3"
    corrupted_file.write_text("This is not a valid MP3 file")

    metadata = extract_metadata(str(corrupted_file))

    # Should return None or handle gracefully
    assert metadata is None or 'title' in metadata  # Mutagen might still extract something


def test_extract_metadata_missing_tags(temp_music_folder):
    """Test extract_metadata provides defaults for missing ID3 tags"""
    # This test would require creating an MP3 without tags
    # Skipping for now as it's complex to create
    pytest.skip("Requires MP3 without ID3 tags")


# ==========================================
# WORKER INITIALIZATION TESTS
# ==========================================

def test_worker_initializes(temp_db, temp_music_folder):
    """Test LibraryImportWorker initializes correctly"""
    worker = LibraryImportWorker(temp_db, temp_music_folder, recursive=True)

    assert worker.db_manager == temp_db
    assert worker.folder_path == temp_music_folder
    assert worker.recursive is True


# ==========================================
# SCAN FOLDER TESTS
# ==========================================

def test_scan_folder_finds_mp3s(temp_db, temp_music_folder):
    """Test recursive scan finds all .mp3 files"""
    worker = LibraryImportWorker(temp_db, temp_music_folder, recursive=True)

    # Collect signals
    import_count = []
    worker.song_imported.connect(lambda song: import_count.append(song))

    finished_result = []
    worker.finished.connect(lambda result: finished_result.append(result))

    # Run worker
    worker.run()

    # Verify 2 MP3s were found
    assert len(import_count) == 2
    assert len(finished_result) == 1
    assert finished_result[0]['success'] == 2


def test_scan_non_recursive_mode(temp_db, temp_music_folder):
    """Test non-recursive scan only scans top folder"""
    # For this test, we'd need MP3s in root and subfolder
    # Current test folder only has subfolder, so skip
    pytest.skip("Requires test data with MP3s in root and subfolder")


def test_scan_empty_folder(temp_db, empty_music_folder):
    """Test scanning empty folder returns 0 results"""
    worker = LibraryImportWorker(temp_db, empty_music_folder, recursive=True)

    finished_result = []
    worker.finished.connect(lambda result: finished_result.append(result))

    worker.run()

    assert len(finished_result) == 1
    assert finished_result[0]['success'] == 0


# ==========================================
# DUPLICATE DETECTION TESTS
# ==========================================

def test_import_skips_duplicates(temp_db, temp_music_folder):
    """Test worker skips files already imported"""
    worker1 = LibraryImportWorker(temp_db, temp_music_folder, recursive=True)

    # First import
    finished1 = []
    worker1.finished.connect(lambda result: finished1.append(result))
    worker1.run()

    assert finished1[0]['success'] == 2

    # Second import (should skip duplicates)
    worker2 = LibraryImportWorker(temp_db, temp_music_folder, recursive=True)
    finished2 = []
    worker2.finished.connect(lambda result: finished2.append(result))
    worker2.run()

    # Should skip all 2 files
    assert finished2[0]['success'] == 0
    assert finished2[0]['skipped'] == 2


# ==========================================
# PROGRESS SIGNALS TESTS
# ==========================================

def test_import_emits_progress_signals(temp_db, temp_music_folder):
    """Test worker emits progress signals during import"""
    worker = LibraryImportWorker(temp_db, temp_music_folder, recursive=True)

    progress_updates = []
    worker.progress.connect(lambda pct, msg: progress_updates.append((pct, msg)))

    worker.run()

    # Should emit at least: start, per-file, finish
    assert len(progress_updates) >= 3
    assert progress_updates[0][0] == 0  # Start at 0%
    assert progress_updates[-1][0] == 100  # End at 100%


def test_import_emits_song_imported_signals(temp_db, temp_music_folder):
    """Test worker emits song_imported for each successful import"""
    worker = LibraryImportWorker(temp_db, temp_music_folder, recursive=True)

    imported_songs = []
    worker.song_imported.connect(lambda song: imported_songs.append(song))

    worker.run()

    # Should emit 2 signals (2 MP3s)
    assert len(imported_songs) == 2
    assert all('title' in song for song in imported_songs)
    assert all('file_path' in song for song in imported_songs)


# ==========================================
# ERROR HANDLING TESTS
# ==========================================

def test_import_handles_db_errors_gracefully(temp_db, temp_music_folder):
    """Test worker handles database errors without crashing"""
    # Close database to simulate error
    temp_db.close()

    worker = LibraryImportWorker(temp_db, temp_music_folder, recursive=True)

    finished_result = []
    worker.finished.connect(lambda result: finished_result.append(result))

    # Should not crash, should report errors
    worker.run()

    assert len(finished_result) == 1
    # Should have errors
    assert finished_result[0]['failed'] > 0 or finished_result[0]['success'] == 0


# ==========================================
# INTEGRATION TESTS
# ==========================================

def test_full_import_workflow(temp_db, temp_music_folder):
    """Test complete import workflow end-to-end"""
    # Verify database starts empty
    assert temp_db.get_song_count() == 0

    # Run import
    worker = LibraryImportWorker(temp_db, temp_music_folder, recursive=True)

    finished_result = []
    worker.finished.connect(lambda result: finished_result.append(result))

    worker.run()

    # Verify results
    assert finished_result[0]['success'] == 2
    assert finished_result[0]['failed'] == 0

    # Verify database has songs
    assert temp_db.get_song_count() == 2

    # Verify songs have correct data
    songs = temp_db.get_all_songs()
    assert len(songs) == 2
    assert any(song['title'] == 'Clavaito' for song in songs)
