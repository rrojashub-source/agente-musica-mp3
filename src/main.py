#!/usr/bin/env python3
"""
NEXUS Music Manager — Main Application Facade (Phase 2.1)

Thin facade that initializes services, delegates UI creation to UIComposer,
and connects controllers. All logic lives in controllers/.

Project: AGENTE_MUSICA_MP3_001
Version: 2.1 (Post-refactoring Phase 2.1)
"""

# CRITICAL: Patch subprocess FIRST to hide console windows on Windows
import utils.subprocess_patch  # noqa: F401

import sqlite3
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Multi-language translation system
from translations import tr, set_language

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
    from PySide6.QtCore import Qt
except ImportError as e:
    print("PySide6 not installed. Install with: pip install PySide6")
    sys.exit(1)

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import core services
from database.manager import DatabaseManager
from core.audio_player import AudioPlayer
from core.playlist_manager import PlaylistManager
from core.waveform_extractor import WaveformExtractor
from core.download_queue import DownloadQueue
from core.theme_manager import ThemeManager
from core.keyboard_shortcuts import KeyboardShortcutManager
from config_manager import ConfigManager
from api.genius_client import GeniusClient
from utils.constants import MAX_CONCURRENT_DOWNLOADS, MAX_DOWNLOAD_RETRIES, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT

# Import controllers
from controllers.playback_controller import PlaybackController
from controllers.remote_controller import RemoteController
from controllers.ui_composer import UIComposer
from controllers.library_controller import LibraryController

import keyring


class MusicPlayerApp(QMainWindow):
    """Main application window — thin facade delegating to controllers"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setGeometry(100, 100, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        # Phase 1: Initialize services
        self._init_services()

        # Phase 2: Build UI (sets widget attributes on self)
        self._ui = UIComposer(
            window=self,
            db_manager=self.db_manager,
            audio_player=self.audio_player,
            playlist_manager=self.playlist_manager,
            waveform_extractor=self.waveform_extractor,
            config_manager=self.config_manager,
            download_queue=self.download_queue,
            theme_manager=self.theme_manager,
            shortcuts_manager=self.shortcuts_manager,
            genius_client=self.genius_client,
        )
        self._ui.compose()

        # Phase 3: Create controllers
        self._init_controllers()

        # Phase 4: Connect all signals
        self._connect_signals()

        # Phase 5: Post-init
        self.theme_manager.apply_theme(self.theme_manager.current_theme)
        self.shortcuts_manager.setup_shortcuts(self)

        if hasattr(self, 'lyrics_tab') and self.lyrics_tab:
            self.now_playing.song_metadata_changed.connect(self.lyrics_tab.on_song_changed)

        if hasattr(self, 'chords_tab') and self.chords_tab:
            self.now_playing.song_metadata_changed.connect(self.chords_tab.on_song_changed)

        logger.info("Application started successfully")
        self._library_ctrl.check_empty_library(self)

    def _init_services(self):
        """Initialize all core services"""
        # Database
        try:
            self.db_manager = DatabaseManager()
            logger.info("Database initialized successfully")
        except (sqlite3.Error, OSError) as e:
            QMessageBox.critical(
                self, "Database Error",
                f"Failed to initialize database:\n{str(e)}\n\n"
                f"Please check database connection and migrations."
            )
            logger.error(f"Database initialization failed: {e}")
            sys.exit(1)

        # Audio engine
        self.audio_player = AudioPlayer()
        logger.info("Audio player initialized")

        # Playlist manager
        self.playlist_manager = PlaylistManager(self.db_manager)
        logger.info("Playlist manager initialized")

        # Waveform extractor
        self.waveform_extractor = WaveformExtractor()

        # Configuration manager
        self.config_manager = ConfigManager()

        # Download queue
        self.download_queue = DownloadQueue(
            max_concurrent=MAX_CONCURRENT_DOWNLOADS,
            max_retries=MAX_DOWNLOAD_RETRIES,
            db_manager=self.db_manager,
            config_manager=self.config_manager
        )
        self.download_queue.start()
        logger.info("Download queue initialized")

        # Theme manager
        self.theme_manager = ThemeManager()

        # Keyboard shortcuts
        self.shortcuts_manager = KeyboardShortcutManager()
        QApplication.instance().installEventFilter(self.shortcuts_manager)
        logger.info("Keyboard shortcuts manager initialized")

        # Genius API client (optional)
        try:
            genius_token = keyring.get_password("nexus_music", "genius_token")
            if genius_token:
                self.genius_client = GeniusClient(genius_token)
                logger.info("Genius client initialized")
            else:
                self.genius_client = None
                logger.info("Genius API token not found (lyrics disabled)")
        except (keyring.errors.KeyringError, RuntimeError, ValueError) as e:
            logger.error(f"Failed to initialize Genius client: {e}")
            self.genius_client = None

    def _init_controllers(self):
        """Create and configure controllers"""
        # Playback controller
        self._playback = PlaybackController(
            audio_player=self.audio_player,
            now_playing=self.now_playing,
            playlist_manager=self.playlist_manager,
            db_manager=self.db_manager,
            parent=self,
        )
        self._playback.set_widgets(
            library_tab=getattr(self, 'library_tab', None),
            playlist_widget=getattr(self, 'playlist_widget', None),
            status_bar=self.statusBar,
        )

        # Remote controller
        self._remote = RemoteController(
            audio_player=self.audio_player,
            now_playing=self.now_playing,
            parent=self,
        )
        self._remote.set_navigation_callbacks(
            next_callback=self._playback.on_global_next_clicked,
            prev_callback=self._playback.on_global_prev_clicked,
        )

        # Library/navigation controller
        self._library_ctrl = LibraryController(
            db_manager=self.db_manager,
            status_bar=self.statusBar,
        )
        self._library_ctrl.set_widgets(
            tabs=self.tabs,
            library_tab=getattr(self, 'library_tab', None),
            search_tab=getattr(self, 'search_tab', None),
            recommendations_widget=getattr(self, 'recommendations_widget', None),
        )

    def _connect_signals(self):
        """Wire up all signal connections between components"""
        # Now Playing → Playback Controller
        self.now_playing.prev_clicked.connect(self._playback.on_global_prev_clicked)
        self.now_playing.next_clicked.connect(self._playback.on_global_next_clicked)
        self.now_playing.song_ended.connect(self._playback.on_global_song_ended)

        # Now Playing → Library Controller (recommendations)
        self.now_playing.song_metadata_changed.connect(self._library_ctrl.update_recommendations)

        # Now Playing → Play count increment + Statistics refresh
        self.now_playing.song_metadata_changed.connect(self._on_song_play_started)

        # Recommendations → Playback Controller
        if hasattr(self, 'recommendations_widget'):
            self.recommendations_widget.song_selected.connect(self._playback.play_recommended_song)

        # Library Tab → Playback Controller
        if hasattr(self, 'library_tab'):
            self.library_tab.playback_started.connect(self._playback.on_library_playback_started)
            self.library_tab.find_similar_requested.connect(
                self._library_ctrl.on_find_similar_requested
            )

        # Albums → Library Controller
        if hasattr(self, 'albums_widget'):
            self.albums_widget.album_selected.connect(self._library_ctrl.on_album_selected)

        # Playlist → Playback Controller
        if hasattr(self, 'playlist_widget'):
            self.playlist_widget.play_song_requested.connect(
                self._playback.play_song_from_playlist
            )

        # Keyboard shortcuts → Controllers
        sm = self.shortcuts_manager
        sm.play_pause_requested.connect(self._playback.handle_play_pause)
        sm.seek_backward_requested.connect(self._playback.handle_seek_backward)
        sm.seek_forward_requested.connect(self._playback.handle_seek_forward)
        sm.volume_change_requested.connect(self._playback.handle_volume_change)
        sm.mute_toggled.connect(self._playback.handle_mute_toggle)
        sm.focus_search_requested.connect(self._library_ctrl.handle_focus_search)
        sm.switch_to_tab_requested.connect(self._library_ctrl.handle_switch_tab)

        # F11 → Fullscreen visualizer
        from PySide6.QtGui import QAction, QKeySequence
        fullscreen_action = QAction("Fullscreen Visualizer", self)
        fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        fullscreen_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        fullscreen_action.triggered.connect(self.visualizer.toggle_fullscreen)
        self.addAction(fullscreen_action)

        logger.info("All signals connected")

    def _on_song_play_started(self, song_info: dict):
        """Increment play count when a song starts playing"""
        song_id = song_info.get('id')
        if song_id:
            try:
                self.db_manager.execute_query(
                    """UPDATE songs
                       SET play_count = COALESCE(play_count, 0) + 1,
                           last_played = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (song_id,)
                )
                logger.debug(f"Play count incremented for song {song_id}")
                # Refresh statistics if tab exists
                if hasattr(self, 'statistics_tab') and self.statistics_tab:
                    self.statistics_tab.refresh_stats()
            except sqlite3.Error as e:
                logger.error(f"Failed to increment play count: {e}")

    def closeEvent(self, event):
        """Handle application close event"""
        try:
            self.audio_player.cleanup()
            logger.info("Audio player cleaned up")
        except RuntimeError as e:
            logger.error(f"Error cleaning up audio player: {e}")

        try:
            self.download_queue.stop()
            logger.info("Download queue stopped")
        except RuntimeError as e:
            logger.error(f"Error stopping download queue: {e}")

        try:
            self.db_manager.close()
            logger.info("Database closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database: {e}")

        event.accept()
        logger.info("Application closed")


def main():
    """Main entry point"""
    def exception_hook(exc_type, exc_value, exc_traceback):
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    app.setApplicationName("NEXUS Music Manager")
    app.setOrganizationName("NEXUS")

    # Load saved language preference
    from PySide6.QtCore import QSettings
    settings = QSettings("NEXUS", "MusicManager")
    saved_language = settings.value("language", "es")
    set_language(saved_language)
    logger.info(f"Language loaded: {saved_language}")

    app.setStyle("Fusion")

    # Set font with emoji fallback for Windows PySide6
    from PySide6.QtGui import QFont, QFontDatabase
    font = QFont("Segoe UI", 10)
    font.setFamilies(["Segoe UI", "Segoe UI Emoji", "Noto Color Emoji", "Arial"])
    app.setFont(font)

    window = MusicPlayerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
