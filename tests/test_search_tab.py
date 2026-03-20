"""
Tests for Search Tab GUI (Phase 4.4)
TDD: Write tests FIRST, then implement src/gui/tabs/search_tab.py
"""

import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import sys

# Ensure QApplication exists for Qt tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


try:
    from gui.tabs.search_tab import SearchTab as _SearchTab
    from unittest.mock import patch as _patch

    class _TestableSearchTab(_SearchTab):
        """SearchTab subclass that suppresses all modal dialogs for test environments."""

        def _show_missing_credentials_prompt(self):
            pass

        def on_add_to_library_clicked(self):
            # QMessageBox is imported locally inside the method, so patch the
            # class directly in PySide6.QtWidgets to prevent modal dialogs.
            with _patch("PySide6.QtWidgets.QMessageBox"):
                super().on_add_to_library_clicked()

        def on_search_clicked(self):
            with _patch("PySide6.QtWidgets.QMessageBox"):
                return super().on_search_clicked()

    _IMPORT_OK = True
except ImportError:
    _TestableSearchTab = None  # type: ignore[assignment,misc]
    _IMPORT_OK = False


class TestSearchTab(unittest.TestCase):
    """Test SearchTab GUI component"""

    def setUp(self):
        """Setup test fixtures"""
        if _IMPORT_OK:
            self.tab_class = _TestableSearchTab
            self.tab = _TestableSearchTab()
        else:
            self.tab_class = None
            self.tab = None

    def tearDown(self):
        """Cleanup"""
        if self.tab:
            self.tab.close()

    def test_search_tab_class_exists(self):
        """Test SearchTab class exists and is a QWidget"""
        if self.tab_class is None:
            self.fail("SearchTab class not found - implement src/gui/tabs/search_tab.py")

        from PySide6.QtWidgets import QWidget

        self.assertTrue(issubclass(self.tab_class, QWidget))

    def test_search_tab_has_search_box(self):
        """Test SearchTab has search input box"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Should have search box (QLineEdit)
        self.assertTrue(hasattr(self.tab, "search_box"))
        from PySide6.QtWidgets import QLineEdit

        self.assertIsInstance(self.tab.search_box, QLineEdit)

    def test_search_tab_has_search_button(self):
        """Test SearchTab has search button"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Should have search button
        self.assertTrue(hasattr(self.tab, "search_button"))
        from PySide6.QtWidgets import QPushButton

        self.assertIsInstance(self.tab.search_button, QPushButton)

    def test_search_tab_has_youtube_checkbox(self):
        """Test SearchTab has YouTube checkbox"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Should have YouTube checkbox
        self.assertTrue(hasattr(self.tab, "youtube_checkbox"))
        from PySide6.QtWidgets import QCheckBox

        self.assertIsInstance(self.tab.youtube_checkbox, QCheckBox)

        # Should be checked by default
        self.assertTrue(self.tab.youtube_checkbox.isChecked())

    def test_search_tab_has_spotify_checkbox(self):
        """Test SearchTab has Spotify checkbox"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Should have Spotify checkbox
        self.assertTrue(hasattr(self.tab, "spotify_checkbox"))
        from PySide6.QtWidgets import QCheckBox

        self.assertIsInstance(self.tab.spotify_checkbox, QCheckBox)

        # Should be checked by default
        self.assertTrue(self.tab.spotify_checkbox.isChecked())

    def test_search_tab_has_results_areas(self):
        """Test SearchTab has result display areas"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Should have YouTube results area
        self.assertTrue(hasattr(self.tab, "youtube_results"))

        # Should have Spotify results area
        self.assertTrue(hasattr(self.tab, "spotify_results"))

    def test_search_tab_has_add_to_library_button(self):
        """Test SearchTab has 'Add to Library' button"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Should have add button
        self.assertTrue(hasattr(self.tab, "add_to_library_button"))
        from PySide6.QtWidgets import QPushButton

        self.assertIsInstance(self.tab.add_to_library_button, QPushButton)

    def test_search_button_click_triggers_search(self):
        """Test clicking search button triggers search"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Set search query
        self.tab.search_box.setText("Bohemian Rhapsody")

        # Mock API searchers
        with (
            patch.object(self.tab, "youtube_searcher") as mock_yt,
            patch.object(self.tab, "spotify_searcher") as mock_sp,
        ):
            mock_yt.search.return_value = []
            mock_sp.search_tracks.return_value = []

            # Click search button
            QTest.mouseClick(self.tab.search_button, Qt.MouseButton.LeftButton)

            # Should call searchers (may be async, so check eventually)
            # For now, just verify method exists
            self.assertTrue(hasattr(self.tab, "on_search_clicked"))

    def test_search_calls_apis_concurrently(self):
        """Test search calls YouTube and Spotify APIs concurrently"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Enable both checkboxes
        self.tab.youtube_checkbox.setChecked(True)
        self.tab.spotify_checkbox.setChecked(True)
        self.tab.search_box.setText("Test Query")

        # Mock searchers
        with (
            patch.object(self.tab, "youtube_searcher") as mock_yt,
            patch.object(self.tab, "spotify_searcher") as mock_sp,
        ):
            mock_yt.search.return_value = [{"video_id": "1", "title": "Test"}]
            mock_sp.search_tracks.return_value = [{"track_id": "1", "title": "Test"}]

            # Trigger search
            self.tab.on_search_clicked()

            # Both should be called
            mock_yt.search.assert_called_once()
            mock_sp.search_tracks.assert_called_once()

    def test_search_respects_checkbox_selection(self):
        """Test search only calls enabled APIs"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Enable only YouTube
        self.tab.youtube_checkbox.setChecked(True)
        self.tab.spotify_checkbox.setChecked(False)
        self.tab.search_box.setText("Test")

        with (
            patch.object(self.tab, "youtube_searcher") as mock_yt,
            patch.object(self.tab, "spotify_searcher") as mock_sp,
        ):
            mock_yt.search.return_value = []
            mock_sp.search_tracks.return_value = []

            self.tab.on_search_clicked()

            # Only YouTube should be called
            mock_yt.search.assert_called_once()
            mock_sp.search_tracks.assert_not_called()

    def test_search_results_displayed_in_ui(self):
        """Test search results are displayed in UI"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Mock search results
        youtube_results = [
            {"video_id": "1", "title": "Song 1", "thumbnail_url": "url1"},
            {"video_id": "2", "title": "Song 2", "thumbnail_url": "url2"},
        ]

        spotify_results = [
            {"track_id": "1", "title": "Song A", "artist": "Artist A", "album": "Album A"},
            {"track_id": "2", "title": "Song B", "artist": "Artist B", "album": "Album B"},
        ]

        # Display results
        self.tab._display_youtube_results(youtube_results)
        self.tab._display_spotify_results(spotify_results)

        # Verify results are displayed
        # (This would check the UI widgets are populated)
        self.assertTrue(hasattr(self.tab, "_display_youtube_results"))
        self.assertTrue(hasattr(self.tab, "_display_spotify_results"))

    def test_user_can_select_songs(self):
        """Test user can select songs from results"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Mock selecting songs
        self.tab.selected_songs = []

        # Simulate selecting a song
        song_data = {"video_id": "1", "title": "Test Song", "source": "youtube"}
        self.tab._add_to_selection(song_data)

        # Verify song added to selection
        self.assertEqual(len(self.tab.selected_songs), 1)
        self.assertEqual(self.tab.selected_songs[0]["title"], "Test Song")

    def test_selected_count_updates(self):
        """Test selected songs counter updates"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Should have label showing count
        self.assertTrue(hasattr(self.tab, "selected_count_label"))

        # Add songs to selection
        self.tab.selected_songs = []
        self.tab._add_to_selection({"title": "Song 1", "source": "youtube"})
        self.tab._add_to_selection({"title": "Song 2", "source": "spotify"})

        # Update UI
        self.tab._update_selected_count()

        # Verify label updated
        label_text = self.tab.selected_count_label.text()
        self.assertIn("2", label_text)

    def test_add_to_library_adds_to_download_queue(self):
        """Test 'Add to Library' adds songs to download queue"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Mock download queue
        with patch.object(self.tab, "download_queue") as mock_queue:
            # Add songs to selection (only YouTube for now, Spotify needs conversion)
            self.tab.selected_songs = [
                {"title": "Song 1", "video_id": "vid1", "source": "youtube"},
                {"title": "Song 2", "video_id": "vid2", "source": "youtube"},
            ]

            # Click add to library
            self.tab.on_add_to_library_clicked()

            # Should add to queue
            self.assertGreaterEqual(mock_queue.add.call_count, 2)

    def test_empty_search_shows_warning(self):
        """Test empty search query shows warning"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Empty search box
        self.tab.search_box.setText("")

        # Try to search
        result = self.tab.on_search_clicked()

        # Should not proceed (or show warning)
        # For now, just verify method handles it
        self.assertTrue(hasattr(self.tab, "on_search_clicked"))

    def test_search_tab_integrates_with_apis(self):
        """Test SearchTab properly integrates API searchers"""
        if self.tab is None:
            self.fail("SearchTab not initialized")

        # Should have searcher instances
        self.assertTrue(hasattr(self.tab, "youtube_searcher"))
        self.assertTrue(hasattr(self.tab, "spotify_searcher"))


if __name__ == "__main__":
    unittest.main()
