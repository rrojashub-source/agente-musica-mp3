#!/usr/bin/env python3
"""
NEXUS Music Manager - COMPLETE APPLICATION
All Phases Integrated: Library + Search/Download + Management Tools

Project: AGENTE_MUSICA_MP3_001
Phases: 3 (Library) + 4 (Search/Download) + 5 (Management)
"""

import sys
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
        QStatusBar, QMessageBox, QTableView, QComboBox, QHBoxLayout, QLabel,
        QMenuBar, QMenu, QDialog, QPushButton
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QAction
except ImportError:
    print("❌ PyQt6 not installed")
    print("   Install with: pip install PyQt6")
    exit(1)

# Import translation system
from translations import t

# Import logging system
from logger_system import get_logger, log_startup, log_shutdown, setup_exception_hook

# Import Phase 3 (Library)
sys.path.insert(0, str(Path(__file__).parent / "phase3_integration"))
from music_model_sqlite import MusicLibrarySQLiteModel

# Import Phase 4 (Search & Download)
sys.path.insert(0, str(Path(__file__).parent / "phase4_search_download"))
from search_tab import SearchTab
from download_queue import DownloadQueueWidget
from playlist_downloader import PlaylistDownloaderWidget

# Import Phase 5 (Management Tools)
sys.path.insert(0, str(Path(__file__).parent / "phase5_management_tools"))
from duplicates_detector import DuplicatesDetectorWidget
from auto_organize import AutoOrganizeWidget
from batch_rename import BatchRenameWidget

# Import Help Tab
from help_tab import HelpTab

# Import Phase 6 (Player & Lyrics)
sys.path.insert(0, str(Path(__file__).parent / "phase6_player_lyrics"))
from music_player import MusicPlayerWidget

# Import Cleanup Assistant (NEW - Fase 1)
from cleanup_assistant_tab import CleanupAssistantTab

# Import API Config Wizard
from api_config_wizard import APIConfigWizard

# Import Setup Wizard and Config Manager
from setup_wizard import SetupWizard
from config_manager import ConfigManager


class NEXUSMusicManager(QMainWindow):
    """
    COMPLETE NEXUS Music Manager
    - Phase 3: Library (10,000+ songs, FTS5 search)
    - Phase 4: Search & Download (YouTube, Spotify, Playlists)
    - Phase 5: Management (Duplicates, Organize, Rename)
    """

    def __init__(self, db_path: str, download_dir: str = None):
        super().__init__()

        # Setup logging
        self.logger = get_logger()
        self.logger.info("Initializing NEXUS Music Manager")

        self.db_path = db_path
        self.download_dir = download_dir or str(Path.home() / "Music" / "Downloads")

        # Components
        self.library_model = None

        try:
            self.init_ui()
            self.setup_connections()
            self.logger.info("UI initialized successfully")
        except Exception as e:
            self.logger.exception("Failed to initialize UI")
            raise

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(t("app_title"))
        self.setGeometry(100, 100, 1600, 900)

        # Create menu bar
        self.create_menu_bar()

        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 10))

        # ========================================
        # CLEANUP ASSISTANT (NEW - antes de Library)
        # ========================================
        self.cleanup_tab = CleanupAssistantTab()
        self.tabs.addTab(self.cleanup_tab, "🧹 Limpieza Metadata")

        # ========================================
        # PHASE 3: LIBRARY MANAGEMENT
        # ========================================
        self.library_tab = self.create_library_tab()
        self.tabs.addTab(self.library_tab, t("tab_library"))

        # ========================================
        # PHASE 4: SEARCH & DOWNLOAD
        # ========================================
        self.search_tab = SearchTab(self.db_path)
        self.tabs.addTab(self.search_tab, t("tab_search"))

        self.playlist_downloader = PlaylistDownloaderWidget()
        self.tabs.addTab(self.playlist_downloader, t("tab_playlist"))

        self.download_queue = DownloadQueueWidget(self.db_path, self.download_dir)
        self.tabs.addTab(self.download_queue, t("tab_queue"))

        # ========================================
        # PHASE 5: MANAGEMENT TOOLS
        # ========================================
        self.duplicates_detector = DuplicatesDetectorWidget(self.db_path)
        self.tabs.addTab(self.duplicates_detector, t("tab_duplicates"))

        self.auto_organize = AutoOrganizeWidget(self.db_path)
        self.tabs.addTab(self.auto_organize, t("tab_organize"))

        self.batch_rename = BatchRenameWidget(self.db_path)
        self.tabs.addTab(self.batch_rename, t("tab_rename"))

        # ========================================
        # PHASE 6: PLAYER & LYRICS
        # ========================================
        self.music_player = MusicPlayerWidget(self.db_path)
        self.tabs.addTab(self.music_player, t("tab_player"))

        # ========================================
        # HELP TAB
        # ========================================
        self.help_tab = HelpTab()
        self.tabs.addTab(self.help_tab, t("tab_help"))

        main_layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(t("status_ready"))

    def create_menu_bar(self):
        """Create menu bar with options"""
        menu_bar = self.menuBar()

        # Tools menu
        tools_menu = menu_bar.addMenu("🔧 Tools")

        # API Configuration action
        api_config_action = QAction("🔑 Configure API Keys...", self)
        api_config_action.triggered.connect(self.open_api_config_wizard)
        tools_menu.addAction(api_config_action)

        tools_menu.addSeparator()

        # About action
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        tools_menu.addAction(about_action)

    def open_api_config_wizard(self):
        """Open API configuration wizard"""
        wizard = APIConfigWizard(self)
        wizard.exec()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About NEXUS Music Manager",
            "<h2>🎵 NEXUS Music Manager</h2>"
            "<p><b>Version:</b> Complete Edition (Phases 3+4+5+6)</p>"
            "<p><b>Project:</b> AGENTE_MUSICA_MP3_001</p>"
            "<br>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>📚 Library Management (10,000+ songs)</li>"
            "<li>🔍 Search & Download (YouTube + Spotify)</li>"
            "<li>📥 Download Queue (concurrent)</li>"
            "<li>🔍 Duplicate Detection (3 methods)</li>"
            "<li>📁 Auto-Organize Library</li>"
            "<li>📝 Batch Rename</li>"
            "<li>▶️ Music Player with Lyrics</li>"
            "<li>🇪🇸 Interfaz en Español</li>"
            "</ul>"
            "<br>"
            "<p>Built with PyQt6 + SQLite + FFmpeg</p>"
        )


    def create_library_tab(self) -> QWidget:
        """Create library tab (Phase 3 view)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Table view with SQLite model
        self.library_table = QTableView()

        # Load library model
        self.library_model = MusicLibrarySQLiteModel(self.db_path)
        self.library_table.setModel(self.library_model)

        # Table settings
        self.library_table.setAlternatingRowColors(True)
        self.library_table.setSortingEnabled(True)
        self.library_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        # Column widths
        self.library_table.setColumnWidth(0, 60)   # ID
        self.library_table.setColumnWidth(1, 250)  # Title
        self.library_table.setColumnWidth(2, 200)  # Artists
        self.library_table.setColumnWidth(3, 200)  # Album
        self.library_table.setColumnWidth(4, 100)  # Genre
        self.library_table.setColumnWidth(5, 70)   # Year

        layout.addWidget(self.library_table)

        # Library management buttons
        buttons_layout = QHBoxLayout()

        rescan_btn = QPushButton("🔄 Reescanear Biblioteca")
        rescan_btn.setFixedHeight(35)
        rescan_btn.setFont(QFont("Arial", 10))
        rescan_btn.clicked.connect(self.rescan_library)
        buttons_layout.addWidget(rescan_btn)

        change_folder_btn = QPushButton("📁 Cambiar Carpeta de Música")
        change_folder_btn.setFixedHeight(35)
        change_folder_btn.setFont(QFont("Arial", 10))
        change_folder_btn.clicked.connect(self.change_music_folder)
        buttons_layout.addWidget(change_folder_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Stats label
        stats = self.library_model.get_stats()
        if stats:
            from PyQt6.QtWidgets import QLabel
            stats_text = (
                f"📊 {stats['total_songs']:,} {t('stats_songs')} | "
                f"👥 {stats['total_artists']:,} {t('stats_artists')} | "
                f"💿 {stats['total_albums']:,} {t('stats_albums')} | "
                f"🎭 {stats['total_genres']} {t('stats_genres')} | "
                f"⏱️ {stats['total_duration_hours']:.1f} {t('stats_hours')}"
            )
            stats_label = QLabel(stats_text)
            stats_label.setFont(QFont("Arial", 10))
            layout.addWidget(stats_label)

        return widget

    def setup_connections(self):
        """Connect signals between components"""

        # Search tab → Download queue
        self.search_tab.add_to_queue_btn.clicked.disconnect()
        self.search_tab.add_to_queue_btn.clicked.connect(self.add_search_to_queue)

        # Playlist downloader → Download queue
        self.playlist_downloader.playlist_ready.connect(self.add_playlist_to_queue)

    def add_search_to_queue(self):
        """Add selected search results to download queue"""
        selected = self.search_tab.selected_songs

        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select songs to download")
            return

        self.download_queue.add_to_queue(selected)
        self.tabs.setCurrentWidget(self.download_queue)
        self.search_tab.clear_selection()

        self.status_bar.showMessage(f"✅ Added {len(selected)} songs to download queue")

    def add_playlist_to_queue(self, songs: list):
        """Add playlist songs to download queue"""
        if not songs:
            return

        self.download_queue.add_to_queue(songs)
        self.tabs.setCurrentWidget(self.download_queue)

        self.status_bar.showMessage(f"✅ Added {len(songs)} songs from playlist")

    def rescan_library(self):
        """Reescanear e importar biblioteca actual"""
        from config_manager import ConfigManager

        config = ConfigManager()
        library_path = config.get_library_path()

        if not library_path:
            QMessageBox.warning(
                self,
                "Sin Biblioteca",
                "No hay una carpeta de música configurada.\n"
                "Usa 'Cambiar Carpeta de Música' para configurar una."
            )
            return

        # Verificar que la carpeta existe
        from pathlib import Path
        if not Path(library_path).exists():
            QMessageBox.warning(
                self,
                "Carpeta No Encontrada",
                f"La carpeta configurada no existe:\n{library_path}\n\n"
                f"Usa 'Cambiar Carpeta de Música' para configurar una nueva."
            )
            return

        # Confirmar reescaneo
        reply = QMessageBox.question(
            self,
            "Reescanear e Importar Biblioteca",
            f"¿Reescanear e importar la biblioteca?\n\n"
            f"Carpeta: {library_path}\n\n"
            f"Esto:\n"
            f"• Buscará todos los archivos de audio\n"
            f"• Extraerá metadatos (título, artista, álbum, etc.)\n"
            f"• Los importará a la base de datos\n\n"
            f"Este proceso puede tardar varios minutos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Importar worker de importación
        from library_import_worker import LibraryImportWorker
        from PyQt6.QtWidgets import QProgressDialog

        # Crear diálogo de progreso
        progress = QProgressDialog(
            "Importando biblioteca de música...",
            "Cancelar",
            0, 100,
            self
        )
        progress.setWindowTitle("Importando Biblioteca")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # Crear worker
        self.import_worker = LibraryImportWorker(library_path, self.db_path)

        # Conectar señales
        def on_progress(value, message):
            progress.setValue(value)
            progress.setLabelText(f"{message}")

        def on_file_processed(file_path, success):
            # Opcional: loggear archivos procesados
            pass

        def on_complete(imported_count, error_count):
            progress.close()
            config.set_audio_files_count(imported_count)

            # Recargar modelo de biblioteca
            if self.library_model:
                self.library_model.reload()

                # Actualizar estadísticas
                stats = self.library_model.get_stats()
                if stats:
                    from PyQt6.QtWidgets import QLabel
                    stats_text = (
                        f"📊 {stats['total_songs']:,} {t('stats_songs')} | "
                        f"👥 {stats['total_artists']:,} {t('stats_artists')} | "
                        f"💿 {stats['total_albums']:,} {t('stats_albums')} | "
                        f"🎭 {stats['total_genres']} {t('stats_genres')} | "
                        f"⏱️ {stats['total_duration_hours']:.1f} {t('stats_hours')}"
                    )
                    # Buscar y actualizar label de stats
                    for child in self.library_tab.findChildren(QLabel):
                        if "📊" in child.text():
                            child.setText(stats_text)
                            break

            # Mensaje de resultado
            result_msg = f"✅ Importación completa\n\n"
            result_msg += f"Archivos importados: {imported_count:,}\n"
            if error_count > 0:
                result_msg += f"Errores: {error_count:,}\n"

            QMessageBox.information(
                self,
                "Importación Completa",
                result_msg
            )

            self.status_bar.showMessage(f"✅ Biblioteca importada: {imported_count:,} archivos")

        def on_error(error_msg):
            progress.close()
            QMessageBox.critical(
                self,
                "Error de Importación",
                f"❌ Error al importar la biblioteca:\n\n{error_msg}"
            )

        def on_cancel():
            if self.import_worker:
                self.import_worker.cancel()
                self.status_bar.showMessage("❌ Importación cancelada")

        self.import_worker.progress_update.connect(on_progress)
        self.import_worker.file_processed.connect(on_file_processed)
        self.import_worker.import_complete.connect(on_complete)
        self.import_worker.error_occurred.connect(on_error)
        progress.canceled.connect(on_cancel)

        # Iniciar importación
        self.import_worker.start()
        self.status_bar.showMessage(f"🔄 Importando: {library_path}")

    def change_music_folder(self):
        """Cambiar carpeta de música"""
        from config_manager import ConfigManager
        from setup_wizard import SetupWizard

        # Mostrar advertencia
        reply = QMessageBox.question(
            self,
            "Cambiar Carpeta de Música",
            "⚠️ ¿Cambiar la carpeta de música?\n\n"
            "ADVERTENCIA: Esto borrará la biblioteca actual\n"
            "y la reemplazará con la nueva carpeta.\n\n"
            "¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Abrir wizard de configuración
        wizard = SetupWizard(self)
        result = wizard.exec()

        if result == QDialog.DialogCode.Accepted:
            library_path = wizard.get_library_path()

            config = ConfigManager()

            if library_path:
                # Limpiar base de datos antes de importar nueva carpeta
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent / "phase2_database"))
                from database_manager import MusicDatabaseManager

                db = MusicDatabaseManager(self.db_path)

                # Borrar todas las canciones - Estrategia: DROP tabla FTS y recrearla
                cursor = db.conn.cursor()

                # ESTRATEGIA RADICAL: DROP tabla FTS completa (evita triggers)
                cursor.execute("DROP TABLE IF EXISTS songs_fts")

                # Borrar relaciones y datos
                cursor.execute("DELETE FROM song_artists")
                cursor.execute("DELETE FROM song_genres")
                cursor.execute("DELETE FROM songs")
                cursor.execute("DELETE FROM artists")
                cursor.execute("DELETE FROM albums")
                cursor.execute("DELETE FROM genres")

                # RECREAR tabla FTS5
                cursor.execute("""
                    CREATE VIRTUAL TABLE songs_fts USING fts5(
                        title,
                        artist_names,
                        album_title,
                        lyrics,
                        content='songs',
                        content_rowid='id'
                    )
                """)

                # RECREAR triggers (copiados del schema original)
                cursor.execute("""
                    CREATE TRIGGER songs_fts_insert AFTER INSERT ON songs
                    BEGIN
                        INSERT INTO songs_fts(rowid, title, artist_names, album_title, lyrics)
                        SELECT
                            NEW.id,
                            NEW.title,
                            (SELECT GROUP_CONCAT(a.name, ', ')
                             FROM song_artists sa
                             JOIN artists a ON sa.artist_id = a.id
                             WHERE sa.song_id = NEW.id),
                            (SELECT al.title FROM albums al WHERE al.id = NEW.album_id),
                            NEW.lyrics;
                    END
                """)

                cursor.execute("""
                    CREATE TRIGGER songs_fts_delete AFTER DELETE ON songs
                    BEGIN
                        DELETE FROM songs_fts WHERE rowid = OLD.id;
                    END
                """)

                cursor.execute("""
                    CREATE TRIGGER songs_fts_update AFTER UPDATE ON songs
                    BEGIN
                        DELETE FROM songs_fts WHERE rowid = OLD.id;
                        INSERT INTO songs_fts(rowid, title, artist_names, album_title, lyrics)
                        SELECT
                            NEW.id,
                            NEW.title,
                            (SELECT GROUP_CONCAT(a.name, ', ')
                             FROM song_artists sa
                             JOIN artists a ON sa.artist_id = a.id
                             WHERE sa.song_id = NEW.id),
                            (SELECT al.title FROM albums al WHERE al.id = NEW.album_id),
                            NEW.lyrics;
                    END
                """)

                db.conn.commit()
                db.close()

                # Usuario configuró nueva biblioteca
                config.set_library_path(library_path)
                config.set_audio_files_count(wizard.get_audio_files_count())
                config.set_use_demo_database(False)

                # Recargar biblioteca (ahora vacía)
                if self.library_model:
                    self.library_model.reload()

                    # Actualizar estadísticas
                    stats = self.library_model.get_stats()
                    if stats:
                        from PyQt6.QtWidgets import QLabel
                        stats_text = (
                            f"📊 {stats['total_songs']:,} {t('stats_songs')} | "
                            f"👥 {stats['total_artists']:,} {t('stats_artists')} | "
                            f"💿 {stats['total_albums']:,} {t('stats_albums')} | "
                            f"🎭 {stats['total_genres']} {t('stats_genres')} | "
                            f"⏱️ {stats['total_duration_hours']:.1f} {t('stats_hours')}"
                        )
                        # Buscar y actualizar label de stats
                        for child in self.library_tab.findChildren(QLabel):
                            if "📊" in child.text():
                                child.setText(stats_text)
                                break

                # Mostrar mensaje y preguntar si quiere importar ahora
                reply = QMessageBox.question(
                    self,
                    "Configuración Actualizada",
                    f"✅ Carpeta de música actualizada exitosamente\n\n"
                    f"Nueva carpeta: {library_path}\n"
                    f"Archivos encontrados: {wizard.get_audio_files_count():,}\n\n"
                    f"¿Importar biblioteca ahora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # Importar automáticamente
                    self.rescan_library()
                else:
                    self.status_bar.showMessage(f"✅ Nueva biblioteca configurada: {library_path} (sin importar aún)")
            else:
                # Usuario eligió usar demo
                config.set_use_demo_database(True)

                QMessageBox.information(
                    self,
                    "Usando Base de Datos Demo",
                    "ℹ️ Configurado para usar la base de datos de demostración.\n\n"
                    "Puedes cambiar esto más tarde usando este mismo botón."
                )

                self.status_bar.showMessage("ℹ️ Usando base de datos demo")
        else:
            self.status_bar.showMessage("❌ Cambio de carpeta cancelado")

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            self.logger.info("Application closing...")

            # Check for active downloads
            if hasattr(self, 'download_queue') and self.download_queue.workers:
                reply = QMessageBox.question(
                    self,
                    "Downloads in Progress",
                    f"{len(self.download_queue.workers)} downloads are in progress.\n"
                    "Are you sure you want to quit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    self.logger.info("Close cancelled by user (downloads in progress)")
                    event.ignore()
                    return

            # Close all components
            if self.library_model:
                self.library_model.close()
                self.logger.info("Library model closed")

            log_shutdown()
            event.accept()

        except Exception as e:
            self.logger.exception("Error during close event")
            event.accept()


def main():
    """Main application entry point"""
    # Setup exception hook first
    setup_exception_hook()
    log_startup()

    logger = get_logger()
    logger.info("Starting application main()")

    print("=" * 80)
    print("🎵 NEXUS MUSIC MANAGER - COMPLETE EDITION")
    print("=" * 80)
    print(f"Project: AGENTE_MUSICA_MP3_001")
    print(f"Version: Complete (Phases 3+4+5+6)")
    print()
    print("✅ PHASE 3 - LIBRARY MANAGEMENT:")
    print("   - Browse 10,000+ songs with instant FTS5 search")
    print("   - Lazy loading and SQL-based sorting")
    print("   - Comprehensive library statistics")
    print()
    print("✅ PHASE 4 - SEARCH & DOWNLOAD:")
    print("   - YouTube + Spotify search integration")
    print("   - Concurrent download queue (3 simultaneous)")
    print("   - YouTube playlist downloader (one-click)")
    print("   - MusicBrainz metadata auto-complete")
    print()
    print("✅ PHASE 5 - MANAGEMENT TOOLS:")
    print("   - Duplicate detection (3 methods)")
    print("   - Auto-organize folders (Genre/Artist/Album)")
    print("   - Batch rename with templates")
    print()
    print("✅ PHASE 6 - PLAYER & LYRICS:")
    print("   - Built-in music player")
    print("   - Automatic lyrics fetching")
    print("   - Playlist management")
    print("=" * 80)

    # Create QApplication first (needed for dialogs)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Load configuration
    config = ConfigManager()
    logger.info(f"Configuration loaded. First run: {config.is_first_run()}")

    # Show setup wizard on first run
    if config.is_first_run():
        print("\n🎉 Welcome! Running first-time setup...")
        wizard = SetupWizard()
        result = wizard.exec()

        if result == QDialog.DialogCode.Accepted:
            # User completed setup
            library_path = wizard.get_library_path()

            if library_path:
                config.set_library_path(library_path)
                config.set_audio_files_count(wizard.get_audio_files_count())
                config.set_use_demo_database(False)
                print(f"✅ Library configured: {library_path}")
                print(f"   Found: {wizard.get_audio_files_count():,} audio files")
            else:
                # User chose to skip (use demo)
                config.set_use_demo_database(True)
                print("ℹ️  Using demo database")

            config.set_first_run_complete()
        else:
            # User cancelled setup
            print("⚠️  Setup cancelled. Exiting...")
            return

    # Get database path based on configuration
    db_path = Path(config.get_database_path())

    # Ensure demo database exists if using it
    if config.should_use_demo_database():
        if not db_path.exists():
            print(f"\n❌ Demo database not found: {db_path}")
            print(f"   Run migration first:")
            print(f"   cd phase2_database")
            print(f"   python migrate_excel_to_sqlite.py")
            return

        print(f"\n📂 Using Demo Database: {db_path}")
        print(f"   Size: {db_path.stat().st_size / (1024*1024):.2f} MB")
    else:
        print(f"\n📂 User Library Database: {db_path}")
        if db_path.exists():
            print(f"   Size: {db_path.stat().st_size / (1024*1024):.2f} MB")
        else:
            print(f"   (Will be created on first scan)")

    # Download directory
    download_dir = Path(config.get_download_directory())
    download_dir.mkdir(parents=True, exist_ok=True)
    print(f"📥 Download Directory: {download_dir}")

    print("\n🎯 READY TO LAUNCH!")
    print()
    print("📋 TABS AVAILABLE:")
    print("   1. 📚 Library          - Browse your complete music collection")
    print("   2. 🔍 Search & Download - Find songs on YouTube/Spotify")
    print("   3. 📺 YouTube Playlist  - Download entire playlists")
    print("   4. 📥 Download Queue    - Monitor download progress")
    print("   5. 🔍 Find Duplicates   - Detect duplicate songs")
    print("   6. 📁 Auto-Organize     - Organize library into folders")
    print("   7. 📝 Batch Rename      - Rename files with templates")
    print()
    print("💡 NOTES:")
    print("   - Phase 4 Search requires API keys (see phase4_search_download/API_KEYS_CONFIG.md)")
    print("   - All other features work without configuration")
    print("=" * 80)

    # Create main window
    window = NEXUSMusicManager(str(db_path), str(download_dir))
    window.show()

    print("\n✅ NEXUS Music Manager launched successfully!")
    print("   Enjoy your complete music management solution! 🎵\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
