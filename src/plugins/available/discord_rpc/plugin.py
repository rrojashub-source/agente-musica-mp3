"""
Discord Rich Presence Plugin for NEXUS Music Manager
Shows currently playing song in Discord status

Requirements:
    pip install pypresence

Features:
- Display current song title and artist in Discord
- Show album art (if available via URL)
- Display playback progress
- Auto-connect to Discord on enable
- Graceful handling when Discord is not running

Created: November 24, 2025
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

from plugins.plugin_base import Plugin, PluginHook, PluginMetadata

logger = logging.getLogger(__name__)

# Check for pypresence
try:
    from pypresence import InvalidID, InvalidPipe, Presence

    HAS_PYPRESENCE = True
except ImportError:
    HAS_PYPRESENCE = False
    logger.warning("pypresence not installed. Run: pip install pypresence")


class DiscordRPCPlugin(Plugin):
    """
    Discord Rich Presence Plugin

    Shows what you're listening to in your Discord status.
    Requires Discord desktop app to be running.
    """

    # Discord Application ID (create at https://discord.com/developers/applications)
    # This is a public ID for NEXUS Music Manager
    DISCORD_APP_ID = "1234567890123456789"  # Placeholder - needs real ID

    def __init__(self) -> None:
        super().__init__()

        self._rpc: Optional["Presence"] = None
        self._connected: bool = False
        self._current_song: Optional[Dict[str, Any]] = None
        self._update_thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._last_update_time: float = 0
        self._update_interval: int = 15  # Seconds between updates (Discord rate limit)

    # Settings schema (used by GUI)
    SETTINGS_SCHEMA = {
        "app_id": {
            "type": "string",
            "label": "Discord App ID",
            "description": "Your Discord application ID (optional)",
            "default": DISCORD_APP_ID,
        },
        "show_album": {
            "type": "bool",
            "label": "Show Album Name",
            "description": "Display album name in status",
            "default": True,
        },
        "show_elapsed": {
            "type": "bool",
            "label": "Show Elapsed Time",
            "description": "Display playback progress",
            "default": True,
        },
        "idle_message": {
            "type": "string",
            "label": "Idle Message",
            "description": "Message when not playing",
            "default": "Browsing music library",
        },
    }

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="discord_rpc",
            display_name="Discord RPC",
            version="1.0.0",
            author="NEXUS Team",
            description="Show currently playing song in Discord status",
            dependencies=[],
            hooks=[PluginHook.ON_SONG_PLAY, PluginHook.ON_SONG_PAUSE, PluginHook.ON_SONG_END, PluginHook.ON_APP_CLOSE],
        )

    def on_enable(self) -> bool:
        """Enable plugin and connect to Discord"""
        if not HAS_PYPRESENCE:
            logger.error("Cannot enable Discord RPC: pypresence not installed")
            return False

        # Register hooks
        self.register_hook(PluginHook.ON_SONG_PLAY, self._on_song_play)
        self.register_hook(PluginHook.ON_SONG_PAUSE, self._on_song_pause)
        self.register_hook(PluginHook.ON_SONG_END, self._on_song_end)
        self.register_hook(PluginHook.ON_APP_CLOSE, self._on_app_close)

        # Connect to Discord
        success = self._connect_discord()

        if success:
            # Start update thread
            self._running = True
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True, name="DiscordRPC-Update")
            self._update_thread.start()
            logger.info("Discord RPC plugin enabled")

        return success

    def on_disable(self) -> bool:
        """Disable plugin and disconnect from Discord"""
        self._running = False

        if self._update_thread:
            self._update_thread.join(timeout=2)

        self._disconnect_discord()
        logger.info("Discord RPC plugin disabled")
        return True

    def _connect_discord(self) -> bool:
        """Connect to Discord RPC"""
        try:
            app_id = self.get_setting("app_id", self.DISCORD_APP_ID)
            self._rpc = Presence(app_id)
            self._rpc.connect()
            self._connected = True
            logger.info("Connected to Discord RPC")

            # Set initial presence
            self._update_presence(idle=True)

            return True
        except InvalidID:
            logger.error("Invalid Discord App ID")
            return False
        except InvalidPipe:
            logger.warning("Discord not running or RPC disabled")
            return False
        except Exception as e:  # Plugin isolation - must not crash host
            logger.error(f"Failed to connect to Discord: {e}")
            return False

    def _disconnect_discord(self) -> None:
        """Disconnect from Discord RPC"""
        if self._rpc and self._connected:
            try:
                self._rpc.clear()
                self._rpc.close()
            except (RuntimeError, OSError) as e:
                logger.debug(f"Error closing Discord RPC: {e}")
            finally:
                self._connected = False
                self._rpc = None

    def _update_loop(self) -> None:
        """Background thread to periodically update presence"""
        while self._running:
            try:
                # Reconnect if disconnected
                if not self._connected:
                    self._connect_discord()

                # Update presence (respecting rate limits)
                current_time = time.time()
                if current_time - self._last_update_time >= self._update_interval:
                    if self._current_song:
                        self._update_presence()
                    self._last_update_time = current_time

            except Exception as e:  # Plugin isolation - must not crash host
                logger.debug(f"Discord RPC update error: {e}")
                self._connected = False

            time.sleep(1)

    def _update_presence(self, idle: bool = False) -> None:
        """Update Discord presence"""
        if not self._rpc or not self._connected:
            return

        try:
            if idle or not self._current_song:
                # Idle state
                idle_msg = self.get_setting("idle_message", "Browsing music library")
                self._rpc.update(
                    state=idle_msg,
                    details="NEXUS Music Manager",
                    large_image="nexus_logo",
                    large_text="NEXUS Music Manager",
                )
            else:
                # Playing song
                song = self._current_song
                title = song.get("title", "Unknown Title")
                artist = song.get("artist", "Unknown Artist")

                details = f"{title}"
                state = f"by {artist}"

                # Add album if enabled
                if self.get_setting("show_album", True) and song.get("album"):
                    state += f" ({song['album']})"

                # Build presence data
                presence_data = {
                    "details": details[:128],  # Discord limit
                    "state": state[:128],
                    "large_image": "nexus_logo",
                    "large_text": "NEXUS Music Manager",
                    "small_image": "play_icon",
                    "small_text": "Playing",
                }

                # Add elapsed time if enabled
                if self.get_setting("show_elapsed", True) and song.get("start_time"):
                    presence_data["start"] = str(int(song["start_time"]))  # type: ignore[arg-type]

                self._rpc.update(**presence_data)  # type: ignore[arg-type]

        except Exception as e:  # Plugin isolation - must not crash host
            logger.debug(f"Failed to update Discord presence: {e}")
            self._connected = False

    def _on_song_play(self, song_data: Dict[str, Any]) -> None:
        """Handle song play event"""
        self._current_song = {
            "title": str(song_data.get("title", "Unknown")),
            "artist": str(song_data.get("artist", "Unknown")),
            "album": str(song_data.get("album", "")),
            "duration": song_data.get("duration", 0),
            "start_time": time.time(),
        }
        self._update_presence()
        logger.debug(f"Discord RPC: Now playing {self._current_song['title']}")

    def _on_song_pause(self, song_data: Optional[Dict[str, Any]] = None) -> None:
        """Handle song pause event"""
        if self._current_song:
            self._current_song["start_time"] = None  # Remove elapsed time
        self._update_presence()
        logger.debug("Discord RPC: Playback paused")

    def _on_song_end(self, song_data: Optional[Dict[str, Any]] = None) -> None:
        """Handle song end event"""
        self._current_song = None
        self._update_presence(idle=True)
        logger.debug("Discord RPC: Song ended")

    def _on_app_close(self) -> None:
        """Handle app close event"""
        self._disconnect_discord()


# Export plugin class
__plugin_class__ = DiscordRPCPlugin
