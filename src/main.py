#!/usr/bin/env python3
"""
NEXUS Music Manager - Complete Application (Phases 1-7)

Music player with library management, search/download, audio playback,
playlists, visualizer, and management tools.

Project: AGENTE_MUSICA_MP3_001
Version: 2.0 (Production)
Phases: 1-7 Complete
Multi-language: Español (es), English (en)
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

# Multi-language translation system
from translations import tr, set_language, get_language, LANGUAGES

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
from config_manager import ConfigManager

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
from gui.tabs.cleanup_tab import CleanupTab
from gui.tabs.cloud_sync_tab import CloudSyncTab
from gui.tabs.plugins_tab import PluginsTab
from gui.tabs.remote_tab import RemoteTab
from gui.tabs.content_filter_tab import ContentFilterTab

# Import GUI widgets
from gui.widgets.now_playing_widget import NowPlayingWidget
from gui.widgets.playlist_widget import PlaylistWidget
from gui.widgets.queue_widget import QueueWidget
from gui.widgets.visualizer_widget import VisualizerWidget
from gui.widgets.album_grid_widget import AlbumGridWidget
from gui.widgets.recommendations_widget import RecommendationsWidget


class MusicPlayerApp(QMainWindow):
    """Main application window integrating all features (Phases 1-7)"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
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

        # Playback source tracking
        # 'library' = playing from Library tab
        # 'playlist' = playing from Playlist widget
        self._playback_source = None
        self._current_playlist_id = None
        self._current_playlist_songs = []
        self._current_playlist_index = -1

        # Initialize waveform extractor
        self.waveform_extractor = WaveformExtractor()
        logger.info("Waveform extractor initialized")

        # Initialize configuration manager
        self.config_manager = ConfigManager()
        logger.info("Configuration manager initialized")

        # Initialize download queue (with database and config integration)
        self.download_queue = DownloadQueue(
            max_concurrent=50,
            max_retries=3,
            db_manager=self.db_manager,  # Pass database for auto-import
            config_manager=self.config_manager  # Pass config for download directory
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
        file_menu = menubar.addMenu(tr("menu_file"))

        # Exit action
        exit_action = file_menu.addAction(tr("menu_exit"))
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Settings menu
        settings_menu = menubar.addMenu(tr("menu_settings"))

        # API Settings action
        api_settings_action = settings_menu.addAction(tr("menu_api_config"))
        api_settings_action.setShortcut("Ctrl+K")
        api_settings_action.triggered.connect(self._show_api_settings)

        # Language submenu
        language_menu = settings_menu.addMenu(tr("menu_language"))
        for lang_code, lang_name in LANGUAGES.items():
            lang_action = language_menu.addAction(lang_name)
            lang_action.setCheckable(True)
            lang_action.setChecked(lang_code == get_language())
            # Use lambda with default argument to capture lang_code
            lang_action.triggered.connect(lambda checked, lc=lang_code: self._change_language(lc))

        # View menu
        view_menu = menubar.addMenu(tr("menu_view"))

        # Toggle Dark/Light Theme action
        theme_action = view_menu.addAction(tr("menu_toggle_theme"))
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self._toggle_theme)

        # Help menu
        help_menu = menubar.addMenu(tr("menu_help"))

        # Keyboard Shortcuts action (F1)
        shortcuts_action = help_menu.addAction(tr("menu_shortcuts"))
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)

        # API Setup Guide action (F2)
        api_guide_action = help_menu.addAction(tr("menu_api_guide"))
        api_guide_action.setShortcut("F2")
        api_guide_action.triggered.connect(self._show_api_guide)

        # Separator
        help_menu.addSeparator()

        # About action
        about_action = help_menu.addAction(tr("menu_about"))
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

    def _change_language(self, lang_code: str):
        """Change application language"""
        from PyQt6.QtCore import QSettings

        if set_language(lang_code):
            # Save preference
            settings = QSettings("NEXUS", "MusicManager")
            settings.setValue("language", lang_code)

            # Show message that restart is needed
            QMessageBox.information(
                self,
                tr("language_changed_title"),
                tr("language_changed_message")
            )

            logger.info(f"Language changed to: {lang_code}")
        else:
            logger.error(f"Invalid language code: {lang_code}")

    def _toggle_theme(self):
        """Toggle between dark and light themes"""
        new_theme = self.theme_manager.toggle_theme()

        # Capitalize first letter for display
        theme_display = new_theme.capitalize()

        # Show status message
        self.statusBar.showMessage(tr("status_theme_switched", theme=theme_display), 2000)

        logger.info(f"User toggled theme to: {new_theme}")

    def _show_about(self):
        """Show about dialog - Bilingual (ES/EN)"""
        from PyQt6.QtWidgets import QMessageBox

        about_text = """
<h2>NEXUS Music Manager</h2>
<p><b>Versión / Version:</b> 2.0 (Production)</p>
<p><b>Fases / Phases:</b> 1-7 Complete</p>
<br>
<p><b>🇪🇸 Español:</b> Reproductor de música moderno con gestión de biblioteca,
búsqueda y descarga, reproducción de audio, listas de reproducción y visualizador.</p>
<p><b>🇬🇧 English:</b> Modern music player with library management, search & download,
audio playback, playlists, and visualizer.</p>
<br>
<p><b>Características / Features:</b></p>
<ul>
<li>📚 Gestión de Biblioteca / Library Management (10,000+ songs)</li>
<li>🔍 Búsqueda y Descarga / Search & Download (YouTube + Spotify)</li>
<li>🔄 Detección de Duplicados / Duplicate Detection</li>
<li>📁 Auto-Organizar / Auto-Organize Folders</li>
<li>✏️ Renombrar en Lote / Batch Rename</li>
<li>🎵 Reproductor con Visualizador / Music Player with Visualizer</li>
<li>📋 Gestión de Playlists / Playlist Management</li>
<li>📀 Vista de Álbumes / Album Grid View</li>
<li>🎯 Recomendaciones / Song Recommendations</li>
</ul>
<br>
<p><small>Construido con / Built with: Python, PyQt6, yt-dlp, pygame</small></p>
        """

        QMessageBox.about(self, "Acerca de / About - NEXUS Music Manager", about_text)

    def _show_api_guide(self):
        """Show API setup guide - Bilingual (ES/EN)"""
        from PyQt6.QtWidgets import QMessageBox, QTextBrowser, QDialog, QVBoxLayout, QPushButton

        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Guía de API / API Setup Guide")
        dialog.setMinimumSize(750, 650)

        layout = QVBoxLayout(dialog)

        # Create text browser for rich text with links
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml("""
<h2>🔑 Guía de Configuración de API / API Setup Guide</h2>

<p>🇪🇸 NEXUS usa claves API para buscar y descargar música de YouTube y Spotify.
Sigue los pasos para obtener tus claves gratuitas.</p>
<p>🇬🇧 NEXUS uses API keys to search and download music from YouTube and Spotify.
Follow the steps below to obtain your free API keys.</p>

<hr>

<h3>📺 YouTube Data API v3</h3>

<p><b>Paso 1 / Step 1:</b> Ir a / Go to <a href="https://console.cloud.google.com/">Google Cloud Console</a></p>
<p><b>Paso 2 / Step 2:</b> Crear proyecto nuevo / Create a new project</p>
<p><b>Paso 3 / Step 3:</b> Habilitar "YouTube Data API v3" / Enable "YouTube Data API v3":</p>
<ul>
<li>Click "Enable APIs and Services"</li>
<li>Buscar / Search "YouTube Data API v3"</li>
<li>Click "Enable"</li>
</ul>
<p><b>Paso 4 / Step 4:</b> Crear credenciales / Create credentials:</p>
<ul>
<li>Ir a / Go to "Credentials" tab</li>
<li>Click "Create Credentials" → "API Key"</li>
<li>Copiar tu clave / Copy your API key</li>
</ul>

<p><b>💡 Cuota / Quota:</b> 10,000 unidades/día gratis / 10,000 units/day free (≈ 100 búsquedas/searches)</p>

<hr>

<h3>🎵 Spotify Web API</h3>

<p><b>Paso 1 / Step 1:</b> Ir a / Go to <a href="https://developer.spotify.com/dashboard">Spotify Developer Dashboard</a></p>
<p><b>Paso 2 / Step 2:</b> Iniciar sesión / Log in (cuenta gratis funciona / free account works)</p>
<p><b>Paso 3 / Step 3:</b> Crear una app / Create an app:</p>
<ul>
<li>Click "Create App"</li>
<li>App Name: "NEXUS Music Manager"</li>
<li>Redirect URI: "http://localhost:8888/callback"</li>
<li>Marcar / Check "Web API"</li>
<li>Aceptar términos / Accept terms → "Create"</li>
</ul>
<p><b>Paso 4 / Step 4:</b> Obtener credenciales / Get credentials:</p>
<ul>
<li>Click "Settings"</li>
<li>Copiar / Copy "Client ID"</li>
<li>Click "View client secret" → Copiar / Copy "Client Secret"</li>
</ul>

<p><b>💡 Cuota / Quota:</b> Búsquedas ilimitadas / Unlimited searches (con límite de velocidad / rate limited)</p>

<hr>

<h3>💾 Guardar tus Claves / Saving Your Keys</h3>

<p><b>Método Recomendado / Recommended Method:</b></p>
<ul>
<li>Ir a / Go to <b>Configuración → Configuración de API</b> (o presiona / or press <b>Ctrl+K</b>)</li>
<li>Pegar tus claves / Paste your keys</li>
<li>Click "Test" para verificar / to verify</li>
<li>Click "Guardar / Save"</li>
</ul>

<hr>

<h3>✅ Probar tu Configuración / Testing Your Setup</h3>

<ol>
<li>Reiniciar la aplicación / Restart the application</li>
<li>Ir a pestaña / Go to tab <b>🔍 Buscar / Search</b></li>
<li>Buscar un artista o canción / Search for an artist or song</li>
<li>Deberían aparecer resultados de YouTube y Spotify / Both YouTube and Spotify results should appear</li>
</ol>

<hr>

<h3>❓ Solución de Problemas / Troubleshooting</h3>

<p><b>Error: "Missing API credentials" / "Faltan credenciales"</b></p>
<ul>
<li>Verificar que las claves estén guardadas / Check that keys are saved</li>
<li>Reiniciar la aplicación / Restart the application</li>
<li>Ir a Configuración → API y click "Test"</li>
</ul>

<p><b>Error: "API quota exceeded" / "Cuota excedida"</b></p>
<ul>
<li>YouTube: Esperar 24 horas / Wait 24 hours</li>
<li>Spotify: Esperar unos minutos / Wait a few minutes</li>
</ul>

<hr>

<p style="color: #666;"><small>
<b>🔒 Seguridad / Security:</b> Tus claves se guardan de forma segura en el gestor de credenciales de tu sistema operativo.
Your API keys are stored securely in your OS credential manager.
</small></p>
        """)

        layout.addWidget(text_browser)

        # Close button
        close_button = QPushButton("Cerrar / Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _create_top_section(self):
        """Create top section with Now Playing + Visualizer + Recommendations"""
        # Horizontal layout
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Now Playing Widget (left)
        self.now_playing = NowPlayingWidget(self.audio_player)
        top_layout.addWidget(self.now_playing, stretch=2)

        # Visualizer Widget (center) - Uses saved style from QSettings
        self.visualizer = VisualizerWidget()
        # NOTE: Don't call set_style() here - VisualizerWidget loads saved preference from QSettings
        top_layout.addWidget(self.visualizer, stretch=3)

        # Recommendations Widget (right)
        self.recommendations_widget = RecommendationsWidget(self.db_manager)
        self.recommendations_widget.setMaximumWidth(280)
        self.recommendations_widget.song_selected.connect(self._play_recommended_song)
        top_layout.addWidget(self.recommendations_widget, stretch=1)

        # Connect signals
        self.now_playing.position_changed.connect(
            lambda pos: self.visualizer.set_position(pos)
        )
        self.now_playing.song_loaded.connect(self._on_song_loaded)

        # Connect song metadata changes to recommendations
        self.now_playing.song_metadata_changed.connect(self._update_recommendations)

        # Connect prev/next signals (centralized handling for library + playlist)
        self.now_playing.prev_clicked.connect(self._on_global_prev_clicked)
        self.now_playing.next_clicked.connect(self._on_global_next_clicked)
        self.now_playing.song_ended.connect(self._on_global_song_ended)

        return top_widget

    def _create_middle_section(self):
        """Create middle section with tabs (including Playlist tab)"""
        # Just return the tab widget - Playlist is now a tab, not a separate panel
        tab_widget = self._create_tab_widget()
        return tab_widget

    def _create_tab_widget(self):
        """Create tab widget with all features"""
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Disable keyboard focus on tab widget to allow global shortcuts (Left/Right)
        # This prevents QTabWidget from consuming arrow keys for tab navigation
        self.tabs.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Tab 1: Import Library (Workflow: Import first)
        try:
            self.import_tab = ImportTab(self.db_manager)
            self.tabs.addTab(self.import_tab, tr("tab_import"))
            logger.info("Import tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Import tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_import") + " (Error)")

        # Tab 2: Library (Main library view)
        try:
            self.library_tab = LibraryTab(
                self.db_manager,
                self.audio_player,
                self.now_playing
            )
            self.tabs.addTab(self.library_tab, tr("tab_library"))
            # Connect playback_started to track source
            self.library_tab.playback_started.connect(self._on_library_playback_started)
            logger.info("Library tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Library tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_library") + " (Error)")

        # Tab 3: Albums (Visual album grid with covers)
        try:
            self.albums_widget = AlbumGridWidget(self.db_manager)
            self.tabs.addTab(self.albums_widget, tr("tab_albums"))
            # Connect album selection to filter library
            self.albums_widget.album_selected.connect(self._on_album_selected)
            logger.info("Albums tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Albums tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_albums") + " (Error)")

        # Tab 4: Lyrics (View lyrics while listening)
        try:
            self.lyrics_tab = LyricsTab(self.genius_client)
            self.tabs.addTab(self.lyrics_tab, tr("tab_lyrics"))
            logger.info("Lyrics tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Lyrics tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_lyrics") + " (Error)")

        # Tab 4: Search & Download (Find new music)
        try:
            self.search_tab = SearchTab(self.download_queue)
            self.tabs.addTab(self.search_tab, tr("tab_search"))
            logger.info("Search tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Search tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_search") + " (Error)")

        # Tab 5: Queue (Download queue)
        try:
            self.queue_widget = QueueWidget(self.download_queue)
            self.tabs.addTab(self.queue_widget, tr("tab_queue"))
            logger.info("Queue tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Queue tab: {e}")

        # Tab 6: Duplicates (Find duplicate files)
        try:
            self.duplicates_tab = DuplicatesTab(self.db_manager)
            self.tabs.addTab(self.duplicates_tab, tr("tab_duplicates"))
            logger.info("Duplicates tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Duplicates tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_duplicates") + " (Error)")

        # Tab 7: Rename (Rename files)
        try:
            self.rename_tab = RenameTab(self.db_manager)
            self.tabs.addTab(self.rename_tab, tr("tab_rename"))
            logger.info("Rename tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Rename tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_rename") + " (Error)")

        # Tab 8: Organize (Organize library)
        try:
            self.organize_tab = OrganizeTab(self.db_manager)
            self.tabs.addTab(self.organize_tab, tr("tab_organize"))
            logger.info("Organize tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Organize tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_organize") + " (Error)")

        # Tab 9: Cleanup Wizard (Metadata cleanup)
        try:
            # Get db_path from db_manager
            db_path = self.db_manager.db_path if hasattr(self.db_manager, 'db_path') else 'music_library.db'
            self.cleanup_tab = CleanupTab(db_path)
            self.tabs.addTab(self.cleanup_tab, tr("tab_cleanup"))
            logger.info("Cleanup Wizard tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Cleanup Wizard tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_cleanup") + " (Error)")

        # Tab 10: Playlist (Playlist management)
        try:
            self.playlist_widget = PlaylistWidget(self.playlist_manager, self.db_manager)
            self.tabs.addTab(self.playlist_widget, tr("tab_playlist"))
            # Connect playlist play signal
            self.playlist_widget.play_song_requested.connect(self._play_song_from_playlist)
            logger.info("Playlist tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Playlist tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_playlist") + " (Error)")

        # Tab 11: Cloud Sync (NEW - Phase 3)
        try:
            self.cloud_sync_tab = CloudSyncTab(db_manager=self.db_manager)
            self.tabs.addTab(self.cloud_sync_tab, tr("tab_cloud_sync"))
            logger.info("Cloud Sync tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Cloud Sync tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_cloud_sync") + " (Error)")

        # Tab 12: Plugins (NEW - Phase 3)
        try:
            self.plugins_tab = PluginsTab()
            self.tabs.addTab(self.plugins_tab, tr("tab_plugins"))
            logger.info("Plugins tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Plugins tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_plugins") + " (Error)")

        # Tab 13: Remote Control (NEW - Phase 3)
        try:
            self.remote_tab = RemoteTab()
            self.tabs.addTab(self.remote_tab, tr("tab_remote"))
            logger.info("Remote Control tab loaded")

            # Connect RemoteServer to audio player
            self._connect_remote_server()
        except Exception as e:
            logger.error(f"Failed to load Remote Control tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_remote") + " (Error)")

        # Tab 14: Content Filter (NEW - Phase 8)
        try:
            self.content_filter_tab = ContentFilterTab(self.db_manager)
            self.tabs.addTab(self.content_filter_tab, tr("tab_content_filter"))
            logger.info("Content Filter tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Content Filter tab: {e}")
            self.tabs.addTab(QWidget(), tr("tab_content_filter") + " (Error)")

        return self.tabs

    def _on_song_loaded(self, file_path: str):
        """
        Handle song loaded event - extract spectrum/waveform asynchronously

        Args:
            file_path: Path to audio file
        """
        try:
            logger.info(f"Starting audio analysis for: {Path(file_path).name}")

            # Get duration from audio player (already loaded)
            duration = self.audio_player.get_duration() if self.audio_player else 0.0

            # Show loading indicator
            self.statusBar.showMessage("Analyzing audio for visualizer...", 0)

            # Stop any existing worker
            if hasattr(self, 'spectrum_worker') and self.spectrum_worker.isRunning():
                self.spectrum_worker.terminate()
                self.spectrum_worker.wait()

            # Create worker thread for spectrum extraction (non-blocking)
            from core.spectrum_worker import SpectrumWorker
            self.spectrum_worker = SpectrumWorker(
                self.waveform_extractor,
                file_path,
                num_bars=60
            )

            # Connect signals
            self.spectrum_worker.finished.connect(
                lambda data, dur: self._on_spectrum_extracted(data, dur, duration, file_path)
            )
            self.spectrum_worker.error.connect(
                lambda err: self._on_spectrum_error(err, file_path, duration)
            )
            self.spectrum_worker.progress.connect(
                lambda pct: self.statusBar.showMessage(f"Analyzing audio... {pct}%", 0)
            )

            # Start extraction in background
            self.spectrum_worker.start()

        except Exception as e:
            logger.error(f"Error starting audio analysis: {e}")
            self.statusBar.showMessage(f"Error: {str(e)}", 5000)
            self.visualizer.clear()

    def _on_spectrum_extracted(self, spectrum_data, spectrum_duration, audio_duration, file_path):
        """
        Handle spectrum extraction completion

        Args:
            spectrum_data: Extracted spectrum data
            spectrum_duration: Spectrum duration
            audio_duration: Audio player duration
            file_path: Original file path
        """
        try:
            # Update visualizer with dynamic spectrum data
            self.visualizer.set_spectrum(spectrum_data, spectrum_duration)
            self.visualizer.set_duration(audio_duration)

            logger.info(f"Dynamic spectrum loaded: {len(spectrum_data)} windows")
            self.statusBar.showMessage("Visualizer ready", 2000)

        except Exception as e:
            logger.error(f"Error applying spectrum data: {e}")
            self.statusBar.showMessage(f"Visualizer error: {str(e)}", 5000)

    def _on_spectrum_error(self, error_msg, file_path, duration):
        """
        Handle spectrum extraction error - fallback to waveform

        Args:
            error_msg: Error message
            file_path: Audio file path
            duration: Audio duration
        """
        logger.warning(f"Spectrum extraction failed: {error_msg}")
        self.statusBar.showMessage("Using simplified visualizer...", 2000)

        try:
            # Fallback: Extract static waveform
            waveform = self.waveform_extractor.extract(file_path, num_points=1000)

            if waveform:
                self.visualizer.set_waveform(waveform)
                self.visualizer.set_duration(duration)
                logger.info(f"Waveform fallback loaded: {len(waveform)} points")
            else:
                logger.warning(f"Failed to extract any visualization data")
                self.visualizer.clear()

        except Exception as e:
            logger.error(f"Fallback extraction error: {e}")
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

    def _play_song_from_playlist(self, song_info: dict):
        """Play song from playlist widget"""
        try:
            file_path = song_info.get('file_path')
            if not file_path:
                logger.error("Song has no file path")
                return

            # Check if file exists
            from pathlib import Path
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                QMessageBox.warning(self, "File Not Found", f"The music file could not be found:\n{file_path}")
                return

            # Load and play
            success = self.audio_player.load(file_path)
            if success:
                self.audio_player.play()
                self.now_playing.load_song(song_info)
                self.now_playing.set_playing(True)

                # Track playback source as playlist
                self._playback_source = 'playlist'
                self._current_playlist_id = self.playlist_widget.current_playlist_id

                # Get current playlist songs and find index
                if self._current_playlist_id:
                    self._current_playlist_songs = self.playlist_manager.get_playlist_songs(
                        self._current_playlist_id
                    )
                    # Find current song index
                    song_id = song_info.get('id')
                    for i, s in enumerate(self._current_playlist_songs):
                        if s.get('id') == song_id:
                            self._current_playlist_index = i
                            break

                    # Highlight the playing song in playlist widget
                    if song_id and hasattr(self, 'playlist_widget'):
                        self.playlist_widget.highlight_playing_song(song_id)

                logger.info(f"Playing from playlist: {song_info.get('title', 'Unknown')} "
                           f"(index {self._current_playlist_index}/{len(self._current_playlist_songs)})")
            else:
                logger.error(f"Failed to load: {file_path}")

        except Exception as e:
            logger.error(f"Error playing song from playlist: {e}")

    def _play_next_from_playlist(self):
        """Play next song in current playlist"""
        if not self._current_playlist_songs:
            logger.warning("No playlist songs loaded")
            return

        # Move to next index
        next_index = self._current_playlist_index + 1

        # Check if we reached the end
        if next_index >= len(self._current_playlist_songs):
            logger.info("Reached end of playlist")
            self.statusBar.showMessage("End of playlist", 2000)
            return

        # Get next song
        next_song = self._current_playlist_songs[next_index]
        song_info = self.db_manager.get_song_by_id(next_song['id'])

        if song_info:
            self._current_playlist_index = next_index
            self._play_song_from_playlist(song_info)
            logger.info(f"Playing next in playlist: {song_info.get('title')}")
        else:
            logger.error(f"Song not found: {next_song['id']}")

    def _play_prev_from_playlist(self):
        """Play previous song in current playlist"""
        if not self._current_playlist_songs:
            logger.warning("No playlist songs loaded")
            return

        # Move to previous index
        prev_index = self._current_playlist_index - 1

        # Check if we're at the beginning
        if prev_index < 0:
            logger.info("Already at beginning of playlist")
            self.statusBar.showMessage("Beginning of playlist", 2000)
            return

        # Get previous song
        prev_song = self._current_playlist_songs[prev_index]
        song_info = self.db_manager.get_song_by_id(prev_song['id'])

        if song_info:
            self._current_playlist_index = prev_index
            self._play_song_from_playlist(song_info)
            logger.info(f"Playing previous in playlist: {song_info.get('title')}")
        else:
            logger.error(f"Song not found: {prev_song['id']}")

    def _on_global_next_clicked(self):
        """Handle next button click - route to correct source"""
        if self._playback_source == 'playlist':
            logger.info("Next clicked (playlist mode)")
            self._play_next_from_playlist()
        else:
            # Delegate to library tab
            logger.info("Next clicked (library mode)")
            if hasattr(self, 'library_tab'):
                self.library_tab._on_next_clicked()

    def _on_global_prev_clicked(self):
        """Handle prev button click - route to correct source"""
        if self._playback_source == 'playlist':
            logger.info("Prev clicked (playlist mode)")
            self._play_prev_from_playlist()
        else:
            # Delegate to library tab
            logger.info("Prev clicked (library mode)")
            if hasattr(self, 'library_tab'):
                self.library_tab._on_prev_clicked()

    def _on_global_song_ended(self):
        """Handle song ended - route to correct source for auto-play"""
        if self._playback_source == 'playlist':
            logger.info("Song ended (playlist mode) - auto-playing next")
            self._play_next_from_playlist()
        else:
            # Delegate to library tab
            logger.info("Song ended (library mode)")
            if hasattr(self, 'library_tab'):
                self.library_tab._on_song_ended()

    def _connect_remote_server(self):
        """Connect RemoteServer callbacks to audio player and controls using Qt signals"""
        try:
            from services.remote_server import RemoteServer, NowPlayingInfo
            from PyQt6.QtCore import QTimer

            server = RemoteServer.get_instance()
            self._remote_server = server  # Keep reference for updates

            # Connect Qt signal (thread-safe) to handle commands
            if hasattr(server, 'command_received'):
                server.command_received.connect(self._handle_remote_command)
                logger.info("Connected to RemoteServer command_received signal")

            # Start timer to update now_playing info for mobile interface
            self._remote_update_timer = QTimer()
            self._remote_update_timer.timeout.connect(self._update_remote_now_playing)
            self._remote_update_timer.start(500)  # Update every 500ms

            # Force immediate update so mobile gets current state right away
            QTimer.singleShot(100, self._update_remote_now_playing)

            logger.info("Remote server callbacks connected to audio player")

        except Exception as e:
            logger.error(f"Failed to connect remote server: {e}")

    def _handle_remote_command(self, command: str, params: dict):
        """Handle remote commands in main Qt thread (thread-safe via signal)"""
        logger.info(f"Handling remote command: {command} with params: {params}")

        try:
            if command == 'play':
                self.audio_player.play()
                if hasattr(self, 'now_playing'):
                    self.now_playing.set_playing(True)

            elif command == 'pause':
                self.audio_player.pause()
                if hasattr(self, 'now_playing'):
                    self.now_playing.set_playing(False)

            elif command == 'toggle':
                if self.audio_player.is_playing():
                    self.audio_player.pause()
                    if hasattr(self, 'now_playing'):
                        self.now_playing.set_playing(False)
                else:
                    self.audio_player.play()
                    if hasattr(self, 'now_playing'):
                        self.now_playing.set_playing(True)

            elif command == 'next':
                self._on_global_next_clicked()

            elif command == 'previous':
                self._on_global_prev_clicked()

            elif command == 'volume':
                volume = params.get('volume', 100)
                self.audio_player.set_volume(volume / 100.0)
                # Sync volume slider and label in now_playing widget
                if hasattr(self, 'now_playing'):
                    if hasattr(self.now_playing, 'volume_slider'):
                        self.now_playing.volume_slider.blockSignals(True)  # Prevent feedback loop
                        self.now_playing.volume_slider.setValue(volume)
                        self.now_playing.volume_slider.blockSignals(False)
                    if hasattr(self.now_playing, 'volume_label_value'):
                        self.now_playing.volume_label_value.setText(f"{volume}%")

            elif command == 'seek':
                position = params.get('position', 0)
                self.audio_player.seek(position)

            logger.info(f"Remote command '{command}' executed in main thread")

        except Exception as e:
            logger.error(f"Error handling remote command '{command}': {e}")

    def _update_remote_now_playing(self):
        """Update RemoteServer with current playback info"""
        if not hasattr(self, '_remote_server') or not self._remote_server:
            return

        try:
            from services.remote_server import NowPlayingInfo

            # Get current song info from now_playing widget
            title = ""
            artist = ""
            album = ""

            if hasattr(self, 'now_playing') and hasattr(self.now_playing, 'current_song'):
                song = self.now_playing.current_song
                if song:
                    title = song.get('title', '')
                    artist = song.get('artist', '')
                    album = song.get('album', '')

            # Get playback state
            position = self.audio_player.get_position() if self.audio_player else 0
            duration = self.audio_player.get_duration() if self.audio_player else 0
            is_playing = self.audio_player.is_playing() if self.audio_player else False
            volume = int(self.audio_player.get_volume() * 100)

            # Update server
            info = NowPlayingInfo(
                title=title,
                artist=artist,
                album=album,
                duration=int(duration),
                position=int(position),
                is_playing=is_playing,
                volume=volume
            )
            self._remote_server.update_now_playing(info)

        except Exception as e:
            pass  # Silently ignore errors to avoid log spam

    def _on_library_playback_started(self):
        """Handle playback started from library - update source tracking"""
        self._playback_source = 'library'
        self._current_playlist_id = None
        self._current_playlist_songs = []
        self._current_playlist_index = -1

        # Clear playlist highlight since we're now playing from library
        if hasattr(self, 'playlist_widget'):
            self.playlist_widget.clear_playing_highlight()

        logger.info("Playback source set to: library")

    def _on_album_selected(self, album_data: dict):
        """Handle album selection from grid - switch to library and filter"""
        album_name = album_data.get('album', '')
        artist_name = album_data.get('artist', '')

        # Switch to library tab
        if hasattr(self, 'library_tab') and hasattr(self, 'tabs'):
            self.tabs.setCurrentWidget(self.library_tab)

            # Apply filter if library tab has search functionality
            if hasattr(self.library_tab, 'search_input'):
                # Search by album name
                self.library_tab.search_input.setText(album_name)
                self.library_tab.search_input.returnPressed.emit()

            self.statusBar.showMessage(f"Showing album: {album_name}", 3000)
            logger.info(f"Album selected: {album_name} by {artist_name}")

    def _update_recommendations(self, song_data: dict):
        """Update recommendations based on current song"""
        if hasattr(self, 'recommendations_widget'):
            self.recommendations_widget.set_current_song(song_data)

    def _play_recommended_song(self, song_data: dict):
        """Play a song selected from recommendations"""
        try:
            file_path = song_data.get('file_path')
            if not file_path:
                logger.error("Recommended song has no file path")
                return

            from pathlib import Path
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                QMessageBox.warning(
                    self, "File Not Found",
                    f"The music file could not be found:\n{file_path}"
                )
                return

            # Load and play
            success = self.audio_player.load(file_path)
            if success:
                self.audio_player.play()
                self.now_playing.load_song(song_data)
                self.now_playing.set_playing(True)

                # Update playback source to library
                self._playback_source = 'library'

                logger.info(f"Playing recommended: {song_data.get('title')}")
                self.statusBar.showMessage(
                    f"Playing recommendation: {song_data.get('title')}", 3000
                )
            else:
                logger.error(f"Failed to load: {file_path}")

        except Exception as e:
            logger.error(f"Error playing recommended song: {e}")

    def _handle_seek_backward(self, seconds):
        """Handle Left arrow - Seek backward"""
        current = self.audio_player.get_position()
        new_pos = max(0, current - seconds)
        logger.debug(f"Seek backward: current={current:.2f}s, new_pos={new_pos:.2f}s")
        self.audio_player.seek(new_pos)

    def _handle_seek_forward(self, seconds):
        """Handle Right arrow - Seek forward"""
        current = self.audio_player.get_position()
        duration = self.audio_player.get_duration()
        new_pos = min(duration, current + seconds)
        logger.debug(f"Seek forward: current={current:.2f}s, new_pos={new_pos:.2f}s")
        self.audio_player.seek(new_pos)

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

    # Load saved language preference
    from PyQt6.QtCore import QSettings
    settings = QSettings("NEXUS", "MusicManager")
    saved_language = settings.value("language", "es")  # Default: Spanish
    set_language(saved_language)
    logger.info(f"Language loaded: {saved_language}")

    # Set dark theme (optional)
    app.setStyle("Fusion")

    # Create and show main window
    window = MusicPlayerApp()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
