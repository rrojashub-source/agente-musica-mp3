"""
Chord Diagram Widget — Renders guitar chord fingering diagrams

Displays a visual guitar fretboard showing where to place fingers
for a given chord. Uses the tombatossals/chords-db JSON database.

Created: March 2026
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class ChordDiagramWidget(QWidget):
    """
    Renders a guitar chord diagram using QPainter.

    Shows 6 strings, fret positions, finger dots, open/muted strings,
    and barre indicators.
    """

    # Layout constants
    NUM_STRINGS = 6
    NUM_FRETS = 5
    PADDING_TOP = 50
    PADDING_BOTTOM = 20
    PADDING_LEFT = 35
    PADDING_RIGHT = 20

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._chord_db: Optional[Dict[str, Any]] = None
        self._current_chord: Optional[str] = None  # chord name string
        self._current_data: Optional[Dict[str, Any]] = None  # chord position data
        self._chord_name_display: str = ""
        self.setMinimumSize(200, 280)
        self.setMaximumWidth(280)
        self._load_chord_db()

    def _load_chord_db(self) -> None:
        """Load the guitar chord database from JSON."""
        # Try multiple locations
        candidates = [
            Path(__file__).parent.parent.parent.parent / "data" / "chords-db" / "guitar.json",
            Path(__file__).parent.parent.parent / "data" / "chords-db" / "guitar.json",
        ]

        for path in candidates:
            if path.exists():
                try:
                    with open(path, "r") as f:
                        self._chord_db = json.load(f)
                    logger.info(f"Loaded guitar chord DB: {len(self._chord_db.get('chords', {}))} keys")
                    return
                except (json.JSONDecodeError, OSError) as e:
                    logger.error(f"Failed to load chord DB: {e}")

        logger.warning("Guitar chord database not found")

    def set_chord(self, chord_name: str) -> None:
        """
        Set the chord to display.

        Args:
            chord_name: Chord name like "C", "Am", "G7", "F#m", etc.
        """
        if chord_name == self._current_chord:
            return

        self._current_chord = chord_name
        self._chord_name_display = chord_name
        self._current_data = self._lookup_chord(chord_name)

        if not self._current_data:
            logger.debug(f"No diagram found for chord: {chord_name}")

        self.update()  # Trigger repaint

    def _lookup_chord(self, chord_name: str) -> Optional[Dict[str, Any]]:
        """Look up chord fingering data from the database."""
        if not self._chord_db:
            return None

        chords = self._chord_db.get("chords", {})

        # Parse chord name into key + suffix
        key, suffix = self._parse_chord_name(chord_name)
        if not key:
            return None

        # Map key to database key name
        db_key = self._key_to_db_key(key)
        if db_key not in chords:
            logger.debug(f"Key '{db_key}' not in chord DB")
            return None

        # Find matching suffix
        for chord_entry in chords[db_key]:
            if chord_entry.get("suffix") == suffix:
                positions = chord_entry.get("positions", [])
                if positions:
                    return positions[0]  # type: ignore[no-any-return]  # Return first position (most common)
                break

        return None

    @staticmethod
    def _parse_chord_name(name: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse 'Am7' into ('A', 'minor7'), 'C' into ('C', 'major'), etc."""
        if not name or name == "N":
            return None, None

        # Extract root note
        i = 1
        if len(name) > 1 and name[1] in ("#", "b"):
            i = 2
        key = name[:i]
        remainder = name[i:]

        # Map suffix
        suffix_map = {
            "": "major",
            "m": "minor",
            "7": "7",
            "m7": "m7",
            "maj7": "maj7",
            "dim": "dim",
            "aug": "aug",
            "sus2": "sus2",
            "sus4": "sus4",
            "add9": "add9",
            "6": "6",
            "m6": "m6",
            "9": "9",
            "m9": "m9",
        }

        suffix = suffix_map.get(remainder, remainder if remainder else "major")
        return key, suffix

    @staticmethod
    def _key_to_db_key(key: str) -> str:
        """Convert note name to chord DB key format."""
        mapping = {
            "C": "C",
            "C#": "Csharp",
            "Db": "Csharp",
            "D": "D",
            "D#": "Eb",
            "Eb": "Eb",
            "E": "E",
            "F": "F",
            "F#": "Fsharp",
            "Gb": "Fsharp",
            "G": "G",
            "G#": "Ab",
            "Ab": "Ab",
            "A": "A",
            "A#": "Bb",
            "Bb": "Bb",
            "B": "B",
        }
        return mapping.get(key, key)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Render the chord diagram."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor("#1e1e2e"))

        # Draw chord name
        painter.setPen(QColor("#cdd6f4"))
        name_font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        painter.setFont(name_font)
        painter.drawText(QRectF(0, 5, w, 35), Qt.AlignmentFlag.AlignCenter, self._chord_name_display or "—")

        if not self._current_data:
            # No data — show message
            painter.setPen(QColor("#6c7086"))
            msg_font = QFont("Segoe UI", 10)
            painter.setFont(msg_font)
            painter.drawText(
                QRectF(0, h // 2 - 20, w, 40),
                Qt.AlignmentFlag.AlignCenter,
                "Sin diagrama" if self._current_chord else "Selecciona un acorde",
            )
            painter.end()
            return

        frets_data = self._current_data.get("frets", [])
        fingers = self._current_data.get("fingers", [])
        barres = self._current_data.get("barres", [])
        base_fret = self._current_data.get("baseFret", 1)

        # Calculate dimensions
        fretboard_x = self.PADDING_LEFT
        fretboard_y = self.PADDING_TOP
        fretboard_w = w - self.PADDING_LEFT - self.PADDING_RIGHT
        fretboard_h = h - self.PADDING_TOP - self.PADDING_BOTTOM
        string_spacing = fretboard_w / (self.NUM_STRINGS - 1)
        fret_spacing = fretboard_h / self.NUM_FRETS

        # Draw nut (thick line at top if base fret = 1)
        if base_fret == 1:
            painter.setPen(QPen(QColor("#cdd6f4"), 4))
            painter.drawLine(int(fretboard_x), int(fretboard_y), int(fretboard_x + fretboard_w), int(fretboard_y))
        else:
            # Show base fret number
            painter.setPen(QColor("#a6adc8"))
            fret_font = QFont("Segoe UI", 10)
            painter.setFont(fret_font)
            painter.drawText(int(fretboard_x - 25), int(fretboard_y + fret_spacing / 2 + 5), f"{base_fret}fr")

        # Draw fret lines
        painter.setPen(QPen(QColor("#585b70"), 1))
        for i in range(self.NUM_FRETS + 1):
            y = fretboard_y + i * fret_spacing
            painter.drawLine(int(fretboard_x), int(y), int(fretboard_x + fretboard_w), int(y))

        # Draw strings
        painter.setPen(QPen(QColor("#7f849c"), 1))
        for i in range(self.NUM_STRINGS):
            x = fretboard_x + i * string_spacing
            painter.drawLine(int(x), int(fretboard_y), int(x), int(fretboard_y + fretboard_h))

        # Draw barres
        if barres:
            for barre_fret in barres:
                barre_y = fretboard_y + (barre_fret - 0.5) * fret_spacing
                # Find first and last string in barre
                first_str = 0
                last_str = self.NUM_STRINGS - 1
                for s_idx, f in enumerate(frets_data):
                    if f == barre_fret:
                        first_str = s_idx
                        break
                for s_idx in range(self.NUM_STRINGS - 1, -1, -1):
                    if frets_data[s_idx] >= barre_fret:
                        last_str = s_idx

                x1 = fretboard_x + first_str * string_spacing
                x2 = fretboard_x + last_str * string_spacing
                painter.setPen(QPen(QColor("#89b4fa"), 3))
                painter.setBrush(QBrush(QColor(137, 180, 250, 100)))
                painter.drawRoundedRect(QRectF(x1 - 6, barre_y - 8, x2 - x1 + 12, 16), 8, 8)

        # Draw finger positions
        dot_radius = min(string_spacing, fret_spacing) * 0.3
        for string_idx, fret_val in enumerate(frets_data):
            x = fretboard_x + string_idx * string_spacing

            if fret_val == -1:
                # Muted string (X)
                painter.setPen(QPen(QColor("#f38ba8"), 2))
                size = 8
                cx = x
                cy = fretboard_y - 15
                painter.drawLine(int(cx - size), int(cy - size), int(cx + size), int(cy + size))
                painter.drawLine(int(cx - size), int(cy + size), int(cx + size), int(cy - size))

            elif fret_val == 0:
                # Open string (O)
                painter.setPen(QPen(QColor("#a6e3a1"), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QRectF(x - 7, fretboard_y - 22, 14, 14))

            else:
                # Fretted note (filled circle)
                y = fretboard_y + (fret_val - 0.5) * fret_spacing
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor("#89b4fa")))
                painter.drawEllipse(QRectF(x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2))

                # Draw finger number
                if fingers and string_idx < len(fingers) and fingers[string_idx] > 0:
                    painter.setPen(QColor("#1e1e2e"))
                    finger_font = QFont("Segoe UI", 8, QFont.Weight.Bold)
                    painter.setFont(finger_font)
                    painter.drawText(
                        QRectF(x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2),
                        Qt.AlignmentFlag.AlignCenter,
                        str(fingers[string_idx]),
                    )

        # Draw string labels at bottom (E A D G B E)
        string_names = ["E", "A", "D", "G", "B", "E"]
        painter.setPen(QColor("#6c7086"))
        label_font = QFont("Segoe UI", 8)
        painter.setFont(label_font)
        for i, name in enumerate(string_names):
            x = fretboard_x + i * string_spacing
            painter.drawText(QRectF(x - 10, fretboard_y + fretboard_h + 3, 20, 15), Qt.AlignmentFlag.AlignCenter, name)

        painter.end()

    def clear(self) -> None:
        """Clear the current chord display."""
        self._current_chord = None
        self._current_data = None
        self._chord_name_display = ""
        self.update()
