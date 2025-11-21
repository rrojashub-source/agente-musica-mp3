"""
Now Playing Widget - Phase 6.2

GUI widget for displaying currently playing song with playback controls.

Features:
- Song metadata display (title, artist, album)
- Album art thumbnail (100x100)
- Playback controls (play/pause, stop, prev, next)
- Progress slider (seek functionality)
- Volume slider
- Time labels (current / total)
- Position updates via QTimer (100ms)
- On-demand cover art search

Created: November 13, 2025
"""
import logging
from typing import Optional, Dict
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from core.audio_player import PlaybackState
from core.cover_art_manager import CoverArtManager

logger = logging.getLogger(__name__)


class NowPlayingWidget(QWidget):
    """
    Now Playing widget with playback controls

    Displays:
    - Album art (100x100 thumbnail)
    - Song info (title, artist, album)
    - Playback controls (play/pause, stop, prev, next)
    - Progress slider (seek bar)
    - Volume slider
    - Time labels (current / total)

    Signals:
    - play_clicked: User clicked play/pause
    - stop_clicked: User clicked stop
    - prev_clicked: User clicked previous
    - next_clicked: User clicked next
    - seek_requested(float): User dragged progress slider to position (seconds)
    - volume_changed(float): User changed volume (0.0-1.0)
    - song_loaded(str): New song loaded, emits file_path
    """

    # Signals
    play_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    seek_requested = pyqtSignal(float)
    volume_changed = pyqtSignal(float)
    position_changed = pyqtSignal(float)  # Emits current position in seconds
    song_loaded = pyqtSignal(str)  # Emits file_path when new song loaded
    song_metadata_changed = pyqtSignal(dict)  # Emits full song_info (for lyrics, stats, etc.)

    def __init__(self, audio_player=None):
        """
        Initialize Now Playing widget

        Args:
            audio_player: AudioPlayer instance (optional)
        """
        super().__init__()
        self.audio_player = audio_player
        self.current_song = None
        self._is_seeking = False  # Prevent position update during seek
        self._is_playing = False
        self._is_paused = False  # Track if we're in paused state

        # Initialize cover art manager
        self.cover_manager = CoverArtManager()

        self._init_ui()
        self._init_timer()
        self._connect_signals()

        logger.info("NowPlayingWidget initialized")

    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # ========== Top Section: Album Art + Song Info ==========
        top_layout = QHBoxLayout()

        # Album art section (with search button)
        art_layout = QVBoxLayout()

        # Album art thumbnail (100x100)
        self.album_art_label = QLabel()
        self.album_art_label.setFixedSize(100, 100)
        self.album_art_label.setFrameStyle(QFrame.Shape.Box)
        # Let theme handle colors
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setText("♪")  # Placeholder
        art_layout.addWidget(self.album_art_label)

        # Search cover button (on-demand)
        self.search_cover_button = QPushButton("🔍 Cover")
        self.search_cover_button.setFixedSize(100, 25)
        self.search_cover_button.setToolTip("Search for album cover art")
        self.search_cover_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #3f3f3f;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #555555;
            }
        """)
        self.search_cover_button.setEnabled(False)  # Disabled until song loaded
        art_layout.addWidget(self.search_cover_button)

        top_layout.addLayout(art_layout)

        # Song info
        info_layout = QVBoxLayout()

        self.title_label = QLabel("No song playing")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self.title_label)

        self.artist_label = QLabel("Artist")
        self.artist_label.setStyleSheet("font-size: 12px;")
        self.artist_label.setProperty("class", "secondary")  # Use theme color
        info_layout.addWidget(self.artist_label)

        self.album_label = QLabel("Album")
        self.album_label.setStyleSheet("font-size: 12px;")
        self.album_label.setProperty("class", "secondary")  # Use theme color
        info_layout.addWidget(self.album_label)

        info_layout.addStretch()
        top_layout.addLayout(info_layout)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        # ========== Middle Section: Progress Slider ==========
        progress_layout = QVBoxLayout()

        # Progress slider
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)  # Use 1000 steps for smooth seeking
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)  # Disabled until song loaded
        progress_layout.addWidget(self.progress_slider)

        # Time labels
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setStyleSheet("font-size: 10px;")
        time_layout.addWidget(self.current_time_label)

        time_layout.addStretch()

        self.total_time_label = QLabel("0:00")
        self.total_time_label.setStyleSheet("font-size: 10px;")
        time_layout.addWidget(self.total_time_label)

        progress_layout.addLayout(time_layout)
        layout.addLayout(progress_layout)

        # ========== Bottom Section: Controls + Volume ==========
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)  # Canvas-inspired spacing (20px)

        # Playback controls - Canvas flat style with original colors
        # Previous button (flat purple, like Canvas)
        self.prev_button = QPushButton("⏮")
        self.prev_button.setFixedSize(70, 70)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #6c5ce7, stop:1 #6c5ce7);
                color: #ffffff;
                border: none;
                border-radius: 35px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #7c6cf7, stop:1 #7c6cf7);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #5b4bc7, stop:1 #5b4bc7);
            }
        """)
        controls_layout.addWidget(self.prev_button)

        # Play/Pause button (flat cyan, larger, like Canvas)
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(80, 80)
        self.play_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #00d2ff, stop:1 #00d2ff);
                color: #ffffff;
                border: none;
                border-radius: 40px;
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #1ee2ff, stop:1 #1ee2ff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #00b8e6, stop:1 #00b8e6);
            }
        """)
        controls_layout.addWidget(self.play_button)

        # Stop button (flat purple, like Canvas)
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(70, 70)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #6c5ce7, stop:1 #6c5ce7);
                color: #ffffff;
                border: none;
                border-radius: 35px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #7c6cf7, stop:1 #7c6cf7);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #5b4bc7, stop:1 #5b4bc7);
            }
        """)
        controls_layout.addWidget(self.stop_button)

        # Next button (flat purple, like Canvas)
        self.next_button = QPushButton("⏭")
        self.next_button.setFixedSize(70, 70)
        self.next_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #6c5ce7, stop:1 #6c5ce7);
                color: #ffffff;
                border: none;
                border-radius: 35px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #7c6cf7, stop:1 #7c6cf7);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:0, stop:0 #5b4bc7, stop:1 #5b4bc7);
            }
        """)
        controls_layout.addWidget(self.next_button)

        controls_layout.addStretch()

        # Volume control
        volume_label = QLabel("Volume:")
        controls_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(75)  # Default 75%
        self.volume_slider.setFixedWidth(100)
        controls_layout.addWidget(self.volume_slider)

        self.volume_label_value = QLabel("75%")
        self.volume_label_value.setFixedWidth(35)
        controls_layout.addWidget(self.volume_label_value)

        layout.addLayout(controls_layout)
        self.setLayout(layout)

    def _init_timer(self):
        """Initialize position update timer"""
        self.position_timer = QTimer(self)
        self.position_timer.setInterval(100)  # 100ms updates (10 FPS)
        self.position_timer.timeout.connect(self._update_position)

    def _connect_signals(self):
        """Connect widget signals to slots"""
        # Playback controls
        self.play_button.clicked.connect(self._on_play_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.prev_button.clicked.connect(self.prev_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)

        # Cover art search
        self.search_cover_button.clicked.connect(self._on_search_cover_clicked)

        # Progress slider
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)

        # Volume slider
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

    def load_song(self, song_info: Dict):
        """
        Load song information into widget

        Args:
            song_info: Dictionary with keys:
                - title: Song title
                - artist: Artist name (optional)
                - album: Album name (optional)
                - duration: Duration in seconds (optional)
                - album_art: Path to album art (optional)
        """
        self.current_song = song_info

        # Update labels
        self.title_label.setText(song_info.get('title', 'Unknown'))
        self.artist_label.setText(song_info.get('artist', 'Unknown Artist'))
        self.album_label.setText(song_info.get('album', 'Unknown Album'))

        # Update duration
        duration = song_info.get('duration', 0)
        self.total_time_label.setText(self._format_time(duration))

        # Enable progress slider
        self.progress_slider.setEnabled(True)
        self.progress_slider.setValue(0)

        # Enable cover search button if artist and album are present
        artist = song_info.get('artist')
        album = song_info.get('album')
        if artist and album and artist != 'Unknown Artist' and album != 'Unknown Album':
            self.search_cover_button.setEnabled(True)
        else:
            self.search_cover_button.setEnabled(False)

        # Load album art if provided
        album_art_path = song_info.get('album_art')
        if album_art_path:
            pixmap = QPixmap(album_art_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    100, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.album_art_label.setPixmap(scaled)
            else:
                self.album_art_label.setText("♪")
        else:
            self.album_art_label.setText("♪")

        logger.info(f"Loaded song: {song_info.get('title', 'Unknown')}")

        # Emit signal for waveform extraction
        file_path = song_info.get('file_path')
        if file_path:
            self.song_loaded.emit(file_path)

        # Emit signal for lyrics, statistics, and other metadata-based features
        self.song_metadata_changed.emit(song_info)

    def _on_play_clicked(self):
        """Handle play/pause button click"""
        self._is_playing = not self._is_playing

        if self._is_playing:
            # User wants to start/resume playback
            self.play_button.setText("⏸")  # Pause icon
            self.position_timer.start()

            if self.audio_player:
                # If we were paused, resume; otherwise play from beginning
                if self._is_paused:
                    self.audio_player.resume()
                    logger.info("Audio resumed from pause")
                    self._is_paused = False
                else:
                    self.audio_player.play()
                    logger.info("Audio playing from beginning")
        else:
            # User wants to pause
            self.play_button.setText("▶")  # Play icon
            self.position_timer.stop()

            if self.audio_player:
                self.audio_player.pause()
                logger.info("Audio paused")
                self._is_paused = True  # Mark that we're in paused state

        self.play_clicked.emit()

    def _on_stop_clicked(self):
        """Handle stop button click"""
        self._is_playing = False
        self._is_paused = False  # Clear paused state on stop
        self.play_button.setText("▶")
        self.position_timer.stop()
        self.progress_slider.setValue(0)
        self.current_time_label.setText("0:00")

        # Actually stop the audio player
        if self.audio_player:
            self.audio_player.stop()
            logger.info("Audio stopped")

        self.stop_clicked.emit()

    def _on_search_cover_clicked(self):
        """Handle cover art search button click (on-demand)"""
        if not self.current_song:
            return

        artist = self.current_song.get('artist')
        album = self.current_song.get('album')

        if not artist or not album:
            QMessageBox.warning(
                self,
                "Missing Metadata",
                "Cannot search for cover: Artist or Album information is missing."
            )
            return

        # Disable button during search
        self.search_cover_button.setEnabled(False)
        self.search_cover_button.setText("Searching...")

        try:
            # Check if cover already exists
            if self.cover_manager.has_cover(artist, album):
                logger.info(f"Cover already exists for {artist} - {album}")

                # Load existing cover
                cover_path = self.cover_manager.get_cover_path(artist, album)
                if cover_path.exists():
                    pixmap = QPixmap(str(cover_path))
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(
                            100, 100,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.album_art_label.setPixmap(scaled)

                        QMessageBox.information(
                            self,
                            "Cover Found",
                            f"Cover art already exists for:\n{artist} - {album}"
                        )
                    else:
                        self.album_art_label.setText("♪")
                        QMessageBox.warning(
                            self,
                            "Invalid Image",
                            "Cover file exists but is invalid."
                        )
                else:
                    QMessageBox.warning(
                        self,
                        "Cover Not Found",
                        "Cover path exists but file is missing."
                    )
            else:
                # Download new cover
                logger.info(f"Searching cover for {artist} - {album}")

                success = self.cover_manager.download_cover(artist, album)

                if success:
                    # Load downloaded cover
                    cover_path = self.cover_manager.get_cover_path(artist, album)
                    pixmap = QPixmap(str(cover_path))

                    if not pixmap.isNull():
                        scaled = pixmap.scaled(
                            100, 100,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.album_art_label.setPixmap(scaled)

                        QMessageBox.information(
                            self,
                            "Cover Downloaded",
                            f"Successfully downloaded cover art for:\n{artist} - {album}"
                        )
                        logger.info(f"Cover downloaded and displayed: {cover_path}")
                    else:
                        self.album_art_label.setText("♪")
                        QMessageBox.warning(
                            self,
                            "Display Error",
                            "Cover downloaded but failed to display."
                        )
                else:
                    QMessageBox.warning(
                        self,
                        "Cover Not Found",
                        f"No cover art found for:\n{artist} - {album}\n\n"
                        f"The album may not be in the Cover Art Archive database."
                    )
                    logger.warning(f"No cover found for {artist} - {album}")

        except Exception as e:
            logger.error(f"Error searching cover: {e}")
            QMessageBox.critical(
                self,
                "Search Error",
                f"Failed to search for cover art:\n{str(e)}"
            )

        finally:
            # Re-enable button
            self.search_cover_button.setEnabled(True)
            self.search_cover_button.setText("🔍 Cover")

    def _on_slider_pressed(self):
        """Handle progress slider press (start seeking)"""
        self._is_seeking = True
        self.position_timer.stop()

    def _on_slider_released(self):
        """Handle progress slider release (seek to position)"""
        self._is_seeking = False

        if self.current_song:
            duration = self.current_song.get('duration', 0)
            if duration > 0:
                # Convert slider value (0-1000) to seconds
                position = (self.progress_slider.value() / 1000.0) * duration
                self.seek_requested.emit(position)
                logger.debug(f"Seek requested: {position:.2f}s")

                # Actually seek in audio player
                if self.audio_player:
                    self.audio_player.seek(position)
                    logger.info(f"Audio seeked to: {position:.2f}s")

        if self._is_playing:
            self.position_timer.start()

    def _on_volume_changed(self, value: int):
        """
        Handle volume slider change

        Args:
            value: Volume value (0-100)
        """
        # Update label
        self.volume_label_value.setText(f"{value}%")

        # Emit signal with 0.0-1.0 range
        volume_float = value / 100.0
        self.volume_changed.emit(volume_float)

        # Update audio player if available
        if self.audio_player:
            self.audio_player.set_volume(volume_float)

    def _update_position(self):
        """Update position display (called by timer)"""
        if not self.audio_player or not self.current_song or self._is_seeking:
            return

        try:
            # Get current position from audio player
            position = self.audio_player.get_position()
            duration = self.current_song.get('duration', 0)

            # Update time label
            self.current_time_label.setText(self._format_time(position))

            # Update progress slider
            if duration > 0:
                slider_value = int((position / duration) * 1000)
                self.progress_slider.setValue(slider_value)

            # Emit position changed signal (for visualizer sync)
            self.position_changed.emit(position)

            # Check if song ended
            if not self.audio_player.is_playing() and self._is_playing:
                # Song ended
                self._on_stop_clicked()
                logger.info("Song ended")

        except Exception as e:
            logger.error(f"Position update error: {e}")

    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to MM:SS

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (e.g., "3:45")
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def set_playing(self, is_playing: bool):
        """
        Set playing state externally

        Args:
            is_playing: True if playing, False otherwise
        """
        self._is_playing = is_playing

        if is_playing:
            self.play_button.setText("⏸")
            self.position_timer.start()
        else:
            self.play_button.setText("▶")
            self.position_timer.stop()

    def cleanup(self):
        """Cleanup resources"""
        self.position_timer.stop()
        logger.info("NowPlayingWidget cleaned up")
