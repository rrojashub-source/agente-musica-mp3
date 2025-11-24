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
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Header
        header_label = QLabel("📱 Remote Control")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header_label)

        # Info
        info_label = QLabel(
            "Control NEXUS Music Manager from your phone or tablet.\n"
            "Scan the QR code or enter the URL in your mobile browser."
        )
        info_label.setStyleSheet("color: #666;")
        layout.addWidget(info_label)

        # Server Control
        server_group = QGroupBox("Server")
        server_layout = QVBoxLayout()

        # Port selection
        port_row = QHBoxLayout()
        port_label = QLabel("Port:")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(8080)
        port_row.addWidget(port_label)
        port_row.addWidget(self.port_spin)
        port_row.addStretch()
        server_layout.addLayout(port_row)

        # Start/Stop buttons
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("▶️ Start Server")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.start_btn.clicked.connect(self._start_server)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ Stop Server")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.stop_btn.clicked.connect(self._stop_server)
        btn_row.addWidget(self.stop_btn)
        btn_row.addStretch()

        server_layout.addLayout(btn_row)
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)

        # Connection Info
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout()

        # QR Code
        qr_frame = QFrame()
        qr_frame.setFixedSize(200, 200)
        qr_frame.setStyleSheet("background: white; border-radius: 10px;")
        qr_layout = QVBoxLayout(qr_frame)

        self.qr_label = QLabel("QR Code")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet("color: #666;")
        qr_layout.addWidget(self.qr_label)

        conn_layout.addWidget(qr_frame)

        # URL and status
        info_layout = QVBoxLayout()

        self.url_label = QLabel("URL: Not running")
        self.url_label.setFont(QFont("Consolas", 12))
        self.url_label.setStyleSheet("padding: 10px; background: #333; border-radius: 5px;")
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_layout.addWidget(self.url_label)

        self.open_btn = QPushButton("🌐 Open in Browser")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_in_browser)
        info_layout.addWidget(self.open_btn)

        self.status_label = QLabel("⚪ Server stopped")
        self.status_label.setStyleSheet("font-weight: bold; padding: 10px;")
        info_layout.addWidget(self.status_label)

        info_layout.addStretch()
        conn_layout.addLayout(info_layout)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # Activity Log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Instructions
        instr_group = QGroupBox("Instructions")
        instr_layout = QVBoxLayout()
        instr_text = QLabel(
            "1. Click 'Start Server' to enable remote control\n"
            "2. Make sure your phone is on the same WiFi network\n"
            "3. Scan the QR code with your phone camera, or\n"
            "4. Enter the URL in your mobile browser\n"
            "5. Use the mobile interface to control playback"
        )
        instr_text.setStyleSheet("color: #888;")
        instr_layout.addWidget(instr_text)
        instr_group.setLayout(instr_layout)
        layout.addWidget(instr_group)

        layout.addStretch()
        self.setLayout(layout)

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
