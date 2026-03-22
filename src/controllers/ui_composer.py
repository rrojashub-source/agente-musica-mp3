"""
UI Composer — Phase 2.1

Builds the complete UI: menu bar, top section (now playing + visualizer),
tab widget with 14 tabs, status bar. Also handles dialog methods and
visualizer signal callbacks.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from api.genius_client import GeniusClient
from config_manager import ConfigManager
from core.audio_player import AudioPlayer
from core.download_queue import DownloadQueue
from core.keyboard_shortcuts import KeyboardShortcutManager
from core.playlist_manager import PlaylistManager
from core.theme_manager import ThemeManager
from core.waveform_extractor import WaveformExtractor
from database.manager import DatabaseManager
from translations import LANGUAGES, get_language, set_language, tr
from utils.constants import APP_VERSION

logger = logging.getLogger(__name__)


class UIComposer:
    """Creates and manages all UI components for the main window"""

    def __init__(
        self,
        window: QMainWindow,
        db_manager: DatabaseManager,
        audio_player: AudioPlayer,
        playlist_manager: PlaylistManager,
        waveform_extractor: WaveformExtractor,
        config_manager: ConfigManager,
        download_queue: DownloadQueue,
        theme_manager: ThemeManager,
        shortcuts_manager: KeyboardShortcutManager,
        genius_client: GeniusClient,
    ) -> None:
        self.window: QMainWindow = window
        self.db_manager: DatabaseManager = db_manager
        self.audio_player: AudioPlayer = audio_player
        self.playlist_manager: PlaylistManager = playlist_manager
        self.waveform_extractor: WaveformExtractor = waveform_extractor
        self.config_manager: ConfigManager = config_manager
        self.download_queue: DownloadQueue = download_queue
        self.theme_manager: ThemeManager = theme_manager
        self.shortcuts_manager: KeyboardShortcutManager = shortcuts_manager
        self.genius_client: GeniusClient = genius_client
        self._spectrum_worker: Optional[Any] = None

    def compose(self) -> None:
        """Build the complete UI. Sets widget references on self.window."""
        self._create_menu_bar()

        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top section: Now Playing + Visualizer + Recommendations
        top_section = self._create_top_section()
        main_layout.addWidget(top_section, stretch=0)

        # Middle section: Tabs
        tab_widget = self._create_tab_widget()
        main_layout.addWidget(tab_widget, stretch=1)

        # Status bar
        self.window.statusBar = QStatusBar()
        self.window.setStatusBar(self.window.statusBar)
        self.window.statusBar.showMessage("Ready")

    # ==========================================
    # Menu Bar
    # ==========================================

    def _create_menu_bar(self) -> None:
        """Create application menu bar"""
        menubar = self.window.menuBar()

        # File menu
        file_menu = menubar.addMenu(tr("menu_file"))
        exit_action = file_menu.addAction(tr("menu_exit"))
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.window.close)

        # Settings menu
        settings_menu = menubar.addMenu(tr("menu_settings"))

        api_settings_action = settings_menu.addAction(tr("menu_api_config"))
        api_settings_action.setShortcut("Ctrl+K")
        api_settings_action.triggered.connect(self._show_api_settings)

        equalizer_action = settings_menu.addAction(tr("menu_equalizer"))
        equalizer_action.setShortcut("Ctrl+E")
        equalizer_action.triggered.connect(self._show_equalizer)

        settings_menu.addSeparator()

        # Language submenu
        language_menu = settings_menu.addMenu(tr("menu_language"))
        for lang_code, lang_name in LANGUAGES.items():
            lang_action = language_menu.addAction(lang_name)
            lang_action.setCheckable(True)
            lang_action.setChecked(lang_code == get_language())
            lang_action.triggered.connect(lambda checked, lc=lang_code: self._change_language(lc))

        # View menu
        view_menu = menubar.addMenu(tr("menu_view"))
        theme_action = view_menu.addAction(tr("menu_toggle_theme"))
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self._toggle_theme)

        # Help menu
        help_menu = menubar.addMenu(tr("menu_help"))

        shortcuts_action = help_menu.addAction(tr("menu_shortcuts"))
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)

        api_guide_action = help_menu.addAction(tr("menu_api_guide"))
        api_guide_action.setShortcut("F2")
        api_guide_action.triggered.connect(self._show_api_guide)

        help_menu.addSeparator()

        about_action = help_menu.addAction(tr("menu_about"))
        about_action.triggered.connect(self._show_about)

    # ==========================================
    # Top Section
    # ==========================================

    def _create_top_section(self) -> QWidget:
        """Create top section with Now Playing + Visualizer + Recommendations"""
        from gui.widgets.now_playing_widget import NowPlayingWidget
        from gui.widgets.recommendations_widget import RecommendationsWidget
        from gui.widgets.visualizer_widget import VisualizerWidget

        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Now Playing Widget (left)
        self.window.now_playing = NowPlayingWidget(self.audio_player)
        top_layout.addWidget(self.window.now_playing, stretch=2)

        # Visualizer Widget (center)
        self.window.visualizer = VisualizerWidget()
        top_layout.addWidget(self.window.visualizer, stretch=3)

        # Recommendations Widget (right)
        self.window.recommendations_widget = RecommendationsWidget(self.db_manager)
        self.window.recommendations_widget.setMaximumWidth(280)
        top_layout.addWidget(self.window.recommendations_widget, stretch=1)

        # Connect visualizer position signal
        self.window.now_playing.position_changed.connect(lambda pos: self.window.visualizer.set_position(pos))

        # Connect song loaded → visualizer analysis
        self.window.now_playing.song_loaded.connect(self._on_song_loaded)

        return top_widget

    # ==========================================
    # Tab Widget (14 tabs)
    # ==========================================

    def _load_tab(self, widget: QWidget, attr_name: str, tab_key: str) -> Optional[QWidget]:
        """Load a tab widget with standard error handling.

        Args:
            widget: The constructed tab/widget instance.
            attr_name: Attribute name to set on self.window (e.g. "import_tab").
            tab_key: Translation key for the tab title (e.g. "tab_import").

        Returns:
            The widget on success, None on failure.
        """
        setattr(self.window, attr_name, widget)
        self.window.tabs.addTab(widget, tr(tab_key))
        logger.info(f"{attr_name} loaded")
        return widget

    def _create_tab_widget(self) -> QTabWidget:
        """Create tab widget with all features"""
        from gui.tabs.chords_tab import ChordsTab
        from gui.tabs.cleanup_tab import CleanupTab
        from gui.tabs.cloud_sync_tab import CloudSyncTab
        from gui.tabs.duplicates_tab import DuplicatesTab
        from gui.tabs.import_tab import ImportTab
        from gui.tabs.library_tab import LibraryTab
        from gui.tabs.lyrics_tab import LyricsTab
        from gui.tabs.organize_tab import OrganizeTab
        from gui.tabs.rename_tab import RenameTab
        from gui.tabs.search_tab import SearchTab
        from gui.tabs.statistics_tab import StatisticsTab
        from gui.widgets.album_grid_widget import AlbumGridWidget
        from gui.widgets.playlist_widget import PlaylistWidget
        from gui.widgets.queue_widget import QueueWidget

        self.window.tabs = QTabWidget()
        self.window.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.window.tabs.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        w = self.window

        # Each tab is loaded with _load_tab() inside a try/except so that
        # a single broken tab cannot prevent the rest of the UI from loading.
        def _try_load(attr_name: str, tab_key: str, factory: Any) -> None:
            try:
                widget = factory()
                self._load_tab(widget, attr_name, tab_key)
            except Exception as e:  # Tab widgets can raise any Qt/import error during construction
                logger.error(f"Failed to load {attr_name}: {e}")
                self.window.tabs.addTab(QWidget(), tr(tab_key) + " (Error)")

        _try_load("import_tab", "tab_import", lambda: ImportTab(self.db_manager))
        _try_load("library_tab", "tab_library", lambda: LibraryTab(self.db_manager, self.audio_player, w.now_playing))
        _try_load("albums_widget", "tab_albums", lambda: AlbumGridWidget(self.db_manager))
        _try_load("lyrics_tab", "tab_lyrics", lambda: LyricsTab(self.genius_client))

        # Chords tab needs client creation
        def _make_chords() -> ChordsTab:
            from api.chords_client import ChordsClient

            client = ChordsClient(db_manager=self.db_manager)
            return ChordsTab(chords_client=client, audio_player=self.audio_player)

        _try_load("chords_tab", "tab_chords", _make_chords)
        _try_load("search_tab", "tab_search", lambda: SearchTab(self.download_queue))
        _try_load("queue_widget", "tab_queue", lambda: QueueWidget(self.download_queue))
        _try_load("duplicates_tab", "tab_duplicates", lambda: DuplicatesTab(self.db_manager))
        _try_load("rename_tab", "tab_rename", lambda: RenameTab(self.db_manager))
        _try_load("organize_tab", "tab_organize", lambda: OrganizeTab(self.db_manager))

        # Cleanup tab uses db_path
        def _make_cleanup() -> CleanupTab:
            db_path = self.db_manager.db_path if hasattr(self.db_manager, "db_path") else "music_library.db"
            return CleanupTab(db_path)

        _try_load("cleanup_tab", "tab_cleanup", _make_cleanup)
        _try_load("playlist_widget", "tab_playlist", lambda: PlaylistWidget(self.playlist_manager, self.db_manager))
        _try_load("cloud_sync_tab", "tab_cloud_sync", lambda: CloudSyncTab(db_manager=self.db_manager))
        _try_load("statistics_tab", "tab_statistics", lambda: StatisticsTab(self.db_manager))

        # Connect all cross-tab signals (data_changed + download queue → refresh)
        self._connect_data_changed_signals(w)

        return self.window.tabs

    def _connect_data_changed_signals(self, w: QMainWindow) -> None:
        """Connect data_changed from all tabs that modify DB → library + statistics refresh"""
        library = getattr(w, "library_tab", None)
        stats = getattr(w, "statistics_tab", None)

        # Connect download queue → library refresh
        try:
            if library and self.download_queue:
                self.download_queue.item_completed.connect(lambda item_id, meta: library.reload_library())
                logger.info("Connected download queue → library refresh")
        except Exception as e:  # Signal connection can fail if widgets were replaced with error stubs
            logger.warning(f"Could not connect queue→library signal: {e}")

        # Connect data_changed from tabs that modify DB
        data_tabs = ["import_tab", "cleanup_tab", "organize_tab", "cloud_sync_tab"]
        for tab_name in data_tabs:
            tab = getattr(w, tab_name, None)
            if tab and hasattr(tab, "data_changed"):
                if library:
                    tab.data_changed.connect(library.reload_library)
                if stats:
                    tab.data_changed.connect(stats.refresh_stats)
                logger.info(f"Connected {tab_name}.data_changed → library/statistics refresh")

    # ==========================================
    # Dialog Handlers
    # ==========================================

    def _show_api_settings(self) -> None:
        """Show API settings dialog"""
        from gui.dialogs.api_settings_dialog import APISettingsDialog

        dialog = APISettingsDialog(self.window)
        if dialog.exec():
            logger.info("API settings updated")
            self.window.statusBar.showMessage("API settings saved successfully", 3000)
        else:
            logger.info("API settings dialog cancelled")

    def _show_equalizer(self) -> None:
        """Show audio equalizer dialog"""
        from gui.widgets.equalizer_widget import EqualizerWidget

        dialog = QDialog(self.window)
        dialog.setWindowTitle(tr("equalizer_title"))
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)
        equalizer = EqualizerWidget()
        layout.addWidget(equalizer)

        if hasattr(self.audio_player, "set_equalizer_gains"):
            equalizer.eq_changed.connect(self.audio_player.set_equalizer_gains)

        dialog.exec()
        logger.info("Equalizer dialog closed")

    def _change_language(self, lang_code: str) -> None:
        """Change application language"""
        from PySide6.QtCore import QSettings

        if set_language(lang_code):
            settings = QSettings("NEXUS", "MusicManager")
            settings.setValue("language", lang_code)

            QMessageBox.information(self.window, tr("language_changed_title"), tr("language_changed_message"))
            logger.info(f"Language changed to: {lang_code}")
        else:
            logger.error(f"Invalid language code: {lang_code}")

    def _toggle_theme(self) -> None:
        """Toggle between dark and light themes"""
        new_theme = self.theme_manager.toggle_theme()
        theme_display = new_theme.capitalize()
        self.window.statusBar.showMessage(tr("status_theme_switched", theme=theme_display), 2000)
        logger.info(f"User toggled theme to: {new_theme}")

    def _show_about(self) -> None:
        """Show about dialog"""
        about_text = f"""
<h2>NEXUS Music Manager</h2>
<p><b>Version:</b> {APP_VERSION}</p>
<p><b>Phases:</b> 1-7 Complete</p>
<br>
<p>Modern music player with library management, search & download,
audio playback, playlists, and visualizer.</p>
<br>
<p><b>Features:</b></p>
<ul>
<li>Library Management (10,000+ songs)</li>
<li>Search & Download (YouTube + Spotify)</li>
<li>Duplicate Detection</li>
<li>Auto-Organize Folders</li>
<li>Batch Rename</li>
<li>Music Player with Visualizer</li>
<li>Playlist Management</li>
<li>Album Grid View</li>
<li>Song Recommendations</li>
</ul>
<br>
<p><small>Built with: Python, PySide6, yt-dlp, python-mpv</small></p>
        """
        QMessageBox.about(self.window, "About - NEXUS Music Manager", about_text)

    def _show_api_guide(self) -> None:
        """Show API setup guide"""
        from PySide6.QtWidgets import QTextBrowser

        dialog = QDialog(self.window)
        dialog.setWindowTitle("API Setup Guide")
        dialog.setMinimumSize(750, 650)

        layout = QVBoxLayout(dialog)

        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(API_GUIDE_HTML)
        layout.addWidget(text_browser)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _show_shortcuts_dialog(self) -> None:
        """Show keyboard shortcuts help dialog"""
        from gui.dialogs.shortcuts_dialog import ShortcutsDialog

        shortcuts = self.shortcuts_manager.get_shortcuts()
        dialog = ShortcutsDialog(shortcuts, self.window)
        dialog.exec()

    # ==========================================
    # Visualizer Signal Handlers
    # ==========================================

    def _on_song_loaded(self, file_path: str) -> None:
        """Handle song loaded — extract spectrum/waveform asynchronously"""
        try:
            logger.info(f"Starting audio analysis for: {Path(file_path).name}")

            duration = self.audio_player.get_duration() if self.audio_player else 0.0
            self.window.statusBar.showMessage("Analyzing audio for visualizer...", 0)

            # Stop any existing worker gracefully (terminate() causes segfaults in C extensions)
            if self._spectrum_worker is not None and self._spectrum_worker.isRunning():  # type: ignore[union-attr]
                self._spectrum_worker.cancel()  # type: ignore[union-attr]
                self._spectrum_worker.requestInterruption()  # type: ignore[union-attr]
                self._spectrum_worker.wait(3000)  # type: ignore[union-attr] — wait up to 3s
                if self._spectrum_worker.isRunning():  # type: ignore[union-attr]
                    logger.warning("Spectrum worker still running after 3s, detaching")
                    self._spectrum_worker.finished.disconnect()  # type: ignore[union-attr]
                    self._spectrum_worker.raw_audio_ready.disconnect()  # type: ignore[union-attr]

            from core.spectrum_worker import SpectrumWorker

            self._spectrum_worker = SpectrumWorker(self.waveform_extractor, file_path, num_bars=60)

            self._spectrum_worker.finished.connect(
                lambda data, dur: self._on_spectrum_extracted(data, dur, duration, file_path)
            )
            self._spectrum_worker.error.connect(lambda err: self._on_spectrum_error(err, file_path, duration))
            self._spectrum_worker.progress.connect(
                lambda pct: self.window.statusBar.showMessage(f"Analyzing audio... {pct}%", 0)
            )
            self._spectrum_worker.raw_audio_ready.connect(
                lambda samples, sr: self.window.visualizer.set_raw_audio(samples, sr)
            )

            self._spectrum_worker.start()

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error starting audio analysis: {e}")
            self.window.statusBar.showMessage(f"Error: {str(e)}", 5000)
            self.window.visualizer.clear()

    def _on_spectrum_extracted(
        self, spectrum_data: list[list[float]], spectrum_duration: float, audio_duration: float, file_path: str
    ) -> None:
        """Handle spectrum extraction completion"""
        try:
            self.window.visualizer.set_spectrum(spectrum_data, spectrum_duration)
            self.window.visualizer.set_duration(audio_duration)
            logger.info(f"Dynamic spectrum loaded: {len(spectrum_data)} windows")
            self.window.statusBar.showMessage("Visualizer ready", 2000)
        except (ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Error applying spectrum data: {e}")
            self.window.statusBar.showMessage(f"Visualizer error: {str(e)}", 5000)

    def _on_spectrum_error(self, error_msg: str, file_path: str, duration: float) -> None:
        """Handle spectrum extraction error — fallback to waveform"""
        logger.warning(f"Spectrum extraction failed: {error_msg}")
        self.window.statusBar.showMessage("Using simplified visualizer...", 2000)

        try:
            waveform = self.waveform_extractor.extract(file_path, num_points=1000)

            if waveform:
                self.window.visualizer.set_waveform(waveform)
                self.window.visualizer.set_duration(duration)
                logger.info(f"Waveform fallback loaded: {len(waveform)} points")
            else:
                logger.warning("Failed to extract any visualization data")
                self.window.visualizer.clear()

        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"Fallback extraction error: {e}")
            self.window.visualizer.clear()


# ==========================================
# API Guide HTML (extracted to reduce method length)
# ==========================================

API_GUIDE_HTML = """
<h2>API Setup Guide</h2>

<h3>YouTube Data API v3</h3>
<p><b>Step 1:</b> Go to <a href="https://console.cloud.google.com/">Google Cloud Console</a></p>
<p><b>Step 2:</b> Create a new project</p>
<p><b>Step 3:</b> Enable "YouTube Data API v3"</p>
<p><b>Step 4:</b> Create credentials: Credentials tab → Create Credentials → API Key</p>
<p><b>Quota:</b> 10,000 units/day free (~100 searches)</p>

<hr>

<h3>Spotify Web API</h3>
<p><b>Step 1:</b> Go to <a href="https://developer.spotify.com/dashboard">Spotify Developer Dashboard</a></p>
<p><b>Step 2:</b> Log in (free account works)</p>
<p><b>Step 3:</b> Create App → Name: "NEXUS Music Manager", Redirect URI: "http://localhost:8888/callback"</p>
<p><b>Step 4:</b> Settings → Copy Client ID and Client Secret</p>
<p><b>Quota:</b> Unlimited searches (rate limited)</p>

<hr>

<h3>Saving Your Keys</h3>
<p>Go to <b>Settings → API Settings</b> (or press <b>Ctrl+K</b>), paste your keys, click Test, then Save.</p>

<hr>

<h3>Testing</h3>
<ol>
<li>Restart the application</li>
<li>Go to Search tab</li>
<li>Search for an artist or song</li>
<li>Both YouTube and Spotify results should appear</li>
</ol>

<hr>

<h3>Troubleshooting</h3>
<p><b>"Missing API credentials"</b> — Check keys are saved, restart app, go to Settings → API and click Test</p>
<p><b>"API quota exceeded"</b> — YouTube: wait 24h. Spotify: wait a few minutes</p>

<hr>

<p style="color: #666;"><small>
<b>Security:</b> Your API keys are stored securely in your OS credential manager.
</small></p>
"""
