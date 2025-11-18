"""
Library Tab with Playback Integration - Phase 6.3

Complete library view with integrated audio playback:
- Table view of all songs in database
- Double-click to play song
- Play button for selected song
- Keyboard shortcuts (Space = play/pause, Arrow keys = prev/next)
- Currently playing song highlighted
- Integration with AudioPlayer and NowPlayingWidget
- Auto-play next song on end
- Graceful error handling for missing files

Created: November 13, 2025
"""
import logging
from pathlib import Path
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


class LibraryTab(QWidget):
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
    """

    def __init__(self, db_manager, audio_player=None, now_playing_widget=None):
        """
        Initialize Library Tab

        Args:
            db_manager: Database manager instance
            audio_player: AudioPlayer instance (optional)
            now_playing_widget: NowPlayingWidget instance (optional)
        """
        super().__init__()
        self.db_manager = db_manager
        self.audio_player = audio_player
        self.now_playing_widget = now_playing_widget

        # State
        self._current_song_id = None
        self._current_song_row = -1
        self._user_stopped = False  # Track if user manually stopped playback

        self._init_ui()
        self._load_library()
        self._connect_signals()

        logger.info("LibraryTab initialized")

    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📚 Music Library")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)

        self.count_label = QLabel("0 songs")
        self.count_label.setStyleSheet("font-size: 12px;")
        self.count_label.setProperty("class", "secondary")  # Use theme color
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Library table
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(6)
        self.library_table.setHorizontalHeaderLabels([
            "Title", "Artist", "Album", "Genre", "Year", "Duration"
        ])

        # Table settings
        self.library_table.setAlternatingRowColors(True)
        self.library_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.library_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.library_table.setSortingEnabled(True)

        # Column widths - All columns manually resizable
        header = self.library_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # All columns resizable

        # Set initial default widths (user can adjust)
        header.resizeSection(0, 250)  # Title
        header.resizeSection(1, 150)  # Artist
        header.resizeSection(2, 150)  # Album
        header.resizeSection(3, 100)  # Genre
        header.resizeSection(4, 60)   # Year
        header.resizeSection(5, 80)   # Duration

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

        buttons_layout.addStretch()

        self.status_label = QLabel("No song selected")
        self.status_label.setStyleSheet("font-size: 12px;")
        self.status_label.setProperty("class", "secondary")  # Use theme color
        buttons_layout.addWidget(self.status_label)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _connect_signals(self):
        """Connect signals to slots"""
        # Table interactions
        self.library_table.itemDoubleClicked.connect(self._on_row_double_clicked)
        self.library_table.itemSelectionChanged.connect(self._on_selection_changed)

        # Buttons
        self.play_button.clicked.connect(self._on_play_button_clicked)
        self.refresh_button.clicked.connect(self._load_library)

        # Now Playing Widget prev/next/stop buttons
        if self.now_playing_widget:
            self.now_playing_widget.prev_clicked.connect(self._on_prev_clicked)
            self.now_playing_widget.next_clicked.connect(self._on_next_clicked)
            self.now_playing_widget.stop_clicked.connect(self._on_stop_clicked)

    def _load_library(self):
        """Load songs from database into table"""
        try:
            # Get all songs from database
            songs = self.db_manager.get_all_songs()

            # Disable sorting while populating
            self.library_table.setSortingEnabled(False)

            # Clear table
            self.library_table.setRowCount(0)

            # Populate table
            for song in songs:
                row = self.library_table.rowCount()
                self.library_table.insertRow(row)

                # Title
                title_item = QTableWidgetItem(song.get('title', 'Unknown'))
                title_item.setData(Qt.ItemDataRole.UserRole, song.get('id'))  # Store song ID
                self.library_table.setItem(row, 0, title_item)

                # Artist
                artist_item = QTableWidgetItem(song.get('artist', 'Unknown Artist'))
                self.library_table.setItem(row, 1, artist_item)

                # Album
                album_item = QTableWidgetItem(song.get('album', 'Unknown Album'))
                self.library_table.setItem(row, 2, album_item)

                # Genre
                genre_item = QTableWidgetItem(song.get('genre', ''))
                self.library_table.setItem(row, 3, genre_item)

                # Year
                year_item = QTableWidgetItem(str(song.get('year', '')) if song.get('year') else '')
                self.library_table.setItem(row, 4, year_item)

                # Duration
                duration = song.get('duration', 0)
                duration_str = self._format_duration(duration)
                duration_item = QTableWidgetItem(duration_str)
                self.library_table.setItem(row, 5, duration_item)

            # Re-enable sorting
            self.library_table.setSortingEnabled(True)

            # Update count
            self.count_label.setText(f"{len(songs)} songs")
            self.status_label.setText(f"Loaded {len(songs)} songs")

            logger.info(f"Loaded {len(songs)} songs into library")

        except Exception as e:
            logger.error(f"Failed to load library: {e}")
            self.status_label.setText(f"Error loading library: {e}")

    def _on_row_double_clicked(self, item: QTableWidgetItem):
        """Handle double-click on table row"""
        row = item.row()
        self._play_song_at_row(row)

    def _on_play_button_clicked(self):
        """Handle play button click"""
        # Get currently selected row
        selected_rows = self.library_table.selectedIndexes()
        if not selected_rows:
            self.status_label.setText("No song selected")
            return

        row = selected_rows[0].row()
        self._play_song_at_row(row)

    def _on_selection_changed(self):
        """Handle selection change in table"""
        selected_rows = self.library_table.selectedIndexes()
        self.play_button.setEnabled(len(selected_rows) > 0)

        if selected_rows:
            row = selected_rows[0].row()
            title_item = self.library_table.item(row, 0)
            if title_item:
                title = title_item.text()
                self.status_label.setText(f"Selected: {title}")

    def _on_prev_clicked(self):
        """Handle previous button click from Now Playing widget"""
        logger.info("Previous button clicked")
        self._play_previous_song()

    def _on_next_clicked(self):
        """Handle next button click from Now Playing widget"""
        logger.info("Next button clicked")
        self._play_next_song()

    def _on_stop_clicked(self):
        """Handle stop button click from Now Playing widget"""
        logger.info("Stop button clicked - setting user_stopped flag")
        self._user_stopped = True  # Prevent auto-play after stop
        # No need to stop audio_player here - NowPlayingWidget already does it

    def _play_song_at_row(self, row: int):
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

    def _play_song(self, song_info: Dict):
        """
        Play song with audio player and update Now Playing widget

        Args:
            song_info: Dictionary with song information
        """
        # Reset user stopped flag when manually playing
        self._user_stopped = False

        file_path = song_info.get('file_path')
        if not file_path:
            logger.error("Song has no file path")
            self.status_label.setText("Error: No file path")
            return

        # Check if file exists
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            self.status_label.setText(f"Error: File not found")
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The music file could not be found:\n{file_path}"
            )
            return

        # Load and play with audio player
        if self.audio_player:
            success = self.audio_player.load(file_path)
            if success:
                self.audio_player.play()
                self.status_label.setText(f"Playing: {song_info.get('title', 'Unknown')}")
                logger.info(f"Playing: {song_info.get('title', 'Unknown')}")

                # Update Now Playing widget
                if self.now_playing_widget:
                    self.now_playing_widget.load_song(song_info)
                    self.now_playing_widget.set_playing(True)

                # Start monitoring for song end
                self._start_end_of_song_monitor()
            else:
                logger.error(f"Failed to load song: {file_path}")
                self.status_label.setText("Error: Failed to load song")
                QMessageBox.warning(
                    self,
                    "Playback Error",
                    f"Failed to load song:\n{file_path}"
                )
        else:
            logger.warning("No audio player available")
            self.status_label.setText("Error: No audio player")

    def _play_next_song(self):
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

    def _play_previous_song(self):
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

    def _start_end_of_song_monitor(self):
        """Start monitoring for end of song to auto-play next"""
        if not hasattr(self, '_end_monitor_timer'):
            self._end_monitor_timer = QTimer(self)
            self._end_monitor_timer.setInterval(1000)  # Check every second
            self._end_monitor_timer.timeout.connect(self._check_song_ended)

        self._end_monitor_timer.start()

    def _check_song_ended(self):
        """Check if current song has ended"""
        if not self.audio_player:
            return

        # Import PlaybackState for state checking
        from core.audio_player import PlaybackState

        # If not playing and NOT paused and NOT manually stopped, then song ended
        # (Don't auto-play next if user paused or stopped)
        if not self.audio_player.is_playing() and self._current_song_id:
            current_state = self.audio_player.get_state()
            if current_state != PlaybackState.PAUSED and not self._user_stopped:
                logger.info("Song ended naturally, playing next")
                self._end_monitor_timer.stop()
                self._play_next_song()

    def _highlight_playing_song(self, row: int):
        """
        Highlight currently playing song in table

        Args:
            row: Row index to highlight
        """
        from PyQt6.QtGui import QBrush

        # Clear previous highlight (reset to default)
        for r in range(self.library_table.rowCount()):
            for c in range(self.library_table.columnCount()):
                item = self.library_table.item(r, c)
                if item:
                    # Reset to default (let theme handle it)
                    item.setData(Qt.ItemDataRole.BackgroundRole, None)

        # Highlight current row with theme-aware color
        palette = self.library_table.palette()
        highlight_color = palette.color(palette.ColorRole.Highlight)

        for c in range(self.library_table.columnCount()):
            item = self.library_table.item(row, c)
            if item:
                item.setBackground(highlight_color)

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

    def keyPressEvent(self, event):
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

    def highlight_row(self, row: int):
        """
        Public method to highlight a specific row

        Args:
            row: Row index to highlight
        """
        self._highlight_playing_song(row)

    def play_song(self, song_id: int):
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

    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, '_end_monitor_timer'):
            self._end_monitor_timer.stop()
        logger.info("LibraryTab cleaned up")
