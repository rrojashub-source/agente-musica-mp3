"""
UI Composer — Phase 2.1

Builds the complete UI: menu bar, top section (now playing + visualizer),
tab widget with 15 tabs, status bar. Also handles dialog methods and
visualizer signal callbacks.
"""
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QTabWidget, QVBoxLayout, QHBoxLayout, QWidget, QStatusBar,
    QMessageBox, QDialog, QPushButton
)
from PyQt6.QtCore import Qt

from translations import tr, get_language, set_language, LANGUAGES

logger = logging.getLogger(__name__)


class UIComposer:
    """Creates and manages all UI components for the main window"""

    def __init__(self, window, db_manager, audio_player, playlist_manager,
                 waveform_extractor, config_manager, download_queue,
                 theme_manager, shortcuts_manager, genius_client):
        self.window = window
        self.db_manager = db_manager
        self.audio_player = audio_player
        self.playlist_manager = playlist_manager
        self.waveform_extractor = waveform_extractor
        self.config_manager = config_manager
        self.download_queue = download_queue
        self.theme_manager = theme_manager
        self.shortcuts_manager = shortcuts_manager
        self.genius_client = genius_client

    def compose(self):
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

    def _create_menu_bar(self):
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
            lang_action.triggered.connect(
                lambda checked, lc=lang_code: self._change_language(lc)
            )

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

    def _create_top_section(self):
        """Create top section with Now Playing + Visualizer + Recommendations"""
        from gui.widgets.now_playing_widget import NowPlayingWidget
        from gui.widgets.visualizer_widget import VisualizerWidget
        from gui.widgets.recommendations_widget import RecommendationsWidget

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
        self.window.now_playing.position_changed.connect(
            lambda pos: self.window.visualizer.set_position(pos)
        )

        # Connect song loaded → visualizer analysis
        self.window.now_playing.song_loaded.connect(self._on_song_loaded)

        return top_widget

    # ==========================================
    # Tab Widget (15 tabs)
    # ==========================================

    def _create_tab_widget(self):
        """Create tab widget with all features"""
        from gui.tabs.library_tab import LibraryTab
        from gui.tabs.search_tab import SearchTab
        from gui.tabs.lyrics_tab import LyricsTab
        from gui.tabs.import_tab import ImportTab
        from gui.tabs.duplicates_tab import DuplicatesTab
        from gui.tabs.organize_tab import OrganizeTab
        from gui.tabs.rename_tab import RenameTab
        from gui.tabs.cleanup_tab import CleanupTab
        from gui.tabs.cloud_sync_tab import CloudSyncTab
        from gui.tabs.plugins_tab import PluginsTab
        from gui.tabs.remote_tab import RemoteTab
        from gui.tabs.content_filter_tab import ContentFilterTab
        from gui.tabs.statistics_tab import StatisticsTab
        from gui.widgets.playlist_widget import PlaylistWidget
        from gui.widgets.queue_widget import QueueWidget
        from gui.widgets.album_grid_widget import AlbumGridWidget

        self.window.tabs = QTabWidget()
        self.window.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.window.tabs.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        tabs = self.window.tabs
        w = self.window

        # Tab 1: Import Library
        try:
            w.import_tab = ImportTab(self.db_manager)
            tabs.addTab(w.import_tab, tr("tab_import"))
            logger.info("Import tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Import tab: {e}")
            tabs.addTab(QWidget(), tr("tab_import") + " (Error)")

        # Tab 2: Library
        try:
            w.library_tab = LibraryTab(self.db_manager, self.audio_player, w.now_playing)
            tabs.addTab(w.library_tab, tr("tab_library"))
            logger.info("Library tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Library tab: {e}")
            tabs.addTab(QWidget(), tr("tab_library") + " (Error)")

        # Tab 3: Albums
        try:
            w.albums_widget = AlbumGridWidget(self.db_manager)
            tabs.addTab(w.albums_widget, tr("tab_albums"))
            logger.info("Albums tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Albums tab: {e}")
            tabs.addTab(QWidget(), tr("tab_albums") + " (Error)")

        # Tab 4: Lyrics
        try:
            w.lyrics_tab = LyricsTab(self.genius_client)
            tabs.addTab(w.lyrics_tab, tr("tab_lyrics"))
            logger.info("Lyrics tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Lyrics tab: {e}")
            tabs.addTab(QWidget(), tr("tab_lyrics") + " (Error)")

        # Tab 5: Search & Download
        try:
            w.search_tab = SearchTab(self.download_queue)
            tabs.addTab(w.search_tab, tr("tab_search"))
            logger.info("Search tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Search tab: {e}")
            tabs.addTab(QWidget(), tr("tab_search") + " (Error)")

        # Tab 6: Queue
        try:
            w.queue_widget = QueueWidget(self.download_queue)
            tabs.addTab(w.queue_widget, tr("tab_queue"))
            logger.info("Queue tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Queue tab: {e}")

        # Tab 7: Duplicates
        try:
            w.duplicates_tab = DuplicatesTab(self.db_manager)
            tabs.addTab(w.duplicates_tab, tr("tab_duplicates"))
            logger.info("Duplicates tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Duplicates tab: {e}")
            tabs.addTab(QWidget(), tr("tab_duplicates") + " (Error)")

        # Tab 8: Rename
        try:
            w.rename_tab = RenameTab(self.db_manager)
            tabs.addTab(w.rename_tab, tr("tab_rename"))
            logger.info("Rename tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Rename tab: {e}")
            tabs.addTab(QWidget(), tr("tab_rename") + " (Error)")

        # Tab 9: Organize
        try:
            w.organize_tab = OrganizeTab(self.db_manager)
            tabs.addTab(w.organize_tab, tr("tab_organize"))
            logger.info("Organize tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Organize tab: {e}")
            tabs.addTab(QWidget(), tr("tab_organize") + " (Error)")

        # Tab 10: Cleanup Wizard
        try:
            db_path = self.db_manager.db_path if hasattr(self.db_manager, 'db_path') else 'music_library.db'
            w.cleanup_tab = CleanupTab(db_path)
            tabs.addTab(w.cleanup_tab, tr("tab_cleanup"))
            logger.info("Cleanup Wizard tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Cleanup Wizard tab: {e}")
            tabs.addTab(QWidget(), tr("tab_cleanup") + " (Error)")

        # Tab 11: Playlist
        try:
            w.playlist_widget = PlaylistWidget(self.playlist_manager, self.db_manager)
            tabs.addTab(w.playlist_widget, tr("tab_playlist"))
            logger.info("Playlist tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Playlist tab: {e}")
            tabs.addTab(QWidget(), tr("tab_playlist") + " (Error)")

        # Tab 12: Cloud Sync
        try:
            w.cloud_sync_tab = CloudSyncTab(db_manager=self.db_manager)
            tabs.addTab(w.cloud_sync_tab, tr("tab_cloud_sync"))
            logger.info("Cloud Sync tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Cloud Sync tab: {e}")
            tabs.addTab(QWidget(), tr("tab_cloud_sync") + " (Error)")

        # Tab 13: Plugins
        try:
            w.plugins_tab = PluginsTab()
            tabs.addTab(w.plugins_tab, tr("tab_plugins"))
            logger.info("Plugins tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Plugins tab: {e}")
            tabs.addTab(QWidget(), tr("tab_plugins") + " (Error)")

        # Tab 14: Remote Control
        try:
            w.remote_tab = RemoteTab()
            tabs.addTab(w.remote_tab, tr("tab_remote"))
            logger.info("Remote Control tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Remote Control tab: {e}")
            tabs.addTab(QWidget(), tr("tab_remote") + " (Error)")

        # Tab 15: Content Filter
        try:
            w.content_filter_tab = ContentFilterTab(self.db_manager)
            tabs.addTab(w.content_filter_tab, tr("tab_content_filter"))
            logger.info("Content Filter tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Content Filter tab: {e}")
            tabs.addTab(QWidget(), tr("tab_content_filter") + " (Error)")

        # Tab 16: Statistics Dashboard
        try:
            w.statistics_tab = StatisticsTab(self.db_manager)
            tabs.addTab(w.statistics_tab, tr("tab_statistics"))
            logger.info("Statistics tab loaded")
        except Exception as e:  # Tab widgets can raise any Qt/import error during construction
            logger.error(f"Failed to load Statistics tab: {e}")
            tabs.addTab(QWidget(), tr("tab_statistics") + " (Error)")

        return self.window.tabs

    # ==========================================
    # Dialog Handlers
    # ==========================================

    def _show_api_settings(self):
        """Show API settings dialog"""
        from gui.dialogs.api_settings_dialog import APISettingsDialog

        dialog = APISettingsDialog(self.window)
        if dialog.exec():
            logger.info("API settings updated")
            self.window.statusBar.showMessage("API settings saved successfully", 3000)
        else:
            logger.info("API settings dialog cancelled")

    def _show_equalizer(self):
        """Show audio equalizer dialog"""
        from gui.widgets.equalizer_widget import EqualizerWidget

        dialog = QDialog(self.window)
        dialog.setWindowTitle(tr("equalizer_title"))
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)
        equalizer = EqualizerWidget()
        layout.addWidget(equalizer)

        if hasattr(self.audio_player, 'set_equalizer_gains'):
            equalizer.gains_changed.connect(self.audio_player.set_equalizer_gains)

        dialog.exec()
        logger.info("Equalizer dialog closed")

    def _change_language(self, lang_code: str):
        """Change application language"""
        from PyQt6.QtCore import QSettings

        if set_language(lang_code):
            settings = QSettings("NEXUS", "MusicManager")
            settings.setValue("language", lang_code)

            QMessageBox.information(
                self.window,
                tr("language_changed_title"),
                tr("language_changed_message")
            )
            logger.info(f"Language changed to: {lang_code}")
        else:
            logger.error(f"Invalid language code: {lang_code}")

    def _toggle_theme(self):
        """Toggle between dark and light themes"""
        new_theme = self.theme_manager.toggle_theme()
        theme_display = new_theme.capitalize()
        self.window.statusBar.showMessage(tr("status_theme_switched", theme=theme_display), 2000)
        logger.info(f"User toggled theme to: {new_theme}")

    def _show_about(self):
        """Show about dialog"""
        about_text = """
<h2>NEXUS Music Manager</h2>
<p><b>Version:</b> 2.0 (Production)</p>
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
<p><small>Built with: Python, PyQt6, yt-dlp, pygame</small></p>
        """
        QMessageBox.about(self.window, "About - NEXUS Music Manager", about_text)

    def _show_api_guide(self):
        """Show API setup guide"""
        from PyQt6.QtWidgets import QTextBrowser

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

    def _show_shortcuts_dialog(self):
        """Show keyboard shortcuts help dialog"""
        from gui.dialogs.shortcuts_dialog import ShortcutsDialog

        shortcuts = self.shortcuts_manager.get_shortcuts()
        dialog = ShortcutsDialog(shortcuts, self.window)
        dialog.exec()

    # ==========================================
    # Visualizer Signal Handlers
    # ==========================================

    def _on_song_loaded(self, file_path: str):
        """Handle song loaded — extract spectrum/waveform asynchronously"""
        try:
            logger.info(f"Starting audio analysis for: {Path(file_path).name}")

            duration = self.audio_player.get_duration() if self.audio_player else 0.0
            self.window.statusBar.showMessage("Analyzing audio for visualizer...", 0)

            # Stop any existing worker
            if hasattr(self, '_spectrum_worker') and self._spectrum_worker.isRunning():
                self._spectrum_worker.terminate()
                self._spectrum_worker.wait()

            from core.spectrum_worker import SpectrumWorker
            self._spectrum_worker = SpectrumWorker(
                self.waveform_extractor, file_path, num_bars=60
            )

            self._spectrum_worker.finished.connect(
                lambda data, dur: self._on_spectrum_extracted(data, dur, duration, file_path)
            )
            self._spectrum_worker.error.connect(
                lambda err: self._on_spectrum_error(err, file_path, duration)
            )
            self._spectrum_worker.progress.connect(
                lambda pct: self.window.statusBar.showMessage(f"Analyzing audio... {pct}%", 0)
            )

            self._spectrum_worker.start()

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error starting audio analysis: {e}")
            self.window.statusBar.showMessage(f"Error: {str(e)}", 5000)
            self.window.visualizer.clear()

    def _on_spectrum_extracted(self, spectrum_data, spectrum_duration, audio_duration, file_path):
        """Handle spectrum extraction completion"""
        try:
            self.window.visualizer.set_spectrum(spectrum_data, spectrum_duration)
            self.window.visualizer.set_duration(audio_duration)
            logger.info(f"Dynamic spectrum loaded: {len(spectrum_data)} windows")
            self.window.statusBar.showMessage("Visualizer ready", 2000)
        except (ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Error applying spectrum data: {e}")
            self.window.statusBar.showMessage(f"Visualizer error: {str(e)}", 5000)

    def _on_spectrum_error(self, error_msg, file_path, duration):
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
