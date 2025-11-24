"""
NEXUS Music Manager - Database Manager
High-performance SQLite manager with WAL mode and FTS5

Thread-safety: Uses threading.local() for per-thread connections
"""

import sqlite3
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    High-performance SQLite manager for music library

    Features:
    - Thread-safe: Each thread gets its own connection via threading.local()
    - WAL mode for concurrent reads (2-3x faster writes)
    - FTS5 for millisecond search
    - Auto-migration system
    - Foreign key enforcement

    Thread-safety:
    - Uses threading.local() for per-thread connections
    - Each thread automatically gets its own SQLite connection
    - Safe for use with PyQt6 QThread workers
    - All connections tracked and closed on cleanup
    """

    def __init__(self, db_path: str = "music_library.db"):
        """Initialize database manager with thread-safe connections"""
        self.db_path = Path(db_path)
        self._local = threading.local()  # Thread-local storage for connections
        self._connections = []  # Track all connections for cleanup
        self._lock = threading.Lock()  # Lock for connection tracking

        # Create database directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup initial connection (main thread) and run migrations
        self._setup_database()

    @property
    def conn(self) -> sqlite3.Connection:
        """
        Get thread-local database connection.

        Each thread gets its own connection for thread-safety.
        Connections are created on first access per thread.
        """
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = self._create_connection()
            # Track connection for cleanup
            with self._lock:
                self._connections.append(self._local.conn)
            logger.debug(f"Created new connection for thread {threading.current_thread().name}")
        return self._local.conn

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new optimized SQLite connection"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,  # 30 second timeout
            check_same_thread=True  # Enforce thread safety
        )
        conn.row_factory = sqlite3.Row

        # Apply performance optimizations to this connection
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = -64000")
        cursor.execute("PRAGMA mmap_size = 30000000000")
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()

        return conn

    def _setup_database(self):
        """Setup database with performance optimizations"""
        # Use conn property to create connection for main thread
        _ = self.conn

        # Run migrations (only needed once)
        self._run_migrations()

        logger.info(f"Database initialized (thread-safe): {self.db_path}")

    def _run_migrations(self):
        """Run SQL migrations from migrations/ folder"""
        migrations_dir = Path(__file__).parent / "migrations"

        if not migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {migrations_dir}")
            return

        # Get all .sql files sorted by name
        migration_files = sorted(migrations_dir.glob("*.sql"))

        if not migration_files:
            logger.info("No migrations found")
            return

        cursor = self.conn.cursor()

        # Create migrations tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Run each migration
        for migration_file in migration_files:
            # Check if already applied
            cursor.execute(
                "SELECT filename FROM schema_migrations WHERE filename = ?",
                (migration_file.name,)
            )
            if cursor.fetchone():
                logger.debug(f"Migration already applied: {migration_file.name}")
                continue

            # Read and execute migration
            try:
                sql = migration_file.read_text(encoding='utf-8')
                cursor.executescript(sql)

                # Record migration
                cursor.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (?)",
                    (migration_file.name,)
                )
                self.conn.commit()

                logger.info(f"Applied migration: {migration_file.name}")
            except Exception as e:
                self.conn.rollback()
                logger.error(f"Failed to apply migration {migration_file.name}: {e}")
                raise

    # Query methods
    def execute_query(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        Execute INSERT/UPDATE/DELETE query

        Returns:
            Last inserted row ID for INSERT, None for UPDATE/DELETE
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.lastrowid if query.strip().upper().startswith("INSERT") else None

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Fetch single row

        Returns:
            Dict of column: value or None
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Fetch all rows

        Returns:
            List of dicts
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_song_count(self) -> int:
        """Get total number of songs in library"""
        result = self.fetch_one("SELECT COUNT(*) as count FROM songs")
        return result['count'] if result else 0

    def search_songs(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search songs using FTS5 (if available) or basic LIKE

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching songs
        """
        # Try FTS5 first
        try:
            sql = """
                SELECT songs.* FROM songs
                JOIN songs_fts ON songs.id = songs_fts.rowid
                WHERE songs_fts MATCH ?
                LIMIT ?
            """
            return self.fetch_all(sql, (query, limit))
        except sqlite3.OperationalError:
            # Fallback to LIKE search
            logger.warning("FTS5 not available, using LIKE search")
            sql = """
                SELECT * FROM songs
                WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?
                LIMIT ?
            """
            pattern = f"%{query}%"
            return self.fetch_all(sql, (pattern, pattern, pattern, limit))

    # ==========================================
    # CRUD OPERATIONS
    # ==========================================

    def add_song(self, song_data: Dict[str, Any]) -> Optional[int]:
        """
        Add new song to library

        Args:
            song_data: Dictionary with song fields
                Required: title, file_path
                Optional: artist, album, year, genre, duration, bitrate, etc.

        Returns:
            Song ID if successful, None if duplicate file_path

        Note: file_path should already be normalized before calling this method
              (done by extract_metadata in import worker)
        """
        # Extract fields with defaults
        title = song_data.get('title', 'Unknown')
        artist = song_data.get('artist')
        album = song_data.get('album')
        year = song_data.get('year')
        genre = song_data.get('genre')
        duration = song_data.get('duration')
        bitrate = song_data.get('bitrate')
        sample_rate = song_data.get('sample_rate')
        file_path = song_data.get('file_path')
        file_size = song_data.get('file_size')

        # Validate required fields
        if not file_path:
            logger.error("Cannot add song without file_path")
            return None

        # Check for duplicate file_path (song_exists() will normalize internally)
        if self.song_exists(file_path):
            logger.warning(f"Song already exists: {file_path}")
            return None

        try:
            sql = """
                INSERT INTO songs (
                    title, artist, album, year, genre,
                    duration, bitrate, sample_rate,
                    file_path, file_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                title, artist, album, year, genre,
                duration, bitrate, sample_rate,
                file_path, file_size
            )

            song_id = self.execute_query(sql, params)
            logger.info(f"Added song: {title} (ID: {song_id})")
            return song_id

        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to add song (duplicate?): {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to add song: {e}")
            return None

    def get_all_songs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all songs from library

        Args:
            limit: Maximum number of songs to return (None = all)

        Returns:
            List of song dictionaries
        """
        if limit:
            sql = "SELECT * FROM songs ORDER BY added_date DESC LIMIT ?"
            return self.fetch_all(sql, (limit,))
        else:
            sql = "SELECT * FROM songs ORDER BY added_date DESC"
            return self.fetch_all(sql)

    def get_song_by_id(self, song_id: int) -> Optional[Dict[str, Any]]:
        """
        Get song by ID

        Args:
            song_id: Song ID

        Returns:
            Song dictionary or None if not found
        """
        sql = "SELECT * FROM songs WHERE id = ?"
        return self.fetch_one(sql, (song_id,))

    def song_exists(self, file_path: str) -> bool:
        """
        Check if song with file_path already exists

        Args:
            file_path: Absolute file path (will be normalized before checking)

        Returns:
            True if exists, False otherwise

        Note: Path normalization ensures duplicate detection works across
              different path formats (forward/back slashes, relative/absolute)
        """
        if not file_path:
            return False

        # Normalize path for consistent comparison
        try:
            normalized_path = str(Path(file_path).resolve())
        except Exception as e:
            logger.error(f"Failed to normalize path {file_path}: {e}")
            return False

        sql = "SELECT id FROM songs WHERE file_path = ?"
        result = self.fetch_one(sql, (normalized_path,))
        return result is not None

    def update_song(self, song_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update song metadata

        Args:
            song_id: Song ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False if song not found
        """
        # Check song exists
        if not self.get_song_by_id(song_id):
            logger.warning(f"Cannot update non-existent song: {song_id}")
            return False

        # Build UPDATE query dynamically
        fields = []
        values = []

        for key, value in updates.items():
            fields.append(f"{key} = ?")
            values.append(value)

        if not fields:
            logger.warning("No fields to update")
            return False

        # Add modified_date update (avoid trigger recursion)
        fields.append("modified_date = CURRENT_TIMESTAMP")

        values.append(song_id)  # For WHERE clause

        sql = f"UPDATE songs SET {', '.join(fields)} WHERE id = ?"

        try:
            self.execute_query(sql, tuple(values))
            logger.info(f"Updated song {song_id}: {updates}")
            return True
        except Exception as e:
            logger.error(f"Failed to update song {song_id}: {e}")
            return False

    def find_by_metadata(self, title: str, artist: str, duration: int, tolerance: int = 3) -> Optional[Dict[str, Any]]:
        """
        Find song by metadata (title + artist + duration with tolerance)

        Used for intelligent duplicate detection when file paths change.
        Searches case-insensitive with duration tolerance.

        Args:
            title: Song title
            artist: Artist name
            duration: Duration in seconds
            tolerance: Duration tolerance in seconds (default: ±3s)

        Returns:
            Song dictionary if found, None otherwise
        """
        try:
            # Case-insensitive search with duration tolerance
            sql = """
                SELECT * FROM songs
                WHERE LOWER(title) = LOWER(?)
                AND LOWER(artist) = LOWER(?)
                AND duration BETWEEN ? AND ?
                LIMIT 1
            """

            duration_min = duration - tolerance
            duration_max = duration + tolerance

            return self.fetch_one(sql, (title, artist, duration_min, duration_max))

        except Exception as e:
            logger.error(f"Failed to find song by metadata: {e}")
            return None

    def update_song_path(self, song_id: int, new_path: str) -> bool:
        """
        Update file path for a song (used after file rename operations)

        Args:
            song_id: Song ID to update
            new_path: New file path (should be normalized)

        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            # Normalize path before storing
            normalized_path = str(Path(new_path).resolve())

            query = "UPDATE songs SET file_path = ?, modified_date = CURRENT_TIMESTAMP WHERE id = ?"
            cursor = self.conn.cursor()
            cursor.execute(query, (normalized_path, song_id))
            self.conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Updated path for song ID {song_id}: {normalized_path}")
                return True
            else:
                logger.warning(f"Song ID {song_id} not found")
                return False

        except Exception as e:
            logger.error(f"Failed to update path for song {song_id}: {e}")
            return False

    def delete_song(self, song_id: int) -> bool:
        """
        Delete song from database

        Args:
            song_id: Song ID to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            query = "DELETE FROM songs WHERE id = ?"
            cursor = self.conn.cursor()
            cursor.execute(query, (song_id,))
            self.conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Deleted song ID: {song_id}")
                return True
            else:
                logger.warning(f"Song ID {song_id} not found")
                return False

        except Exception as e:
            logger.error(f"Failed to delete song {song_id}: {e}")
            return False

    def cleanup_orphans(self) -> dict:
        """
        Remove songs from database whose files no longer exist

        Returns:
            dict: Statistics about cleanup operation
            {
                'total_checked': int,
                'orphans_found': int,
                'orphans_deleted': int,
                'errors': [str]
            }
        """
        import os

        stats = {
            'total_checked': 0,
            'orphans_found': 0,
            'orphans_deleted': 0,
            'errors': []
        }

        try:
            # Get all songs from database
            all_songs = self.get_all_songs()
            stats['total_checked'] = len(all_songs)

            orphan_ids = []

            # Check each song's file existence
            for song in all_songs:
                file_path = song.get('file_path', '')
                song_id = song.get('id')

                if not file_path or not os.path.exists(file_path):
                    orphan_ids.append(song_id)
                    logger.debug(f"Orphan found: ID {song_id} - {file_path}")

            stats['orphans_found'] = len(orphan_ids)

            # Delete orphans
            for song_id in orphan_ids:
                try:
                    if self.delete_song(song_id):
                        stats['orphans_deleted'] += 1
                except Exception as e:
                    stats['errors'].append(f"Failed to delete song {song_id}: {e}")

            logger.info(
                f"Orphan cleanup: {stats['orphans_deleted']}/{stats['orphans_found']} deleted "
                f"(checked {stats['total_checked']} songs)"
            )

            return stats

        except Exception as e:
            logger.error(f"Orphan cleanup failed: {e}")
            stats['errors'].append(str(e))
            return stats

    def close(self):
        """Close all database connections (thread-safe cleanup)"""
        with self._lock:
            closed_count = 0
            for conn in self._connections:
                try:
                    conn.close()
                    closed_count += 1
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
            self._connections.clear()

        # Clear thread-local connection
        if hasattr(self._local, 'conn'):
            self._local.conn = None

        logger.info(f"Database connections closed ({closed_count} total)")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
