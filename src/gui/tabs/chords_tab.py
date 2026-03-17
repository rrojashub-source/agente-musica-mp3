"""
Chords Tab — Display detected chords for the current song

Features:
- Auto-detect chords when song changes (background worker)
- Timeline display with clickable chord names
- Guitar chord diagram widget (click a chord to see fingering)
- Transpose controls (+/- semitone)
- Current chord highlight synchronized with playback
- Color legend (Major / Minor / 7th)
- Cache results for instant re-display

Created: March 2026
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
)

from gui.base import BaseTab
from gui.base.base_worker import BaseWorker
from gui.themes.style_constants import Styles
from gui.widgets.chord_diagram_widget import ChordDiagramWidget
from utils.constants import DEFAULT_ARTIST

logger = logging.getLogger(__name__)


class ChordsAnalyzeWorker(BaseWorker):
    """Background worker for chord analysis (non-blocking)."""

    # Override progress signal: single str instead of BaseWorker's (int, str)
    progress = Signal(str)

    def __init__(self, chords_client: Any, file_path: str, song_id: Optional[int] = None) -> None:
        super().__init__()
        self.chords_client: Any = chords_client
        self.file_path: str = file_path
        self.song_id: Optional[int] = song_id

    def do_work(self) -> Any:
        self.progress.emit("Analizando audio...")
        chords = self.chords_client.get_chords(self.file_path, song_id=self.song_id)
        if chords:
            return chords
        else:
            self.error.emit("No se pudieron detectar acordes")
            return None


class ChordsTab(BaseTab):
    """
    Tab for displaying detected song chords with guitar diagrams.

    Shows a timeline of chords detected from the audio,
    with transpose controls, clickable chord names that display
    guitar fingering diagrams, and current-chord highlighting.
    """

    # YouTube title noise patterns to strip for cleaner display
    _NOISE_PATTERNS = [
        r"\s*[\(\[](Official\s*)?(Music\s*)?Video[\)\]]",
        r"\s*[\(\[]Official\s*Audio[\)\]]",
        r"\s*[\(\[]Audio[\)\]]",
        r"\s*[\(\[]Lyric[s]?\s*Video[\)\]]",
        r"\s*[\(\[]Visuali[zs]er[\)\]]",
        r"\s*[\(\[]Live[\)\]]",
        r"\s*[\(\[](HD|HQ)[\)\]]",
        r"\s*[\(\[]Remaster(ed)?[\)\]]",
    ]

    def __init__(self, chords_client: Any = None, audio_player: Any = None) -> None:
        self.chords_client: Any = chords_client
        self.audio_player: Any = audio_player
        self.current_song: Optional[Dict[str, Any]] = None
        self._worker: Optional[ChordsAnalyzeWorker] = None
        self._chords: List[Dict[str, Any]] = []  # Original chord list
        self._displayed_chords: List[Dict[str, Any]] = []  # Currently displayed (possibly transposed)
        self._transpose: int = 0
        self._current_chord_idx: int = -1
        super().__init__(db_manager=None, parent=None)

        # Timer for highlighting current chord during playback
        self._highlight_timer = QTimer()
        self._highlight_timer.setInterval(250)
        self._highlight_timer.timeout.connect(self._update_current_chord)

        logger.info("ChordsTab initialized")

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # ===== Header =====
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)

        self.header_label = QLabel("🎸 No hay cancion reproduciendo")
        self.header_label.setStyleSheet(Styles.LABEL_16PT_BOLD)
        self.header_label.setWordWrap(True)
        header_layout.addWidget(self.header_label)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(Styles.LABEL_10PT)
        self.status_label.setProperty("class", "secondary")
        header_layout.addWidget(self.status_label)

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        # ===== Controls Row =====
        controls_frame = QFrame()
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(5, 5, 5, 5)

        # Transpose controls
        controls_layout.addWidget(QLabel("Transponer:"))

        self.transpose_down_btn = QPushButton("- 1")
        self.transpose_down_btn.setFixedWidth(50)
        self.transpose_down_btn.setToolTip("Bajar medio tono")
        self.transpose_down_btn.clicked.connect(lambda: self._on_transpose(-1))
        controls_layout.addWidget(self.transpose_down_btn)

        self.transpose_label = QLabel("0")
        self.transpose_label.setFixedWidth(30)
        self.transpose_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transpose_label.setStyleSheet(Styles.LABEL_BOLD_PT)
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

        controls_layout.addSpacing(20)

        # Color legend
        legend = QLabel(
            '<span style="color: #61afef;">&#9632;</span> Mayor &nbsp; '
            '<span style="color: #e06c75;">&#9632;</span> Menor &nbsp; '
            '<span style="color: #e5c07b;">&#9632;</span> 7ma'
        )
        legend.setStyleSheet(Styles.LABEL_9PT)
        controls_layout.addWidget(legend)

        controls_layout.addStretch()

        # Instrument selector
        controls_layout.addWidget(QLabel("Instrumento:"))
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems(["Guitarra"])
        self.instrument_combo.setToolTip("Diagrama de acordes")
        controls_layout.addWidget(self.instrument_combo)

        controls_frame.setLayout(controls_layout)
        layout.addWidget(controls_frame)

        # ===== Main Content: Splitter (Chords Timeline + Diagram) =====
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Clickable chord timeline
        self.chords_text = QTextBrowser()
        self.chords_text.setReadOnly(True)
        self.chords_text.setOpenExternalLinks(False)
        self.chords_text.setOpenLinks(False)
        self.chords_text.anchorClicked.connect(self._on_chord_clicked)
        self.chords_text.setPlaceholderText(
            "🎸 Reproduce una cancion para detectar acordes...\n\n"
            "Los acordes se analizan automaticamente del audio.\n"
            "Haz click en un acorde para ver el diagrama de guitarra."
        )

        font = QFont("Consolas", 13)
        if not font.exactMatch():
            font = QFont("Courier New", 13)
        self.chords_text.setFont(font)
        self.chords_text.setStyleSheet("QTextBrowser { padding: 15px; }")

        self.splitter.addWidget(self.chords_text)

        # Right: Guitar chord diagram
        self.chord_diagram = ChordDiagramWidget()
        self.splitter.addWidget(self.chord_diagram)

        # 75% chords, 25% diagram
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter, 1)

        # ===== Bottom Controls =====
        bottom_layout = QHBoxLayout()

        self.analyze_button = QPushButton("🔄 Re-analizar")
        self.analyze_button.setToolTip("Analizar acordes de nuevo (ignora cache)")
        self.analyze_button.clicked.connect(self._on_manual_analyze)
        self.analyze_button.setStyleSheet(Styles.BTN_ACTION)
        bottom_layout.addWidget(self.analyze_button)

        self.copy_button = QPushButton("📋 Copiar Acordes")
        self.copy_button.setToolTip("Copiar acordes al portapapeles")
        self.copy_button.clicked.connect(self._on_copy_chords)
        self.copy_button.setEnabled(False)
        self.copy_button.setStyleSheet(Styles.BTN_ACTION)
        bottom_layout.addWidget(self.copy_button)

        bottom_layout.addStretch()

        self.count_label = QLabel("")
        self.count_label.setProperty("class", "muted")
        bottom_layout.addWidget(self.count_label)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    # ===== Song Events =====

    def on_song_changed(self, song_info: Dict[str, Any]) -> None:
        """Called when a new song starts playing."""
        self.current_song = song_info
        self._transpose = 0
        self.transpose_label.setText("0")
        self._current_chord_idx = -1
        self.chord_diagram.clear()

        title = song_info.get("title", "Unknown")
        artist = song_info.get("artist", DEFAULT_ARTIST)
        clean_title = self._clean_display_title(title, artist)
        self.header_label.setText(f"🎸 {clean_title} — {artist}")

        file_path = song_info.get("file_path", "")
        song_id = song_info.get("id")

        if file_path:
            self._analyze_chords(file_path, song_id)
        else:
            self.status_label.setText("⚠️ Sin ruta de archivo")

    @staticmethod
    def _clean_display_title(title: str, artist: str) -> str:
        """Strip YouTube noise from title for cleaner display."""
        cleaned = title.strip()

        # Strip "Artist - " prefix
        if artist:
            prefix = re.compile(r"^" + re.escape(artist.strip()) + r"\s*[-\u2013\u2014:]\s*", re.IGNORECASE)
            cleaned = prefix.sub("", cleaned)

        # Strip noise suffixes
        for pattern in ChordsTab._NOISE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        return cleaned.strip() or title

    # ===== Analysis =====

    def _analyze_chords(self, file_path: str, song_id: Optional[int] = None) -> None:
        """Start background chord analysis."""
        if not self.chords_client:
            self.chords_text.setPlainText(
                "❌ Servicio de acordes no disponible\n\n" "Requiere: pip install librosa pychord"
            )
            self.status_label.setText("⚠️ Librosa no instalado")
            return

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

        self._worker = ChordsAnalyzeWorker(self.chords_client, file_path, song_id)
        self._worker.finished.connect(self._on_chords_found)
        self._worker.error.connect(self._on_chords_error)
        self._worker.progress.connect(lambda msg: self.status_label.setText(f"🔍 {msg}"))
        self._worker.start()

    def _on_chords_found(self, chords: List[Dict[str, Any]]) -> None:
        """Display detected chords."""
        self._chords = chords
        self._displayed_chords = chords
        self._render_chords(chords)
        self.status_label.setText(f"✅ {len(chords)} acordes detectados")
        self.analyze_button.setEnabled(True)
        self.copy_button.setEnabled(True)
        self.count_label.setText(f"{len(chords)} acordes")

        # Show first chord on the diagram
        if chords:
            self.chord_diagram.set_chord(chords[0]["chord"])

        # Start highlight timer if playing
        if self.audio_player:
            self._highlight_timer.start()

        logger.info(f"Displayed {len(chords)} chords")

    def _on_chords_error(self, error: str) -> None:
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

    # ===== Display =====

    def _render_chords(self, chords: List[Dict[str, Any]]) -> None:
        """Render chords as clickable HTML in the text browser."""
        if not chords:
            self.chords_text.setPlainText("No se detectaron acordes.")
            return

        lines = ['<div style="font-family: Consolas, monospace; font-size: 13pt; ' 'line-height: 2.0;">']

        for i, entry in enumerate(chords):
            t = entry["t"]
            chord = entry["chord"]
            minutes = int(t // 60)
            seconds = int(t % 60)
            timestamp = f"{minutes}:{seconds:02d}"

            # Color by chord type
            if "m" in chord and "7" not in chord:
                color = "#e06c75"  # Minor (red)
            elif "7" in chord:
                color = "#e5c07b"  # 7th (yellow)
            else:
                color = "#61afef"  # Major (blue)

            # Clickable chord — href uses index to avoid URL encoding issues with #
            lines.append(
                f'<span style="color: #888;">[{timestamp}]</span> '
                f'<a href="chord://{i}" style="color: {color}; font-weight: bold; '
                f'font-size: 15pt; text-decoration: none;">'
                f"{chord}</a><br/>"
            )

        lines.append("</div>")
        self.chords_text.setHtml("\n".join(lines))

    def _on_chord_clicked(self, url: QUrl) -> None:
        """Handle click on a chord name — show its guitar diagram."""
        text = url.toString()
        if text.startswith("chord://"):
            try:
                idx = int(text[8:])
                if 0 <= idx < len(self._displayed_chords):
                    chord_name = self._displayed_chords[idx]["chord"]
                    self.chord_diagram.set_chord(chord_name)
            except (ValueError, IndexError):
                pass

    # ===== Transpose =====

    def _on_transpose(self, semitones: int) -> None:
        """Transpose all chords by N semitones."""
        if not self._chords:
            return

        self._transpose += semitones
        self.transpose_label.setText(f"{'+' if self._transpose > 0 else ''}{self._transpose}")

        if self.chords_client:
            transposed = self.chords_client.transpose_chords(self._chords, self._transpose)
            self._displayed_chords = transposed
            self._render_chords(transposed)
            self.status_label.setText(
                f"✅ Transpuesto {'+' if self._transpose > 0 else ''}" f"{self._transpose} semitonos"
            )

            # Update diagram with current chord in new key
            if 0 <= self._current_chord_idx < len(transposed):
                self.chord_diagram.set_chord(transposed[self._current_chord_idx]["chord"])

    def _on_transpose_reset(self) -> None:
        """Reset transposition to original key."""
        self._transpose = 0
        self.transpose_label.setText("0")
        self._displayed_chords = self._chords
        self._render_chords(self._chords)
        self.status_label.setText("✅ Tonalidad original")

        if 0 <= self._current_chord_idx < len(self._chords):
            self.chord_diagram.set_chord(self._chords[self._current_chord_idx]["chord"])

    # ===== Playback Sync =====

    def _update_current_chord(self) -> None:
        """Highlight current chord and update diagram during playback."""
        if not self.audio_player or not self._displayed_chords:
            return

        try:
            position = self.audio_player.get_position()
        except (RuntimeError, OSError):
            return

        # Find chord at current position (use original timestamps)
        chord_idx = -1
        for i, entry in enumerate(self._chords):
            if entry["t"] <= position:
                chord_idx = i
            else:
                break

        if chord_idx != self._current_chord_idx and chord_idx >= 0:
            self._current_chord_idx = chord_idx

            # Update guitar diagram
            if chord_idx < len(self._displayed_chords):
                self.chord_diagram.set_chord(self._displayed_chords[chord_idx]["chord"])

            # Scroll to current chord
            cursor = self.chords_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(chord_idx):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            self.chords_text.setTextCursor(cursor)
            self.chords_text.ensureCursorVisible()

    # ===== Actions =====

    def _on_manual_analyze(self) -> None:
        """Re-analyze chords (clears all caches)."""
        if self.current_song:
            file_path = self.current_song.get("file_path", "")
            song_id = self.current_song.get("id")
            if file_path:
                # Clear memory + DB cache to force re-analysis
                if self.chords_client and song_id:
                    self.chords_client._cache.pop(song_id, None)
                    self._clear_db_cache(song_id)
                self._transpose = 0
                self.transpose_label.setText("0")
                self.chord_diagram.clear()
                self._analyze_chords(file_path, song_id)
            else:
                self.status_label.setText("⚠️ Sin ruta de archivo")
        else:
            self.status_label.setText("⚠️ Reproduce una cancion primero")

    def _clear_db_cache(self, song_id: int) -> None:
        """Clear cached chords from database for a specific song."""
        if self.chords_client and self.chords_client.db_manager:
            try:
                self.chords_client.db_manager.execute_query("UPDATE songs SET chords = NULL WHERE id = ?", (song_id,))
                logger.debug(f"Cleared DB chord cache for song {song_id}")
            except (OSError, ValueError) as e:
                logger.debug(f"Could not clear DB chord cache: {e}")

    def _on_copy_chords(self) -> None:
        """Copy chords to clipboard as plain text."""
        if not self._chords:
            self.status_label.setText("⚠️ No hay acordes para copiar")
            return

        chords = self._displayed_chords or self._chords

        lines = []
        if self.current_song:
            title = self.current_song.get("title", "")
            artist = self.current_song.get("artist", "")
            if title:
                clean = self._clean_display_title(title, artist)
                lines.append(f"{clean} - {artist}")
                if self._transpose != 0:
                    lines.append(f"(Transpuesto: {self._transpose:+d} semitonos)")
                lines.append("")

        for entry in chords:
            t = entry["t"]
            minutes = int(t // 60)
            seconds = int(t % 60)
            lines.append(f"[{minutes}:{seconds:02d}] {entry['chord']}")

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(lines))
        self.status_label.setText("✅ Acordes copiados al portapapeles")
