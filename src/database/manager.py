"""
NEXUS Music Manager - Database Manager
High-performance SQLite manager with WAL mode and FTS5
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    High-performance SQLite manager for music library

    Features:
    - WAL mode for concurrent reads (2-3x faster writes)
    - FTS5 for millisecond search
    - Auto-migration system
    - Foreign key enforcement
    """

    def __init__(self, db_path: str = "music_library.db"):
        """Initialize database manager with optimized connection"""
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._setup_database()

    def _setup_database(self):
        """Setup database with performance optimizations"""
        # Create database directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect with optimized settings
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,  # Allow multi-threading
            timeout=30.0  # 30 second timeout
        )

        # Return rows as dictionaries
        self.conn.row_factory = sqlite3.Row

        # Apply performance optimizations
        self._apply_performance_pragmas()

        # Run migrations
        self._run_migrations()

        logger.info(f"Database initialized: {self.db_path}")

    def _apply_performance_pragmas(self):
        """Apply performance optimizations"""
        cursor = self.conn.cursor()

        # WAL mode: 2-3x faster writes + concurrent reads
        cursor.execute("PRAGMA journal_mode = WAL")

        # Balance durability and speed
        cursor.execute("PRAGMA synchronous = NORMAL")

        # 64MB cache
        cursor.execute("PRAGMA cache_size = -64000")

        # Memory-mapped I/O
        cursor.execute("PRAGMA mmap_size = 30000000000")  # 30GB

        # Temp tables in memory
        cursor.execute("PRAGMA temp_store = MEMORY")

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        self.conn.commit()

        logger.info("Performance PRAGMAs applied (WAL mode, 64MB cache)")

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
        """
        # Check for duplicate file_path
        if self.song_exists(song_data.get('file_path', '')):
            logger.warning(f"Song already exists: {song_data.get('file_path')}")
            return None

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
            file_path: Absolute file path

        Returns:
            True if exists, False otherwise
        """
        if not file_path:
            return False

        sql = "SELECT id FROM songs WHERE file_path = ?"
        result = self.fetch_one(sql, (file_path,))
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

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
