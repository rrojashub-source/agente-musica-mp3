"""
Recommendations Widget - Show similar songs

Displays a collapsible list of recommended songs based on
the currently playing track.

Created: November 23, 2025
"""
import logging
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class RecommendationsWidget(QWidget):
    """
    Widget showing recommended songs similar to currently playing

    Signals:
        song_selected: Emitted when a recommendation is clicked (song_data dict)
    """

    song_selected = pyqtSignal(dict)

    def __init__(self, db_manager, parent=None):
        """
        Initialize recommendations widget

        Args:
            db_manager: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.recommendation_engine = RecommendationEngine(db_manager)

        self._current_song: Optional[Dict] = None
        self._recommendations: List[Dict] = []
        self._is_collapsed = False

        self._init_ui()

        logger.info("RecommendationsWidget initialized")

    def _init_ui(self):
        """Initialize UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Header with collapse button
        header_layout = QHBoxLayout()

        self.title_label = QLabel("🎯 Similar Songs")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(24, 24)
        self.refresh_btn.setToolTip("Refresh recommendations")
        self.refresh_btn.clicked.connect(self._refresh_recommendations)
        header_layout.addWidget(self.refresh_btn)

        self.collapse_btn = QPushButton("▼")
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.setToolTip("Collapse/Expand")
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.collapse_btn)

        main_layout.addLayout(header_layout)

        # Recommendations list
        self.recommendations_list = QListWidget()
        self.recommendations_list.setMaximumHeight(200)
        self.recommendations_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 180, 230, 0.3);
            }
        """)
        self.recommendations_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        main_layout.addWidget(self.recommendations_list)

        # Initially hidden
        self.recommendations_list.hide()
        self.title_label.setText("🎯 Similar Songs (play a song)")

    def set_current_song(self, song_data: Optional[Dict]):
        """
        Update current song and refresh recommendations

        Args:
            song_data: Currently playing song dict, or None if stopped
        """
        self._current_song = song_data

        if song_data:
            self._refresh_recommendations()
            self.recommendations_list.show()
            song_title = song_data.get('title', 'Unknown')
            self.title_label.setText(f"🎯 Similar to: {song_title[:30]}...")
        else:
            self.recommendations_list.clear()
            self.recommendations_list.hide()
            self.title_label.setText("🎯 Similar Songs (play a song)")

    def _refresh_recommendations(self):
        """Refresh the recommendations list"""
        self.recommendations_list.clear()

        if not self._current_song:
            return

        # Get recommendations
        self._recommendations = self.recommendation_engine.get_recommendations(
            self._current_song,
            limit=8
        )

        if not self._recommendations:
            item = QListWidgetItem("No similar songs found")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.recommendations_list.addItem(item)
            return

        # Populate list
        for song in self._recommendations:
            title = song.get('title', 'Unknown')
            artist = song.get('artist', 'Unknown')

            item = QListWidgetItem(f"♪ {title}\n   {artist}")
            item.setData(Qt.ItemDataRole.UserRole, song)
            self.recommendations_list.addItem(item)

        logger.info(f"Loaded {len(self._recommendations)} recommendations")

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle recommendation double-click"""
        song_data = item.data(Qt.ItemDataRole.UserRole)
        if song_data:
            self.song_selected.emit(song_data)
            logger.info(f"Recommendation selected: {song_data.get('title')}")

    def _toggle_collapse(self):
        """Toggle collapsed state"""
        self._is_collapsed = not self._is_collapsed

        if self._is_collapsed:
            self.recommendations_list.hide()
            self.collapse_btn.setText("▶")
        else:
            if self._current_song:
                self.recommendations_list.show()
            self.collapse_btn.setText("▼")

    def clear(self):
        """Clear recommendations"""
        self._current_song = None
        self._recommendations = []
        self.recommendations_list.clear()
        self.recommendations_list.hide()
        self.title_label.setText("🎯 Similar Songs (play a song)")
