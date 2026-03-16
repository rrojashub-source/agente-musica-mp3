"""
Remote Controller — Phase 2.1

Manages RemoteServer integration: connects callbacks,
handles commands from mobile interface, updates now playing info.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QWidget

from core.audio_player import AudioPlayer
from utils.constants import REMOTE_UPDATE_INTERVAL_MS

logger = logging.getLogger(__name__)


class RemoteController(QObject):
    """Bridges RemoteServer with audio player and UI"""

    def __init__(self, audio_player: AudioPlayer, now_playing: QWidget, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.audio_player: AudioPlayer = audio_player
        self.now_playing: QWidget = now_playing
        self._remote_server: Optional[Any] = None
        self._remote_update_timer: Optional[QTimer] = None

        # Late-bound references
        self._global_next_callback: Optional[Callable[[], None]] = None
        self._global_prev_callback: Optional[Callable[[], None]] = None

    def set_navigation_callbacks(self, next_callback: Callable[[], None], prev_callback: Callable[[], None]) -> None:
        """Set callbacks for next/prev that route through PlaybackController"""
        self._global_next_callback = next_callback
        self._global_prev_callback = prev_callback

    def connect_server(self) -> None:
        """Connect RemoteServer callbacks to audio player and controls"""
        try:
            from services.remote_server import RemoteServer

            server = RemoteServer.get_instance()
            self._remote_server = server

            # Connect Qt signal (thread-safe) to handle commands
            if hasattr(server, "command_received"):
                server.command_received.connect(self.handle_command)
                logger.info("Connected to RemoteServer command_received signal")

            # Start timer to update now_playing info for mobile interface
            self._remote_update_timer = QTimer()
            self._remote_update_timer.timeout.connect(self.update_now_playing)
            self._remote_update_timer.start(REMOTE_UPDATE_INTERVAL_MS)

            # Force immediate update
            QTimer.singleShot(100, self.update_now_playing)

            logger.info("Remote server callbacks connected to audio player")

        except (ImportError, RuntimeError, AttributeError) as e:
            logger.error(f"Failed to connect remote server: {e}")

    def handle_command(self, command: str, params: dict[str, Any]) -> None:
        """Handle remote commands in main Qt thread (thread-safe via signal)"""
        logger.info(f"Handling remote command: {command} with params: {params}")

        try:
            if command == "play":
                self.audio_player.play()
                if hasattr(self.now_playing, "set_playing"):
                    self.now_playing.set_playing(True)

            elif command == "pause":
                self.audio_player.pause()
                if hasattr(self.now_playing, "set_playing"):
                    self.now_playing.set_playing(False)

            elif command == "toggle":
                if self.audio_player.is_playing():
                    self.audio_player.pause()
                    if hasattr(self.now_playing, "set_playing"):
                        self.now_playing.set_playing(False)
                else:
                    self.audio_player.play()
                    if hasattr(self.now_playing, "set_playing"):
                        self.now_playing.set_playing(True)

            elif command == "next":
                if self._global_next_callback:
                    self._global_next_callback()

            elif command == "previous":
                if self._global_prev_callback:
                    self._global_prev_callback()

            elif command == "volume":
                volume = params.get("volume", 100)
                self.audio_player.set_volume(volume / 100.0)
                # Sync volume slider and label in now_playing widget
                if hasattr(self.now_playing, "volume_slider"):
                    self.now_playing.volume_slider.blockSignals(True)
                    self.now_playing.volume_slider.setValue(volume)
                    self.now_playing.volume_slider.blockSignals(False)
                if hasattr(self.now_playing, "volume_label_value"):
                    self.now_playing.volume_label_value.setText(f"{volume}%")

            elif command == "seek":
                position = params.get("position", 0)
                self.audio_player.seek(position)

            logger.info(f"Remote command '{command}' executed in main thread")

        except (RuntimeError, AttributeError, ValueError) as e:
            logger.error(f"Error handling remote command '{command}': {e}")

    def update_now_playing(self) -> None:
        """Update RemoteServer with current playback info"""
        if not self._remote_server:
            return

        try:
            from services.remote_server import NowPlayingInfo

            title = ""
            artist = ""
            album = ""

            if hasattr(self.now_playing, "current_song"):
                song = self.now_playing.current_song
                if song:
                    title = song.get("title", "")
                    artist = song.get("artist", "")
                    album = song.get("album", "")

            position = self.audio_player.get_position() if self.audio_player else 0
            duration = self.audio_player.get_duration() if self.audio_player else 0
            is_playing = self.audio_player.is_playing() if self.audio_player else False
            volume = int(self.audio_player.get_volume() * 100)

            info = NowPlayingInfo(
                title=title,
                artist=artist,
                album=album,
                duration=int(duration),
                position=int(position),
                is_playing=is_playing,
                volume=volume,
            )
            self._remote_server.update_now_playing(info)

        except Exception:  # noqa: BLE001 — intentional: called every 500ms, any error is transient
            pass  # Silently ignore to avoid log spam on frequent timer tick
