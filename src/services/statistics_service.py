"""
Statistics Service - Analytics and Listening Statistics

Provides detailed analytics about music listening habits.

Features:
- Total listening time (all-time, weekly, monthly)
- Top artists, albums, genres
- Play count statistics
- Listening trends over time
- Peak listening hours
- Decade breakdown

Created: December 11, 2025
"""

import logging
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class ListeningStats:
    """Container for listening statistics"""

    total_plays: int = 0
    total_duration_seconds: int = 0
    unique_songs: int = 0
    unique_artists: int = 0
    unique_albums: int = 0
    unique_genres: int = 0

    @property
    def total_hours(self) -> float:
        return self.total_duration_seconds / 3600

    @property
    def total_days(self) -> float:
        return self.total_duration_seconds / 86400


class StatisticsService:
    """
    Statistics Service for Music Library Analytics

    Provides comprehensive statistics about listening habits,
    library composition, and trends.

    Usage:
        stats = StatisticsService(db_manager)

        # Get overview
        overview = stats.get_library_overview()

        # Get top artists
        top_artists = stats.get_top_artists(limit=10)

        # Get listening trends
        weekly = stats.get_weekly_stats()
    """

    def __init__(self, db_manager: Any) -> None:
        """
        Initialize statistics service

        Args:
            db_manager: DatabaseManager instance
        """
        self.db: Any = db_manager
        logger.info("StatisticsService initialized")

    # ==========================================
    # Library Overview Statistics
    # ==========================================

    def get_library_overview(self) -> Dict[str, Any]:
        """
        Get complete library overview statistics

        Returns:
            Dictionary with library stats:
            {
                'total_songs': int,
                'total_artists': int,
                'total_albums': int,
                'total_genres': int,
                'total_duration_hours': float,
                'total_size_gb': float,
                'avg_bitrate': int,
                'oldest_song_year': int,
                'newest_song_year': int
            }
        """
        try:
            stats = {}

            # Basic counts
            result = self.db.fetch_one(
                """
                SELECT
                    COUNT(*) as total_songs,
                    COUNT(DISTINCT artist) as total_artists,
                    COUNT(DISTINCT album) as total_albums,
                    COUNT(DISTINCT genre) as total_genres,
                    SUM(duration) as total_duration,
                    SUM(file_size) as total_size,
                    AVG(bitrate) as avg_bitrate,
                    MIN(year) as oldest_year,
                    MAX(year) as newest_year
                FROM songs
                WHERE artist IS NOT NULL
            """
            )

            if result:
                stats["total_songs"] = result["total_songs"] or 0
                stats["total_artists"] = result["total_artists"] or 0
                stats["total_albums"] = result["total_albums"] or 0
                stats["total_genres"] = result["total_genres"] or 0
                stats["total_duration_hours"] = (result["total_duration"] or 0) / 3600
                stats["total_size_gb"] = (result["total_size"] or 0) / (1024**3)
                stats["avg_bitrate"] = int(result["avg_bitrate"] or 0)
                stats["oldest_song_year"] = result["oldest_year"]
                stats["newest_song_year"] = result["newest_year"]

            # Play statistics
            play_result = self.db.fetch_one(
                """
                SELECT
                    SUM(play_count) as total_plays,
                    COUNT(CASE WHEN play_count > 0 THEN 1 END) as songs_played
                FROM songs
            """
            )

            if play_result:
                stats["total_plays"] = play_result["total_plays"] or 0
                stats["songs_played"] = play_result["songs_played"] or 0

            return stats

        except sqlite3.Error as e:
            logger.error(f"Failed to get library overview: {e}")
            return {}

    # ==========================================
    # Top Charts
    # ==========================================

    def get_top_artists(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top artists by song count and play count

        Returns:
            List of artists with stats:
            [
                {
                    'artist': str,
                    'song_count': int,
                    'total_plays': int,
                    'total_duration_hours': float
                }
            ]
        """
        try:
            results = self.db.fetch_all(
                """
                SELECT
                    artist,
                    COUNT(*) as song_count,
                    SUM(play_count) as total_plays,
                    SUM(duration) as total_duration
                FROM songs
                WHERE artist IS NOT NULL AND artist != ''
                GROUP BY artist
                ORDER BY total_plays DESC, song_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [
                {
                    "artist": r["artist"],
                    "song_count": r["song_count"],
                    "total_plays": r["total_plays"] or 0,
                    "total_duration_hours": (r["total_duration"] or 0) / 3600,
                }
                for r in results
            ]

        except sqlite3.Error as e:
            logger.error(f"Failed to get top artists: {e}")
            return []

    def get_top_albums(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top albums by play count"""
        try:
            results = self.db.fetch_all(
                """
                SELECT
                    album,
                    artist,
                    COUNT(*) as song_count,
                    SUM(play_count) as total_plays,
                    SUM(duration) as total_duration
                FROM songs
                WHERE album IS NOT NULL AND album != ''
                GROUP BY album, artist
                ORDER BY total_plays DESC, song_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [
                {
                    "album": r["album"],
                    "artist": r["artist"],
                    "song_count": r["song_count"],
                    "total_plays": r["total_plays"] or 0,
                    "total_duration_hours": (r["total_duration"] or 0) / 3600,
                }
                for r in results
            ]

        except sqlite3.Error as e:
            logger.error(f"Failed to get top albums: {e}")
            return []

    def get_top_songs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most played songs"""
        try:
            results = self.db.fetch_all(
                """
                SELECT
                    id,
                    title,
                    artist,
                    album,
                    play_count,
                    duration,
                    last_played
                FROM songs
                WHERE play_count > 0
                ORDER BY play_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(r) for r in results]

        except sqlite3.Error as e:
            logger.error(f"Failed to get top songs: {e}")
            return []

    def get_top_genres(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top genres by song count"""
        try:
            results = self.db.fetch_all(
                """
                SELECT
                    genre,
                    COUNT(*) as song_count,
                    SUM(play_count) as total_plays,
                    SUM(duration) as total_duration
                FROM songs
                WHERE genre IS NOT NULL AND genre != ''
                GROUP BY genre
                ORDER BY song_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [
                {
                    "genre": r["genre"],
                    "song_count": r["song_count"],
                    "total_plays": r["total_plays"] or 0,
                    "total_duration_hours": (r["total_duration"] or 0) / 3600,
                }
                for r in results
            ]

        except sqlite3.Error as e:
            logger.error(f"Failed to get top genres: {e}")
            return []

    # ==========================================
    # Time-based Statistics
    # ==========================================

    def get_decade_breakdown(self) -> List[Dict[str, Any]]:
        """
        Get song count by decade

        Returns:
            List of decades with song counts
        """
        try:
            results = self.db.fetch_all(
                """
                SELECT
                    (year / 10) * 10 as decade,
                    COUNT(*) as song_count,
                    SUM(play_count) as total_plays
                FROM songs
                WHERE year IS NOT NULL AND year > 1900
                GROUP BY decade
                ORDER BY decade DESC
            """
            )

            return [
                {
                    "decade": f"{r['decade']}s",
                    "decade_year": r["decade"],
                    "song_count": r["song_count"],
                    "total_plays": r["total_plays"] or 0,
                }
                for r in results
            ]

        except sqlite3.Error as e:
            logger.error(f"Failed to get decade breakdown: {e}")
            return []

    def get_recently_added(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently added songs"""
        try:
            results = self.db.fetch_all(
                """
                SELECT id, title, artist, album, added_date
                FROM songs
                ORDER BY added_date DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(r) for r in results]

        except sqlite3.Error as e:
            logger.error(f"Failed to get recently added: {e}")
            return []

    def get_recently_played(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently played songs"""
        try:
            results = self.db.fetch_all(
                """
                SELECT id, title, artist, album, last_played, play_count
                FROM songs
                WHERE last_played IS NOT NULL
                ORDER BY last_played DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(r) for r in results]

        except sqlite3.Error as e:
            logger.error(f"Failed to get recently played: {e}")
            return []

    # ==========================================
    # Quality & Metadata Statistics
    # ==========================================

    def get_bitrate_distribution(self) -> List[Dict[str, Any]]:
        """Get distribution of songs by bitrate quality"""
        try:
            results = self.db.fetch_all(
                """
                SELECT
                    CASE
                        WHEN bitrate >= 320 THEN 'High (320+ kbps)'
                        WHEN bitrate >= 256 THEN 'Good (256-319 kbps)'
                        WHEN bitrate >= 192 THEN 'Medium (192-255 kbps)'
                        WHEN bitrate >= 128 THEN 'Low (128-191 kbps)'
                        ELSE 'Very Low (<128 kbps)'
                    END as quality,
                    COUNT(*) as song_count,
                    AVG(bitrate) as avg_bitrate
                FROM songs
                WHERE bitrate IS NOT NULL AND bitrate > 0
                GROUP BY quality
                ORDER BY avg_bitrate DESC
            """
            )

            return [
                {"quality": r["quality"], "song_count": r["song_count"], "avg_bitrate": int(r["avg_bitrate"] or 0)}
                for r in results
            ]

        except sqlite3.Error as e:
            logger.error(f"Failed to get bitrate distribution: {e}")
            return []

    def get_metadata_completeness(self) -> Dict[str, Any]:
        """Get statistics on metadata completeness"""
        try:
            total = self.db.fetch_one("SELECT COUNT(*) as count FROM songs")
            total_count = total["count"] if total else 0

            if total_count == 0:
                return {"total": 0, "fields": {}}

            # Check each field (allowlist validated to prevent SQL injection)
            fields = {}
            _ALLOWED_FIELDS = frozenset({"artist", "album", "year", "genre", "duration", "bitrate"})
            field_names = ["artist", "album", "year", "genre", "duration", "bitrate"]

            for field in field_names:
                if field not in _ALLOWED_FIELDS:
                    continue  # skip unknown fields (defensive)
                result = self.db.fetch_one(
                    f"""
                    SELECT COUNT(*) as count
                    FROM songs
                    WHERE {field} IS NOT NULL
                    AND {field} != ''
                    AND {field} != 0
                """
                )
                count = result["count"] if result else 0
                fields[field] = {"count": count, "percentage": (count / total_count) * 100}

            return {"total": total_count, "fields": fields}

        except sqlite3.Error as e:
            logger.error(f"Failed to get metadata completeness: {e}")
            return {"total": 0, "fields": {}}

    # ==========================================
    # Listening Trends (requires play_history)
    # ==========================================

    def get_listening_by_hour(self) -> List[Dict[str, Any]]:
        """
        Get play counts by hour of day

        Note: Requires play_history table
        """
        try:
            # Try to use play_history if available
            results = self.db.fetch_all(
                """
                SELECT
                    strftime('%H', last_played) as hour,
                    COUNT(*) as play_count
                FROM songs
                WHERE last_played IS NOT NULL
                GROUP BY hour
                ORDER BY hour
            """
            )

            # Fill in missing hours
            hour_data = {str(i).zfill(2): 0 for i in range(24)}
            for r in results:
                if r["hour"]:
                    hour_data[r["hour"]] = r["play_count"]

            return [{"hour": h, "play_count": c} for h, c in sorted(hour_data.items())]

        except sqlite3.Error as e:
            logger.error(f"Failed to get listening by hour: {e}")
            return []

    def get_listening_by_day(self) -> List[Dict[str, Any]]:
        """Get play counts by day of week"""
        try:
            results = self.db.fetch_all(
                """
                SELECT
                    strftime('%w', last_played) as day_num,
                    COUNT(*) as play_count
                FROM songs
                WHERE last_played IS NOT NULL
                GROUP BY day_num
                ORDER BY day_num
            """
            )

            day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

            day_data = {str(i): {"day": day_names[i], "play_count": 0} for i in range(7)}
            for r in results:
                if r["day_num"]:
                    day_num = int(r["day_num"])
                    day_data[str(day_num)]["play_count"] = r["play_count"]

            return list(day_data.values())

        except sqlite3.Error as e:
            logger.error(f"Failed to get listening by day: {e}")
            return []

    # ==========================================
    # Record Play Event
    # ==========================================

    def record_play(self, song_id: int, duration_played: int = 0, completed: bool = False) -> None:
        """
        Record a play event in play_history.

        Note: play_count increment is handled by LibraryService.increment_play_count()
        which is called from main.py on song play start. This method only records
        the play event details (duration, completion) in the history table.

        Args:
            song_id: ID of the song played
            duration_played: Seconds actually played
            completed: Whether the song was played to completion
        """
        try:
            self.db.execute_query(
                """
                INSERT INTO play_history (song_id, duration_played, completed)
                VALUES (?, ?, ?)
            """,
                (song_id, duration_played, completed),
            )
            logger.debug(f"Recorded play for song {song_id}")

        except sqlite3.OperationalError:
            # play_history table might not exist yet — safe to ignore
            pass
        except sqlite3.Error as e:
            logger.error(f"Failed to record play for song {song_id}: {e}")

    # ==========================================
    # Summary Statistics
    # ==========================================

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for dashboard display

        Returns comprehensive stats in a single call
        """
        return {
            "overview": self.get_library_overview(),
            "top_artists": self.get_top_artists(5),
            "top_songs": self.get_top_songs(5),
            "top_genres": self.get_top_genres(5),
            "decades": self.get_decade_breakdown(),
            "recently_added": self.get_recently_added(5),
            "recently_played": self.get_recently_played(5),
            "quality": self.get_bitrate_distribution(),
            "metadata": self.get_metadata_completeness(),
        }
