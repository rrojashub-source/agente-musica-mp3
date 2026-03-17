"""
Phase 2 Tests for src/main.py — MAPS Round 28

Covers MusicPlayerApp methods:
- _on_song_play_started (play count + stats refresh)
- closeEvent (cleanup: audio, queue, db)
- _init_services (service initialization + error paths)
- _init_controllers (controller creation)
- _connect_signals (signal wiring)
- main() entry point

Pattern: Patch QMainWindow to a real base class before importing main,
so MusicPlayerApp methods are real Python functions (not MagicMock).
"""

import os
import sqlite3
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Ensure QMainWindow is a real class (not MagicMock) before importing main
# This lets MusicPlayerApp's class body execute normally.
_qt_widgets = sys.modules.get("PySide6.QtWidgets")
if _qt_widgets is not None:
    _orig_qmainwindow = getattr(_qt_widgets, "QMainWindow", None)
    _is_mock = not isinstance(_orig_qmainwindow, type)
    if _is_mock:
        _qt_widgets.QMainWindow = type(
            "QMainWindow",
            (),
            {
                "__init__": lambda self, *a, **k: None,
                "setWindowTitle": lambda self, *a: None,
                "setGeometry": lambda self, *a: None,
                "statusBar": lambda self: MagicMock(),
                "addAction": lambda self, *a: None,
                "show": lambda self: None,
            },
        )

# Force re-import of main with the real QMainWindow
if "main" in sys.modules:
    del sys.modules["main"]

from main import MusicPlayerApp  # noqa: E402


@pytest.fixture
def mock_self():
    """Create a mock object with all attributes MusicPlayerApp methods need."""
    ms = MagicMock()
    ms.db_manager = MagicMock()
    ms.audio_player = MagicMock()
    ms.playlist_manager = MagicMock()
    ms.waveform_extractor = MagicMock()
    ms.config_manager = MagicMock()
    ms.download_queue = MagicMock()
    ms.theme_manager = MagicMock()
    ms.shortcuts_manager = MagicMock()
    ms.genius_client = MagicMock()
    ms.now_playing = MagicMock()
    ms.tabs = MagicMock()
    ms.library_tab = MagicMock()
    ms.playlist_widget = MagicMock()
    ms.albums_widget = MagicMock()
    ms.search_tab = MagicMock()
    ms.recommendations_widget = MagicMock()
    ms.visualizer = MagicMock()
    ms.lyrics_tab = MagicMock()
    ms.chords_tab = MagicMock()
    ms.statistics_tab = MagicMock()
    ms.statusBar = MagicMock()
    ms._playback = MagicMock()
    ms._remote = MagicMock()
    ms._library_ctrl = MagicMock()
    ms._ui = MagicMock()
    ms.addAction = MagicMock()
    return ms


# Helper to get methods from MusicPlayerApp.__dict__
def _method(name):
    """Get method from MusicPlayerApp.__dict__."""
    return MusicPlayerApp.__dict__[name]


# --- _on_song_play_started ---


class TestOnSongPlayStarted:
    def test_with_id(self, mock_self):
        """Song with ID increments play count and refreshes stats."""
        func = _method("_on_song_play_started")
        mock_library = MagicMock()
        mock_module = MagicMock()
        mock_module.LibraryService.get_instance.return_value = mock_library
        with patch.dict("sys.modules", {"services.library_service": mock_module}):
            func(mock_self, {"id": 42, "title": "Test"})
            mock_library.increment_play_count.assert_called_once_with(42)
            mock_self.statistics_tab.refresh_stats.assert_called_once()

    def test_no_id(self, mock_self):
        """Song without ID does not increment play count."""
        func = _method("_on_song_play_started")
        func(mock_self, {"title": "No ID"})

    def test_no_statistics_tab(self, mock_self):
        """Play count works without statistics tab."""
        func = _method("_on_song_play_started")
        mock_self.statistics_tab = None
        mock_library = MagicMock()
        mock_module = MagicMock()
        mock_module.LibraryService.get_instance.return_value = mock_library
        with patch.dict("sys.modules", {"services.library_service": mock_module}):
            func(mock_self, {"id": 1})
            mock_library.increment_play_count.assert_called_once_with(1)

    def test_exception(self, mock_self):
        """Exception in play count is caught gracefully."""
        func = _method("_on_song_play_started")
        mock_module = MagicMock()
        mock_module.LibraryService.get_instance.side_effect = RuntimeError("fail")
        with patch.dict("sys.modules", {"services.library_service": mock_module}):
            func(mock_self, {"id": 99})  # Should not raise


# --- closeEvent ---


class TestCloseEvent:
    def test_success(self, mock_self):
        """closeEvent cleans up all services."""
        func = _method("closeEvent")
        event = MagicMock()
        func(mock_self, event)
        mock_self.audio_player.cleanup.assert_called_once()
        mock_self.download_queue.stop.assert_called_once()
        mock_self.db_manager.close.assert_called_once()
        event.accept.assert_called_once()

    def test_audio_error(self, mock_self):
        """closeEvent handles audio cleanup error."""
        func = _method("closeEvent")
        event = MagicMock()
        mock_self.audio_player.cleanup.side_effect = RuntimeError("mpv")
        func(mock_self, event)
        mock_self.db_manager.close.assert_called_once()
        event.accept.assert_called_once()

    def test_queue_error(self, mock_self):
        """closeEvent handles queue stop error."""
        func = _method("closeEvent")
        event = MagicMock()
        mock_self.download_queue.stop.side_effect = RuntimeError("queue")
        func(mock_self, event)
        mock_self.db_manager.close.assert_called_once()
        event.accept.assert_called_once()

    def test_db_error(self, mock_self):
        """closeEvent handles database close error."""
        func = _method("closeEvent")
        event = MagicMock()
        mock_self.db_manager.close.side_effect = sqlite3.Error("db")
        func(mock_self, event)
        event.accept.assert_called_once()


# --- _init_controllers ---


class TestInitControllers:
    def test_creates_all_controllers(self, mock_self):
        """_init_controllers creates playback, remote, and library controllers."""
        func = _method("_init_controllers")
        with patch("main.PlaybackController") as mock_pc, patch("main.RemoteController") as mock_rc, patch(
            "main.LibraryController"
        ) as mock_lc:
            mock_pc.return_value = MagicMock()
            mock_rc.return_value = MagicMock()
            mock_lc.return_value = MagicMock()

            func(mock_self)

            mock_pc.assert_called_once()
            mock_pc.return_value.set_widgets.assert_called_once()
            mock_rc.assert_called_once()
            mock_rc.return_value.set_navigation_callbacks.assert_called_once()
            mock_lc.assert_called_once()
            mock_lc.return_value.set_widgets.assert_called_once()


# --- _connect_signals ---


class TestConnectSignals:
    def test_all_signals_connected(self, mock_self):
        """_connect_signals wires up all signal connections."""
        func = _method("_connect_signals")

        mock_qtgui = MagicMock()
        mock_action = MagicMock()
        mock_qtgui.QAction.return_value = mock_action
        mock_qtgui.QKeySequence = MagicMock()

        with patch.dict("sys.modules", {"PySide6.QtGui": mock_qtgui}):
            func(mock_self)

        # Core signals
        mock_self.now_playing.prev_clicked.connect.assert_called()
        mock_self.now_playing.next_clicked.connect.assert_called()
        mock_self.now_playing.song_ended.connect.assert_called()
        assert mock_self.now_playing.song_metadata_changed.connect.call_count >= 2

        # Optional widget signals
        mock_self.recommendations_widget.song_selected.connect.assert_called()
        mock_self.library_tab.playback_started.connect.assert_called()
        mock_self.library_tab.find_similar_requested.connect.assert_called()
        mock_self.albums_widget.album_selected.connect.assert_called()
        mock_self.playlist_widget.play_song_requested.connect.assert_called()

        # Keyboard shortcuts
        sm = mock_self.shortcuts_manager
        sm.play_pause_requested.connect.assert_called()
        sm.seek_backward_requested.connect.assert_called()
        sm.seek_forward_requested.connect.assert_called()
        sm.volume_change_requested.connect.assert_called()
        sm.mute_toggled.connect.assert_called()
        sm.focus_search_requested.connect.assert_called()
        sm.switch_to_tab_requested.connect.assert_called()

        # F11 action
        mock_qtgui.QAction.assert_called_once()
        mock_self.addAction.assert_called_once()

    def test_no_optional_widgets(self, mock_self):
        """_connect_signals skips missing optional widgets via hasattr."""
        func = _method("_connect_signals")

        # Use spec to control which attributes exist
        mock_limited = MagicMock(
            spec=[
                "now_playing",
                "_playback",
                "_library_ctrl",
                "_on_song_play_started",
                "shortcuts_manager",
                "visualizer",
                "addAction",
            ]
        )
        mock_limited.now_playing = MagicMock()
        mock_limited._playback = MagicMock()
        mock_limited._library_ctrl = MagicMock()
        mock_limited._on_song_play_started = MagicMock()
        mock_limited.shortcuts_manager = MagicMock()
        mock_limited.visualizer = MagicMock()
        mock_limited.addAction = MagicMock()

        mock_qtgui = MagicMock()
        mock_qtgui.QAction = MagicMock(return_value=MagicMock())
        mock_qtgui.QKeySequence = MagicMock()

        with patch.dict("sys.modules", {"PySide6.QtGui": mock_qtgui}):
            func(mock_limited)

        # Core signals still connected
        mock_limited.now_playing.prev_clicked.connect.assert_called()


# --- _init_services ---


class TestInitServices:
    def test_success_with_genius(self, mock_self):
        """_init_services initializes all services with Genius token."""
        func = _method("_init_services")
        with patch("main.DatabaseManager") as mock_db, patch("main.AudioPlayer") as mock_audio, patch(
            "main.PlaylistManager"
        ) as mock_pm, patch("main.WaveformExtractor") as mock_wf, patch("main.ConfigManager") as mock_cfg, patch(
            "main.DownloadQueue"
        ) as mock_dq, patch(
            "main.ThemeManager"
        ) as mock_tm, patch(
            "main.KeyboardShortcutManager"
        ) as mock_ks, patch(
            "main.QApplication"
        ) as mock_qapp, patch(
            "main.GeniusClient"
        ) as mock_gc:
            mock_qapp.instance.return_value = MagicMock()
            mock_db.return_value = MagicMock()
            mock_dq.return_value = MagicMock()

            mock_cred = MagicMock()
            mock_cred.load_credential.return_value = "test_token"
            with patch.dict("sys.modules", {"utils.credentials": mock_cred}):
                func(mock_self)

            mock_db.assert_called_once()
            mock_audio.assert_called_once()
            mock_pm.assert_called_once()
            mock_wf.assert_called_once()
            mock_cfg.assert_called_once()
            mock_dq.assert_called_once()
            mock_tm.assert_called_once()
            mock_ks.assert_called_once()
            mock_gc.assert_called_once_with("test_token")

    def test_no_genius_token(self, mock_self):
        """_init_services works without Genius token."""
        func = _method("_init_services")
        with patch("main.DatabaseManager") as mock_db, patch("main.AudioPlayer"), patch("main.PlaylistManager"), patch(
            "main.WaveformExtractor"
        ), patch("main.ConfigManager"), patch("main.DownloadQueue") as mock_dq, patch("main.ThemeManager"), patch(
            "main.KeyboardShortcutManager"
        ), patch(
            "main.QApplication"
        ) as mock_qapp:
            mock_qapp.instance.return_value = MagicMock()
            mock_db.return_value = MagicMock()
            mock_dq.return_value = MagicMock()

            mock_cred = MagicMock()
            mock_cred.load_credential.return_value = None
            with patch.dict("sys.modules", {"utils.credentials": mock_cred}):
                func(mock_self)

            assert mock_self.genius_client is None

    def test_genius_error(self, mock_self):
        """_init_services handles Genius client initialization error."""
        func = _method("_init_services")
        with patch("main.DatabaseManager") as mock_db, patch("main.AudioPlayer"), patch("main.PlaylistManager"), patch(
            "main.WaveformExtractor"
        ), patch("main.ConfigManager"), patch("main.DownloadQueue") as mock_dq, patch("main.ThemeManager"), patch(
            "main.KeyboardShortcutManager"
        ), patch(
            "main.QApplication"
        ) as mock_qapp, patch(
            "main.GeniusClient", side_effect=RuntimeError("API error")
        ):
            mock_qapp.instance.return_value = MagicMock()
            mock_db.return_value = MagicMock()
            mock_dq.return_value = MagicMock()

            mock_cred = MagicMock()
            mock_cred.load_credential.return_value = "bad_token"
            with patch.dict("sys.modules", {"utils.credentials": mock_cred}):
                func(mock_self)

            assert mock_self.genius_client is None

    def test_db_error(self, mock_self):
        """_init_services exits on database error."""
        func = _method("_init_services")
        with patch("main.DatabaseManager", side_effect=sqlite3.Error("DB fail")), patch(
            "main.QMessageBox"
        ) as mock_msgbox, pytest.raises(SystemExit):
            func(mock_self)
        mock_msgbox.critical.assert_called_once()


# --- main() entry point ---


class TestMainEntryPoint:
    def test_main_runs(self):
        """main() creates app, loads language, creates window, and exits."""
        from main import main

        mock_qapp = MagicMock()
        mock_qapp.exec.return_value = 0

        mock_settings = MagicMock()
        mock_settings.value.return_value = "es"

        mock_qtcore = MagicMock()
        mock_qtcore.QSettings.return_value = mock_settings
        mock_qtgui = MagicMock()
        mock_qtgui.QFont.return_value = MagicMock()

        with patch("main.QApplication", return_value=mock_qapp), patch("main.MusicPlayerApp") as mock_app_cls, patch(
            "main.set_language"
        ) as mock_set_lang, patch.dict(
            "sys.modules",
            {
                "PySide6.QtCore": mock_qtcore,
                "PySide6.QtGui": mock_qtgui,
            },
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

            mock_app_cls.assert_called_once()
            mock_set_lang.assert_called_with("es")
            mock_qapp.setApplicationName.assert_called_once()
            mock_qapp.setStyle.assert_called_once_with("Fusion")

    def test_main_english(self):
        """main() loads English language preference."""
        from main import main

        mock_qapp = MagicMock()
        mock_qapp.exec.return_value = 0

        mock_settings = MagicMock()
        mock_settings.value.return_value = "en"

        mock_qtcore = MagicMock()
        mock_qtcore.QSettings.return_value = mock_settings
        mock_qtgui = MagicMock()
        mock_qtgui.QFont.return_value = MagicMock()

        with patch("main.QApplication", return_value=mock_qapp), patch("main.MusicPlayerApp"), patch(
            "main.set_language"
        ) as mock_set_lang, patch.dict(
            "sys.modules",
            {
                "PySide6.QtCore": mock_qtcore,
                "PySide6.QtGui": mock_qtgui,
            },
        ):
            with pytest.raises(SystemExit):
                main()
            mock_set_lang.assert_called_with("en")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
