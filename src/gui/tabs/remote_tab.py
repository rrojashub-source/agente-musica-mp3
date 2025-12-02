"""
Remote Control Tab - Mobile Remote Server GUI
Allows users to control NEXUS from their mobile devices

Created: November 24, 2025
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QSpinBox, QMessageBox,
    QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont, QDesktopServices
from PyQt6.QtCore import QUrl
import logging
from typing import Optional
import base64

from services.remote_server import RemoteServer
from translations import tr

logger = logging.getLogger(__name__)


class RemoteTab(QWidget):
    """
    Remote Control Tab

    Features:
    - Start/stop remote server
    - Display connection URL
    - QR code for easy mobile connection
    - Connection status
    - Activity log
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server: Optional[RemoteServer] = None
        self._init_ui()
        self._init_server()

    def _init_ui(self):
        """Initialize user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)  # Reduced from 15 to 10
        main_layout.setContentsMargins(10, 5, 10, 10)  # Reduced top margin from 10 to 5

        # Header
        header = QLabel(tr("remote_title"))
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(header)

        # Instructions (moved from bottom)
        instructions = QLabel(tr("remote_instructions"))
        instructions.setStyleSheet("color: #888; font-size: 11px; padding: 5px 0;")
        main_layout.addWidget(instructions)

        main_layout.addSpacing(5)  # Reduced from 10 to 5

        # === ROW 1: QR CODE (CENTERED) ===
        qr_row = QHBoxLayout()
        qr_row.addStretch()

        qr_frame = QFrame()
        qr_frame.setFixedSize(280, 280)
        qr_frame.setStyleSheet("background: white; border: 2px solid #666; border-radius: 6px;")
        qr_layout = QVBoxLayout(qr_frame)
        qr_layout.setContentsMargins(0, 0, 0, 0)

        self.qr_label = QLabel("QR Code")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet("color: #999;")
        qr_layout.addWidget(self.qr_label)

        qr_row.addWidget(qr_frame)
        qr_row.addStretch()
        main_layout.addLayout(qr_row)

        main_layout.addSpacing(10)  # Reduced from 15 to 10

        # === ROW 2: SERVER + CONNECTION (SIDE BY SIDE) ===
        controls_row = QHBoxLayout()
        controls_row.setSpacing(20)

        # SERVER (LEFT SIDE)
        server_group = QGroupBox(tr("remote_server"))
        server_layout = QVBoxLayout(server_group)

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel(tr("remote_port")))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(8080)
        self.port_spin.setFixedWidth(80)
        port_row.addWidget(self.port_spin)
        port_row.addStretch()
        server_layout.addLayout(port_row)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton(tr("remote_start"))
        self.start_btn.setFixedHeight(35)
        self.start_btn.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self._start_server)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton(tr("remote_stop"))
        self.stop_btn.setFixedHeight(35)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background: #f44336; color: white; font-weight: bold;")
        self.stop_btn.clicked.connect(self._stop_server)
        btn_row.addWidget(self.stop_btn)
        server_layout.addLayout(btn_row)

        controls_row.addWidget(server_group)

        # CONNECTION (RIGHT SIDE)
        conn_group = QGroupBox(tr("remote_connection"))
        conn_layout = QVBoxLayout(conn_group)

        self.url_label = QLabel(tr("remote_url_not_running"))
        self.url_label.setStyleSheet("background: #2d2d2d; color: #ffffff; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 10px;")
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        conn_layout.addWidget(self.url_label)

        self.open_btn = QPushButton(tr("remote_open_browser"))
        self.open_btn.setFixedHeight(35)
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_in_browser)
        conn_layout.addWidget(self.open_btn)

        self.status_label = QLabel(tr("remote_status_stopped"))
        self.status_label.setStyleSheet("font-weight: bold;")
        conn_layout.addWidget(self.status_label)

        controls_row.addWidget(conn_group)

        main_layout.addLayout(controls_row)

        # Activity Log
        log_group = QGroupBox(tr("remote_activity_log"))
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(80)  # Fixed height to prevent pushing content
        self.log_text.setStyleSheet("font-family: monospace; font-size: 10px; background: #1e1e1e; color: #cccccc;")
        log_layout.addWidget(self.log_text)

        main_layout.addWidget(log_group)
        main_layout.addStretch()

    def _init_server(self):
        """Initialize remote server"""
        try:
            self._server = RemoteServer.get_instance()

            # Connect signals
            if hasattr(self._server, 'server_started'):
                self._server.server_started.connect(self._on_server_started)
                self._server.server_stopped.connect(self._on_server_stopped)
                self._server.command_received.connect(self._on_command_received)

            self._log("Remote server initialized")

        except Exception as e:
            logger.error(f"Failed to init remote server: {e}")
            self._log(f"ERROR: {e}")

    def _start_server(self):
        """Start the remote server"""
        if not self._server:
            return

        port = self.port_spin.value()

        try:
            if self._server.start(port=port):
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.port_spin.setEnabled(False)
                self._update_qr_code()
            else:
                QMessageBox.warning(
                    self,
                    "Server Error",
                    "Failed to start server.\n"
                    "Make sure Flask is installed: pip install flask flask-cors"
                )
        except Exception as e:
            logger.error(f"Server start error: {e}")
            self._log(f"ERROR: {e}")

    def _stop_server(self):
        """Stop the remote server"""
        if self._server:
            self._server.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.port_spin.setEnabled(True)
            self.open_btn.setEnabled(False)

            self.url_label.setText("URL: Not running")
            self.status_label.setText("⚪ Server stopped")
            self.status_label.setStyleSheet("font-weight: bold; padding: 10px; color: #666;")
            self.qr_label.setText("QR Code")
            self.qr_label.setPixmap(QPixmap())

            self._log("Server stopped")

    def _update_qr_code(self):
        """Update QR code display"""
        if not self._server or not self._server.is_running:
            return

        try:
            # Try to get QR code from server
            import requests
            response = requests.get(f"http://127.0.0.1:{self.port_spin.value()}/qr", timeout=5)
            data = response.json()

            if 'qr_image' in data:
                # Decode base64 image
                img_data = data['qr_image'].split(',')[1]
                img_bytes = base64.b64decode(img_data)

                # Create QPixmap
                image = QImage()
                image.loadFromData(img_bytes)
                pixmap = QPixmap.fromImage(image)
                self.qr_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio))

        except Exception as e:
            logger.debug(f"QR code fetch failed (expected if qrcode not installed): {e}")
            self.qr_label.setText("QR not available\n(install qrcode)")

    def _open_in_browser(self):
        """Open remote URL in browser"""
        if self._server and self._server.is_running:
            QDesktopServices.openUrl(QUrl(self._server.url))

    @pyqtSlot(str, int)
    def _on_server_started(self, host: str, port: int):
        """Handle server started signal"""
        url = f"http://{host}:{port}"
        self.url_label.setText(f"URL: {url}")
        self.status_label.setText("🟢 Server running")
        self.status_label.setStyleSheet("font-weight: bold; padding: 10px; color: #4CAF50;")
        self.open_btn.setEnabled(True)
        self._log(f"Server started at {url}")

    @pyqtSlot()
    def _on_server_stopped(self):
        """Handle server stopped signal"""
        self.status_label.setText("⚪ Server stopped")
        self.status_label.setStyleSheet("font-weight: bold; padding: 10px; color: #666;")

    @pyqtSlot(str, dict)
    def _on_command_received(self, command: str, params: dict):
        """Handle command received from mobile"""
        self._log(f"Command: {command} {params}")

    def _log(self, message: str):
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
