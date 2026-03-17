"""
Plugin Manager
Handles loading, enabling, disabling and executing plugins
"""

import importlib
import importlib.util
import json
import logging
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from utils.resource_path import get_resource_path

try:
    from PySide6.QtCore import QObject, Signal

    HAS_QT = True
except ImportError:
    HAS_QT = False
    QObject = object

from .plugin_base import Plugin, PluginHook

logger = logging.getLogger(__name__)


@dataclass
class PluginState:
    """Tracks state of a loaded plugin"""

    plugin: Plugin
    enabled: bool = False
    load_error: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)


class PluginManager(QObject if HAS_QT else object):  # type: ignore[misc]
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
    _instance: Optional["PluginManager"] = None
    _lock: threading.Lock = threading.Lock()

    # PySide6 signals (if available)
    if HAS_QT:
        plugin_loaded = Signal(str)  # plugin_name
        plugin_enabled = Signal(str)  # plugin_name
        plugin_disabled = Signal(str)  # plugin_name
        plugin_error = Signal(str, str)  # plugin_name, error_message
        hook_executed = Signal(str, int)  # hook_name, handlers_count

    def __init__(self, plugins_dir: Optional[str] = None, data_dir: Optional[str] = None) -> None:
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
            self._plugins_dir = get_resource_path("plugins/available")

        if data_dir:
            self._data_dir = Path(data_dir)
        else:
            self._data_dir = Path.home() / ".nexus_music" / "plugins"

        # Create data directory (user writable), plugins dir is bundled
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # Plugin registry
        self._plugins: Dict[str, PluginState] = {}

        # SECURITY: Default-deny plugin loading. Only bundled plugins are
        # allowed unless an explicit whitelist file overrides this list.
        # This prevents arbitrary code execution from third-party plugins
        # that may appear in the plugins directory.
        self._bundled_plugins = ["discord_rpc", "play_counter", "scrobbler"]
        self._whitelist: Optional[List[str]] = list(self._bundled_plugins)
        self._whitelist_file = self._data_dir / "plugin_whitelist.json"
        self._load_whitelist()

        # Settings file
        self._settings_file = self._data_dir / "plugin_settings.json"

        # Load saved settings
        self._load_settings()

    @classmethod
    def get_instance(cls, plugins_dir: Optional[str] = None, data_dir: Optional[str] = None) -> "PluginManager":
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            with cls._lock:
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

    def _load_whitelist(self) -> None:
        """Load plugin whitelist from file.

        SECURITY: Validates entries against bundled plugins. Unknown plugin
        names are stripped and logged as warnings (defense against file tampering).
        """
        if self._whitelist_file.exists():
            try:
                with open(self._whitelist_file, "r") as f:
                    data = json.load(f)
                    raw_list = data.get("allowed_plugins", None)

                    if raw_list is not None:
                        # Filter out unknown plugin names (tamper protection)
                        unknown = [p for p in raw_list if p not in self._bundled_plugins]
                        if unknown:
                            logger.warning(f"Whitelist contains unknown plugins (removed): {unknown}")
                        self._whitelist = [p for p in raw_list if p in self._bundled_plugins]
                    else:
                        self._whitelist = None

                    logger.info(f"Plugin whitelist loaded: {self._whitelist}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load plugin whitelist: {e}")
                self._whitelist = []  # Deny all on error

    def set_whitelist(self, plugin_names: Optional[List[str]]) -> None:
        """Set plugin whitelist. None or empty = bundled plugins only, list = only allow listed."""
        self._whitelist = plugin_names
        try:
            with open(self._whitelist_file, "w") as f:
                json.dump({"allowed_plugins": plugin_names}, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save plugin whitelist: {e}")

    def _is_plugin_allowed(self, plugin_name: str) -> bool:
        """Check if a plugin is allowed by the whitelist.

        SECURITY: Default-deny. When whitelist is None or empty,
        only bundled plugins are permitted.
        """
        if not self._whitelist:
            # No whitelist or empty list -> fall back to bundled plugins only
            return plugin_name in self._bundled_plugins
        return plugin_name in self._whitelist

    def load_plugins(self) -> int:
        """
        Discover and load all whitelisted plugins from plugins directory.

        Returns:
            Number of plugins successfully loaded
        """
        loaded_count = 0

        # NOTE: Do NOT add plugins_dir to sys.path globally.
        # Each plugin is loaded via spec_from_file_location with explicit paths.

        # Scan for plugin modules
        if not self._plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self._plugins_dir}")
            return 0

        for item in self._plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                # Check whitelist before loading
                if not self._is_plugin_allowed(item.name):
                    logger.warning(f"Plugin '{item.name}' not in whitelist, skipping")
                    continue
                # Directory-based plugin
                plugin_file = item / "plugin.py"
                if plugin_file.exists():
                    if self._load_plugin_from_file(plugin_file, item.name):
                        loaded_count += 1
            elif item.suffix == ".py" and not item.name.startswith("_"):
                # Check whitelist before loading
                if not self._is_plugin_allowed(item.stem):
                    logger.warning(f"Plugin '{item.stem}' not in whitelist, skipping")
                    continue
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
            # Verify plugin file is within plugins directory (prevent path traversal)
            resolved_file = file_path.resolve()
            resolved_plugins = self._plugins_dir.resolve()
            try:
                resolved_file.relative_to(resolved_plugins)
            except ValueError:
                logger.error(f"Plugin file outside plugins directory: {file_path}")
                return False

            # Load module with explicit file path (no sys.path modification)
            spec = importlib.util.spec_from_file_location(
                f"nexus_plugin_{plugin_name}", resolved_file, submodule_search_locations=[str(resolved_file.parent)]
            )
            if spec is None or spec.loader is None:
                logger.error(f"Cannot load plugin spec: {file_path}")
                return False

            module = importlib.util.module_from_spec(spec)
            # Register in sys.modules with namespaced name to avoid collisions
            module_name = f"nexus_plugin_{plugin_name}"
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find Plugin subclass
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.warning(f"No Plugin subclass found in {file_path}")
                # Clean up module registration
                sys.modules.pop(module_name, None)
                return False

            # Instantiate plugin
            plugin_instance = plugin_class()
            plugin_name = plugin_instance.metadata.name

            # Re-validate against whitelist using actual plugin name
            if not self._is_plugin_allowed(plugin_name):
                logger.warning(f"Plugin '{plugin_name}' (from {file_path}) not in whitelist")
                sys.modules.pop(module_name, None)
                return False

            # Register plugin
            self._plugins[plugin_name] = PluginState(
                plugin=plugin_instance, enabled=False, settings=self._get_saved_settings(plugin_name)
            )

            # Load saved settings into plugin
            plugin_instance.load_settings(self._plugins[plugin_name].settings)

            logger.info(f"Loaded plugin: {plugin_name} v{plugin_instance.version}")

            if HAS_QT:
                self.plugin_loaded.emit(plugin_name)

            return True

        except ImportError as e:
            logger.error(f"Import error loading plugin {plugin_name} from {file_path}: {e}")
            if HAS_QT:
                self.plugin_error.emit(plugin_name, str(e))
            return False
        except (TypeError, AttributeError) as e:
            logger.error(f"Plugin class error for {plugin_name} from {file_path}: {e}")
            if HAS_QT:
                self.plugin_error.emit(plugin_name, str(e))
            return False
        except Exception as e:  # Plugin isolation - must not crash host
            logger.error(f"Unexpected error loading plugin {plugin_name} from {file_path}: {e}")
            if HAS_QT:
                self.plugin_error.emit(plugin_name, str(e))
            return False

    def load_plugin_class(self, plugin_class: Type[Plugin], *, _skip_whitelist: bool = False) -> bool:
        """
        Load a plugin from a class directly (useful for testing).

        Args:
            plugin_class: Plugin subclass to instantiate
            _skip_whitelist: Skip whitelist check (testing only, keyword-only)

        Returns:
            True if plugin was loaded successfully
        """
        try:
            plugin_instance = plugin_class()
            plugin_name = plugin_instance.metadata.name

            # SECURITY: Enforce whitelist even for class-based loading
            if not _skip_whitelist and not self._is_plugin_allowed(plugin_name):
                logger.warning(f"Plugin '{plugin_name}' not in whitelist, refusing to load")
                return False

            self._plugins[plugin_name] = PluginState(
                plugin=plugin_instance, enabled=False, settings=self._get_saved_settings(plugin_name)
            )

            plugin_instance.load_settings(self._plugins[plugin_name].settings)

            logger.info(f"Loaded plugin class: {plugin_name}")
            return True

        except Exception as e:  # Plugin isolation - must not crash host
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

        except Exception as e:  # Plugin isolation - must not crash host
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
                if other_state.enabled and plugin_name in other_state.plugin.metadata.dependencies:
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

        except Exception as e:  # Plugin isolation - must not crash host
            logger.error(f"Error disabling plugin {plugin_name}: {e}")
            if HAS_QT:
                self.plugin_error.emit(plugin_name, str(e))
            return False

    # ==========================================
    # Hook Execution
    # ==========================================

    def execute_hook(self, hook: PluginHook, *args: Any, **kwargs: Any) -> List[Any]:
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
                except Exception as e:  # Plugin isolation - must not crash host
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
        return [state.plugin for state in self._plugins.values() if state.enabled]

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin info as dictionary"""
        if plugin_name not in self._plugins:
            return None

        state = self._plugins[plugin_name]
        return {"metadata": state.plugin.metadata.to_dict(), "enabled": state.enabled, "error": state.load_error}

    def get_all_plugin_info(self) -> List[Dict[str, Any]]:
        """Get info for all plugins"""
        return [
            {"metadata": state.plugin.metadata.to_dict(), "enabled": state.enabled, "error": state.load_error}
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
                with open(self._settings_file, "r") as f:
                    self._saved_settings = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to load plugin settings: {e}")

    def _save_settings(self) -> None:
        """Save plugin settings to file"""
        settings = {}
        for name, state in self._plugins.items():
            settings[name] = {"enabled": state.enabled, "settings": state.plugin.get_all_settings()}

        try:
            with open(self._settings_file, "w") as f:
                json.dump(settings, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save plugin settings: {e}")

    def _get_saved_settings(self, plugin_name: str) -> Dict[str, Any]:
        """Get saved settings for a plugin"""
        if plugin_name in self._saved_settings:
            return self._saved_settings[plugin_name].get("settings", {})  # type: ignore[no-any-return]
        return {}

    def _restore_enabled_state(self) -> None:
        """Restore enabled state for plugins"""
        for name, saved in self._saved_settings.items():
            if saved.get("enabled", False) and name in self._plugins:
                self.enable_plugin(name)

    _MAX_SETTINGS_SIZE: int = 10_000  # Max serialized settings size in bytes

    def save_plugin_settings(self, plugin_name: str, settings: Dict[str, Any]) -> bool:
        """Save settings for a specific plugin (with size validation)"""
        if plugin_name not in self._plugins:
            return False

        # Validate settings size to prevent abuse
        try:
            serialized = json.dumps(settings)
            if len(serialized) > self._MAX_SETTINGS_SIZE:
                logger.warning(f"Plugin settings for '{plugin_name}' exceed max size")
                return False
        except (TypeError, ValueError):
            logger.warning(f"Plugin settings for '{plugin_name}' are not serializable")
            return False

        self._plugins[plugin_name].plugin.load_settings(settings)
        self._plugins[plugin_name].settings = settings
        self._save_settings()
        return True
