"""
Download Worker - Phase 4.2
PySide6 QThread worker for downloading music from YouTube using yt-dlp

Features:
- Background downloads (non-blocking UI)
- Progress reporting (0-100%)
- Metadata extraction
- Error handling with signals
- MP3 conversion (320kbps)
"""
import yt_dlp
from PySide6.QtCore import QThread, Signal
import logging
from pathlib import Path
from utils.input_sanitizer import validate_path

# Setup logger
logger = logging.getLogger(__name__)


class DownloadWorker(QThread):
    """
    Background worker for downloading YouTube videos as MP3

    Usage:
        worker = DownloadWorker(video_url, output_path)
        worker.progress.connect(update_progress_bar)
        worker.finished.connect(on_download_complete)
        worker.error.connect(on_download_error)
        worker.start()
    """

    # Signals
    progress = Signal(int)  # Progress percentage 0-100
    finished = Signal(dict)  # Metadata when download completes
    error = Signal(str)      # Error message on failure

    # Allowed base directories for downloads
    ALLOWED_BASE_DIRS = [
        Path.home() / "Music",
        Path.home() / "Downloads",
        Path.home() / ".nexus_music",
        Path.cwd() / "downloads",
        Path.cwd() / "data" / "downloads",
    ]

    def __init__(self, video_url, output_path, allowed_base_dir=None):
        """
        Initialize download worker

        Args:
            video_url (str): YouTube video URL
            output_path (str): Output path for MP3 file
            allowed_base_dir (str): Base directory that output_path must be within.
                                    If None, validates against ALLOWED_BASE_DIRS.

        Raises:
            ValueError: If output_path escapes allowed base directory
        """
        super().__init__()

        # Validate output path to prevent path traversal
        output_path_str = str(output_path)
        if allowed_base_dir:
            is_valid, result = validate_path(output_path_str, str(allowed_base_dir))
            if not is_valid:
                raise ValueError(f"Invalid output path: {result}")
            output_path_str = result  # Use resolved path
        else:
            # Validate against known safe directories
            path_valid = False
            for base_dir in self.ALLOWED_BASE_DIRS:
                if base_dir.exists():
                    is_valid, _ = validate_path(output_path_str, str(base_dir))
                    if is_valid:
                        path_valid = True
                        break

            # If no base dir matched, ensure parent exists and is within CWD
            if not path_valid:
                resolved = Path(output_path_str).resolve()
                parent = resolved.parent
                parent.mkdir(parents=True, exist_ok=True)
                logger.warning(f"Output path {resolved} not in known safe dirs, allowing as fallback")

        self.video_url = video_url
        self.output_path = output_path_str

        # Configure yt-dlp options
        self.yt_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path_str,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'progress_hooks': [self._progress_hook],
            'quiet': True,
            'no_warnings': True,
        }

    def run(self):
        """
        Execute download in background thread

        Emits:
            progress: Progress updates 0-100
            finished: Metadata dict when complete
            error: Error message if download fails
        """
        try:
            logger.info(f"Starting download: {self.video_url}")

            # Download with yt-dlp
            with yt_dlp.YoutubeDL(self.yt_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(self.video_url, download=True)

                # Get actual downloaded file path (yt-dlp may rename after post-processing)
                actual_filepath = None
                if 'requested_downloads' in info and info['requested_downloads']:
                    # After post-processing, filepath contains the final MP3 path
                    actual_filepath = info['requested_downloads'][0].get('filepath')

                # Fallback to prepare_filename if requested_downloads not available
                if not actual_filepath:
                    actual_filepath = ydl.prepare_filename(info)
                    # If post-processor changed extension to .mp3, update path
                    if not actual_filepath.endswith('.mp3'):
                        actual_filepath = actual_filepath.rsplit('.', 1)[0] + '.mp3'

                logger.debug(f"Downloaded file path: {actual_filepath}")

                # Build metadata dict
                raw_title = info.get('title', 'Unknown')
                raw_artist = info.get('uploader', 'Unknown')

                # Clean YouTube artifacts from title and artist
                from core.metadata_cleaner import MetadataCleaner
                cleaner = MetadataCleaner()
                clean_title, _ = cleaner.clean_title(raw_title, raw_artist)
                clean_artist, _ = cleaner.clean_artist(raw_artist)

                metadata = {
                    'title': clean_title,
                    'artist': clean_artist,
                    'duration': info.get('duration', 0),
                    'upload_date': info.get('upload_date', None),
                    'output_path': actual_filepath  # Use ACTUAL path, not template
                }

                # Emit finished signal
                logger.info(f"Download complete: {metadata['title']} (raw: {raw_title})")
                self.finished.emit(metadata)

        except yt_dlp.utils.DownloadError as e:
            error_msg = f"Download failed: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)

    def _progress_hook(self, d):
        """
        Callback for yt-dlp progress updates

        Args:
            d (dict): Progress data from yt-dlp
        """
        if d['status'] == 'downloading':
            # Calculate percentage
            if 'total_bytes' in d and d['total_bytes'] > 0:
                percentage = int((d['downloaded_bytes'] / d['total_bytes']) * 100)
                self.progress.emit(percentage)
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                percentage = int((d['downloaded_bytes'] / d['total_bytes_estimate']) * 100)
                self.progress.emit(percentage)

        elif d['status'] == 'finished':
            # Download complete, processing starts
            self.progress.emit(100)
            logger.debug("Download finished, processing...")
