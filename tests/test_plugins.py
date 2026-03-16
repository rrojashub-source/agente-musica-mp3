"""
Tests for Plugin System
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from plugins.plugin_base import Plugin, PluginHook, PluginMetadata
from plugins.plugin_manager import PluginManager

# ==========================================
# Test Plugin Implementation
# ==========================================


class TestPlugin(Plugin):
    """Simple test plugin"""

    def __init__(self):
        super().__init__()
        self.enabled_called = False
        self.disabled_called = False
        self.handler_calls = []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_plugin",
            display_name="Test Plugin",
            version="1.0.0",
            author="Test Author",
            description="A test plugin",
            hooks=[PluginHook.ON_SONG_PLAY],
        )

    def on_enable(self) -> bool:
        self.enabled_called = True
        self.register_hook(PluginHook.ON_SONG_PLAY, self.on_song_play)
        return True

    def on_disable(self) -> bool:
        self.disabled_called = True
        return True

    def on_song_play(self, song_data: dict):
        self.handler_calls.append(song_data)
        return f"Played: {song_data.get('title')}"


class DependentPlugin(Plugin):
    """Plugin that depends on TestPlugin"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dependent_plugin",
            display_name="Dependent Plugin",
            version="1.0.0",
            author="Test Author",
            description="Depends on test_plugin",
            dependencies=["test_plugin"],
        )

    def on_enable(self) -> bool:
        return True

    def on_disable(self) -> bool:
        return True


class FailingPlugin(Plugin):
    """Plugin that fails to enable"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="failing_plugin",
            display_name="Failing Plugin",
            version="1.0.0",
            author="Test Author",
            description="Always fails",
        )

    def on_enable(self) -> bool:
        return False  # Always fail

    def on_disable(self) -> bool:
        return True


# ==========================================
# Plugin Base Tests
# ==========================================


class TestPluginBase:
    """Tests for Plugin base class"""

    def test_plugin_metadata(self):
        """Test plugin metadata access"""
        plugin = TestPlugin()

        assert plugin.name == "test_plugin"
        assert plugin.version == "1.0.0"
        assert plugin.metadata.display_name == "Test Plugin"
        assert plugin.metadata.author == "Test Author"

    def test_plugin_metadata_to_dict(self):
        """Test metadata serialization"""
        plugin = TestPlugin()
        data = plugin.metadata.to_dict()

        assert data["name"] == "test_plugin"
        assert data["version"] == "1.0.0"
        assert "ON_SONG_PLAY" in data["hooks"]

    def test_plugin_initial_state(self):
        """Test plugin starts disabled"""
        plugin = TestPlugin()
        assert not plugin.enabled

    def test_plugin_settings(self):
        """Test plugin settings"""
        plugin = TestPlugin()

        # Set and get
        plugin.set_setting("key1", "value1")
        assert plugin.get_setting("key1") == "value1"

        # Default value
        assert plugin.get_setting("nonexistent", "default") == "default"

        # Load settings
        plugin.load_settings({"key2": "value2", "key3": 123})
        assert plugin.get_setting("key2") == "value2"
        assert plugin.get_setting("key3") == 123

    def test_hook_registration(self):
        """Test hook registration"""
        plugin = TestPlugin()

        handler = Mock()
        plugin.register_hook(PluginHook.ON_SONG_PLAY, handler)

        handlers = plugin.get_handlers(PluginHook.ON_SONG_PLAY)
        assert handler in handlers

    def test_hook_unregistration(self):
        """Test hook unregistration"""
        plugin = TestPlugin()

        handler = Mock()
        plugin.register_hook(PluginHook.ON_SONG_PLAY, handler)
        plugin.unregister_hook(PluginHook.ON_SONG_PLAY, handler)

        handlers = plugin.get_handlers(PluginHook.ON_SONG_PLAY)
        assert handler not in handlers

    def test_get_handlers_empty(self):
        """Test getting handlers for unregistered hook"""
        plugin = TestPlugin()
        handlers = plugin.get_handlers(PluginHook.ON_SONG_PAUSE)
        assert handlers == []


# ==========================================
# Plugin Hook Tests
# ==========================================


class TestPluginHooks:
    """Tests for PluginHook enum"""

    def test_all_hooks_exist(self):
        """Test all expected hooks exist"""
        expected_hooks = [
            "ON_SONG_PLAY",
            "ON_SONG_PAUSE",
            "ON_SONG_STOP",
            "ON_SONG_END",
            "ON_QUEUE_CHANGE",
            "ON_SONG_IMPORT",
            "ON_SONG_DELETE",
            "ON_METADATA_UPDATE",
            "ON_LIBRARY_SCAN",
            "ON_DOWNLOAD_START",
            "ON_DOWNLOAD_COMPLETE",
            "ON_DOWNLOAD_ERROR",
            "ON_APP_START",
            "ON_APP_CLOSE",
            "ON_TAB_CHANGE",
            "ON_SYNC_START",
            "ON_SYNC_COMPLETE",
        ]

        for hook_name in expected_hooks:
            assert hasattr(PluginHook, hook_name)


# ==========================================
# Plugin Manager Tests
# ==========================================


class TestPluginManager:
    """Tests for PluginManager"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        PluginManager.reset_instance()
        yield
        PluginManager.reset_instance()

    @pytest.fixture
    def manager(self, tmp_path):
        """Create PluginManager with temp directories"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        return PluginManager.get_instance(plugins_dir=str(plugins_dir), data_dir=str(data_dir))

    def test_singleton_pattern(self, tmp_path):
        """Test singleton pattern"""
        plugins_dir = str(tmp_path / "plugins")
        data_dir = str(tmp_path / "data")

        manager1 = PluginManager.get_instance(plugins_dir, data_dir)
        manager2 = PluginManager.get_instance()

        assert manager1 is manager2

    def test_load_plugin_class(self, manager):
        """Test loading plugin from class"""
        result = manager.load_plugin_class(TestPlugin, _skip_whitelist=True)

        assert result is True
        assert manager.get_plugin("test_plugin") is not None

    def test_load_plugin_class_denied_by_whitelist(self, manager):
        """Test that non-whitelisted plugin is refused when whitelist is enforced"""
        result = manager.load_plugin_class(TestPlugin)  # No _skip_whitelist

        assert result is False
        assert manager.get_plugin("test_plugin") is None

    def test_enable_plugin(self, manager):
        """Test enabling a plugin"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)

        result = manager.enable_plugin("test_plugin")

        assert result is True
        assert manager.is_plugin_enabled("test_plugin")

        plugin = manager.get_plugin("test_plugin")
        assert plugin.enabled_called

    def test_disable_plugin(self, manager):
        """Test disabling a plugin"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager.enable_plugin("test_plugin")

        result = manager.disable_plugin("test_plugin")

        assert result is True
        assert not manager.is_plugin_enabled("test_plugin")

        plugin = manager.get_plugin("test_plugin")
        assert plugin.disabled_called

    def test_enable_nonexistent_plugin(self, manager):
        """Test enabling a plugin that doesn't exist"""
        result = manager.enable_plugin("nonexistent")
        assert result is False

    def test_enable_failing_plugin(self, manager):
        """Test enabling a plugin that fails"""
        manager.load_plugin_class(FailingPlugin, _skip_whitelist=True)

        result = manager.enable_plugin("failing_plugin")
        assert result is False

    def test_dependency_check(self, manager):
        """Test dependency checking"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager.load_plugin_class(DependentPlugin, _skip_whitelist=True)

        # Should fail - dependency not enabled
        result = manager.enable_plugin("dependent_plugin")
        assert result is False

        # Enable dependency first
        manager.enable_plugin("test_plugin")

        # Now should succeed
        result = manager.enable_plugin("dependent_plugin")
        assert result is True

    def test_cannot_disable_dependency(self, manager):
        """Test cannot disable plugin if others depend on it"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager.load_plugin_class(DependentPlugin, _skip_whitelist=True)

        manager.enable_plugin("test_plugin")
        manager.enable_plugin("dependent_plugin")

        # Should fail - dependent_plugin depends on test_plugin
        result = manager.disable_plugin("test_plugin")
        assert result is False

    def test_execute_hook(self, manager):
        """Test hook execution"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager.enable_plugin("test_plugin")

        song_data = {"title": "Test Song", "artist": "Test Artist"}
        results = manager.execute_hook(PluginHook.ON_SONG_PLAY, song_data)

        assert len(results) == 1
        assert results[0] == "Played: Test Song"

        plugin = manager.get_plugin("test_plugin")
        assert len(plugin.handler_calls) == 1
        assert plugin.handler_calls[0] == song_data

    def test_execute_hook_disabled_plugin(self, manager):
        """Test hook not executed for disabled plugins"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)
        # Don't enable

        results = manager.execute_hook(PluginHook.ON_SONG_PLAY, {"title": "Test"})

        assert len(results) == 0

    def test_get_all_plugins(self, manager):
        """Test getting all plugins"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager.load_plugin_class(FailingPlugin, _skip_whitelist=True)

        plugins = manager.get_all_plugins()
        assert len(plugins) == 2

    def test_get_enabled_plugins(self, manager):
        """Test getting enabled plugins"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager.load_plugin_class(FailingPlugin, _skip_whitelist=True)

        manager.enable_plugin("test_plugin")

        enabled = manager.get_enabled_plugins()
        assert len(enabled) == 1
        assert enabled[0].name == "test_plugin"

    def test_get_plugin_info(self, manager):
        """Test getting plugin info"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)

        info = manager.get_plugin_info("test_plugin")

        assert info is not None
        assert info["metadata"]["name"] == "test_plugin"
        assert info["enabled"] is False

    def test_get_all_plugin_info(self, manager):
        """Test getting all plugin info"""
        manager.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager.load_plugin_class(FailingPlugin, _skip_whitelist=True)

        all_info = manager.get_all_plugin_info()
        assert len(all_info) == 2

    def test_settings_persistence(self, tmp_path):
        """Test plugin settings are persisted"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        # First manager
        manager1 = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        manager1.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager1.enable_plugin("test_plugin")
        manager1.save_plugin_settings("test_plugin", {"key": "value"})

        # Second manager (simulates restart)
        PluginManager.reset_instance()
        manager2 = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        manager2.load_plugin_class(TestPlugin, _skip_whitelist=True)

        plugin = manager2.get_plugin("test_plugin")
        assert plugin.get_setting("key") == "value"

    def test_auto_enable_previously_enabled(self, tmp_path):
        """Test plugins are auto-enabled on restart"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        # First manager
        manager1 = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        manager1.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager1.enable_plugin("test_plugin")

        # Second manager (simulates restart)
        PluginManager.reset_instance()
        manager2 = PluginManager(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        manager2.load_plugin_class(TestPlugin, _skip_whitelist=True)
        manager2.load_plugins()  # This triggers auto-enable

        # Plugin should be auto-enabled
        assert manager2.is_plugin_enabled("test_plugin")


# ==========================================
# Plugin Loading from File Tests
# ==========================================


class TestPluginFileLoading:
    """Tests for loading plugins from files"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        PluginManager.reset_instance()
        yield
        PluginManager.reset_instance()

    def test_load_plugin_from_file(self, tmp_path):
        """Test loading a plugin from a Python file"""
        plugins_dir = tmp_path / "plugins"
        data_dir = tmp_path / "data"
        plugins_dir.mkdir()
        data_dir.mkdir()

        # Create a simple plugin file
        plugin_code = """
from plugins.plugin_base import Plugin, PluginMetadata

class FilePlugin(Plugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="file_plugin",
            display_name="File Plugin",
            version="1.0.0",
            author="Test",
            description="Loaded from file"
        )

    def on_enable(self):
        return True

    def on_disable(self):
        return True
"""
        plugin_file = plugins_dir / "file_plugin.py"
        plugin_file.write_text(plugin_code)

        manager = PluginManager.get_instance(plugins_dir=str(plugins_dir), data_dir=str(data_dir))
        # Whitelist the test plugin so default-deny doesn't block it
        manager.set_whitelist(["file_plugin"])
        count = manager.load_plugins()

        assert count == 1
        assert manager.get_plugin("file_plugin") is not None


# ==========================================
# Example Plugin Tests
# ==========================================


class TestPlayCounterPlugin:
    """Tests for PlayCounter example plugin"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        PluginManager.reset_instance()
        yield
        PluginManager.reset_instance()

    def test_play_counter_loads(self, tmp_path):
        """Test PlayCounter plugin can be loaded"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        plugin = PlayCounterPlugin()
        assert plugin.name == "play_counter"
        assert plugin.version == "1.0.0"

    def test_play_counter_tracks_plays(self, tmp_path):
        """Test PlayCounter tracks plays correctly"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        plugin = PlayCounterPlugin()
        plugin._data_file = tmp_path / "data.json"

        plugin.on_enable()

        # Simulate plays
        song1 = {"id": "1", "title": "Song 1"}
        song2 = {"id": "2", "title": "Song 2"}

        plugin._on_song_play(song1)
        plugin._on_song_play(song1)
        plugin._on_song_play(song2)

        assert plugin.get_play_count("1") == 2
        assert plugin.get_play_count("2") == 1
        assert plugin.get_total_plays() == 3
        assert plugin.get_unique_songs_played() == 2

    def test_play_counter_most_played(self, tmp_path):
        """Test most played functionality"""
        from plugins.available.play_counter.plugin import PlayCounterPlugin

        plugin = PlayCounterPlugin()
        plugin._data_file = tmp_path / "data.json"
        plugin.on_enable()

        # Play songs different amounts
        for _ in range(5):
            plugin._on_song_play({"id": "1", "title": "Popular"})
        for _ in range(2):
            plugin._on_song_play({"id": "2", "title": "Less Popular"})

        most_played = plugin.get_most_played(10)
        assert most_played[0] == ("1", 5)
        assert most_played[1] == ("2", 2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
