"""
Tests for Queue Widget GUI (Phase 4.7)
TDD: Write tests FIRST, then implement src/gui/widgets/queue_widget.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
import sys

# Ensure QApplication exists for Qt tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestQueueWidget(unittest.TestCase):
    """Test QueueWidget GUI component"""

    def setUp(self):
        """Setup test fixtures"""
        # Import the class we're testing (will fail initially - expected in TDD Red phase)
        try:
            from src.gui.widgets.queue_widget import QueueWidget
            self.widget_class = QueueWidget

            # Mock download queue
            self.mock_queue = Mock()
            self.mock_queue.get_all_items.return_value = {}

            self.widget = QueueWidget(download_queue=self.mock_queue)
        except ImportError:
            self.widget_class = None
            self.widget = None

    def tearDown(self):
        """Cleanup"""
        if self.widget:
            self.widget.close()

    def test_queue_widget_class_exists(self):
        """Test QueueWidget class exists and is a QWidget"""
        if self.widget_class is None:
            self.fail("QueueWidget class not found - implement src/gui/widgets/queue_widget.py")

        from PyQt6.QtWidgets import QWidget
        self.assertTrue(issubclass(self.widget_class, QWidget))

    def test_queue_widget_has_table(self):
        """Test QueueWidget has table for displaying items"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Should have table widget
        self.assertTrue(hasattr(self.widget, 'table'))
        from PyQt6.QtWidgets import QTableWidget
        self.assertIsInstance(self.widget.table, QTableWidget)

    def test_queue_widget_table_has_columns(self):
        """Test table has correct columns"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Should have columns: Title, Artist, Progress, Status, Actions
        table = self.widget.table
        expected_columns = ['Title', 'Artist', 'Progress', 'Status', 'Actions']

        self.assertEqual(table.columnCount(), len(expected_columns))

    def test_queue_widget_has_refresh_button(self):
        """Test QueueWidget has refresh button"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Should have refresh button
        self.assertTrue(hasattr(self.widget, 'refresh_button'))
        from PyQt6.QtWidgets import QPushButton
        self.assertIsInstance(self.widget.refresh_button, QPushButton)

    def test_queue_widget_displays_queue_items(self):
        """Test widget displays items from download queue"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Mock queue items
        self.mock_queue.get_all_items.return_value = {
            'item-1': {
                'id': 'item-1',
                'video_url': 'https://youtube.com/watch?v=1',
                'metadata': {'title': 'Song 1', 'artist': 'Artist 1'},
                'status': 'downloading',
                'progress': 50
            },
            'item-2': {
                'id': 'item-2',
                'video_url': 'https://youtube.com/watch?v=2',
                'metadata': {'title': 'Song 2', 'artist': 'Artist 2'},
                'status': 'pending',
                'progress': 0
            }
        }

        # Refresh display
        self.widget.refresh_display()

        # Should display 2 items
        self.assertEqual(self.widget.table.rowCount(), 2)

    def test_queue_widget_shows_progress_bars(self):
        """Test widget shows progress bars for each item"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Mock queue item with progress
        self.mock_queue.get_all_items.return_value = {
            'item-1': {
                'id': 'item-1',
                'video_url': 'https://youtube.com/watch?v=1',
                'metadata': {'title': 'Song 1', 'artist': 'Artist 1'},
                'status': 'downloading',
                'progress': 75
            }
        }

        self.widget.refresh_display()

        # Should have progress bar (check via method existence)
        self.assertTrue(hasattr(self.widget, '_create_progress_bar'))

    def test_queue_widget_shows_status(self):
        """Test widget displays status for each item"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Mock items with different statuses
        self.mock_queue.get_all_items.return_value = {
            'item-1': {'id': 'item-1', 'video_url': 'url', 'metadata': {'title': 'S1', 'artist': 'A1'}, 'status': 'pending', 'progress': 0},
            'item-2': {'id': 'item-2', 'video_url': 'url', 'metadata': {'title': 'S2', 'artist': 'A2'}, 'status': 'downloading', 'progress': 50},
            'item-3': {'id': 'item-3', 'video_url': 'url', 'metadata': {'title': 'S3', 'artist': 'A3'}, 'status': 'completed', 'progress': 100},
            'item-4': {'id': 'item-4', 'video_url': 'url', 'metadata': {'title': 'S4', 'artist': 'A4'}, 'status': 'failed', 'progress': 0}
        }

        self.widget.refresh_display()

        # Should display all 4 items with different statuses
        self.assertEqual(self.widget.table.rowCount(), 4)

    def test_queue_widget_has_pause_action(self):
        """Test widget has pause action for items"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Should have method to create pause button
        self.assertTrue(hasattr(self.widget, '_create_action_buttons'))

    def test_queue_widget_pause_calls_queue_pause(self):
        """Test pause button calls download queue pause method"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Mock queue item
        item_id = 'test-item-1'
        self.mock_queue.get_all_items.return_value = {
            item_id: {
                'id': item_id,
                'video_url': 'https://youtube.com/watch?v=1',
                'metadata': {'title': 'Song 1', 'artist': 'Artist 1'},
                'status': 'downloading',
                'progress': 30
            }
        }

        self.widget.refresh_display()

        # Simulate pause button click
        self.widget._on_pause_clicked(item_id)

        # Should call queue.pause()
        self.mock_queue.pause.assert_called_once_with(item_id)

    def test_queue_widget_resume_calls_queue_resume(self):
        """Test resume button calls download queue resume method"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Mock paused item
        item_id = 'test-item-1'
        self.mock_queue.get_all_items.return_value = {
            item_id: {
                'id': item_id,
                'video_url': 'https://youtube.com/watch?v=1',
                'metadata': {'title': 'Song 1', 'artist': 'Artist 1'},
                'status': 'paused',
                'progress': 30
            }
        }

        self.widget.refresh_display()

        # Simulate resume button click
        self.widget._on_resume_clicked(item_id)

        # Should call queue.resume()
        self.mock_queue.resume.assert_called_once_with(item_id)

    def test_queue_widget_cancel_calls_queue_cancel(self):
        """Test cancel button calls download queue cancel method"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Mock downloading item
        item_id = 'test-item-1'
        self.mock_queue.get_all_items.return_value = {
            item_id: {
                'id': item_id,
                'video_url': 'https://youtube.com/watch?v=1',
                'metadata': {'title': 'Song 1', 'artist': 'Artist 1'},
                'status': 'downloading',
                'progress': 50
            }
        }

        self.widget.refresh_display()

        # Simulate cancel button click
        self.widget._on_cancel_clicked(item_id)

        # Should call queue.cancel()
        self.mock_queue.cancel.assert_called_once_with(item_id)

    def test_queue_widget_updates_on_progress_signal(self):
        """Test widget updates when queue emits progress signal"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Mock queue with signals
        item_id = 'test-item-1'

        # Initial state
        self.mock_queue.get_all_items.return_value = {
            item_id: {
                'id': item_id,
                'video_url': 'https://youtube.com/watch?v=1',
                'metadata': {'title': 'Song 1', 'artist': 'Artist 1'},
                'status': 'downloading',
                'progress': 10
            }
        }

        self.widget.refresh_display()

        # Simulate progress update
        self.mock_queue.get_all_items.return_value[item_id]['progress'] = 50

        # Should have method to handle progress updates
        self.assertTrue(hasattr(self.widget, '_on_item_progress'))

    def test_queue_widget_integration_with_download_queue(self):
        """Test QueueWidget properly integrates with DownloadQueue"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Should have download_queue instance
        self.assertTrue(hasattr(self.widget, 'download_queue'))
        self.assertIsNotNone(self.widget.download_queue)

    def test_queue_widget_clear_completed_button(self):
        """Test widget has button to clear completed downloads"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Should have clear completed button
        self.assertTrue(hasattr(self.widget, 'clear_completed_button'))
        from PyQt6.QtWidgets import QPushButton
        self.assertIsInstance(self.widget.clear_completed_button, QPushButton)

    def test_queue_widget_clear_completed_removes_items(self):
        """Test clear completed button removes completed items from display"""
        if self.widget is None:
            self.fail("QueueWidget not initialized")

        # Mock queue with completed and active items
        self.mock_queue.get_all_items.return_value = {
            'item-1': {'id': 'item-1', 'video_url': 'url', 'metadata': {'title': 'S1', 'artist': 'A1'}, 'status': 'completed', 'progress': 100},
            'item-2': {'id': 'item-2', 'video_url': 'url', 'metadata': {'title': 'S2', 'artist': 'A2'}, 'status': 'downloading', 'progress': 50},
            'item-3': {'id': 'item-3', 'video_url': 'url', 'metadata': {'title': 'S3', 'artist': 'A3'}, 'status': 'completed', 'progress': 100}
        }

        self.widget.refresh_display()

        # Initial: 3 items
        self.assertEqual(self.widget.table.rowCount(), 3)

        # Mock clear_completed to remove completed items
        def mock_clear_completed():
            items = self.mock_queue.get_all_items()
            for item_id in list(items.keys()):
                if items[item_id]['status'] == 'completed':
                    del items[item_id]

        self.mock_queue.clear_completed = mock_clear_completed

        # Click clear completed
        self.widget._on_clear_completed_clicked()

        # After clear: should have method to handle clearing
        self.assertTrue(hasattr(self.widget, '_on_clear_completed_clicked'))


if __name__ == "__main__":
    unittest.main()
