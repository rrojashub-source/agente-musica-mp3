"""
Statistics Tab - Analytics Dashboard for Music Library

Visual dashboard showing listening statistics and library analytics.

Features:
- Library overview (total songs, artists, albums)
- Top charts (artists, songs, genres)
- Listening trends
- Decade breakdown
- Quality distribution
- Metadata completeness

Created: December 11, 2025
"""
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QScrollArea, QFrame, QProgressBar,
    QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from services.statistics_service import StatisticsService

logger = logging.getLogger(__name__)


class StatCard(QFrame):
    """Card widget for displaying a single statistic"""

    def __init__(self, title: str, value: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            StatCard {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(title_label)

        # Value
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: #333;")
        layout.addWidget(value_label)

        # Subtitle
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("color: #888; font-size: 10px;")
            layout.addWidget(sub_label)

        self.value_label = value_label
        self.subtitle_label = sub_label if subtitle else None

    def update_value(self, value: str, subtitle: str = None):
        """Update the displayed value"""
        self.value_label.setText(value)
        if subtitle and self.subtitle_label:
            self.subtitle_label.setText(subtitle)


class TopListWidget(QGroupBox):
    """Widget for displaying a top list (artists, songs, etc.)"""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)

        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        # Make table stretch
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

    def set_data(self, headers: list, rows: list):
        """Set table data"""
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(headers)

        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if j > 0:  # Right-align numbers
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, j, item)


class StatisticsTab(QWidget):
    """
    Statistics Dashboard Tab

    Displays comprehensive analytics about the music library.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)

        self.db_manager = db_manager
        self.stats_service = StatisticsService(db_manager)

        self._init_ui()

        # Auto-refresh on first show
        QTimer.singleShot(100, self.refresh_stats)

    def _init_ui(self):
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for dashboard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # === Header ===
        header_layout = QHBoxLayout()

        title = QLabel("Library Statistics")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_stats)
        header_layout.addWidget(refresh_btn)

        content_layout.addLayout(header_layout)

        # === Overview Cards ===
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        self.total_songs_card = StatCard("Total Songs", "0", "in library")
        self.total_artists_card = StatCard("Artists", "0", "unique")
        self.total_albums_card = StatCard("Albums", "0", "unique")
        self.total_duration_card = StatCard("Total Duration", "0h", "of music")
        self.total_plays_card = StatCard("Total Plays", "0", "all time")

        for card in [self.total_songs_card, self.total_artists_card,
                     self.total_albums_card, self.total_duration_card,
                     self.total_plays_card]:
            cards_layout.addWidget(card)

        content_layout.addLayout(cards_layout)

        # === Top Charts Row ===
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)

        # Top Artists
        self.top_artists_widget = TopListWidget("Top Artists")
        charts_layout.addWidget(self.top_artists_widget)

        # Top Songs
        self.top_songs_widget = TopListWidget("Most Played Songs")
        charts_layout.addWidget(self.top_songs_widget)

        content_layout.addLayout(charts_layout)

        # === Genre & Decades Row ===
        genre_decade_layout = QHBoxLayout()
        genre_decade_layout.setSpacing(15)

        # Top Genres
        self.top_genres_widget = TopListWidget("Top Genres")
        genre_decade_layout.addWidget(self.top_genres_widget)

        # Decades
        self.decades_widget = TopListWidget("Songs by Decade")
        genre_decade_layout.addWidget(self.decades_widget)

        content_layout.addLayout(genre_decade_layout)

        # === Quality & Metadata Row ===
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(15)

        # Quality Distribution
        self.quality_widget = TopListWidget("Audio Quality Distribution")
        quality_layout.addWidget(self.quality_widget)

        # Metadata Completeness
        self.metadata_group = QGroupBox("Metadata Completeness")
        metadata_layout = QVBoxLayout(self.metadata_group)
        self.metadata_bars = {}

        for field in ['artist', 'album', 'year', 'genre', 'duration', 'bitrate']:
            row = QHBoxLayout()
            label = QLabel(field.capitalize())
            label.setMinimumWidth(80)
            row.addWidget(label)

            bar = QProgressBar()
            bar.setMaximum(100)
            bar.setValue(0)
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            row.addWidget(bar)

            metadata_layout.addLayout(row)
            self.metadata_bars[field] = bar

        quality_layout.addWidget(self.metadata_group)

        content_layout.addLayout(quality_layout)

        # === Recent Activity Row ===
        recent_layout = QHBoxLayout()
        recent_layout.setSpacing(15)

        # Recently Added
        self.recent_added_widget = TopListWidget("Recently Added")
        recent_layout.addWidget(self.recent_added_widget)

        # Recently Played
        self.recent_played_widget = TopListWidget("Recently Played")
        recent_layout.addWidget(self.recent_played_widget)

        content_layout.addLayout(recent_layout)

        # Add stretch at bottom
        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def refresh_stats(self):
        """Refresh all statistics"""
        try:
            logger.info("Refreshing statistics...")

            # Get all stats
            stats = self.stats_service.get_summary_stats()

            # Update overview cards
            overview = stats.get('overview', {})
            self.total_songs_card.update_value(
                f"{overview.get('total_songs', 0):,}",
                "in library"
            )
            self.total_artists_card.update_value(
                f"{overview.get('total_artists', 0):,}",
                "unique"
            )
            self.total_albums_card.update_value(
                f"{overview.get('total_albums', 0):,}",
                "unique"
            )

            hours = overview.get('total_duration_hours', 0)
            if hours >= 24:
                self.total_duration_card.update_value(
                    f"{hours/24:.1f}d",
                    f"({hours:.0f} hours)"
                )
            else:
                self.total_duration_card.update_value(
                    f"{hours:.1f}h",
                    "of music"
                )

            self.total_plays_card.update_value(
                f"{overview.get('total_plays', 0):,}",
                "all time"
            )

            # Update top artists
            top_artists = stats.get('top_artists', [])
            self.top_artists_widget.set_data(
                ['Artist', 'Songs', 'Plays'],
                [[a['artist'], a['song_count'], a['total_plays']] for a in top_artists]
            )

            # Update top songs
            top_songs = stats.get('top_songs', [])
            self.top_songs_widget.set_data(
                ['Song', 'Artist', 'Plays'],
                [[s['title'], s['artist'], s['play_count']] for s in top_songs]
            )

            # Update top genres
            top_genres = stats.get('top_genres', [])
            self.top_genres_widget.set_data(
                ['Genre', 'Songs', 'Plays'],
                [[g['genre'], g['song_count'], g['total_plays']] for g in top_genres]
            )

            # Update decades
            decades = stats.get('decades', [])
            self.decades_widget.set_data(
                ['Decade', 'Songs', 'Plays'],
                [[d['decade'], d['song_count'], d['total_plays']] for d in decades]
            )

            # Update quality distribution
            quality = stats.get('quality', [])
            self.quality_widget.set_data(
                ['Quality', 'Songs', 'Avg Bitrate'],
                [[q['quality'], q['song_count'], f"{q['avg_bitrate']} kbps"] for q in quality]
            )

            # Update metadata completeness
            metadata = stats.get('metadata', {})
            fields = metadata.get('fields', {})
            for field, bar in self.metadata_bars.items():
                if field in fields:
                    bar.setValue(int(fields[field]['percentage']))

            # Update recently added
            recent_added = stats.get('recently_added', [])
            self.recent_added_widget.set_data(
                ['Song', 'Artist', 'Album'],
                [[s['title'], s['artist'] or '-', s['album'] or '-'] for s in recent_added]
            )

            # Update recently played
            recent_played = stats.get('recently_played', [])
            self.recent_played_widget.set_data(
                ['Song', 'Artist', 'Plays'],
                [[s['title'], s['artist'] or '-', s['play_count']] for s in recent_played]
            )

            logger.info("Statistics refreshed successfully")

        except Exception as e:
            logger.error(f"Failed to refresh statistics: {e}")
