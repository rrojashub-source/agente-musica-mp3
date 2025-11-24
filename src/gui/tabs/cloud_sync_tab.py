"""
Cloud Sync Tab - Library Cloud Synchronization GUI
Phase: Cloud Sync Feature

Purpose: Sync library metadata across devices via cloud storage
- Provider selection (Local Folder, Google Drive)
- Sync status display
- Manual sync controls
- Export/Import functionality
- Conflict resolution settings

Created: November 24, 2025
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QProgressBar,
    QTextEdit, QCheckBox, QGroupBox, QMessageBox,
    QComboBox, QSpinBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
import logging
from pathlib import Path
from datetime import datetime

from services.cloud_sync_service import (
    CloudSyncService, LocalFolderProvider, GoogleDriveProvider,
    SyncStatus, ConflictStrategy
)

logger = logging.getLogger(__name__)


class CloudSyncTab(QWidget):
    """
    Cloud Sync Tab for Library Synchronization

    Features:
    - Provider selection (Local Folder, Google Drive)
    - Provider configuration
    - Sync status display
    - Manual sync button
    - Export/Import controls
    - Conflict strategy selection
    - Last sync info
    """

    def __init__(self, db_manager=None, parent=None):
        """
        Initialize Cloud Sync Tab

        Args:
            db_manager: DatabaseManager instance for library access
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.sync_service = None
        self.provider = None

        self._init_ui()
        # Connect signals after UI is initialized
        if self.sync_service:
            self._connect_signals()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Header
        header_label = QLabel("☁️ Cloud Sync")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header_label)

        # Info label
        info_label = QLabel(
            "Sync your library metadata across devices using cloud storage.\n"
            "Note: Only metadata is synced, not the actual MP3 files."
        )
        info_label.setStyleSheet("margin-bottom: 10px; color: #666;")
        layout.addWidget(info_label)

        # === PROVIDER SELECTION ===
        provider_group = QGroupBox("Provider Configuration")
        provider_layout = QVBoxLayout()

        # Provider dropdown
        provider_row = QHBoxLayout()
        provider_label = QLabel("Cloud Provider:")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Local Folder (NAS/USB)", "Google Drive"])
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_row.addWidget(provider_label)
        provider_row.addWidget(self.provider_combo)
        provider_row.addStretch()
        provider_layout.addLayout(provider_row)

        # Local folder config
        self.local_folder_widget = QWidget()
        local_layout = QHBoxLayout(self.local_folder_widget)
        local_layout.setContentsMargins(0, 10, 0, 0)
        local_label = QLabel("Sync Folder:")
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("D:\\Sync\\NexusMusic or /mnt/nas/music")
        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.clicked.connect(self._browse_folder)
        local_layout.addWidget(local_label)
        local_layout.addWidget(self.folder_input, 1)
        local_layout.addWidget(self.browse_btn)
        provider_layout.addWidget(self.local_folder_widget)

        # Google Drive config (hidden by default)
        self.gdrive_widget = QWidget()
        gdrive_layout = QVBoxLayout(self.gdrive_widget)
        gdrive_layout.setContentsMargins(0, 10, 0, 0)
        gdrive_label = QLabel("🔐 Google Drive requires OAuth authentication")
        gdrive_label.setStyleSheet("color: #666;")
        self.gdrive_auth_btn = QPushButton("🔑 Authenticate with Google")
        self.gdrive_auth_btn.clicked.connect(self._authenticate_google)
        self.gdrive_status = QLabel("Status: Not authenticated")
        gdrive_layout.addWidget(gdrive_label)
        gdrive_layout.addWidget(self.gdrive_auth_btn)
        gdrive_layout.addWidget(self.gdrive_status)
        self.gdrive_widget.hide()
        provider_layout.addWidget(self.gdrive_widget)

        # Connect button
        self.connect_btn = QPushButton("🔗 Connect Provider")
        self.connect_btn.clicked.connect(self._connect_provider)
        provider_layout.addWidget(self.connect_btn)

        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # === SYNC STATUS ===
        status_group = QGroupBox("Sync Status")
        status_layout = QVBoxLayout()

        # Connection status
        status_row = QHBoxLayout()
        status_label = QLabel("Connection:")
        self.connection_status = QLabel("⚪ Not connected")
        self.connection_status.setStyleSheet("font-weight: bold;")
        status_row.addWidget(status_label)
        status_row.addWidget(self.connection_status)
        status_row.addStretch()
        status_layout.addLayout(status_row)

        # Last sync info
        last_sync_row = QHBoxLayout()
        last_sync_label = QLabel("Last Sync:")
        self.last_sync_status = QLabel("Never")
        last_sync_row.addWidget(last_sync_label)
        last_sync_row.addWidget(self.last_sync_status)
        last_sync_row.addStretch()
        status_layout.addLayout(last_sync_row)

        # Device ID
        device_row = QHBoxLayout()
        device_label = QLabel("Device ID:")
        self.device_id_label = QLabel("---")
        self.device_id_label.setStyleSheet("font-family: monospace;")
        device_row.addWidget(device_label)
        device_row.addWidget(self.device_id_label)
        device_row.addStretch()
        status_layout.addLayout(device_row)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # === SYNC OPTIONS ===
        options_group = QGroupBox("Sync Options")
        options_layout = QVBoxLayout()

        # Conflict strategy
        conflict_row = QHBoxLayout()
        conflict_label = QLabel("Conflict Resolution:")
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItems([
            "Newer Wins (recommended)",
            "Local Wins (prefer this device)",
            "Remote Wins (prefer cloud)",
            "Keep Both (no data loss)",
            "Manual (ask each time)"
        ])
        self.conflict_combo.currentIndexChanged.connect(self._on_conflict_changed)
        conflict_row.addWidget(conflict_label)
        conflict_row.addWidget(self.conflict_combo)
        conflict_row.addStretch()
        options_layout.addLayout(conflict_row)

        # Auto sync checkbox
        self.auto_sync_check = QCheckBox("Auto-sync on startup")
        options_layout.addWidget(self.auto_sync_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # === PROGRESS ===
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Ready")
        self.progress_label.setStyleSheet("color: #666;")
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # === ACTION BUTTONS ===
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()

        self.sync_btn = QPushButton("🔄 Sync Now")
        self.sync_btn.setEnabled(False)
        self.sync_btn.clicked.connect(self._do_sync)
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        actions_layout.addWidget(self.sync_btn)

        self.export_btn = QPushButton("📤 Export Library")
        self.export_btn.clicked.connect(self._do_export)
        actions_layout.addWidget(self.export_btn)

        self.import_btn = QPushButton("📥 Import Library")
        self.import_btn.clicked.connect(self._do_import)
        actions_layout.addWidget(self.import_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # === LOG ===
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_log_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()
        self.setLayout(layout)

        # Initialize service
        self._init_service()

    def _init_service(self):
        """Initialize cloud sync service"""
        try:
            data_dir = str(Path.home() / ".nexus_music")
            self.sync_service = CloudSyncService.get_instance(data_dir)

            if self.sync_service:
                self.device_id_label.setText(self.sync_service.device_id[:12] + "...")
                self._log("Cloud sync service initialized")

                # Check for existing state
                if self.sync_service.sync_state and self.sync_service.sync_state.last_sync_time:
                    self.last_sync_status.setText(self.sync_service.sync_state.last_sync_time)

                # Connect signals now that service is ready
                self._connect_signals()
        except Exception as e:
            logger.error(f"Failed to init sync service: {e}")
            self._log(f"ERROR: Failed to initialize: {e}")

    def _connect_signals(self):
        """Connect service signals to UI slots"""
        if self.sync_service:
            self.sync_service.sync_started.connect(self._on_sync_started)
            self.sync_service.sync_progress.connect(self._on_sync_progress)
            self.sync_service.sync_completed.connect(self._on_sync_completed)
            self.sync_service.sync_failed.connect(self._on_sync_failed)

    def _on_provider_changed(self, index: int):
        """Handle provider selection change"""
        if index == 0:  # Local Folder
            self.local_folder_widget.show()
            self.gdrive_widget.hide()
        else:  # Google Drive
            self.local_folder_widget.hide()
            self.gdrive_widget.show()

    def _browse_folder(self):
        """Browse for sync folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Sync Folder",
            str(Path.home())
        )
        if folder:
            self.folder_input.setText(folder)

    def _authenticate_google(self):
        """Authenticate with Google Drive"""
        QMessageBox.information(
            self,
            "Google Drive Authentication",
            "Google Drive OAuth authentication will open in your browser.\n\n"
            "This feature requires setting up Google Cloud credentials.\n"
            "See docs/cloud_sync_setup.md for instructions."
        )
        # TODO: Implement actual OAuth flow
        self._log("Google Drive authentication not yet implemented")

    def _connect_provider(self):
        """Connect to selected provider"""
        provider_idx = self.provider_combo.currentIndex()

        if provider_idx == 0:  # Local Folder
            folder = self.folder_input.text().strip()
            if not folder:
                QMessageBox.warning(self, "Error", "Please select a sync folder")
                return

            # Create folder if doesn't exist
            Path(folder).mkdir(parents=True, exist_ok=True)

            self.provider = LocalFolderProvider(folder)
            if self.sync_service.set_provider(self.provider):
                if self.sync_service.connect():
                    self._update_connection_status(True)
                    self._log(f"Connected to local folder: {folder}")
                else:
                    self._log("Failed to connect to local folder")
                    QMessageBox.warning(self, "Error", "Failed to connect to folder")
        else:  # Google Drive
            self.provider = GoogleDriveProvider()
            if self.sync_service.set_provider(self.provider):
                if self.sync_service.connect():
                    self._update_connection_status(True)
                    self._log("Connected to Google Drive")
                else:
                    self._log("Google Drive authentication required")
                    QMessageBox.warning(
                        self,
                        "Authentication Required",
                        "Please authenticate with Google Drive first"
                    )

    def _update_connection_status(self, connected: bool):
        """Update connection status display"""
        if connected:
            self.connection_status.setText("🟢 Connected")
            self.connection_status.setStyleSheet("font-weight: bold; color: #4CAF50;")
            self.sync_btn.setEnabled(True)
        else:
            self.connection_status.setText("⚪ Not connected")
            self.connection_status.setStyleSheet("font-weight: bold; color: #666;")
            self.sync_btn.setEnabled(False)

    def _on_conflict_changed(self, index: int):
        """Handle conflict strategy change"""
        strategies = [
            ConflictStrategy.NEWER_WINS,
            ConflictStrategy.LOCAL_WINS,
            ConflictStrategy.REMOTE_WINS,
            ConflictStrategy.KEEP_BOTH,
            ConflictStrategy.MANUAL
        ]
        if self.sync_service and index < len(strategies):
            self.sync_service.conflict_strategy = strategies[index]
            self._log(f"Conflict strategy: {strategies[index].value}")

    def _do_sync(self):
        """Perform sync"""
        if not self.sync_service or not self.sync_service.is_connected:
            QMessageBox.warning(self, "Error", "Not connected to provider")
            return

        self.sync_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        try:
            result = self.sync_service.sync(self.db_manager)
            if result:
                self._log("Sync completed successfully")
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.last_sync_status.setText(now)
            else:
                self._log("Sync failed")
        except Exception as e:
            logger.error(f"Sync error: {e}")
            self._log(f"ERROR: {e}")
        finally:
            self.sync_btn.setEnabled(True)
            self.progress_bar.setVisible(False)

    def _do_export(self):
        """Export library to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Library",
            str(Path.home() / "nexus_library_export.json"),
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                if self.sync_service:
                    export_data = self.sync_service.export_library(self.db_manager)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        import json
                        json.dump(export_data.__dict__, f, indent=2)
                    self._log(f"Library exported to: {file_path}")
                    QMessageBox.information(
                        self,
                        "Export Complete",
                        f"Library exported successfully!\n\n"
                        f"Songs: {len(export_data.songs)}\n"
                        f"Playlists: {len(export_data.playlists)}"
                    )
            except Exception as e:
                logger.error(f"Export error: {e}")
                self._log(f"ERROR: Export failed - {e}")
                QMessageBox.warning(self, "Export Error", str(e))

    def _do_import(self):
        """Import library from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Library",
            str(Path.home()),
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                if self.sync_service:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        import json
                        data = json.load(f)

                    # Confirm import
                    reply = QMessageBox.question(
                        self,
                        "Confirm Import",
                        f"Import library from {Path(file_path).name}?\n\n"
                        f"This will merge the imported data with your current library.\n"
                        f"Songs in file: {len(data.get('songs', []))}\n"
                        f"Playlists in file: {len(data.get('playlists', []))}",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        result = self.sync_service.import_library(data, self.db_manager)
                        if result:
                            self._log(f"Library imported from: {file_path}")
                            QMessageBox.information(
                                self,
                                "Import Complete",
                                "Library imported successfully!"
                            )
                        else:
                            self._log("Import failed")
            except Exception as e:
                logger.error(f"Import error: {e}")
                self._log(f"ERROR: Import failed - {e}")
                QMessageBox.warning(self, "Import Error", str(e))

    @pyqtSlot()
    def _on_sync_started(self):
        """Handle sync started signal"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Syncing...")
        self._log("Sync started")

    @pyqtSlot(str, str, int)
    def _on_sync_progress(self, status: str, message: str, percent: int):
        """Handle sync progress signal"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"{status}: {message}")
        self._log(f"[{percent}%] {message}")

    @pyqtSlot(bool, str)
    def _on_sync_completed(self, success: bool, message: str):
        """Handle sync completed signal"""
        self.progress_bar.setVisible(False)
        if success:
            self.progress_label.setText("Sync completed successfully")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.last_sync_status.setText(now)
        else:
            self.progress_label.setText(f"Sync completed with issues: {message}")
        self._log(f"Sync completed: {message}")

    @pyqtSlot(str)
    def _on_sync_failed(self, error: str):
        """Handle sync failed signal"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText(f"Sync failed: {error}")
        self._log(f"ERROR: Sync failed - {error}")

    def _log(self, message: str):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
