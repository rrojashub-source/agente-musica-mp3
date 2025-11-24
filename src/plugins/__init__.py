"""
NEXUS Music Manager - Plugin System
Provides extensibility through plugins

Usage:
    from plugins import PluginManager, Plugin, PluginHook

    # Load plugins
    manager = PluginManager.get_instance()
    manager.load_plugins()

    # Execute hook
    manager.execute_hook(PluginHook.ON_SONG_PLAY, song_data)
"""

from .plugin_base import Plugin, PluginMetadata, PluginHook
from .plugin_manager import PluginManager

__all__ = [
    'Plugin',
    'PluginMetadata',
    'PluginHook',
    'PluginManager'
]
