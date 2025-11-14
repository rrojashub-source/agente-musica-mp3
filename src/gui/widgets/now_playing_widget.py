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

Created: November 13, 2025
"""
import logging
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap

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
    """

    # Signals
    play_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    seek_requested = pyqtSignal(float)
    volume_changed = pyqtSignal(float)
    position_changed = pyqtSignal(float)  # Emits current position in seconds

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

        # Album art thumbnail (100x100)
        self.album_art_label = QLabel()
        self.album_art_label.setFixedSize(100, 100)
        self.album_art_label.setFrameStyle(QFrame.Shape.Box)
        self.album_art_label.setStyleSheet("background-color: #333; color: #fff;")
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setText("♪")  # Placeholder
        top_layout.addWidget(self.album_art_label)

        # Song info
        info_layout = QVBoxLayout()

        self.title_label = QLabel("No song playing")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self.title_label)

        self.artist_label = QLabel("Artist")
        self.artist_label.setStyleSheet("font-size: 12px; color: #666;")
        info_layout.addWidget(self.artist_label)

        self.album_label = QLabel("Album")
        self.album_label.setStyleSheet("font-size: 12px; color: #666;")
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

        # Playback controls
        self.prev_button = QPushButton("⏮")
        self.prev_button.setFixedWidth(40)
        controls_layout.addWidget(self.prev_button)

        self.play_button = QPushButton("▶")
        self.play_button.setFixedWidth(50)
        self.play_button.setStyleSheet("font-size: 16px;")
        controls_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedWidth(40)
        controls_layout.addWidget(self.stop_button)

        self.next_button = QPushButton("⏭")
        self.next_button.setFixedWidth(40)
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

    def _on_play_clicked(self):
        """Handle play/pause button click"""
        self._is_playing = not self._is_playing

        if self._is_playing:
            self.play_button.setText("⏸")  # Pause icon
            self.position_timer.start()

            # Actually play or resume the audio
            if self.audio_player:
                # Check if paused - use resume(), otherwise use play()
                from core.audio_player import PlaybackState
                if self.audio_player.get_state() == PlaybackState.PAUSED:
                    self.audio_player.resume()
                    logger.info("Audio resumed")
                else:
                    self.audio_player.play()
                    logger.info("Audio playing")
        else:
            self.play_button.setText("▶")  # Play icon
            self.position_timer.stop()

            # Actually pause the audio
            if self.audio_player:
                self.audio_player.pause()
                logger.info("Audio paused")

        self.play_clicked.emit()

    def _on_stop_clicked(self):
        """Handle stop button click"""
        self._is_playing = False
        self.play_button.setText("▶")
        self.position_timer.stop()
        self.progress_slider.setValue(0)
        self.current_time_label.setText("0:00")

        # Actually stop the audio player
        if self.audio_player:
            self.audio_player.stop()
            logger.info("Audio stopped")

        self.stop_clicked.emit()

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
