"""
NEXUS Music Manager - Download Service
Encapsulates download operations with business logic and PySide6 signals

Features:
- Thread-safe singleton pattern
- PySide6 signals for UI updates
- Download queue management
- Auto-import to library after download
- Rate limiting integration
"""

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    """Download status enum"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class DownloadItem:
    """Domain model for a download item"""

    id: str
    url: str
    title: str
    artist: Optional[str] = None
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DownloadItem":
        """Create from dictionary"""
        status_str = data.get("status", "pending")
        status = DownloadStatus(status_str) if isinstance(status_str, str) else status_str

        return cls(
            id=data.get("id", ""),
            url=data.get("url", data.get("video_url", "")),
            title=data.get("title", "Unknown"),
            artist=data.get("artist", data.get("metadata", {}).get("artist")),
            status=status,
            progress=data.get("progress", 0.0),
            file_path=data.get("file_path"),
            error_message=data.get("error"),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "artist": self.artist,
            "status": self.status.value,
            "progress": self.progress,
            "file_path": self.file_path,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class DownloadService(QObject):
    """
    Download Service - Manages music downloads

    Signals:
        download_added: Emitted when a download is added (item_id)
        download_started: Emitted when download starts (item_id)
        download_progress: Emitted on progress (item_id, progress_percent)
        download_completed: Emitted when download finishes (item_id, file_path)
        download_failed: Emitted on failure (item_id, error_message)
        download_canceled: Emitted when canceled (item_id)
        queue_changed: Emitted when queue changes
        auto_import_completed: Emitted when auto-import to library finishes (song_id)
        error_occurred: Emitted on errors (error_message)
    """

    # Signals
    download_added = Signal(str)  # item_id
    download_started = Signal(str)  # item_id
    download_progress = Signal(str, float)  # item_id, progress
    download_completed = Signal(str, str)  # item_id, file_path
    download_failed = Signal(str, str)  # item_id, error_message
    download_canceled = Signal(str)  # item_id
    queue_changed = Signal()
    auto_import_completed = Signal(int)  # song_id
    error_occurred = Signal(str)  # error_message

    # Singleton (class-level for QObject compatibility)
    _instance: Optional["DownloadService"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, download_dir: Optional[str] = None, auto_import: bool = True) -> None:
        """
        Initialize DownloadService

        Args:
            download_dir: Directory for downloads
            auto_import: Auto-import to library after download
        """
        super().__init__()

        self._download_dir: str = download_dir or str(Path.home() / "Music" / "Downloads")
        self._auto_import: bool = auto_import
        self._queue: Any = None

        # Ensure download directory exists
        Path(self._download_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"DownloadService initialized with dir: {self._download_dir}")

    @classmethod
    def get_instance(cls, download_dir: Optional[str] = None) -> "DownloadService":
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(download_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)"""
        with cls._lock:
            cls._instance = None

    @property
    def queue(self) -> Any:
        """Lazy-load download queue"""
        if self._queue is None:
            from core.download_queue import DownloadQueue

            self._queue = DownloadQueue(max_concurrent=2)
            self._connect_queue_signals()
        return self._queue

    def _connect_queue_signals(self) -> None:
        """Connect internal queue signals to service signals"""
        if self._queue:
            # Connect to queue's signals if available
            if hasattr(self._queue, "progress_updated"):
                self._queue.progress_updated.connect(self._on_progress)
            if hasattr(self._queue, "download_completed"):
                self._queue.download_completed.connect(self._on_completed)
            if hasattr(self._queue, "download_failed"):
                self._queue.download_failed.connect(self._on_failed)

    def _on_progress(self, item_id: str, progress: float) -> None:
        """Handle progress update from queue"""
        self.download_progress.emit(item_id, progress)

    def _on_completed(self, item_id: str, file_path: str) -> None:
        """Handle download completed"""
        self.download_completed.emit(item_id, file_path)
        self.queue_changed.emit()

        # Auto-import to library if enabled
        if self._auto_import:
            self._import_to_library(item_id, file_path)

    def _on_failed(self, item_id: str, error: str) -> None:
        """Handle download failed"""
        self.download_failed.emit(item_id, error)
        self.queue_changed.emit()

    def _import_to_library(self, item_id: str, file_path: str) -> None:
        """Import downloaded file to library"""
        try:
            from core.metadata_fetcher import extract_metadata
            from services.library_service import LibraryService

            library = LibraryService.get_instance()

            # Extract metadata from file
            metadata = extract_metadata(file_path)
            if metadata:
                song_id = library.add_song(metadata)
                if song_id:
                    self.auto_import_completed.emit(song_id)
                    logger.info(f"Auto-imported to library: {file_path} (ID: {song_id})")
        except (ImportError, OSError, ValueError) as e:
            logger.error(f"Failed to auto-import {file_path}: {e}")

    # ==========================================
    # Queue Operations
    # ==========================================

    def add_download(self, url: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Add a download to the queue

        Args:
            url: Video/audio URL
            metadata: Optional metadata (title, artist, etc.)

        Returns:
            Item ID if successful
        """
        try:
            item_id = self.queue.add(video_url=url, metadata=metadata or {})
            if item_id:
                self.download_added.emit(item_id)
                self.queue_changed.emit()
                logger.info(f"Added download: {(metadata or {}).get('title', url)}")
            return item_id  # type: ignore[no-any-return]
        except (ValueError, RuntimeError, AttributeError) as e:
            logger.error(f"Error adding download: {e}")
            self.error_occurred.emit(str(e))
            return None

    def add_batch(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple downloads

        Args:
            items: List of {url, metadata} dictionaries

        Returns:
            List of item IDs
        """
        item_ids = []
        for item in items:
            item_id = self.add_download(
                url=item.get("url", item.get("video_url", "")), metadata=item.get("metadata", item)
            )
            if item_id:
                item_ids.append(item_id)
        return item_ids

    def pause(self, item_id: str) -> bool:
        """Pause a download"""
        try:
            self.queue.pause(item_id)
            self.queue_changed.emit()
            return True
        except (KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"Error pausing {item_id}: {e}")
            return False

    def resume(self, item_id: str) -> bool:
        """Resume a paused download"""
        try:
            self.queue.resume(item_id)
            self.queue_changed.emit()
            return True
        except (KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"Error resuming {item_id}: {e}")
            return False

    def cancel(self, item_id: str) -> bool:
        """Cancel a download"""
        try:
            self.queue.cancel(item_id)
            self.download_canceled.emit(item_id)
            self.queue_changed.emit()
            return True
        except (KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"Error canceling {item_id}: {e}")
            return False

    def retry(self, item_id: str) -> bool:
        """Retry a failed download"""
        try:
            self.queue.retry(item_id)
            self.queue_changed.emit()
            return True
        except (KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"Error retrying {item_id}: {e}")
            return False

    def clear_completed(self) -> int:
        """Clear completed downloads from queue.

        Returns:
            Number of items cleared.
        """
        try:
            count: int = self.queue.clear_completed()
            self.queue_changed.emit()
            return count
        except (KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"Error clearing completed: {e}")
            return 0

    def clear_all(self) -> int:
        """Clear all downloads from queue."""
        try:
            count: int = self.queue.clear_all()
            self.queue_changed.emit()
            return count
        except (KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"Error clearing all: {e}")
            return 0

    # ==========================================
    # Query Operations
    # ==========================================

    def get_item(self, item_id: str) -> Optional[DownloadItem]:
        """Get download item by ID"""
        try:
            items = self.queue.get_all_items()
            if item_id in items:
                return DownloadItem.from_dict(items[item_id])
            return None
        except (KeyError, AttributeError, ValueError) as e:
            logger.error(f"Error getting item {item_id}: {e}")
            return None

    def get_all_items(self) -> List[DownloadItem]:
        """Get all download items"""
        try:
            items = self.queue.get_all_items()
            return [DownloadItem.from_dict(item) for item in items.values()]
        except (AttributeError, ValueError) as e:
            logger.error(f"Error getting all items: {e}")
            return []

    def get_pending_count(self) -> int:
        """Get number of pending downloads"""
        try:
            items = self.queue.get_all_items()
            return sum(1 for i in items.values() if i.get("status") == "pending")
        except (AttributeError, KeyError, TypeError) as e:
            logger.debug(f"Error getting pending count: {e}")
            return 0

    def get_active_count(self) -> int:
        """Get number of active (downloading) downloads"""
        try:
            items = self.queue.get_all_items()
            return sum(1 for i in items.values() if i.get("status") == "downloading")
        except (AttributeError, KeyError, TypeError) as e:
            logger.debug(f"Error getting active count: {e}")
            return 0

    def get_completed_count(self) -> int:
        """Get number of completed downloads"""
        try:
            items = self.queue.get_all_items()
            return sum(1 for i in items.values() if i.get("status") == "completed")
        except (AttributeError, KeyError, TypeError) as e:
            logger.debug(f"Error getting completed count: {e}")
            return 0

    # ==========================================
    # Settings
    # ==========================================

    @property
    def download_dir(self) -> str:
        """Get download directory"""
        return self._download_dir

    @download_dir.setter
    def download_dir(self, path: str) -> None:
        """Set download directory"""
        self._download_dir = path
        Path(path).mkdir(parents=True, exist_ok=True)

    @property
    def auto_import_enabled(self) -> bool:
        """Check if auto-import is enabled"""
        return self._auto_import

    @auto_import_enabled.setter
    def auto_import_enabled(self, value: bool) -> None:
        """Enable/disable auto-import"""
        self._auto_import = value

    @property
    def max_concurrent(self) -> int:
        """Get max concurrent downloads"""
        return getattr(self.queue, "max_concurrent", 2)

    @max_concurrent.setter
    def max_concurrent(self, value: int) -> None:
        """Set max concurrent downloads"""
        if hasattr(self.queue, "max_concurrent"):
            self.queue.max_concurrent = value

    # ==========================================
    # Cleanup
    # ==========================================

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self._queue:
            if hasattr(self._queue, "stop"):
                self._queue.stop()
            self._queue = None
        logger.info("DownloadService cleaned up")
