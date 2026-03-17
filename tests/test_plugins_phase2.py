"""
Phase 2 coverage tests for src/plugins/ module.

Covers uncovered paths in:
- plugin_manager.py: whitelist loading, error handlers, edge cases
- play_counter/plugin.py: on_disable, save/load data, get_statistics
- discord_rpc/plugin.py: _update_presence idle, error handling
- plugin_base.py: get_settings_widget default
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402

from plugins.plugin_base import Plugin, PluginMetadata  # noqa: E402
from plugins.plugin_manager import PluginManager  # noqa: E402


# ==========================================
# Helper test plugin
# ==========================================
class _SimplePlugin(Plugin):
    """Minimal plugin for tests"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="simple_test",
            display_name="Simple",
            version="1.0.0",
            author="Test",
            description="Simple test plugin",
        )

    def on_enable(self) -> bool:
        return True

    def on_disable(self) -> bool:
        return True


# ==========================================
# PluginBase — get_settings_widget
# ==========================================
class TestPluginBaseSettingsWidget:
    """Test default get_settings_widget returns None"""

    def test_get_settings_widget_default(self) -> None:
        plugin = _SimplePlugin()
        assert plugin.get_settings_ui() is None


# ==========================================
# PluginManager — whitelist, error paths
# ==========================================
class TestPluginManagerWhitelist:
    """Test whitelist loading and edge cases"""

    @pytest.fixture(autouse=True)
    def reset(self) -> None:
        PluginManager.reset_instance()
        yield  # type: ignore[misc]
        PluginManager.reset_instance()

    def test_load_whitelist_from_file(self, tmp_path: Path) -> None:
        """Whitelist is loaded from JSON file when present"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        # Write whitelist file
        wl_file = data_dir / "plugin_whitelist.json"
        wl_file.write_text(json.dumps({"allowed_plugins": ["discord_rpc", "play_counter"]}))

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        assert mgr._whitelist == ["discord_rpc", "play_counter"]

    def test_load_whitelist_filters_unknown(self, tmp_path: Path) -> None:
        """Unknown plugin names are removed from whitelist"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        wl_file = data_dir / "plugin_whitelist.json"
        wl_file.write_text(json.dumps({"allowed_plugins": ["play_counter", "HACKER_PLUGIN"]}))

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        assert "HACKER_PLUGIN" not in mgr._whitelist
        assert "play_counter" in mgr._whitelist

    def test_load_whitelist_null_allows_none(self, tmp_path: Path) -> None:
        """Whitelist with null allowed_plugins sets whitelist to None"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        wl_file = data_dir / "plugin_whitelist.json"
        wl_file.write_text(json.dumps({"allowed_plugins": None}))

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        assert mgr._whitelist is None

    def test_load_whitelist_invalid_json(self, tmp_path: Path) -> None:
        """Bad whitelist JSON results in deny-all"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        wl_file = data_dir / "plugin_whitelist.json"
        wl_file.write_text("{invalid json!!!")

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        assert mgr._whitelist == []  # Deny all on error

    def test_set_whitelist_io_error(self, tmp_path: Path) -> None:
        """set_whitelist handles IOError gracefully"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        # Make the whitelist file path unwritable
        mgr._whitelist_file = Path("/nonexistent/dir/whitelist.json")
        # Should not raise
        mgr.set_whitelist(["play_counter"])
        assert mgr._whitelist == ["play_counter"]

    def test_is_plugin_allowed_empty_whitelist(self, tmp_path: Path) -> None:
        """Empty whitelist falls back to bundled plugins"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        mgr._whitelist = []  # Empty

        assert mgr._is_plugin_allowed("discord_rpc") is True  # bundled
        assert mgr._is_plugin_allowed("unknown") is False


class TestPluginManagerLoadErrors:
    """Test error paths in plugin loading"""

    @pytest.fixture(autouse=True)
    def reset(self) -> None:
        PluginManager.reset_instance()
        yield  # type: ignore[misc]
        PluginManager.reset_instance()

    def test_load_plugins_missing_dir(self, tmp_path: Path) -> None:
        """load_plugins returns 0 when directory doesn't exist"""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        mgr = PluginManager(plugins_dir=str(tmp_path / "nonexistent"), data_dir=str(data_dir))
        assert mgr.load_plugins() == 0

    def test_load_plugin_from_file_no_plugin_class(self, tmp_path: Path) -> None:
        """File without Plugin subclass is rejected"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        # Write a Python file with NO Plugin subclass
        no_plugin = plugins_dir / "empty_module.py"
        no_plugin.write_text("# Just a comment\nVALUE = 42\n")

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        result = mgr._load_plugin_from_file(no_plugin, "empty_module")
        assert result is False

    def test_load_plugin_from_file_path_traversal(self, tmp_path: Path) -> None:
        """Plugin file outside plugins directory is rejected"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        outside = tmp_path / "outside"
        plugins_dir.mkdir()
        data_dir.mkdir()
        outside.mkdir()

        evil_file = outside / "evil.py"
        evil_file.write_text("# evil code")

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        result = mgr._load_plugin_from_file(evil_file, "evil")
        assert result is False

    def test_load_plugin_from_file_import_error(self, tmp_path: Path) -> None:
        """ImportError during loading is handled"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        bad_import = plugins_dir / "bad_import.py"
        bad_import.write_text("import this_does_not_exist_at_all\n")

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        result = mgr._load_plugin_from_file(bad_import, "bad_import")
        assert result is False

    def test_load_plugin_class_exception(self, tmp_path: Path) -> None:
        """load_plugin_class handles exception in constructor"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        class BrokenPlugin(Plugin):
            def __init__(self) -> None:
                raise RuntimeError("Boom")

            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(name="broken", display_name="X", version="0", author="X", description="X")

            def on_enable(self) -> bool:
                return True

            def on_disable(self) -> bool:
                return True

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        result = mgr.load_plugin_class(BrokenPlugin, _skip_whitelist=True)
        assert result is False


class TestPluginManagerEdgeCases:
    """Test enable/disable/query edge cases"""

    @pytest.fixture(autouse=True)
    def reset(self) -> None:
        PluginManager.reset_instance()
        yield  # type: ignore[misc]
        PluginManager.reset_instance()

    @pytest.fixture
    def manager(self, tmp_path: Path) -> PluginManager:
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()
        return PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))

    def test_enable_already_enabled(self, manager: PluginManager) -> None:
        """Enabling already-enabled plugin returns True"""
        manager.load_plugin_class(_SimplePlugin, _skip_whitelist=True)
        manager.enable_plugin("simple_test")
        assert manager.enable_plugin("simple_test") is True

    def test_disable_nonexistent(self, manager: PluginManager) -> None:
        """Disabling nonexistent plugin returns False"""
        assert manager.disable_plugin("ghost") is False

    def test_disable_already_disabled(self, manager: PluginManager) -> None:
        """Disabling already-disabled plugin returns True"""
        manager.load_plugin_class(_SimplePlugin, _skip_whitelist=True)
        assert manager.disable_plugin("simple_test") is True

    def test_get_plugin_info_not_found(self, manager: PluginManager) -> None:
        """get_plugin_info returns None for unknown plugin"""
        assert manager.get_plugin_info("ghost") is None

    def test_is_plugin_enabled_not_found(self, manager: PluginManager) -> None:
        """is_plugin_enabled returns False for unknown plugin"""
        assert manager.is_plugin_enabled("ghost") is False

    def test_save_plugin_settings_not_found(self, manager: PluginManager) -> None:
        """save_plugin_settings returns False for unknown plugin"""
        assert manager.save_plugin_settings("ghost", {"key": "val"}) is False

    def test_load_settings_bad_json(self, tmp_path: Path) -> None:
        """_load_settings handles corrupt settings file"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        # Write corrupt settings file
        settings_file = data_dir / "plugin_settings.json"
        settings_file.write_text("{corrupt!!")

        mgr = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        assert mgr._saved_settings == {}

    def test_save_settings_error(self, manager: PluginManager) -> None:
        """_save_settings handles OSError gracefully"""
        manager._settings_file = Path("/nonexistent/dir/settings.json")
        manager.load_plugin_class(_SimplePlugin, _skip_whitelist=True)
        # Should not raise
        manager._save_settings()

    def test_enable_exception_handler(self, manager: PluginManager) -> None:
        """Enable plugin exception is caught (plugin isolation)"""

        class CrashOnEnable(Plugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(name="crasher", display_name="X", version="0", author="X", description="X")

            def on_enable(self) -> bool:
                raise RuntimeError("Crash during enable")

            def on_disable(self) -> bool:
                return True

        manager.load_plugin_class(CrashOnEnable, _skip_whitelist=True)
        result = manager.enable_plugin("crasher")
        assert result is False

    def test_disable_exception_handler(self, manager: PluginManager) -> None:
        """Disable plugin exception is caught (plugin isolation)"""

        class CrashOnDisable(Plugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(name="crash_dis", display_name="X", version="0", author="X", description="X")

            def on_enable(self) -> bool:
                return True

            def on_disable(self) -> bool:
                raise RuntimeError("Crash during disable")

        manager.load_plugin_class(CrashOnDisable, _skip_whitelist=True)
        manager.enable_plugin("crash_dis")
        result = manager.disable_plugin("crash_dis")
        assert result is False


# ==========================================
# PlayCounter — on_disable, save/load, stats
# ==========================================
class TestPlayCounterCoverage:
    """Cover uncovered paths in play_counter plugin"""

    def test_on_disable_saves_data(self, tmp_path: Path) -> None:
        """on_disable saves data and unregisters hooks"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        plugin = PlayCounterPlugin()
        plugin.on_enable()
        # Override _data_file AFTER on_enable (which sets it to real path)
        plugin._data_file = tmp_path / "data.json"

        # Play a song so there's data
        plugin._on_song_play({"id": "1", "title": "Song"})

        result = plugin.on_disable()
        assert result is True

        # Data file should be written
        assert plugin._data_file.exists()
        data = json.loads(plugin._data_file.read_text())
        assert "1" in data["play_counts"]

    def test_on_song_end_saves(self, tmp_path: Path) -> None:
        """on_song_end triggers save"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        plugin = PlayCounterPlugin()
        plugin.on_enable()
        plugin._data_file = tmp_path / "data.json"

        plugin._on_song_play({"id": "1", "title": "Song"})
        plugin._on_song_end({"id": "1"})

        assert plugin._data_file.exists()

    def test_load_data_from_file(self, tmp_path: Path) -> None:
        """_load_data reads existing play data"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        data_file = tmp_path / "data.json"
        data_file.write_text(
            json.dumps(
                {
                    "play_counts": {"s1": 5, "s2": 3},
                    "last_played": {"s1": "2026-01-01", "s2": "2026-01-02"},
                }
            )
        )

        plugin = PlayCounterPlugin()
        plugin._data_file = data_file
        plugin._load_data()

        assert plugin.get_play_count("s1") == 5
        assert plugin.get_play_count("s2") == 3

    def test_load_data_bad_json(self, tmp_path: Path) -> None:
        """_load_data handles corrupt JSON"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        data_file = tmp_path / "data.json"
        data_file.write_text("{bad json!!")

        plugin = PlayCounterPlugin()
        plugin._data_file = data_file
        plugin._load_data()  # Should not raise

    def test_save_data_error(self, tmp_path: Path) -> None:
        """_save_data handles OSError"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        plugin = PlayCounterPlugin()
        plugin._data_file = Path("/nonexistent/dir/data.json")
        plugin._save_data()  # Should not raise

    def test_get_last_played(self, tmp_path: Path) -> None:
        """get_last_played returns timestamp"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        plugin = PlayCounterPlugin()
        plugin.on_enable()
        plugin._data_file = tmp_path / "data.json"

        plugin._on_song_play({"id": "1", "title": "Song"})
        result = plugin.get_last_played("1")
        assert result is not None

    def test_get_statistics(self, tmp_path: Path) -> None:
        """get_statistics returns complete stats dict"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        plugin = PlayCounterPlugin()
        plugin.on_enable()
        plugin._data_file = tmp_path / "data.json"
        # Reset play counts to avoid stale data from on_enable loading
        plugin._play_counts.clear()
        plugin._last_played.clear()

        for _ in range(3):
            plugin._on_song_play({"id": "1", "title": "Song A"})
        plugin._on_song_play({"id": "2", "title": "Song B"})

        stats = plugin.get_statistics()
        assert stats["total_plays"] == 4
        assert stats["unique_songs"] == 2
        assert stats["average_plays"] == 2.0
        assert len(stats["most_played"]) == 2


# ==========================================
# DiscordRPC — update_presence, error paths
# ==========================================
class TestDiscordRPCCoverage:
    """Cover uncovered paths in discord_rpc plugin"""

    def test_update_presence_idle(self) -> None:
        """_update_presence idle sends idle message"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._connected = True
        plugin._rpc = MagicMock()

        plugin._update_presence(idle=True)

        plugin._rpc.update.assert_called_once()
        call_kwargs = plugin._rpc.update.call_args
        assert "Browsing music library" in str(call_kwargs)

    def test_update_presence_with_song(self) -> None:
        """_update_presence with song data sends details"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._connected = True
        plugin._rpc = MagicMock()
        plugin._current_song = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "start_time": 12345,
        }

        plugin._update_presence()

        plugin._rpc.update.assert_called_once()
        call_kwargs = plugin._rpc.update.call_args[1]
        assert "Test Song" in call_kwargs["details"]
        assert "Test Artist" in call_kwargs["state"]

    def test_update_presence_exception(self) -> None:
        """_update_presence handles exception gracefully"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._connected = True
        plugin._rpc = MagicMock()
        plugin._rpc.update.side_effect = RuntimeError("Discord crash")

        plugin._update_presence(idle=True)

        # Should set connected to False
        assert plugin._connected is False

    def test_on_app_close_disconnects(self) -> None:
        """_on_app_close calls disconnect"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        plugin = DiscordRPCPlugin()
        plugin._connected = True
        plugin._rpc = MagicMock()

        plugin._on_app_close()

        assert plugin._connected is False

    def test_settings_schema_exists(self) -> None:
        """SETTINGS_SCHEMA has expected keys"""
        from plugins.available.discord_rpc.plugin import DiscordRPCPlugin

        schema = DiscordRPCPlugin.SETTINGS_SCHEMA
        assert "app_id" in schema
        assert "show_album" in schema
        assert "show_elapsed" in schema
        assert "idle_message" in schema
