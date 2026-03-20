"""
Rename Tab - Phase 5.3 GUI

Purpose: Batch rename MP3 files based on metadata patterns
- Select rename template
- Find/replace operations
- Case conversion (UPPER, lower, Title Case)
- Number sequences
- Preview changes before applying
- Safe execution with progress feedback

Created: November 13, 2025
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.batch_renamer import BatchRenamer
from gui.base import BaseTab
from gui.base.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class RenameWorker(BaseWorker):
    """Background worker for batch renaming"""

    def __init__(
        self,
        renamer: BatchRenamer,
        songs: List[Dict[str, Any]],
        template: str,
        find: str = "",
        replace: str = "",
        case: str = "none",
        dry_run: bool = False,
    ) -> None:
        super().__init__()
        self.renamer: BatchRenamer = renamer
        self.songs: List[Dict[str, Any]] = songs
        self.template: str = template
        self.find: str = find
        self.replace: str = replace
        self.case: str = case
        self.dry_run: bool = dry_run

    def do_work(self) -> Any:
        """Run renaming in background"""
        self.report_progress(10, "Initializing rename...")

        self.report_progress(30, f"Renaming {len(self.songs)} files...")

        # Perform rename
        result = self.renamer.rename_batch(
            songs=self.songs,
            template=self.template,
            find=self.find,
            replace=self.replace,
            case=self.case,
            dry_run=self.dry_run,
        )

        self.report_progress(90, "Processing results...")

        return result


class RenameTab(BaseTab):
    """
    Batch Rename Tab

    Features:
    - Select from predefined templates or create custom
    - Find/replace operations
    - Case conversion (UPPER, lower, Title Case)
    - Preview changes (dry-run mode)
    - Execute with progress feedback
    """

    def __init__(self, db_manager: Any, parent: Optional[QWidget] = None) -> None:
        self.renamer: BatchRenamer = BatchRenamer(db_manager)
        self.rename_worker: Optional[RenameWorker] = None
        self.last_result: Optional[Dict[str, Any]] = None
        super().__init__(db_manager=db_manager, parent=parent)

    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout()

        # === SETTINGS GROUP ===
        settings_group = QGroupBox("Rename Settings")
        settings_layout = QVBoxLayout()

        # Template selection
        template_layout = QHBoxLayout()
        template_label = QLabel("Filename Template:")
        self.template_combo = QComboBox()
        self._populate_templates()
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        settings_layout.addLayout(template_layout)

        # Find/Replace
        find_replace_layout = QHBoxLayout()
        find_label = QLabel("Find:")
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Text to find...")
        replace_label = QLabel("Replace:")
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        find_replace_layout.addWidget(find_label)
        find_replace_layout.addWidget(self.find_input)
        find_replace_layout.addWidget(replace_label)
        find_replace_layout.addWidget(self.replace_input)
        settings_layout.addLayout(find_replace_layout)

        # Case conversion
        case_layout = QHBoxLayout()
        case_label = QLabel("Case Conversion:")
        self.case_combo = QComboBox()
        self.case_combo.addItem("No Change", "none")
        self.case_combo.addItem("UPPERCASE", "upper")
        self.case_combo.addItem("lowercase", "lower")
        self.case_combo.addItem("Title Case", "title")
        case_layout.addWidget(case_label)
        case_layout.addWidget(self.case_combo)
        case_layout.addStretch()
        settings_layout.addLayout(case_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # === PREVIEW BUTTON ===
        self.preview_button = QPushButton("Preview Changes")
        self.preview_button.clicked.connect(self._on_preview_clicked)
        layout.addWidget(self.preview_button)

        # === PROGRESS + STATUS ===
        self.add_progress_section(layout)
        self.status_label.setText("Ready to rename files")

        # === RESULTS TREE ===
        results_group = QGroupBox("Preview / Results")
        results_layout = QVBoxLayout()

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Current Filename", "→", "New Filename"])
        self.results_tree.setColumnWidth(0, 400)
        self.results_tree.setColumnWidth(1, 30)
        self.results_tree.setColumnWidth(2, 400)

        results_layout.addWidget(self.results_tree)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # === ACTION BUTTONS ===
        actions_layout = QHBoxLayout()

        self.apply_button = QPushButton("Apply Renames")
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.apply_button.setEnabled(False)

        actions_layout.addStretch()
        actions_layout.addWidget(self.apply_button)

        layout.addLayout(actions_layout)

        self.setLayout(layout)

    def _populate_templates(self) -> None:
        """Populate template combo box with common patterns"""
        templates = [
            ("Track - Title", "{track:02d} - {title}.mp3"),
            ("Track - Artist - Title", "{track:02d} - {artist} - {title}.mp3"),
            ("Artist - Album - Track - Title", "{artist} - {album} - {track:02d} - {title}.mp3"),
            ("Sequence - Title", "{seq:03d} - {title}.mp3"),
            ("Artist - Title", "{artist} - {title}.mp3"),
        ]

        for display_name, template_pattern in templates:
            self.template_combo.addItem(display_name, template_pattern)

    def _on_preview_clicked(self) -> None:
        """Handle preview button click"""
        songs = self.db.get_all_songs()

        if len(songs) == 0:
            QMessageBox.information(self, "Empty Library", "No songs in library to rename.")
            return

        logger.info(f"Previewing rename for {len(songs)} songs")

        template = self.template_combo.currentData()
        find = self.find_input.text()
        replace = self.replace_input.text()
        case = self.case_combo.currentData()

        self.rename_worker = RenameWorker(
            self.renamer, songs, template, find=find, replace=replace, case=case, dry_run=True
        )
        self.connect_worker(
            self.rename_worker,
            on_finished=self._on_preview_finished,
            on_error=self._on_worker_error,
            action_button=self.preview_button,
        )
        self.rename_worker.start()

    def _on_apply_clicked(self) -> None:
        """Handle apply button click"""
        if not self.show_confirm(
            f"Apply rename to all files?\n\n"
            f"Template: {self.template_combo.currentText()}\n"
            f"This will rename files permanently.",
            "Confirm Rename",
        ):
            return

        songs = self.db.get_all_songs()
        logger.info(f"Renaming {len(songs)} songs")

        self.apply_button.setEnabled(False)

        template = self.template_combo.currentData()
        find = self.find_input.text()
        replace = self.replace_input.text()
        case = self.case_combo.currentData()

        self.rename_worker = RenameWorker(
            self.renamer, songs, template, find=find, replace=replace, case=case, dry_run=False
        )
        self.connect_worker(
            self.rename_worker,
            on_finished=self._on_apply_finished,
            on_error=self._on_worker_error,
            action_button=self.preview_button,
        )
        self.rename_worker.start()

    def _on_preview_finished(self, result: Dict[str, Any]) -> None:
        """Handle preview completion"""
        self.last_result = result

        total_songs = result["success"]
        self.status_label.setText(f"Preview: {total_songs} files will be renamed")

        self._populate_preview(result["preview"])

        if result["success"] > 0:
            self.apply_button.setEnabled(True)

        logger.info(f"Preview complete: {result['success']} files")

    def _on_apply_finished(self, result: Dict[str, Any]) -> None:
        """Handle execution completion"""
        self.last_result = result
        self._show_results(result)
        logger.info(f"Rename complete: {result['success']} success, {result['failed']} failed")

    def _on_worker_error(self, error_message: str) -> None:
        """Handle worker error — ensure apply button is disabled"""
        self.apply_button.setEnabled(False)
        self.show_error(error_message)

    def _populate_preview(self, preview_list: List[Dict[str, str]]) -> None:
        """Populate results tree with preview data"""
        self.results_tree.clear()

        for item in preview_list[:100]:  # Limit to first 100 for performance
            old_path = item["old"]
            new_path = item["new"]

            # Get just filenames
            old_filename = os.path.basename(old_path)
            new_filename = os.path.basename(new_path)

            tree_item = QTreeWidgetItem([old_filename, "→", new_filename])

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
        self.status_label.setText(f"Renamed: {success} success, {failed} failed")

        # Show message box
        if failed == 0:
            QMessageBox.information(self, "Rename Complete", f"Successfully renamed {success} files.")
        else:
            error_text = "\n".join(errors[:5])
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more errors"

            QMessageBox.warning(
                self,
                "Rename Partially Complete",
                f"Renamed {success} files.\nFailed to rename {failed} files.\n\nErrors:\n{error_text}",
            )
