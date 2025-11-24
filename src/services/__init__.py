"""
NEXUS Music Manager - Service Layer
Encapsulates business logic and provides clean API for GUI components

Services follow singleton pattern and emit PyQt6 signals for UI updates.
"""

from .library_service import LibraryService
from .download_service import DownloadService
from .player_service import PlayerService

__all__ = ['LibraryService', 'DownloadService', 'PlayerService']
