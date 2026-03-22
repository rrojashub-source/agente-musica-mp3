"""
NEXUS Music Manager - Library Service
Encapsulates library operations with business logic and PySide6 signals

Features:
- Thread-safe singleton pattern
- PySide6 signals for UI updates
- Cached statistics
- Search with result transformation
- Import/export operations
"""

import logging
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


@dataclass
class Song:
    """Domain model for a song"""

    id: int
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration: Optional[float] = None
    file_path: Optional[str] = None
    bitrate: Optional[int] = None
    play_count: int = 0
    rating: int = 0
    date_added: Optional[datetime] = None
    last_played: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Song":
        """Create Song from dictionary"""
        return cls(
            id=data.get("id", 0),
            title=data.get("title", "Unknown"),
            artist=data.get("artist"),
            album=data.get("album"),
            year=data.get("year"),
            genre=data.get("genre"),
            duration=data.get("duration"),
            file_path=data.get("file_path"),
            bitrate=data.get("bitrate"),
            play_count=data.get("play_count", 0),
            rating=data.get("rating", 0),
            date_added=data.get("date_added"),
            last_played=data.get("last_played"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "year": self.year,
            "genre": self.genre,
            "duration": self.duration,
            "file_path": self.file_path,
            "bitrate": self.bitrate,
            "play_count": self.play_count,
            "rating": self.rating,
            "date_added": self.date_added,
            "last_played": self.last_played,
        }


@dataclass
class LibraryStats:
    """Statistics for the library"""

    total_songs: int = 0
    total_artists: int = 0
    total_albums: int = 0
    total_genres: int = 0
    total_duration_hours: float = 0.0
    total_size_mb: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LibraryStats":
        """Create from dictionary"""
        return cls(
            total_songs=data.get("total_songs", 0),
            total_artists=data.get("total_artists", 0),
            total_albums=data.get("total_albums", 0),
            total_genres=data.get("total_genres", 0),
            total_duration_hours=data.get("total_duration_hours", 0.0),
            total_size_mb=data.get("total_size_mb", 0.0),
        )


class LibraryService(QObject):
    """
    Library Service - Manages music library operations

    Signals:
        song_added: Emitted when a song is added (song_id)
        song_updated: Emitted when a song is updated (song_id)
        song_deleted: Emitted when a song is deleted (song_id)
        library_changed: Emitted when library changes significantly
        import_progress: Emitted during import (current, total, message)
        import_completed: Emitted when import finishes (success_count, error_count)
        stats_updated: Emitted when statistics change
        error_occurred: Emitted on errors (error_message)
    """

    # Signals
    song_added = Signal(int)  # song_id
    song_updated = Signal(int)  # song_id
    song_deleted = Signal(int)  # song_id
    library_changed = Signal()
    import_progress = Signal(int, int, str)  # current, total, message
    import_completed = Signal(int, int)  # success_count, error_count
    stats_updated = Signal(object)  # LibraryStats
    error_occurred = Signal(str)  # error_message

    # Singleton (class-level, not instance-level for QObject compatibility)
    _instance: Optional["LibraryService"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize LibraryService

        Args:
            db_path: Path to SQLite database (optional if already initialized)
        """
        super().__init__()

        self._db_path: Optional[str] = db_path or "music_library.db"
        self._db_manager: Any = None
        self._stats_cache: Optional[LibraryStats] = None
        self._stats_cache_time: Optional[datetime] = None
        self._stats_cache_ttl: int = 60  # Cache TTL in seconds

        logger.info(f"LibraryService initialized with db: {db_path}")

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> "LibraryService":
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)"""
        with cls._lock:
            cls._instance = None

    @property
    def db(self) -> Any:
        """Lazy-load database manager"""
        if self._db_manager is None:
            from database.manager import DatabaseManager

            self._db_manager = DatabaseManager(self._db_path)
        return self._db_manager

    # ==========================================
    # CRUD Operations
    # ==========================================

    def get_song(self, song_id: int) -> Optional[Song]:
        """Get song by ID"""
        try:
            result = self.db.fetch_one("SELECT * FROM songs WHERE id = ?", (song_id,))
            return Song.from_dict(result) if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting song {song_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_song_by_path(self, file_path: str) -> Optional[Song]:
        """Get song by file path"""
        try:
            result = self.db.fetch_one("SELECT * FROM songs WHERE file_path = ?", (file_path,))
            return Song.from_dict(result) if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting song by path {file_path}: {e}")
            return None

    def add_song(self, song_data: Dict[str, Any]) -> Optional[int]:
        """
        Add song to library

        Args:
            song_data: Song data dictionary

        Returns:
            Song ID if successful, None otherwise
        """
        try:
            song_id = self.db.add_song(song_data)
            if song_id:
                self.song_added.emit(song_id)
                self._invalidate_stats_cache()
                logger.info(f"Added song: {song_data.get('title')} (ID: {song_id})")
            return song_id  # type: ignore[no-any-return]
        except sqlite3.Error as e:
            logger.error(f"Error adding song: {e}")
            self.error_occurred.emit(f"Failed to add song: {e}")
            return None

    def update_song(self, song_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update song metadata

        Delegates field validation, modified_date update, and SQL execution
        to DatabaseManager.update_song(). Adds signal emission and cache
        invalidation on top.

        Args:
            song_id: Song ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        try:
            # Filter out 'id' before delegating
            filtered = {k: v for k, v in updates.items() if k != "id"}
            if not filtered:
                return False

            result: bool = self.db.update_song(song_id, filtered)
            if result:
                self.song_updated.emit(song_id)
                self._invalidate_stats_cache()
            return result
        except (sqlite3.Error, AttributeError) as e:
            logger.error(f"Error updating song {song_id}: {e}")
            self.error_occurred.emit(f"Failed to update song: {e}")
            return False

    def delete_song(self, song_id: int) -> bool:
        """Delete song from library"""
        try:
            self.db.execute_query("DELETE FROM songs WHERE id = ?", (song_id,))
            self.song_deleted.emit(song_id)
            self._invalidate_stats_cache()
            logger.info(f"Deleted song {song_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting song {song_id}: {e}")
            self.error_occurred.emit(f"Failed to delete song: {e}")
            return False

    def delete_songs(self, song_ids: List[int]) -> int:
        """
        Delete multiple songs

        Returns:
            Number of songs deleted
        """
        deleted = 0
        for song_id in song_ids:
            if self.delete_song(song_id):
                deleted += 1

        if deleted > 0:
            self.library_changed.emit()

        return deleted

    # ==========================================
    # Query Operations
    # ==========================================

    def get_all_songs(self, limit: int = 10000, offset: int = 0) -> List[Song]:
        """Get all songs with pagination"""
        try:
            results = self.db.fetch_all("SELECT * FROM songs ORDER BY title LIMIT ? OFFSET ?", (limit, offset))
            return [Song.from_dict(r) for r in results]
        except sqlite3.Error as e:
            logger.error(f"Error getting all songs: {e}")
            return []

    def search(self, query: str, limit: int = 100) -> List[Song]:
        """
        Search songs by title, artist, album

        Uses FTS5 if available, falls back to LIKE
        """
        try:
            results = self.db.search_songs(query, limit)
            return [Song.from_dict(r) for r in results]
        except sqlite3.Error as e:
            logger.error(f"Error searching songs: {e}")
            return []

    def get_by_artist(self, artist: str) -> List[Song]:
        """Get all songs by artist"""
        try:
            results = self.db.fetch_all("SELECT * FROM songs WHERE artist = ? ORDER BY album, title", (artist,))
            return [Song.from_dict(r) for r in results]
        except sqlite3.Error as e:
            logger.error(f"Error getting songs by artist: {e}")
            return []

    def get_by_album(self, album: str, artist: Optional[str] = None) -> List[Song]:
        """Get all songs from an album"""
        try:
            if artist:
                results = self.db.fetch_all(
                    "SELECT * FROM songs WHERE album = ? AND artist = ? ORDER BY track_number, title", (album, artist)
                )
            else:
                results = self.db.fetch_all(
                    "SELECT * FROM songs WHERE album = ? ORDER BY track_number, title", (album,)
                )
            return [Song.from_dict(r) for r in results]
        except sqlite3.Error as e:
            logger.error(f"Error getting songs by album: {e}")
            return []

    def get_by_genre(self, genre: str) -> List[Song]:
        """Get all songs of a genre"""
        try:
            escaped_genre = genre.replace("%", "\\%").replace("_", "\\_")
            results = self.db.fetch_all(
                "SELECT * FROM songs WHERE genre LIKE ? ESCAPE '\\' ORDER BY artist, album, title",
                (f"%{escaped_genre}%",),
            )
            return [Song.from_dict(r) for r in results]
        except sqlite3.Error as e:
            logger.error(f"Error getting songs by genre: {e}")
            return []

    def get_recently_added(self, days: int = 30, limit: int = 100) -> List[Song]:
        """Get recently added songs"""
        try:
            results = self.db.fetch_all(
                """SELECT * FROM songs
                   WHERE date_added >= datetime('now', ? || ' days')
                   ORDER BY date_added DESC
                   LIMIT ?""",
                (f"-{days}", limit),
            )
            return [Song.from_dict(r) for r in results]
        except sqlite3.Error as e:
            logger.error(f"Error getting recently added: {e}")
            return []

    def get_most_played(self, limit: int = 50) -> List[Song]:
        """Get most played songs"""
        try:
            results = self.db.fetch_all(
                "SELECT * FROM songs WHERE play_count > 0 ORDER BY play_count DESC LIMIT ?", (limit,)
            )
            return [Song.from_dict(r) for r in results]
        except sqlite3.Error as e:
            logger.error(f"Error getting most played: {e}")
            return []

    # ==========================================
    # Statistics
    # ==========================================

    def get_stats(self, force_refresh: bool = False) -> LibraryStats:
        """
        Get library statistics (cached)

        Args:
            force_refresh: Force cache invalidation
        """
        now = datetime.now()

        # Check cache validity
        if not force_refresh and self._stats_cache is not None and self._stats_cache_time is not None:
            age = (now - self._stats_cache_time).total_seconds()
            if age < self._stats_cache_ttl:
                return self._stats_cache

        # Fetch fresh stats
        try:
            result = self.db.fetch_one(
                """
                SELECT
                    COUNT(*) as total_songs,
                    COUNT(DISTINCT artist) as total_artists,
                    COUNT(DISTINCT album) as total_albums,
                    COUNT(DISTINCT genre) as total_genres,
                    COALESCE(SUM(duration) / 3600.0, 0) as total_duration_hours
                FROM songs
            """
            )

            if result:
                self._stats_cache = LibraryStats.from_dict(result)
                self._stats_cache_time = now
                self.stats_updated.emit(self._stats_cache)
                return self._stats_cache

            return LibraryStats()
        except sqlite3.Error as e:
            logger.error(f"Error getting stats: {e}")
            return LibraryStats()

    def _invalidate_stats_cache(self) -> None:
        """Invalidate statistics cache"""
        self._stats_cache = None
        self._stats_cache_time = None

    # ==========================================
    # Unique Values
    # ==========================================

    def get_all_artists(self) -> List[str]:
        """Get list of all unique artists"""
        try:
            results = self.db.fetch_all("SELECT DISTINCT artist FROM songs WHERE artist IS NOT NULL ORDER BY artist")
            return [r["artist"] for r in results if r["artist"]]
        except sqlite3.Error as e:
            logger.error(f"Error getting artists: {e}")
            return []

    def get_all_albums(self) -> List[str]:
        """Get list of all unique albums"""
        try:
            results = self.db.fetch_all("SELECT DISTINCT album FROM songs WHERE album IS NOT NULL ORDER BY album")
            return [r["album"] for r in results if r["album"]]
        except sqlite3.Error as e:
            logger.error(f"Error getting albums: {e}")
            return []

    def get_all_genres(self) -> List[str]:
        """Get list of all unique genres"""
        try:
            results = self.db.fetch_all("SELECT DISTINCT genre FROM songs WHERE genre IS NOT NULL ORDER BY genre")
            return [r["genre"] for r in results if r["genre"]]
        except sqlite3.Error as e:
            logger.error(f"Error getting genres: {e}")
            return []

    # ==========================================
    # Playback Tracking
    # ==========================================

    def increment_play_count(self, song_id: int) -> bool:
        """Increment play count and update last_played"""
        try:
            self.db.execute_query(
                """UPDATE songs
                   SET play_count = play_count + 1,
                       last_played = datetime('now')
                   WHERE id = ?""",
                (song_id,),
            )
            self.song_updated.emit(song_id)
            return True
        except sqlite3.Error as e:
            logger.error(f"Error incrementing play count: {e}")
            return False

    def set_rating(self, song_id: int, rating: int) -> bool:
        """Set song rating (0-5)"""
        if not 0 <= rating <= 5:
            return False
        return self.update_song(song_id, {"rating": rating})

    # ==========================================
    # Cleanup
    # ==========================================

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self._db_manager:
            self._db_manager.close()
            self._db_manager = None
        logger.info("LibraryService cleaned up")
