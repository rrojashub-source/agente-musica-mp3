"""
Plugin Base Classes and Interfaces
Defines the contract for all NEXUS plugins
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class PluginHook(Enum):
    """
    Available hook points for plugins to extend functionality.
    Plugins can register handlers for these events.
    """
    # Playback hooks
    ON_SONG_PLAY = auto()           # When a song starts playing
    ON_SONG_PAUSE = auto()          # When playback is paused
    ON_SONG_STOP = auto()           # When playback stops
    ON_SONG_END = auto()            # When a song finishes
    ON_QUEUE_CHANGE = auto()        # When queue is modified

    # Library hooks
    ON_SONG_IMPORT = auto()         # When a song is imported
    ON_SONG_DELETE = auto()         # When a song is deleted
    ON_METADATA_UPDATE = auto()     # When metadata is updated
    ON_LIBRARY_SCAN = auto()        # When library scan starts/ends

    # Download hooks
    ON_DOWNLOAD_START = auto()      # When download starts
    ON_DOWNLOAD_COMPLETE = auto()   # When download finishes
    ON_DOWNLOAD_ERROR = auto()      # When download fails

    # UI hooks
    ON_APP_START = auto()           # When application starts
    ON_APP_CLOSE = auto()           # When application closes
    ON_TAB_CHANGE = auto()          # When user changes tab

    # Sync hooks
    ON_SYNC_START = auto()          # When sync starts
    ON_SYNC_COMPLETE = auto()       # When sync completes


@dataclass
class PluginMetadata:
    """
    Metadata describing a plugin.
    Every plugin must provide this information.
    """
    name: str                           # Unique plugin identifier
    display_name: str                   # Human-readable name
    version: str                        # Semantic version (e.g., "1.0.0")
    author: str                         # Plugin author
    description: str                    # Short description
    website: str = ""                   # Optional website/repo URL
    min_app_version: str = "0.9.0"      # Minimum NEXUS version required
    dependencies: List[str] = field(default_factory=list)  # Required plugins
    hooks: List[PluginHook] = field(default_factory=list)  # Hooks this plugin uses

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'website': self.website,
            'min_app_version': self.min_app_version,
            'dependencies': self.dependencies,
            'hooks': [h.name for h in self.hooks]
        }


class Plugin(ABC):
    """
    Abstract base class for all NEXUS plugins.

    To create a plugin:
    1. Subclass Plugin
    2. Implement metadata property
    3. Implement on_enable() and on_disable()
    4. Register hook handlers in on_enable()

    Example:
        class MyPlugin(Plugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="my_plugin",
                    display_name="My Plugin",
                    version="1.0.0",
                    author="Your Name",
                    description="Does something cool"
                )

            def on_enable(self) -> bool:
                self.register_hook(PluginHook.ON_SONG_PLAY, self.on_song_play)
                return True

            def on_disable(self) -> bool:
                return True

            def on_song_play(self, song_data: dict):
                print(f"Playing: {song_data['title']}")
    """

    def __init__(self):
        self._enabled = False
        self._hook_handlers: Dict[PluginHook, List[Callable]] = {}
        self._settings: Dict[str, Any] = {}

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata. Must be implemented by subclass."""
        pass

    @property
    def enabled(self) -> bool:
        """Check if plugin is currently enabled"""
        return self._enabled

    @property
    def name(self) -> str:
        """Get plugin name from metadata"""
        return self.metadata.name

    @property
    def version(self) -> str:
        """Get plugin version from metadata"""
        return self.metadata.version

    @abstractmethod
    def on_enable(self) -> bool:
        """
        Called when plugin is enabled.
        Register hooks and initialize resources here.
        Return True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def on_disable(self) -> bool:
        """
        Called when plugin is disabled.
        Clean up resources here.
        Return True if successful, False otherwise.
        """
        pass

    def register_hook(self, hook: PluginHook, handler: Callable) -> None:
        """
        Register a handler for a specific hook.

        Args:
            hook: The hook point to register for
            handler: Callable to be invoked when hook is triggered
        """
        if hook not in self._hook_handlers:
            self._hook_handlers[hook] = []
        self._hook_handlers[hook].append(handler)
        logger.debug(f"Plugin {self.name}: registered handler for {hook.name}")

    def unregister_hook(self, hook: PluginHook, handler: Callable) -> None:
        """
        Unregister a handler from a hook.

        Args:
            hook: The hook point to unregister from
            handler: The handler to remove
        """
        if hook in self._hook_handlers and handler in self._hook_handlers[hook]:
            self._hook_handlers[hook].remove(handler)
            logger.debug(f"Plugin {self.name}: unregistered handler for {hook.name}")

    def get_handlers(self, hook: PluginHook) -> List[Callable]:
        """Get all handlers registered for a hook"""
        return self._hook_handlers.get(hook, [])

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a plugin setting value"""
        return self._settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a plugin setting value"""
        self._settings[key] = value

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all plugin settings"""
        return self._settings.copy()

    def load_settings(self, settings: Dict[str, Any]) -> None:
        """Load settings from dictionary"""
        self._settings = settings.copy()

    def get_settings_ui(self) -> Optional[Any]:
        """
        Return a QWidget for plugin settings UI.
        Override this to provide custom settings interface.
        Returns None if plugin has no settings UI.
        """
        return None

    def _set_enabled(self, enabled: bool) -> None:
        """Internal method to set enabled state"""
        self._enabled = enabled
