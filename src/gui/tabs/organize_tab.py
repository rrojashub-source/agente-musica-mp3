"""
Organize Tab - Phase 5.2 GUI

Purpose: Auto-organize music library into structured folders
- Select organization template (artist/album/genre patterns)
- Choose base directory
- Preview changes before execution
- Safe execution with progress
- Rollback support on errors

Created: November 13, 2025
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QProgressBar, QGroupBox, QLineEdit,
    QFileDialog, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QIcon
import logging
import os

from src.core.library_organizer import LibraryOrganizer

logger = logging.getLogger(__name__)


class OrganizeWorker(QThread):
    """Background worker for library organization"""

    # Signals
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    finished = pyqtSignal(dict)  # Result dictionary
    error = pyqtSignal(str)  # Error message

    def __init__(self, organizer, base_path, template, songs, move=True, dry_run=False):
        super().__init__()
        self.organizer = organizer
        self.base_path = base_path
        self.template = template
        self.songs = songs
        self.move = move
        self.dry_run = dry_run

    def run(self):
        """Run organization in background"""
        try:
            self.progress.emit(10, "Initializing organization...")

            self.progress.emit(30, f"Organizing {len(self.songs)} files...")

            # Perform organization
            result = self.organizer.organize(
                base_path=self.base_path,
                template=self.template,
                songs=self.songs,
                move=self.move,
                dry_run=self.dry_run
            )

            self.progress.emit(90, "Processing results...")

            # Emit results
            self.finished.emit(result)

        except Exception as e:
            logger.error(f"Organization error: {e}")
            self.error.emit(str(e))


class OrganizeTab(QWidget):
    """
    Library Organization Tab

    Features:
    - Select from predefined templates or create custom
    - Choose base directory for organized library
    - Preview changes (dry-run mode)
    - Execute with move or copy option
    - Progress feedback
    - Rollback capability
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.organizer = LibraryOrganizer(self.db)
        self.organize_worker = None
        self.last_result = None

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # === SETTINGS GROUP ===
        settings_group = QGroupBox("Organization Settings")
        settings_layout = QVBoxLayout()

        # Template selection
        template_layout = QHBoxLayout()
        template_label = QLabel("Organization Template:")
        self.template_combo = QComboBox()
        self._populate_templates()
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        settings_layout.addLayout(template_layout)

        # Base path selection
        path_layout = QHBoxLayout()
        path_label = QLabel("Base Directory:")
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("/music/organized")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._on_browse_clicked)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        settings_layout.addLayout(path_layout)

        # Operation mode (move vs copy)
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Operation Mode:")
        self.mode_group = QButtonGroup(self)
        self.move_radio = QRadioButton("Move files")
        self.copy_radio = QRadioButton("Copy files (keep originals)")
        self.move_radio.setChecked(True)
        self.mode_group.addButton(self.move_radio)
        self.mode_group.addButton(self.copy_radio)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.move_radio)
        mode_layout.addWidget(self.copy_radio)
        mode_layout.addStretch()
        settings_layout.addLayout(mode_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # === PREVIEW BUTTON ===
        self.preview_button = QPushButton("Preview Changes")
        self.preview_button.clicked.connect(self._on_preview_clicked)
        layout.addWidget(self.preview_button)

        # === PROGRESS BAR ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # === STATUS LABEL ===
        self.status_label = QLabel("Ready to organize library")
        layout.addWidget(self.status_label)

        # === RESULTS TREE ===
        results_group = QGroupBox("Preview / Results")
        results_layout = QVBoxLayout()

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels([
            "Current Path",
            "→",
            "New Path"
        ])
        self.results_tree.setColumnWidth(0, 400)
        self.results_tree.setColumnWidth(1, 30)
        self.results_tree.setColumnWidth(2, 400)

        results_layout.addWidget(self.results_tree)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # === ACTION BUTTONS ===
        actions_layout = QHBoxLayout()

        self.execute_button = QPushButton("Organize Library")
        self.execute_button.clicked.connect(self._on_execute_clicked)
        self.execute_button.setEnabled(False)

        self.rollback_button = QPushButton("Rollback")
        self.rollback_button.clicked.connect(self._on_rollback_clicked)
        self.rollback_button.setEnabled(False)

        actions_layout.addStretch()
        actions_layout.addWidget(self.rollback_button)
        actions_layout.addWidget(self.execute_button)

        layout.addLayout(actions_layout)

        self.setLayout(layout)

    def _populate_templates(self):
        """Populate template combo box with common patterns"""
        templates = [
            ("Artist/Album/Track - Title", "{artist}/{album}/{track:02d} - {title}.mp3"),
            ("Artist/Album (Year)/Track - Title", "{artist}/{album} ({year})/{track:02d} - {title}.mp3"),
            ("Genre/Artist/Album/Title", "{genre}/{artist}/{album}/{title}.mp3"),
            ("Artist/Year - Album/Title", "{artist}/{year} - {album}/{title}.mp3"),
            ("Album/Track - Title", "{album}/{track:02d} - {title}.mp3"),
        ]

        for display_name, template_pattern in templates:
            self.template_combo.addItem(display_name, template_pattern)

    def _on_browse_clicked(self):
        """Handle browse button click"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Base Directory for Organized Library",
            self.path_input.text() or os.path.expanduser("~")
        )

        if directory:
            self.path_input.setText(directory)

    def _on_preview_clicked(self):
        """Handle preview button click"""
        # Validate settings
        if not self.path_input.text():
            QMessageBox.warning(
                self,
                "Missing Path",
                "Please select a base directory first."
            )
            return

        # Get all songs
        songs = self.db.get_all_songs()

        if len(songs) == 0:
            QMessageBox.information(
                self,
                "Empty Library",
                "No songs in library to organize."
            )
            return

        logger.info(f"Previewing organization for {len(songs)} songs")

        # Disable buttons during preview
        self.preview_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generating preview...")

        # Get settings
        base_path = self.path_input.text()
        template = self.template_combo.currentData()
        move = self.move_radio.isChecked()

        # Create worker thread (dry_run=True for preview)
        self.organize_worker = OrganizeWorker(
            self.organizer,
            base_path,
            template,
            songs,
            move=move,
            dry_run=True
        )
        self.organize_worker.progress.connect(self._on_progress)
        self.organize_worker.finished.connect(self._on_preview_finished)
        self.organize_worker.error.connect(self._on_error)
        self.organize_worker.start()

    def _on_execute_clicked(self):
        """Handle execute button click"""
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Organization",
            f"Organize library with current settings?\n\n"
            f"Template: {self.template_combo.currentText()}\n"
            f"Base Path: {self.path_input.text()}\n"
            f"Mode: {'Move' if self.move_radio.isChecked() else 'Copy'}\n\n"
            f"This will {'move' if self.move_radio.isChecked() else 'copy'} files to new locations.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Get all songs
        songs = self.db.get_all_songs()

        logger.info(f"Organizing {len(songs)} songs")

        # Disable buttons during execution
        self.execute_button.setEnabled(False)
        self.preview_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Organizing library...")

        # Get settings
        base_path = self.path_input.text()
        template = self.template_combo.currentData()
        move = self.move_radio.isChecked()

        # Create worker thread (dry_run=False for actual execution)
        self.organize_worker = OrganizeWorker(
            self.organizer,
            base_path,
            template,
            songs,
            move=move,
            dry_run=False
        )
        self.organize_worker.progress.connect(self._on_progress)
        self.organize_worker.finished.connect(self._on_execute_finished)
        self.organize_worker.error.connect(self._on_error)
        self.organize_worker.start()

    def _on_rollback_clicked(self):
        """Handle rollback button click"""
        reply = QMessageBox.question(
            self,
            "Confirm Rollback",
            "Rollback last organization?\n\n"
            "Files will be moved back to their original locations.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.organizer.rollback()
            self._show_results(result)
            self.rollback_button.setEnabled(False)

    def _on_progress(self, percentage, message):
        """Handle progress updates"""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)

    def _on_preview_finished(self, result):
        """Handle preview completion"""
        self.last_result = result

        # Hide progress
        self.progress_bar.setVisible(False)
        self.preview_button.setEnabled(True)

        # Update status
        total_songs = result['success']
        self.status_label.setText(
            f"Preview: {total_songs} files will be organized"
        )

        # Populate preview tree
        self._populate_preview(result['preview'])

        # Enable execute button if preview successful
        if result['success'] > 0:
            self.execute_button.setEnabled(True)

        logger.info(f"Preview complete: {result['success']} files")

    def _on_execute_finished(self, result):
        """Handle execution completion"""
        self.last_result = result

        # Hide progress
        self.progress_bar.setVisible(False)
        self.preview_button.setEnabled(True)

        # Show results
        self._show_results(result)

        # Enable rollback button
        if result['success'] > 0:
            self.rollback_button.setEnabled(True)

        logger.info(f"Organization complete: {result['success']} success, {result['failed']} failed")

    def _on_error(self, error_message):
        """Handle organization error"""
        self.progress_bar.setVisible(False)
        self.preview_button.setEnabled(True)
        self.execute_button.setEnabled(False)
        self.status_label.setText(f"Error: {error_message}")

        QMessageBox.critical(
            self,
            "Organization Error",
            f"Failed to organize library:\n\n{error_message}"
        )

    def _populate_preview(self, preview_list):
        """Populate results tree with preview data"""
        self.results_tree.clear()

        for item in preview_list[:100]:  # Limit to first 100 for performance
            old_path = item['old']
            new_path = item['new']

            tree_item = QTreeWidgetItem([
                old_path,
                "→",
                new_path
            ])

            self.results_tree.addTopLevelItem(tree_item)

        if len(preview_list) > 100:
            info_item = QTreeWidgetItem([
                f"... and {len(preview_list) - 100} more files",
                "",
                ""
            ])
            self.results_tree.addTopLevelItem(info_item)

    def _show_results(self, result):
        """Show results summary"""
        success = result['success']
        failed = result['failed']
        errors = result.get('errors', [])

        # Update status
        self.status_label.setText(
            f"Organized: {success} success, {failed} failed"
        )

        # Show message box
        if failed == 0:
            QMessageBox.information(
                self,
                "Organization Complete",
                f"Successfully organized {success} files."
            )
        else:
            error_text = "\n".join(errors[:5])
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more errors"

            QMessageBox.warning(
                self,
                "Organization Partially Complete",
                f"Organized {success} files.\n"
                f"Failed to organize {failed} files.\n\n"
                f"Errors:\n{error_text}"
            )
