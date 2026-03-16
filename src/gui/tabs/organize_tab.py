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

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.library_organizer import LibraryOrganizer
from gui.base import BaseTab
from gui.base.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class OrganizeWorker(BaseWorker):
    """Background worker for library organization"""

    def __init__(
        self,
        organizer: LibraryOrganizer,
        base_path: str,
        template: str,
        songs: List[Dict[str, Any]],
        move: bool = True,
        dry_run: bool = False,
    ) -> None:
        super().__init__()
        self.organizer: LibraryOrganizer = organizer
        self.base_path: str = base_path
        self.template: str = template
        self.songs: List[Dict[str, Any]] = songs
        self.move: bool = move
        self.dry_run: bool = dry_run

    def do_work(self) -> Any:
        """Run organization in background"""
        self.report_progress(10, "Initializing organization...")

        self.report_progress(30, f"Organizing {len(self.songs)} files...")

        # Perform organization
        result = self.organizer.organize(
            base_path=self.base_path, template=self.template, songs=self.songs, move=self.move, dry_run=self.dry_run
        )

        self.report_progress(90, "Processing results...")

        return result


class OrganizeTab(BaseTab):
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

    def __init__(self, db_manager: Any, parent: Optional[QWidget] = None) -> None:
        self.organizer: LibraryOrganizer = LibraryOrganizer(db_manager)
        self.organize_worker: Optional[OrganizeWorker] = None
        self.last_result: Optional[Dict[str, Any]] = None
        super().__init__(db_manager=db_manager, parent=parent)

    def _init_ui(self) -> None:
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

        # === PROGRESS + STATUS ===
        self.add_progress_section(layout)
        self.status_label.setText("Ready to organize library")

        # === RESULTS TREE ===
        results_group = QGroupBox("Preview / Results")
        results_layout = QVBoxLayout()

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Current Path", "→", "New Path"])
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

    def _populate_templates(self) -> None:
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

    def _on_browse_clicked(self) -> None:
        """Handle browse button click"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Base Directory for Organized Library", self.path_input.text() or os.path.expanduser("~")
        )

        if directory:
            self.path_input.setText(directory)

    def _on_preview_clicked(self) -> None:
        """Handle preview button click"""
        if not self.path_input.text():
            self.show_warning("Please select a base directory first.", "Missing Path")
            return

        songs = self.db.get_all_songs()

        if len(songs) == 0:
            QMessageBox.information(self, "Empty Library", "No songs in library to organize.")
            return

        logger.info(f"Previewing organization for {len(songs)} songs")

        base_path = self.path_input.text()
        template = self.template_combo.currentData()
        move = self.move_radio.isChecked()

        self.organize_worker = OrganizeWorker(self.organizer, base_path, template, songs, move=move, dry_run=True)
        self.connect_worker(
            self.organize_worker,
            on_finished=self._on_preview_finished,
            on_error=self._on_worker_error,
            action_button=self.preview_button,
        )
        self.organize_worker.start()

    def _on_execute_clicked(self) -> None:
        """Handle execute button click"""
        if not self.show_confirm(
            f"Organize library with current settings?\n\n"
            f"Template: {self.template_combo.currentText()}\n"
            f"Base Path: {self.path_input.text()}\n"
            f"Mode: {'Move' if self.move_radio.isChecked() else 'Copy'}\n\n"
            f"This will {'move' if self.move_radio.isChecked() else 'copy'} files to new locations.",
            "Confirm Organization",
        ):
            return

        songs = self.db.get_all_songs()
        logger.info(f"Organizing {len(songs)} songs")

        self.execute_button.setEnabled(False)

        base_path = self.path_input.text()
        template = self.template_combo.currentData()
        move = self.move_radio.isChecked()

        self.organize_worker = OrganizeWorker(self.organizer, base_path, template, songs, move=move, dry_run=False)
        self.connect_worker(
            self.organize_worker,
            on_finished=self._on_execute_finished,
            on_error=self._on_worker_error,
            action_button=self.preview_button,
        )
        self.organize_worker.start()

    def _on_rollback_clicked(self) -> None:
        """Handle rollback button click"""
        reply = QMessageBox.question(
            self,
            "Confirm Rollback",
            "Rollback last organization?\n\n" "Files will be moved back to their original locations.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.organizer.rollback()
            self._show_results(result)
            self.rollback_button.setEnabled(False)

    def _on_preview_finished(self, result: Dict[str, Any]) -> None:
        """Handle preview completion"""
        self.last_result = result

        total_songs = result["success"]
        self.status_label.setText(f"Preview: {total_songs} files will be organized")

        self._populate_preview(result["preview"])

        if result["success"] > 0:
            self.execute_button.setEnabled(True)

        logger.info(f"Preview complete: {result['success']} files")

    def _on_execute_finished(self, result: Dict[str, Any]) -> None:
        """Handle execution completion"""
        self.last_result = result
        self._show_results(result)
        self.data_changed.emit()

        if result["success"] > 0:
            self.rollback_button.setEnabled(True)

        logger.info(f"Organization complete: {result['success']} success, {result['failed']} failed")

    def _on_worker_error(self, error_message: str) -> None:
        """Handle worker error — ensure execute button is disabled"""
        self.execute_button.setEnabled(False)
        self.show_error(error_message)

    def _populate_preview(self, preview_list: List[Dict[str, str]]) -> None:
        """Populate results tree with preview data"""
        self.results_tree.clear()

        for item in preview_list[:100]:  # Limit to first 100 for performance
            old_path = item["old"]
            new_path = item["new"]

            tree_item = QTreeWidgetItem([old_path, "→", new_path])

            self.results_tree.addTopLevelItem(tree_item)

        if len(preview_list) > 100:
            info_item = QTreeWidgetItem([f"... and {len(preview_list) - 100} more files", "", ""])
            self.results_tree.addTopLevelItem(info_item)

    def _show_results(self, result: Dict[str, Any]) -> None:
        """Show results summary"""
        success = result["success"]
        failed = result["failed"]
        errors = result.get("errors", [])

        # Update status
        self.status_label.setText(f"Organized: {success} success, {failed} failed")

        # Show message box
        if failed == 0:
            QMessageBox.information(self, "Organization Complete", f"Successfully organized {success} files.")
        else:
            error_text = "\n".join(errors[:5])
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more errors"

            QMessageBox.warning(
                self,
                "Organization Partially Complete",
                f"Organized {success} files.\n" f"Failed to organize {failed} files.\n\n" f"Errors:\n{error_text}",
            )
