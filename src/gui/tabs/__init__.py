"""
GUI Tabs Module
Contains all tab widgets for NEXUS Music Manager
"""

from .cloud_sync_tab import CloudSyncTab
from .plugins_tab import PluginsTab
from .remote_tab import RemoteTab

__all__ = [
    'CloudSyncTab',
    'PluginsTab',
    'RemoteTab'
]
