"""
Duplicates Tab - Phase 5.1 GUI

Purpose: Find and manage duplicate songs in library
- Scan using 3 detection methods (metadata, fingerprint, filesize)
- Display results in tree structure
- Select duplicates for deletion
- Safe deletion with confirmation

Created: November 13, 2025
Updated: November 20, 2025 (UX improvements: visual indicators, dark mode colors)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QSlider, QLabel, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QColor, QBrush, QFont
import logging
import os

from core.duplicate_detector import DuplicateDetector

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """Background worker for duplicate scanning"""

    # Signals
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    finished = pyqtSignal(list)  # List of duplicate groups
    error = pyqtSignal(str)  # Error message

    def __init__(self, detector, method):
        super().__init__()
        self.detector = detector
        self.method = method

    def run(self):
        """Run duplicate detection in background"""
        try:
            self.progress.emit(10, "Initializing scan...")

            self.progress.emit(30, f"Scanning library ({self.method})...")

            # Perform scan
            duplicates = self.detector.scan_library(method=self.method)

            self.progress.emit(90, "Processing results...")

            # Emit results
            self.finished.emit(duplicates)

        except Exception as e:
            logger.error(f"Scan error: {e}")
            self.error.emit(str(e))


class DuplicatesTab(QWidget):
    """
    Duplicates Detection Tab

    Features:
    - Select detection method (metadata, fingerprint, filesize)
    - Adjust similarity threshold
    - Scan library for duplicates
    - Display results in tree structure
    - Select duplicates for deletion
    - Safe deletion with confirmation
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.detector = DuplicateDetector(self.db)
        self.scan_worker = None
        self.duplicate_groups = []

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()

        # === CONTROLS GROUP ===
        controls_group = QGroupBox("Scan Settings")
        controls_layout = QVBoxLayout()

        # Method selection
        method_layout = QHBoxLayout()
        method_label = QLabel("Detection Method:")
        self.method_combo = QComboBox()
        self.method_combo.addItem("Metadata Comparison", "metadata")
        self.method_combo.addItem("Audio Fingerprint", "fingerprint")
        self.method_combo.addItem("File Size", "filesize")
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.method_combo)
        method_layout.addStretch()

        # Threshold slider
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Similarity Threshold:")
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(70)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(85)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(5)
        self.threshold_value_label = QLabel("85%")
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)

        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_value_label)

        # Scan button
        self.scan_button = QPushButton("Scan Library")
        self.scan_button.clicked.connect(self._on_scan_clicked)

        controls_layout.addLayout(method_layout)
        controls_layout.addLayout(threshold_layout)
        controls_layout.addWidget(self.scan_button)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # === PROGRESS BAR ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # === STATUS LABEL ===
        self.status_label = QLabel("Ready to scan")
        layout.addWidget(self.status_label)

        # === RESULTS TREE ===
        results_group = QGroupBox("Duplicate Groups")
        results_layout = QVBoxLayout()

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels([
            "Song / File",
            "Details",
            "Bitrate",
            "Size",
            "Path"
        ])
        self.results_tree.setColumnWidth(0, 300)
        self.results_tree.setColumnWidth(1, 200)

        results_layout.addWidget(self.results_tree)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # === ACTION BUTTONS ===
        actions_layout = QHBoxLayout()

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.delete_button.setEnabled(False)

        self.select_all_button = QPushButton("Select All Low Quality")
        self.select_all_button.clicked.connect(self._select_low_quality)
        self.select_all_button.setEnabled(False)

        actions_layout.addWidget(self.select_all_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.delete_button)

        layout.addLayout(actions_layout)

        self.setLayout(layout)

    def _on_threshold_changed(self, value):
        """Handle threshold slider change"""
        self.threshold_value_label.setText(f"{value}%")
        # Update detector threshold
        self.detector.similarity_threshold = value / 100.0

    def _on_scan_clicked(self):
        """Handle scan button click"""
        if self.scan_worker and self.scan_worker.isRunning():
            logger.warning("Scan already in progress")
            return

        # Get selected method
        method = self.method_combo.currentData()

        logger.info(f"Starting duplicate scan (method: {method})")

        # Disable scan button during scan
        self.scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Scanning...")

        # Create worker thread
        self.scan_worker = ScanWorker(self.detector, method)
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.start()

    def _on_scan_progress(self, percentage, message):
        """Handle scan progress updates"""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)

    def _on_scan_finished(self, duplicate_groups):
        """Handle scan completion"""
        self.duplicate_groups = duplicate_groups

        # Hide progress
        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)

        # Update status
        total_songs = sum(len(group['songs']) for group in duplicate_groups)
        self.status_label.setText(
            f"Found {len(duplicate_groups)} duplicate groups ({total_songs} files)"
        )

        # Populate results
        self._populate_results(duplicate_groups)

        # Enable action buttons if duplicates found
        if len(duplicate_groups) > 0:
            self.delete_button.setEnabled(True)
            self.select_all_button.setEnabled(True)

        logger.info(f"Scan complete: {len(duplicate_groups)} groups found")

    def _on_scan_error(self, error_message):
        """Handle scan error"""
        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_message}")

        QMessageBox.critical(
            self,
            "Scan Error",
            f"Failed to scan library:\n\n{error_message}"
        )

    def _populate_results(self, duplicate_groups):
        """Populate results tree with duplicate groups"""
        self.results_tree.clear()

        for group_idx, group in enumerate(duplicate_groups, 1):
            songs = group['songs']
            confidence = group.get('confidence', 0.0)
            method = group.get('method', 'unknown')

            # Create group item
            group_item = QTreeWidgetItem([
                f"Group {group_idx}: {songs[0].get('title', 'Unknown')} ({len(songs)} files)",
                f"Confidence: {confidence * 100:.1f}% ({method})",
                "",
                "",
                ""
            ])

            # CRITICAL: Make bold and expand by default
            font = group_item.font(0)
            font.setBold(True)
            group_item.setFont(0, font)
            group_item.setExpanded(True)

            # Add songs to group (with quality indicator)
            for idx, song in enumerate(songs):
                is_best_quality = (idx == 0)  # First song is highest quality
                song_item = self._create_song_item(song, is_best_quality)
                group_item.addChild(song_item)

            self.results_tree.addTopLevelItem(group_item)

    def _create_song_item(self, song, is_best_quality=False):
        """
        Create tree item for a song

        Args:
            song: Song dictionary
            is_best_quality: True if this is the highest quality song in group
        """
        title = song.get('title', 'Unknown')
        artist = song.get('artist', 'Unknown')
        bitrate = song.get('bitrate', 0)
        file_path = song.get('file_path', '')

        # Get file size
        size_mb = 0
        if os.path.exists(file_path):
            try:
                size_bytes = os.path.getsize(file_path)
                size_mb = size_bytes / (1024 * 1024)
            except:
                pass

        # CRITICAL: Add visual indicator for best quality
        quality_indicator = "⭐ [KEEP]" if is_best_quality else ""
        details_text = f"{quality_indicator} ID: {song.get('id', 0)}".strip()

        song_item = QTreeWidgetItem([
            f"{title} - {artist}",
            details_text,
            f"{bitrate} kbps" if bitrate > 0 else "Unknown",
            f"{size_mb:.1f} MB",
            file_path
        ])

        # Visual styling for best quality
        if is_best_quality:
            # Green color for best quality (works in both light/dark themes)
            font = song_item.font(0)
            font.setBold(True)
            song_item.setFont(0, font)
            song_item.setForeground(0, QBrush(QColor(34, 139, 34)))  # Forest green
            song_item.setForeground(1, QBrush(QColor(34, 139, 34)))

        # Make checkable (but NOT the best quality by default)
        song_item.setFlags(song_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        song_item.setCheckState(0, Qt.CheckState.Unchecked)

        # Store song data
        song_item.setData(0, Qt.ItemDataRole.UserRole, song)
        song_item.setData(0, Qt.ItemDataRole.UserRole + 1, is_best_quality)  # Store quality flag

        return song_item

    def _select_low_quality(self):
        """Auto-select all duplicates except highest quality"""
        selected_count = 0
        kept_count = 0

        for i in range(self.results_tree.topLevelItemCount()):
            group_item = self.results_tree.topLevelItem(i)

            # Skip first child (highest quality) and check others
            for j in range(group_item.childCount()):
                child = group_item.child(j)
                is_best = child.data(0, Qt.ItemDataRole.UserRole + 1)

                if is_best or j == 0:
                    # Keep highest quality (first in list)
                    child.setCheckState(0, Qt.CheckState.Unchecked)
                    # Visual: Remove any "delete" styling
                    child.setForeground(2, QBrush(QColor()))  # Reset
                    child.setForeground(3, QBrush(QColor()))  # Reset
                    kept_count += 1
                else:
                    # Select others for deletion
                    child.setCheckState(0, Qt.CheckState.Checked)
                    # Visual: Red color for selected low quality (works in dark mode)
                    child.setForeground(2, QBrush(QColor(220, 20, 60)))  # Crimson red
                    child.setForeground(3, QBrush(QColor(220, 20, 60)))
                    selected_count += 1

        # Update status label with clear feedback
        self.status_label.setText(
            f"✓ Selected {selected_count} LOW QUALITY songs for deletion "
            f"(Keeping {kept_count} BEST QUALITY)"
        )

        logger.info(f"Auto-selected {selected_count} low quality duplicates (keeping {kept_count} best)")

        # Show feedback message box
        QMessageBox.information(
            self,
            "Selection Complete",
            f"Selected {selected_count} LOW QUALITY songs for deletion.\n\n"
            f"Keeping {kept_count} BEST QUALITY songs (marked with ⭐ [KEEP]).\n\n"
            f"Review the selection and click 'Delete Selected' to proceed."
        )

    def _on_delete_clicked(self):
        """Handle delete button click"""
        # Collect checked items and count best quality songs
        selected_songs = []
        selected_best_quality = 0
        total_best_quality = 0

        for i in range(self.results_tree.topLevelItemCount()):
            group_item = self.results_tree.topLevelItem(i)

            for j in range(group_item.childCount()):
                child = group_item.child(j)
                is_best = child.data(0, Qt.ItemDataRole.UserRole + 1)

                if is_best:
                    total_best_quality += 1

                if child.checkState(0) == Qt.CheckState.Checked:
                    song_data = child.data(0, Qt.ItemDataRole.UserRole)
                    selected_songs.append(song_data)

                    if is_best:
                        selected_best_quality += 1

        if len(selected_songs) == 0:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select files to delete by checking the checkboxes.\n\n"
                "TIP: Click 'Select All Low Quality' to auto-select duplicates."
            )
            return

        # WARNING: If user selected best quality songs
        warning_msg = ""
        if selected_best_quality > 0:
            warning_msg = (
                f"\n\n⚠️ WARNING: You selected {selected_best_quality} BEST QUALITY songs!\n"
                f"These are marked with ⭐ [KEEP] and should NOT be deleted.\n"
                f"Are you sure you want to delete them?"
            )

        # Calculate kept songs
        kept_count = total_best_quality - selected_best_quality

        # Confirmation dialog with context
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete {len(selected_songs)} files?\n\n"
            f"Selected for deletion: {len(selected_songs)} songs\n"
            f"Keeping: {kept_count} BEST QUALITY songs{warning_msg}\n\n"
            f"⚠️ This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._delete_files(selected_songs)

    def _delete_files(self, songs):
        """Delete selected song files"""
        success_count = 0
        error_count = 0
        errors = []

        for song in songs:
            file_path = song.get('file_path', '')
            song_id = song.get('id')

            try:
                # Delete file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    success_count += 1

                # Remove from database
                if song_id:
                    self.db.delete_song(song_id)

            except Exception as e:
                error_count += 1
                errors.append(f"{file_path}: {str(e)}")
                logger.error(f"Failed to delete {file_path}: {e}")

        # Show result
        if error_count == 0:
            QMessageBox.information(
                self,
                "Deletion Complete",
                f"Successfully deleted {success_count} files."
            )
        else:
            QMessageBox.warning(
                self,
                "Deletion Partially Complete",
                f"Deleted {success_count} files.\n"
                f"Failed to delete {error_count} files.\n\n"
                f"Errors:\n" + "\n".join(errors[:5])
            )

        # Refresh results
        self._on_scan_clicked()
