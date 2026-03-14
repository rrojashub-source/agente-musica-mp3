"""
Recommendations Widget - AI-Powered Similar Songs (Phase 9)

Displays a collapsible list of recommended songs based on
the currently playing track using AI audio embeddings.

Created: November 23, 2025
Updated: December 8, 2025 - Integrated AI audio embeddings for real similarity
Updated: 2026-03-13 - Moved find_similar() to background thread (fixed GUI freeze)
"""
import logging
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame,
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor

from core.audio_embeddings import AudioEmbeddings

logger = logging.getLogger(__name__)


class _SimilarityWorker(QThread):
    """Background worker for CPU-intensive find_similar() computation"""

    finished = Signal(list)   # List[Dict] with results
    error = Signal(str)       # Error message

    def __init__(self, audio_embeddings, song_id, limit=8, min_similarity=0.3):
        super().__init__()
        self._audio_embeddings = audio_embeddings
        self._song_id = song_id
        self._limit = limit
        self._min_similarity = min_similarity

    def run(self):
        try:
            results = self._audio_embeddings.find_similar(
                self._song_id,
                limit=self._limit,
                min_similarity=self._min_similarity,
            )
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Similarity worker error: {e}")
            self.error.emit(str(e))


class RecommendationsWidget(QWidget):
    """
    Widget showing recommended songs similar to currently playing

    Signals:
        song_selected: Emitted when a recommendation is clicked (song_data dict)
    """

    song_selected = Signal(dict)

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.audio_embeddings = AudioEmbeddings(db_manager)

        self._current_song: Optional[Dict] = None
        self._recommendations: List[Dict] = []
        self._is_collapsed = False
        self._worker: Optional[_SimilarityWorker] = None

        self._init_ui()

        logger.info("RecommendationsWidget initialized with AI audio embeddings")

    def _init_ui(self):
        """Initialize UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Header with collapse button
        header_layout = QHBoxLayout()

        self.title_label = QLabel("🧠 Brain AI")
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
        self.title_label.setText("🧠 Brain AI (play a song)")

    def set_current_song(self, song_data: Optional[Dict]):
        """
        Update current song and refresh recommendations using AI

        Args:
            song_data: Currently playing song dict, or None if stopped
        """
        self._current_song = song_data

        if song_data:
            self.recommendations_list.show()
            song_title = song_data.get('title', 'Unknown')
            self.title_label.setText(f"🧠 Similar to: {song_title[:25]}...")
            self._refresh_recommendations()
        else:
            self.recommendations_list.clear()
            self.recommendations_list.hide()
            self.title_label.setText("🧠 Brain AI (play a song)")

    def _refresh_recommendations(self):
        """Refresh recommendations in a background thread (non-blocking)"""
        if not self._current_song:
            return

        song_id = self._current_song.get('id')
        if not song_id:
            logger.warning("No song ID for recommendations")
            return

        # Cancel previous worker if still running
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(1000)

        # Show loading state
        self.recommendations_list.clear()
        loading_item = QListWidgetItem("🔄 Analyzing audio...")
        loading_item.setFlags(loading_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        self.recommendations_list.addItem(loading_item)

        # Launch background worker
        self._worker = _SimilarityWorker(
            self.audio_embeddings, song_id, limit=8, min_similarity=0.3
        )
        self._worker.finished.connect(self._on_results_ready)
        self._worker.error.connect(self._on_results_error)
        self._worker.start()

    def _on_results_ready(self, similar_results: list):
        """Handle results from background worker (runs on main thread via signal)"""
        self.recommendations_list.clear()

        if not similar_results:
            item = QListWidgetItem("No similar songs found")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.recommendations_list.addItem(item)
            return

        # Populate list with similarity scores
        self._recommendations = []
        for result in similar_results:
            song = result['song']
            similarity = result['similarity']
            self._recommendations.append(song)

            title = song.get('title', 'Unknown')
            artist = song.get('artist', 'Unknown')
            similarity_pct = int(similarity * 100)

            item = QListWidgetItem(f"♪ {title}\n   {artist} ({similarity_pct}%)")
            item.setData(Qt.ItemDataRole.UserRole, song)

            # Color code by similarity
            if similarity >= 0.8:
                item.setForeground(QColor(0, 200, 100))  # Green - very similar
            elif similarity >= 0.6:
                item.setForeground(QColor(0, 180, 230))  # Cyan - similar
            elif similarity >= 0.4:
                item.setForeground(QColor(200, 180, 0))  # Yellow - somewhat similar

            self.recommendations_list.addItem(item)

        logger.info(f"AI found {len(self._recommendations)} similar songs")

    def _on_results_error(self, error_msg: str):
        """Handle error from background worker"""
        self.recommendations_list.clear()
        item = QListWidgetItem(f"Error: {error_msg[:30]}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        self.recommendations_list.addItem(item)

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
        self.title_label.setText("🧠 Brain AI (play a song)")
