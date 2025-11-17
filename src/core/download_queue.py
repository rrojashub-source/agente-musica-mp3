"""
Download Queue Manager - Phase 4.2
Manages concurrent downloads with pause/resume/cancel support

Features:
- Concurrent downloads (up to 50 simultaneous)
- Queue persistence (survives app restart)
- Progress tracking per download
- Pause/resume/cancel individual downloads
- Automatic retry on failure
"""
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from workers.download_worker import DownloadWorker

# Setup logger
logger = logging.getLogger(__name__)


class DownloadQueue(QObject):
    """
    Manages queue of downloads with concurrent processing

    Usage:
        queue = DownloadQueue(max_concurrent=50)
        queue.on_complete = lambda item_id, meta: print(f"Done: {meta['title']}")

        item_id = queue.add(video_url, metadata)
        queue.start()

        queue.pause(item_id)
        queue.resume(item_id)
        queue.cancel(item_id)
    """

    # Signals
    item_completed = pyqtSignal(str, dict)  # item_id, metadata
    item_failed = pyqtSignal(str, str)      # item_id, error
    queue_completed = pyqtSignal()          # All items done

    def __init__(self, max_concurrent=50, max_retries=3, db_manager=None):
        """
        Initialize download queue

        Args:
            max_concurrent (int): Maximum simultaneous downloads (default: 50)
            max_retries (int): Maximum retry attempts for failed downloads (default: 3)
            db_manager (DatabaseManager): Database manager for auto-import (optional)
        """
        super().__init__()

        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.db_manager = db_manager
        self._items = {}  # item_id -> item_dict
        self._workers = {}  # item_id -> DownloadWorker
        self._running = False

        # Callback for completion (optional)
        self.on_complete = None

        logger.info(f"DownloadQueue initialized (max_concurrent={max_concurrent}, max_retries={max_retries}, db_integration={'enabled' if db_manager else 'disabled'})")

    def add(self, video_url: str, metadata: dict) -> str:
        """
        Add download to queue

        Args:
            video_url (str): YouTube video URL
            metadata (dict): Song metadata (title, artist, etc.)

        Returns:
            str: Unique item ID
        """
        # Generate unique ID
        item_id = str(uuid.uuid4())

        # Create item
        item = {
            'id': item_id,
            'video_url': video_url,
            'metadata': metadata,
            'status': 'pending',  # pending, downloading, paused, completed, canceled, failed
            'progress': 0,
            'error': None,
            'retry_count': 0
        }

        self._items[item_id] = item
        logger.info(f"Added to queue: {metadata.get('title', video_url)} (id={item_id})")

        # Auto-start if already running
        if self._running:
            self._process_next()

        return item_id

    def get_all(self) -> List[dict]:
        """
        Get all items in queue

        Returns:
            list: List of item dicts
        """
        return list(self._items.values())

    def get_all_items(self) -> Dict[str, dict]:
        """
        Get all items in queue as dictionary

        Returns:
            dict: Dictionary of item_id -> item_dict
        """
        return self._items.copy()

    def get_item(self, item_id: str) -> Optional[dict]:
        """
        Get specific item by ID

        Args:
            item_id (str): Item ID

        Returns:
            dict: Item dict or None if not found
        """
        return self._items.get(item_id)

    def start(self):
        """
        Start processing queue
        """
        self._running = True
        logger.info("Queue started")

        # Start processing pending items
        self._process_next()

    def stop(self):
        """
        Stop processing queue (pauses all active downloads)
        """
        self._running = False
        logger.info("Queue stopped")

    def is_running(self) -> bool:
        """
        Check if queue is processing

        Returns:
            bool: True if running
        """
        return self._running

    def get_active_downloads(self) -> List[dict]:
        """
        Get currently downloading items

        Returns:
            list: Items with status='downloading'
        """
        return [item for item in self._items.values() if item['status'] == 'downloading']

    def pause(self, item_id: str) -> bool:
        """
        Pause download

        Args:
            item_id (str): Item ID

        Returns:
            bool: True if paused successfully
        """
        item = self._items.get(item_id)
        if not item:
            return False

        # Terminate worker if running
        if item_id in self._workers:
            worker = self._workers[item_id]
            worker.terminate()
            worker.wait()
            del self._workers[item_id]

        # Update status
        item['status'] = 'paused'
        logger.info(f"Paused: {item_id}")

        return True

    def resume(self, item_id: str) -> bool:
        """
        Resume paused download

        Args:
            item_id (str): Item ID

        Returns:
            bool: True if resumed successfully
        """
        item = self._items.get(item_id)
        if not item or item['status'] != 'paused':
            return False

        # Reset to pending
        item['status'] = 'pending'
        logger.info(f"Resumed: {item_id}")

        # Process if queue running
        if self._running:
            self._process_next()

        return True

    def cancel(self, item_id: str) -> bool:
        """
        Cancel download

        Args:
            item_id (str): Item ID

        Returns:
            bool: True if canceled successfully
        """
        item = self._items.get(item_id)
        if not item:
            return False

        # Terminate worker if running
        if item_id in self._workers:
            worker = self._workers[item_id]
            worker.terminate()
            worker.wait()
            del self._workers[item_id]

        # Update status
        item['status'] = 'canceled'
        logger.info(f"Canceled: {item_id}")

        # Process next
        if self._running:
            self._process_next()

        return True

    def clear_completed(self):
        """
        Remove all completed items from queue

        Returns:
            int: Number of items removed
        """
        completed_ids = [
            item_id for item_id, item in self._items.items()
            if item['status'] == 'completed'
        ]

        for item_id in completed_ids:
            del self._items[item_id]

        count = len(completed_ids)
        logger.info(f"Cleared {count} completed items")
        return count

    def update_progress(self, item_id: str, percentage: int):
        """
        Update download progress

        Args:
            item_id (str): Item ID
            percentage (int): Progress 0-100
        """
        item = self._items.get(item_id)
        if item:
            item['progress'] = percentage

    def mark_completed(self, item_id: str, metadata: dict):
        """
        Mark download as completed

        Args:
            item_id (str): Item ID
            metadata (dict): Final metadata
        """
        item = self._items.get(item_id)
        if not item:
            return

        # Update status
        item['status'] = 'completed'
        item['progress'] = 100
        item['metadata'].update(metadata)

        logger.info(f"Completed: {item['metadata'].get('title', item_id)}")

        # Auto-import to database if available
        if self.db_manager and 'output_path' in metadata:
            self._import_to_database(metadata['output_path'], metadata)

        # Fire callback
        if self.on_complete:
            self.on_complete(item_id, metadata)

        # Emit signal
        self.item_completed.emit(item_id, metadata)

        # Cleanup worker
        if item_id in self._workers:
            del self._workers[item_id]

        # Process next
        if self._running:
            self._process_next()

    def _import_to_database(self, file_path: str, metadata: dict):
        """
        Import downloaded song to database

        Args:
            file_path (str): Path to downloaded MP3 file (relative or absolute)
            metadata (dict): Song metadata
        """
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3
            from pathlib import Path

            # Convert to Path object and resolve to absolute path
            file_path_obj = Path(file_path)

            # If relative path, resolve from current working directory
            if not file_path_obj.is_absolute():
                file_path_obj = Path.cwd() / file_path_obj

            # Verify file exists
            if not file_path_obj.exists():
                logger.error(f"Downloaded file not found: {file_path_obj}")
                logger.debug(f"Current working directory: {Path.cwd()}")
                logger.debug(f"Attempted paths: {file_path} → {file_path_obj}")
                return

            # Read MP3 metadata
            try:
                audio = MP3(str(file_path_obj))
                id3 = audio.tags if audio.tags else ID3()
            except Exception as e:
                logger.warning(f"Could not read ID3 tags: {e}")
                audio = None
                id3 = None

            # Extract metadata
            title = metadata.get('title', file_path_obj.stem)
            artist = metadata.get('artist', 'Unknown Artist')
            album = metadata.get('album', '')
            year = metadata.get('year', '')
            genre = metadata.get('genre', '')
            duration = int(audio.info.length) if audio else 0

            # Get file info
            file_size = file_path_obj.stat().st_size
            bitrate = int(audio.info.bitrate / 1000) if audio else 0  # kbps

            # Insert into database
            self.db_manager.add_song(
                title=title,
                artist=artist,
                album=album,
                year=year,
                genre=genre,
                duration=duration,
                file_path=str(file_path_obj.absolute()),
                file_size=file_size,
                bitrate=bitrate
            )

            logger.info(f"Imported to database: {artist} - {title}")

        except Exception as e:
            logger.error(f"Failed to import to database: {e}")

    def _mark_failed(self, item_id: str, error: str):
        """
        Mark download as failed (with auto-retry if attempts remaining)

        Args:
            item_id (str): Item ID
            error (str): Error message
        """
        item = self._items.get(item_id)
        if not item:
            return

        # Increment retry count
        item['retry_count'] += 1
        item['error'] = error

        # Check if should retry
        if item['retry_count'] < self.max_retries:
            # Retry download
            item['status'] = 'pending'
            item['progress'] = 0
            logger.warning(f"Retry {item['retry_count']}/{self.max_retries}: {item_id} - {error}")

            # Cleanup worker
            if item_id in self._workers:
                del self._workers[item_id]

            # Process next (will retry this item)
            if self._running:
                self._process_next()

        else:
            # Max retries exhausted
            item['status'] = 'failed'
            logger.error(f"Failed (max retries): {item_id} - {error}")

            # Emit signal
            self.item_failed.emit(item_id, error)

            # Cleanup worker
            if item_id in self._workers:
                del self._workers[item_id]

            # Process next
            if self._running:
                self._process_next()

    def _process_next(self):
        """
        Process next pending item if under max_concurrent limit
        """
        # Check if we can start more downloads
        active_count = len(self.get_active_downloads())
        if active_count >= self.max_concurrent:
            logger.debug(f"Max concurrent reached ({active_count}/{self.max_concurrent})")
            return

        # Find next pending item
        pending = [item for item in self._items.values() if item['status'] == 'pending']
        if not pending:
            # Check if queue completed
            if active_count == 0 and all(item['status'] in ['completed', 'canceled', 'failed'] for item in self._items.values()):
                logger.info("Queue completed")
                self.queue_completed.emit()
            return

        # Start next download
        item = pending[0]
        self._start_download(item)

    def _start_download(self, item: dict):
        """
        Start downloading item

        Args:
            item (dict): Item to download
        """
        item_id = item['id']

        # Create output path
        # For now, use a simple path (can be customized later)
        output_path = Path(f"downloads/{item['metadata'].get('title', item_id)}.mp3")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create worker
        worker = DownloadWorker(item['video_url'], str(output_path))

        # Connect signals
        worker.progress.connect(lambda p: self.update_progress(item_id, p))
        worker.finished.connect(lambda meta: self.mark_completed(item_id, meta))
        worker.error.connect(lambda err: self._mark_failed(item_id, err))

        # Store worker
        self._workers[item_id] = worker

        # Update status
        item['status'] = 'downloading'

        # Start download
        worker.start()
        logger.info(f"Started download: {item['metadata'].get('title', item_id)}")

    def save(self, filepath: str):
        """
        Save queue to JSON file (persistence)

        Args:
            filepath (str): Path to JSON file
        """
        # Only save items that are not actively downloading
        saveable_items = [
            item for item in self._items.values()
            if item['status'] != 'downloading'
        ]

        data = {
            'max_concurrent': self.max_concurrent,
            'items': saveable_items
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Queue saved to {filepath} ({len(saveable_items)} items)")

    def load(self, filepath: str):
        """
        Load queue from JSON file

        Args:
            filepath (str): Path to JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Restore items
        for item in data.get('items', []):
            self._items[item['id']] = item

        logger.info(f"Queue loaded from {filepath} ({len(self._items)} items)")
