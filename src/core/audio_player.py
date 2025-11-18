"""
Audio Player Engine - Phase 6.1

Core audio playback engine using pygame.mixer for MP3 playback.

Features:
- Load MP3 files
- Play/pause/resume/stop controls
- Seek to position
- Volume control (0.0-1.0)
- Position and duration tracking
- Playback state management

Created: November 13, 2025
"""
import logging
import os
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PlaybackState(Enum):
    """Playback state enumeration"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class AudioPlayer:
    """
    Audio playback engine using pygame.mixer

    Usage:
        player = AudioPlayer()

        # Load and play
        if player.load("/path/to/song.mp3"):
            player.play()

        # Controls
        player.pause()
        player.resume()
        player.stop()

        # Seek
        player.seek(30.0)  # Jump to 30 seconds

        # Volume
        player.set_volume(0.75)  # 75%

        # Status
        position = player.get_position()
        duration = player.get_duration()
        is_playing = player.is_playing()
    """

    def __init__(self):
        """Initialize audio player"""
        self._current_file = None
        self._duration = 0.0
        self._state = PlaybackState.STOPPED
        self._start_time = 0.0
        self._paused_position = 0.0  # Track position when paused
        self._start_offset = 0.0  # Track where playback started (for seek)

        # Initialize pygame.mixer
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._pygame = pygame
            logger.info("AudioPlayer initialized with pygame.mixer")
        except ImportError:
            logger.error("pygame not installed - audio playback unavailable")
            self._pygame = None
        except Exception as e:
            logger.error(f"Failed to initialize pygame.mixer: {e}")
            self._pygame = None

    def load(self, file_path: str) -> bool:
        """
        Load MP3 file for playback

        Args:
            file_path: Path to MP3 file

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self._pygame:
            logger.error("pygame not available")
            return False

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        try:
            # Load file
            self._pygame.mixer.music.load(file_path)
            self._current_file = file_path

            # Get duration using mutagen
            try:
                from mutagen.mp3 import MP3
                audio = MP3(file_path)
                self._duration = audio.info.length
            except ImportError:
                logger.warning("mutagen not installed - duration unavailable")
                self._duration = 0.0
            except Exception as e:
                logger.warning(f"Failed to get duration: {e}")
                self._duration = 0.0

            self._state = PlaybackState.STOPPED
            logger.info(f"Loaded: {file_path} (duration: {self._duration:.2f}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return False

    def play(self):
        """Start playback from beginning"""
        if not self._pygame or not self._current_file:
            logger.warning("No file loaded")
            return

        try:
            self._pygame.mixer.music.play()
            self._state = PlaybackState.PLAYING
            self._start_time = self._pygame.time.get_ticks() / 1000.0
            self._start_offset = 0.0  # Playing from beginning
            logger.debug("Playback started")
        except Exception as e:
            logger.error(f"Failed to play: {e}")

    def pause(self):
        """Pause playback"""
        if not self._pygame:
            return

        try:
            # Save current position before pausing
            if self._state == PlaybackState.PLAYING:
                self._paused_position = self.get_position()

            self._pygame.mixer.music.pause()
            self._state = PlaybackState.PAUSED
            logger.debug(f"Playback paused at {self._paused_position:.2f}s")
        except Exception as e:
            logger.error(f"Failed to pause: {e}")

    def resume(self):
        """Resume playback from pause"""
        if not self._pygame:
            return

        try:
            self._pygame.mixer.music.unpause()
            self._state = PlaybackState.PLAYING
            logger.debug("Playback resumed")
        except Exception as e:
            logger.error(f"Failed to resume: {e}")

    def stop(self):
        """Stop playback and reset position"""
        if not self._pygame:
            return

        try:
            self._pygame.mixer.music.stop()
            self._state = PlaybackState.STOPPED
            self._paused_position = 0.0  # Reset position
            self._start_offset = 0.0  # Reset offset
            logger.debug("Playback stopped")
        except Exception as e:
            logger.error(f"Failed to stop: {e}")

    def seek(self, position: float):
        """
        Seek to position in seconds

        Args:
            position: Position in seconds

        Note: Uses play(start=position) for MP3 compatibility
              This method works reliably with MP3 files (unlike set_pos)
        """
        if not self._pygame or not self._current_file:
            logger.warning("Seek called but no pygame or no file loaded")
            return

        try:
            # Store current state
            was_playing = self.is_playing()
            was_paused = self._state == PlaybackState.PAUSED
            logger.info(f"Seek to {position:.2f}s - was_playing={was_playing}, was_paused={was_paused}")

            # Stop current playback
            self._pygame.mixer.music.stop()

            # Reload the file
            self._pygame.mixer.music.load(self._current_file)

            # Use play(start=position) - works reliably with MP3
            logger.info(f"Calling pygame play(start={position:.2f})")
            self._pygame.mixer.music.play(start=position)
            self._state = PlaybackState.PLAYING
            self._start_time = self._pygame.time.get_ticks() / 1000.0 - position
            self._start_offset = position  # Remember where we started playing from

            # If it was paused or stopped, pause it again at the new position
            if was_paused or not was_playing:
                logger.info(f"Re-pausing at position {position:.2f}s")
                self._pygame.mixer.music.pause()
                self._state = PlaybackState.PAUSED
                self._paused_position = position  # Save new paused position

            logger.info(f"Seek completed to {position:.2f}s")
        except Exception as e:
            logger.error(f"Seek failed: {e}")

    def get_position(self) -> float:
        """
        Get current playback position in seconds

        Returns:
            Current position in seconds
        """
        if not self._pygame:
            return 0.0

        # If paused, return the saved paused position
        if self._state == PlaybackState.PAUSED:
            return self._paused_position

        # If stopped, return 0
        if self._state == PlaybackState.STOPPED:
            return 0.0

        # If playing, get current position from pygame
        try:
            # pygame.mixer.music.get_pos() returns milliseconds since play() was called
            # Need to add the start offset (where we started playing from)
            pos_ms = self._pygame.mixer.music.get_pos()
            elapsed = pos_ms / 1000.0
            absolute_position = self._start_offset + elapsed
            return absolute_position
        except Exception as e:
            logger.error(f"Failed to get position: {e}")
            return 0.0

    def get_duration(self) -> float:
        """
        Get total duration in seconds

        Returns:
            Duration in seconds
        """
        return self._duration

    def set_volume(self, level: float):
        """
        Set playback volume

        Args:
            level: Volume level (0.0 = mute, 1.0 = max)
        """
        if not self._pygame:
            return

        try:
            # Clamp to valid range
            level = max(0.0, min(1.0, level))
            self._pygame.mixer.music.set_volume(level)
            logger.debug(f"Volume set to {level:.2f}")
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing

        Returns:
            True if playing, False otherwise
        """
        if not self._pygame:
            return False

        try:
            # get_busy() returns True if music is playing
            return self._pygame.mixer.music.get_busy()
        except Exception as e:
            logger.error(f"Failed to check playback state: {e}")
            return False

    def get_state(self) -> PlaybackState:
        """
        Get current playback state

        Returns:
            Current state (STOPPED, PLAYING, PAUSED)
        """
        return self._state

    def cleanup(self):
        """Cleanup resources"""
        if self._pygame:
            try:
                self._pygame.mixer.music.stop()
                self._pygame.mixer.quit()
                logger.info("AudioPlayer cleaned up")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
