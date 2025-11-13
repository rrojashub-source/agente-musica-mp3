"""
Tests for Download Integration (Phase 4.8)
TDD: Write tests FIRST, then implement integration
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
import sys
import time

# Ensure QApplication exists for Qt tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestDownloadIntegration(unittest.TestCase):
    """Test integration between SearchTab, DownloadQueue, and QueueWidget"""

    def setUp(self):
        """Setup test fixtures"""
        # Import classes
        try:
            from src.core.download_queue import DownloadQueue
            from src.gui.tabs.search_tab import SearchTab
            from src.gui.widgets.queue_widget import QueueWidget

            # Create download queue
            self.download_queue = DownloadQueue(max_concurrent=3)

            # Create search tab with queue
            self.search_tab = SearchTab(download_queue=self.download_queue)

            # Create queue widget with queue
            self.queue_widget = QueueWidget(download_queue=self.download_queue)

        except ImportError as e:
            self.fail(f"Import failed: {e}")

    def tearDown(self):
        """Cleanup"""
        if hasattr(self, 'search_tab'):
            self.search_tab.close()
        if hasattr(self, 'queue_widget'):
            self.queue_widget.close()
        if hasattr(self, 'download_queue'):
            # Cancel all pending downloads
            items = self.download_queue.get_all_items()
            for item_id in items.keys():
                self.download_queue.cancel(item_id)

    def test_integration_components_exist(self):
        """Test all integration components exist"""
        self.assertIsNotNone(self.download_queue)
        self.assertIsNotNone(self.search_tab)
        self.assertIsNotNone(self.queue_widget)

    def test_search_tab_has_download_queue_reference(self):
        """Test SearchTab has reference to DownloadQueue"""
        self.assertTrue(hasattr(self.search_tab, 'download_queue'))
        self.assertIsNotNone(self.search_tab.download_queue)

    def test_queue_widget_has_download_queue_reference(self):
        """Test QueueWidget has reference to DownloadQueue"""
        self.assertTrue(hasattr(self.queue_widget, 'download_queue'))
        self.assertIsNotNone(self.queue_widget.download_queue)

    def test_add_to_library_adds_to_queue(self):
        """Test 'Add to Library' button adds songs to download queue"""
        # Mock YouTube search results
        with patch.object(self.search_tab, 'youtube_searcher') as mock_yt:
            mock_yt.search.return_value = [
                {'video_id': 'test123', 'title': 'Test Song', 'thumbnail_url': 'url'}
            ]

            # Search
            self.search_tab.search_box.setText("Test Song")
            self.search_tab.on_search_clicked()

            # Select song (double-click)
            item = self.search_tab.youtube_results.item(0)
            self.search_tab._on_youtube_item_clicked(item)

            # Verify song added to selection
            self.assertEqual(len(self.search_tab.selected_songs), 1)

            # Add to library
            self.search_tab.on_add_to_library_clicked()

            # Verify added to download queue
            items = self.download_queue.get_all_items()
            self.assertGreater(len(items), 0)

    def test_queue_widget_displays_added_songs(self):
        """Test QueueWidget displays songs added to queue"""
        # Add mock item to queue
        item_id = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test123',
            metadata={'title': 'Test Song', 'artist': 'Test Artist'}
        )

        # Refresh queue widget display
        self.queue_widget.refresh_display()

        # Verify item appears in table
        self.assertEqual(self.queue_widget.table.rowCount(), 1)

        # Verify title displayed correctly
        title_item = self.queue_widget.table.item(0, 0)  # Column 0 = Title
        self.assertIsNotNone(title_item)
        self.assertIn('Test Song', title_item.text())

    def test_queue_widget_shows_correct_status(self):
        """Test QueueWidget shows correct status for items"""
        # Add item to queue
        item_id = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test123',
            metadata={'title': 'Test Song', 'artist': 'Test Artist'}
        )

        # Refresh display
        self.queue_widget.refresh_display()

        # Verify status column shows 'Pending' or 'Downloading'
        status_item = self.queue_widget.table.item(0, 3)  # Column 3 = Status
        self.assertIsNotNone(status_item)
        self.assertIn(status_item.text().lower(), ['pending', 'downloading'])

    def test_pause_button_appears_for_downloading_items(self):
        """Test pause button appears for downloading items"""
        # Add item and start download
        item_id = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test123',
            metadata={'title': 'Test Song', 'artist': 'Test Artist'}
        )

        # Mock as downloading
        items = self.download_queue.get_all_items()
        items[item_id]['status'] = 'downloading'

        # Refresh display
        self.queue_widget.refresh_display()

        # Verify action buttons widget exists
        action_widget = self.queue_widget.table.cellWidget(0, 4)  # Column 4 = Actions
        self.assertIsNotNone(action_widget)

    def test_pause_from_queue_widget(self):
        """Test pausing download from QueueWidget"""
        # Add item to queue
        item_id = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test123',
            metadata={'title': 'Test Song', 'artist': 'Test Artist'}
        )

        # Mock as downloading
        items = self.download_queue.get_all_items()
        items[item_id]['status'] = 'downloading'

        # Refresh display
        self.queue_widget.refresh_display()

        # Pause via widget method
        self.queue_widget._on_pause_clicked(item_id)

        # Verify item paused in queue
        updated_items = self.download_queue.get_all_items()
        self.assertEqual(updated_items[item_id]['status'], 'paused')

    def test_resume_from_queue_widget(self):
        """Test resuming download from QueueWidget"""
        # Add item to queue
        item_id = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test123',
            metadata={'title': 'Test Song', 'artist': 'Test Artist'}
        )

        # Pause it
        self.download_queue.pause(item_id)

        # Resume via widget method
        self.queue_widget._on_resume_clicked(item_id)

        # Verify item resumed (pending or downloading)
        updated_items = self.download_queue.get_all_items()
        self.assertIn(updated_items[item_id]['status'], ['pending', 'downloading'])

    def test_cancel_from_queue_widget(self):
        """Test cancelling download from QueueWidget"""
        # Add item to queue
        item_id = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test123',
            metadata={'title': 'Test Song', 'artist': 'Test Artist'}
        )

        # Cancel via widget method
        self.queue_widget._on_cancel_clicked(item_id)

        # Verify item cancelled in queue
        updated_items = self.download_queue.get_all_items()
        self.assertEqual(updated_items[item_id]['status'], 'canceled')

    def test_multiple_songs_from_search_to_queue(self):
        """Test adding multiple songs from search to queue"""
        # Mock YouTube search with multiple results
        with patch.object(self.search_tab, 'youtube_searcher') as mock_yt:
            mock_yt.search.return_value = [
                {'video_id': 'vid1', 'title': 'Song 1', 'thumbnail_url': 'url1'},
                {'video_id': 'vid2', 'title': 'Song 2', 'thumbnail_url': 'url2'},
                {'video_id': 'vid3', 'title': 'Song 3', 'thumbnail_url': 'url3'}
            ]

            # Search
            self.search_tab.search_box.setText("Test")
            self.search_tab.on_search_clicked()

            # Select all 3 songs
            for i in range(3):
                item = self.search_tab.youtube_results.item(i)
                self.search_tab._on_youtube_item_clicked(item)

            # Verify 3 songs selected
            self.assertEqual(len(self.search_tab.selected_songs), 3)

            # Add to library
            self.search_tab.on_add_to_library_clicked()

            # Verify 3 items in queue
            items = self.download_queue.get_all_items()
            self.assertEqual(len(items), 3)

            # Refresh queue widget
            self.queue_widget.refresh_display()

            # Verify 3 rows in queue widget
            self.assertEqual(self.queue_widget.table.rowCount(), 3)

    def test_clear_completed_removes_from_display(self):
        """Test clearing completed downloads removes them from display"""
        # Add items to queue
        item_id_1 = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test1',
            metadata={'title': 'Song 1', 'artist': 'Artist 1'}
        )
        item_id_2 = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test2',
            metadata={'title': 'Song 2', 'artist': 'Artist 2'}
        )

        # Mark first as completed (access internal _items directly)
        self.download_queue._items[item_id_1]['status'] = 'completed'
        self.download_queue._items[item_id_1]['progress'] = 100

        # Refresh display
        self.queue_widget.refresh_display()

        # Initial: 2 items
        self.assertEqual(self.queue_widget.table.rowCount(), 2)

        # Clear completed
        self.queue_widget._on_clear_completed_clicked()

        # After clear: 1 item (only pending one remains)
        # Use _do_refresh() to bypass throttling in tests
        self.queue_widget._do_refresh()
        self.assertEqual(self.queue_widget.table.rowCount(), 1)

    def test_search_tab_clears_selection_after_adding(self):
        """Test SearchTab clears selection after adding to library"""
        # Mock search
        with patch.object(self.search_tab, 'youtube_searcher') as mock_yt:
            mock_yt.search.return_value = [
                {'video_id': 'test123', 'title': 'Test Song', 'thumbnail_url': 'url'}
            ]

            # Search and select
            self.search_tab.search_box.setText("Test Song")
            self.search_tab.on_search_clicked()
            item = self.search_tab.youtube_results.item(0)
            self.search_tab._on_youtube_item_clicked(item)

            # Verify selection
            self.assertEqual(len(self.search_tab.selected_songs), 1)

            # Add to library
            self.search_tab.on_add_to_library_clicked()

            # Verify selection cleared
            self.assertEqual(len(self.search_tab.selected_songs), 0)

            # Verify counter updated
            self.assertEqual(self.search_tab.selected_count_label.text(), "Selected: 0 songs")


if __name__ == "__main__":
    unittest.main()
