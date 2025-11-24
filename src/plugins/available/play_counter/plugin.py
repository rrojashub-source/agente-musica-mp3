"""
Play Counter Plugin
Tracks play counts for songs and provides statistics

This is an example plugin demonstrating:
- Hook registration (ON_SONG_PLAY, ON_SONG_END)
- Plugin settings
- Data persistence
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict

# Import from parent plugins package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from plugins.plugin_base import Plugin, PluginMetadata, PluginHook

logger = logging.getLogger(__name__)


class PlayCounterPlugin(Plugin):
    """
    Tracks how many times each song has been played.
    Provides statistics and most-played songs list.
    """

    def __init__(self):
        super().__init__()
        self._play_counts: Dict[str, int] = defaultdict(int)
        self._last_played: Dict[str, str] = {}
        self._data_file: Optional[Path] = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="play_counter",
            display_name="Play Counter",
            version="1.0.0",
            author="NEXUS Team",
            description="Tracks play counts and provides listening statistics",
            hooks=[PluginHook.ON_SONG_PLAY, PluginHook.ON_SONG_END]
        )

    def on_enable(self) -> bool:
        """Enable plugin and register hooks"""
        try:
            # Setup data file
            data_dir = Path.home() / ".nexus_music" / "plugins" / "play_counter"
            data_dir.mkdir(parents=True, exist_ok=True)
            self._data_file = data_dir / "play_data.json"

            # Load existing data
            self._load_data()

            # Register hooks
            self.register_hook(PluginHook.ON_SONG_PLAY, self._on_song_play)
            self.register_hook(PluginHook.ON_SONG_END, self._on_song_end)

            logger.info("PlayCounter plugin enabled")
            return True

        except Exception as e:
            logger.error(f"Failed to enable PlayCounter: {e}")
            return False

    def on_disable(self) -> bool:
        """Disable plugin and save data"""
        try:
            # Save data before disabling
            self._save_data()

            # Unregister hooks
            self.unregister_hook(PluginHook.ON_SONG_PLAY, self._on_song_play)
            self.unregister_hook(PluginHook.ON_SONG_END, self._on_song_end)

            logger.info("PlayCounter plugin disabled")
            return True

        except Exception as e:
            logger.error(f"Failed to disable PlayCounter: {e}")
            return False

    def _on_song_play(self, song_data: Dict[str, Any]) -> None:
        """Handler for ON_SONG_PLAY hook"""
        song_id = self._get_song_id(song_data)
        if song_id:
            self._play_counts[song_id] += 1
            self._last_played[song_id] = datetime.now().isoformat()
            logger.debug(f"Play count for {song_id}: {self._play_counts[song_id]}")

    def _on_song_end(self, song_data: Dict[str, Any]) -> None:
        """Handler for ON_SONG_END hook"""
        # Save data periodically when songs end
        self._save_data()

    def _get_song_id(self, song_data: Dict[str, Any]) -> Optional[str]:
        """Get unique identifier for a song"""
        # Try different keys for song identification
        if 'id' in song_data:
            return str(song_data['id'])
        elif 'file_path' in song_data:
            return song_data['file_path']
        elif 'title' in song_data and 'artist' in song_data:
            return f"{song_data['artist']}|{song_data['title']}"
        return None

    def _load_data(self) -> None:
        """Load play data from file"""
        if self._data_file and self._data_file.exists():
            try:
                with open(self._data_file, 'r') as f:
                    data = json.load(f)
                    self._play_counts = defaultdict(int, data.get('play_counts', {}))
                    self._last_played = data.get('last_played', {})
            except Exception as e:
                logger.error(f"Failed to load play data: {e}")

    def _save_data(self) -> None:
        """Save play data to file"""
        if self._data_file:
            try:
                data = {
                    'play_counts': dict(self._play_counts),
                    'last_played': self._last_played
                }
                with open(self._data_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save play data: {e}")

    # ==========================================
    # Public API
    # ==========================================

    def get_play_count(self, song_id: str) -> int:
        """Get play count for a specific song"""
        return self._play_counts.get(song_id, 0)

    def get_last_played(self, song_id: str) -> Optional[str]:
        """Get last played timestamp for a song"""
        return self._last_played.get(song_id)

    def get_most_played(self, limit: int = 10) -> list:
        """Get most played songs"""
        sorted_songs = sorted(
            self._play_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_songs[:limit]

    def get_total_plays(self) -> int:
        """Get total number of plays across all songs"""
        return sum(self._play_counts.values())

    def get_unique_songs_played(self) -> int:
        """Get number of unique songs played"""
        return len(self._play_counts)

    def get_statistics(self) -> Dict[str, Any]:
        """Get complete statistics"""
        return {
            'total_plays': self.get_total_plays(),
            'unique_songs': self.get_unique_songs_played(),
            'most_played': self.get_most_played(5),
            'average_plays': (
                self.get_total_plays() / self.get_unique_songs_played()
                if self.get_unique_songs_played() > 0 else 0
            )
        }
