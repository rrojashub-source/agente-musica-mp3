"""
Library Tab with Playback Integration - Phase 6.3 + AI Similarity (Phase 9)

Complete library view with integrated audio playback:
- Table view of all songs in database
- Double-click to play song
- Play button for selected song
- Keyboard shortcuts (Space = play/pause, Arrow keys = prev/next)
- Currently playing song highlighted
- Integration with AudioPlayer and NowPlayingWidget
- Auto-play next song on end
- Graceful error handling for missing files
- Skeleton loading animation during data load
- AI-powered "Find Similar Songs" using audio embeddings

Created: November 13, 2025
Updated: November 23, 2025 (Added skeleton loading)
Updated: December 8, 2025 (Added AI similarity search - Phase 9)
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QPoint, Qt, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.cover_art_manager import CoverArtManager
from gui.base import BaseTab
from gui.themes.style_constants import Styles
from utils.constants import TRACK_END_CHECK_INTERVAL_MS

logger = logging.getLogger(__name__)


class LibraryTab(BaseTab):
    """
    Library tab with playback integration

    Features:
    - Table view of all songs
    - Double-click to play
    - Play button
    - Keyboard shortcuts
    - Currently playing highlight
    - Auto-play next on end
    - Integration with AudioPlayer and NowPlayingWidget

    Signals:
    - playback_started: Emitted when playback starts from library
    """

    # Signals
    playback_started = Signal()  # Emitted when a song starts playing from library
    find_similar_requested = Signal(dict)  # Emitted when user requests similar songs (song_data)

    def __init__(self, db_manager: Any, audio_player: Any = None, now_playing_widget: Any = None) -> None:
        """
        Initialize Library Tab

        Args:
            db_manager: Database manager instance
            audio_player: AudioPlayer instance (optional)
            now_playing_widget: NowPlayingWidget instance (optional)
        """
        self.db_manager: Any = db_manager
        self.audio_player: Any = audio_player
        self.now_playing_widget: Any = now_playing_widget

        # Initialize cover art manager
        self.cover_manager: CoverArtManager = CoverArtManager()

        # State
        self._current_song_id: Optional[int] = None
        self._current_song_row: int = -1
        self._user_stopped: bool = False  # Track if user manually stopped playback

        super().__init__(db_manager=db_manager, parent=None)

        # Enable drag & drop for MP3 files
        self.setAcceptDrops(True)

        logger.info("LibraryTab initialized with cover art and drag & drop support")

    def _init_ui(self) -> None:
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📚 Music Library")
        title_label.setStyleSheet(Styles.SECTION_TITLE)
        header_layout.addWidget(title_label)

        self.count_label = QLabel("0 songs")
        self.count_label.setStyleSheet(Styles.LABEL_SMALL)
        self.count_label.setProperty("class", "secondary")  # Use theme color
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Library table
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(8)
        self.library_table.setHorizontalHeaderLabels(
            ["Title", "Artist", "Album", "Genre", "Year", "Duration", "BPM", "Mood"]
        )

        # Table settings
        self.library_table.setAlternatingRowColors(True)
        self.library_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.library_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # Multi-selection enabled
        self.library_table.setSortingEnabled(True)

        # Neon selection style - works with both dark and light themes
        # Only style selection colors, let theme handle backgrounds
        self.library_table.setStyleSheet(
            """
            QTableWidget::item:selected {
                background-color: rgba(0, 180, 230, 0.4);
                color: #006080;
            }
            QTableWidget::item:hover:!selected {
                background-color: rgba(0, 180, 230, 0.15);
            }
        """
        )

        # CRITICAL: Set row height for proper text visibility when editing
        # Default height (~25px) cuts off text in inline editor
        # 35px ensures full text visibility during double-click editing
        self.library_table.verticalHeader().setDefaultSectionSize(35)

        # Context menu (right-click)
        self.library_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.library_table.customContextMenuRequested.connect(self._show_context_menu)

        # Column widths - All columns manually resizable
        header = self.library_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # All columns resizable

        # Set initial default widths (user can adjust)
        header.resizeSection(0, 220)  # Title
        header.resizeSection(1, 140)  # Artist
        header.resizeSection(2, 140)  # Album
        header.resizeSection(3, 80)  # Genre
        header.resizeSection(4, 50)  # Year
        header.resizeSection(5, 70)  # Duration
        header.resizeSection(6, 50)  # BPM
        header.resizeSection(7, 80)  # Mood

        # Last column stretches to fill remaining space
        header.setStretchLastSection(True)

        layout.addWidget(self.library_table)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.play_button = QPushButton("▶ Play")
        self.play_button.setFixedWidth(100)
        self.play_button.setEnabled(False)  # Disabled until song selected
        buttons_layout.addWidget(self.play_button)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setFixedWidth(100)
        buttons_layout.addWidget(self.refresh_button)

        self.clean_db_button = QPushButton("🧹 Clean Database")
        self.clean_db_button.setFixedWidth(140)
        self.clean_db_button.setToolTip(
            "Remove songs from database whose files no longer exist\n" "(Prevents duplicates when re-importing)"
        )
        buttons_layout.addWidget(self.clean_db_button)

        self.clean_titles_button = QPushButton("✨ Clean Titles")
        self.clean_titles_button.setFixedWidth(120)
        self.clean_titles_button.setToolTip(
            "Clean YouTube artifacts from song titles\n" "Removes: (Official Video), Artist prefix, [Audio], etc."
        )
        buttons_layout.addWidget(self.clean_titles_button)

        buttons_layout.addStretch()

        self.status_label = QLabel("No song selected")
        self.status_label.setStyleSheet(Styles.LABEL_SMALL)
        self.status_label.setProperty("class", "secondary")  # Use theme color
        buttons_layout.addWidget(self.status_label)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        # Load library data before signals are connected (avoids triggering handlers)
        self._load_library()

    def _connect_signals(self) -> None:
        """Connect signals to slots"""
        # Table interactions
        self.library_table.itemDoubleClicked.connect(self._on_row_double_clicked)
        self.library_table.itemSelectionChanged.connect(self._on_selection_changed)

        # Buttons
        self.play_button.clicked.connect(self._on_play_button_clicked)
        self.refresh_button.clicked.connect(self._load_library)
        self.clean_db_button.clicked.connect(self._on_clean_database_clicked)
        self.clean_titles_button.clicked.connect(self._on_clean_titles_clicked)

        # Now Playing Widget prev/next/stop buttons
        # NOTE: prev_clicked, next_clicked and song_ended are now handled by main.py
        # to support both library and playlist playback sources
        if self.now_playing_widget:
            # self.now_playing_widget.prev_clicked.connect(self._on_prev_clicked)  # Handled by main.py
            # self.now_playing_widget.next_clicked.connect(self._on_next_clicked)  # Handled by main.py
            # self.now_playing_widget.song_ended.connect(self._on_song_ended)  # Handled by main.py
            self.now_playing_widget.stop_clicked.connect(self._on_stop_clicked)

    def _show_skeleton_loading(self, num_rows: int = 10) -> None:
        """Show skeleton loading placeholders"""
        self.library_table.setSortingEnabled(False)
        self.library_table.setRowCount(0)

        skeleton_color = QColor(128, 128, 128, 80)  # Semi-transparent gray

        for i in range(num_rows):
            row = self.library_table.rowCount()
            self.library_table.insertRow(row)

            # Create placeholder items with skeleton style
            placeholders = ["Loading...", "...", "...", "...", "...", "..."]
            for col, text in enumerate(placeholders):
                item = QTableWidgetItem(text)
                item.setForeground(QBrush(skeleton_color))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                self.library_table.setItem(row, col, item)

        self.status_label.setText("⏳ Cargando biblioteca... / Loading library...")
        QApplication.processEvents()

    def _load_library(self) -> None:
        """Load songs from database into table with skeleton loading"""
        try:
            # Show skeleton loading first
            self._show_skeleton_loading(8)

            # Get all songs from database
            songs = self.db_manager.get_all_songs()

            # Disable sorting while populating
            self.library_table.setSortingEnabled(False)

            # Clear skeleton and load real data
            self.library_table.setRowCount(0)

            # Populate table
            for song in songs:
                row = self.library_table.rowCount()
                self.library_table.insertRow(row)

                # Title
                title_item = QTableWidgetItem(song.get("title", "Unknown"))
                title_item.setData(Qt.ItemDataRole.UserRole, song.get("id"))  # Store song ID
                self.library_table.setItem(row, 0, title_item)

                # Artist
                artist_item = QTableWidgetItem(song.get("artist", "Unknown Artist"))
                self.library_table.setItem(row, 1, artist_item)

                # Album
                album_item = QTableWidgetItem(song.get("album", "Unknown Album"))
                self.library_table.setItem(row, 2, album_item)

                # Genre
                genre_item = QTableWidgetItem(song.get("genre", ""))
                self.library_table.setItem(row, 3, genre_item)

                # Year
                year_item = QTableWidgetItem(str(song.get("year", "")) if song.get("year") else "")
                self.library_table.setItem(row, 4, year_item)

                # Duration
                duration = song.get("duration", 0)
                duration_str = self._format_duration(duration)
                duration_item = QTableWidgetItem(duration_str)
                self.library_table.setItem(row, 5, duration_item)

                # BPM (AI-detected tempo)
                bpm = song.get("bpm")
                bpm_item = QTableWidgetItem(str(bpm) if bpm else "")
                bpm_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.library_table.setItem(row, 6, bpm_item)

                # Mood (AI-classified)
                mood = song.get("mood", "")
                mood_item = QTableWidgetItem(mood if mood else "")
                # Color-code moods for visual feedback
                if mood == "Energetic":
                    mood_item.setForeground(QColor(255, 100, 50))  # Orange
                elif mood == "Happy":
                    mood_item.setForeground(QColor(50, 200, 50))  # Green
                elif mood == "Calm":
                    mood_item.setForeground(QColor(100, 150, 255))  # Blue
                elif mood == "Sad":
                    mood_item.setForeground(QColor(150, 100, 200))  # Purple
                elif mood == "Intense":
                    mood_item.setForeground(QColor(255, 50, 50))  # Red
                self.library_table.setItem(row, 7, mood_item)

            # Re-enable sorting
            self.library_table.setSortingEnabled(True)

            # Update count
            self.count_label.setText(f"{len(songs)} songs")
            self.status_label.setText(f"Loaded {len(songs)} songs")

            logger.info(f"Loaded {len(songs)} songs into library")

        except sqlite3.Error as e:
            logger.error(f"Failed to load library: {e}")
            self.status_label.setText(f"Error loading library: {e}")

    def _on_row_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on table row"""
        row = item.row()
        self._play_song_at_row(row)

    def _on_play_button_clicked(self) -> None:
        """Handle play button click"""
        # Get currently selected row
        selected_rows = self.library_table.selectedIndexes()
        if not selected_rows:
            self.status_label.setText("No song selected")
            return

        row = selected_rows[0].row()
        self._play_song_at_row(row)

    def _on_selection_changed(self) -> None:
        """Handle selection change in table"""
        selected_rows = self.library_table.selectedIndexes()
        self.play_button.setEnabled(len(selected_rows) > 0)

        if selected_rows:
            row = selected_rows[0].row()
            title_item = self.library_table.item(row, 0)
            if title_item:
                title = title_item.text()
                self.status_label.setText(f"Selected: {title}")

    def _on_prev_clicked(self) -> None:
        """Handle previous button click from Now Playing widget"""
        logger.info("Previous button clicked")
        self._play_previous_song()

    def _on_next_clicked(self) -> None:
        """Handle next button click from Now Playing widget"""
        logger.info("Next button clicked")
        self._play_next_song()

    def _on_stop_clicked(self) -> None:
        """Handle stop button click from Now Playing widget"""
        logger.info("Stop button clicked - setting user_stopped flag")
        self._user_stopped = True  # Prevent auto-play after stop
        # No need to stop audio_player here - NowPlayingWidget already does it

    def _play_song_at_row(self, row: int) -> None:
        """
        Play song at specified row

        Args:
            row: Row index in table
        """
        # Get song ID from row
        title_item = self.library_table.item(row, 0)
        if not title_item:
            return

        song_id = title_item.data(Qt.ItemDataRole.UserRole)
        if not song_id:
            logger.error(f"No song ID found for row {row}")
            return

        # Get song info from database
        song_info = self.db_manager.get_song_by_id(song_id)
        if not song_info:
            logger.error(f"Song not found in database: {song_id}")
            self.status_label.setText("Song not found in database")
            return

        # Play song
        self._play_song(song_info)

        # Update current song tracking
        self._current_song_id = song_id
        self._current_song_row = row

        # Highlight playing song
        self._highlight_playing_song(row)

    def _play_song(self, song_info: Dict[str, Any]) -> None:
        """
        Play song with audio player and update Now Playing widget

        Args:
            song_info: Dictionary with song information
        """
        # Reset user stopped flag when manually playing
        self._user_stopped = False

        file_path = song_info.get("file_path")
        if not file_path:
            logger.error("Song has no file path")
            self.status_label.setText("Error: No file path")
            return

        # Check if file exists
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            self.status_label.setText(f"Error: File not found")
            QMessageBox.warning(self, "File Not Found", f"The music file could not be found:\n{file_path}")
            return

        # Load and play with audio player
        if self.audio_player:
            success = self.audio_player.load(file_path)
            if success:
                self.audio_player.play()
                self.status_label.setText(f"Playing: {song_info.get('title', 'Unknown')}")
                logger.info(f"Playing: {song_info.get('title', 'Unknown')}")

                # Enrich song_info with album art path if available
                artist = song_info.get("artist")
                album = song_info.get("album")
                if artist and album:
                    cover_path = self.cover_manager.get_cover_path(artist, album)
                    if cover_path:
                        song_info["album_art"] = str(cover_path)
                        logger.debug(f"Cover found: {cover_path}")
                    else:
                        logger.debug(f"No cover found for {artist} - {album}")

                # Update Now Playing widget
                if self.now_playing_widget:
                    self.now_playing_widget.load_song(song_info)
                    self.now_playing_widget.set_playing(True)

                # Emit signal so main.py can track playback source
                self.playback_started.emit()

                # Start monitoring for song end
                self._start_end_of_song_monitor()
            else:
                logger.error(f"Failed to load song: {file_path}")
                self.status_label.setText("Error: Failed to load song")
                QMessageBox.warning(self, "Playback Error", f"Failed to load song:\n{file_path}")
        else:
            logger.warning("No audio player available")
            self.status_label.setText("Error: No audio player")

    def _on_song_ended(self) -> None:
        """Handle song ended signal from NowPlayingWidget"""
        logger.info("Song ended signal received")
        self._user_stopped = False  # Reset flag

        # Check if shuffle is enabled
        if self.now_playing_widget and self.now_playing_widget.is_shuffle_enabled():
            self._play_random_song()
        else:
            self._play_next_song()

    def _play_next_song(self) -> None:
        """Play next song in library"""
        if self._current_song_row < 0:
            return

        next_row = self._current_song_row + 1
        if next_row < self.library_table.rowCount():
            self._play_song_at_row(next_row)
            logger.info("Auto-playing next song")
        else:
            logger.info("End of library reached")
            self.status_label.setText("End of library")

    def _play_random_song(self) -> None:
        """Play a random song from the library (shuffle mode)"""
        import random

        row_count = self.library_table.rowCount()
        if row_count <= 1:
            logger.info("Not enough songs for shuffle")
            return

        # Pick a random row different from current
        available_rows = [r for r in range(row_count) if r != self._current_song_row]
        if available_rows:
            next_row = random.choice(available_rows)
            self._play_song_at_row(next_row)
            logger.info(f"Shuffle: playing random song at row {next_row}")
        else:
            logger.info("No songs available for shuffle")
            self.status_label.setText("No songs available")

    def _play_previous_song(self) -> None:
        """Play previous song in library"""
        if self._current_song_row < 0:
            return

        prev_row = self._current_song_row - 1
        if prev_row >= 0:
            self._play_song_at_row(prev_row)
            logger.info("Playing previous song")
        else:
            logger.info("Beginning of library reached")
            self.status_label.setText("Beginning of library")

    def _start_end_of_song_monitor(self) -> None:
        """Start monitoring for end of song to auto-play next"""
        if not hasattr(self, "_end_monitor_timer"):
            self._end_monitor_timer = QTimer(self)
            self._end_monitor_timer.setInterval(TRACK_END_CHECK_INTERVAL_MS)  # Check every second
            self._end_monitor_timer.timeout.connect(self._check_song_ended)

        self._end_monitor_timer.start()

    def _check_song_ended(self) -> None:
        """Check if current song has ended (legacy monitor - now handled by NowPlayingWidget)"""
        # This method is kept for backward compatibility but the main
        # song ended logic is now handled by NowPlayingWidget.song_ended signal
        # which triggers _on_song_ended in this class
        pass

    def _highlight_playing_song(self, row: int) -> None:
        """
        Highlight currently playing song in table

        Args:
            row: Row index to highlight
        """
        from PySide6.QtGui import QBrush

        # Colors that work in both dark and light themes
        highlight_bg = QColor(0, 160, 200, 100)  # Semi-transparent cyan
        highlight_text = QColor(0, 80, 120)  # Dark cyan text (readable in both themes)

        # Clear previous highlight (reset to default)
        for r in range(self.library_table.rowCount()):
            for c in range(self.library_table.columnCount()):
                item = self.library_table.item(r, c)
                if item:
                    # Reset to default (let theme handle it)
                    item.setData(Qt.ItemDataRole.BackgroundRole, None)
                    item.setData(Qt.ItemDataRole.ForegroundRole, None)

        # Highlight current row
        for c in range(self.library_table.columnCount()):
            item = self.library_table.item(row, c)
            if item:
                item.setBackground(highlight_bg)
                item.setForeground(highlight_text)

    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to MM:SS

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        """Handle keyboard shortcuts"""
        key = event.key()

        # Space = toggle play/pause
        if key == Qt.Key.Key_Space:
            if self._current_song_id:
                # Toggle play/pause (would need player state tracking)
                logger.info("Space pressed - toggle play/pause")
                self.status_label.setText("Play/Pause toggled")
            event.accept()

        # Up/Down arrows = prev/next song
        elif key == Qt.Key.Key_Down:
            self._play_next_song()
            event.accept()

        elif key == Qt.Key.Key_Up:
            self._play_previous_song()
            event.accept()

        else:
            super().keyPressEvent(event)

    def highlight_row(self, row: int) -> None:
        """
        Public method to highlight a specific row

        Args:
            row: Row index to highlight
        """
        self._highlight_playing_song(row)

    def play_song(self, song_id: int) -> None:
        """
        Public method to play song by ID

        Args:
            song_id: Song ID to play
        """
        # Find row with this song ID
        for row in range(self.library_table.rowCount()):
            title_item = self.library_table.item(row, 0)
            if title_item and title_item.data(Qt.ItemDataRole.UserRole) == song_id:
                self._play_song_at_row(row)
                return

        logger.error(f"Song ID not found in table: {song_id}")

    def _show_context_menu(self, position: QPoint) -> None:
        """
        Show context menu on right-click

        Args:
            position: Mouse position relative to table
        """
        # Get selected rows (unique row numbers)
        selected_indexes = self.library_table.selectedIndexes()
        if not selected_indexes:
            return  # No row selected

        # Get unique row numbers (each row has 6 columns, so we get duplicates)
        selected_rows = sorted(set(index.row() for index in selected_indexes))

        # Get song data for all selected rows
        songs_to_delete = []
        for row in selected_rows:
            title_item = self.library_table.item(row, 0)
            if not title_item:
                continue

            song_id = title_item.data(Qt.ItemDataRole.UserRole)
            title = title_item.text()
            artist = self.library_table.item(row, 1).text() if self.library_table.item(row, 1) else "Unknown"

            songs_to_delete.append({"id": song_id, "title": title, "artist": artist, "row": row})

        if not songs_to_delete:
            return

        # Create context menu
        menu = QMenu(self)

        # Find Similar Songs action (only for single selection)
        find_similar_action = None
        analyze_action = None
        if len(songs_to_delete) == 1:
            find_similar_action = menu.addAction("🧠 Find Similar Songs (AI)")
            find_similar_action.setStatusTip(f"Find songs similar to '{songs_to_delete[0]['title']}' using AI")

            analyze_action = menu.addAction("🎵 Analyze BPM/Mood (AI)")
            analyze_action.setStatusTip(f"Detect tempo and mood for '{songs_to_delete[0]['title']}'")
            menu.addSeparator()

        # Delete action (singular or plural)
        if len(songs_to_delete) == 1:
            delete_text = "🗑️ Delete Song"
            status_tip = f"Delete '{songs_to_delete[0]['title']}' from library"
        else:
            delete_text = f"🗑️ Delete {len(songs_to_delete)} Songs"
            status_tip = f"Delete {len(songs_to_delete)} selected songs from library"

        delete_action = menu.addAction(delete_text)
        delete_action.setStatusTip(status_tip)

        # Show menu and get action
        action = menu.exec(self.library_table.viewport().mapToGlobal(position))

        # Handle action
        if action == find_similar_action and find_similar_action:
            self._find_similar_songs(songs_to_delete[0])
        elif action == analyze_action and analyze_action:
            self._analyze_bpm_mood(songs_to_delete[0])
        elif action == delete_action:
            self._delete_selected_songs(songs_to_delete)

    def _find_similar_songs(self, song: Dict[str, Any]) -> None:
        """
        Find songs similar to the selected song using AI audio embeddings.

        Emits find_similar_requested signal to update the Brain AI panel.

        Args:
            song: Dict with 'id', 'title', 'artist' keys
        """
        song_id = song["id"]
        song_title = song["title"]
        song_artist = song["artist"]

        logger.info(f"Finding similar songs to: {song_title} - {song_artist}")

        # First check if the file exists
        song_info = self.db_manager.get_song_by_id(song_id)
        if song_info:
            file_path = song_info.get("file_path", "")
            if not Path(file_path).exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Cannot analyze this song - file not found:\n\n"
                    f"'{song_title}' by {song_artist}\n\n"
                    f"Path: {file_path}\n\n"
                    f"The file may have been moved or deleted.\n"
                    f"Use '🧹 Clean Database' to remove missing files.",
                )
                self.status_label.setText("File not found")
                return

            # Emit signal to update Brain AI panel
            self.find_similar_requested.emit(song_info)
            self.status_label.setText(f"🧠 Finding similar to '{song_title}'...")

    def _analyze_bpm_mood(self, song: Dict[str, Any]) -> None:
        """
        Analyze BPM and Mood for a song using AI audio analysis.

        Updates the database and refreshes the table row.

        Args:
            song: Dict with 'id', 'title', 'artist', 'row' keys
        """
        from core.audio_embeddings import AudioEmbeddings

        song_id = song["id"]
        song_title = song["title"]
        row = song["row"]

        # Get full song info
        song_info = self.db_manager.get_song_by_id(song_id)
        if not song_info:
            self.status_label.setText("Song not found")
            return

        file_path = song_info.get("file_path", "")
        if not Path(file_path).exists():
            QMessageBox.warning(self, "File Not Found", f"Cannot analyze - file not found:\n\n{file_path}")
            return

        # Show progress
        self.status_label.setText(f"🎵 Analyzing '{song_title}'...")
        QApplication.processEvents()

        try:
            # Perform AI analysis
            embeddings = AudioEmbeddings(self.db_manager)
            analysis = embeddings.analyze_song(file_path)

            if analysis:
                bpm = analysis.get("bpm")
                mood = analysis.get("mood")
                energy = analysis.get("energy")
                valence = analysis.get("valence")

                # Update database
                updates = {}
                if bpm:
                    updates["bpm"] = bpm
                if mood:
                    updates["mood"] = mood
                if energy is not None:
                    updates["energy"] = energy
                if valence is not None:
                    updates["valence"] = valence

                if updates:
                    self.db_manager.update_song(song_id, updates)

                    # Update table display
                    if bpm:
                        bpm_item = QTableWidgetItem(str(bpm))
                        bpm_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.library_table.setItem(row, 6, bpm_item)

                    if mood:
                        mood_item = QTableWidgetItem(mood)
                        # Color-code moods
                        if mood == "Energetic":
                            mood_item.setForeground(QColor(255, 100, 50))
                        elif mood == "Happy":
                            mood_item.setForeground(QColor(50, 200, 50))
                        elif mood == "Calm":
                            mood_item.setForeground(QColor(100, 150, 255))
                        elif mood == "Sad":
                            mood_item.setForeground(QColor(150, 100, 200))
                        elif mood == "Intense":
                            mood_item.setForeground(QColor(255, 50, 50))
                        self.library_table.setItem(row, 7, mood_item)

                    self.status_label.setText(f"✅ {song_title}: BPM={bpm or '?'}, Mood={mood or '?'}")
                    logger.info(f"Analyzed song {song_id}: BPM={bpm}, Mood={mood}")
                else:
                    self.status_label.setText(f"⚠️ Could not analyze '{song_title}'")
            else:
                self.status_label.setText(f"⚠️ Analysis failed for '{song_title}'")

        except (ValueError, TypeError, OSError) as e:
            logger.error(f"BPM/Mood analysis failed: {e}")
            self.status_label.setText(f"❌ Analysis error: {str(e)[:50]}")

    def _delete_selected_songs(self, songs: List[Dict[str, Any]]) -> None:
        """
        Delete selected songs from database (supports single or multiple songs)

        Args:
            songs: List of song dicts with keys: id, title, artist, row
        """
        if not songs:
            return

        # Build confirmation message
        if len(songs) == 1:
            # Single song confirmation
            song = songs[0]
            message = (
                f"Are you sure you want to delete this song from the library?\n\n"
                f"Title: {song['title']}\n"
                f"Artist: {song['artist']}\n\n"
                f"Note: This will only remove the song from the library database.\n"
                f"The MP3 file will remain on your disk."
            )
            title = "Delete Song"
        else:
            # Multiple songs confirmation
            message = f"Are you sure you want to delete {len(songs)} songs from the library?\n\n" f"First 5 songs:\n"
            for song in songs[:5]:
                message += f"  • {song['title']} - {song['artist']}\n"

            if len(songs) > 5:
                message += f"  ... and {len(songs) - 5} more\n"

            message += (
                f"\nNote: This will only remove songs from the library database.\n"
                f"The MP3 files will remain on your disk."
            )
            title = f"Delete {len(songs)} Songs"

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,  # Default to No for safety
        )

        if reply == QMessageBox.StandardButton.No:
            logger.info(f"Delete canceled by user ({len(songs)} songs)")
            return

        # Delete from database (batch delete)
        try:
            cursor = self.db_manager.conn.cursor()
            song_ids = [song["id"] for song in songs]

            # Batch delete using IN clause
            placeholders = ",".join("?" * len(song_ids))
            cursor.execute(f"DELETE FROM songs WHERE id IN ({placeholders})", song_ids)
            self.db_manager.conn.commit()

            logger.info(f"Deleted {len(songs)} songs from database")

            # Remove rows from table (in reverse order to avoid index issues)
            rows_to_remove = sorted([song["row"] for song in songs], reverse=True)
            for row in rows_to_remove:
                self.library_table.removeRow(row)

            # Update count label
            song_count = self.library_table.rowCount()
            self.count_label.setText(f"{song_count} songs")

            # Update status
            if len(songs) == 1:
                self.status_label.setText(f"Deleted: {songs[0]['title']}")
            else:
                self.status_label.setText(f"Deleted {len(songs)} songs")

            # If any deleted song was playing, stop playback
            deleted_ids = set(song["id"] for song in songs)
            if self._current_song_id in deleted_ids:
                logger.info("Deleted song was playing, stopping playback")
                if self.audio_player:
                    self.audio_player.stop()
                self._current_song_id = None
                self._current_song_row = -1
                if self.now_playing_widget:
                    self.now_playing_widget.clear()

            logger.info(f"Successfully deleted {len(songs)} songs")

        except sqlite3.Error as e:
            logger.error(f"Failed to delete {len(songs)} songs: {e}", exc_info=True)
            QMessageBox.critical(self, "Delete Failed", f"Failed to delete songs from database:\n{e}")

    def _on_clean_database_clicked(self) -> None:
        """Handle clean database button click"""
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Clean Database",
            "This will remove songs from the database whose files no longer exist.\n\n"
            "This is useful after deleting duplicate files to prevent them from\n"
            "being re-imported when you scan folders again.\n\n"
            "⚠️ This operation cannot be undone.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Disable button during cleanup
            self.clean_db_button.setEnabled(False)
            self.status_label.setText("Cleaning database...")

            # Execute cleanup
            stats = self.db_manager.cleanup_orphans()

            # Show results
            total = stats["total_checked"]
            found = stats["orphans_found"]
            deleted = stats["orphans_deleted"]
            errors = stats["errors"]

            if found == 0:
                QMessageBox.information(
                    self, "Database Clean", f"Database is clean!\n\n" f"Checked {total} songs, no orphans found."
                )
                self.status_label.setText(f"Database clean ({total} songs checked)")
            elif deleted > 0:
                error_msg = ""
                if errors:
                    error_msg = f"\n\nErrors: {len(errors)}"

                QMessageBox.information(
                    self,
                    "Cleanup Complete",
                    f"Cleaned {deleted} orphan songs from database.\n\n"
                    f"Checked: {total} songs\n"
                    f"Found: {found} orphans\n"
                    f"Deleted: {deleted}{error_msg}",
                )
                self.status_label.setText(f"Cleaned {deleted} orphans")

                # Refresh library view
                self._load_library()
            else:
                QMessageBox.warning(
                    self,
                    "Cleanup Failed",
                    f"Found {found} orphans but failed to delete them.\n\n" f"Errors: {len(errors)}",
                )
                self.status_label.setText("Cleanup failed")

            logger.info(f"Database cleanup: {deleted}/{found} deleted")

        except sqlite3.Error as e:
            logger.error(f"Cleanup database error: {e}", exc_info=True)
            QMessageBox.critical(self, "Cleanup Error", f"Failed to clean database:\n\n{e}")
            self.status_label.setText("Cleanup error")

        finally:
            # Re-enable button
            self.clean_db_button.setEnabled(True)

    def _on_clean_titles_clicked(self) -> None:
        """Clean YouTube artifacts from all song titles in the database."""
        self.clean_titles_button.setEnabled(False)
        self.status_label.setText("Cleaning titles...")

        try:
            count = self.db_manager.batch_clean_titles()
            if count > 0:
                self._load_library()
                self.status_label.setText(f"✅ {count} titles cleaned")
                QMessageBox.information(
                    self,
                    "Titles Cleaned",
                    f"Cleaned {count} song titles.\n\n"
                    "Removed: YouTube artifacts (Official Video, Audio, etc.),\n"
                    "artist prefixes, and channel suffixes.",
                )
            else:
                self.status_label.setText("✅ All titles are already clean")
        except Exception as e:  # GUI error boundary - DB/metadata errors must not crash
            logger.error(f"Clean titles error: {e}")
            self.status_label.setText("Error cleaning titles")
        finally:
            self.clean_titles_button.setEnabled(True)

    # ==================== Drag & Drop Support ====================

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        """Handle drag enter - accept audio files"""
        if event.mimeData().hasUrls():
            # Check if any URL is an audio file
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path and self._is_audio_file(file_path):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # type: ignore[override]
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        """Handle file drop - import audio files to library"""
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        audio_files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path and self._is_audio_file(file_path):
                audio_files.append(file_path)

        if not audio_files:
            event.ignore()
            return

        event.acceptProposedAction()

        # Import the dropped files
        self._import_dropped_files(audio_files)

    def _is_audio_file(self, file_path: str) -> bool:
        """Check if file is a supported audio format"""
        supported_extensions = {".mp3", ".m4a", ".flac", ".wav", ".ogg", ".aac", ".wma"}
        return Path(file_path).suffix.lower() in supported_extensions

    def _import_dropped_files(self, file_paths: List[str]) -> None:
        """Import dropped audio files to the library"""
        from core.metadata_tagger import MetadataTagger

        imported = 0
        duplicates = 0
        errors = 0

        tagger = MetadataTagger()

        for file_path in file_paths:
            try:
                # Check if already in database
                if self.db_manager.song_exists_by_file_path(file_path):
                    duplicates += 1
                    logger.debug(f"Skipping duplicate: {file_path}")
                    continue

                # Extract metadata
                metadata = tagger.read_metadata(file_path)

                # Prepare song data
                song_data = {
                    "file_path": file_path,
                    "title": metadata.get("title") or Path(file_path).stem,
                    "artist": metadata.get("artist") or "Unknown Artist",
                    "album": metadata.get("album") or "Unknown Album",
                    "genre": metadata.get("genre") or "",
                    "year": metadata.get("year"),
                    "duration": metadata.get("duration") or 0,
                    "bitrate": metadata.get("bitrate") or 0,
                }

                # Add to database
                self.db_manager.add_song(song_data)
                imported += 1
                logger.info(f"Imported: {song_data['title']} - {song_data['artist']}")

            except (OSError, sqlite3.Error) as e:
                errors += 1
                logger.error(f"Error importing {file_path}: {e}")

        # Refresh library view
        if imported > 0:
            self._load_library()

        # Show summary
        msg_parts = []
        if imported > 0:
            msg_parts.append(f"Imported: {imported}")
        if duplicates > 0:
            msg_parts.append(f"Duplicates skipped: {duplicates}")
        if errors > 0:
            msg_parts.append(f"Errors: {errors}")

        summary = ", ".join(msg_parts) if msg_parts else "No files imported"
        self.status_label.setText(f"Drop: {summary}")

        if imported > 0 or duplicates > 0 or errors > 0:
            QMessageBox.information(
                self,
                "Drag & Drop Import",
                f"Dropped {len(file_paths)} files:\n\n"
                f"✅ Imported: {imported}\n"
                f"⏭️ Duplicates skipped: {duplicates}\n"
                f"❌ Errors: {errors}",
            )

        logger.info(f"Drag & drop import: {imported} imported, {duplicates} duplicates, {errors} errors")

    def cleanup(self) -> None:
        """Cleanup resources"""
        if hasattr(self, "_end_monitor_timer"):
            self._end_monitor_timer.stop()
        logger.info("LibraryTab cleaned up")
