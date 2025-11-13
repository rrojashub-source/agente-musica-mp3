"""
Tests for Download Queue System (Phase 4.2)
TDD: Write tests FIRST, then implement src/core/download_queue.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json


class TestDownloadQueue(unittest.TestCase):
    """Test DownloadQueue (manages concurrent downloads)"""

    def setUp(self):
        """Setup test fixtures"""
        # Create temporary directory for test persistence
        self.test_dir = tempfile.mkdtemp()
        self.queue_file = Path(self.test_dir) / "queue.json"

        # Import the class we're testing (will fail initially - expected in TDD Red phase)
        try:
            from src.core.download_queue import DownloadQueue
            self.queue_class = DownloadQueue
        except ImportError:
            self.queue_class = None  # Expected to fail initially

    def tearDown(self):
        """Cleanup test files"""
        import shutil
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_queue_class_exists(self):
        """Test DownloadQueue class exists"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found - implement src/core/download_queue.py")

        # Should be able to instantiate
        queue = self.queue_class(max_concurrent=3)
        self.assertIsNotNone(queue)

    def test_queue_initialization(self):
        """Test DownloadQueue initializes with max_concurrent limit"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        # Initialize with max_concurrent=50 (as per requirements)
        queue = self.queue_class(max_concurrent=50)

        # Verify max_concurrent set
        self.assertEqual(queue.max_concurrent, 50)

        # Verify queue starts empty
        self.assertEqual(len(queue.get_all()), 0)

    def test_queue_add_item(self):
        """Test adding download to queue"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Add download item
        item_id = queue.add(
            video_url="https://www.youtube.com/watch?v=test123",
            metadata={'title': 'Test Song', 'artist': 'Test Artist'}
        )

        # Verify item added
        self.assertIsNotNone(item_id, "add() should return item ID")
        self.assertEqual(len(queue.get_all()), 1)

        # Verify item has correct data
        items = queue.get_all()
        self.assertEqual(items[0]['video_url'], "https://www.youtube.com/watch?v=test123")
        self.assertEqual(items[0]['metadata']['title'], 'Test Song')

    def test_queue_add_multiple_items(self):
        """Test adding multiple downloads to queue"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Add 5 items
        for i in range(5):
            queue.add(
                video_url=f"https://www.youtube.com/watch?v=test{i}",
                metadata={'title': f'Song {i}', 'artist': 'Artist'}
            )

        # Verify all added
        self.assertEqual(len(queue.get_all()), 5)

    def test_queue_start_processing(self):
        """Test starting queue processing"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Add items
        queue.add(
            video_url="https://www.youtube.com/watch?v=test1",
            metadata={'title': 'Song 1'}
        )

        # Mock DownloadWorker to prevent actual downloads
        with patch('src.workers.download_worker.DownloadWorker'):
            # Start processing
            queue.start()

            # Verify queue is processing
            self.assertTrue(queue.is_running())

    def test_queue_respects_max_concurrent_limit(self):
        """Test queue respects max_concurrent limit (50 max)"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        # Set low limit for testing
        queue = self.queue_class(max_concurrent=3)

        # Add 10 items
        for i in range(10):
            queue.add(
                video_url=f"https://www.youtube.com/watch?v=test{i}",
                metadata={'title': f'Song {i}'}
            )

        # Mock DownloadWorker
        with patch('src.workers.download_worker.DownloadWorker'):
            # Start processing
            queue.start()

            # Verify only 3 are active (not all 10)
            active = queue.get_active_downloads()
            self.assertLessEqual(len(active), 3, "Should not exceed max_concurrent")

    def test_queue_pause_download(self):
        """Test pausing individual download"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Add item
        item_id = queue.add(
            video_url="https://www.youtube.com/watch?v=test1",
            metadata={'title': 'Song 1'}
        )

        # Mock worker
        with patch('src.workers.download_worker.DownloadWorker') as mock_worker:
            queue.start()

            # Pause the download
            result = queue.pause(item_id)

            # Verify paused
            self.assertTrue(result, "pause() should return True on success")

            # Verify status changed
            item = queue.get_item(item_id)
            self.assertEqual(item['status'], 'paused')

    def test_queue_resume_download(self):
        """Test resuming paused download"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Add and pause item
        item_id = queue.add(
            video_url="https://www.youtube.com/watch?v=test1",
            metadata={'title': 'Song 1'}
        )

        with patch('src.workers.download_worker.DownloadWorker'):
            queue.start()
            queue.pause(item_id)

            # Resume the download
            result = queue.resume(item_id)

            # Verify resumed
            self.assertTrue(result, "resume() should return True on success")

            # Verify status changed
            item = queue.get_item(item_id)
            self.assertIn(item['status'], ['downloading', 'pending'])

    def test_queue_cancel_download(self):
        """Test canceling active download"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Add item
        item_id = queue.add(
            video_url="https://www.youtube.com/watch?v=test1",
            metadata={'title': 'Song 1'}
        )

        with patch('src.workers.download_worker.DownloadWorker'):
            queue.start()

            # Cancel the download
            result = queue.cancel(item_id)

            # Verify canceled
            self.assertTrue(result, "cancel() should return True on success")

            # Verify item removed or status changed
            item = queue.get_item(item_id)
            if item is not None:
                self.assertEqual(item['status'], 'canceled')

    def test_queue_progress_tracking(self):
        """Test tracking progress for each download"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Add item
        item_id = queue.add(
            video_url="https://www.youtube.com/watch?v=test1",
            metadata={'title': 'Song 1'}
        )

        # Update progress
        queue.update_progress(item_id, 50)

        # Verify progress updated
        item = queue.get_item(item_id)
        self.assertEqual(item['progress'], 50)

    def test_queue_completion_callback(self):
        """Test callback fires when download completes"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Track completed items
        completed = []

        def on_complete(item_id, metadata):
            completed.append(item_id)

        queue.on_complete = on_complete

        # Add item
        item_id = queue.add(
            video_url="https://www.youtube.com/watch?v=test1",
            metadata={'title': 'Song 1'}
        )

        # Simulate completion
        queue.mark_completed(item_id, metadata={'title': 'Song 1', 'path': '/tmp/song.mp3'})

        # Verify callback fired
        self.assertIn(item_id, completed)

    def test_queue_persistence_save(self):
        """Test saving queue to disk"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        queue = self.queue_class(max_concurrent=3)

        # Add items
        for i in range(3):
            queue.add(
                video_url=f"https://www.youtube.com/watch?v=test{i}",
                metadata={'title': f'Song {i}'}
            )

        # Save queue
        queue.save(str(self.queue_file))

        # Verify file created
        self.assertTrue(self.queue_file.exists(), "Queue file should be created")

        # Verify file contains queue data
        with open(self.queue_file) as f:
            data = json.load(f)

        self.assertIn('items', data)
        self.assertEqual(len(data['items']), 3)

    def test_queue_persistence_load(self):
        """Test loading queue from disk (survives app restart)"""
        if self.queue_class is None:
            self.fail("DownloadQueue class not found")

        # Create and save queue
        queue1 = self.queue_class(max_concurrent=3)
        for i in range(3):
            queue1.add(
                video_url=f"https://www.youtube.com/watch?v=test{i}",
                metadata={'title': f'Song {i}'}
            )
        queue1.save(str(self.queue_file))

        # Load into new queue instance (simulate app restart)
        queue2 = self.queue_class(max_concurrent=3)
        queue2.load(str(self.queue_file))

        # Verify items restored
        self.assertEqual(len(queue2.get_all()), 3)

        # Verify data matches
        items = queue2.get_all()
        self.assertEqual(items[0]['metadata']['title'], 'Song 0')
        self.assertEqual(items[2]['metadata']['title'], 'Song 2')


if __name__ == "__main__":
    unittest.main()
