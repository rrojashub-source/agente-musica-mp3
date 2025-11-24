"""
Plugin Manager
Handles loading, enabling, disabling and executing plugins
"""
import os
import sys
import json
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field

try:
    from PyQt6.QtCore import QObject, pyqtSignal
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QObject = object

from .plugin_base import Plugin, PluginHook, PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class PluginState:
    """Tracks state of a loaded plugin"""
    plugin: Plugin
    enabled: bool = False
    load_error: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)


class PluginManager(QObject if HAS_QT else object):
    """
    Manages all plugins in NEXUS Music Manager.

    Features:
    - Auto-discovery of plugins in plugins/ directory
    - Enable/disable plugins at runtime
    - Persist plugin states
    - Execute hooks across all enabled plugins
    - Plugin settings management

    Usage:
        manager = PluginManager.get_instance()
        manager.load_plugins()
        manager.enable_plugin("my_plugin")
        manager.execute_hook(PluginHook.ON_SONG_PLAY, song_data)
    """

    # Singleton instance
    _instance: Optional['PluginManager'] = None

    # PyQt6 signals (if available)
    if HAS_QT:
        plugin_loaded = pyqtSignal(str)           # plugin_name
        plugin_enabled = pyqtSignal(str)          # plugin_name
        plugin_disabled = pyqtSignal(str)         # plugin_name
        plugin_error = pyqtSignal(str, str)       # plugin_name, error_message
        hook_executed = pyqtSignal(str, int)      # hook_name, handlers_count

    def __init__(self, plugins_dir: str = None, data_dir: str = None):
        """
        Initialize Plugin Manager.

        Args:
            plugins_dir: Directory containing plugins (default: src/plugins/available)
            data_dir: Directory for plugin data/settings (default: ~/.nexus_music/plugins)
        """
        if HAS_QT:
            super().__init__()

        # Set directories
        if plugins_dir:
            self._plugins_dir = Path(plugins_dir)
        else:
            self._plugins_dir = Path(__file__).parent / "available"

        if data_dir:
            self._data_dir = Path(data_dir)
        else:
            self._data_dir = Path.home() / ".nexus_music" / "plugins"

        # Create directories if needed
        self._plugins_dir.mkdir(parents=True, exist_ok=True)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # Plugin registry
        self._plugins: Dict[str, PluginState] = {}

        # Settings file
        self._settings_file = self._data_dir / "plugin_settings.json"

        # Load saved settings
        self._load_settings()

    @classmethod
    def get_instance(cls, plugins_dir: str = None, data_dir: str = None) -> 'PluginManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls(plugins_dir, data_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)"""
        cls._instance = None

    # ==========================================
    # Plugin Loading
    # ==========================================

    def load_plugins(self) -> int:
        """
        Discover and load all plugins from plugins directory.

        Returns:
            Number of plugins successfully loaded
        """
        loaded_count = 0

        # Add plugins directory to path
        if str(self._plugins_dir) not in sys.path:
            sys.path.insert(0, str(self._plugins_dir))

        # Scan for plugin modules
        for item in self._plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # Directory-based plugin
                plugin_file = item / "plugin.py"
                if plugin_file.exists():
                    if self._load_plugin_from_file(plugin_file, item.name):
                        loaded_count += 1
            elif item.suffix == '.py' and not item.name.startswith('_'):
                # Single-file plugin
                if self._load_plugin_from_file(item, item.stem):
                    loaded_count += 1

        logger.info(f"Loaded {loaded_count} plugins")

        # Auto-enable plugins that were previously enabled
        self._restore_enabled_state()

        return loaded_count

    def _load_plugin_from_file(self, file_path: Path, plugin_name: str) -> bool:
        """
        Load a plugin from a Python file.

        Args:
            file_path: Path to the plugin file
            plugin_name: Name to use for the plugin module

        Returns:
            True if plugin was loaded successfully
        """
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"nexus_plugin_{plugin_name}",
                file_path
            )
            if spec is None or spec.loader is None:
                logger.error(f"Cannot load plugin spec: {file_path}")
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find Plugin subclass
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, Plugin) and
                    attr is not Plugin):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.warning(f"No Plugin subclass found in {file_path}")
                return False

            # Instantiate plugin
            plugin_instance = plugin_class()
            plugin_name = plugin_instance.metadata.name

            # Register plugin
            self._plugins[plugin_name] = PluginState(
                plugin=plugin_instance,
                enabled=False,
                settings=self._get_saved_settings(plugin_name)
            )

            # Load saved settings into plugin
            plugin_instance.load_settings(self._plugins[plugin_name].settings)

            logger.info(f"Loaded plugin: {plugin_name} v{plugin_instance.version}")

            if HAS_QT:
                self.plugin_loaded.emit(plugin_name)

            return True

        except Exception as e:
            logger.error(f"Failed to load plugin from {file_path}: {e}")
            if HAS_QT:
                self.plugin_error.emit(plugin_name, str(e))
            return False

    def load_plugin_class(self, plugin_class: Type[Plugin]) -> bool:
        """
        Load a plugin from a class directly (useful for testing).

        Args:
            plugin_class: Plugin subclass to instantiate

        Returns:
            True if plugin was loaded successfully
        """
        try:
            plugin_instance = plugin_class()
            plugin_name = plugin_instance.metadata.name

            self._plugins[plugin_name] = PluginState(
                plugin=plugin_instance,
                enabled=False,
                settings=self._get_saved_settings(plugin_name)
            )

            plugin_instance.load_settings(self._plugins[plugin_name].settings)

            logger.info(f"Loaded plugin class: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin class: {e}")
            return False

    # ==========================================
    # Plugin Enable/Disable
    # ==========================================

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_name: Name of the plugin to enable

        Returns:
            True if plugin was enabled successfully
        """
        if plugin_name not in self._plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return False

        state = self._plugins[plugin_name]
        if state.enabled:
            logger.warning(f"Plugin already enabled: {plugin_name}")
            return True

        try:
            # Check dependencies
            for dep in state.plugin.metadata.dependencies:
                if dep not in self._plugins or not self._plugins[dep].enabled:
                    logger.error(f"Plugin {plugin_name} requires {dep} to be enabled")
                    return False

            # Enable plugin
            if state.plugin.on_enable():
                state.enabled = True
                state.plugin._set_enabled(True)
                self._save_settings()

                logger.info(f"Enabled plugin: {plugin_name}")
                if HAS_QT:
                    self.plugin_enabled.emit(plugin_name)
                return True
            else:
                logger.error(f"Plugin {plugin_name} failed to enable")
                return False

        except Exception as e:
            logger.error(f"Error enabling plugin {plugin_name}: {e}")
            state.load_error = str(e)
            if HAS_QT:
                self.plugin_error.emit(plugin_name, str(e))
            return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_name: Name of the plugin to disable

        Returns:
            True if plugin was disabled successfully
        """
        if plugin_name not in self._plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return False

        state = self._plugins[plugin_name]
        if not state.enabled:
            logger.warning(f"Plugin already disabled: {plugin_name}")
            return True

        try:
            # Check if other plugins depend on this one
            for name, other_state in self._plugins.items():
                if (other_state.enabled and
                    plugin_name in other_state.plugin.metadata.dependencies):
                    logger.error(f"Cannot disable {plugin_name}: {name} depends on it")
                    return False

            # Disable plugin
            if state.plugin.on_disable():
                state.enabled = False
                state.plugin._set_enabled(False)
                self._save_settings()

                logger.info(f"Disabled plugin: {plugin_name}")
                if HAS_QT:
                    self.plugin_disabled.emit(plugin_name)
                return True
            else:
                logger.error(f"Plugin {plugin_name} failed to disable")
                return False

        except Exception as e:
            logger.error(f"Error disabling plugin {plugin_name}: {e}")
            if HAS_QT:
                self.plugin_error.emit(plugin_name, str(e))
            return False

    # ==========================================
    # Hook Execution
    # ==========================================

    def execute_hook(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """
        Execute a hook across all enabled plugins.

        Args:
            hook: The hook to execute
            *args: Arguments to pass to handlers
            **kwargs: Keyword arguments to pass to handlers

        Returns:
            List of return values from all handlers
        """
        results = []
        handlers_count = 0

        for name, state in self._plugins.items():
            if not state.enabled:
                continue

            handlers = state.plugin.get_handlers(hook)
            for handler in handlers:
                try:
                    result = handler(*args, **kwargs)
                    results.append(result)
                    handlers_count += 1
                except Exception as e:
                    logger.error(f"Plugin {name} handler error for {hook.name}: {e}")

        if HAS_QT and handlers_count > 0:
            self.hook_executed.emit(hook.name, handlers_count)

        return results

    # ==========================================
    # Plugin Access
    # ==========================================

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a plugin instance by name"""
        if plugin_name in self._plugins:
            return self._plugins[plugin_name].plugin
        return None

    def get_all_plugins(self) -> List[Plugin]:
        """Get all loaded plugins"""
        return [state.plugin for state in self._plugins.values()]

    def get_enabled_plugins(self) -> List[Plugin]:
        """Get all enabled plugins"""
        return [
            state.plugin for state in self._plugins.values()
            if state.enabled
        ]

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin info as dictionary"""
        if plugin_name not in self._plugins:
            return None

        state = self._plugins[plugin_name]
        return {
            'metadata': state.plugin.metadata.to_dict(),
            'enabled': state.enabled,
            'error': state.load_error
        }

    def get_all_plugin_info(self) -> List[Dict[str, Any]]:
        """Get info for all plugins"""
        return [
            {
                'metadata': state.plugin.metadata.to_dict(),
                'enabled': state.enabled,
                'error': state.load_error
            }
            for state in self._plugins.values()
        ]

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled"""
        if plugin_name in self._plugins:
            return self._plugins[plugin_name].enabled
        return False

    # ==========================================
    # Settings Management
    # ==========================================

    def _load_settings(self) -> None:
        """Load plugin settings from file"""
        self._saved_settings: Dict[str, Dict[str, Any]] = {}

        if self._settings_file.exists():
            try:
                with open(self._settings_file, 'r') as f:
                    self._saved_settings = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load plugin settings: {e}")

    def _save_settings(self) -> None:
        """Save plugin settings to file"""
        settings = {}
        for name, state in self._plugins.items():
            settings[name] = {
                'enabled': state.enabled,
                'settings': state.plugin.get_all_settings()
            }

        try:
            with open(self._settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save plugin settings: {e}")

    def _get_saved_settings(self, plugin_name: str) -> Dict[str, Any]:
        """Get saved settings for a plugin"""
        if plugin_name in self._saved_settings:
            return self._saved_settings[plugin_name].get('settings', {})
        return {}

    def _restore_enabled_state(self) -> None:
        """Restore enabled state for plugins"""
        for name, saved in self._saved_settings.items():
            if saved.get('enabled', False) and name in self._plugins:
                self.enable_plugin(name)

    def save_plugin_settings(self, plugin_name: str, settings: Dict[str, Any]) -> bool:
        """Save settings for a specific plugin"""
        if plugin_name not in self._plugins:
            return False

        self._plugins[plugin_name].plugin.load_settings(settings)
        self._plugins[plugin_name].settings = settings
        self._save_settings()
        return True
