"""
NEXUS Music Manager - Service Layer
Encapsulates business logic and provides clean API for GUI components

Services follow singleton pattern and emit PySide6 signals for UI updates.
"""

from .cloud_sync_service import CloudSyncService, GoogleDriveProvider, LocalFolderProvider
from .download_service import DownloadService
from .library_service import LibraryService
from .player_service import PlayerService
from .remote_server import RemoteServer

__all__: list[str] = [
    "LibraryService",
    "DownloadService",
    "PlayerService",
    "CloudSyncService",
    "LocalFolderProvider",
    "GoogleDriveProvider",
    "RemoteServer",
]
