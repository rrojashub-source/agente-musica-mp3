"""
Phase 2 coverage tests for src/controllers/

Covers uncovered paths in:
- PlaybackController: _on_mpv_track_end, _play_song, play_song_from_playlist,
  _play_adjacent_in_playlist, play_recommended_song, handle_volume_change, handle_mute_toggle
- RemoteController: connect_server, update_now_playing with server, handle_command error
- LibraryController: set_widgets all params, handle_switch_tab queue, check_empty_library exception
- UIComposer: __init__, _load_tab, _connect_data_changed_signals, _on_song_loaded,
  _on_spectrum_extracted, _on_spectrum_error, dialog handlers
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402

# ==========================================
# PlaybackController — uncovered paths
# ==========================================


class TestPlaybackControllerPhase2:
    """Cover uncovered PlaybackController paths."""

    @pytest.fixture
    def ctrl(self):
        """Create PlaybackController bypassing QObject.__init__."""
        with patch("controllers.playback_controller.QObject.__init__"):
            from controllers.playback_controller import PlaybackController

            c = PlaybackController.__new__(PlaybackController)
            c.audio_player = Mock()
            c.audio_player.load.return_value = True
            c.audio_player.get_position.return_value = 30.0
            c.audio_player.get_duration.return_value = 180.0
            c.audio_player.get_volume.return_value = 0.7
            c.audio_player.is_playing.return_value = True
            c.now_playing = Mock()
            c.now_playing.volume_slider = Mock()
            c.now_playing.volume_label_value = Mock()
            c.playlist_manager = Mock()
            c.db_manager = Mock()
            c.library_tab = None
            c.playlist_widget = None
            c.status_bar = Mock()
            c._playback_source = None
            c._current_playlist_id = None
            c._current_playlist_songs = []
            c._current_playlist_index = -1
            c._previous_volume = 0.7
            return c

    # --- _on_mpv_track_end ---

    def test_track_end_repeat_one(self, ctrl) -> None:
        """Repeat one mode: seek(0) + play."""
        ctrl.now_playing.is_playing = True
        ctrl.now_playing.is_repeat_one_enabled.return_value = True

        ctrl._on_mpv_track_end("/music/song.mp3")

        ctrl.audio_player.seek.assert_called_once_with(0)
        ctrl.audio_player.play.assert_called_once()
        ctrl.now_playing.repeat_song.emit.assert_called_once()

    def test_track_end_continue_mode(self, ctrl) -> None:
        """Continue mode: set_playing(False) + on_global_song_ended."""
        ctrl.now_playing.is_playing = True
        ctrl.now_playing.is_repeat_one_enabled.return_value = False
        ctrl.now_playing.is_continue_enabled.return_value = True
        ctrl._playback_source = "library"
        ctrl.library_tab = Mock()

        ctrl._on_mpv_track_end("/music/song.mp3")

        ctrl.now_playing.set_playing.assert_called_once_with(False)
        ctrl.library_tab.notify_song_ended.assert_called_once()

    def test_track_end_stop(self, ctrl) -> None:
        """No repeat/continue: stop_playback."""
        ctrl.now_playing.is_playing = True
        ctrl.now_playing.is_repeat_one_enabled.return_value = False
        ctrl.now_playing.is_continue_enabled.return_value = False

        ctrl._on_mpv_track_end("/music/song.mp3")

        ctrl.now_playing.stop_playback.assert_called_once()

    def test_track_end_not_playing(self, ctrl) -> None:
        """If not playing, do nothing."""
        ctrl.now_playing.is_playing = False
        ctrl._on_mpv_track_end("/music/song.mp3")
        ctrl.now_playing.is_repeat_one_enabled.assert_not_called()

    # --- _play_song ---

    def test_play_song_no_file_path(self, ctrl) -> None:
        """Returns False when song has no file_path."""
        result = ctrl._play_song({"title": "No Path"})
        assert result is False

    def test_play_song_file_not_found(self, ctrl, tmp_path) -> None:
        """Returns False when file doesn't exist."""
        with patch("controllers.playback_controller.QMessageBox"):
            # parent() needs to work for QMessageBox.warning call
            ctrl.parent = Mock(return_value=Mock())
            result = ctrl._play_song({"file_path": str(tmp_path / "nonexistent.mp3")})
        assert result is False

    def test_play_song_load_fails(self, ctrl, tmp_path) -> None:
        """Returns False when audio_player.load() fails."""
        mp3 = tmp_path / "song.mp3"
        mp3.touch()
        ctrl.audio_player.load.return_value = False

        result = ctrl._play_song({"file_path": str(mp3)})
        assert result is False

    def test_play_song_success(self, ctrl, tmp_path) -> None:
        """Returns True on successful load + play."""
        mp3 = tmp_path / "song.mp3"
        mp3.touch()
        ctrl.audio_player.load.return_value = True
        song = {"file_path": str(mp3), "title": "Test"}

        result = ctrl._play_song(song)

        assert result is True
        ctrl.audio_player.play.assert_called_once()
        ctrl.now_playing.load_song.assert_called_once_with(song)
        ctrl.now_playing.set_playing.assert_called_once_with(True)

    # --- play_song_from_playlist ---

    def test_play_from_playlist_success(self, ctrl, tmp_path) -> None:
        """play_song_from_playlist tracks source and index."""
        mp3 = tmp_path / "song.mp3"
        mp3.touch()
        ctrl.playlist_widget = Mock()
        ctrl.playlist_widget.current_playlist_id = 10
        ctrl.playlist_manager.get_playlist_songs.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]

        ctrl.play_song_from_playlist({"id": 2, "file_path": str(mp3), "title": "S2"})

        assert ctrl._playback_source == "playlist"
        assert ctrl._current_playlist_id == 10
        assert ctrl._current_playlist_index == 1
        ctrl.playlist_widget.highlight_playing_song.assert_called_once_with(2)

    def test_play_from_playlist_play_fails(self, ctrl) -> None:
        """play_song_from_playlist returns early when _play_song fails."""
        ctrl.play_song_from_playlist({"title": "No Path"})
        assert ctrl._playback_source is None

    def test_play_from_playlist_exception(self, ctrl, tmp_path) -> None:
        """Exception in play_song_from_playlist is caught."""
        mp3 = tmp_path / "song.mp3"
        mp3.touch()
        ctrl.audio_player.load.return_value = True
        ctrl.playlist_widget = Mock()
        ctrl.playlist_widget.current_playlist_id = 1
        ctrl.playlist_manager.get_playlist_songs.side_effect = RuntimeError("boom")

        ctrl.play_song_from_playlist({"file_path": str(mp3), "title": "X", "id": 1})

    # --- _play_adjacent_in_playlist ---

    def test_adjacent_empty_playlist(self, ctrl) -> None:
        """Empty playlist logs warning."""
        ctrl._current_playlist_songs = []
        ctrl._play_adjacent_in_playlist(1)

    def test_adjacent_end_of_playlist(self, ctrl) -> None:
        """End of playlist shows status message."""
        ctrl._current_playlist_songs = [{"id": 1}]
        ctrl._current_playlist_index = 0

        ctrl._play_adjacent_in_playlist(1)

        ctrl.status_bar.showMessage.assert_called_once()
        assert "End" in ctrl.status_bar.showMessage.call_args[0][0]

    def test_adjacent_beginning_of_playlist(self, ctrl) -> None:
        """Beginning of playlist shows status message."""
        ctrl._current_playlist_songs = [{"id": 1}]
        ctrl._current_playlist_index = 0

        ctrl._play_adjacent_in_playlist(-1)

        ctrl.status_bar.showMessage.assert_called_once()
        assert "Beginning" in ctrl.status_bar.showMessage.call_args[0][0]

    def test_adjacent_song_not_found_in_db(self, ctrl) -> None:
        """Song not found in DB logs error."""
        ctrl._current_playlist_songs = [{"id": 1}, {"id": 2}]
        ctrl._current_playlist_index = 0
        ctrl.db_manager.get_song_by_id.return_value = None

        ctrl._play_adjacent_in_playlist(1)

        assert ctrl._current_playlist_index == 0

    def test_adjacent_end_no_status_bar(self, ctrl) -> None:
        """End of playlist without status_bar doesn't crash."""
        ctrl._current_playlist_songs = [{"id": 1}]
        ctrl._current_playlist_index = 0
        ctrl.status_bar = None

        ctrl._play_adjacent_in_playlist(1)

    def test_adjacent_beginning_no_status_bar(self, ctrl) -> None:
        """Beginning of playlist without status_bar doesn't crash."""
        ctrl._current_playlist_songs = [{"id": 1}]
        ctrl._current_playlist_index = 0
        ctrl.status_bar = None

        ctrl._play_adjacent_in_playlist(-1)

    # --- __init__ via proper construction ---

    def test_init_proper_construction(self) -> None:
        """Test PlaybackController.__init__ with QObject patched."""
        with patch("controllers.playback_controller.QObject.__init__"):
            from controllers.playback_controller import PlaybackController

            audio = Mock()
            now = Mock()
            pm = Mock()
            db = Mock()

            c = PlaybackController(audio, now, pm, db)

            assert c.audio_player is audio
            assert c.now_playing is now
            assert c.playlist_manager is pm
            assert c.db_manager is db
            assert c.library_tab is None
            assert c.playlist_widget is None
            assert c.status_bar is None
            assert c._playback_source is None
            assert c._current_playlist_id is None
            assert c._current_playlist_songs == []
            assert c._current_playlist_index == -1
            assert c._previous_volume == 0.7
            audio.on_track_end.assert_called_once()

    # --- play_recommended_song ---

    def test_play_recommended_success(self, ctrl, tmp_path) -> None:
        """play_recommended_song sets source to library."""
        mp3 = tmp_path / "rec.mp3"
        mp3.touch()

        ctrl.play_recommended_song({"file_path": str(mp3), "title": "Rec"})

        assert ctrl._playback_source == "library"
        ctrl.status_bar.showMessage.assert_called_once()

    def test_play_recommended_fails(self, ctrl) -> None:
        """play_recommended_song returns early when _play_song fails."""
        ctrl.play_recommended_song({"title": "No Path"})
        assert ctrl._playback_source is None

    def test_play_recommended_exception(self, ctrl, tmp_path) -> None:
        """Exception in play_recommended_song is caught."""
        mp3 = tmp_path / "song.mp3"
        mp3.touch()
        ctrl.audio_player.load.return_value = True
        ctrl.audio_player.play.side_effect = RuntimeError("boom")
        ctrl.play_recommended_song({"file_path": str(mp3), "title": "X"})

    # --- handle_play_pause ---

    def test_handle_play_pause(self, ctrl) -> None:
        ctrl.handle_play_pause()
        ctrl.now_playing.toggle_play_pause.assert_called_once()

    # --- handle_volume_change ---

    def test_volume_up(self, ctrl) -> None:
        ctrl.audio_player.get_volume.return_value = 0.5
        ctrl.handle_volume_change(10)
        ctrl.audio_player.set_volume.assert_called_once_with(0.6)
        ctrl.status_bar.showMessage.assert_called_once()

    def test_volume_clamp_at_max(self, ctrl) -> None:
        ctrl.audio_player.get_volume.return_value = 0.95
        ctrl.handle_volume_change(10)
        ctrl.audio_player.set_volume.assert_called_once_with(1.0)

    def test_volume_clamp_at_min(self, ctrl) -> None:
        ctrl.audio_player.get_volume.return_value = 0.05
        ctrl.handle_volume_change(-10)
        ctrl.audio_player.set_volume.assert_called_once_with(0.0)

    def test_volume_change_error(self, ctrl) -> None:
        ctrl.audio_player.get_volume.side_effect = RuntimeError("fail")
        ctrl.handle_volume_change(10)

    # --- handle_mute_toggle ---

    def test_mute_when_playing(self, ctrl) -> None:
        ctrl.audio_player.get_volume.return_value = 0.7
        ctrl.handle_mute_toggle()
        assert ctrl._previous_volume == 0.7
        ctrl.audio_player.set_volume.assert_called_once_with(0.0)
        ctrl.status_bar.showMessage.assert_called_once()

    def test_unmute_restores_volume(self, ctrl) -> None:
        ctrl.audio_player.get_volume.return_value = 0.0
        ctrl._previous_volume = 0.6
        ctrl.handle_mute_toggle()
        ctrl.audio_player.set_volume.assert_called_once_with(0.6)

    def test_mute_toggle_error(self, ctrl) -> None:
        ctrl.audio_player.get_volume.side_effect = RuntimeError("fail")
        ctrl.handle_mute_toggle()

    # --- on_global_prev_clicked playlist ---

    def test_prev_playlist_mode(self, ctrl) -> None:
        ctrl._playback_source = "playlist"
        ctrl._current_playlist_songs = [{"id": 1}, {"id": 2}]
        ctrl._current_playlist_index = 1
        ctrl.db_manager.get_song_by_id.return_value = None
        ctrl.on_global_prev_clicked()


# ==========================================
# RemoteController — uncovered paths
# ==========================================


class TestRemoteControllerPhase2:
    """Cover uncovered RemoteController paths."""

    @pytest.fixture
    def ctrl(self):
        with patch("controllers.remote_controller.QObject.__init__"):
            from controllers.remote_controller import RemoteController

            c = RemoteController.__new__(RemoteController)
            c.audio_player = Mock()
            c.audio_player.get_position.return_value = 60.0
            c.audio_player.get_duration.return_value = 200.0
            c.audio_player.is_playing.return_value = True
            c.audio_player.get_volume.return_value = 0.8
            c.now_playing = Mock()
            c.now_playing.volume_slider = Mock()
            c.now_playing.volume_label_value = Mock()
            c.now_playing.current_song = {"title": "Song", "artist": "Art", "album": "Alb"}
            c._remote_server = None
            c._remote_update_timer = None
            c._global_next_callback = None
            c._global_prev_callback = None
            return c

    def test_init_proper_construction(self) -> None:
        """Test RemoteController.__init__ with QObject patched."""
        with patch("controllers.remote_controller.QObject.__init__"):
            from controllers.remote_controller import RemoteController

            audio = Mock()
            now = Mock()
            c = RemoteController(audio, now)

            assert c.audio_player is audio
            assert c.now_playing is now
            assert c._remote_server is None
            assert c._remote_update_timer is None
            assert c._global_next_callback is None
            assert c._global_prev_callback is None

    def test_connect_server(self, ctrl) -> None:
        """connect_server connects signals and starts timer."""
        mock_server = Mock()
        mock_server.command_received = Mock()

        with patch.dict("sys.modules", {"services.remote_server": Mock()}):
            import sys as _sys

            mock_mod = _sys.modules["services.remote_server"]
            mock_mod.RemoteServer.get_instance.return_value = mock_server

            with patch("controllers.remote_controller.QTimer") as MockTimer:
                mock_timer_instance = Mock()
                MockTimer.return_value = mock_timer_instance
                MockTimer.singleShot = Mock()

                ctrl.connect_server()

                assert ctrl._remote_server is mock_server
                mock_timer_instance.start.assert_called_once()

    def test_connect_server_import_error(self, ctrl) -> None:
        """connect_server handles ImportError gracefully."""
        # Make the local import fail
        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def fail_import(name, *args, **kwargs):
            if name == "services.remote_server":
                raise ImportError("no flask")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fail_import):
            ctrl.connect_server()

        assert ctrl._remote_server is None

    def test_update_now_playing_with_server(self, ctrl) -> None:
        """update_now_playing sends info to remote server."""
        mock_server = Mock()
        ctrl._remote_server = mock_server

        with patch.dict("sys.modules", {"services.remote_server": Mock()}):
            import sys as _sys

            mock_npi = Mock()
            _sys.modules["services.remote_server"].NowPlayingInfo = mock_npi
            mock_info = Mock()
            mock_npi.return_value = mock_info

            ctrl.update_now_playing()

            mock_npi.assert_called_once()
            mock_server.update_now_playing.assert_called_once_with(mock_info)

    def test_update_now_playing_no_song(self, ctrl) -> None:
        """update_now_playing with no current_song uses empty strings."""
        mock_server = Mock()
        ctrl._remote_server = mock_server
        ctrl.now_playing.current_song = None

        with patch.dict("sys.modules", {"services.remote_server": Mock()}):
            import sys as _sys

            mock_npi = Mock()
            _sys.modules["services.remote_server"].NowPlayingInfo = mock_npi

            ctrl.update_now_playing()

            call_kwargs = mock_npi.call_args[1]
            assert call_kwargs["title"] == ""
            assert call_kwargs["artist"] == ""

    def test_update_now_playing_exception(self, ctrl) -> None:
        """update_now_playing catches exceptions silently."""
        ctrl._remote_server = Mock()

        with patch.dict("sys.modules", {"services.remote_server": Mock()}):
            import sys as _sys

            _sys.modules["services.remote_server"].NowPlayingInfo.side_effect = RuntimeError("fail")

            ctrl.update_now_playing()  # should not raise

    def test_handle_command_error(self, ctrl) -> None:
        """handle_command catches RuntimeError."""
        ctrl.audio_player.play.side_effect = RuntimeError("fail")
        ctrl.handle_command("play", {})

    def test_sync_volume_ui(self, ctrl) -> None:
        ctrl._sync_volume_ui(50)
        ctrl.now_playing.volume_slider.blockSignals.assert_called()
        ctrl.now_playing.volume_slider.setValue.assert_called_once_with(50)


# ==========================================
# LibraryController — uncovered paths
# ==========================================


class TestLibraryControllerPhase2:
    """Cover uncovered LibraryController paths."""

    @pytest.fixture
    def ctrl(self):
        from controllers.library_controller import LibraryController

        c = LibraryController(db_manager=Mock(), status_bar=Mock())
        c.tabs = Mock()
        c.library_tab = Mock()
        c.search_tab = Mock()
        c.recommendations_widget = Mock()
        return c

    def test_set_widgets_all_params(self, ctrl) -> None:
        tabs = Mock()
        lib = Mock()
        search = Mock()
        rec = Mock()
        sb = Mock()

        ctrl.set_widgets(tabs=tabs, library_tab=lib, search_tab=search, recommendations_widget=rec, status_bar=sb)

        assert ctrl.tabs is tabs
        assert ctrl.library_tab is lib
        assert ctrl.search_tab is search
        assert ctrl.recommendations_widget is rec
        assert ctrl.status_bar is sb

    def test_handle_switch_tab_queue(self, ctrl) -> None:
        """Switch to queue tab by searching tab texts."""
        ctrl.tabs.count.return_value = 3
        tab_names = {0: "Library", 1: "Import", 2: "Queue"}
        ctrl.tabs.tabText = Mock(side_effect=lambda i: tab_names[i])

        ctrl.handle_switch_tab("queue")

        ctrl.tabs.setCurrentIndex.assert_called_once_with(2)

    def test_handle_switch_tab_queue_cola(self, ctrl) -> None:
        """Switch to queue tab with Spanish 'Cola' label."""
        ctrl.tabs.count.return_value = 2
        tab_names = {0: "Biblioteca", 1: "Cola de descargas"}
        ctrl.tabs.tabText = Mock(side_effect=lambda i: tab_names[i])

        ctrl.handle_switch_tab("queue")

        ctrl.tabs.setCurrentIndex.assert_called_once_with(1)

    def test_handle_switch_tab_no_tabs(self, ctrl) -> None:
        ctrl.tabs = None
        ctrl.handle_switch_tab("library")

    def test_check_empty_library_with_import_tab(self, ctrl) -> None:
        """Empty library switches to Import tab."""
        ctrl.db_manager.get_song_count.return_value = 0
        ctrl.tabs.count.return_value = 3
        tab_names = {0: "Library", 1: "Import", 2: "Search"}
        ctrl.tabs.tabText = Mock(side_effect=lambda i: tab_names[i])

        with patch("controllers.library_controller.QMessageBox"):
            ctrl.check_empty_library(Mock())

        ctrl.tabs.setCurrentIndex.assert_called_once_with(1)

    def test_check_empty_library_exception(self, ctrl) -> None:
        ctrl.db_manager.get_song_count.side_effect = RuntimeError("db error")
        ctrl.check_empty_library(Mock())

    def test_on_album_selected_no_library(self, ctrl) -> None:
        ctrl.library_tab = None
        ctrl.on_album_selected({"album": "Test", "artist": "Art"})
        ctrl.tabs.setCurrentWidget.assert_not_called()

    def test_update_recommendations_no_widget(self, ctrl) -> None:
        ctrl.recommendations_widget = None
        ctrl.update_recommendations({"title": "X"})


# ==========================================
# UIComposer — uncovered paths
# ==========================================


class TestUIComposerPhase2:
    """Cover UIComposer business logic paths via mocking."""

    @pytest.fixture
    def composer(self):
        from controllers.ui_composer import UIComposer

        c = UIComposer.__new__(UIComposer)
        c.window = Mock()
        c.window.statusBar = Mock()
        c.window.visualizer = Mock()
        c.db_manager = Mock()
        c.audio_player = Mock()
        c.playlist_manager = Mock()
        c.waveform_extractor = Mock()
        c.config_manager = Mock()
        c.download_queue = Mock()
        c.theme_manager = Mock()
        c.shortcuts_manager = Mock()
        c.genius_client = Mock()
        c._spectrum_worker = None
        return c

    # --- __init__ ---

    def test_init_stores_all_deps(self) -> None:
        from controllers.ui_composer import UIComposer

        mocks = {
            k: Mock()
            for k in [
                "window",
                "db_manager",
                "audio_player",
                "playlist_manager",
                "waveform_extractor",
                "config_manager",
                "download_queue",
                "theme_manager",
                "shortcuts_manager",
                "genius_client",
            ]
        }
        c = UIComposer(**mocks)
        for k, v in mocks.items():
            assert getattr(c, k) is v
        assert c._spectrum_worker is None

    # --- _load_tab ---

    def test_load_tab(self, composer) -> None:
        composer.window.tabs = Mock()
        widget = Mock()

        with patch("controllers.ui_composer.tr", return_value="Tab Title"):
            result = composer._load_tab(widget, "test_tab", "tab_test")

        assert result is widget
        assert getattr(composer.window, "test_tab") is widget
        composer.window.tabs.addTab.assert_called_once()

    # --- _connect_data_changed_signals ---

    def test_connect_data_changed_signals(self, composer) -> None:
        w = Mock()
        w.library_tab = Mock()
        w.statistics_tab = Mock()

        import_tab = Mock()
        import_tab.data_changed = Mock()
        w.import_tab = import_tab
        w.cleanup_tab = Mock()
        w.cleanup_tab.data_changed = Mock()
        w.organize_tab = Mock()
        w.organize_tab.data_changed = Mock()
        w.cloud_sync_tab = Mock()
        w.cloud_sync_tab.data_changed = Mock()

        composer.download_queue = Mock()
        composer.download_queue.item_completed = Mock()

        composer._connect_data_changed_signals(w)

        composer.download_queue.item_completed.connect.assert_called_once()
        assert import_tab.data_changed.connect.call_count >= 1

    def test_connect_data_changed_queue_error(self, composer) -> None:
        """Exception in queue connection is caught."""
        w = Mock()
        w.library_tab = Mock()
        w.statistics_tab = None
        w.import_tab = None
        w.cleanup_tab = None
        w.organize_tab = None
        w.cloud_sync_tab = None

        composer.download_queue = Mock()
        composer.download_queue.item_completed.connect.side_effect = RuntimeError("signal error")

        composer._connect_data_changed_signals(w)  # should not raise

    def test_connect_data_changed_no_library(self, composer) -> None:
        w = Mock(spec=[])
        # Mock with no attributes
        for attr in ["library_tab", "statistics_tab", "import_tab", "cleanup_tab", "organize_tab", "cloud_sync_tab"]:
            setattr(w, attr, None)
        composer.download_queue = Mock()
        composer._connect_data_changed_signals(w)

    # --- _on_song_loaded ---

    def test_on_song_loaded_starts_worker(self, composer) -> None:
        composer.audio_player.get_duration.return_value = 200.0

        with patch("core.spectrum_worker.SpectrumWorker") as MockSW:
            mock_worker = Mock()
            MockSW.return_value = mock_worker
            composer._on_song_loaded("/music/test.mp3")
            mock_worker.start.assert_called_once()
            assert composer._spectrum_worker is mock_worker

    def test_on_song_loaded_stops_existing_worker(self, composer) -> None:
        old_worker = Mock()
        old_worker.isRunning.return_value = True
        composer._spectrum_worker = old_worker
        composer.audio_player.get_duration.return_value = 200.0

        with patch("core.spectrum_worker.SpectrumWorker") as MockSW:
            MockSW.return_value = Mock()
            composer._on_song_loaded("/music/test.mp3")

        old_worker.terminate.assert_called_once()
        old_worker.wait.assert_called_once()

    def test_on_song_loaded_error(self, composer) -> None:
        composer.audio_player.get_duration.side_effect = RuntimeError("fail")
        composer._on_song_loaded("/music/test.mp3")
        composer.window.statusBar.showMessage.assert_called()
        composer.window.visualizer.clear.assert_called_once()

    # --- _on_spectrum_extracted ---

    def test_on_spectrum_extracted(self, composer) -> None:
        data = [[0.1, 0.2], [0.3, 0.4]]
        composer._on_spectrum_extracted(data, 180.0, 200.0, "/music/test.mp3")
        composer.window.visualizer.set_spectrum.assert_called_once_with(data, 180.0)
        composer.window.visualizer.set_duration.assert_called_once_with(200.0)

    def test_on_spectrum_extracted_error(self, composer) -> None:
        composer.window.visualizer.set_spectrum.side_effect = ValueError("bad data")
        composer._on_spectrum_extracted([], 0, 0, "/music/test.mp3")
        composer.window.statusBar.showMessage.assert_called()

    # --- _on_spectrum_error ---

    def test_on_spectrum_error_waveform_fallback(self, composer) -> None:
        composer.waveform_extractor.extract.return_value = [0.1, 0.2, 0.3]
        composer._on_spectrum_error("fft failed", "/music/test.mp3", 200.0)
        composer.window.visualizer.set_waveform.assert_called_once()
        composer.window.visualizer.set_duration.assert_called_once_with(200.0)

    def test_on_spectrum_error_waveform_empty(self, composer) -> None:
        composer.waveform_extractor.extract.return_value = None
        composer._on_spectrum_error("fft failed", "/music/test.mp3", 200.0)
        composer.window.visualizer.clear.assert_called_once()

    def test_on_spectrum_error_fallback_exception(self, composer) -> None:
        composer.waveform_extractor.extract.side_effect = OSError("disk error")
        composer._on_spectrum_error("fft failed", "/music/test.mp3", 200.0)
        composer.window.visualizer.clear.assert_called_once()

    # --- Dialog handlers ---

    def test_toggle_theme(self, composer) -> None:
        composer.theme_manager.toggle_theme.return_value = "light"
        with patch("controllers.ui_composer.tr", return_value="Theme switched"):
            composer._toggle_theme()
        composer.theme_manager.toggle_theme.assert_called_once()
        composer.window.statusBar.showMessage.assert_called_once()

    def test_change_language_success(self, composer) -> None:
        with patch("controllers.ui_composer.set_language", return_value=True), patch(
            "controllers.ui_composer.QMessageBox"
        ) as MockMB, patch("controllers.ui_composer.tr", return_value="Changed"):
            composer._change_language("en")
            MockMB.information.assert_called_once()

    def test_change_language_invalid(self, composer) -> None:
        with patch("controllers.ui_composer.set_language", return_value=False):
            composer._change_language("xx")

    def test_show_about(self, composer) -> None:
        with patch("controllers.ui_composer.QMessageBox") as MockMB:
            composer._show_about()
            MockMB.about.assert_called_once()

    def test_show_shortcuts_dialog(self, composer) -> None:
        composer.shortcuts_manager.get_shortcuts.return_value = []
        with patch("gui.dialogs.shortcuts_dialog.ShortcutsDialog") as MockSD:
            mock_dialog = Mock()
            MockSD.return_value = mock_dialog
            composer._show_shortcuts_dialog()
            mock_dialog.exec.assert_called_once()

    def test_show_api_settings(self, composer) -> None:
        with patch("gui.dialogs.api_settings_dialog.APISettingsDialog") as MockASD:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = True
            MockASD.return_value = mock_dialog
            composer._show_api_settings()
            mock_dialog.exec.assert_called_once()

    def test_show_api_settings_cancelled(self, composer) -> None:
        with patch("gui.dialogs.api_settings_dialog.APISettingsDialog") as MockASD:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = False
            MockASD.return_value = mock_dialog
            composer._show_api_settings()

    def test_show_equalizer(self, composer) -> None:
        with patch("controllers.ui_composer.QDialog") as MockDialog, patch(
            "controllers.ui_composer.QVBoxLayout"
        ), patch("gui.widgets.equalizer_widget.EqualizerWidget") as MockEQ:
            mock_eq = Mock()
            MockEQ.return_value = mock_eq
            mock_dialog = Mock()
            MockDialog.return_value = mock_dialog
            composer.audio_player.set_equalizer_gains = Mock()
            composer._show_equalizer()
            mock_dialog.exec.assert_called_once()

    def test_show_api_guide(self, composer) -> None:
        with patch("controllers.ui_composer.QDialog") as MockDialog, patch(
            "controllers.ui_composer.QVBoxLayout"
        ), patch("controllers.ui_composer.QPushButton"), patch("PySide6.QtWidgets.QTextBrowser"):
            mock_dialog = Mock()
            MockDialog.return_value = mock_dialog
            composer._show_api_guide()
            mock_dialog.exec.assert_called_once()
