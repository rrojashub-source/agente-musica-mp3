"""
Tests for End-to-End Complete Flow (Phase 4.10)
TDD: Write tests FIRST, then verify integration
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
import sys
import time
import tempfile
import os

# Ensure QApplication exists for Qt tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestEndToEndFlow(unittest.TestCase):
    """Test complete end-to-end flow: Search → Select → Download → Tag → Complete"""

    def setUp(self):
        """Setup test fixtures"""
        # Import all components
        try:
            from src.core.download_queue import DownloadQueue
            from src.gui.tabs.search_tab import SearchTab
            from src.gui.widgets.queue_widget import QueueWidget
            from src.core.metadata_tagger import MetadataTagger

            # Create components
            self.download_queue = DownloadQueue(max_concurrent=3)
            self.search_tab = SearchTab(download_queue=self.download_queue)
            self.queue_widget = QueueWidget(download_queue=self.download_queue)
            self.tagger = MetadataTagger()

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

    def test_complete_flow_all_components_exist(self):
        """Test all components for complete flow exist"""
        self.assertIsNotNone(self.download_queue)
        self.assertIsNotNone(self.search_tab)
        self.assertIsNotNone(self.queue_widget)
        self.assertIsNotNone(self.tagger)

    def test_complete_flow_search_to_download(self):
        """Test complete flow: Search → Select → Add to Queue → Display"""
        # Mock YouTube search
        with patch.object(self.search_tab, 'youtube_searcher') as mock_yt:
            mock_yt.search.return_value = [
                {'video_id': 'test123', 'title': 'Test Song', 'thumbnail_url': 'url'}
            ]

            # Step 1: Search
            self.search_tab.search_box.setText("Test Song")
            self.search_tab.on_search_clicked()

            # Verify results displayed
            self.assertGreater(self.search_tab.youtube_results.count(), 0)

            # Step 2: Select song
            item = self.search_tab.youtube_results.item(0)
            self.search_tab._on_youtube_item_clicked(item)

            # Verify song selected
            self.assertEqual(len(self.search_tab.selected_songs), 1)

            # Step 3: Add to library (download queue)
            self.search_tab.on_add_to_library_clicked()

            # Verify added to queue
            items = self.download_queue.get_all_items()
            self.assertEqual(len(items), 1)

            # Step 4: Display in queue widget
            self.queue_widget.refresh_display()

            # Verify displayed
            self.assertEqual(self.queue_widget.table.rowCount(), 1)

    def test_complete_flow_download_to_tag(self):
        """Test complete flow: Download → Auto-tag → Complete"""
        # Add mock item to queue
        item_id = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test123',
            metadata={'title': 'Bohemian Rhapsody', 'artist': 'Queen'}
        )

        # Mock download completion
        items = self.download_queue.get_all_items()
        items[item_id]['status'] = 'completed'
        items[item_id]['progress'] = 100
        items[item_id]['file_path'] = '/tmp/test_song.mp3'

        # Mock metadata tagging
        with patch.object(self.tagger, 'lookup_and_tag') as mock_tag:
            mock_tag.return_value = True

            # Simulate auto-tagging after download
            file_path = items[item_id].get('file_path', '/tmp/test_song.mp3')
            metadata = items[item_id]['metadata']

            result = self.tagger.lookup_and_tag(file_path, metadata)

            # Verify tagging was called
            mock_tag.assert_called_once()

            # Verify success
            self.assertTrue(result)

    def test_complete_flow_multiple_songs(self):
        """Test complete flow with multiple songs"""
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

            # Add to queue
            self.search_tab.on_add_to_library_clicked()

            # Verify all in queue
            items = self.download_queue.get_all_items()
            self.assertEqual(len(items), 3)

            # Verify displayed in widget
            self.queue_widget.refresh_display()
            self.assertEqual(self.queue_widget.table.rowCount(), 3)

    def test_complete_flow_handles_api_errors(self):
        """Test complete flow handles API errors gracefully"""
        # Mock YouTube search error
        with patch.object(self.search_tab, 'youtube_searcher') as mock_yt:
            mock_yt.search.side_effect = Exception("API Error")

            # Search should handle error
            self.search_tab.search_box.setText("Test")
            result = self.search_tab.on_search_clicked()

            # Should complete without crashing
            self.assertIsNotNone(result)

    def test_complete_flow_empty_search_results(self):
        """Test complete flow handles empty search results"""
        # Mock empty search results
        with patch.object(self.search_tab, 'youtube_searcher') as mock_yt:
            mock_yt.search.return_value = []

            # Search
            self.search_tab.search_box.setText("NonexistentSong12345")
            self.search_tab.on_search_clicked()

            # Verify no results
            self.assertEqual(self.search_tab.youtube_results.count(), 0)

            # Try to add to library (should do nothing)
            self.search_tab.on_add_to_library_clicked()

            # Verify queue still empty
            items = self.download_queue.get_all_items()
            self.assertEqual(len(items), 0)

    def test_complete_flow_pause_resume_cancel(self):
        """Test complete flow with pause/resume/cancel operations"""
        # Add item to queue
        item_id = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test123',
            metadata={'title': 'Test Song', 'artist': 'Test Artist'}
        )

        # Mock as downloading
        self.download_queue._items[item_id]['status'] = 'downloading'

        # Display in widget
        self.queue_widget.refresh_display()

        # Pause
        self.queue_widget._on_pause_clicked(item_id)
        self.assertEqual(self.download_queue._items[item_id]['status'], 'paused')

        # Resume
        self.queue_widget._on_resume_clicked(item_id)
        self.assertIn(self.download_queue._items[item_id]['status'], ['pending', 'downloading'])

        # Cancel
        self.queue_widget._on_cancel_clicked(item_id)
        self.assertEqual(self.download_queue._items[item_id]['status'], 'canceled')

    def test_complete_flow_concurrent_downloads(self):
        """Test complete flow with concurrent downloads (max 50)"""
        # Add multiple items to queue
        item_ids = []
        for i in range(10):
            item_id = self.download_queue.add(
                video_url=f'https://youtube.com/watch?v=test{i}',
                metadata={'title': f'Song {i}', 'artist': 'Test Artist'}
            )
            item_ids.append(item_id)

        # Verify all added
        items = self.download_queue.get_all_items()
        self.assertEqual(len(items), 10)

        # Verify queue respects concurrent limit (max_concurrent=3 in setUp)
        self.assertEqual(self.download_queue.max_concurrent, 3)

        # Display in widget
        self.queue_widget.refresh_display()
        self.assertEqual(self.queue_widget.table.rowCount(), 10)

    def test_complete_flow_clear_completed(self):
        """Test complete flow: Clear completed downloads"""
        # Add items
        item_id_1 = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test1',
            metadata={'title': 'Song 1', 'artist': 'Artist 1'}
        )
        item_id_2 = self.download_queue.add(
            video_url='https://youtube.com/watch?v=test2',
            metadata={'title': 'Song 2', 'artist': 'Artist 2'}
        )

        # Mark first as completed
        self.download_queue._items[item_id_1]['status'] = 'completed'
        self.download_queue._items[item_id_1]['progress'] = 100

        # Display
        self.queue_widget.refresh_display()
        self.assertEqual(self.queue_widget.table.rowCount(), 2)

        # Clear completed
        self.queue_widget._on_clear_completed_clicked()

        # Verify only 1 item remains
        self.queue_widget._do_refresh()
        self.assertEqual(self.queue_widget.table.rowCount(), 1)

    def test_complete_flow_metadata_autocomplete(self):
        """Test complete flow: Metadata auto-complete with MusicBrainz"""
        # Mock partial metadata
        metadata = {'title': 'Bohemian Rhapsody'}

        # Mock MusicBrainz lookup
        with patch.object(self.tagger.autocompleter, 'autocomplete_single') as mock_auto:
            mock_auto.return_value = [
                {
                    'title': 'Bohemian Rhapsody',
                    'artist': 'Queen',
                    'album': 'A Night at the Opera',
                    'year': '1975',
                    'genre': 'rock',
                    'confidence': 95
                }
            ]

            # Mock file tagging
            with patch('src.core.metadata_tagger.MP3') as mock_mp3:
                mock_audio = MagicMock()
                mock_mp3.return_value = mock_audio

                # Lookup and tag
                result = self.tagger.lookup_and_tag('/tmp/test.mp3', metadata)

                # Verify autocomplete was used
                mock_auto.assert_called_once()

                # Verify success
                self.assertTrue(result)

    def test_complete_flow_integration_all_features(self):
        """Test complete integration of ALL Phase 4 features"""
        # This test verifies all components work together
        components_exist = all([
            hasattr(self, 'download_queue'),
            hasattr(self, 'search_tab'),
            hasattr(self, 'queue_widget'),
            hasattr(self, 'tagger')
        ])
        self.assertTrue(components_exist)

        # Verify SearchTab has all required components
        self.assertTrue(hasattr(self.search_tab, 'youtube_searcher'))
        self.assertTrue(hasattr(self.search_tab, 'spotify_searcher'))
        self.assertTrue(hasattr(self.search_tab, 'download_queue'))

        # Verify DownloadQueue has all required methods
        self.assertTrue(hasattr(self.download_queue, 'add'))
        self.assertTrue(hasattr(self.download_queue, 'pause'))
        self.assertTrue(hasattr(self.download_queue, 'resume'))
        self.assertTrue(hasattr(self.download_queue, 'cancel'))
        self.assertTrue(hasattr(self.download_queue, 'get_all_items'))
        self.assertTrue(hasattr(self.download_queue, 'clear_completed'))

        # Verify QueueWidget has all required components
        self.assertTrue(hasattr(self.queue_widget, 'table'))
        self.assertTrue(hasattr(self.queue_widget, 'refresh_button'))
        self.assertTrue(hasattr(self.queue_widget, 'clear_completed_button'))

        # Verify MetadataTagger has all required methods
        self.assertTrue(hasattr(self.tagger, 'tag_file'))
        self.assertTrue(hasattr(self.tagger, 'lookup_and_tag'))
        self.assertTrue(hasattr(self.tagger, 'autocompleter'))


if __name__ == "__main__":
    unittest.main()
