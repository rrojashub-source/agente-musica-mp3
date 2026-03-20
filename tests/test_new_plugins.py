"""
Tests for New Plugins (Discord RPC, Lyrics)
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ==========================================
# Discord RPC Plugin Tests
# ==========================================


class TestDiscordRPCPlugin:
    """Tests for Discord RPC plugin"""

    def test_plugin_metadata(self):
        """Test plugin has correct metadata"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        metadata = plugin.metadata

        assert metadata.name == "discord_rpc"
        assert metadata.display_name == "Discord RPC"
        assert metadata.version == "1.0.0"
        # Settings schema is now a class attribute
        assert "show_album" in plugin.SETTINGS_SCHEMA
        assert "show_elapsed" in plugin.SETTINGS_SCHEMA

    def test_plugin_init_state(self):
        """Test plugin initial state"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()

        assert plugin._connected is False
        assert plugin._rpc is None
        assert plugin._current_song is None
        assert plugin._running is False

    def test_enable_without_pypresence(self):
        """Test enable fails gracefully without pypresence"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin, HAS_PYPRESENCE

        if HAS_PYPRESENCE:
            pytest.skip("pypresence is installed, can't test missing dependency")

        plugin = DiscordRPCPlugin()
        result = plugin.on_enable()

        assert result is False

    def test_disable(self):
        """Test plugin disable"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._running = True

        result = plugin.on_disable()

        assert result is True
        assert plugin._running is False

    @patch("plugins.available.discord_rpc.plugin.HAS_PYPRESENCE", True)
    def test_on_song_play_handler(self):
        """Test song play handler updates current song"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._connected = True
        plugin._rpc = MagicMock()

        song_data = {"title": "Test Song", "artist": "Test Artist", "album": "Test Album", "duration": 180}

        plugin._on_song_play(song_data)

        assert plugin._current_song is not None
        assert plugin._current_song["title"] == "Test Song"
        assert plugin._current_song["artist"] == "Test Artist"

    def test_on_song_pause_handler(self):
        """Test song pause handler clears start time"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._current_song = {"title": "Test", "artist": "Artist", "start_time": 12345}

        plugin._on_song_pause()

        assert plugin._current_song["start_time"] is None

    def test_on_song_end_handler(self):
        """Test song end handler clears current song"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._current_song = {"title": "Test"}

        plugin._on_song_end()

        assert plugin._current_song is None

    def test_disconnect_clears_state(self):
        """Test disconnect clears RPC state"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._connected = True
        plugin._rpc = MagicMock()

        plugin._disconnect_discord()

        assert plugin._connected is False
        assert plugin._rpc is None


# ==========================================
# Lyrics Plugin Tests
# ==========================================

LYRICS_PLUGIN_EXISTS = (Path(__file__).parent.parent / "src" / "plugins" / "available" / "lyrics").exists()


@pytest.mark.skipif(not LYRICS_PLUGIN_EXISTS, reason="Lyrics plugin not implemented yet (TDD RED phase)")
class TestLyricsPlugin:
    """Tests for Lyrics plugin"""

    def test_plugin_metadata(self):
        """Test plugin has correct metadata"""
        from plugins.available.lyrics.plugin import LyricsPlugin

        plugin = LyricsPlugin()
        metadata = plugin.metadata

        assert metadata.name == "lyrics"
        assert metadata.display_name == "Lyrics"
        assert metadata.version == "1.0.0"
        # Settings schema is now a class attribute
        assert "genius_api_key" in plugin.SETTINGS_SCHEMA
        assert "auto_fetch" in plugin.SETTINGS_SCHEMA
        assert "save_to_file" in plugin.SETTINGS_SCHEMA

    def test_plugin_init_state(self):
        """Test plugin initial state"""
        from plugins.available.lyrics.plugin import LyricsPlugin

        plugin = LyricsPlugin()

        assert plugin._cache_dir is None
        assert plugin._genius_client is None
        assert plugin._current_lyrics is None

    def test_enable_creates_cache_dir(self, tmp_path):
        """Test enable creates cache directory"""
        from plugins.available.lyrics.plugin import LyricsPlugin

        with patch.object(Path, "home", return_value=tmp_path):
            plugin = LyricsPlugin()
            result = plugin.on_enable()

        assert result is True
        expected_dir = tmp_path / ".nexus_music" / "lyrics_cache"
        assert expected_dir.exists()

    def test_disable(self):
        """Test plugin disable"""
        from plugins.available.lyrics.plugin import LyricsPlugin

        plugin = LyricsPlugin()
        plugin._genius_client = MagicMock()

        result = plugin.on_disable()

        assert result is True
        assert plugin._genius_client is None

    def test_lyrics_result_dataclass(self):
        """Test LyricsResult dataclass"""
        from plugins.available.lyrics.plugin import LyricsResult

        result = LyricsResult(
            title="Test Song",
            artist="Test Artist",
            lyrics="These are the lyrics...",
            source="Genius",
            url="https://genius.com/test",
        )

        assert result.title == "Test Song"
        assert result.artist == "Test Artist"
        assert result.synced is False

    def test_cache_key_generation(self):
        """Test cache key generation is consistent"""
        from plugins.available.lyrics.plugin import LyricsPlugin

        plugin = LyricsPlugin()

        key1 = plugin._get_cache_key("Test Song", "Test Artist")
        key2 = plugin._get_cache_key("Test Song", "Test Artist")
        key3 = plugin._get_cache_key("Different Song", "Test Artist")

        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different inputs = different key
        assert len(key1) == 32  # MD5 hash length

    def test_cache_key_case_insensitive(self):
        """Test cache key is case insensitive"""
        from plugins.available.lyrics.plugin import LyricsPlugin

        plugin = LyricsPlugin()

        key1 = plugin._get_cache_key("Test Song", "Test Artist")
        key2 = plugin._get_cache_key("TEST SONG", "TEST ARTIST")

        assert key1 == key2

    def test_get_cached_lyrics_returns_none_without_cache_dir(self):
        """Test get cached lyrics returns None without cache dir"""
        from plugins.available.lyrics.plugin import LyricsPlugin

        plugin = LyricsPlugin()
        plugin._cache_dir = None

        result = plugin._get_cached_lyrics("Test", "Artist")

        assert result is None

    def test_cache_lyrics(self, tmp_path):
        """Test caching lyrics works"""
        from plugins.available.lyrics.plugin import LyricsPlugin, LyricsResult

        plugin = LyricsPlugin()
        plugin._cache_dir = tmp_path

        lyrics_result = LyricsResult(
            title="Cached Song", artist="Cached Artist", lyrics="These lyrics are cached", source="Test"
        )

        plugin._cache_lyrics(lyrics_result)

        # Verify cache file was created
        cache_key = plugin._get_cache_key("Cached Song", "Cached Artist")
        cache_file = tmp_path / f"{cache_key}.json"
        assert cache_file.exists()

        # Verify we can retrieve it
        retrieved = plugin._get_cached_lyrics("Cached Song", "Cached Artist")
        assert retrieved is not None
        assert retrieved.lyrics == "These lyrics are cached"

    def test_register_lyrics_callback(self):
        """Test registering lyrics callbacks"""
        from plugins.available.lyrics.plugin import LyricsPlugin

        plugin = LyricsPlugin()
        callback = Mock()

        plugin.register_lyrics_callback(callback)

        assert callback in plugin._lyrics_callbacks

    def test_save_lyrics_file(self, tmp_path):
        """Test saving lyrics to .lrc file"""
        from plugins.available.lyrics.plugin import LyricsPlugin, LyricsResult

        plugin = LyricsPlugin()

        lyrics_result = LyricsResult(
            title="Save Test", artist="Test Artist", lyrics="Line 1\nLine 2\nLine 3", source="Test"
        )

        mp3_path = tmp_path / "test_song.mp3"
        mp3_path.touch()

        plugin._save_lyrics_file(lyrics_result, str(mp3_path))

        lrc_path = tmp_path / "test_song.lrc"
        assert lrc_path.exists()

        content = lrc_path.read_text()
        assert "[ti:Save Test]" in content
        assert "[ar:Test Artist]" in content
        assert "Line 1" in content

    def test_get_current_lyrics(self):
        """Test getting current lyrics"""
        from plugins.available.lyrics.plugin import LyricsPlugin, LyricsResult

        plugin = LyricsPlugin()
        plugin._current_lyrics = LyricsResult(title="Current", artist="Artist", lyrics="Current lyrics", source="Test")

        result = plugin.get_current_lyrics()

        assert result is not None
        assert result.title == "Current"


# ==========================================
# Integration Tests
# ==========================================


class TestPluginIntegration:
    """Integration tests for plugins with PluginManager"""

    def test_plugins_discovered(self):
        """Test new plugins are discovered by manager"""
        from plugins.plugin_manager import PluginManager

        PluginManager.reset_instance()
        manager = PluginManager.get_instance()

        # Check if plugins directory exists
        plugins_dir = Path(__file__).parent.parent / "src" / "plugins" / "available"
        assert plugins_dir.exists()

        # Check discord_rpc directory exists (lyrics plugin not yet implemented)
        assert (plugins_dir / "discord_rpc").exists()

        PluginManager.reset_instance()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
