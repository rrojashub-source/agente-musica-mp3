"""
Phase 2 coverage tests for src/workers/

Covers:
- extract_metadata: all paths (valid, missing file, corrupt, Unknown title fallback, year parse error)
- LibraryImportWorker: __init__, do_work, _scan_folder, _process_file (all branches)
- DownloadWorker: path validation branches, progress_hook estimate branch, do_work paths

NOTE: QApplication created at module level (not via qapp fixture)
to avoid conftest auto-skip.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure src/ on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

# Create QApplication at module level (not as fixture to avoid conftest skip)
_app = QApplication.instance()
if _app is None:
    _app = QApplication(sys.argv)

from workers.download_worker import DownloadWorker  # noqa: E402
from workers.library_import_worker import LibraryImportWorker, extract_metadata  # noqa: E402

# ==========================================
# Helper: create valid MP3 with ID3 tags
# ==========================================


def _create_test_mp3(
    path: Path,
    title: str = "Test Song",
    artist: str = "Test Artist",
    album: str = "Test Album",
    year: str = "2024",
    genre: str = "Pop",
) -> None:
    """Create a minimal valid MP3 file with ID3 tags."""
    from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1

    frame_header = b"\xff\xfb\x90\x04"
    frame_size = 417
    silence = b"\x00" * (frame_size - len(frame_header))
    frames = (frame_header + silence) * 115  # ~3 seconds

    path.write_bytes(frames)

    tags = ID3()
    tags.add(TIT2(encoding=3, text=[title]))
    tags.add(TPE1(encoding=3, text=[artist]))
    tags.add(TALB(encoding=3, text=[album]))
    tags.add(TDRC(encoding=3, text=[year]))
    tags.add(TCON(encoding=3, text=[genre]))
    tags.save(str(path))


def _create_mp3_no_title(path: Path) -> None:
    """Create MP3 with title='Unknown' to trigger filename fallback."""
    from mutagen.id3 import ID3, TIT2, TPE1

    frame_header = b"\xff\xfb\x90\x04"
    frame_size = 417
    silence = b"\x00" * (frame_size - len(frame_header))
    frames = (frame_header + silence) * 50

    path.write_bytes(frames)

    tags = ID3()
    tags.add(TIT2(encoding=3, text=["Unknown"]))
    tags.add(TPE1(encoding=3, text=["Some Artist"]))
    tags.save(str(path))


def _create_mp3_bad_year(path: Path) -> None:
    """Create MP3 with unparseable year tag."""
    from mutagen.id3 import ID3, TDRC, TIT2, TPE1

    frame_header = b"\xff\xfb\x90\x04"
    frame_size = 417
    silence = b"\x00" * (frame_size - len(frame_header))
    frames = (frame_header + silence) * 50

    path.write_bytes(frames)

    tags = ID3()
    tags.add(TIT2(encoding=3, text=["Good Title"]))
    tags.add(TPE1(encoding=3, text=["Good Artist"]))
    tags.add(TDRC(encoding=3, text=["XXXX"]))
    tags.save(str(path))


# ==========================================
# extract_metadata tests
# ==========================================


class TestExtractMetadata:
    """Cover extract_metadata function (lines 53-103)."""

    def test_valid_mp3(self, tmp_path) -> None:
        """Extract metadata from valid MP3 with all tags."""
        mp3 = tmp_path / "song.mp3"
        _create_test_mp3(mp3, title="Hello", artist="Adele", album="25", year="2015", genre="Pop")

        meta = extract_metadata(str(mp3))
        assert meta is not None
        assert meta["title"] == "Hello"
        assert meta["artist"] == "Adele"
        assert meta["album"] == "25"
        assert meta["year"] == 2015
        assert meta["genre"] == "Pop"
        assert meta["duration"] > 0
        assert meta["bitrate"] > 0
        assert meta["sample_rate"] > 0
        assert meta["file_size"] > 0
        assert meta["file_path"] == str(mp3.resolve())

    def test_missing_file(self) -> None:
        """Returns None for non-existent file."""
        result = extract_metadata("/nonexistent/file.mp3")
        assert result is None

    def test_corrupt_file(self, tmp_path) -> None:
        """Returns None for corrupt/invalid file."""
        bad = tmp_path / "bad.mp3"
        bad.write_text("not an mp3")

        with patch("mutagen.mp3.MP3", side_effect=ValueError("invalid")):
            result = extract_metadata(str(bad))
        assert result is None

    def test_unknown_title_uses_filename(self, tmp_path) -> None:
        """When title is 'Unknown', uses filename stem as fallback."""
        mp3 = tmp_path / "my_cool_song.mp3"
        _create_mp3_no_title(mp3)

        meta = extract_metadata(str(mp3))
        assert meta is not None
        assert meta["title"] == "my_cool_song"

    def test_bad_year_gracefully_handled(self, tmp_path) -> None:
        """Unparseable TDRC year tag doesn't crash."""
        mp3 = tmp_path / "badyear.mp3"
        _create_mp3_bad_year(mp3)

        meta = extract_metadata(str(mp3))
        assert meta is not None
        assert meta["title"] == "Good Title"
        assert meta["year"] is None  # year parsing failed

    def test_os_error_returns_none(self, tmp_path) -> None:
        """OSError during extraction returns None."""
        mp3 = tmp_path / "oserror.mp3"
        _create_test_mp3(mp3)

        with patch("mutagen.mp3.MP3", side_effect=OSError("disk error")):
            result = extract_metadata(str(mp3))
        assert result is None


# ==========================================
# LibraryImportWorker tests
# ==========================================


@pytest.fixture
def mock_db():
    """Mock DatabaseManager for worker tests."""
    db = MagicMock()
    db.song_exists.return_value = False
    db.find_by_metadata.return_value = None
    db.add_song.return_value = 1
    return db


@pytest.fixture
def music_folder(tmp_path):
    """Folder with 2 valid MP3 files in a subfolder."""
    sub = tmp_path / "artist"
    sub.mkdir()
    _create_test_mp3(sub / "song1.mp3", title="Song One", artist="Artist A")
    _create_test_mp3(sub / "song2.mp3", title="Song Two", artist="Artist B")
    return tmp_path


class TestLibraryImportWorkerInit:
    """Cover __init__ (lines 136-146)."""

    def test_init_sets_attributes(self, mock_db) -> None:
        worker = LibraryImportWorker(mock_db, "/some/path", recursive=False, max_duration=600)
        assert worker.db_manager is mock_db
        assert worker.folder_path == "/some/path"
        assert worker.recursive is False
        assert worker.max_duration == 600
        assert worker.success_count == 0
        assert worker.failed_count == 0
        assert worker.skipped_count == 0
        assert worker.errors == []


class TestScanFolder:
    """Cover _scan_folder (lines 211-226)."""

    def test_recursive_scan(self, mock_db, music_folder) -> None:
        worker = LibraryImportWorker(mock_db, str(music_folder), recursive=True)
        files = worker._scan_folder()
        assert len(files) == 2
        assert all(f.endswith(".mp3") for f in files)

    def test_non_recursive_scan(self, mock_db, music_folder) -> None:
        """Non-recursive skips subfolder files."""
        worker = LibraryImportWorker(mock_db, str(music_folder), recursive=False)
        files = worker._scan_folder()
        assert len(files) == 0  # MP3s are in subfolder

    def test_nonexistent_folder(self, mock_db) -> None:
        worker = LibraryImportWorker(mock_db, "/nonexistent/folder")
        files = worker._scan_folder()
        assert files == []


class TestDoWork:
    """Cover do_work (lines 161-202)."""

    def test_empty_folder(self, mock_db, tmp_path) -> None:
        """Empty folder returns zero summary."""
        worker = LibraryImportWorker(mock_db, str(tmp_path))
        finished = []
        worker.finished.connect(lambda r: finished.append(r))
        worker.run()

        assert len(finished) == 1
        assert finished[0]["success"] == 0
        assert finished[0]["failed"] == 0
        assert finished[0]["skipped"] == 0

    def test_successful_import(self, mock_db, music_folder) -> None:
        """Import 2 valid MP3s successfully."""
        worker = LibraryImportWorker(mock_db, str(music_folder))
        finished = []
        worker.finished.connect(lambda r: finished.append(r))
        imported = []
        worker.song_imported.connect(lambda s: imported.append(s))

        worker.run()

        assert finished[0]["success"] == 2
        assert finished[0]["failed"] == 0
        assert len(imported) == 2

    def test_progress_signals(self, mock_db, music_folder) -> None:
        """Progress starts at 0 and ends at 100."""
        worker = LibraryImportWorker(mock_db, str(music_folder))
        progress = []
        worker.progress.connect(lambda p, m: progress.append((p, m)))

        worker.run()

        assert progress[0][0] == 0
        assert progress[-1][0] == 100

    def test_process_file_exception(self, mock_db, music_folder) -> None:
        """OSError in _process_file is caught and counted as failed."""
        worker = LibraryImportWorker(mock_db, str(music_folder))

        with patch.object(worker, "_process_file", side_effect=OSError("disk error")):
            finished = []
            worker.finished.connect(lambda r: finished.append(r))
            worker.run()

        assert finished[0]["failed"] == 2
        assert len(finished[0]["errors"]) == 2


class TestProcessFile:
    """Cover _process_file (lines 248-311) — all branches."""

    def test_skip_duplicate_by_path(self, mock_db, music_folder) -> None:
        """Level 1: skip if song_exists returns True."""
        mock_db.song_exists.return_value = True
        worker = LibraryImportWorker(mock_db, str(music_folder))

        finished = []
        worker.finished.connect(lambda r: finished.append(r))
        worker.run()

        assert finished[0]["skipped"] == 2
        assert finished[0]["success"] == 0

    def test_metadata_extraction_fails(self, mock_db, music_folder) -> None:
        """When extract_metadata returns None, count as failed."""
        worker = LibraryImportWorker(mock_db, str(music_folder))

        with patch("workers.library_import_worker.extract_metadata", return_value=None):
            finished = []
            worker.finished.connect(lambda r: finished.append(r))
            worker.run()

        assert finished[0]["failed"] == 2

    def test_skip_long_duration(self, mock_db, music_folder) -> None:
        """Songs exceeding max_duration are skipped."""
        worker = LibraryImportWorker(mock_db, str(music_folder), max_duration=1)

        finished = []
        worker.finished.connect(lambda r: finished.append(r))
        worker.run()

        # MP3s are ~3s which exceeds max_duration=1
        assert finished[0]["skipped"] == 2

    def test_moved_file_updates_path(self, mock_db, music_folder) -> None:
        """Level 2: existing match by metadata → update path, count as skipped."""
        mock_db.find_by_metadata.return_value = {"id": 42, "file_path": "/old/path.mp3"}

        worker = LibraryImportWorker(mock_db, str(music_folder))
        finished = []
        worker.finished.connect(lambda r: finished.append(r))
        worker.run()

        assert finished[0]["skipped"] == 2
        assert mock_db.update_song_path.call_count == 2

    def test_db_insert_fails(self, mock_db, music_folder) -> None:
        """Level 3: add_song returns None → count as failed."""
        mock_db.add_song.return_value = None

        worker = LibraryImportWorker(mock_db, str(music_folder))
        finished = []
        worker.finished.connect(lambda r: finished.append(r))
        worker.run()

        assert finished[0]["failed"] == 2

    def test_path_normalize_error(self, mock_db) -> None:
        """OSError in Path.resolve() during normalization → count as failed."""
        worker = LibraryImportWorker(mock_db, "/fake")

        with patch("workers.library_import_worker.Path.resolve", side_effect=OSError("bad path")):
            worker._process_file("/some/file.mp3")

        assert worker.failed_count == 1

    def test_successful_insert(self, mock_db, music_folder) -> None:
        """Level 3: truly new song → add to DB, emit song_imported."""
        mock_db.add_song.return_value = 42

        worker = LibraryImportWorker(mock_db, str(music_folder))
        imported = []
        worker.song_imported.connect(lambda s: imported.append(s))
        finished = []
        worker.finished.connect(lambda r: finished.append(r))
        worker.run()

        assert finished[0]["success"] == 2
        assert len(imported) == 2
        assert all(s["id"] == 42 for s in imported)


# ==========================================
# DownloadWorker tests — uncovered paths
# ==========================================


class TestDownloadWorkerPathValidation:
    """Cover path validation branches (lines 71-87)."""

    def test_invalid_path_with_allowed_base_dir(self, tmp_path) -> None:
        """ValueError raised when path escapes allowed_base_dir."""
        with pytest.raises(ValueError, match="Invalid output path"):
            DownloadWorker(
                "https://youtube.com/watch?v=test",
                str(tmp_path / ".." / ".." / "etc" / "passwd.mp3"),
                allowed_base_dir=str(tmp_path),
            )

    def test_valid_path_with_allowed_base_dir(self, tmp_path) -> None:
        """Accepts path within allowed_base_dir."""
        worker = DownloadWorker(
            "https://youtube.com/watch?v=test",
            str(tmp_path / "song.mp3"),
            allowed_base_dir=str(tmp_path),
        )
        assert worker.output_path == str((tmp_path / "song.mp3").resolve())

    def test_no_base_dir_validates_against_defaults(self, tmp_path) -> None:
        """Without allowed_base_dir, validates against ALLOWED_BASE_DIRS."""
        # Path outside all allowed dirs → ValueError
        with pytest.raises(ValueError, match="outside all allowed"):
            DownloadWorker(
                "https://youtube.com/watch?v=test",
                "/tmp/totally_random_path_xyz/song.mp3",
            )


class TestDownloadWorkerProgressHook:
    """Cover _progress_hook branches (lines 166-178)."""

    def test_progress_with_total_bytes(self, tmp_path) -> None:
        """Progress calculated from total_bytes."""
        worker = DownloadWorker(
            "https://youtube.com/watch?v=test",
            str(tmp_path / "song.mp3"),
            allowed_base_dir=str(tmp_path),
        )
        progress_vals = []
        worker.progress.connect(lambda v: progress_vals.append(v))

        worker._progress_hook(
            {
                "status": "downloading",
                "downloaded_bytes": 50,
                "total_bytes": 100,
            }
        )
        assert progress_vals == [50]

    def test_progress_with_total_bytes_estimate(self, tmp_path) -> None:
        """Fallback to total_bytes_estimate when total_bytes absent."""
        worker = DownloadWorker(
            "https://youtube.com/watch?v=test",
            str(tmp_path / "song.mp3"),
            allowed_base_dir=str(tmp_path),
        )
        progress_vals = []
        worker.progress.connect(lambda v: progress_vals.append(v))

        worker._progress_hook(
            {
                "status": "downloading",
                "downloaded_bytes": 75,
                "total_bytes_estimate": 100,
            }
        )
        assert progress_vals == [75]

    def test_progress_finished_status(self, tmp_path) -> None:
        """Finished status emits 100%."""
        worker = DownloadWorker(
            "https://youtube.com/watch?v=test",
            str(tmp_path / "song.mp3"),
            allowed_base_dir=str(tmp_path),
        )
        progress_vals = []
        worker.progress.connect(lambda v: progress_vals.append(v))

        worker._progress_hook({"status": "finished"})
        assert progress_vals == [100]


class TestDownloadWorkerDoWork:
    """Cover do_work paths (lines 108-157)."""

    def test_do_work_with_requested_downloads(self, tmp_path) -> None:
        """do_work uses requested_downloads[0].filepath when available."""
        worker = DownloadWorker(
            "https://youtube.com/watch?v=test",
            str(tmp_path / "song.mp3"),
            allowed_base_dir=str(tmp_path),
        )

        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 200,
            "upload_date": "20250101",
            "requested_downloads": [{"filepath": str(tmp_path / "final.mp3")}],
        }

        with patch("yt_dlp.YoutubeDL") as mock_ytdl:
            mock_instance = MagicMock()
            mock_ytdl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = mock_info

            finished = []
            worker.finished.connect(lambda r: finished.append(r))
            worker.run()

        assert len(finished) == 1
        assert finished[0]["output_path"] == str(tmp_path / "final.mp3")

    def test_do_work_fallback_prepare_filename(self, tmp_path) -> None:
        """do_work falls back to prepare_filename when requested_downloads absent."""
        worker = DownloadWorker(
            "https://youtube.com/watch?v=test",
            str(tmp_path / "song.mp3"),
            allowed_base_dir=str(tmp_path),
        )

        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 200,
            "upload_date": None,
        }

        with patch("yt_dlp.YoutubeDL") as mock_ytdl:
            mock_instance = MagicMock()
            mock_ytdl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = mock_info
            mock_instance.prepare_filename.return_value = str(tmp_path / "song.webm")

            finished = []
            worker.finished.connect(lambda r: finished.append(r))
            worker.run()

        assert len(finished) == 1
        # webm → mp3 extension replacement
        assert finished[0]["output_path"].endswith(".mp3")

    def test_do_work_prepare_filename_already_mp3(self, tmp_path) -> None:
        """prepare_filename returning .mp3 doesn't double-replace."""
        worker = DownloadWorker(
            "https://youtube.com/watch?v=test",
            str(tmp_path / "song.mp3"),
            allowed_base_dir=str(tmp_path),
        )

        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 200,
        }

        with patch("yt_dlp.YoutubeDL") as mock_ytdl:
            mock_instance = MagicMock()
            mock_ytdl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = mock_info
            mock_instance.prepare_filename.return_value = str(tmp_path / "song.mp3")

            finished = []
            worker.finished.connect(lambda r: finished.append(r))
            worker.run()

        assert finished[0]["output_path"] == str(tmp_path / "song.mp3")
