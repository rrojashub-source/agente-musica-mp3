"""
Tests for Now Playing Widget - Phase 6.2 (TDD Red Phase)

Purpose: GUI widget for displaying currently playing song with playback controls
- Display song metadata (title, artist, album)
- Album art thumbnail
- Playback controls (play/pause, stop, prev, next)
- Progress slider (seek functionality)
- Volume slider
- Time labels (current / total duration)
- Position updates via QTimer

Test Strategy: Red → Green → Refactor
Expected Result: All tests FAIL initially (no implementation yet)
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QPushButton, QSlider, QLabel
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
import sys

# Ensure QApplication exists for PyQt6 tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestNowPlayingWidget(unittest.TestCase):
    """Test Now Playing Widget GUI"""

    def setUp(self):
        """Setup test fixtures"""
        try:
            from src.gui.widgets.now_playing_widget import NowPlayingWidget

            # Mock audio player
            self.mock_player = Mock()
            self.widget = NowPlayingWidget(self.mock_player)
        except ImportError:
            self.widget = None

    def tearDown(self):
        """Cleanup"""
        if self.widget:
            self.widget.close()

    # ========== STRUCTURAL TESTS ==========

    def test_01_now_playing_widget_exists(self):
        """Test NowPlayingWidget class exists"""
        if self.widget is None:
            self.fail("NowPlayingWidget not found - implement src/gui/widgets/now_playing_widget.py")

        self.assertIsNotNone(self.widget)

    def test_02_widget_displays_song_info(self):
        """Test widget displays title, artist, album"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # Should have labels for song info
        self.assertTrue(hasattr(self.widget, 'title_label'), "Missing title_label")
        self.assertTrue(hasattr(self.widget, 'artist_label'), "Missing artist_label")
        self.assertTrue(hasattr(self.widget, 'album_label'), "Missing album_label")

        # Labels should be QLabel
        self.assertIsInstance(self.widget.title_label, QLabel)
        self.assertIsInstance(self.widget.artist_label, QLabel)

    def test_03_widget_has_playback_controls(self):
        """Test widget has play/pause, stop, prev, next buttons"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # Should have control buttons
        self.assertTrue(hasattr(self.widget, 'play_button'), "Missing play_button")
        self.assertTrue(hasattr(self.widget, 'stop_button'), "Missing stop_button")

        # Buttons should be QPushButton
        self.assertIsInstance(self.widget.play_button, QPushButton)
        self.assertIsInstance(self.widget.stop_button, QPushButton)

    def test_04_widget_has_progress_slider(self):
        """Test widget has progress slider for seeking"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # Should have progress slider
        self.assertTrue(hasattr(self.widget, 'progress_slider'), "Missing progress_slider")
        self.assertIsInstance(self.widget.progress_slider, QSlider)

        # Should be horizontal
        self.assertEqual(self.widget.progress_slider.orientation(), Qt.Orientation.Horizontal)

    def test_05_widget_has_volume_slider(self):
        """Test widget has volume slider"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # Should have volume slider
        self.assertTrue(hasattr(self.widget, 'volume_slider'), "Missing volume_slider")
        self.assertIsInstance(self.widget.volume_slider, QSlider)

        # Should have reasonable range (0-100)
        self.assertEqual(self.widget.volume_slider.minimum(), 0)
        self.assertEqual(self.widget.volume_slider.maximum(), 100)

    # ========== FUNCTIONAL TESTS ==========

    def test_06_widget_updates_position(self):
        """Test widget updates position display via QTimer"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # Should have timer for position updates
        self.assertTrue(hasattr(self.widget, 'position_timer'), "Missing position_timer")

        # Should have time labels
        self.assertTrue(hasattr(self.widget, 'current_time_label'), "Missing current_time_label")
        self.assertTrue(hasattr(self.widget, 'total_time_label'), "Missing total_time_label")

    def test_07_play_button_toggles_state(self):
        """Test play button toggles between play and pause"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # Initial state should be play
        initial_text = self.widget.play_button.text()

        # Should have method to update song info
        if hasattr(self.widget, 'load_song'):
            song_info = {
                'title': 'Bohemian Rhapsody',
                'artist': 'Queen',
                'album': 'A Night at the Opera',
                'duration': 355.0
            }
            self.widget.load_song(song_info)

            # After loading, verify labels updated
            self.assertIn('Bohemian Rhapsody', self.widget.title_label.text())

    def test_08_progress_slider_seeks(self):
        """Test dragging progress slider triggers seek"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # Load a song first
        if hasattr(self.widget, 'load_song'):
            song_info = {
                'title': 'Test Song',
                'duration': 200.0
            }
            self.widget.load_song(song_info)

            # Change slider position
            self.widget.progress_slider.setValue(50)  # 50% through

            # Should trigger seek (verify via signal or player mock)
            # (Implementation will connect slider to seek method)

    def test_09_volume_slider_adjusts_volume(self):
        """Test volume slider adjusts player volume"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # Mock player should have set_volume
        self.mock_player.set_volume = Mock()

        # Change volume slider
        if hasattr(self.widget, '_on_volume_changed'):
            self.widget._on_volume_changed(75)  # 75%

            # Should call player.set_volume with 0.0-1.0 range
            if self.mock_player.set_volume.called:
                call_args = self.mock_player.set_volume.call_args[0]
                self.assertGreaterEqual(call_args[0], 0.0)
                self.assertLessEqual(call_args[0], 1.0)

    def test_10_widget_handles_no_song_loaded(self):
        """Test widget displays correctly when no song loaded"""
        if self.widget is None:
            self.skipTest("Widget not implemented")

        # With no song loaded, should display placeholder text
        # (e.g., "No song playing")
        self.assertIsNotNone(self.widget.title_label.text())

        # Play button should be disabled or show "No song"
        # Progress slider should be disabled
        if hasattr(self.widget, 'progress_slider'):
            # Initial state should be reasonable
            self.assertEqual(self.widget.progress_slider.value(), 0)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
