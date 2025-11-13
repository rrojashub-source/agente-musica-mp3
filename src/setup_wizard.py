#!/usr/bin/env python3
"""
Setup Wizard - Primera Configuración
Detecta carpeta de música y escanea biblioteca
Project: AGENTE_MUSICA_MP3_001
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QFileDialog, QProgressBar, QTextEdit, QMessageBox,
        QComboBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError:
    print("❌ PyQt6 not installed")
    exit(1)

from translations import t


class LibraryScanWorker(QThread):
    """Worker para escanear archivos de música"""
    progress_update = pyqtSignal(int, str)  # (progress, message)
    scan_complete = pyqtSignal(int)  # total files found
    error_occurred = pyqtSignal(str)

    def __init__(self, library_path: str):
        super().__init__()
        self.library_path = Path(library_path)
        self.audio_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.wav', '.wma', '.aac'}
        self._is_cancelled = False

    def cancel(self):
        """Cancel scanning"""
        self._is_cancelled = True

    def run(self):
        """Scan for audio files"""
        try:
            self.progress_update.emit(0, "Iniciando escaneo...")

            # Count total files first (for progress calculation)
            self.progress_update.emit(10, "Contando archivos...")

            audio_files = []

            # Scan directory recursively
            for i, file_path in enumerate(self.library_path.rglob('*')):
                if self._is_cancelled:
                    return

                if file_path.suffix.lower() in self.audio_extensions:
                    audio_files.append(file_path)

                    # Update progress every 100 files
                    if i % 100 == 0:
                        self.progress_update.emit(
                            min(90, 10 + (i // 10)),
                            f"Encontrados: {len(audio_files)} archivos..."
                        )

            self.progress_update.emit(100, f"Escaneo completo: {len(audio_files)} archivos")
            self.scan_complete.emit(len(audio_files))

        except Exception as e:
            self.error_occurred.emit(f"Error escaneando: {str(e)}")


class SetupWizard(QDialog):
    """
    Setup Wizard - Configuración Inicial
    - Detecta carpeta Music del sistema
    - Permite seleccionar carpeta personalizada
    - Escanea archivos de música
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.library_path = None
        self.audio_files_count = 0
        self.scan_worker = None

        self.setWindowTitle("🎵 NEXUS Music Manager - Primera Configuración")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setModal(True)

        self.init_ui()
        self.detect_music_folder()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)

        # Header
        self.header = QLabel("🎵 Bienvenido a NEXUS Music Manager")
        self.header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header)

        # Description
        self.description = QLabel(
            "Configuremos tu biblioteca de música.\n\n"
            "NEXUS detectará automáticamente tu carpeta de música del sistema,\n"
            "o puedes seleccionar una carpeta personalizada."
        )
        self.description.setWordWrap(True)
        self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description.setStyleSheet("color: gray; padding: 20px;")
        layout.addWidget(self.description)

        # Library path selection
        path_layout = QHBoxLayout()

        path_label = QLabel("📁 Carpeta de Música:")
        path_label.setFixedWidth(150)
        path_layout.addWidget(path_label)

        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText("Selecciona una carpeta...")
        path_layout.addWidget(self.path_input)

        self.browse_btn = QPushButton("📂 Seleccionar...")
        self.browse_btn.setFixedWidth(120)
        self.browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.browse_btn)

        layout.addLayout(path_layout)

        # Scan button
        scan_layout = QHBoxLayout()
        scan_layout.addStretch()

        self.scan_btn = QPushButton("🔍 Escanear Biblioteca")
        self.scan_btn.setFixedHeight(40)
        self.scan_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)
        scan_layout.addWidget(self.scan_btn)

        scan_layout.addStretch()
        layout.addLayout(scan_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Results panel
        results_label = QLabel("📊 Resultados del Escaneo:")
        results_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(results_label)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        self.results_text.setPlaceholderText("Los resultados del escaneo aparecerán aquí...")
        layout.addWidget(self.results_text)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.skip_btn = QPushButton("⏭️ Omitir (usar demo)")
        self.skip_btn.clicked.connect(self.skip_setup)
        buttons_layout.addWidget(self.skip_btn)

        self.finish_btn = QPushButton("✅ Finalizar Configuración")
        self.finish_btn.setFixedHeight(40)
        self.finish_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.finish_btn.clicked.connect(self.finish_setup)
        self.finish_btn.setEnabled(False)
        buttons_layout.addWidget(self.finish_btn)

        layout.addLayout(buttons_layout)

    def detect_music_folder(self):
        """Auto-detect system Music folder"""
        # Try standard Music folder locations
        music_paths = [
            Path.home() / "Music",
            Path.home() / "Música",
            Path.home() / "My Music",
            Path.home() / "Documents" / "Music",
        ]

        for path in music_paths:
            if path.exists() and path.is_dir():
                self.library_path = str(path)
                self.path_input.setText(str(path))
                self.scan_btn.setEnabled(True)

                self.results_text.append(
                    f"✅ Carpeta de música detectada automáticamente:\n"
                    f"   {path}\n\n"
                    f"💡 Puedes cambiarla usando 'Seleccionar...' o hacer clic en 'Escanear Biblioteca'\n"
                )
                return

        # No standard folder found
        self.results_text.append(
            "⚠️ No se detectó una carpeta de música estándar.\n"
            "Por favor, selecciona tu carpeta de música manualmente.\n"
        )

    def browse_folder(self):
        """Browse for custom folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecciona tu Carpeta de Música",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            self.library_path = folder
            self.path_input.setText(folder)
            self.scan_btn.setEnabled(True)
            self.results_text.append(f"\n📁 Carpeta seleccionada: {folder}\n")

    def start_scan(self):
        """Start library scan"""
        if not self.library_path:
            QMessageBox.warning(self, "Error", "Por favor selecciona una carpeta primero")
            return

        # Check if folder exists and is accessible
        path = Path(self.library_path)
        if not path.exists() or not path.is_dir():
            QMessageBox.warning(
                self,
                "Error",
                f"La carpeta no existe o no es accesible:\n{self.library_path}"
            )
            return

        # Disable controls during scan
        self.scan_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.results_text.append("\n🔍 Iniciando escaneo de archivos de música...\n")

        # Start scan worker
        self.scan_worker = LibraryScanWorker(self.library_path)
        self.scan_worker.progress_update.connect(self.on_progress_update)
        self.scan_worker.scan_complete.connect(self.on_scan_complete)
        self.scan_worker.error_occurred.connect(self.on_scan_error)
        self.scan_worker.start()

    def on_progress_update(self, progress: int, message: str):
        """Handle scan progress update"""
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{progress}% - {message}")

    def on_scan_complete(self, total_files: int):
        """Handle scan completion"""
        self.audio_files_count = total_files

        self.results_text.append(
            f"\n✅ Escaneo completado!\n"
            f"📊 Total de archivos de audio encontrados: {total_files:,}\n\n"
        )

        if total_files > 0:
            self.results_text.append(
                f"✅ Tu biblioteca está lista para ser importada.\n"
                f"Haz clic en 'Finalizar Configuración' para continuar.\n"
            )
            self.finish_btn.setEnabled(True)
        else:
            self.results_text.append(
                f"⚠️ No se encontraron archivos de audio en esta carpeta.\n"
                f"Puedes seleccionar otra carpeta o usar el modo demo.\n"
            )
            self.browse_btn.setEnabled(True)
            self.scan_btn.setEnabled(True)

        self.skip_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_scan_error(self, error: str):
        """Handle scan error"""
        self.results_text.append(f"\n❌ {error}\n")

        self.scan_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "Error de Escaneo", error)

    def skip_setup(self):
        """Skip setup and use demo database"""
        reply = QMessageBox.question(
            self,
            "Omitir Configuración",
            "¿Deseas omitir la configuración y usar la biblioteca de demostración?\n\n"
            "Podrás configurar tu biblioteca real más tarde desde el menú.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.library_path = None  # Use demo database
            self.accept()

    def finish_setup(self):
        """Finish setup with configured library"""
        if not self.library_path or self.audio_files_count == 0:
            QMessageBox.warning(
                self,
                "Configuración Incompleta",
                "Por favor escanea tu biblioteca primero o selecciona 'Omitir'."
            )
            return

        # Save configuration
        self.accept()

    def get_library_path(self) -> Optional[str]:
        """Get configured library path"""
        return self.library_path

    def get_audio_files_count(self) -> int:
        """Get total audio files found"""
        return self.audio_files_count
