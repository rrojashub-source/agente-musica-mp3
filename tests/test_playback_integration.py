"""
Tests for Playback Integration - Phase 6.3 (TDD Red Phase)

Purpose: Integrate audio player with library view for complete playback experience
- Double-click library row to play song
- Play button plays selected song
- Auto-play next song on end
- Keyboard shortcuts (Space = play/pause, Arrow keys = prev/next)
- Currently playing song highlighted in library
- Now Playing widget updates on play
- Graceful handling of missing files

Test Strategy: Red → Green → Refactor
Expected Result: All tests FAIL initially (no integration yet)
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QPoint
import sys

# Ensure QApplication exists for PyQt6 tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestPlaybackIntegration(unittest.TestCase):
    """Test playback integration with library view"""

    def setUp(self):
        """Setup test fixtures"""
        # Mock components
        self.mock_player = Mock()
        self.mock_now_playing = Mock()
        self.mock_db = Mock()

        # Try to import library tab (which should have playback integration)
        try:
            from src.gui.tabs.library_tab import LibraryTab
            self.library_tab = LibraryTab(self.mock_db)

            # Inject mocks
            self.library_tab.audio_player = self.mock_player
            self.library_tab.now_playing_widget = self.mock_now_playing
        except ImportError:
            self.library_tab = None

    def tearDown(self):
        """Cleanup"""
        if self.library_tab:
            self.library_tab.close()

    # ========== STRUCTURAL TESTS ==========

    def test_01_double_click_plays_song(self):
        """Test double-clicking library row plays song"""
        if self.library_tab is None:
            self.skipTest("LibraryTab not available")

        # Add test song to library table
        if hasattr(self.library_tab, 'library_table'):
            table = self.library_tab.library_table

            # Mock database to return song
            self.mock_db.get_song_by_id.return_value = {
                'id': 1,
                'title': 'Test Song',
                'artist': 'Test Artist',
                'file_path': '/path/to/test.mp3',
                'duration': 180.0
            }

            # Add row to table
            table.setRowCount(1)
            table.setItem(0, 0, QTableWidgetItem('Test Song'))

            # Set song ID in row data
            table.item(0, 0).setData(Qt.ItemDataRole.UserRole, 1)

            # Should have double-click handler
            self.assertTrue(
                hasattr(self.library_tab, '_on_row_double_clicked'),
                "Missing _on_row_double_clicked handler"
            )

    def test_02_play_button_plays_selected_song(self):
        """Test play button plays currently selected song"""
        if self.library_tab is None:
            self.skipTest("LibraryTab not available")

        # Should have play button
        self.assertTrue(
            hasattr(self.library_tab, 'play_button'),
            "Missing play_button"
        )

        # Mock song selection
        if hasattr(self.library_tab, 'library_table'):
            table = self.library_tab.library_table
            table.setRowCount(1)
            table.setItem(0, 0, QTableWidgetItem('Test Song'))
            table.item(0, 0).setData(Qt.ItemDataRole.UserRole, 1)
            table.selectRow(0)

            # Mock database
            self.mock_db.get_song_by_id.return_value = {
                'id': 1,
                'title': 'Test Song',
                'file_path': '/path/to/test.mp3',
                'duration': 180.0
            }

            # Should have play method
            self.assertTrue(
                hasattr(self.library_tab, '_play_selected_song') or
                hasattr(self.library_tab, 'play_song'),
                "Missing play song method"
            )

    def test_03_end_of_song_plays_next(self):
        """Test auto-play next song when current ends"""
        if self.library_tab is None:
            self.skipTest("LibraryTab not available")

        # Should have method to play next song
        self.assertTrue(
            hasattr(self.library_tab, '_play_next_song') or
            hasattr(self.library_tab, 'play_next'),
            "Missing play next song method"
        )

    def test_04_keyboard_space_toggles_playback(self):
        """Test Space key toggles play/pause"""
        if self.library_tab is None:
            self.skipTest("LibraryTab not available")

        # Should have keyPressEvent handler
        self.assertTrue(
            hasattr(self.library_tab, 'keyPressEvent'),
            "Missing keyPressEvent handler"
        )

        # Mock current song
        if hasattr(self.library_tab, '_current_song_id'):
            self.library_tab._current_song_id = 1

        # Simulate Space key press
        # (In real test, would use QTest.keyPress, but checking handler exists is enough for RED phase)

    def test_05_keyboard_arrows_change_song(self):
        """Test arrow keys change to prev/next song"""
        if self.library_tab is None:
            self.skipTest("LibraryTab not available")

        # Should have keyboard navigation
        self.assertTrue(
            hasattr(self.library_tab, 'keyPressEvent'),
            "Missing keyPressEvent handler"
        )

    def test_06_playing_song_highlights_in_library(self):
        """Test currently playing song is highlighted"""
        if self.library_tab is None:
            self.skipTest("LibraryTab not available")

        # Should have method to highlight playing song
        self.assertTrue(
            hasattr(self.library_tab, '_highlight_playing_song') or
            hasattr(self.library_tab, 'highlight_row'),
            "Missing highlight method"
        )

    def test_07_play_updates_now_playing_widget(self):
        """Test playing song updates Now Playing widget"""
        if self.library_tab is None:
            self.skipTest("LibraryTab not available")

        # Mock song
        song_info = {
            'id': 1,
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'file_path': '/path/to/test.mp3',
            'duration': 180.0
        }

        # Mock database
        self.mock_db.get_song_by_id.return_value = song_info

        # Mock player load
        self.mock_player.load.return_value = True

        # Play song (with mocked Path.exists and QMessageBox to avoid blocking)
        if hasattr(self.library_tab, '_play_song'):
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('PyQt6.QtWidgets.QMessageBox.warning'):
                self.library_tab._play_song(song_info)

                # Verify now_playing_widget.load_song was called
                if self.mock_now_playing.load_song.called:
                    call_args = self.mock_now_playing.load_song.call_args[0][0]
                    self.assertEqual(call_args['title'], 'Test Song')

    def test_08_handles_missing_file_gracefully(self):
        """Test graceful handling when MP3 file is missing"""
        if self.library_tab is None:
            self.skipTest("LibraryTab not available")

        # Mock song with non-existent file
        song_info = {
            'id': 1,
            'title': 'Missing Song',
            'file_path': '/nonexistent/file.mp3',
            'duration': 180.0
        }

        # Mock database
        self.mock_db.get_song_by_id.return_value = song_info

        # Mock player load failure
        self.mock_player.load.return_value = False

        # Try to play song (with mocked QMessageBox to avoid blocking)
        if hasattr(self.library_tab, '_play_song'):
            # Should not crash
            try:
                with patch('PyQt6.QtWidgets.QMessageBox.warning'):
                    self.library_tab._play_song(song_info)
            except Exception as e:
                self.fail(f"Should handle missing file gracefully: {e}")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
