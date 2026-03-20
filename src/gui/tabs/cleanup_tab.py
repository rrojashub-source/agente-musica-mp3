"""
Cleanup Tab - Metadata Cleanup Wizard

Purpose: GUI wizard for metadata cleanup workflow
- Step-by-step process (Analyze → Clean → Fetch → Preview → Apply)
- Visual progress tracking
- Preview changes before applying
- Batch operations with user control

Created: November 18, 2025
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.cleanup_workflow import CleanupApplier, CleanupWorkflowWorker
from core.metadata_cleaner import MetadataCleaner
from core.metadata_fetcher import MetadataFetcher
from database.manager import DatabaseManager
from gui.base import BaseTab
from gui.themes.style_constants import Styles
from utils.constants import CONFIDENCE_THRESHOLD_DEFAULT

logger = logging.getLogger(__name__)


class CleanupTab(BaseTab):
    """
    Metadata Cleanup Wizard Tab

    6-Step workflow:
    1. Scan Library → Detect corrupted metadata
    2. Clean Titles → Auto-normalize
    3. Fetch Metadata → Search MusicBrainz/Spotify
    4. Preview Changes → User review
    5. Apply Changes → Update files + database
    6. Organize (optional) → Clean library structure
    """

    def __init__(self, db_path: str, parent: Optional[QWidget] = None) -> None:
        self.db_path: str = db_path
        db: DatabaseManager = DatabaseManager(db_path)
        self.cleaner: MetadataCleaner = MetadataCleaner()
        self.fetcher: Optional[MetadataFetcher] = None  # Initialize when needed (requires API clients)
        self.applier: CleanupApplier = CleanupApplier(db)
        self.workflow_worker: Optional[CleanupWorkflowWorker] = None
        self.workflow_results: Optional[Dict[str, Any]] = None
        self.preview_changes: List[Dict[str, Any]] = []
        super().__init__(db_manager=db, parent=parent)

    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("🧹 Metadata Cleanup Wizard")
        header.setStyleSheet(Styles.HEADER_TITLE_PADDED)
        layout.addWidget(header)

        # Instructions
        instructions = QLabel(
            "This wizard will help you clean and correct corrupted metadata.\n"
            "Process: Scan → Clean → Fetch Correct Data → Preview → Apply"
        )
        instructions.setStyleSheet(Styles.TEXT_INSTRUCTIONS)
        layout.addWidget(instructions)

        # === STEP 1: SCAN SETTINGS ===
        scan_group = QGroupBox("Step 1: Scan Settings")
        scan_layout = QVBoxLayout()

        # Fetch metadata checkbox
        self.fetch_metadata_check = QCheckBox("Fetch correct metadata from MusicBrainz/Spotify")
        self.fetch_metadata_check.setChecked(True)
        self.fetch_metadata_check.setToolTip("Search external APIs for correct metadata (recommended)")
        scan_layout.addWidget(self.fetch_metadata_check)

        # Download cover art checkbox
        self.download_covers_check = QCheckBox("Download album cover art automatically")
        self.download_covers_check.setChecked(False)
        self.download_covers_check.setToolTip(
            "Download cover images from Cover Art Archive\nSaves to: downloads/covers/{artist}/{album}/cover.jpg"
        )
        scan_layout.addWidget(self.download_covers_check)

        # Confidence threshold
        confidence_layout = QHBoxLayout()
        confidence_label = QLabel("Min. Confidence:")
        self.confidence_spin = QSpinBox()
        self.confidence_spin.setRange(50, 100)
        self.confidence_spin.setValue(CONFIDENCE_THRESHOLD_DEFAULT)
        self.confidence_spin.setSuffix("%")
        self.confidence_spin.setToolTip("Minimum confidence to accept metadata matches (70% recommended)")
        confidence_layout.addWidget(confidence_label)
        confidence_layout.addWidget(self.confidence_spin)
        confidence_layout.addStretch()
        scan_layout.addLayout(confidence_layout)

        # Scan button
        self.scan_button = QPushButton("🔍 Scan Library")
        self.scan_button.clicked.connect(self._on_scan_clicked)
        scan_layout.addWidget(self.scan_button)

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        # === PROGRESS + STATUS ===
        self.add_progress_section(layout)
        self.status_label.setText("Ready to scan")

        # === STEP 2-4: PREVIEW RESULTS ===
        preview_group = QGroupBox("Step 2-4: Preview Changes")
        preview_layout = QVBoxLayout()

        # Preview tree
        self.preview_tree = QTreeWidget()
        self.preview_tree.setHeaderLabels(["Song", "Original", "→", "Proposed", "Confidence", "Source"])
        self.preview_tree.setColumnWidth(0, 200)
        self.preview_tree.setColumnWidth(1, 250)
        self.preview_tree.setColumnWidth(2, 30)
        self.preview_tree.setColumnWidth(3, 250)
        self.preview_tree.setColumnWidth(4, 80)
        self.preview_tree.setColumnWidth(5, 100)

        preview_layout.addWidget(self.preview_tree)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # === STEP 5: ACTION BUTTONS ===
        actions_layout = QHBoxLayout()

        # Select all button
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self._on_select_all)
        self.select_all_button.setEnabled(False)

        # Deselect all button
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self._on_deselect_all)
        self.deselect_all_button.setEnabled(False)

        # Apply button
        self.apply_button = QPushButton("✅ Apply Selected Changes")
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.apply_button.setEnabled(False)

        actions_layout.addWidget(self.select_all_button)
        actions_layout.addWidget(self.deselect_all_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.apply_button)

        layout.addLayout(actions_layout)

        self.setLayout(layout)

    def _on_scan_clicked(self) -> None:
        """Handle scan button click - Start workflow"""
        # Get all songs from database
        songs = self.db.get_all_songs()

        if not songs:
            QMessageBox.information(self, "Empty Library", "No songs in library to scan.")
            return

        logger.info(f"Starting cleanup workflow for {len(songs)} songs")

        # Disable controls
        self.scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting scan...")

        # Initialize fetcher if needed
        if self.fetch_metadata_check.isChecked():
            try:
                # Import API clients and adapters
                from api.musicbrainz_client import MusicBrainzClient
                from api.spotify_search import SpotifySearcher
                from core.api_adapters import MusicBrainzAdapter, SpotifyAdapter

                # Initialize MusicBrainz client
                mb_client = MusicBrainzClient(
                    app_name="NEXUS Music Manager", app_version="2.0", contact="support@nexusmusic.com"
                )
                mb_adapter = MusicBrainzAdapter(mb_client)

                # Initialize Spotify client
                try:
                    from utils.credentials import load_credential

                    spotify_id = load_credential("spotify_client_id")
                    spotify_secret = load_credential("spotify_client_secret")

                    if spotify_id and spotify_secret:
                        spotify_searcher = SpotifySearcher(spotify_id, spotify_secret)
                        spotify_adapter = SpotifyAdapter(spotify_searcher)
                    else:
                        logger.warning("Spotify credentials not found")
                        spotify_adapter = None
                except Exception as e:  # GUI error boundary
                    logger.warning(f"Failed to initialize Spotify: {e}")
                    spotify_adapter = None

                # Create MetadataFetcher with adapters
                self.fetcher = MetadataFetcher(mb_adapter, spotify_adapter)
                logger.info("Metadata fetcher initialized with API adapters")

            except Exception as e:  # API client init - diverse import/auth/network errors
                logger.warning(f"Failed to initialize API clients: {e}")
                self.fetcher = None

        # Create workflow worker
        self.workflow_worker = CleanupWorkflowWorker(
            db_manager=self.db,
            cleaner=self.cleaner,
            fetcher=self.fetcher,
            songs_to_clean=songs,
            fetch_metadata=self.fetch_metadata_check.isChecked(),
            min_confidence=self.confidence_spin.value(),
            download_covers=self.download_covers_check.isChecked(),
        )

        # Connect worker signals (connect_worker handles progress/finished/error)
        self.connect_worker(
            self.workflow_worker, on_finished=self._on_workflow_finished, action_button=self.scan_button
        )
        self.workflow_worker.step_completed.connect(self._on_step_completed)
        self.workflow_worker.start()

    def _on_step_completed(self, step_number: int, results: Any) -> None:
        """Handle step completion"""
        logger.info(f"Step {step_number} completed: {results}")

    def _on_workflow_finished(self, results: Dict[str, Any]) -> None:
        """Handle workflow completion - Show preview"""
        self.workflow_results = results
        self.preview_changes = results.get("preview", [])

        analysis = results.get("analysis", {})
        cleaned_count = len(results.get("cleaned", []))
        fetched_count = len(results.get("fetched", []))

        self.status_label.setText(f"Scan complete: {cleaned_count} songs cleaned, {fetched_count} fetched from APIs")

        # Populate preview tree
        self._populate_preview(self.preview_changes)

        # Enable action buttons
        if self.preview_changes:
            self.select_all_button.setEnabled(True)
            self.deselect_all_button.setEnabled(True)
            self.apply_button.setEnabled(True)

        # Show summary dialog
        self._show_scan_summary(analysis, cleaned_count, fetched_count)

        logger.info(f"Workflow complete: {len(self.preview_changes)} changes to preview")

    def _populate_preview(self, preview_changes: List[Dict[str, Any]]) -> None:
        """Populate preview tree with changes"""
        self.preview_tree.clear()

        for change in preview_changes:
            original = change["original"]
            proposed = change["proposed"]
            confidence = change.get("confidence", 0)
            source = change.get("source", "unknown")

            # Create tree item
            item = QTreeWidgetItem(
                [
                    "",  # Will add checkbox
                    f"{original.get('title', 'Unknown')}",
                    "→",
                    f"{proposed.get('title', 'Unknown')}",
                    f"{confidence:.1f}%",
                    source,
                ]
            )

            # Make checkable
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked)  # Default: checked

            # Color code by confidence
            if confidence >= 80:
                color = QColor(0, 200, 0)  # Green (high confidence)
            elif confidence >= 70:
                color = QColor(200, 200, 0)  # Yellow (medium confidence)
            else:
                color = QColor(200, 100, 0)  # Orange (low confidence)

            item.setForeground(4, QBrush(color))

            # Store change data
            item.setData(0, Qt.ItemDataRole.UserRole, change)

            self.preview_tree.addTopLevelItem(item)

    def _show_scan_summary(self, analysis: Dict[str, Any], cleaned_count: int, fetched_count: int) -> None:
        """Show scan summary dialog"""
        total = analysis.get("total_songs", 0)
        clean = analysis.get("clean", 0)
        problematic = total - clean

        summary_text = (
            f"Scan Complete!\n\n"
            f"Total songs: {total}\n"
            f"Clean: {clean}\n"
            f"Problematic: {problematic}\n\n"
            f"Cleaned: {cleaned_count} songs\n"
            f"Fetched from APIs: {fetched_count} songs\n\n"
            f"Review the preview below and select changes to apply."
        )

        QMessageBox.information(self, "Scan Summary", summary_text)

    def _on_select_all(self) -> None:
        """Select all changes"""
        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            item.setCheckState(0, Qt.CheckState.Checked)

    def _on_deselect_all(self) -> None:
        """Deselect all changes"""
        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            item.setCheckState(0, Qt.CheckState.Unchecked)

    def _on_apply_clicked(self) -> None:
        """Handle apply button click - Apply selected changes"""
        # Collect selected changes
        approved_changes = []

        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                change = item.data(0, Qt.ItemDataRole.UserRole)
                approved_changes.append(change)

        if not approved_changes:
            QMessageBox.information(self, "No Selection", "Please select at least one change to apply.")
            return

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Changes",
            f"Apply {len(approved_changes)} metadata changes?\n\n"
            f"This will update:\n"
            f"- Database records\n"
            f"- MP3 file tags (ID3)\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Apply changes
        download_covers = self.download_covers_check.isChecked()
        logger.info(f"Applying {len(approved_changes)} changes (covers: {download_covers})")
        self.status_label.setText(f"Applying {len(approved_changes)} changes...")

        results = self.applier.apply_changes(approved_changes, download_covers=download_covers)

        # Show results
        self._show_apply_results(results)
        self.data_changed.emit()

        # Clear preview
        self.preview_tree.clear()
        self.apply_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.deselect_all_button.setEnabled(False)

    def _show_apply_results(self, results: Dict[str, Any]) -> None:
        """Show apply results dialog"""
        success = results["success"]
        failed = results["failed"]
        errors = results.get("errors", [])
        covers_downloaded = results.get("covers_downloaded", 0)

        if failed == 0:
            message = f"Successfully updated {success} songs!"
            if covers_downloaded > 0:
                message += f"\n\nCover art downloaded: {covers_downloaded} albums"

            QMessageBox.information(self, "Changes Applied", message)
        else:
            error_text = "\n".join(errors[:5])
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more errors"

            message = f"Updated {success} songs.\nFailed to update {failed} songs."
            if covers_downloaded > 0:
                message += f"\n\nCover art downloaded: {covers_downloaded} albums"
            message += f"\n\nErrors:\n{error_text}"

            QMessageBox.warning(self, "Partially Complete", message)

        logger.info(f"Apply complete: {success} success, {failed} failed, {covers_downloaded} covers")
