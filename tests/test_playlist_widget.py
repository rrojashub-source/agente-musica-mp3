"""
Tests for Playlist Widget - Phase 7.2 (TDD Red Phase)

Purpose: GUI for managing playlists
- Display all playlists in left panel
- Show songs of selected playlist in right panel
- Create/delete/rename playlists
- Add songs to playlists from library
- Drag-and-drop reordering
- Import/export .m3u8 files

Test Strategy: Red → Green → Refactor
Expected Result: All tests FAIL initially (no implementation yet)
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Ensure QApplication exists for PyQt6 tests (module level, created once)
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestPlaylistWidget(unittest.TestCase):
    """Test Playlist Widget GUI"""

    def setUp(self):
        """Setup test fixtures"""
        try:
            from gui.widgets.playlist_widget import PlaylistWidget

            # Mock dependencies
            self.mock_playlist_manager = Mock()
            self.mock_db_manager = Mock()

            # Patch load_playlists to prevent it from running during __init__
            with patch.object(PlaylistWidget, 'load_playlists'):
                # Create widget (load_playlists is mocked, won't execute)
                self.widget = PlaylistWidget(self.mock_playlist_manager, self.mock_db_manager)

        except ImportError:
            self.widget = None

    def tearDown(self):
        """Cleanup"""
        if hasattr(self, 'widget') and self.widget:
            self.widget.close()

    # ========== STRUCTURAL TESTS ==========

    def test_01_playlist_widget_exists(self):
        """Test PlaylistWidget class exists"""
        if self.widget is None:
            self.fail("PlaylistWidget not found - implement src/gui/widgets/playlist_widget.py")

        self.assertIsNotNone(self.widget)

    def test_02_widget_has_playlists_list(self):
        """Test widget has playlists list view"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Should have QListWidget or QTreeWidget for playlists
        self.assertTrue(hasattr(self.widget, 'playlists_list'))

    def test_03_widget_has_songs_table(self):
        """Test widget has songs table for current playlist"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Should have QTableWidget for playlist songs
        self.assertTrue(hasattr(self.widget, 'songs_table'))

    def test_04_widget_has_create_button(self):
        """Test widget has create playlist button"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Should have create button
        self.assertTrue(hasattr(self.widget, 'create_button'))

    # ========== FUNCTIONAL TESTS ==========

    def test_05_widget_displays_playlists(self):
        """Test widget displays playlists from manager"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Mock playlist data
        self.mock_playlist_manager.get_playlists.return_value = [
            {'id': 1, 'name': 'Favorites', 'description': 'My favorites', 'song_count': 10},
            {'id': 2, 'name': 'Rock', 'description': 'Rock songs', 'song_count': 25},
        ]

        # Load playlists
        self.widget.load_playlists()

        # Should display 2 playlists
        self.assertEqual(self.widget.playlists_list.count(), 2)

    def test_06_create_new_playlist(self):
        """Test creating new playlist"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Mock dialogs and manager
        with patch('gui.widgets.playlist_widget.QInputDialog.getText') as mock_input, \
             patch('gui.widgets.playlist_widget.QMessageBox.information') as mock_msg:
            mock_input.return_value = ('New Playlist', True)
            self.mock_playlist_manager.create_playlist.return_value = 3
            self.mock_playlist_manager.get_playlists.return_value = []  # For load_playlists call

            # Create playlist
            self.widget.create_playlist()

            # Should call manager
            self.assertTrue(self.mock_playlist_manager.create_playlist.called)

    def test_07_delete_playlist_with_confirmation(self):
        """Test deleting playlist with confirmation"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Mock playlists
        self.mock_playlist_manager.get_playlists.return_value = [
            {'id': 1, 'name': 'Favorites', 'song_count': 10},
        ]
        self.widget.load_playlists()

        # Select first playlist
        self.widget.playlists_list.setCurrentRow(0)

        # Mock confirmation dialogs
        with patch('gui.widgets.playlist_widget.QMessageBox.question') as mock_question, \
             patch('gui.widgets.playlist_widget.QMessageBox.information') as mock_info:
            mock_question.return_value = 16384  # QMessageBox.StandardButton.Yes

            # Delete playlist
            self.widget.delete_playlist()

            # Should call manager
            self.assertTrue(self.mock_playlist_manager.delete_playlist.called)

    def test_08_add_songs_to_playlist(self):
        """Test adding songs to playlist from library"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Mock playlists
        self.mock_playlist_manager.get_playlists.return_value = [
            {'id': 1, 'name': 'Favorites', 'song_count': 0},
        ]
        self.widget.load_playlists()

        # Select playlist (manually set current_playlist_id since signals might not fire in tests)
        self.widget.playlists_list.setCurrentRow(0)
        self.widget.current_playlist_id = 1

        # Mock song selection dialog and message box
        with patch.object(self.widget, 'select_songs_dialog') as mock_dialog, \
             patch('gui.widgets.playlist_widget.QMessageBox.information') as mock_msg:
            mock_dialog.return_value = [100, 200, 300]  # Selected song IDs
            self.mock_playlist_manager.get_playlist_songs.return_value = []  # For load_playlist_songs

            # Add songs
            self.widget.add_songs_to_playlist()

            # Should call manager for each song
            self.assertTrue(self.mock_playlist_manager.add_song.called)

    def test_09_import_m3u8_playlist(self):
        """Test importing .m3u8 playlist"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Mock file dialog and message box
        with patch('gui.widgets.playlist_widget.QFileDialog.getOpenFileName') as mock_dialog, \
             patch('gui.widgets.playlist_widget.QMessageBox.information') as mock_msg:
            mock_dialog.return_value = ('/path/to/playlist.m3u8', 'M3U8 Files (*.m3u8)')
            self.mock_playlist_manager.load_playlist.return_value = 5  # New playlist ID
            self.mock_playlist_manager.get_playlists.return_value = []  # For load_playlists call

            # Import playlist
            self.widget.import_playlist()

            # Should call manager
            self.assertTrue(self.mock_playlist_manager.load_playlist.called)

    def test_10_export_m3u8_playlist(self):
        """Test exporting playlist to .m3u8"""
        if self.widget is None:
            self.skipTest("PlaylistWidget not implemented")

        # Mock playlists
        self.mock_playlist_manager.get_playlists.return_value = [
            {'id': 1, 'name': 'Favorites', 'song_count': 10},
        ]
        self.widget.load_playlists()

        # Select playlist
        self.widget.playlists_list.setCurrentRow(0)

        # Mock file dialog and message box
        with patch('gui.widgets.playlist_widget.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('gui.widgets.playlist_widget.QMessageBox.information') as mock_msg:
            mock_dialog.return_value = ('/path/to/export.m3u8', 'M3U8 Files (*.m3u8)')
            self.mock_playlist_manager.save_playlist.return_value = True

            # Export playlist
            self.widget.export_playlist()

            # Should call manager
            self.assertTrue(self.mock_playlist_manager.save_playlist.called)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
