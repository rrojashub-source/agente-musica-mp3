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
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QProgressBar,
    QTextEdit, QCheckBox, QGroupBox, QMessageBox,
    QComboBox, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont
import json
import logging
from pathlib import Path
from datetime import datetime

from services.cloud_sync_service import (
    CloudSyncService, LocalFolderProvider, GoogleDriveProvider,
    SyncStatus, ConflictStrategy
)
from translations import tr

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

    # Emitted when sync/import modifies DB data (library refresh trigger)
    data_changed = Signal()

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
        header_label = QLabel(tr("cloud_sync_title"))
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header_label)

        # Info label
        info_label = QLabel(tr("cloud_sync_info"))
        info_label.setStyleSheet("margin-bottom: 10px; color: #666;")
        layout.addWidget(info_label)

        # === PROVIDER SELECTION ===
        provider_group = QGroupBox(tr("cloud_sync_provider_config"))
        provider_layout = QVBoxLayout()

        # Provider dropdown
        provider_row = QHBoxLayout()
        provider_label = QLabel(tr("cloud_sync_provider"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([tr("cloud_sync_local_folder"), "Google Drive"])
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_row.addWidget(provider_label)
        provider_row.addWidget(self.provider_combo)
        provider_row.addStretch()
        provider_layout.addLayout(provider_row)

        # Local folder config
        self.local_folder_widget = QWidget()
        local_layout = QHBoxLayout(self.local_folder_widget)
        local_layout.setContentsMargins(0, 10, 0, 0)
        local_label = QLabel(tr("cloud_sync_folder"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText(tr("cloud_sync_folder_placeholder"))
        self.browse_btn = QPushButton(tr("cloud_sync_browse"))
        self.browse_btn.clicked.connect(self._browse_folder)
        local_layout.addWidget(local_label)
        local_layout.addWidget(self.folder_input, 1)
        local_layout.addWidget(self.browse_btn)
        provider_layout.addWidget(self.local_folder_widget)

        # Google Drive config (hidden by default)
        self.gdrive_widget = QWidget()
        gdrive_layout = QVBoxLayout(self.gdrive_widget)
        gdrive_layout.setContentsMargins(0, 10, 0, 0)

        # Simple info - no technical setup required
        gdrive_info = QLabel(tr("cloud_sync_gdrive_simple_info"))
        gdrive_info.setStyleSheet("color: #666;")
        gdrive_info.setWordWrap(True)
        gdrive_layout.addWidget(gdrive_info)

        # Auth status with user email
        self.gdrive_status = QLabel(tr("cloud_sync_status_not_auth"))
        self.gdrive_status.setStyleSheet("font-weight: bold; font-size: 13px; margin: 10px 0;")
        gdrive_layout.addWidget(self.gdrive_status)

        # Connect/Disconnect buttons row
        gdrive_buttons = QHBoxLayout()

        self.gdrive_connect_btn = QPushButton("🔗 " + tr("cloud_sync_connect_google"))
        self.gdrive_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3367D6;
            }
        """)
        self.gdrive_connect_btn.clicked.connect(self._connect_google_drive)
        gdrive_buttons.addWidget(self.gdrive_connect_btn)

        self.gdrive_logout_btn = QPushButton("🚪 " + tr("cloud_sync_logout"))
        self.gdrive_logout_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border-radius: 4px;
            }
        """)
        self.gdrive_logout_btn.clicked.connect(self._logout_google_drive)
        self.gdrive_logout_btn.hide()  # Hidden until connected
        gdrive_buttons.addWidget(self.gdrive_logout_btn)

        gdrive_buttons.addStretch()
        gdrive_layout.addLayout(gdrive_buttons)

        self.gdrive_widget.hide()
        provider_layout.addWidget(self.gdrive_widget)

        # Check if already authenticated
        self._check_gdrive_auth_status()

        # Connect button
        self.connect_btn = QPushButton(tr("cloud_sync_connect"))
        self.connect_btn.clicked.connect(self._connect_provider)
        provider_layout.addWidget(self.connect_btn)

        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # === SYNC STATUS ===
        status_group = QGroupBox(tr("cloud_sync_status"))
        status_layout = QVBoxLayout()

        # Connection status
        status_row = QHBoxLayout()
        status_label = QLabel(tr("cloud_sync_connection"))
        self.connection_status = QLabel(tr("cloud_sync_not_connected"))
        self.connection_status.setStyleSheet("font-weight: bold;")
        status_row.addWidget(status_label)
        status_row.addWidget(self.connection_status)
        status_row.addStretch()
        status_layout.addLayout(status_row)

        # Last sync info
        last_sync_row = QHBoxLayout()
        last_sync_label = QLabel(tr("cloud_sync_last_sync"))
        self.last_sync_status = QLabel(tr("cloud_sync_never"))
        last_sync_row.addWidget(last_sync_label)
        last_sync_row.addWidget(self.last_sync_status)
        last_sync_row.addStretch()
        status_layout.addLayout(last_sync_row)

        # Device ID
        device_row = QHBoxLayout()
        device_label = QLabel(tr("cloud_sync_device_id"))
        self.device_id_label = QLabel("---")
        self.device_id_label.setStyleSheet("font-family: monospace;")
        device_row.addWidget(device_label)
        device_row.addWidget(self.device_id_label)
        device_row.addStretch()
        status_layout.addLayout(device_row)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # === SYNC OPTIONS ===
        options_group = QGroupBox(tr("cloud_sync_options"))
        options_layout = QVBoxLayout()

        # Conflict strategy
        conflict_row = QHBoxLayout()
        conflict_label = QLabel(tr("cloud_sync_conflict"))
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItems([
            tr("cloud_sync_conflict_newer"),
            tr("cloud_sync_conflict_local"),
            tr("cloud_sync_conflict_remote"),
            tr("cloud_sync_conflict_both"),
            tr("cloud_sync_conflict_manual")
        ])
        self.conflict_combo.currentIndexChanged.connect(self._on_conflict_changed)
        conflict_row.addWidget(conflict_label)
        conflict_row.addWidget(self.conflict_combo)
        conflict_row.addStretch()
        options_layout.addLayout(conflict_row)

        # Auto sync checkbox
        self.auto_sync_check = QCheckBox(tr("cloud_sync_auto_sync"))
        options_layout.addWidget(self.auto_sync_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # === PROGRESS ===
        progress_group = QGroupBox(tr("cloud_sync_progress"))
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel(tr("cloud_sync_ready"))
        self.progress_label.setStyleSheet("color: #666;")
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # === ACTION BUTTONS ===
        actions_group = QGroupBox(tr("cloud_sync_actions"))
        actions_layout = QHBoxLayout()

        self.sync_btn = QPushButton(tr("cloud_sync_sync_now"))
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

        self.export_btn = QPushButton(tr("cloud_sync_export"))
        self.export_btn.clicked.connect(self._do_export)
        actions_layout.addWidget(self.export_btn)

        self.import_btn = QPushButton(tr("cloud_sync_import"))
        self.import_btn.clicked.connect(self._do_import)
        actions_layout.addWidget(self.import_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # === LOG ===
        log_group = QGroupBox(tr("cloud_sync_activity_log"))
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton(tr("cloud_sync_clear_log"))
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
        except (OSError, RuntimeError) as e:
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

    def _check_gdrive_auth_status(self):
        """Check if Google Drive is already authenticated"""
        try:
            provider = GoogleDriveProvider()
            if provider.is_authenticated:
                self.gdrive_status.setText("⏳ " + tr("cloud_sync_checking_auth"))
                self.gdrive_status.setStyleSheet("font-weight: bold; color: #FF9800;")
        except Exception:  # GUI error boundary - must not crash
            pass

    def _connect_google_drive(self):
        """Connect to Google Drive with simple OAuth flow"""
        self._log("Connecting to Google Drive...")
        self.gdrive_status.setText("⏳ " + tr("cloud_sync_opening_browser"))
        self.gdrive_status.setStyleSheet("font-weight: bold; color: #FF9800;")
        self.gdrive_connect_btn.setEnabled(False)

        try:
            self.provider = GoogleDriveProvider()
            self.sync_service.set_provider(self.provider)

            if self.sync_service.connect():
                # Success!
                user_email = getattr(self.provider, 'user_email', 'Connected')
                self.gdrive_status.setText(f"✅ {tr('cloud_sync_connected_as')}: {user_email}")
                self.gdrive_status.setStyleSheet("font-weight: bold; color: #4CAF50;")
                self.gdrive_connect_btn.hide()
                self.gdrive_logout_btn.show()
                self._update_connection_status(True)
                self._log(f"Connected to Google Drive as {user_email}")

                QMessageBox.information(
                    self,
                    tr("cloud_sync_success"),
                    tr("cloud_sync_gdrive_success_msg")
                )
            else:
                self.gdrive_status.setText("❌ " + tr("cloud_sync_connection_failed"))
                self.gdrive_status.setStyleSheet("font-weight: bold; color: #f44336;")
                self.gdrive_connect_btn.setEnabled(True)
                self._log("Google Drive connection failed")

        except ImportError:
            self.gdrive_status.setText("❌ " + tr("cloud_sync_missing_deps"))
            self.gdrive_status.setStyleSheet("font-weight: bold; color: #f44336;")
            self.gdrive_connect_btn.setEnabled(True)
            self._log("Missing dependencies: pip install google-api-python-client google-auth-oauthlib")
            QMessageBox.warning(
                self,
                tr("cloud_sync_missing_deps"),
                "pip install google-api-python-client google-auth-oauthlib"
            )
        except (RuntimeError, OSError) as e:
            self.gdrive_status.setText("❌ Error")
            self.gdrive_status.setStyleSheet("font-weight: bold; color: #f44336;")
            self.gdrive_connect_btn.setEnabled(True)
            self._log(f"Google Drive error: {e}")
            logger.error(f"Google Drive connection error: {e}")

    def _logout_google_drive(self):
        """Logout from Google Drive"""
        reply = QMessageBox.question(
            self,
            tr("cloud_sync_logout_confirm_title"),
            tr("cloud_sync_logout_confirm_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.provider and hasattr(self.provider, 'logout'):
                self.provider.logout()
            self.provider = None
            self._update_connection_status(False)
            self.gdrive_status.setText(tr("cloud_sync_status_not_auth"))
            self.gdrive_status.setStyleSheet("font-weight: bold;")
            self.gdrive_connect_btn.show()
            self.gdrive_connect_btn.setEnabled(True)
            self.gdrive_logout_btn.hide()
            self._log("Logged out from Google Drive")

    def _connect_provider(self):
        """Connect to selected provider"""
        provider_idx = self.provider_combo.currentIndex()

        if provider_idx == 0:  # Local Folder
            folder = self.folder_input.text().strip()
            if not folder:
                QMessageBox.warning(self, "Error", tr("cloud_sync_folder_placeholder"))
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
        else:  # Google Drive - use dedicated OAuth flow
            self._connect_google_drive()

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
                self.data_changed.emit()
            else:
                self._log("Sync failed")
        except (OSError, RuntimeError) as e:
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
            except (OSError, AttributeError, TypeError) as e:
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
                            self.data_changed.emit()
                            QMessageBox.information(
                                self,
                                "Import Complete",
                                "Library imported successfully!"
                            )
                        else:
                            self._log("Import failed")
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.error(f"Import error: {e}")
                self._log(f"ERROR: Import failed - {e}")
                QMessageBox.warning(self, "Import Error", str(e))

    @Slot()
    def _on_sync_started(self):
        """Handle sync started signal"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Syncing...")
        self._log("Sync started")

    @Slot(str, str, int)
    def _on_sync_progress(self, status: str, message: str, percent: int):
        """Handle sync progress signal"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"{status}: {message}")
        self._log(f"[{percent}%] {message}")

    @Slot(bool, str)
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

    @Slot(str)
    def _on_sync_failed(self, error: str):
        """Handle sync failed signal"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText(f"Sync failed: {error}")
        self._log(f"ERROR: Sync failed - {error}")

    def _log(self, message: str):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
