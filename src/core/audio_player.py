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
- Gapless playback (queue next track)
- End-of-track callbacks

Created: November 13, 2025
Updated: November 24, 2025 - Added gapless playback support
"""
import logging
import os
import threading
from typing import Optional, Callable, List
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
        # Thread safety: RLock protects all mutable state fields
        self._lock = threading.RLock()

        self._current_file = None
        self._duration = 0.0
        self._state = PlaybackState.STOPPED
        self._start_time = 0.0
        self._paused_position = 0.0  # Track position when paused
        self._start_offset = 0.0  # Track where playback started (for seek)

        # Gapless playback support
        self._queued_file = None  # Next track queued for gapless playback
        self._queued_duration = 0.0
        self._gapless_enabled = True
        self._on_track_end_callbacks: List[Callable[[str], None]] = []
        self._end_event_timer = None
        self._crossfade_ms = 0  # Crossfade duration (0 = gapless, no crossfade)

        # Initialize pygame.mixer
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._pygame = pygame

            # Set up end-of-track event
            self._MUSIC_END_EVENT = pygame.USEREVENT + 1
            pygame.mixer.music.set_endevent(self._MUSIC_END_EVENT)

            logger.info("AudioPlayer initialized with pygame.mixer (gapless enabled)")
        except ImportError:
            logger.error("pygame not installed - audio playback unavailable")
            self._pygame = None
        except (OSError, RuntimeError) as e:
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
            with self._lock:
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
                except Exception as e:  # MutagenError inherits from Exception
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
            with self._lock:
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
            with self._lock:
                # Save current position before pausing
                if self._state == PlaybackState.PLAYING:
                    self._paused_position = self._get_position_unlocked()

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
            with self._lock:
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
            with self._lock:
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
            with self._lock:
                # Store current state
                was_playing = self._pygame.mixer.music.get_busy()
                was_paused = self._state == PlaybackState.PAUSED
                logger.debug(f"Seek to {position:.2f}s - was_playing={was_playing}, was_paused={was_paused}")

                # Stop current playback
                self._pygame.mixer.music.stop()

                # Reload the file
                self._pygame.mixer.music.load(self._current_file)

                # Use play(start=position) - works reliably with MP3
                logger.debug(f"Calling pygame play(start={position:.2f})")
                self._pygame.mixer.music.play(start=position)
                self._state = PlaybackState.PLAYING
                self._start_time = self._pygame.time.get_ticks() / 1000.0 - position
                self._start_offset = position  # Remember where we started playing from

                # If it was paused or stopped, pause it again at the new position
                if was_paused or not was_playing:
                    logger.debug(f"Re-pausing at position {position:.2f}s")
                    self._pygame.mixer.music.pause()
                    self._state = PlaybackState.PAUSED
                    self._paused_position = position  # Save new paused position

            logger.debug(f"Seek completed to {position:.2f}s")
        except Exception as e:
            logger.error(f"Seek failed: {e}")

    def _get_position_unlocked(self) -> float:
        """Get position without acquiring lock (for internal use when lock is held)"""
        if not self._pygame:
            return 0.0

        if self._state == PlaybackState.PAUSED:
            return self._paused_position

        if self._state == PlaybackState.STOPPED:
            return 0.0

        try:
            pos_ms = self._pygame.mixer.music.get_pos()
            elapsed = pos_ms / 1000.0
            return self._start_offset + elapsed
        except Exception as e:
            logger.error(f"Failed to get position: {e}")
            return 0.0

    def get_position(self) -> float:
        """
        Get current playback position in seconds

        Returns:
            Current position in seconds
        """
        with self._lock:
            return self._get_position_unlocked()

    def get_duration(self) -> float:
        """
        Get total duration in seconds

        Returns:
            Duration in seconds
        """
        with self._lock:
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

    def get_volume(self) -> float:
        """
        Get current volume level

        Returns:
            Volume level (0.0 - 1.0)
        """
        if not self._pygame:
            return 1.0

        try:
            return self._pygame.mixer.music.get_volume()
        except Exception:
            return 1.0

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
        with self._lock:
            return self._state

    def cleanup(self):
        """Cleanup resources"""
        if self._end_event_timer:
            self._end_event_timer.cancel()

        if self._pygame:
            try:
                self._pygame.mixer.music.stop()
                self._pygame.mixer.quit()
                logger.info("AudioPlayer cleaned up")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    # ==========================================
    # Gapless Playback Methods
    # ==========================================

    def queue_next(self, file_path: str) -> bool:
        """
        Queue next track for gapless playback

        The queued track will start immediately when the current track ends,
        providing seamless transitions between songs.

        Args:
            file_path: Path to the next MP3 file

        Returns:
            True if queued successfully, False otherwise

        Example:
            player.load("song1.mp3")
            player.play()
            player.queue_next("song2.mp3")  # Will play seamlessly after song1
        """
        if not self._pygame:
            logger.error("pygame not available")
            return False

        if not os.path.exists(file_path):
            logger.error(f"Queue file not found: {file_path}")
            return False

        if not self._gapless_enabled:
            logger.warning("Gapless playback is disabled")
            return False

        try:
            # Queue the next track using pygame's built-in queue
            self._pygame.mixer.music.queue(file_path)
            self._queued_file = file_path

            # Pre-calculate duration for the queued file
            try:
                from mutagen.mp3 import MP3
                audio = MP3(file_path)
                self._queued_duration = audio.info.length
            except Exception as e:
                logger.warning(f"Failed to get queued track duration: {e}")
                self._queued_duration = 0.0

            logger.info(f"Queued for gapless: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to queue {file_path}: {e}")
            return False

    def clear_queue(self):
        """Clear the queued next track"""
        self._queued_file = None
        self._queued_duration = 0.0
        logger.debug("Queue cleared")

    def get_queued_file(self) -> Optional[str]:
        """
        Get the currently queued file path

        Returns:
            Path to queued file, or None if no file queued
        """
        return self._queued_file

    def set_gapless_enabled(self, enabled: bool):
        """
        Enable or disable gapless playback

        Args:
            enabled: True to enable, False to disable
        """
        self._gapless_enabled = enabled
        logger.info(f"Gapless playback: {'enabled' if enabled else 'disabled'}")

    def is_gapless_enabled(self) -> bool:
        """Check if gapless playback is enabled"""
        return self._gapless_enabled

    def set_crossfade(self, duration_ms: int):
        """
        Set crossfade duration between tracks

        Args:
            duration_ms: Crossfade duration in milliseconds (0 = no crossfade)

        Note: Crossfade is a future feature - currently only gapless (0ms) is supported
        """
        self._crossfade_ms = max(0, duration_ms)
        logger.info(f"Crossfade set to {self._crossfade_ms}ms")

    def get_crossfade(self) -> int:
        """Get current crossfade duration in milliseconds"""
        return self._crossfade_ms

    # ==========================================
    # Track End Event Handling
    # ==========================================

    def on_track_end(self, callback: Callable[[str], None]):
        """
        Register callback for track end event

        The callback receives the path of the track that just ended.
        Use this to implement playlist advancement, shuffle, etc.

        Args:
            callback: Function to call when track ends. Receives file_path as argument.

        Example:
            def handle_track_end(file_path):
                print(f"Track ended: {file_path}")
                # Load next track from playlist

            player.on_track_end(handle_track_end)
        """
        if callback not in self._on_track_end_callbacks:
            self._on_track_end_callbacks.append(callback)
            logger.debug(f"Track end callback registered (total: {len(self._on_track_end_callbacks)})")

    def remove_track_end_callback(self, callback: Callable[[str], None]):
        """Remove a track end callback"""
        if callback in self._on_track_end_callbacks:
            self._on_track_end_callbacks.remove(callback)
            logger.debug("Track end callback removed")

    def check_track_end(self) -> bool:
        """
        Check if track has ended and handle transition

        This should be called periodically (e.g., from a timer) to detect
        when the current track ends and trigger callbacks.

        Returns:
            True if track ended, False otherwise
        """
        if not self._pygame:
            return False

        with self._lock:
            # Check if music stopped playing
            if self._state == PlaybackState.PLAYING and not self._pygame.mixer.music.get_busy():
                ended_file = self._current_file

                # If there's a queued track, it's now playing
                if self._queued_file:
                    logger.info(f"Gapless transition: {self._queued_file}")
                    self._current_file = self._queued_file
                    self._duration = self._queued_duration
                    self._queued_file = None
                    self._queued_duration = 0.0
                    self._start_time = self._pygame.time.get_ticks() / 1000.0
                    self._start_offset = 0.0
                else:
                    # No queued track - playback stopped
                    self._state = PlaybackState.STOPPED
                    logger.info(f"Track ended: {ended_file}")
            else:
                return False

        # Notify callbacks outside lock to prevent deadlocks
        self._notify_track_end(ended_file)
        return True

    def _notify_track_end(self, file_path: str):
        """Notify all registered callbacks that track ended"""
        for callback in self._on_track_end_callbacks:
            try:
                callback(file_path)
            except Exception as e:
                logger.error(f"Track end callback error: {e}")

    def start_end_detection(self, interval_ms: int = 100):
        """
        Start automatic track end detection

        Args:
            interval_ms: Check interval in milliseconds (default: 100ms)
        """
        def check_loop():
            if self._state == PlaybackState.PLAYING:
                self.check_track_end()

            # Schedule next check
            if self._pygame and self._state != PlaybackState.STOPPED:
                self._end_event_timer = threading.Timer(
                    interval_ms / 1000.0,
                    check_loop
                )
                self._end_event_timer.daemon = True
                self._end_event_timer.start()

        # Start the loop
        check_loop()
        logger.debug(f"Track end detection started (interval: {interval_ms}ms)")

    def stop_end_detection(self):
        """Stop automatic track end detection"""
        if self._end_event_timer:
            self._end_event_timer.cancel()
            self._end_event_timer = None
            logger.debug("Track end detection stopped")
