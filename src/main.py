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

# Import GUI tabs
from gui.tabs.library_tab import LibraryTab
from gui.tabs.search_tab import SearchTab
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

        # Setup UI
        self._init_ui()

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

        # Help menu
        help_menu = menubar.addMenu("&Help")

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
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: Library (Phase 3 + Phase 6 playback integration)
        try:
            self.library_tab = LibraryTab(
                self.db_manager,
                self.audio_player,
                self.now_playing
            )
            tabs.addTab(self.library_tab, "🎵 Library")
            logger.info("Library tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Library tab: {e}")
            tabs.addTab(QWidget(), "🎵 Library (Error)")

        # Tab 2: Search & Download (Phase 4)
        try:
            self.search_tab = SearchTab(self.download_queue)
            tabs.addTab(self.search_tab, "🔍 Search & Download")
            logger.info("Search tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Search tab: {e}")
            tabs.addTab(QWidget(), "🔍 Search (Error)")

        # Tab 3: Import Library (NEW - Library Import Feature)
        try:
            self.import_tab = ImportTab(self.db_manager)
            tabs.addTab(self.import_tab, "📥 Import Library")
            logger.info("Import tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Import tab: {e}")
            tabs.addTab(QWidget(), "📥 Import (Error)")

        # Tab 4: Download Queue (Phase 4)
        try:
            self.queue_widget = QueueWidget(self.download_queue)
            tabs.addTab(self.queue_widget, "📥 Queue")
            logger.info("Queue tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Queue tab: {e}")

        # Tab 4: Duplicates (Phase 5)
        try:
            self.duplicates_tab = DuplicatesTab(self.db_manager)
            tabs.addTab(self.duplicates_tab, "🔍 Duplicates")
            logger.info("Duplicates tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Duplicates tab: {e}")
            tabs.addTab(QWidget(), "🔍 Duplicates (Error)")

        # Tab 5: Organize (Phase 5)
        try:
            self.organize_tab = OrganizeTab(self.db_manager)
            tabs.addTab(self.organize_tab, "📁 Organize")
            logger.info("Organize tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Organize tab: {e}")
            tabs.addTab(QWidget(), "📁 Organize (Error)")

        # Tab 6: Rename (Phase 5)
        try:
            self.rename_tab = RenameTab(self.db_manager)
            tabs.addTab(self.rename_tab, "✏️ Rename")
            logger.info("Rename tab loaded")
        except Exception as e:
            logger.error(f"Failed to load Rename tab: {e}")
            tabs.addTab(QWidget(), "✏️ Rename (Error)")

        return tabs

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
