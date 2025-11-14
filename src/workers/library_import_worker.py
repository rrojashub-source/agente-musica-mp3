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
import os
import logging
from pathlib import Path
from typing import Optional, Dict, List
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


def extract_metadata(file_path: str) -> Optional[Dict]:
    """
    Extract metadata from MP3 file using mutagen

    Args:
        file_path: Absolute path to MP3 file

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
        - file_path (str): Absolute file path
        - file_size (int): File size in bytes
    """
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3

        # Check file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        # Read audio info
        audio = MP3(file_path)

        # Read ID3 tags
        tags = ID3(file_path)

        # Extract metadata with defaults
        song_data = {
            'title': str(tags.get('TIT2', 'Unknown')),
            'artist': str(tags.get('TPE1', 'Unknown Artist')),
            'album': str(tags.get('TALB', 'Unknown Album')),
            'year': None,
            'genre': str(tags.get('TCON', '')) if tags.get('TCON') else None,
            'duration': int(audio.info.length),
            'bitrate': audio.info.bitrate,
            'sample_rate': audio.info.sample_rate,
            'file_path': file_path,
            'file_size': os.path.getsize(file_path)
        }

        # Parse year from TDRC tag (handles various formats)
        if tags.get('TDRC'):
            try:
                year_str = str(tags.get('TDRC'))
                # Extract first 4 digits
                year = int(year_str[:4])
                song_data['year'] = year
            except (ValueError, IndexError):
                logger.warning(f"Could not parse year from: {tags.get('TDRC')}")

        # Clean up "Unknown" to None for optional fields
        if song_data['title'] == 'Unknown':
            song_data['title'] = Path(file_path).stem  # Use filename as fallback

        return song_data

    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}")
        return None


class LibraryImportWorker(QThread):
    """
    Background worker for importing MP3 library

    Scans folder recursively for .mp3 files, extracts metadata,
    and imports into database with real-time progress updates.

    Signals:
        progress(int, str): Progress percentage (0-100) and status message
        song_imported(dict): Emitted for each successfully imported song
        finished(dict): Emitted when complete with summary:
            {
                'success': int,    # Songs successfully imported
                'failed': int,     # Songs that failed to import
                'skipped': int,    # Duplicate songs skipped
                'errors': [str]    # List of error messages
            }
        error(str): Emitted on fatal error
    """

    # Signals
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    song_imported = pyqtSignal(dict)  # Song data dictionary
    finished = pyqtSignal(dict)  # Summary dictionary
    error = pyqtSignal(str)  # Fatal error message

    def __init__(self, db_manager, folder_path: str, recursive: bool = True):
        """
        Initialize import worker

        Args:
            db_manager: DatabaseManager instance
            folder_path: Root folder to scan
            recursive: Scan subfolders recursively (default: True)
        """
        super().__init__()
        self.db_manager = db_manager
        self.folder_path = folder_path
        self.recursive = recursive

        # State tracking
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.errors = []

    def run(self):
        """
        Run import in background thread

        Workflow:
        1. Scan folder for .mp3 files
        2. For each file:
            - Check if already imported (skip duplicates)
            - Extract metadata
            - Insert into database
            - Emit progress signal
        3. Emit finished signal with summary
        """
        try:
            self.progress.emit(0, "Starting import...")

            # Scan for MP3 files
            mp3_files = self._scan_folder()

            if len(mp3_files) == 0:
                logger.info("No MP3 files found")
                self.progress.emit(100, "No MP3 files found")
                self.finished.emit({
                    'success': 0,
                    'failed': 0,
                    'skipped': 0,
                    'errors': []
                })
                return

            total_files = len(mp3_files)
            logger.info(f"Found {total_files} MP3 files")

            # Process each MP3
            for idx, mp3_file in enumerate(mp3_files):
                try:
                    self._process_file(mp3_file)
                except Exception as e:
                    self.failed_count += 1
                    error_msg = f"Failed to process {mp3_file}: {e}"
                    self.errors.append(error_msg)
                    logger.error(error_msg)

                # Update progress
                percentage = int(((idx + 1) / total_files) * 100)
                self.progress.emit(
                    percentage,
                    f"Importing... ({idx + 1}/{total_files} files)"
                )

            # Emit completion
            self.progress.emit(100, "Import complete")
            self.finished.emit({
                'success': self.success_count,
                'failed': self.failed_count,
                'skipped': self.skipped_count,
                'errors': self.errors[:10]  # Limit to first 10 errors
            })

            logger.info(
                f"Import complete: {self.success_count} success, "
                f"{self.failed_count} failed, {self.skipped_count} skipped"
            )

        except Exception as e:
            logger.error(f"Fatal import error: {e}")
            self.error.emit(str(e))

    def _scan_folder(self) -> List[str]:
        """
        Scan folder for .mp3 files

        Returns:
            List of absolute file paths
        """
        mp3_files = []

        folder = Path(self.folder_path)

        if not folder.exists():
            logger.error(f"Folder not found: {folder}")
            return mp3_files

        if self.recursive:
            # Recursive scan
            mp3_files = [
                str(f) for f in folder.rglob("*.mp3")
                if f.is_file()
            ]
        else:
            # Non-recursive (only top level)
            mp3_files = [
                str(f) for f in folder.glob("*.mp3")
                if f.is_file()
            ]

        return mp3_files

    def _process_file(self, file_path: str):
        """
        Process single MP3 file

        Args:
            file_path: Absolute path to MP3

        Increments:
            - success_count if imported
            - skipped_count if duplicate
            - failed_count if error
        """
        # Check if already imported
        if self.db_manager.song_exists(file_path):
            self.skipped_count += 1
            logger.debug(f"Skipping duplicate: {file_path}")
            return

        # Extract metadata
        metadata = extract_metadata(file_path)

        if metadata is None:
            self.failed_count += 1
            error_msg = f"Could not extract metadata: {file_path}"
            self.errors.append(error_msg)
            logger.warning(error_msg)
            return

        # Insert into database
        song_id = self.db_manager.add_song(metadata)

        if song_id is None:
            self.failed_count += 1
            error_msg = f"Database insert failed: {file_path}"
            self.errors.append(error_msg)
            logger.warning(error_msg)
            return

        # Success
        self.success_count += 1
        metadata['id'] = song_id
        self.song_imported.emit(metadata)
        logger.debug(f"Imported: {metadata['title']} (ID: {song_id})")
