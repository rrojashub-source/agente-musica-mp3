"""
Chords Tab — Display detected chords for the current song

Features:
- Auto-detect chords when song changes (background worker)
- Timeline display with chord names
- Transpose controls (+/- semitone)
- Current chord highlight synchronized with playback
- Cache results for instant re-display

Created: March 2026
"""
import logging
from typing import Optional, Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QPushButton, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor

logger = logging.getLogger(__name__)


class ChordsAnalyzeWorker(QThread):
    """Background worker for chord analysis (non-blocking)"""

    finished = Signal(list)    # chord list
    error = Signal(str)        # error message
    progress = Signal(str)     # status message

    def __init__(self, chords_client, file_path: str, song_id: int = None):
        super().__init__()
        self.chords_client = chords_client
        self.file_path = file_path
        self.song_id = song_id

    def run(self):
        try:
            self.progress.emit("Analizando audio...")
            chords = self.chords_client.get_chords(
                self.file_path, song_id=self.song_id
            )
            if chords:
                self.finished.emit(chords)
            else:
                self.error.emit("No se pudieron detectar acordes")
        except Exception as e:
            logger.error(f"Chord worker error: {e}")
            self.error.emit(f"Error de analisis: {str(e)}")


class ChordsTab(QWidget):
    """
    Tab for displaying detected song chords.

    Shows a timeline of chords detected from the audio,
    with transpose controls and current-chord highlighting.
    """

    def __init__(self, chords_client=None, audio_player=None):
        super().__init__()
        self.chords_client = chords_client
        self.audio_player = audio_player
        self.current_song = None
        self._worker = None
        self._chords = []           # Current chord list
        self._transpose = 0         # Current transposition in semitones
        self._current_chord_idx = -1
        self._init_ui()

        # Timer for highlighting current chord during playback
        self._highlight_timer = QTimer()
        self._highlight_timer.setInterval(250)  # Check 4x/second
        self._highlight_timer.timeout.connect(self._update_current_chord)

        logger.info("ChordsTab initialized")

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # ===== Header =====
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)

        self.header_label = QLabel("🎸 No hay cancion reproduciendo")
        self.header_label.setStyleSheet("""
            QLabel { font-size: 16pt; font-weight: bold; padding: 5px; }
        """)
        self.header_label.setWordWrap(True)
        header_layout.addWidget(self.header_label)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel { font-size: 10pt; padding: 2px; }
        """)
        self.status_label.setProperty("class", "secondary")
        header_layout.addWidget(self.status_label)

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        # ===== Transpose Controls =====
        controls_frame = QFrame()
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(5, 5, 5, 5)

        controls_layout.addWidget(QLabel("Transponer:"))

        self.transpose_down_btn = QPushButton("- 1")
        self.transpose_down_btn.setFixedWidth(50)
        self.transpose_down_btn.setToolTip("Bajar medio tono")
        self.transpose_down_btn.clicked.connect(lambda: self._on_transpose(-1))
        controls_layout.addWidget(self.transpose_down_btn)

        self.transpose_label = QLabel("0")
        self.transpose_label.setFixedWidth(30)
        self.transpose_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transpose_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        controls_layout.addWidget(self.transpose_label)

        self.transpose_up_btn = QPushButton("+ 1")
        self.transpose_up_btn.setFixedWidth(50)
        self.transpose_up_btn.setToolTip("Subir medio tono")
        self.transpose_up_btn.clicked.connect(lambda: self._on_transpose(+1))
        controls_layout.addWidget(self.transpose_up_btn)

        self.reset_transpose_btn = QPushButton("Reset")
        self.reset_transpose_btn.setFixedWidth(60)
        self.reset_transpose_btn.clicked.connect(self._on_transpose_reset)
        controls_layout.addWidget(self.reset_transpose_btn)

        controls_layout.addStretch()

        # Instrument selector (for future Phase 2)
        controls_layout.addWidget(QLabel("Instrumento:"))
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems(["Guitarra", "Piano", "Ukulele"])
        self.instrument_combo.setEnabled(False)  # Phase 2
        self.instrument_combo.setToolTip("Diagramas de acordes (proximamente)")
        controls_layout.addWidget(self.instrument_combo)

        controls_frame.setLayout(controls_layout)
        layout.addWidget(controls_frame)

        # ===== Chords Display =====
        self.chords_text = QTextEdit()
        self.chords_text.setReadOnly(True)
        self.chords_text.setPlaceholderText(
            "🎸 Reproduce una cancion para detectar acordes...\n\n"
            "Los acordes se analizan automaticamente del audio."
        )

        font = QFont("Consolas", 13)
        if not font.exactMatch():
            font = QFont("Courier New", 13)
        self.chords_text.setFont(font)
        self.chords_text.setStyleSheet("""
            QTextEdit { padding: 15px; }
        """)

        layout.addWidget(self.chords_text)

        # ===== Bottom Controls =====
        bottom_layout = QHBoxLayout()

        self.analyze_button = QPushButton("🔄 Re-analizar")
        self.analyze_button.setToolTip("Analizar acordes de nuevo")
        self.analyze_button.clicked.connect(self._on_manual_analyze)
        self.analyze_button.setStyleSheet("""
            QPushButton { padding: 8px 16px; font-size: 10pt; border-radius: 4px; }
        """)
        bottom_layout.addWidget(self.analyze_button)

        self.copy_button = QPushButton("📋 Copiar Acordes")
        self.copy_button.setToolTip("Copiar acordes al portapapeles")
        self.copy_button.clicked.connect(self._on_copy_chords)
        self.copy_button.setEnabled(False)
        self.copy_button.setStyleSheet("""
            QPushButton { padding: 8px 16px; font-size: 10pt; border-radius: 4px; }
        """)
        bottom_layout.addWidget(self.copy_button)

        bottom_layout.addStretch()

        # Chord count label
        self.count_label = QLabel("")
        self.count_label.setProperty("class", "muted")
        bottom_layout.addWidget(self.count_label)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def on_song_changed(self, song_info: Dict):
        """Called when a new song starts playing."""
        self.current_song = song_info
        self._transpose = 0
        self.transpose_label.setText("0")
        self._current_chord_idx = -1

        title = song_info.get('title', 'Unknown')
        artist = song_info.get('artist', 'Unknown Artist')
        self.header_label.setText(f"🎸 {title} - {artist}")

        file_path = song_info.get('file_path', '')
        song_id = song_info.get('id')

        if file_path:
            self._analyze_chords(file_path, song_id)
        else:
            self.status_label.setText("⚠️ Sin ruta de archivo")

    def _analyze_chords(self, file_path: str, song_id: int = None):
        """Start background chord analysis."""
        if not self.chords_client:
            self.chords_text.setPlainText(
                "❌ Servicio de acordes no disponible\n\n"
                "Requiere: pip install librosa pychord"
            )
            self.status_label.setText("⚠️ Librosa no instalado")
            return

        # Show loading state
        self.chords_text.setPlainText("⏳ Analizando acordes del audio...")
        self.status_label.setText("🔍 Analizando...")
        self.analyze_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self._highlight_timer.stop()

        # Cancel previous worker
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            if not self._worker.wait(3000):
                self._worker.terminate()
                self._worker.wait()

        # Start background analysis
        self._worker = ChordsAnalyzeWorker(
            self.chords_client, file_path, song_id
        )
        self._worker.finished.connect(self._on_chords_found)
        self._worker.error.connect(self._on_chords_error)
        self._worker.progress.connect(
            lambda msg: self.status_label.setText(f"🔍 {msg}")
        )
        self._worker.start()

    def _on_chords_found(self, chords: list):
        """Display detected chords."""
        self._chords = chords
        self._display_chords(chords)
        self.status_label.setText(
            f"✅ {len(chords)} acordes detectados del audio"
        )
        self.analyze_button.setEnabled(True)
        self.copy_button.setEnabled(True)
        self.count_label.setText(f"{len(chords)} acordes")

        # Start highlight timer if playing
        if self.audio_player:
            self._highlight_timer.start()

        logger.info(f"Displayed {len(chords)} chords")

    def _on_chords_error(self, error: str):
        """Show error message."""
        self.chords_text.setPlainText(
            f"❌ {error}\n\n"
            "Posibles causas:\n"
            "• Archivo de audio no encontrado\n"
            "• Formato no soportado\n"
            "• Librosa no instalado\n\n"
            "Intenta: Click 'Re-analizar'"
        )
        self.status_label.setText(f"❌ {error}")
        self.analyze_button.setEnabled(True)
        self.copy_button.setEnabled(False)
        self.count_label.setText("")

    def _display_chords(self, chords: list):
        """Render chords in the text display."""
        if not chords:
            self.chords_text.setPlainText("No se detectaron acordes.")
            return

        # Build HTML with colored chords
        lines = []
        lines.append(
            '<div style="font-family: Consolas, monospace; font-size: 13pt; '
            'line-height: 2.0;">'
        )

        for i, entry in enumerate(chords):
            t = entry["t"]
            chord = entry["chord"]
            minutes = int(t // 60)
            seconds = int(t % 60)
            timestamp = f"{minutes}:{seconds:02d}"

            # Chord color based on type
            if 'm' in chord and '7' not in chord:
                color = "#e06c75"  # Minor = red-ish
            elif '7' in chord:
                color = "#e5c07b"  # 7th = yellow-ish
            else:
                color = "#61afef"  # Major = blue

            lines.append(
                f'<span id="chord_{i}">'
                f'<span style="color: #888;">[{timestamp}]</span> '
                f'<span style="color: {color}; font-weight: bold; '
                f'font-size: 15pt;">{chord}</span>'
                f'</span><br/>'
            )

        lines.append('</div>')
        self.chords_text.setHtml('\n'.join(lines))

    def _on_transpose(self, semitones: int):
        """Transpose all chords."""
        if not self._chords:
            return

        self._transpose += semitones
        self.transpose_label.setText(
            f"{'+' if self._transpose > 0 else ''}{self._transpose}"
        )

        if self.chords_client:
            transposed = self.chords_client.transpose_chords(
                self._chords, self._transpose
            )
            self._display_chords(transposed)
            self.status_label.setText(
                f"✅ Transpuesto {'+' if self._transpose > 0 else ''}"
                f"{self._transpose} semitonos"
            )

    def _on_transpose_reset(self):
        """Reset transposition to original key."""
        self._transpose = 0
        self.transpose_label.setText("0")
        self._display_chords(self._chords)
        self.status_label.setText("✅ Tonalidad original")

    def _update_current_chord(self):
        """Highlight the chord that's currently playing."""
        if not self.audio_player or not self._chords:
            return

        try:
            position = self.audio_player.get_position()
        except (RuntimeError, OSError):
            return

        # Find the chord at the current position
        chord_idx = -1
        for i, entry in enumerate(self._chords):
            if entry["t"] <= position:
                chord_idx = i
            else:
                break

        if chord_idx != self._current_chord_idx and chord_idx >= 0:
            self._current_chord_idx = chord_idx
            # Scroll to show current chord
            cursor = self.chords_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            # Move down to the right line
            for _ in range(chord_idx):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            self.chords_text.setTextCursor(cursor)
            self.chords_text.ensureCursorVisible()

    def _on_manual_analyze(self):
        """Re-analyze chords for current song."""
        if self.current_song:
            file_path = self.current_song.get('file_path', '')
            song_id = self.current_song.get('id')
            if file_path:
                # Clear cache to force re-analysis
                if self.chords_client and song_id:
                    self.chords_client._cache.pop(song_id, None)
                self._transpose = 0
                self.transpose_label.setText("0")
                self._analyze_chords(file_path, song_id)
            else:
                self.status_label.setText("⚠️ Sin ruta de archivo")
        else:
            self.status_label.setText("⚠️ Reproduce una cancion primero")

    def _on_copy_chords(self):
        """Copy chords to clipboard as text."""
        from PySide6.QtWidgets import QApplication

        if not self._chords:
            self.status_label.setText("⚠️ No hay acordes para copiar")
            return

        # Apply current transposition
        chords = self._chords
        if self._transpose != 0 and self.chords_client:
            chords = self.chords_client.transpose_chords(
                self._chords, self._transpose
            )

        # Format as text
        lines = []
        title = self.current_song.get('title', '') if self.current_song else ''
        artist = self.current_song.get('artist', '') if self.current_song else ''
        if title:
            lines.append(f"{title} - {artist}")
            if self._transpose != 0:
                lines.append(f"(Transpuesto: {self._transpose:+d} semitonos)")
            lines.append("")

        for entry in chords:
            t = entry["t"]
            minutes = int(t // 60)
            seconds = int(t % 60)
            lines.append(f"[{minutes}:{seconds:02d}] {entry['chord']}")

        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(lines))
        self.status_label.setText("✅ Acordes copiados al portapapeles")
