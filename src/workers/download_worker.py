"""
Download Worker - Phase 4.2
PyQt6 QThread worker for downloading music from YouTube using yt-dlp

Features:
- Background downloads (non-blocking UI)
- Progress reporting (0-100%)
- Metadata extraction
- Error handling with signals
- MP3 conversion (320kbps)
"""
import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal
import logging
from pathlib import Path

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
    progress = pyqtSignal(int)  # Progress percentage 0-100
    finished = pyqtSignal(dict)  # Metadata when download completes
    error = pyqtSignal(str)      # Error message on failure

    def __init__(self, video_url, output_path):
        """
        Initialize download worker

        Args:
            video_url (str): YouTube video URL
            output_path (str): Output path for MP3 file
        """
        super().__init__()

        self.video_url = video_url
        self.output_path = output_path

        # Configure yt-dlp options
        self.yt_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(output_path),
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

                # Build metadata dict
                metadata = {
                    'title': info.get('title', 'Unknown'),
                    'artist': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'upload_date': info.get('upload_date', None),
                    'output_path': str(self.output_path)
                }

                # Emit finished signal
                logger.info(f"Download complete: {metadata['title']}")
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
