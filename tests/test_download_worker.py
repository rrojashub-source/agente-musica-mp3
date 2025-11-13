"""
Tests for Download Worker (Phase 4.2)
TDD: Write tests FIRST, then implement src/workers/download_worker.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
import sys

# Ensure QApplication exists for Qt tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestDownloadWorker(unittest.TestCase):
    """Test DownloadWorker (yt-dlp integration with PyQt6)"""

    def setUp(self):
        """Setup test fixtures"""
        # Create temporary directory for test downloads
        self.test_dir = tempfile.mkdtemp()
        self.output_path = Path(self.test_dir) / "test_song.mp3"

        # Test video URL (short Creative Commons video for testing)
        self.test_video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

        # Import the class we're testing (will fail initially - expected in TDD Red phase)
        try:
            from src.workers.download_worker import DownloadWorker
            self.worker_class = DownloadWorker
        except ImportError:
            self.worker_class = None  # Expected to fail initially

    def tearDown(self):
        """Cleanup test files"""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_worker_class_exists(self):
        """Test DownloadWorker class exists and inherits from QThread"""
        if self.worker_class is None:
            self.fail("DownloadWorker class not found - implement src/workers/download_worker.py")

        # Verify it inherits from QThread
        self.assertTrue(
            issubclass(self.worker_class, QThread),
            "DownloadWorker must inherit from QThread"
        )

    def test_worker_initialization(self):
        """Test DownloadWorker initializes with video_url and output_path"""
        if self.worker_class is None:
            self.fail("DownloadWorker class not found")

        # Create worker instance
        worker = self.worker_class(self.test_video_url, str(self.output_path))

        # Verify attributes set correctly
        self.assertEqual(worker.video_url, self.test_video_url)
        self.assertEqual(worker.output_path, str(self.output_path))

    def test_worker_has_signals(self):
        """Test DownloadWorker has progress, finished, error signals"""
        if self.worker_class is None:
            self.fail("DownloadWorker class not found")

        # Create worker instance
        worker = self.worker_class(self.test_video_url, str(self.output_path))

        # Verify signals exist (they should be class attributes)
        self.assertTrue(hasattr(self.worker_class, 'progress'))
        self.assertTrue(hasattr(self.worker_class, 'finished'))
        self.assertTrue(hasattr(self.worker_class, 'error'))

    def test_worker_progress_signal_emits(self):
        """Test progress signal emits values 0-100 during download"""
        if self.worker_class is None:
            self.fail("DownloadWorker class not found")

        # Mock the download to emit progress
        worker = self.worker_class(self.test_video_url, str(self.output_path))

        # Collect progress values
        progress_values = []

        def collect_progress(value):
            progress_values.append(value)

        worker.progress.connect(collect_progress)

        # Mock yt-dlp to simulate progress
        with patch('src.workers.download_worker.yt_dlp.YoutubeDL') as mock_ytdl:
            # Setup mock to call progress hooks
            def mock_extract_info(url, download=False):
                # Call progress hooks
                if worker.yt_opts.get('progress_hooks'):
                    for hook in worker.yt_opts['progress_hooks']:
                        hook({'status': 'downloading', 'downloaded_bytes': 50, 'total_bytes': 100})
                        hook({'status': 'downloading', 'downloaded_bytes': 100, 'total_bytes': 100})
                        hook({'status': 'finished'})

                return {
                    'title': 'Test Video',
                    'uploader': 'Test Artist',
                    'duration': 180
                }

            mock_ytdl.return_value.__enter__.return_value.extract_info = mock_extract_info

            # Run worker (in same thread for testing)
            worker.run()

        # Verify progress values were emitted
        # We expect at least some progress updates
        self.assertGreater(len(progress_values), 0, "Progress signal should emit values")

        # All values should be 0-100
        for value in progress_values:
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)

    def test_worker_finished_signal_emits_metadata(self):
        """Test finished signal emits metadata dict when download completes"""
        if self.worker_class is None:
            self.fail("DownloadWorker class not found")

        worker = self.worker_class(self.test_video_url, str(self.output_path))

        # Collect finished data
        finished_data = []

        def collect_finished(data):
            finished_data.append(data)

        worker.finished.connect(collect_finished)

        # Mock successful download
        with patch('yt_dlp.YoutubeDL') as mock_ytdl:
            mock_instance = MagicMock()
            mock_ytdl.return_value.__enter__.return_value = mock_instance
            mock_instance.download.return_value = 0  # Success
            mock_instance.extract_info.return_value = {
                'title': 'Test Video',
                'uploader': 'Test Artist',
                'duration': 180
            }

            # Run worker
            worker.run()

        # Verify finished signal was emitted with metadata
        self.assertEqual(len(finished_data), 1)
        self.assertIsInstance(finished_data[0], dict)
        self.assertIn('title', finished_data[0])

    def test_worker_error_signal_on_download_failure(self):
        """Test error signal emits error message on download failure"""
        if self.worker_class is None:
            self.fail("DownloadWorker class not found")

        worker = self.worker_class(self.test_video_url, str(self.output_path))

        # Collect errors
        errors = []

        def collect_error(error_msg):
            errors.append(error_msg)

        worker.error.connect(collect_error)

        # Mock failed download
        with patch('src.workers.download_worker.yt_dlp.YoutubeDL') as mock_ytdl:
            mock_instance = MagicMock()
            mock_ytdl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.side_effect = Exception("Download failed")

            # Run worker
            worker.run()

        # Verify error signal was emitted
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], str)
        self.assertIn("fail", errors[0].lower())

    def test_worker_handles_invalid_url(self):
        """Test worker handles invalid YouTube URL gracefully"""
        if self.worker_class is None:
            self.fail("DownloadWorker class not found")

        invalid_url = "https://invalid-url.com/not-youtube"
        worker = self.worker_class(invalid_url, str(self.output_path))

        # Collect errors
        errors = []
        worker.error.connect(lambda msg: errors.append(msg))

        # Run worker
        worker.run()

        # Should emit error (not crash)
        self.assertGreater(len(errors), 0, "Should emit error for invalid URL")

    def test_worker_yt_dlp_options_configured(self):
        """Test yt-dlp options are configured correctly"""
        if self.worker_class is None:
            self.fail("DownloadWorker class not found")

        worker = self.worker_class(self.test_video_url, str(self.output_path))

        # Verify worker has yt_opts attribute
        self.assertTrue(hasattr(worker, 'yt_opts'), "Worker should have yt_opts attribute")

        # Verify essential options are set
        yt_opts = worker.yt_opts
        self.assertIn('format', yt_opts, "Should specify audio format")
        self.assertIn('outtmpl', yt_opts, "Should specify output template")
        self.assertIn('progress_hooks', yt_opts, "Should have progress hooks")


if __name__ == "__main__":
    unittest.main()
