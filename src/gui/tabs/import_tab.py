"""
Import Tab - Library Import GUI
Phase: Library Import Feature

Purpose: Import MP3 library into database with GUI
- Browse for folder
- Recursive scan option
- Real-time progress
- Results summary

Created: November 13, 2025
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QProgressBar,
    QTextEdit, QCheckBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
import logging
from pathlib import Path

from workers.library_import_worker import LibraryImportWorker

logger = logging.getLogger(__name__)


class ImportTab(QWidget):
    """
    Import Tab for MP3 Library

    Features:
    - Browse for folder (QFileDialog)
    - Recursive scan checkbox
    - Import button
    - Progress bar (0-100%)
    - Status messages
    - Results summary
    """

    def __init__(self, db_manager, parent=None):
        """
        Initialize Import Tab

        Args:
            db_manager: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.import_worker = None

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Header
        header_label = QLabel("📥 Import Music Library")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header_label)

        # Info label
        info_label = QLabel(
            "Import MP3 files from a folder into your library.\n"
            "The importer will read ID3 tags and audio metadata automatically."
        )
        info_label.setStyleSheet("margin-bottom: 10px;")
        info_label.setProperty("class", "secondary")  # Use theme color
        layout.addWidget(info_label)

        # === FOLDER SELECTION ===
        folder_group = QGroupBox("Select Folder")
        folder_layout = QVBoxLayout()

        path_layout = QHBoxLayout()
        path_label = QLabel("Folder Path:")
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("C:\\Users\\ricar\\Music")

        # Set default path
        default_music = Path.home() / "Music"
        if default_music.exists():
            self.path_input.setText(str(default_music))

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._on_browse_clicked)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input, stretch=1)
        path_layout.addWidget(self.browse_button)

        folder_layout.addLayout(path_layout)

        # Recursive checkbox
        self.recursive_checkbox = QCheckBox("Scan subfolders recursively")
        self.recursive_checkbox.setChecked(True)
        folder_layout.addWidget(self.recursive_checkbox)

        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # === IMPORT BUTTON ===
        self.import_button = QPushButton("🚀 Import Library")
        self.import_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.import_button.clicked.connect(self._on_import_clicked)
        layout.addWidget(self.import_button)

        # === PROGRESS ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to import")
        self.status_label.setProperty("class", "secondary")  # Use theme color
        layout.addWidget(self.status_label)

        # === RESULTS ===
        results_group = QGroupBox("Import Log")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Add stretch to push everything up
        layout.addStretch()

        self.setLayout(layout)

    def _on_browse_clicked(self):
        """Handle browse button click"""
        current_path = self.path_input.text()
        if not current_path:
            current_path = str(Path.home() / "Music")

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Music Folder to Import",
            current_path
        )

        if directory:
            self.path_input.setText(directory)
            logger.info(f"Selected folder: {directory}")

    def _on_import_clicked(self):
        """Handle import button click"""
        # Validate path
        folder_path = self.path_input.text().strip()
        if not folder_path:
            QMessageBox.warning(
                self,
                "No Folder Selected",
                "Please select a folder to import."
            )
            return

        if not Path(folder_path).exists():
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"The folder does not exist:\n{folder_path}"
            )
            return

        # Confirm import
        recursive = self.recursive_checkbox.isChecked()
        reply = QMessageBox.question(
            self,
            "Confirm Import",
            f"Import MP3 files from:\n{folder_path}\n\n"
            f"Recursive: {'Yes' if recursive else 'No'}\n\n"
            f"This may take a few minutes for large libraries.\n"
            f"Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Start import
        self._start_import(folder_path, recursive)

    def _start_import(self, folder_path: str, recursive: bool):
        """
        Start import worker

        Args:
            folder_path: Folder to scan
            recursive: Scan recursively
        """
        # Disable controls
        self.import_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.path_input.setEnabled(False)
        self.recursive_checkbox.setEnabled(False)

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting import...")

        # Clear results
        self.results_text.clear()
        self._log("🚀 Starting import...")
        self._log(f"📁 Folder: {folder_path}")
        self._log(f"🔄 Recursive: {'Yes' if recursive else 'No'}")
        self._log("")

        # Create worker
        self.import_worker = LibraryImportWorker(
            self.db_manager,
            folder_path,
            recursive=recursive
        )

        # Connect signals
        self.import_worker.progress.connect(self._on_progress)
        self.import_worker.song_imported.connect(self._on_song_imported)
        self.import_worker.finished.connect(self._on_import_finished)
        self.import_worker.error.connect(self._on_import_error)

        # Start worker
        self.import_worker.start()

        logger.info(f"Started import: {folder_path}")

    def _on_progress(self, percentage: int, message: str):
        """Handle progress update"""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)

    def _on_song_imported(self, song_data: dict):
        """Handle song imported signal"""
        title = song_data.get('title', 'Unknown')
        artist = song_data.get('artist', 'Unknown Artist')
        self._log(f"✅ {title} - {artist}")

    def _on_import_finished(self, result: dict):
        """Handle import completion"""
        success = result['success']
        failed = result['failed']
        skipped = result['skipped']
        errors = result.get('errors', [])

        # Hide progress
        self.progress_bar.setVisible(False)

        # Update status
        self.status_label.setText(
            f"Complete: {success} imported, {skipped} skipped, {failed} failed"
        )

        # Log summary
        self._log("")
        self._log("=" * 50)
        self._log("✅ IMPORT COMPLETE!")
        self._log(f"   Imported: {success} songs")
        self._log(f"   Skipped: {skipped} (duplicates)")
        self._log(f"   Failed: {failed}")

        if errors:
            self._log("")
            self._log("⚠️ Errors:")
            for error in errors[:5]:
                self._log(f"   - {error}")
            if len(errors) > 5:
                self._log(f"   ... and {len(errors) - 5} more errors")

        # Total in library
        total = self.db_manager.get_song_count()
        self._log("")
        self._log(f"📊 Total songs in library: {total}")

        # Re-enable controls
        self.import_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.path_input.setEnabled(True)
        self.recursive_checkbox.setEnabled(True)

        # Show completion dialog
        if failed == 0:
            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported {success} songs!\n\n"
                f"Skipped {skipped} duplicates.\n\n"
                f"Total songs in library: {total}"
            )
        else:
            QMessageBox.warning(
                self,
                "Import Completed with Errors",
                f"Imported {success} songs.\n"
                f"Skipped {skipped} duplicates.\n"
                f"Failed to import {failed} files.\n\n"
                f"Check the log for details.\n\n"
                f"Total songs in library: {total}"
            )

        logger.info(f"Import finished: {success} success, {failed} failed, {skipped} skipped")

    def _on_import_error(self, error_message: str):
        """Handle fatal import error"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Error: {error_message}")

        self._log("")
        self._log(f"❌ FATAL ERROR: {error_message}")

        # Re-enable controls
        self.import_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.path_input.setEnabled(True)
        self.recursive_checkbox.setEnabled(True)

        QMessageBox.critical(
            self,
            "Import Error",
            f"Failed to import library:\n\n{error_message}"
        )

        logger.error(f"Import error: {error_message}")

    def _log(self, message: str):
        """
        Append message to results text

        Args:
            message: Message to log
        """
        self.results_text.append(message)
        # Auto-scroll to bottom
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)
