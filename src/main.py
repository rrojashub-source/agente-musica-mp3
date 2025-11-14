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

        # Setup UI
        self._init_ui()

        logger.info("Application started successfully")

    def _init_ui(self):
        """Initialize user interface"""
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
            self.search_tab = SearchTab(self.db_manager)
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
            # Note: QueueWidget needs download_queue instance
            # For now, use placeholder
            self.queue_widget = QWidget()  # TODO: Integrate with DownloadQueue
            tabs.addTab(self.queue_widget, "📥 Queue")
            logger.info("Queue tab loaded (placeholder)")
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

    def closeEvent(self, event):
        """Handle application close event"""
        # Cleanup audio player
        try:
            self.audio_player.cleanup()
            logger.info("Audio player cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up audio player: {e}")

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
