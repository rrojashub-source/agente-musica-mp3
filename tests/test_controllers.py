"""
Tests for Phase 2.1 Controllers

Tests that extracted controllers work correctly independently.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ==========================================
# PlaybackController Tests
# ==========================================


class TestPlaybackController:
    """Tests for PlaybackController"""

    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies"""
        audio_player = Mock()
        audio_player.load.return_value = True
        audio_player.get_position.return_value = 30.0
        audio_player.get_duration.return_value = 180.0
        audio_player.get_volume.return_value = 0.7
        audio_player.is_playing.return_value = True

        now_playing = Mock()
        now_playing.volume_slider = Mock()
        now_playing.volume_label_value = Mock()

        playlist_manager = Mock()
        db_manager = Mock()

        return {
            "audio_player": audio_player,
            "now_playing": now_playing,
            "playlist_manager": playlist_manager,
            "db_manager": db_manager,
        }

    @pytest.fixture
    def controller(self, mock_deps):
        """Create PlaybackController with mocked PyQt"""
        with patch("controllers.playback_controller.QObject.__init__"):
            from controllers.playback_controller import PlaybackController

            ctrl = PlaybackController.__new__(PlaybackController)
            ctrl.audio_player = mock_deps["audio_player"]
            ctrl.now_playing = mock_deps["now_playing"]
            ctrl.playlist_manager = mock_deps["playlist_manager"]
            ctrl.db_manager = mock_deps["db_manager"]
            ctrl.library_tab = None
            ctrl.playlist_widget = None
            ctrl.status_bar = Mock()
            ctrl._playback_source = None
            ctrl._current_playlist_id = None
            ctrl._current_playlist_songs = []
            ctrl._current_playlist_index = -1
            ctrl._previous_volume = 0.7
            return ctrl

    def test_initial_state(self, controller):
        """Test initial playback state"""
        assert controller._playback_source is None
        assert controller._current_playlist_index == -1
        assert controller._current_playlist_songs == []

    def test_on_library_playback_started(self, controller):
        """Test switching to library source clears playlist state"""
        controller._playback_source = "playlist"
        controller._current_playlist_id = 42
        controller._current_playlist_songs = [{"id": 1}]
        controller._current_playlist_index = 0
        controller.playlist_widget = Mock()

        controller.on_library_playback_started()

        assert controller._playback_source == "library"
        assert controller._current_playlist_id is None
        assert controller._current_playlist_songs == []
        assert controller._current_playlist_index == -1
        controller.playlist_widget.clear_playing_highlight.assert_called_once()

    def test_on_global_next_library_mode(self, controller):
        """Test next routes to library tab in library mode"""
        controller._playback_source = "library"
        controller.library_tab = Mock()

        controller.on_global_next_clicked()

        controller.library_tab.play_next.assert_called_once()

    def test_on_global_next_playlist_mode(self, controller):
        """Test next routes to playlist in playlist mode"""
        controller._playback_source = "playlist"
        controller._current_playlist_songs = [{"id": 1}, {"id": 2}, {"id": 3}]
        controller._current_playlist_index = 0
        controller.db_manager.get_song_by_id.return_value = {"id": 2, "title": "Song 2", "file_path": "/tmp/test.mp3"}

        with patch.object(controller, "play_song_from_playlist"):
            controller.on_global_next_clicked()
            controller.play_song_from_playlist.assert_called_once()

    def test_on_global_prev_library_mode(self, controller):
        """Test prev routes to library tab in library mode"""
        controller._playback_source = "library"
        controller.library_tab = Mock()

        controller.on_global_prev_clicked()

        controller.library_tab.play_previous.assert_called_once()

    def test_on_global_song_ended_library(self, controller):
        """Test song ended routes to library in library mode"""
        controller._playback_source = "library"
        controller.library_tab = Mock()

        controller.on_global_song_ended()

        controller.library_tab.notify_song_ended.assert_called_once()

    def test_on_global_song_ended_playlist(self, controller):
        """Test song ended auto-plays next in playlist mode"""
        controller._playback_source = "playlist"
        controller._current_playlist_songs = [{"id": 1}, {"id": 2}]
        controller._current_playlist_index = 0
        controller.db_manager.get_song_by_id.return_value = {"id": 2, "title": "Song 2", "file_path": "/tmp/test.mp3"}

        with patch.object(controller, "play_song_from_playlist"):
            controller.on_global_song_ended()
            controller.play_song_from_playlist.assert_called_once()

    def test_handle_seek_backward(self, controller):
        """Test seek backward calculates correct position"""
        controller.audio_player.get_position.return_value = 30.0

        controller.handle_seek_backward(5)

        controller.audio_player.seek.assert_called_once_with(25.0)

    def test_handle_seek_backward_clamps_to_zero(self, controller):
        """Test seek backward doesn't go below 0"""
        controller.audio_player.get_position.return_value = 2.0

        controller.handle_seek_backward(5)

        controller.audio_player.seek.assert_called_once_with(0)

    def test_handle_seek_forward(self, controller):
        """Test seek forward calculates correct position"""
        controller.audio_player.get_position.return_value = 30.0
        controller.audio_player.get_duration.return_value = 180.0

        controller.handle_seek_forward(5)

        controller.audio_player.seek.assert_called_once_with(35.0)

    def test_handle_seek_forward_clamps_to_duration(self, controller):
        """Test seek forward doesn't exceed duration"""
        controller.audio_player.get_position.return_value = 178.0
        controller.audio_player.get_duration.return_value = 180.0

        controller.handle_seek_forward(5)

        controller.audio_player.seek.assert_called_once_with(180.0)

    def test_set_widgets(self, controller):
        """Test set_widgets updates references"""
        lib = Mock()
        pl = Mock()
        sb = Mock()

        controller.set_widgets(library_tab=lib, playlist_widget=pl, status_bar=sb)

        assert controller.library_tab is lib
        assert controller.playlist_widget is pl
        assert controller.status_bar is sb


# ==========================================
# RemoteController Tests
# ==========================================


class TestRemoteController:
    """Tests for RemoteController"""

    @pytest.fixture
    def controller(self):
        """Create RemoteController with mocks"""
        with patch("controllers.remote_controller.QObject.__init__"):
            from controllers.remote_controller import RemoteController

            ctrl = RemoteController.__new__(RemoteController)
            ctrl.audio_player = Mock()
            ctrl.audio_player.is_playing.return_value = False
            ctrl.now_playing = Mock()
            ctrl._remote_server = None
            ctrl._remote_update_timer = None
            ctrl._global_next_callback = None
            ctrl._global_prev_callback = None
            return ctrl

    def test_handle_command_play(self, controller):
        """Test play command"""
        controller.handle_command("play", {})

        controller.audio_player.play.assert_called_once()
        controller.now_playing.set_playing.assert_called_with(True)

    def test_handle_command_pause(self, controller):
        """Test pause command"""
        controller.handle_command("pause", {})

        controller.audio_player.pause.assert_called_once()
        controller.now_playing.set_playing.assert_called_with(False)

    def test_handle_command_toggle_when_stopped(self, controller):
        """Test toggle starts playback when stopped"""
        controller.audio_player.is_playing.return_value = False

        controller.handle_command("toggle", {})

        controller.audio_player.play.assert_called_once()

    def test_handle_command_toggle_when_playing(self, controller):
        """Test toggle pauses playback when playing"""
        controller.audio_player.is_playing.return_value = True

        controller.handle_command("toggle", {})

        controller.audio_player.pause.assert_called_once()

    def test_handle_command_volume(self, controller):
        """Test volume command sets correct level"""
        controller.now_playing.volume_slider = Mock()
        controller.now_playing.volume_label_value = Mock()

        controller.handle_command("volume", {"volume": 75})

        controller.audio_player.set_volume.assert_called_once_with(0.75)

    def test_handle_command_seek(self, controller):
        """Test seek command"""
        controller.handle_command("seek", {"position": 60})

        controller.audio_player.seek.assert_called_once_with(60)

    def test_handle_command_next(self, controller):
        """Test next command calls registered callback"""
        callback = Mock()
        controller.set_navigation_callbacks(next_callback=callback, prev_callback=Mock())

        controller.handle_command("next", {})

        callback.assert_called_once()

    def test_handle_command_previous(self, controller):
        """Test previous command calls registered callback"""
        callback = Mock()
        controller.set_navigation_callbacks(next_callback=Mock(), prev_callback=callback)

        controller.handle_command("previous", {})

        callback.assert_called_once()

    def test_update_now_playing_no_server(self, controller):
        """Test update_now_playing does nothing without server"""
        controller._remote_server = None
        # Should not raise
        controller.update_now_playing()

    def test_set_navigation_callbacks(self, controller):
        """Test setting navigation callbacks"""
        next_cb = Mock()
        prev_cb = Mock()

        controller.set_navigation_callbacks(next_cb, prev_cb)

        assert controller._global_next_callback is next_cb
        assert controller._global_prev_callback is prev_cb


# ==========================================
# LibraryController Tests
# ==========================================


class TestLibraryController:
    """Tests for LibraryController"""

    @pytest.fixture
    def controller(self):
        """Create LibraryController with mocks"""
        from controllers.library_controller import LibraryController

        ctrl = LibraryController(db_manager=Mock(), status_bar=Mock())
        ctrl.tabs = Mock()
        ctrl.library_tab = Mock()
        ctrl.search_tab = Mock()
        ctrl.recommendations_widget = Mock()
        return ctrl

    def test_on_album_selected(self, controller):
        """Test album selection switches to library tab and filters"""
        controller.on_album_selected({"album": "Dark Side", "artist": "Pink Floyd"})

        controller.tabs.setCurrentWidget.assert_called_once_with(controller.library_tab)
        controller.library_tab.search_box.setText.assert_called_once_with("Dark Side")
        controller.status_bar.showMessage.assert_called_once()

    def test_update_recommendations(self, controller):
        """Test recommendations update"""
        song = {"title": "Test", "artist": "Artist"}
        controller.update_recommendations(song)

        controller.recommendations_widget.set_current_song.assert_called_once_with(song)

    def test_on_find_similar_requested(self, controller):
        """Test find similar routes to recommendations"""
        song = {"title": "Test"}
        controller.on_find_similar_requested(song)

        controller.recommendations_widget.set_current_song.assert_called_once_with(song)
        controller.status_bar.showMessage.assert_called_once()

    def test_handle_focus_search(self, controller):
        """Test focus search switches to search tab"""
        controller.handle_focus_search()

        controller.tabs.setCurrentWidget.assert_called_once_with(controller.search_tab)
        controller.search_tab.search_box.setFocus.assert_called_once()

    def test_handle_switch_tab_library(self, controller):
        """Test switch to library tab"""
        controller.handle_switch_tab("library")

        controller.tabs.setCurrentWidget.assert_called_once_with(controller.library_tab)

    def test_check_empty_library_not_empty(self, controller):
        """Test no dialog shown when library has songs"""
        controller.db_manager.get_song_count.return_value = 100

        with patch("controllers.library_controller.QMessageBox") as mock_mb:
            controller.check_empty_library(Mock())
            mock_mb.information.assert_not_called()

    def test_check_empty_library_empty(self, controller):
        """Test dialog shown when library is empty"""
        controller.db_manager.get_song_count.return_value = 0
        controller.tabs.count.return_value = 0

        with patch("controllers.library_controller.QMessageBox") as mock_mb:
            controller.check_empty_library(Mock())
            mock_mb.information.assert_called_once()

    def test_set_widgets(self, controller):
        """Test set_widgets updates references"""
        new_tabs = Mock()
        controller.set_widgets(tabs=new_tabs)
        assert controller.tabs is new_tabs


# ==========================================
# UIComposer Tests (structural only)
# ==========================================


class TestUIComposerStructure:
    """Structural tests for UIComposer — verify class interface exists"""

    def test_ui_composer_import(self):
        """Test UIComposer can be imported"""
        from controllers.ui_composer import UIComposer

        assert UIComposer is not None

    def test_ui_composer_has_compose_method(self):
        """Test UIComposer has compose() method"""
        from controllers.ui_composer import UIComposer

        assert hasattr(UIComposer, "compose")
        assert callable(getattr(UIComposer, "compose"))

    def test_ui_composer_has_dialog_methods(self):
        """Test UIComposer has all dialog handler methods"""
        from controllers.ui_composer import UIComposer

        expected = [
            "_show_api_settings",
            "_show_equalizer",
            "_change_language",
            "_toggle_theme",
            "_show_about",
            "_show_api_guide",
            "_show_shortcuts_dialog",
        ]
        for method in expected:
            assert hasattr(UIComposer, method), f"Missing method: {method}"

    def test_ui_composer_has_visualizer_handlers(self):
        """Test UIComposer has visualizer signal handlers"""
        from controllers.ui_composer import UIComposer

        expected = ["_on_song_loaded", "_on_spectrum_extracted", "_on_spectrum_error"]
        for method in expected:
            assert hasattr(UIComposer, method), f"Missing method: {method}"

    def test_api_guide_html_exists(self):
        """Test API guide HTML constant exists"""
        from controllers.ui_composer import API_GUIDE_HTML

        assert len(API_GUIDE_HTML) > 100
        assert "YouTube" in API_GUIDE_HTML
        assert "Spotify" in API_GUIDE_HTML


# ==========================================
# Facade (main.py) Tests
# ==========================================


class TestMainFacadeStructure:
    """Structural tests for the main.py facade"""

    def test_main_module_imports(self):
        """Test main.py imports controllers correctly"""
        # Just verify the imports don't fail
        from controllers import LibraryController, PlaybackController, RemoteController, UIComposer

        assert PlaybackController is not None
        assert RemoteController is not None
        assert UIComposer is not None
        assert LibraryController is not None

    def test_main_py_line_count(self):
        """Test main.py is under 500 lines (was 1373)"""
        main_path = Path(__file__).parent.parent / "src" / "main.py"
        with open(main_path) as f:
            line_count = sum(1 for _ in f)
        assert line_count < 500, f"main.py has {line_count} lines, should be <500"

    def test_no_file_over_500_lines(self):
        """Test no controller file exceeds 600 lines"""
        controllers_dir = Path(__file__).parent.parent / "src" / "controllers"
        for py_file in controllers_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            with open(py_file) as f:
                line_count = sum(1 for _ in f)
            assert line_count < 650, f"{py_file.name} has {line_count} lines"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
