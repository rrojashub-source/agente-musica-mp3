"""
Scrobbler Plugin
Example plugin that demonstrates external service integration

This plugin shows how to:
- Connect to external APIs (Last.fm style)
- Use plugin settings
- Provide a settings UI
"""

import logging
from typing import Any, Dict

from plugins.plugin_base import Plugin, PluginHook, PluginMetadata
from utils.constants import DEFAULT_ARTIST

logger = logging.getLogger(__name__)


class ScrobblerPlugin(Plugin):
    """
    Scrobbles played songs to a music tracking service.
    Currently a demonstration - actual API integration would go here.
    """

    def __init__(self) -> None:
        super().__init__()
        self._scrobble_queue: list[dict[str, Any]] = []
        self._MAX_QUEUE_SIZE: int = 100
        self._current_song: dict[str, Any] | None = None
        self._play_start_time: float | None = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="scrobbler",
            display_name="Scrobbler",
            version="1.0.0",
            author="NEXUS Team",
            description="Scrobble your plays to Last.fm or ListenBrainz",
            website="https://www.last.fm/api",
            hooks=[PluginHook.ON_SONG_PLAY, PluginHook.ON_SONG_END, PluginHook.ON_SONG_PAUSE],
        )

    def on_enable(self) -> bool:
        """Enable plugin"""
        try:
            # Check for API key in settings
            api_key = self.get_setting("api_key", "")
            if not api_key:
                logger.warning("Scrobbler: No API key configured")

            # Register hooks
            self.register_hook(PluginHook.ON_SONG_PLAY, self._on_song_play)
            self.register_hook(PluginHook.ON_SONG_END, self._on_song_end)
            self.register_hook(PluginHook.ON_SONG_PAUSE, self._on_song_pause)

            logger.info("Scrobbler plugin enabled")
            return True

        except Exception as e:  # Plugin isolation - must not crash host
            logger.error(f"Failed to enable Scrobbler: {e}")
            return False

    def on_disable(self) -> bool:
        """Disable plugin"""
        try:
            # Flush any pending scrobbles
            self._flush_queue()

            # Unregister hooks
            self.unregister_hook(PluginHook.ON_SONG_PLAY, self._on_song_play)
            self.unregister_hook(PluginHook.ON_SONG_END, self._on_song_end)
            self.unregister_hook(PluginHook.ON_SONG_PAUSE, self._on_song_pause)

            logger.info("Scrobbler plugin disabled")
            return True

        except Exception as e:  # Plugin isolation - must not crash host
            logger.error(f"Failed to disable Scrobbler: {e}")
            return False

    def _on_song_play(self, song_data: Dict[str, Any]) -> None:
        """Handle song play - send 'now playing' update"""
        import time

        self._current_song = song_data
        self._play_start_time = time.time()

        # In real implementation, send 'now playing' to API
        logger.debug(f"Now playing: {song_data.get('title', 'Unknown')}")

        if self.get_setting("api_key"):
            self._send_now_playing(song_data)

    def _on_song_end(self, song_data: Dict[str, Any]) -> None:
        """Handle song end - scrobble if played long enough"""
        import time

        if self._current_song and self._play_start_time:
            play_duration = time.time() - self._play_start_time
            song_duration = song_data.get("duration", 0)

            # Scrobble rules: played > 4 min OR > 50% of track
            min_play_time = min(240, song_duration * 0.5) if song_duration else 30

            if play_duration >= min_play_time:
                self._add_to_queue(song_data)

        self._current_song = None
        self._play_start_time = None

    def _on_song_pause(self, song_data: Dict[str, Any]) -> None:
        """Handle pause - track time accurately"""
        # Could implement pause time tracking here
        pass

    def _send_now_playing(self, song_data: Dict[str, Any]) -> bool:
        """Send 'now playing' to scrobble service"""
        # In real implementation:
        # - Build API request
        # - Send to Last.fm/ListenBrainz
        # - Handle response
        logger.debug(f"Would send now playing: {song_data.get('title')}")
        return True

    def _add_to_queue(self, song_data: Dict[str, Any]) -> None:
        """Add song to scrobble queue"""
        import time

        scrobble = {
            "artist": song_data.get("artist", DEFAULT_ARTIST),
            "track": song_data.get("title", "Unknown Track"),
            "album": song_data.get("album", ""),
            "timestamp": int(time.time()),
        }
        self._scrobble_queue.append(scrobble)
        logger.debug(f"Queued scrobble: {scrobble['track']}")

        # Drop oldest if queue exceeds max size (prevent unbounded growth)
        if len(self._scrobble_queue) > self._MAX_QUEUE_SIZE:
            dropped = len(self._scrobble_queue) - self._MAX_QUEUE_SIZE
            self._scrobble_queue = self._scrobble_queue[dropped:]
            logger.warning(f"Scrobble queue overflow: dropped {dropped} oldest entries")

        # Auto-flush if queue is getting large
        if len(self._scrobble_queue) >= 10:
            self._flush_queue()

    def _flush_queue(self) -> bool:
        """Send all queued scrobbles"""
        if not self._scrobble_queue:
            return True

        if not self.get_setting("api_key"):
            logger.warning("Cannot scrobble: No API key")
            return False

        # In real implementation, batch send to API
        count = len(self._scrobble_queue)
        logger.info(f"Would scrobble {count} tracks")

        self._scrobble_queue.clear()
        return True

    # ==========================================
    # Public API
    # ==========================================

    def get_queue_size(self) -> int:
        """Get number of pending scrobbles"""
        return len(self._scrobble_queue)

    def force_scrobble(self) -> bool:
        """Force immediate scrobble of queue"""
        return self._flush_queue()

    def is_authenticated(self) -> bool:
        """Check if API key is configured"""
        return bool(self.get_setting("api_key"))

    def get_settings_schema(self) -> Dict[str, Any]:
        """Return settings schema for UI generation"""
        return {
            "api_key": {"type": "password", "label": "API Key", "description": "Your Last.fm or ListenBrainz API key"},
            "service": {
                "type": "select",
                "label": "Service",
                "options": ["last.fm", "listenbrainz"],
                "default": "last.fm",
            },
            "scrobble_threshold": {
                "type": "number",
                "label": "Scrobble Threshold (%)",
                "min": 10,
                "max": 100,
                "default": 50,
                "description": "Percentage of song that must be played to scrobble",
            },
        }
