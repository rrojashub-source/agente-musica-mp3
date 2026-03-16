"""
Audio Player Engine - Phase 6.1 (migrated to python-mpv)

Core audio playback engine using libmpv for audio playback.

Features:
- Load audio files (MP3, FLAC, OGG, OPUS, AAC, WAV, etc.)
- Play/pause/resume/stop controls
- Seek to position
- Volume control (0.0-1.0)
- Position and duration tracking
- Playback state management
- Native gapless playback via mpv playlist
- End-of-track callbacks via mpv events

Created: November 13, 2025
Updated: March 11, 2026 - Migrated from pygame.mixer to python-mpv
"""

import logging
import os
import sys
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PlaybackState(Enum):
    """Playback state enumeration"""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class AudioPlayer:
    """
    Audio playback engine using python-mpv (libmpv)

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

    def __init__(self) -> None:
        """Initialize audio player"""
        # Thread safety: RLock protects all mutable state fields
        self._lock: threading.RLock = threading.RLock()

        self._current_file: Optional[str] = None
        self._duration: float = 0.0
        self._state: PlaybackState = PlaybackState.STOPPED
        self._volume: float = 1.0  # 0.0-1.0 scale (mpv uses 0-100 internally)

        # Gapless playback support
        self._queued_file: Optional[str] = None
        self._queued_duration: float = 0.0
        self._gapless_enabled: bool = True
        self._on_track_end_callbacks: List[Callable[[str], None]] = []
        self._end_event_timer: Optional[threading.Timer] = None
        self._crossfade_ms: int = 0

        # Initialize mpv player
        try:
            # Ensure libmpv-2.dll is findable on Windows
            if os.name == "nt":
                if hasattr(sys, "_MEIPASS"):
                    # PyInstaller: DLL is in extraction root
                    dll_dir = sys._MEIPASS
                elif "__compiled__" in globals():
                    # Nuitka: DLL is next to executable
                    dll_dir = os.path.dirname(sys.argv[0])
                else:
                    # Development: DLL is in src/
                    dll_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if dll_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
            import mpv

            self._player: Optional[Any] = mpv.MPV(
                ytdl=False,
                video=False,  # Audio only
                terminal=False,  # No terminal output
                input_default_bindings=False,
                input_vo_keyboard=False,
            )
            # Configure for gapless audio
            self._player["gapless-audio"] = "yes"
            self._player["audio-display"] = "no"

            # Register end-of-file event handler
            @self._player.event_callback("end-file")
            def _on_end_file(event: Any) -> None:
                self._handle_track_end(event)

            self._mpv: Optional[Any] = mpv  # Keep module reference
            logger.info("AudioPlayer initialized with python-mpv (gapless enabled)")
        except ImportError:
            logger.error("python-mpv not installed - audio playback unavailable")
            self._player = None
            self._mpv = None
        except Exception as e:  # mpv raises RuntimeError/OSError for various init failures
            logger.error(f"Failed to initialize mpv: {e}")
            self._player = None
            self._mpv = None

    def _handle_track_end(self, event: Any) -> None:
        """Handle mpv end-file event for track transitions"""
        try:
            # event['reason'] can be 'eof', 'stop', 'quit', 'error', etc.
            _reason = event.get("event", {}).get("reason", None) if isinstance(event, dict) else None  # noqa: F841

            with self._lock:
                if self._state != PlaybackState.PLAYING:
                    return

                ended_file = self._current_file

                if self._queued_file:
                    # Gapless transition to queued track
                    logger.info(f"Gapless transition: {self._queued_file}")
                    self._current_file = self._queued_file
                    self._duration = self._queued_duration
                    self._queued_file = None
                    self._queued_duration = 0.0
                else:
                    self._state = PlaybackState.STOPPED
                    logger.info(f"Track ended: {ended_file}")

            # Notify callbacks outside lock
            if ended_file:
                self._notify_track_end(ended_file)
        except Exception as e:  # mpv event callback - must not crash event thread
            logger.error(f"Error handling track end: {e}")

    def load(self, file_path: str) -> bool:
        """
        Load audio file for playback

        Args:
            file_path: Path to audio file (MP3, FLAC, OGG, etc.)

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self._player:
            logger.error("mpv not available")
            return False

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        try:
            with self._lock:
                # Stop current playback if any
                try:
                    self._player.command("stop")
                except (RuntimeError, OSError):
                    pass  # mpv may not be in a stoppable state

                self._current_file = file_path
                self._state = PlaybackState.STOPPED

                # Get duration using mutagen (faster than loading in mpv)
                self._duration = self._get_file_duration(file_path)

            logger.info(f"Loaded: {file_path} (duration: {self._duration:.2f}s)")
            return True

        except Exception as e:  # mpv/mutagen can raise diverse errors on corrupt files
            logger.error(f"Failed to load {file_path}: {e}")
            return False

    def _get_file_duration(self, file_path: str) -> float:
        """Get audio file duration using mutagen"""
        try:
            from mutagen import File as MutagenFile

            audio = MutagenFile(file_path)
            if audio and audio.info:
                return audio.info.length  # type: ignore[no-any-return]
        except ImportError:
            logger.warning("mutagen not installed - duration unavailable")
        except Exception as e:  # mutagen raises diverse errors on corrupt/unknown formats
            logger.warning(f"Failed to get duration: {e}")
        return 0.0

    def play(self) -> None:
        """Start playback from beginning"""
        try:
            with self._lock:
                if not self._player or not self._current_file:
                    logger.warning("No file loaded")
                    return

                self._player.play(self._current_file)
                self._player.pause = False
                self._state = PlaybackState.PLAYING

                # Update duration from mpv if mutagen didn't get it
                if self._duration <= 0:
                    self._update_duration_from_mpv()

            logger.debug("Playback started")
        except Exception as e:  # mpv raises RuntimeError for various playback failures
            logger.error(f"Failed to play: {e}")

    def _update_duration_from_mpv(self) -> None:
        """Try to get duration from mpv (call within lock)"""
        try:
            # mpv needs a moment to parse the file
            for _ in range(10):
                dur = self._player.duration  # type: ignore[union-attr]
                if dur is not None and dur > 0:
                    self._duration = dur
                    break
                time.sleep(0.05)
        except (RuntimeError, OSError):
            pass  # mpv property access can fail during startup

    def pause(self) -> None:
        """Pause playback"""
        if not self._player:
            return

        try:
            with self._lock:
                if self._state == PlaybackState.PLAYING:
                    self._player.pause = True
                    self._state = PlaybackState.PAUSED
            logger.debug("Playback paused")
        except Exception as e:  # mpv raises RuntimeError for various state errors
            logger.error(f"Failed to pause: {e}")

    def resume(self) -> None:
        """Resume playback from pause"""
        if not self._player:
            return

        try:
            with self._lock:
                if self._state == PlaybackState.PAUSED:
                    self._player.pause = False
                    self._state = PlaybackState.PLAYING
            logger.debug("Playback resumed")
        except Exception as e:  # mpv raises RuntimeError for various state errors
            logger.error(f"Failed to resume: {e}")

    def stop(self) -> None:
        """Stop playback and reset position"""
        if not self._player:
            return

        try:
            with self._lock:
                self._player.command("stop")
                self._state = PlaybackState.STOPPED
            logger.debug("Playback stopped")
        except Exception as e:  # mpv raises RuntimeError for various state errors
            logger.error(f"Failed to stop: {e}")

    def seek(self, position: float) -> None:
        """
        Seek to position in seconds

        Args:
            position: Position in seconds
        """
        if not self._player or not self._current_file:
            logger.warning("Seek called but no mpv or no file loaded")
            return

        try:
            with self._lock:
                was_paused = self._state == PlaybackState.PAUSED

                # If stopped, need to start playback first
                if self._state == PlaybackState.STOPPED:
                    self._player.play(self._current_file)
                    self._state = PlaybackState.PLAYING
                    # Wait for mpv to be ready
                    time.sleep(0.05)

                self._player.seek(position, reference="absolute")

                if was_paused:
                    self._player.pause = True
                    self._state = PlaybackState.PAUSED

            logger.debug(f"Seek completed to {position:.2f}s")
        except Exception as e:  # mpv raises RuntimeError for various seek/state errors
            logger.error(f"Seek failed: {e}")

    def get_position(self) -> float:
        """
        Get current playback position in seconds

        Returns:
            Current position in seconds
        """
        if not self._player:
            return 0.0

        with self._lock:
            if self._state == PlaybackState.STOPPED:
                return 0.0

            try:
                pos = self._player.time_pos
                return pos if pos is not None else 0.0
            except (RuntimeError, OSError):
                return 0.0

    def get_duration(self) -> float:
        """
        Get total duration in seconds

        Returns:
            Duration in seconds
        """
        with self._lock:
            # Try getting from mpv first (more accurate)
            if self._player and self._state != PlaybackState.STOPPED:
                try:
                    dur = self._player.duration
                    if dur is not None and dur > 0:
                        self._duration = dur
                except (RuntimeError, OSError):
                    pass  # mpv property may be unavailable during transitions
            return self._duration

    def set_volume(self, level: float) -> None:
        """
        Set playback volume

        Args:
            level: Volume level (0.0 = mute, 1.0 = max)
        """
        if not self._player:
            return

        try:
            level = max(0.0, min(1.0, level))
            self._volume = level
            self._player.volume = level * 100  # mpv uses 0-100 scale
            logger.debug(f"Volume set to {level:.2f}")
        except Exception as e:  # mpv raises RuntimeError if player is in invalid state
            logger.error(f"Failed to set volume: {e}")

    def get_volume(self) -> float:
        """
        Get current volume level

        Returns:
            Volume level (0.0 - 1.0)
        """
        if not self._player:
            return 1.0

        try:
            vol = self._player.volume
            return (vol / 100.0) if vol is not None else self._volume
        except (RuntimeError, OSError):
            return self._volume

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing

        Returns:
            True if playing, False otherwise
        """
        if not self._player:
            return False

        with self._lock:
            return self._state == PlaybackState.PLAYING

    def get_state(self) -> PlaybackState:
        """
        Get current playback state

        Returns:
            Current state (STOPPED, PLAYING, PAUSED)
        """
        with self._lock:
            return self._state

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self._end_event_timer:
            self._end_event_timer.cancel()

        if self._player:
            try:
                self._player.terminate()
                logger.info("AudioPlayer cleaned up")
            except Exception as e:  # mpv terminate can raise during shutdown
                logger.error(f"Cleanup error: {e}")

    # ==========================================
    # Gapless Playback Methods
    # ==========================================

    def queue_next(self, file_path: str) -> bool:
        """
        Queue next track for gapless playback

        Args:
            file_path: Path to the next audio file

        Returns:
            True if queued successfully, False otherwise
        """
        if not self._player:
            logger.error("mpv not available")
            return False

        if not os.path.exists(file_path):
            logger.error(f"Queue file not found: {file_path}")
            return False

        if not self._gapless_enabled:
            logger.warning("Gapless playback is disabled")
            return False

        try:
            # Use mpv playlist for native gapless
            self._player.playlist_append(file_path)
            self._queued_file = file_path
            self._queued_duration = self._get_file_duration(file_path)
            logger.info(f"Queued for gapless: {file_path}")
            return True

        except Exception as e:  # mpv playlist ops raise RuntimeError for various failures
            logger.error(f"Failed to queue {file_path}: {e}")
            return False

    def clear_queue(self) -> None:
        """Clear the queued next track"""
        if self._player:
            try:
                self._player.playlist_clear()
            except (RuntimeError, OSError):
                pass  # mpv may not support playlist ops in current state
        self._queued_file = None
        self._queued_duration = 0.0
        logger.debug("Queue cleared")

    def get_queued_file(self) -> Optional[str]:
        """Get the currently queued file path"""
        return self._queued_file

    def set_gapless_enabled(self, enabled: bool) -> None:
        """Enable or disable gapless playback"""
        self._gapless_enabled = enabled
        if self._player:
            try:
                self._player["gapless-audio"] = "yes" if enabled else "no"
            except (RuntimeError, OSError):
                pass  # mpv property may not be settable
        logger.info(f"Gapless playback: {'enabled' if enabled else 'disabled'}")

    def is_gapless_enabled(self) -> bool:
        """Check if gapless playback is enabled"""
        return self._gapless_enabled

    def set_crossfade(self, duration_ms: int) -> None:
        """
        Set crossfade duration between tracks

        Args:
            duration_ms: Crossfade duration in milliseconds (0 = no crossfade)
        """
        self._crossfade_ms = max(0, duration_ms)
        if self._player and duration_ms > 0:
            try:
                self._player["audio-crossfade"] = duration_ms / 1000.0
            except (RuntimeError, OSError):
                pass  # mpv may not support crossfade property
        logger.info(f"Crossfade set to {self._crossfade_ms}ms")

    def get_crossfade(self) -> int:
        """Get current crossfade duration in milliseconds"""
        return self._crossfade_ms

    # ==========================================
    # Equalizer
    # ==========================================

    def set_equalizer_gains(self, gains: Dict[int, float]) -> None:
        """Apply equalizer gains via mpv's audio filter.

        Args:
            gains: Dict of {frequency_hz: gain_db}, e.g. {31: 0.0, 62: 2.5, ...}
        """
        if not self._player:
            return

        try:
            # Build mpv equalizer filter string
            # mpv uses superequalizer af filter: superequalizer=1b=g1:2b=g2:...
            # Band mapping: superequalizer has 18 bands, we map our 10 to the closest
            # Simpler approach: use 'equalizer' audio filter with individual bands
            band_filters = []
            for freq, gain in gains.items():
                if gain != 0.0:
                    # mpv equalizer filter: equalizer=f=freq:width_type=o:width=2:g=gain
                    band_filters.append(f"equalizer=f={freq}:width_type=o:width=2:g={gain}")

            if band_filters:
                filter_str = ",".join(band_filters)
                self._player["af"] = filter_str
            else:
                self._player["af"] = ""

            logger.debug(f"Equalizer applied: {len(gains)} bands")
        except Exception as e:  # mpv af filter can raise RuntimeError for unsupported configs
            logger.error(f"Failed to apply equalizer: {e}")

    # ==========================================
    # Track End Event Handling
    # ==========================================

    def on_track_end(self, callback: Callable[[str], None]) -> None:
        """Register callback for track end event"""
        if callback not in self._on_track_end_callbacks:
            self._on_track_end_callbacks.append(callback)
            logger.debug(f"Track end callback registered (total: {len(self._on_track_end_callbacks)})")

    def remove_track_end_callback(self, callback: Callable[[str], None]) -> None:
        """Remove a track end callback"""
        if callback in self._on_track_end_callbacks:
            self._on_track_end_callbacks.remove(callback)
            logger.debug("Track end callback removed")

    def check_track_end(self) -> bool:
        """
        Check if track has ended and handle transition

        Note: With mpv, track end is handled via events (_handle_track_end).
        This method is kept for API compatibility and can be called
        from a timer for additional safety.

        Returns:
            True if track ended, False otherwise
        """
        if not self._player:
            return False

        with self._lock:
            if self._state == PlaybackState.PLAYING:
                try:
                    idle = self._player.core_idle
                    if idle:
                        ended_file = self._current_file

                        if self._queued_file:
                            logger.info(f"Gapless transition: {self._queued_file}")
                            self._current_file = self._queued_file
                            self._duration = self._queued_duration
                            self._queued_file = None
                            self._queued_duration = 0.0
                        else:
                            self._state = PlaybackState.STOPPED
                            logger.info(f"Track ended: {ended_file}")

                        # Notify outside lock
                        threading.Thread(target=self._notify_track_end, args=(ended_file,), daemon=True).start()
                        return True
                except (RuntimeError, OSError):
                    pass  # mpv property access can fail

        return False

    def _notify_track_end(self, file_path: str) -> None:
        """Notify all registered callbacks that track ended.

        When called from a non-main thread (mpv event thread), uses
        QTimer.singleShot to marshal to Qt main thread. When called
        from the main thread (tests, polling), calls directly.
        """
        use_timer = False
        try:
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app and threading.current_thread() is not threading.main_thread():
                use_timer = True
        except ImportError:
            pass

        for callback in self._on_track_end_callbacks:
            if use_timer:
                QTimer.singleShot(0, lambda cb=callback, fp=file_path: self._safe_callback(cb, fp))
            else:
                self._safe_callback(callback, file_path)

    @staticmethod
    def _safe_callback(callback: Callable[[str], None], file_path: str) -> None:
        """Execute a callback with error handling"""
        try:
            callback(file_path)
        except Exception as e:  # user callback isolation - must not crash player
            logger.error(f"Track end callback error: {e}")

    def start_end_detection(self, interval_ms: int = 100) -> None:
        """
        Start automatic track end detection

        Args:
            interval_ms: Check interval in milliseconds (default: 100ms)
        """

        def check_loop() -> None:
            if self._state == PlaybackState.PLAYING:
                self.check_track_end()

            if self._player and self._state != PlaybackState.STOPPED:
                self._end_event_timer = threading.Timer(interval_ms / 1000.0, check_loop)
                self._end_event_timer.daemon = True
                self._end_event_timer.start()

        check_loop()
        logger.debug(f"Track end detection started (interval: {interval_ms}ms)")

    def stop_end_detection(self) -> None:
        """Stop automatic track end detection"""
        if self._end_event_timer:
            self._end_event_timer.cancel()
            self._end_event_timer = None
            logger.debug("Track end detection stopped")
