#!/usr/bin/env python3
"""
NEXUS Music Manager - Complete Application (Phases 1-7)

Music player with library management, search/download, audio playback,
playlists, visualizer, and management tools.

Project: AGENTE_MUSICA_MP3_001
Version: 2.0 (Production)
Phases: 1-7 Complete
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout,
        QWidget, QSplitter, QStatusBar, QMessageBox
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
except ImportError as e:
    print("❌ PyQt6 not installed")
    print("   Install with: pip install PyQt6")
    sys.exit(1)

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import database
from database.manager import DatabaseManager

# Import core engines
from core.audio_player import AudioPlayer
from core.playlist_manager import PlaylistManager
from core.waveform_extractor import WaveformExtractor
from core.download_queue import DownloadQueue
from core.theme_manager import ThemeManager
from core.keyboard_shortcuts import KeyboardShortcutManager

# Import API clients
from api.genius_client import GeniusClient

# Import utilities
import keyring

# Import GUI tabs
from gui.tabs.library_tab import LibraryTab
from gui.tabs.search_tab import SearchTab
from gui.tabs.lyrics_tab import LyricsTab
from gui.tabs.import_tab import ImportTab
from gui.tabs.duplicates_tab import DuplicatesTab
from gui.tabs.organize_tab import OrganizeTab
from gui.tabs.rename_tab import RenameTab

# Import GUI widgets
from gui.widgets.now_playing_widget import NowPlayingWidget
from gui.widgets.playlist_widget import PlaylistWidget
from gui.widgets.queue_widget import QueueWidget
from gui.widgets.visualizer_widget import VisualizerWidget


class MusicPlayerApp(QMainWindow):
    """Main application window integrating all features (Phases 1-7)"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEXUS Music Manager - Complete Edition")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize database
        try:
            self.db_manager = DatabaseManager()
            logger.info("Database initialized successfully")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to initialize database:\n{str(e)}\n\n"
                f"Please check database connection and migrations."
            )
            logger.error(f"Database initialization failed: {e}")
            sys.exit(1)

        # Initialize audio engine
        self.audio_player = AudioPlayer()
        logger.info("Audio player initialized")

        # Initialize playlist manager
        self.playlist_manager = PlaylistManager(self.db_manager)
        logger.info("Playlist manager initialized")

        # Initialize waveform extractor
        self.waveform_extractor = WaveformExtractor()
        logger.info("Waveform extractor initialized")

        # Initialize download queue (with database integration)
        self.download_queue = DownloadQueue(
            max_concurrent=50,
            max_retries=3,
            db_manager=self.db_manager  # Pass database for auto-import
        )
        self.download_queue.start()  # Start processing downloads
        logger.info("Download queue initialized")

        # Initialize theme manager
        self.theme_manager = ThemeManager()
        logger.info("Theme manager initialized")

        # Initialize keyboard shortcuts manager
        self.shortcuts_manager = KeyboardShortcutManager()
        QApplication.instance().installEventFilter(self.shortcuts_manager)
        logger.info("Keyboard shortcuts manager initialized")

        # Initialize Genius API client (optional - for lyrics)
        try:
            genius_token = keyring.get_password("nexus_music", "genius_token")
            if genius_token:
                self.genius_client = GeniusClient(genius_token)
                logger.info("Genius client initialized")
            else:
                self.genius_client = None
                logger.info("Genius API token not found (lyrics disabled)")
        except Exception as e:
            logger.error(f"Failed to initialize Genius client: {e}")
            self.genius_client = None

        # Setup UI
        self._init_ui()

        # Apply theme (after UI is created)
        self.theme_manager.apply_theme(self.theme_manager.current_theme)

        # Connect shortcut signals (after UI is created)
        self._connect_keyboard_shortcuts()

        # Setup QShortcut-based shortcuts (high priority, cannot be blocked)
        self.shortcuts_manager.setup_shortcuts(self)

        # Connect lyrics signal (after lyrics_tab is created)
        if hasattr(self, 'lyrics_tab') and self.lyrics_tab:
            self.now_playing.song_metadata_changed.connect(self.lyrics_tab.on_song_changed)
            logger.info("Lyrics signal connected")

        logger.info("Application started successfully")

        # Check if library is empty and suggest import
        self._check_empty_library()

    def _init_ui(self):
        """Initialize user interface"""
        # Create menu bar
        self._create_menu_bar()

        # Central widget with main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top section: Now Playing + Visualizer
        top_section = self._create_top_section()
        main_layout.addWidget(top_section, stretch=0)

        # Middle section: Main content (tabs + playlist panel)
        middle_section = self._create_middle_section()
        main_layout.addWidget(middle_section, stretch=1)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def _create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Exit action
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        # API Settings action
        api_settings_action = settings_menu.addAction("&API Configuration...")
        api_settings_action.setShortcut("Ctrl+K")
        api_settings_action.triggered.connect(self._show_api_settings)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Toggle Dark/Light Theme action
        theme_action = view_menu.addAction("Toggle &Dark/Light Theme")
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self._toggle_theme)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # Keyboard Shortcuts action (F1)
        shortcuts_action = help_menu.addAction("&Keyboard Shortcuts")
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)

        # API Setup Guide action (F2)
        api_guide_action = help_menu.addAction("&API Setup Guide")
        api_guide_action.setShortcut("F2")
        api_guide_action.triggered.connect(self._show_api_guide)

        # Separator
        help_menu.addSeparator()

        # About action
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self._show_about)

    def _show_api_settings(self):
        """Show API settings dialog"""
        from gui.dialogs.api_settings_dialog import APISettingsDialog

        dialog = APISettingsDialog(self)

        if dialog.exec():
            logger.info("API settings updated")
            self.statusBar.showMessage("API settings saved successfully", 3000)
        else:
            logger.info("API settings dialog cancelled")

    def _toggle_theme(self):
        """Toggle between dark and light themes"""
        new_theme = self.theme_manager.toggle_theme()

        # Capitalize first letter for display
        theme_display = new_theme.capitalize()

        # Show status message
        self.statusBar.showMessage(f"Switched to {theme_display} theme", 2000)

        logger.info(f"User toggled theme to: {new_theme}")

    def _show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox

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
</ul>
<br>
<p><small>Built with Python, PyQt6, yt-dlp, and pygame</small></p>
        """

        QMessageBox.about(self, "About NEXUS Music Manager", about_text)

    def _show_api_guide(self):
        """Show API setup guide"""
        from PyQt6.QtWidgets import QMessageBox, QTextBrowser, QDialog, QVBoxLayout, QPushButton

        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("API Setup Guide")
        dialog.setMinimumSize(700, 600)

        layout = QVBoxLayout(dialog)

        # Create text browser for rich text with links
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml("""
<h2>🔑 API Setup Guide</h2>

<p>NEXUS Music Manager uses API keys to search and download music from YouTube and Spotify.
Follow the steps below to obtain your free API keys.</p>

<hr>

<h3>📺 YouTube Data API v3</h3>

<p><b>Step 1:</b> Go to <a href="https://console.cloud.google.com/">Google Cloud Console</a></p>
<p><b>Step 2:</b> Create a new project (or select existing)</p>
<p><b>Step 3:</b> Enable "YouTube Data API v3":</p>
<ul>
<li>Click "Enable APIs and Services"</li>
<li>Search for "YouTube Data API v3"</li>
<li>Click "Enable"</li>
</ul>
<p><b>Step 4:</b> Create credentials:</p>
<ul>
<li>Go to "Credentials" tab</li>
<li>Click "Create Credentials" → "API Key"</li>
<li>Copy your API key</li>
<li>(Optional) Restrict key to "YouTube Data API v3" only</li>
</ul>

<p><b>💡 Quota:</b> Free tier provides 10,000 units/day (≈ 100 searches)</p>

<hr>

<h3>🎵 Spotify Web API</h3>

<p><b>Step 1:</b> Go to <a href="https://developer.spotify.com/dashboard">Spotify Developer Dashboard</a></p>
<p><b>Step 2:</b> Log in with your Spotify account (free account works)</p>
<p><b>Step 3:</b> Create an app:</p>
<ul>
<li>Click "Create App"</li>
<li>App Name: "NEXUS Music Manager" (or any name)</li>
<li>App Description: "Personal music library manager"</li>
<li>Redirect URI: Leave default or use "http://localhost:8888/callback"</li>
<li>Check "Web API" checkbox</li>
<li>Accept terms and click "Create"</li>
</ul>
<p><b>Step 4:</b> Get credentials:</p>
<ul>
<li>Click "Settings" on your app</li>
<li>Copy "Client ID"</li>
<li>Click "View client secret" and copy "Client Secret"</li>
</ul>

<p><b>💡 Quota:</b> Free tier provides unlimited searches (rate limited)</p>

<hr>

<h3>💾 Saving Your Keys</h3>

<p><b>Method 1: API Settings Dialog (Recommended)</b></p>
<ul>
<li>Go to <b>Settings → API Configuration</b> (or press <b>Ctrl+K</b>)</li>
<li>Paste your keys in the respective tabs</li>
<li>Click "Test" to verify each API</li>
<li>Click "Save" to store securely in your OS keyring</li>
</ul>

<p><b>Method 2: Environment Variables</b></p>
<pre style="background-color: #f0f0f0; padding: 10px;">
export YOUTUBE_API_KEY="your_youtube_key_here"
export SPOTIFY_CLIENT_ID="your_spotify_id_here"
export SPOTIFY_CLIENT_SECRET="your_spotify_secret_here"
</pre>

<p><b>Method 3: .env File</b></p>
<ul>
<li>Create a file named <code>.env</code> in the project root</li>
<li>Copy from <code>.env.example</code> and fill in your keys</li>
</ul>

<hr>

<h3>✅ Testing Your Setup</h3>

<p>After saving your keys:</p>
<ol>
<li>Restart the application</li>
<li>Go to <b>Search & Download</b> tab</li>
<li>Try searching for an artist or song</li>
<li>Both YouTube and Spotify results should appear</li>
</ol>

<hr>

<h3>❓ Troubleshooting</h3>

<p><b>Error: "Missing API credentials"</b></p>
<ul>
<li>Check that all three keys are saved correctly</li>
<li>Restart the application</li>
<li>Try opening Settings → API Configuration and click "Test"</li>
</ul>

<p><b>Error: "API quota exceeded"</b></p>
<ul>
<li>YouTube: Wait 24 hours for quota reset</li>
<li>Spotify: Wait a few minutes and try again</li>
</ul>

<p><b>Need Help?</b></p>
<ul>
<li>Check logs in console for detailed error messages</li>
<li>Verify your keys are correct (no extra spaces)</li>
<li>Ensure APIs are enabled in respective dashboards</li>
</ul>

<hr>

<p style="color: #666;"><small>
<b>Note:</b> Your API keys are stored securely in your operating system's credential manager
and are never shared or transmitted outside of official API requests to YouTube and Spotify.
</small></p>
        """)

        layout.addWidget(text_browser)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _create_top_section(self):
        """Create top section with Now Playing + Visualizer"""
        # Horizontal layout
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Now Playing Widget (left)
        self.now_playing = NowPlayingWidget(self.audio_player)
        top_layout.addWidget(self.now_playing, stretch=1)

        # Visualizer Widget (right)
        self.visualizer = VisualizerWidget()
        top_layout.addWidget(self.visualizer, stretch=2)

        # Connect signals
        self.now_playing.position_changed.connect(
            lambda pos: self.visualizer.set_position(pos)
        )
        self.now_playing.song_loaded.connect(self._on_song_loaded)

        return top_widget

    def _create_middle_section(self):
        """Create middle section with tabs and playlist panel"""
        # Horizontal splitter (main content | playlist panel)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Tab widget with all features
        tab_widget = self._create_tab_widget()
        splitter.addWidget(tab_widget)

        # Right: Playlist panel (Phase 7)
        self.playlist_widget = PlaylistWidget(self.playlist_manager, self.db_manager)
        splitter.addWidget(self.playlist_widget)

        # Set initial sizes (70% tabs, 30% playlist)
        splitter.setSizes([1000, 400])

        return splitter

    def _create_tab_widget(self):
        """Create tab widget with all features"""
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Disable keyboard focus on tab widget to allow global shortcuts (Left/Right)
        # This prevents QTabWidget from consuming arrow keys for tab navigation
        self.tabs.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Tab 1: Library (Phase 3 + Phase 6 playback integration)
        try:
            self.library_tab = LibraryTab(
                self.db_manager,
                self.audio_player,
                self.now_playing
            )
            self.tabs.addTab(self.library_tab, "🎵 Library")
            logger.info("Library tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Library tab: {e}")
            self.tabs.addTab(QWidget(), "🎵 Library (Error)")

        # Tab 2: Search & Download (Phase 4)
        try:
            self.search_tab = SearchTab(self.download_queue)
            self.tabs.addTab(self.search_tab, "🔍 Search & Download")
            logger.info("Search tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Search tab: {e}")
            self.tabs.addTab(QWidget(), "🔍 Search (Error)")

        # Tab 3: Lyrics (Feature #2)
        try:
            self.lyrics_tab = LyricsTab(self.genius_client)
            self.tabs.addTab(self.lyrics_tab, "📝 Lyrics")
            logger.info("Lyrics tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Lyrics tab: {e}")
            self.tabs.addTab(QWidget(), "📝 Lyrics (Error)")

        # Tab 4: Import Library (NEW - Library Import Feature)
        try:
            self.import_tab = ImportTab(self.db_manager)
            self.tabs.addTab(self.import_tab, "📥 Import Library")
            logger.info("Import tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Import tab: {e}")
            self.tabs.addTab(QWidget(), "📥 Import (Error)")

        # Tab 4: Download Queue (Phase 4)
        try:
            self.queue_widget = QueueWidget(self.download_queue)
            self.tabs.addTab(self.queue_widget, "📥 Queue")
            logger.info("Queue tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Queue tab: {e}")

        # Tab 4: Duplicates (Phase 5)
        try:
            self.duplicates_tab = DuplicatesTab(self.db_manager)
            self.tabs.addTab(self.duplicates_tab, "🔍 Duplicates")
            logger.info("Duplicates tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Duplicates tab: {e}")
            self.tabs.addTab(QWidget(), "🔍 Duplicates (Error)")

        # Tab 5: Organize (Phase 5)
        try:
            self.organize_tab = OrganizeTab(self.db_manager)
            self.tabs.addTab(self.organize_tab, "📁 Organize")
            logger.info("Organize tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Organize tab: {e}")
            self.tabs.addTab(QWidget(), "📁 Organize (Error)")

        # Tab 6: Rename (Phase 5)
        try:
            self.rename_tab = RenameTab(self.db_manager)
            self.tabs.addTab(self.rename_tab, "✏️ Rename")
            logger.info("Rename tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Rename tab: {e}")
            self.tabs.addTab(QWidget(), "✏️ Rename (Error)")

        return self.tabs

    def _on_song_loaded(self, file_path: str):
        """
        Handle song loaded event - extract waveform and update visualizer

        Args:
            file_path: Path to audio file
        """
        try:
            logger.info(f"Extracting waveform for: {Path(file_path).name}")

            # Get duration from audio player (already loaded)
            duration = self.audio_player.get_duration() if self.audio_player else 0.0

            # Extract waveform (1000 points is good for visualization)
            waveform = self.waveform_extractor.extract(file_path, num_points=1000)

            if waveform:
                # Update visualizer with waveform and duration
                self.visualizer.set_waveform(waveform)
                self.visualizer.set_duration(duration)
                logger.info(f"Waveform loaded: {len(waveform)} points, duration: {duration:.2f}s")
            else:
                logger.warning(f"Failed to extract waveform from: {file_path}")
                # Clear visualizer on failure
                self.visualizer.clear()

        except Exception as e:
            logger.error(f"Error extracting waveform: {e}")
            self.visualizer.clear()

    def _check_empty_library(self):
        """Check if library is empty and suggest importing music"""
        try:
            song_count = self.db_manager.get_song_count()

            if song_count == 0:
                logger.info("Library is empty, showing import suggestion")

                reply = QMessageBox.information(
                    self,
                    "Welcome to NEXUS Music Manager",
                    "Your music library is empty.\n\n"
                    "Would you like to import your MP3 collection now?\n\n"
                    "Go to the '📥 Import Library' tab to get started.",
                    QMessageBox.StandardButton.Ok
                )

                # Switch to Import tab automatically
                # Find Import tab index (should be tab 2)
                for i in range(self.findChild(QTabWidget).count()):
                    if "Import" in self.findChild(QTabWidget).tabText(i):
                        self.findChild(QTabWidget).setCurrentIndex(i)
                        logger.info("Switched to Import tab automatically")
                        break

        except Exception as e:
            logger.error(f"Error checking library status: {e}")

    def _connect_keyboard_shortcuts(self):
        """Connect keyboard shortcut signals to handlers"""
        sm = self.shortcuts_manager

        # Playback controls
        sm.play_pause_requested.connect(self._handle_play_pause_shortcut)
        sm.seek_backward_requested.connect(self._handle_seek_backward)
        sm.seek_forward_requested.connect(self._handle_seek_forward)
        sm.volume_change_requested.connect(self._handle_volume_change)
        sm.mute_toggled.connect(self._handle_mute_toggle)

        # Navigation
        sm.focus_search_requested.connect(self._handle_focus_search)
        sm.switch_to_tab_requested.connect(self._handle_switch_tab)

        logger.info("Keyboard shortcuts connected")

    def _handle_play_pause_shortcut(self):
        """Handle Space key - Play/Pause"""
        # Use the widget's play/pause method directly
        self.now_playing._on_play_clicked()
        logger.debug("Shortcut: Play/Pause toggled")

    def _handle_seek_backward(self, seconds):
        """Handle Left arrow - Seek backward"""
        current = self.audio_player.get_position()
        new_pos = max(0, current - seconds)
        self.audio_player.seek(new_pos)
        logger.debug(f"Shortcut: Seek to {new_pos}s")

    def _handle_seek_forward(self, seconds):
        """Handle Right arrow - Seek forward"""
        current = self.audio_player.get_position()
        duration = self.audio_player.get_duration()
        new_pos = min(duration, current + seconds)
        self.audio_player.seek(new_pos)
        logger.debug(f"Shortcut: Seek to {new_pos}s")

    def _handle_volume_change(self, delta):
        """Handle Up/Down arrows - Volume change"""
        try:
            import pygame
            # Get current volume (0.0-1.0 range)
            current = pygame.mixer.music.get_volume()
            # Calculate new volume
            new_volume = max(0.0, min(1.0, current + (delta / 100.0)))
            self.audio_player.set_volume(new_volume)

            # Update UI slider (prevent signal loop)
            percentage = int(new_volume * 100)
            if hasattr(self, 'now_playing') and hasattr(self.now_playing, 'volume_slider'):
                self.now_playing.volume_slider.blockSignals(True)
                self.now_playing.volume_slider.setValue(percentage)
                self.now_playing.volume_slider.blockSignals(False)
                # Also update the percentage label
                if hasattr(self.now_playing, 'volume_label_value'):
                    self.now_playing.volume_label_value.setText(f"{percentage}%")

            # Update status bar (show as percentage)
            self.statusBar.showMessage(f"Volume: {percentage}%", 1000)
            logger.debug(f"Shortcut: Volume {percentage}%")
        except Exception as e:
            logger.error(f"Volume change failed: {e}")

    def _handle_mute_toggle(self):
        """Handle M key - Mute/Unmute"""
        try:
            import pygame
            current = pygame.mixer.music.get_volume()

            if current > 0:
                # Mute: save current volume
                self._previous_volume = current
                self.audio_player.set_volume(0.0)

                # Update UI slider to 0%
                if hasattr(self, 'now_playing') and hasattr(self.now_playing, 'volume_slider'):
                    self.now_playing.volume_slider.blockSignals(True)
                    self.now_playing.volume_slider.setValue(0)
                    self.now_playing.volume_slider.blockSignals(False)
                    if hasattr(self.now_playing, 'volume_label_value'):
                        self.now_playing.volume_label_value.setText("0%")

                self.statusBar.showMessage("Muted", 1000)
                logger.debug("Shortcut: Muted")
            else:
                # Unmute: restore previous volume
                volume = getattr(self, '_previous_volume', 0.7)
                self.audio_player.set_volume(volume)

                # Update UI slider to restored volume
                percentage = int(volume * 100)
                if hasattr(self, 'now_playing') and hasattr(self.now_playing, 'volume_slider'):
                    self.now_playing.volume_slider.blockSignals(True)
                    self.now_playing.volume_slider.setValue(percentage)
                    self.now_playing.volume_slider.blockSignals(False)
                    if hasattr(self.now_playing, 'volume_label_value'):
                        self.now_playing.volume_label_value.setText(f"{percentage}%")

                self.statusBar.showMessage(f"Volume: {percentage}%", 1000)
                logger.debug(f"Shortcut: Unmuted to {percentage}%")
        except Exception as e:
            logger.error(f"Mute toggle failed: {e}")

    def _handle_focus_search(self):
        """Handle Ctrl+F - Focus search"""
        if hasattr(self, 'search_tab') and hasattr(self, 'tabs'):
            # Switch to search tab
            self.tabs.setCurrentWidget(self.search_tab)

            # Focus search input field
            if hasattr(self.search_tab, 'search_input'):
                self.search_tab.search_input.setFocus()
                logger.debug("Shortcut: Focused search")

    def _handle_switch_tab(self, tab_name):
        """Handle Ctrl+L/D - Switch tabs"""
        if not hasattr(self, 'tabs'):
            return

        if tab_name == 'library' and hasattr(self, 'library_tab'):
            self.tabs.setCurrentWidget(self.library_tab)
            logger.debug("Shortcut: Switched to Library tab")
        elif tab_name == 'queue' and hasattr(self, 'queue_widget'):
            self.tabs.setCurrentWidget(self.queue_widget)
            logger.debug("Shortcut: Switched to Queue tab")

    def _show_shortcuts_dialog(self):
        """Show keyboard shortcuts help dialog"""
        from gui.dialogs.shortcuts_dialog import ShortcutsDialog

        shortcuts = self.shortcuts_manager.get_shortcuts()
        dialog = ShortcutsDialog(shortcuts, self)
        dialog.exec()

    def closeEvent(self, event):
        """Handle application close event"""
        # Cleanup audio player
        try:
            self.audio_player.cleanup()
            logger.info("Audio player cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up audio player: {e}")

        # Stop download queue
        try:
            self.download_queue.stop()
            logger.info("Download queue stopped")
        except Exception as e:
            logger.error(f"Error stopping download queue: {e}")

        # Close database
        try:
            self.db_manager.close()
            logger.info("Database closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")

        event.accept()
        logger.info("Application closed")


def main():
    """Main entry point"""
    # Configure exception hook for better error reporting
    def exception_hook(exc_type, exc_value, exc_traceback):
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_hook

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("NEXUS Music Manager")
    app.setOrganizationName("NEXUS")

    # Set dark theme (optional)
    app.setStyle("Fusion")

    # Create and show main window
    window = MusicPlayerApp()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
