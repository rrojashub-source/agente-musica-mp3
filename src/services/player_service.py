"""
NEXUS Music Manager - Player Service
Encapsulates audio playback with business logic and PySide6 signals

Features:
- Thread-safe singleton pattern
- PySide6 signals for UI updates
- Gapless playback support
- Play queue management
- Playback statistics tracking
"""

import logging
import random
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from utils.constants import POSITION_UPDATE_INTERVAL_MS

logger = logging.getLogger(__name__)


class PlaybackState(Enum):
    """Playback state enum"""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"


class RepeatMode(Enum):
    """Repeat mode enum"""

    OFF = "off"
    ONE = "one"
    ALL = "all"


@dataclass
class NowPlaying:
    """Currently playing track info"""

    song_id: Optional[int] = None
    file_path: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    duration: float = 0.0
    position: float = 0.0
    state: PlaybackState = PlaybackState.STOPPED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "file_path": self.file_path,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "position": self.position,
            "state": self.state.value,
        }


class PlayerService(QObject):
    """
    Player Service - Manages audio playback

    Signals:
        state_changed: Emitted when playback state changes (PlaybackState)
        track_changed: Emitted when track changes (NowPlaying)
        position_changed: Emitted on position update (position_seconds)
        volume_changed: Emitted when volume changes (volume_percent)
        track_ended: Emitted when track finishes
        queue_changed: Emitted when play queue changes
        error_occurred: Emitted on errors (error_message)
    """

    # Signals
    state_changed = Signal(object)  # PlaybackState
    track_changed = Signal(object)  # NowPlaying
    position_changed = Signal(float)  # position in seconds
    volume_changed = Signal(int)  # volume 0-100
    track_ended = Signal()
    queue_changed = Signal()
    error_occurred = Signal(str)

    # Singleton (class-level for QObject compatibility)
    _instance: Optional["PlayerService"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize PlayerService"""
        super().__init__()

        self._player: Any = None
        self._now_playing: NowPlaying = NowPlaying()
        self._play_queue: List[Dict[str, Any]] = []
        self._queue_index: int = -1
        self._shuffle: bool = False
        self._repeat: RepeatMode = RepeatMode.OFF
        self._volume: int = 100
        self._position_timer: Optional[QTimer] = None

        # Setup position update timer
        self._setup_position_timer()

        logger.info("PlayerService initialized")

    @classmethod
    def get_instance(cls) -> "PlayerService":
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)"""
        with cls._lock:
            cls._instance = None

    @property
    def player(self) -> Any:
        """Lazy-load audio player"""
        if self._player is None:
            from core.audio_player import AudioPlayer

            self._player = AudioPlayer()
            self._connect_player_callbacks()
        return self._player

    def _connect_player_callbacks(self) -> None:
        """Connect to audio player callbacks"""
        if self._player:
            self._player.on_track_end(self._on_track_end)

    def _setup_position_timer(self) -> None:
        """Setup timer for position updates"""
        self._position_timer = QTimer()
        self._position_timer.timeout.connect(self._update_position)
        self._position_timer.setInterval(POSITION_UPDATE_INTERVAL_MS)  # 4 updates per second

    def _update_position(self) -> None:
        """Update position and emit signal"""
        if self._now_playing.state == PlaybackState.PLAYING:
            position = self.player.get_position()
            self._now_playing.position = position
            self.position_changed.emit(position)

    def _on_track_end(self, file_path: Optional[str] = None) -> None:
        """Handle track end event"""
        self.track_ended.emit()
        self._track_play_count()

        # Handle repeat/queue
        if self._repeat == RepeatMode.ONE:
            self.play()  # Replay same track
        elif self._queue_index < len(self._play_queue) - 1:
            self.next()  # Play next in queue
        elif self._repeat == RepeatMode.ALL and self._play_queue:
            self._queue_index = -1
            self.next()  # Restart queue
        else:
            self.stop()

    def _track_play_count(self) -> None:
        """Increment play count for current track"""
        if self._now_playing.song_id:
            try:
                from services.library_service import LibraryService

                library = LibraryService.get_instance()
                library.increment_play_count(self._now_playing.song_id)
            except (ImportError, RuntimeError) as e:
                logger.debug(f"Could not track play count: {e}")

    # ==========================================
    # Playback Control
    # ==========================================

    def play(
        self, file_path: Optional[str] = None, song_id: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Start playback

        Args:
            file_path: Path to audio file (optional if resuming)
            song_id: Song ID for tracking (optional)
            metadata: Song metadata (optional)
        """
        try:
            if file_path:
                # Load new track
                if not self.player.load(file_path):
                    self.error_occurred.emit(f"Failed to load: {file_path}")
                    return False

                # Update now playing info
                self._now_playing = NowPlaying(
                    song_id=song_id,
                    file_path=file_path,
                    title=metadata.get("title", Path(file_path).stem) if metadata else Path(file_path).stem,
                    artist=metadata.get("artist") if metadata else None,
                    album=metadata.get("album") if metadata else None,
                    duration=metadata.get("duration", 0) if metadata else self.player.get_duration(),
                    position=0.0,
                    state=PlaybackState.LOADING,
                )

            # Start playback
            if self.player.play():
                self._now_playing.state = PlaybackState.PLAYING
                self.state_changed.emit(PlaybackState.PLAYING)
                self.track_changed.emit(self._now_playing)
                self._position_timer.start()  # type: ignore[union-attr]
                logger.info(f"Playing: {self._now_playing.title}")
                return True
            else:
                self.error_occurred.emit("Failed to start playback")
                return False

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error playing: {e}")
            self.error_occurred.emit(str(e))
            return False

    def pause(self) -> bool:
        """Pause playback"""
        try:
            if self.player.pause():
                self._now_playing.state = PlaybackState.PAUSED
                self.state_changed.emit(PlaybackState.PAUSED)
                self._position_timer.stop()  # type: ignore[union-attr]
                return True
            return False
        except (OSError, RuntimeError) as e:
            logger.error(f"Error pausing: {e}")
            return False

    def resume(self) -> bool:
        """Resume playback"""
        return self.play()

    def toggle_play_pause(self) -> bool:
        """Toggle between play and pause"""
        if self._now_playing.state == PlaybackState.PLAYING:
            return self.pause()
        elif self._now_playing.state == PlaybackState.PAUSED:
            return self.resume()
        return False

    def stop(self) -> bool:
        """Stop playback"""
        try:
            self.player.stop()
            self._now_playing.state = PlaybackState.STOPPED
            self._now_playing.position = 0.0
            self.state_changed.emit(PlaybackState.STOPPED)
            self._position_timer.stop()  # type: ignore[union-attr]
            return True
        except (OSError, RuntimeError) as e:
            logger.error(f"Error stopping: {e}")
            return False

    def seek(self, position: float) -> bool:
        """
        Seek to position

        Args:
            position: Position in seconds
        """
        try:
            if self.player.seek(position):
                self._now_playing.position = position
                self.position_changed.emit(position)
                return True
            return False
        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error seeking: {e}")
            return False

    def seek_relative(self, delta: float) -> bool:
        """Seek relative to current position"""
        new_pos = max(0, self._now_playing.position + delta)
        new_pos = min(new_pos, self._now_playing.duration)
        return self.seek(new_pos)

    # ==========================================
    # Volume Control
    # ==========================================

    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)"""
        try:
            volume = max(0, min(100, volume))
            if self.player.set_volume(volume / 100.0):
                self._volume = volume
                self.volume_changed.emit(volume)
                return True
            return False
        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error setting volume: {e}")
            return False

    def get_volume(self) -> int:
        """Get current volume (0-100)"""
        return self._volume

    def mute(self) -> bool:
        """Mute audio"""
        return self.set_volume(0)

    def unmute(self) -> bool:
        """Unmute to previous volume"""
        return self.set_volume(self._volume or 100)

    # ==========================================
    # Queue Management
    # ==========================================

    def set_queue(self, songs: List[Dict[str, Any]], start_index: int = 0) -> None:
        """
        Set play queue

        Args:
            songs: List of song dictionaries (with file_path, title, etc.)
            start_index: Index to start playing from
        """
        self._play_queue = songs.copy()
        self._queue_index = start_index - 1  # Will be incremented by next()

        if self._shuffle:
            self._shuffle_queue()

        self.queue_changed.emit()

        # Start playing
        if songs:
            self.next()

    def add_to_queue(self, song: Dict[str, Any]) -> None:
        """Add song to end of queue"""
        self._play_queue.append(song)
        self.queue_changed.emit()

    def insert_next(self, song: Dict[str, Any]) -> None:
        """Insert song as next in queue"""
        insert_pos = self._queue_index + 1
        self._play_queue.insert(insert_pos, song)
        self.queue_changed.emit()

    def remove_from_queue(self, index: int) -> bool:
        """Remove song from queue by index"""
        if 0 <= index < len(self._play_queue):
            self._play_queue.pop(index)
            if index <= self._queue_index:
                self._queue_index -= 1
            self.queue_changed.emit()
            return True
        return False

    def clear_queue(self) -> None:
        """Clear play queue"""
        self._play_queue.clear()
        self._queue_index = -1
        self.queue_changed.emit()

    def get_queue(self) -> List[Dict[str, Any]]:
        """Get current queue"""
        return self._play_queue.copy()

    def get_queue_index(self) -> int:
        """Get current queue index"""
        return self._queue_index

    def next(self) -> bool:
        """Play next track in queue"""
        if not self._play_queue:
            return False

        self._queue_index += 1
        if self._queue_index >= len(self._play_queue):
            if self._repeat == RepeatMode.ALL:
                self._queue_index = 0
            else:
                self._queue_index = len(self._play_queue) - 1
                return False

        song = self._play_queue[self._queue_index]

        # Queue next for gapless if available
        if self._queue_index + 1 < len(self._play_queue):
            next_song = self._play_queue[self._queue_index + 1]
            self.player.queue_next(next_song.get("file_path", ""))

        return self.play(file_path=song.get("file_path"), song_id=song.get("id"), metadata=song)

    def previous(self) -> bool:
        """Play previous track in queue"""
        if not self._play_queue:
            return False

        # If we're past 3 seconds, restart current track
        if self._now_playing.position > 3.0:
            return self.seek(0)

        self._queue_index -= 1
        if self._queue_index < 0:
            if self._repeat == RepeatMode.ALL:
                self._queue_index = len(self._play_queue) - 1
            else:
                self._queue_index = 0
                return self.seek(0)

        song = self._play_queue[self._queue_index]
        return self.play(file_path=song.get("file_path"), song_id=song.get("id"), metadata=song)

    # ==========================================
    # Shuffle & Repeat
    # ==========================================

    def set_shuffle(self, enabled: bool) -> None:
        """Enable/disable shuffle"""
        self._shuffle = enabled
        if enabled and self._play_queue:
            self._shuffle_queue()

    def is_shuffle_enabled(self) -> bool:
        """Check if shuffle is enabled"""
        return self._shuffle

    def _shuffle_queue(self) -> None:
        """Shuffle the queue while keeping current track"""
        if self._queue_index >= 0 and self._queue_index < len(self._play_queue):
            current = self._play_queue[self._queue_index]
            remaining = self._play_queue[self._queue_index + 1 :]
            random.shuffle(remaining)
            self._play_queue = self._play_queue[: self._queue_index + 1] + remaining

    def set_repeat(self, mode: RepeatMode) -> None:
        """Set repeat mode"""
        self._repeat = mode

    def get_repeat(self) -> RepeatMode:
        """Get repeat mode"""
        return self._repeat

    def cycle_repeat(self) -> RepeatMode:
        """Cycle through repeat modes"""
        modes = [RepeatMode.OFF, RepeatMode.ALL, RepeatMode.ONE]
        current_idx = modes.index(self._repeat)
        self._repeat = modes[(current_idx + 1) % len(modes)]
        return self._repeat

    # ==========================================
    # State Getters
    # ==========================================

    def get_state(self) -> PlaybackState:
        """Get current playback state"""
        return self._now_playing.state

    def get_now_playing(self) -> NowPlaying:
        """Get current track info"""
        return self._now_playing

    def get_position(self) -> float:
        """Get current position in seconds"""
        return self._now_playing.position

    def get_duration(self) -> float:
        """Get current track duration"""
        return self._now_playing.duration

    def is_playing(self) -> bool:
        """Check if currently playing"""
        return self._now_playing.state == PlaybackState.PLAYING

    def is_paused(self) -> bool:
        """Check if paused"""
        return self._now_playing.state == PlaybackState.PAUSED

    # ==========================================
    # Gapless Playback
    # ==========================================

    def is_gapless_enabled(self) -> bool:
        """Check if gapless playback is enabled"""
        return self.player.is_gapless_enabled()  # type: ignore[no-any-return]

    def set_gapless(self, enabled: bool) -> None:
        """Enable/disable gapless playback"""
        self.player.set_gapless(enabled)

    def set_crossfade(self, duration_ms: int) -> None:
        """Set crossfade duration in milliseconds"""
        self.player.set_crossfade(duration_ms)

    def get_crossfade(self) -> int:
        """Get crossfade duration"""
        return self.player.get_crossfade()  # type: ignore[no-any-return]

    # ==========================================
    # Cleanup
    # ==========================================

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self._position_timer:
            self._position_timer.stop()
        if self._player:
            self._player.cleanup()
            self._player = None
        logger.info("PlayerService cleaned up")
