"""
Content Filter Tab - AI Content Classification GUI
Part of NEXUS Music Manager Phase 8

Features:
- Scan library or folder for content classification
- View results in sortable table
- Bulk actions: move, copy, tag, delete
- Export filtered selection
- Safe Zone profiles

Created: December 8, 2025
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QProgressBar, QComboBox, QFileDialog, QMessageBox,
    QHeaderView, QCheckBox, QSpinBox, QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QAction
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional
import shutil

from services.content_filter import (
    ContentClassifier, ContentRating, ClassificationResult, get_classifier
)
from translations import tr

logger = logging.getLogger(__name__)


# Rating colors
RATING_COLORS = {
    ContentRating.EXPLICIT: QColor("#e74c3c"),      # Red
    ContentRating.SUGGESTIVE: QColor("#f39c12"),    # Orange
    ContentRating.CLEAN: QColor("#27ae60"),         # Green
    ContentRating.CHILDREN: QColor("#3498db"),      # Blue
    ContentRating.CHRISTIAN: QColor("#9b59b6"),     # Purple
    ContentRating.UNKNOWN: QColor("#95a5a6"),       # Gray
}

RATING_LABELS = {
    ContentRating.EXPLICIT: "Explicit",
    ContentRating.SUGGESTIVE: "Suggestive",
    ContentRating.CLEAN: "Clean",
    ContentRating.CHILDREN: "Children",
    ContentRating.CHRISTIAN: "Christian",
    ContentRating.UNKNOWN: "Unknown",
}


class ClassificationWorker(QThread):
    """Background worker for classification"""
    progress = pyqtSignal(int, int, object)  # current, total, result
    finished = pyqtSignal(list)  # all results
    error = pyqtSignal(str)

    def __init__(self, file_paths: List[str], use_lyrics: bool = False,
                 use_audio: bool = False):
        super().__init__()
        self.file_paths = file_paths
        self.use_lyrics = use_lyrics
        self.use_audio = use_audio
        self._cancelled = False

    def run(self):
        try:
            classifier = get_classifier()
            results = []

            for i, path in enumerate(self.file_paths):
                if self._cancelled:
                    break

                result = classifier.classify_file(
                    path,
                    use_lyrics=self.use_lyrics,
                    use_audio=self.use_audio
                )
                results.append(result)
                self.progress.emit(i + 1, len(self.file_paths), result)

            self.finished.emit(results)
        except Exception as e:  # GUI error boundary - must not crash
            self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True


class ContentFilterTab(QWidget):
    """
    Content Filter Tab

    Features:
    - Scan folder or library
    - View classification results
    - Filter by rating
    - Bulk actions
    - Safe Zones (Kids Mode, Family Mode)
    - USB Export with organization
    - Dashboard statistics
    """

    # Safe Zone profiles
    SAFE_ZONES = {
        "kids": {
            "name": "Kids Mode",
            "icon": "👶",
            "allowed": [ContentRating.CHILDREN],
            "description": "Solo música infantil"
        },
        "family": {
            "name": "Family Mode",
            "icon": "👨‍👩‍👧‍👦",
            "allowed": [ContentRating.CHILDREN, ContentRating.CLEAN, ContentRating.CHRISTIAN],
            "description": "Música familiar (sin contenido explícito)"
        },
        "clean": {
            "name": "Clean Mode",
            "icon": "✨",
            "allowed": [ContentRating.CLEAN, ContentRating.CHRISTIAN],
            "description": "Música limpia para adultos"
        },
    }

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._results: List[ClassificationResult] = []
        self._worker: Optional[ClassificationWorker] = None
        self._init_ui()

    def _init_ui(self):
        """Initialize user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Header
        header = QLabel(tr("content_filter_title"))
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(header)

        description = QLabel(tr("content_filter_description"))
        description.setStyleSheet("color: #888; font-size: 11px;")
        description.setWordWrap(True)
        main_layout.addWidget(description)

        # === SCAN SECTION ===
        scan_group = QGroupBox(tr("content_filter_scan"))
        scan_layout = QVBoxLayout(scan_group)

        # Scan options row
        options_row = QHBoxLayout()

        options_row.addWidget(QLabel(tr("content_filter_source")))
        self.source_combo = QComboBox()
        self.source_combo.addItems([
            tr("content_filter_source_folder"),
            tr("content_filter_source_library"),
        ])
        self.source_combo.setFixedWidth(150)
        options_row.addWidget(self.source_combo)

        options_row.addSpacing(20)

        self.lyrics_check = QCheckBox(tr("content_filter_use_lyrics"))
        self.lyrics_check.setToolTip(tr("content_filter_lyrics_tooltip"))
        options_row.addWidget(self.lyrics_check)

        self.audio_check = QCheckBox(tr("content_filter_use_audio"))
        self.audio_check.setToolTip(tr("content_filter_audio_tooltip"))
        options_row.addWidget(self.audio_check)

        options_row.addStretch()
        scan_layout.addLayout(options_row)

        # Scan button row
        btn_row = QHBoxLayout()
        self.scan_btn = QPushButton(tr("content_filter_scan_btn"))
        self.scan_btn.setFixedHeight(35)
        self.scan_btn.setStyleSheet("background: #3498db; color: white; font-weight: bold;")
        self.scan_btn.clicked.connect(self._start_scan)
        btn_row.addWidget(self.scan_btn)

        self.cancel_btn = QPushButton(tr("content_filter_cancel"))
        self.cancel_btn.setFixedHeight(35)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_scan)
        btn_row.addWidget(self.cancel_btn)

        btn_row.addStretch()
        scan_layout.addLayout(btn_row)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        scan_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        scan_layout.addWidget(self.status_label)

        main_layout.addWidget(scan_group)

        # === SAFE ZONES SECTION (moved to top for visibility) ===
        zones_group = QGroupBox(tr("content_filter_safe_zones"))
        zones_layout = QHBoxLayout(zones_group)

        # Kids Mode
        kids_btn = QPushButton(tr("content_filter_kids_mode"))
        kids_btn.setToolTip(tr("content_filter_kids_mode_tooltip"))
        kids_btn.setStyleSheet("background: #3498db; color: white; padding: 8px 16px;")
        kids_btn.clicked.connect(lambda: self._export_safe_zone("kids"))
        zones_layout.addWidget(kids_btn)

        # Family Mode
        family_btn = QPushButton(tr("content_filter_family_mode"))
        family_btn.setToolTip(tr("content_filter_family_mode_tooltip"))
        family_btn.setStyleSheet("background: #27ae60; color: white; padding: 8px 16px;")
        family_btn.clicked.connect(lambda: self._export_safe_zone("family"))
        zones_layout.addWidget(family_btn)

        # Clean Mode
        clean_btn = QPushButton(tr("content_filter_clean_mode"))
        clean_btn.setToolTip(tr("content_filter_clean_mode_tooltip"))
        clean_btn.setStyleSheet("background: #9b59b6; color: white; padding: 8px 16px;")
        clean_btn.clicked.connect(lambda: self._export_safe_zone("clean"))
        zones_layout.addWidget(clean_btn)

        zones_layout.addStretch()

        # USB Export button
        usb_btn = QPushButton(tr("content_filter_export_usb"))
        usb_btn.setToolTip(tr("content_filter_export_usb_tooltip"))
        usb_btn.setStyleSheet("background: #e67e22; color: white; padding: 8px 16px;")
        usb_btn.clicked.connect(self._export_to_usb)
        zones_layout.addWidget(usb_btn)

        main_layout.addWidget(zones_group)

        # === ACTIONS SECTION (also at top) ===
        actions_group = QGroupBox(tr("content_filter_actions"))
        actions_layout = QHBoxLayout(actions_group)

        self.move_btn = QPushButton(tr("content_filter_move_to"))
        self.move_btn.clicked.connect(self._move_selected)
        actions_layout.addWidget(self.move_btn)

        self.copy_btn = QPushButton(tr("content_filter_copy_to"))
        self.copy_btn.clicked.connect(self._copy_selected)
        actions_layout.addWidget(self.copy_btn)

        self.delete_btn = QPushButton(tr("content_filter_delete"))
        self.delete_btn.setStyleSheet("background: #e74c3c; color: white;")
        self.delete_btn.clicked.connect(self._delete_selected)
        actions_layout.addWidget(self.delete_btn)

        actions_layout.addStretch()

        self.export_btn = QPushButton(tr("content_filter_export_safe"))
        self.export_btn.setStyleSheet("background: #27ae60; color: white;")
        self.export_btn.clicked.connect(self._export_safe)
        actions_layout.addWidget(self.export_btn)

        main_layout.addWidget(actions_group)

        # === RESULTS SECTION (now at bottom, can expand) ===
        results_group = QGroupBox(tr("content_filter_results"))
        results_layout = QVBoxLayout(results_group)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel(tr("content_filter_show")))

        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            tr("content_filter_all"),
            tr("content_filter_explicit_only"),
            tr("content_filter_clean_only"),
            tr("content_filter_children_only"),
            tr("content_filter_unknown_only"),
        ])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(self.filter_combo)

        filter_row.addStretch()

        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #666;")
        filter_row.addWidget(self.stats_label)

        results_layout.addLayout(filter_row)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            tr("content_filter_col_artist"),
            tr("content_filter_col_title"),
            tr("content_filter_col_rating"),
            tr("content_filter_col_confidence"),
            tr("content_filter_col_reasons"),
            tr("content_filter_col_path"),
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Column widths - all interactive (user can resize)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Artist
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Rating
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Confidence
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)      # Reasons (fills space)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Path

        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(5, 200)

        results_layout.addWidget(self.table)

        main_layout.addWidget(results_group)

    def _start_scan(self):
        """Start classification scan"""
        source = self.source_combo.currentIndex()

        if source == 0:  # Folder
            folder = QFileDialog.getExistingDirectory(
                self, tr("content_filter_select_folder")
            )
            if not folder:
                return
            file_paths = self._get_audio_files(folder)
        else:  # Library
            file_paths = self._scan_library()
            if not file_paths:
                return

        if not file_paths:
            QMessageBox.warning(
                self, tr("content_filter_no_files_title"),
                tr("content_filter_no_files_msg")
            )
            return

        # Start worker
        self._results = []
        self.table.setRowCount(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(file_paths))
        self.progress_bar.setValue(0)
        self.scan_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText(f"Scanning {len(file_paths)} files...")

        self._worker = ClassificationWorker(
            file_paths,
            use_lyrics=self.lyrics_check.isChecked(),
            use_audio=self.audio_check.isChecked()
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _cancel_scan(self):
        """Cancel ongoing scan"""
        if self._worker:
            self._worker.cancel()
            self.status_label.setText("Cancelling...")

    def _get_audio_files(self, folder: str) -> List[str]:
        """Get all audio files in folder"""
        extensions = {'.mp3', '.m4a', '.flac', '.wav', '.ogg', '.wma', '.aac'}
        files = []

        for path in Path(folder).rglob('*'):
            if path.suffix.lower() in extensions:
                files.append(str(path))

        return files

    def _on_progress(self, current: int, total: int, result: ClassificationResult):
        """Handle progress update"""
        self.progress_bar.setValue(current)
        self.status_label.setText(
            f"Scanning: {current}/{total} - {result.artist} - {result.title}"
        )
        self._results.append(result)
        self._add_result_to_table(result)

    def _on_finished(self, results: List[ClassificationResult]):
        """Handle scan completion"""
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self._update_stats()
        self.status_label.setText(f"Scan complete: {len(results)} files classified")

    def _on_error(self, error: str):
        """Handle error"""
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Error", error)

    def _add_result_to_table(self, result: ClassificationResult):
        """Add classification result to table"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Artist
        self.table.setItem(row, 0, QTableWidgetItem(result.artist))

        # Title
        self.table.setItem(row, 1, QTableWidgetItem(result.title))

        # Rating (with color)
        rating_item = QTableWidgetItem(RATING_LABELS.get(result.rating, "?"))
        rating_item.setBackground(RATING_COLORS.get(result.rating, QColor("#999")))
        rating_item.setForeground(QColor("white"))
        rating_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, rating_item)

        # Confidence
        confidence_item = QTableWidgetItem(f"{result.score.confidence:.0%}")
        confidence_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, confidence_item)

        # Reasons
        reasons = "; ".join(result.score.reasons[:3])  # First 3 reasons
        self.table.setItem(row, 4, QTableWidgetItem(reasons))

        # Path
        self.table.setItem(row, 5, QTableWidgetItem(result.file_path))

    def _apply_filter(self):
        """Apply rating filter to table"""
        filter_idx = self.filter_combo.currentIndex()

        for row in range(self.table.rowCount()):
            show = True

            if filter_idx > 0 and row < len(self._results):
                result = self._results[row]
                if filter_idx == 1:  # Explicit only
                    show = result.rating in [ContentRating.EXPLICIT, ContentRating.SUGGESTIVE]
                elif filter_idx == 2:  # Clean only
                    show = result.rating == ContentRating.CLEAN
                elif filter_idx == 3:  # Children only
                    show = result.rating == ContentRating.CHILDREN
                elif filter_idx == 4:  # Unknown only
                    show = result.rating == ContentRating.UNKNOWN

            self.table.setRowHidden(row, not show)

    def _update_stats(self):
        """Update statistics label"""
        if not self._results:
            self.stats_label.setText("")
            return

        counts = {}
        for result in self._results:
            rating = result.rating
            counts[rating] = counts.get(rating, 0) + 1

        parts = []
        for rating, count in sorted(counts.items(), key=lambda x: -x[1]):
            label = RATING_LABELS.get(rating, "?")
            parts.append(f"{label}: {count}")

        self.stats_label.setText(" | ".join(parts))

    def _show_context_menu(self, pos):
        """Show context menu for selected rows"""
        menu = QMenu(self)

        move_action = QAction(tr("content_filter_move_to"), self)
        move_action.triggered.connect(self._move_selected)
        menu.addAction(move_action)

        copy_action = QAction(tr("content_filter_copy_to"), self)
        copy_action.triggered.connect(self._copy_selected)
        menu.addAction(copy_action)

        menu.addSeparator()

        delete_action = QAction(tr("content_filter_delete"), self)
        delete_action.triggered.connect(self._delete_selected)
        menu.addAction(delete_action)

        menu.exec(self.table.mapToGlobal(pos))

    def _get_selected_results(self) -> List[ClassificationResult]:
        """Get selected classification results"""
        selected = []
        for index in self.table.selectedIndexes():
            if index.column() == 0:  # Only count once per row
                row = index.row()
                if row < len(self._results):
                    selected.append(self._results[row])
        return selected

    def _move_selected(self):
        """Move selected files to folder"""
        selected = self._get_selected_results()
        if not selected:
            return

        folder = QFileDialog.getExistingDirectory(
            self, tr("content_filter_select_dest")
        )
        if not folder:
            return

        moved = 0
        for result in selected:
            try:
                src = Path(result.file_path)
                dst = Path(folder) / src.name
                shutil.move(str(src), str(dst))
                moved += 1
            except OSError as e:
                logger.error(f"Move failed: {e}")

        QMessageBox.information(
            self, tr("content_filter_move_complete"),
            tr("content_filter_moved_count").format(count=moved)
        )

    def _copy_selected(self):
        """Copy selected files to folder"""
        selected = self._get_selected_results()
        if not selected:
            return

        folder = QFileDialog.getExistingDirectory(
            self, tr("content_filter_select_dest")
        )
        if not folder:
            return

        copied = 0
        for result in selected:
            try:
                src = Path(result.file_path)
                dst = Path(folder) / src.name
                shutil.copy2(str(src), str(dst))
                copied += 1
            except OSError as e:
                logger.error(f"Copy failed: {e}")

        QMessageBox.information(
            self, tr("content_filter_copy_complete"),
            tr("content_filter_copied_count").format(count=copied)
        )

    def _delete_selected(self):
        """Delete selected files"""
        selected = self._get_selected_results()
        if not selected:
            return

        reply = QMessageBox.question(
            self,
            tr("content_filter_confirm_delete"),
            tr("content_filter_delete_confirm_msg").format(count=len(selected)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted = 0
        for result in selected:
            try:
                Path(result.file_path).unlink()
                deleted += 1
            except OSError as e:
                logger.error(f"Delete failed: {e}")

        QMessageBox.information(
            self, tr("content_filter_delete_complete"),
            tr("content_filter_deleted_count").format(count=deleted)
        )

        # Refresh table
        self._start_scan()

    def _export_safe(self):
        """Export safe (clean + children) music to folder"""
        if not self._results:
            QMessageBox.warning(
                self, "Warning",
                tr("content_filter_scan_first")
            )
            return

        folder = QFileDialog.getExistingDirectory(
            self, tr("content_filter_select_export_dest")
        )
        if not folder:
            return

        # Filter safe content
        safe_ratings = [ContentRating.CLEAN, ContentRating.CHILDREN, ContentRating.CHRISTIAN]
        safe_results = [r for r in self._results if r.rating in safe_ratings]

        if not safe_results:
            QMessageBox.information(
                self, "Info",
                tr("content_filter_no_safe_content")
            )
            return

        copied = 0
        for result in safe_results:
            try:
                src = Path(result.file_path)
                dst = Path(folder) / src.name
                shutil.copy2(str(src), str(dst))
                copied += 1
            except OSError as e:
                logger.error(f"Export failed: {e}")

        QMessageBox.information(
            self, tr("content_filter_export_complete"),
            tr("content_filter_exported_count").format(count=copied, total=len(safe_results))
        )

    def _export_safe_zone(self, zone_id: str):
        """Export music matching a Safe Zone profile"""
        if not self._results:
            QMessageBox.warning(
                self, "Warning",
                tr("content_filter_scan_first")
            )
            return

        zone = self.SAFE_ZONES.get(zone_id)
        if not zone:
            return

        folder = QFileDialog.getExistingDirectory(
            self, f"Select destination for {zone['name']}"
        )
        if not folder:
            return

        # Filter by allowed ratings
        allowed = zone['allowed']
        matching = [r for r in self._results if r.rating in allowed]

        if not matching:
            QMessageBox.information(
                self, "Info",
                f"No songs match {zone['name']} criteria.\n"
                f"Allowed: {', '.join([RATING_LABELS[r] for r in allowed])}"
            )
            return

        # Create zone subfolder
        dest_folder = Path(folder) / zone['name'].replace(" ", "_")
        dest_folder.mkdir(exist_ok=True)

        copied = 0
        for result in matching:
            try:
                src = Path(result.file_path)
                dst = dest_folder / src.name
                if not dst.exists():
                    shutil.copy2(str(src), str(dst))
                    copied += 1
            except OSError as e:
                logger.error(f"Export failed: {e}")

        QMessageBox.information(
            self, f"{zone['icon']} {zone['name']} Export Complete",
            f"Exported {copied} songs to:\n{dest_folder}"
        )

    def _export_to_usb(self):
        """Export organized music to USB drive"""
        if not self._results:
            QMessageBox.warning(
                self, "Warning",
                tr("content_filter_scan_first")
            )
            return

        # Select USB drive
        usb_path = QFileDialog.getExistingDirectory(
            self, "Select USB Drive or Destination"
        )
        if not usb_path:
            return

        # Create organized folder structure
        base = Path(usb_path) / "NEXUS_Music"
        folders = {
            ContentRating.CHILDREN: base / "Infantil",
            ContentRating.CLEAN: base / "Clean",
            ContentRating.CHRISTIAN: base / "Christian",
            ContentRating.EXPLICIT: base / "Explicit",
            ContentRating.SUGGESTIVE: base / "Suggestive",
            ContentRating.UNKNOWN: base / "Other",
        }

        # Create all folders
        for folder in folders.values():
            folder.mkdir(parents=True, exist_ok=True)

        copied = 0
        skipped = 0
        for result in self._results:
            try:
                src = Path(result.file_path)
                dest_folder = folders.get(result.rating, folders[ContentRating.UNKNOWN])
                dst = dest_folder / src.name
                if not dst.exists():
                    shutil.copy2(str(src), str(dst))
                    copied += 1
                else:
                    skipped += 1
            except OSError as e:
                logger.error(f"USB export failed: {e}")

        # Create summary file
        summary_path = base / "NEXUS_Summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("NEXUS Music Manager - Content Classification Summary\n")
            f.write("=" * 50 + "\n\n")

            counts = {}
            for result in self._results:
                rating = result.rating
                counts[rating] = counts.get(rating, 0) + 1

            f.write("Classification Results:\n")
            for rating, count in sorted(counts.items(), key=lambda x: -x[1]):
                label = RATING_LABELS.get(rating, "?")
                f.write(f"  {label}: {count} songs\n")

            f.write(f"\nTotal: {len(self._results)} songs\n")
            f.write(f"Copied: {copied}\n")
            f.write(f"Skipped (already exists): {skipped}\n")

        QMessageBox.information(
            self, "USB Export Complete",
            f"Exported {copied} songs to USB.\n\n"
            f"Folder structure:\n"
            f"  {base}/Infantil - Children's music\n"
            f"  {base}/Clean - Clean music\n"
            f"  {base}/Christian - Christian music\n"
            f"  {base}/Explicit - Explicit content\n\n"
            f"Summary saved to: {summary_path}"
        )

    def _scan_library(self):
        """Scan songs from database library"""
        if not self.db_manager:
            QMessageBox.warning(
                self, "Warning",
                "Database not available. Use folder scan instead."
            )
            return []

        try:
            # Get all songs from database
            songs = self.db_manager.get_all_songs()
            file_paths = [s.get('file_path') for s in songs if s.get('file_path')]

            # Filter existing files
            existing = [p for p in file_paths if Path(p).exists()]
            return existing
        except sqlite3.Error as e:
            logger.error(f"Library scan failed: {e}")
            return []
