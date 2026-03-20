"""
Album Grid Widget - Visual album browser with cover art

Displays albums in a responsive grid layout with cover art thumbnails.
Features:
- Cover art display (from embedded or folder images)
- Responsive grid that adapts to window size
- Click to expand album details
- Smooth scrolling
- Dark/light theme support

Created: November 23, 2025
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPixmap, QResizeEvent
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from core.cover_art_manager import CoverArtManager
from gui.themes.style_constants import Styles
from utils.constants import DEFAULT_ALBUM, DEFAULT_ARTIST

logger = logging.getLogger(__name__)


class AlbumCard(QFrame):
    """Single album card with cover art and info"""

    clicked = Signal(dict)  # Emits album data when clicked

    CARD_WIDTH = 160
    CARD_HEIGHT = 200
    COVER_SIZE = 140

    def __init__(
        self, album_data: Dict[str, Any], cover_manager: CoverArtManager, parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize album card

        Args:
            album_data: Dict with album, artist, song_count, cover_path keys
            cover_manager: CoverArtManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.album_data: Dict[str, Any] = album_data
        self.cover_manager: CoverArtManager = cover_manager

        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._init_ui()
        self._apply_style()

    def _init_ui(self) -> None:
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Cover art
        self.cover_label: QLabel = QLabel()
        self.cover_label.setFixedSize(self.COVER_SIZE, self.COVER_SIZE)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setScaledContents(False)
        layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Load cover art
        self._load_cover()

        # Album name
        album_name = self.album_data.get("album", DEFAULT_ALBUM)
        if len(album_name) > 18:
            album_name = album_name[:16] + "..."
        self.album_label = QLabel(album_name)
        self.album_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_label.setStyleSheet(Styles.LABEL_BOLD)
        self.album_label.setToolTip(self.album_data.get("album", DEFAULT_ALBUM))
        layout.addWidget(self.album_label)

        # Artist name
        artist_name = self.album_data.get("artist", DEFAULT_ARTIST)
        if len(artist_name) > 20:
            artist_name = artist_name[:18] + "..."
        self.artist_label = QLabel(artist_name)
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artist_label.setStyleSheet(Styles.LABEL_TINY_FADED)
        self.artist_label.setToolTip(self.album_data.get("artist", DEFAULT_ARTIST))
        layout.addWidget(self.artist_label)

        # Song count
        song_count = self.album_data.get("song_count", 0)
        self.count_label = QLabel(f"{song_count} songs")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet(Styles.LABEL_TINY_FAINT)
        layout.addWidget(self.count_label)

    def _load_cover(self) -> None:
        """Load cover art for the album"""
        pixmap = None

        # Try to get cover from cover manager
        artist = self.album_data.get("artist", DEFAULT_ARTIST)
        album = self.album_data.get("album", DEFAULT_ALBUM)

        # Check if cover exists in cache
        if self.cover_manager.has_cover(artist, album):
            cover_path = self.cover_manager.get_cover_path(artist, album)
            if cover_path.exists():
                pixmap = QPixmap(str(cover_path))

        # If no cached cover, try to extract from sample file
        if not pixmap or pixmap.isNull():
            sample_file = self.album_data.get("sample_file")
            if sample_file and Path(sample_file).exists():
                pixmap = self._extract_cover_from_file(sample_file)

        # Apply pixmap or default
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.COVER_SIZE,
                self.COVER_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.cover_label.setPixmap(scaled)
        else:
            # Default album art
            self._set_default_cover()

    def _extract_cover_from_file(self, file_path: str) -> Optional[QPixmap]:
        """Extract cover art from audio file using mutagen"""
        try:
            from utils.mutagen_compat import MutagenFile as File, APIC

            audio = File(file_path)
            if audio is None:
                return None

            # Handle MP3 (ID3 tags)
            if hasattr(audio, "tags") and audio.tags:
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        # APIC frame contains the image
                        image_data = tag.data  # type: ignore[attr-defined]
                        image = QImage()
                        if image.loadFromData(image_data):
                            return QPixmap.fromImage(image)

            # Handle M4A/MP4
            if isinstance(audio, type(audio)) and hasattr(audio, "get"):
                covers = audio.get("covr", [])
                if covers:
                    image_data = bytes(covers[0])
                    image = QImage()
                    if image.loadFromData(image_data):
                        return QPixmap.fromImage(image)

        except Exception as e:  # mutagen raises diverse errors on corrupt/unknown audio formats
            logger.debug(f"Failed to extract cover from {file_path}: {e}")

        return None

    def _set_default_cover(self) -> None:
        """Set default album cover (gradient placeholder)"""
        size = self.COVER_SIZE
        image = QImage(size, size, QImage.Format.Format_RGB32)
        painter = QPainter(image)

        # Create gradient based on album name hash for variety
        album_name = self.album_data.get("album", "Unknown")
        hash_val = hash(album_name) % 360

        # Gradient colors
        color1 = QColor.fromHsv(hash_val, 120, 80)
        color2 = QColor.fromHsv((hash_val + 30) % 360, 100, 60)

        painter.fillRect(0, 0, size, size, color1)
        painter.fillRect(0, size // 2, size, size // 2, color2)

        # Draw music note icon
        painter.setPen(QColor(255, 255, 255, 180))
        font = painter.font()
        font.setPointSize(48)
        painter.setFont(font)
        painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "♪")

        painter.end()

        self.cover_label.setPixmap(QPixmap.fromImage(image))

    def _apply_style(self) -> None:
        """Apply card styling"""
        self.setStyleSheet(
            """
            AlbumCard {
                background-color: #2d2d2d;
                border-radius: 8px;
                border: 1px solid #3d3d3d;
            }
            AlbumCard:hover {
                background-color: #3d3d3d;
                border: 1px solid #0af;
            }
        """
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.album_data)
        super().mousePressEvent(event)


class AlbumGridWidget(QWidget):
    """
    Grid widget displaying all albums with cover art

    Signals:
        album_selected: Emitted when an album is clicked (album_data dict)
    """

    album_selected = Signal(dict)

    def __init__(self, db_manager: Any, parent: Optional[QWidget] = None) -> None:
        """
        Initialize album grid

        Args:
            db_manager: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager: Any = db_manager
        self.cover_manager: CoverArtManager = CoverArtManager()
        self._album_cards: List[AlbumCard] = []

        self._init_ui()
        self._load_albums()

        logger.info("AlbumGridWidget initialized")

    def _init_ui(self) -> None:
        """Initialize UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("📀 Albums")
        title_label.setStyleSheet(Styles.SECTION_TITLE)
        header_layout.addWidget(title_label)

        self.count_label = QLabel("0 albums")
        self.count_label.setStyleSheet(Styles.LABEL_SMALL_MUTED)
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._load_albums)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        # Scroll area for grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background: transparent;
            }
        """
        )

        # Container widget for grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)

        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)

    def _load_albums(self) -> None:
        """Load albums from database and populate grid"""
        # Clear existing cards
        for card in self._album_cards:
            card.deleteLater()
        self._album_cards.clear()

        # Clear layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get albums from database
        albums = self._get_albums_from_db()

        if not albums:
            # Show empty message
            empty_label = QLabel("No albums found.\nImport music to see albums here.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(Styles.FALLBACK_LABEL)
            self.grid_layout.addWidget(empty_label, 0, 0)
            self.count_label.setText("0 albums")
            return

        # Calculate columns based on width
        available_width = self.scroll_area.viewport().width()
        card_width = AlbumCard.CARD_WIDTH + 12  # card + spacing
        columns = max(1, available_width // card_width)

        # Create album cards
        row = 0
        col = 0

        for album_data in albums:
            card = AlbumCard(album_data, self.cover_manager)
            card.clicked.connect(self._on_album_clicked)

            self.grid_layout.addWidget(card, row, col)
            self._album_cards.append(card)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        # Update count
        self.count_label.setText(f"{len(albums)} albums")

        logger.info(f"Loaded {len(albums)} albums into grid")

    def _get_albums_from_db(self) -> List[Dict[str, Any]]:
        """Get unique albums from database with cover art info"""
        try:
            # Query unique albums with song counts
            query = """
                SELECT
                    TRIM(album) as album,
                    TRIM(artist) as artist,
                    COUNT(*) as song_count,
                    MIN(file_path) as sample_file
                FROM songs
                WHERE album IS NOT NULL
                  AND TRIM(album) != ''
                  AND LOWER(TRIM(album)) NOT IN ('unknown', 'unknown album')
                GROUP BY LOWER(TRIM(album)), LOWER(TRIM(artist))
                ORDER BY album ASC
            """

            # Use public fetch_all method instead of private _get_connection
            rows = self.db_manager.fetch_all(query)

            albums = []
            for row in rows:
                albums.append(
                    {
                        "album": row["album"] if isinstance(row, dict) else row[0],
                        "artist": row["artist"] if isinstance(row, dict) else row[1],
                        "song_count": row["song_count"] if isinstance(row, dict) else row[2],
                        "sample_file": row["sample_file"] if isinstance(row, dict) else row[3],
                        "cover_path": None,  # Will be loaded dynamically
                    }
                )

            return albums

        except Exception as e:  # DB query errors - return empty list gracefully
            logger.error(f"Error loading albums: {e}")
            return []

    def _on_album_clicked(self, album_data: Dict[str, Any]) -> None:
        """Handle album card click"""
        logger.info(f"Album clicked: {album_data.get('album')} by {album_data.get('artist')}")
        self.album_selected.emit(album_data)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize - recalculate grid columns"""
        super().resizeEvent(event)
        # Debounce resize by using timer would be better,
        # but for now just reload on significant changes
        if self._album_cards:
            self._rearrange_grid()

    def _rearrange_grid(self) -> None:
        """Rearrange grid based on current width"""
        available_width = self.scroll_area.viewport().width()
        card_width = AlbumCard.CARD_WIDTH + 12
        columns = max(1, available_width // card_width)

        # Rearrange existing cards
        row = 0
        col = 0

        for card in self._album_cards:
            self.grid_layout.removeWidget(card)
            self.grid_layout.addWidget(card, row, col)

            col += 1
            if col >= columns:
                col = 0
                row += 1

    def refresh(self) -> None:
        """Public method to refresh album grid"""
        self._load_albums()
