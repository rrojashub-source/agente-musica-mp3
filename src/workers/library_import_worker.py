"""
Library Import Worker - Background MP3 Scanning & Import

Scans folder recursively for MP3 files, extracts metadata using mutagen,
and imports into database with progress signals.

Features:
- Recursive folder scanning
- Metadata extraction (ID3 tags + audio info)
- Duplicate detection (skip already imported files)
- Progress signals for UI updates
- Error handling with detailed logging
- Background execution via QThread

Created: November 13, 2025
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Signal

from gui.base.base_worker import BaseWorker
from utils.constants import DEFAULT_ALBUM, DEFAULT_ARTIST

logger = logging.getLogger(__name__)


def extract_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract metadata from MP3 file using mutagen

    Args:
        file_path: Absolute path to MP3 file (should be normalized before calling)

    Returns:
        Dictionary with song metadata, or None if extraction fails

    Metadata fields:
        - title (str): Song title from TIT2 tag
        - artist (str): Artist name from TPE1 tag
        - album (str): Album name from TALB tag
        - year (int): Year from TDRC tag
        - genre (str): Genre from TCON tag
        - duration (int): Duration in seconds
        - bitrate (int): Bitrate in bps
        - sample_rate (int): Sample rate in Hz
        - file_path (str): Normalized absolute file path
        - file_size (int): File size in bytes
    """
    try:
        from mutagen.id3 import ID3
        from mutagen.mp3 import MP3

        # Normalize path to canonical format (absolute, resolved symlinks, correct separators)
        normalized_path = str(Path(file_path).resolve())

        # Check file exists
        if not os.path.exists(normalized_path):
            logger.error(f"File not found: {normalized_path}")
            return None

        # Read audio info
        audio = MP3(normalized_path)

        # Read ID3 tags
        tags = ID3(normalized_path)

        # Extract metadata with defaults (IMPORTANT: Use normalized_path for storage)
        song_data = {
            "title": str(tags.get("TIT2", "Unknown")),
            "artist": str(tags.get("TPE1", DEFAULT_ARTIST)),
            "album": str(tags.get("TALB", DEFAULT_ALBUM)),
            "year": None,
            "genre": str(tags.get("TCON", "")) if tags.get("TCON") else None,
            "duration": int(audio.info.length),  # type: ignore[attr-defined]
            "bitrate": audio.info.bitrate,  # type: ignore[attr-defined]
            "sample_rate": audio.info.sample_rate,  # type: ignore[attr-defined]
            "file_path": normalized_path,  # Store normalized path
            "file_size": os.path.getsize(normalized_path),
        }

        # Parse year from TDRC tag (handles various formats)
        if tags.get("TDRC"):
            try:
                year_str = str(tags.get("TDRC"))
                # Extract first 4 digits
                year = int(year_str[:4])
                song_data["year"] = year
            except (ValueError, IndexError):
                logger.warning(f"Could not parse year from: {tags.get('TDRC')}")

        # Clean up "Unknown" to None for optional fields
        if song_data["title"] == "Unknown":
            song_data["title"] = Path(normalized_path).stem  # Use filename as fallback

        return song_data

    except (OSError, ValueError, UnicodeDecodeError) as e:
        logger.error(f"Failed to extract metadata from {normalized_path}: {e}")
        return None


class LibraryImportWorker(BaseWorker):
    """
    Background worker for importing MP3 library

    Scans folder recursively for .mp3 files, extracts metadata,
    and imports into database with real-time progress updates.

    Signals (inherited from BaseWorker):
        progress(int, str): Progress percentage (0-100) and status message
        finished(object): Emitted when complete with summary dict
        error(str): Emitted on fatal error

    Custom signals:
        song_imported(dict): Emitted for each successfully imported song
    """

    # Custom signal (not in BaseWorker)
    song_imported = Signal(dict)  # Song data dictionary

    def __init__(self, db_manager: Any, folder_path: str, recursive: bool = True, max_duration: int = 900) -> None:
        """
        Initialize import worker

        Args:
            db_manager: DatabaseManager instance
            folder_path: Root folder to scan
            recursive: Scan subfolders recursively (default: True)
            max_duration: Maximum song duration in seconds (default: 900s = 15 min)
                         Songs longer than this are skipped (prevents importing playlists)
        """
        super().__init__()
        self.db_manager: Any = db_manager
        self.folder_path: str = folder_path
        self.recursive: bool = recursive
        self.max_duration: int = max_duration  # Skip ultra-long files (playlists)

        # State tracking
        self.success_count: int = 0
        self.failed_count: int = 0
        self.skipped_count: int = 0
        self.errors: List[str] = []

    def do_work(self) -> dict:
        """
        Run import in background thread.

        Workflow:
        1. Scan folder for .mp3 files
        2. For each file:
            - Check if already imported (skip duplicates)
            - Extract metadata
            - Insert into database
            - Emit progress signal
        3. Return summary dict (emitted via finished signal by BaseWorker)
        """
        self.report_progress(0, "Starting import...")

        # Scan for MP3 files
        mp3_files = self._scan_folder()

        if len(mp3_files) == 0:
            logger.info("No MP3 files found")
            self.report_progress(100, "No MP3 files found")
            return {"success": 0, "failed": 0, "skipped": 0, "errors": []}

        total_files = len(mp3_files)
        logger.info(f"Found {total_files} MP3 files")

        # Process each MP3
        for idx, mp3_file in enumerate(mp3_files):
            try:
                self._process_file(mp3_file)
            except (OSError, ValueError, UnicodeDecodeError) as e:
                self.failed_count += 1
                error_msg = f"Failed to process {mp3_file}: {e}"
                self.errors.append(error_msg)
                logger.error(error_msg)

            # Update progress
            percentage = int(((idx + 1) / total_files) * 100)
            self.report_progress(percentage, f"Importing... ({idx + 1}/{total_files} files)")

        # Return summary (BaseWorker emits via finished signal)
        self.report_progress(100, "Import complete")
        summary = {
            "success": self.success_count,
            "failed": self.failed_count,
            "skipped": self.skipped_count,
            "errors": self.errors[:10],  # Limit to first 10 errors
        }

        logger.info(
            f"Import complete: {self.success_count} success, {self.failed_count} failed, {self.skipped_count} skipped"
        )

        return summary

    def _scan_folder(self) -> List[str]:
        """
        Scan folder for .mp3 files

        Returns:
            List of absolute file paths
        """
        mp3_files: list[str] = []

        folder = Path(self.folder_path)

        if not folder.exists():
            logger.error(f"Folder not found: {folder}")
            return mp3_files  # type: ignore[return-value]

        if self.recursive:
            # Recursive scan
            mp3_files = [str(f) for f in folder.rglob("*.mp3") if f.is_file()]  # type: ignore[misc]
        else:
            # Non-recursive (only top level)
            mp3_files = [str(f) for f in folder.glob("*.mp3") if f.is_file()]  # type: ignore[misc]

        return mp3_files  # type: ignore[return-value]

    def _process_file(self, file_path: str) -> None:
        """
        Process single MP3 file with INTELLIGENT duplicate detection

        Uses multi-level detection:
        1. Check by file path (fast)
        2. Check by metadata (title + artist + duration) if path fails
        3. Update path if file moved, or add as new if truly unique

        Args:
            file_path: Absolute path to MP3

        Increments:
            - success_count if imported
            - skipped_count if duplicate
            - failed_count if error
        """
        # CRITICAL: Normalize path to canonical format before processing
        # This ensures duplicate detection works across different path formats
        # (forward/backward slashes, relative/absolute, case variations)
        try:
            normalized_path = str(Path(file_path).resolve())
        except OSError as e:
            logger.error(f"Failed to normalize path {file_path}: {e}")
            self.failed_count += 1
            return

        # LEVEL 1: Check if already imported by path (fast check)
        if self.db_manager.song_exists(normalized_path):
            self.skipped_count += 1
            logger.debug(f"Skipping duplicate (by path): {normalized_path}")
            return

        # Extract metadata for deeper checks
        metadata = extract_metadata(normalized_path)

        if metadata is None:
            self.failed_count += 1
            error_msg = f"Could not extract metadata: {normalized_path}"
            self.errors.append(error_msg)
            logger.warning(error_msg)
            return

        # VALIDATION: Skip ultra-long files (playlists, mixes, etc.)
        duration = metadata.get("duration", 0)
        if duration > self.max_duration:
            self.skipped_count += 1
            duration_min = duration / 60
            max_min = self.max_duration / 60
            logger.info(
                f"Skipping long file ({duration_min:.1f} min > {max_min:.1f} min max): "
                f"{metadata.get('title', 'Unknown')}"
            )
            return

        # LEVEL 2: Check by metadata (title + artist + duration ±3s)
        # This catches files that were moved/organized to different paths
        existing = self.db_manager.find_by_metadata(
            title=metadata["title"], artist=metadata["artist"], duration=metadata["duration"], tolerance=3
        )

        if existing:
            # File was moved! Update path instead of adding duplicate
            old_path = existing.get("file_path", "unknown")
            self.db_manager.update_song_path(existing["id"], normalized_path)
            self.skipped_count += 1
            logger.info(f"Updated path for song ID {existing['id']}: {old_path} -> {normalized_path}")
            return

        # LEVEL 3: Truly new song - add to database
        song_id = self.db_manager.add_song(metadata)

        if song_id is None:
            self.failed_count += 1
            error_msg = f"Database insert failed: {file_path}"
            self.errors.append(error_msg)
            logger.warning(error_msg)
            return

        # Success
        self.success_count += 1
        metadata["id"] = song_id
        self.song_imported.emit(metadata)
        logger.debug(f"Imported: {metadata['title']} (ID: {song_id})")
