"""
Tests for Library Service

Tests cover:
- Song dataclass (from_dict, to_dict)
- LibraryStats dataclass
- CRUD operations (add, get, update, delete)
- Query operations (search, by_artist, by_album, by_genre)
- Statistics with caching
- Playback tracking (play count, rating)
- Singleton pattern
- Edge cases (empty inputs, invalid IDs, DB errors)
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

# Add src and tests to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

# Mock PySide6 if not available (allows tests to run without GUI framework)
import _mock_pyside6

_mock_pyside6.install()

from services.library_service import LibraryService, LibraryStats, Song

# ==========================================
# Song Dataclass Tests
# ==========================================


class TestSongDataclass:
    """Test Song dataclass creation and conversion"""

    def test_from_dict_full(self):
        """Should create Song from a complete dictionary"""
        data = {
            "id": 1,
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "year": 2020,
            "genre": "Rock",
            "duration": 180.0,
            "file_path": "/music/test.mp3",
            "bitrate": 320,
            "play_count": 5,
            "rating": 4,
            "date_added": "2024-01-01",
            "last_played": "2024-06-01",
        }
        song = Song.from_dict(data)

        assert song.id == 1
        assert song.title == "Test Song"
        assert song.artist == "Test Artist"
        assert song.album == "Test Album"
        assert song.year == 2020
        assert song.genre == "Rock"
        assert song.duration == 180.0
        assert song.file_path == "/music/test.mp3"
        assert song.bitrate == 320
        assert song.play_count == 5
        assert song.rating == 4

    def test_from_dict_minimal(self):
        """Should handle missing fields with defaults"""
        data = {"id": 99, "title": "Minimal"}
        song = Song.from_dict(data)

        assert song.id == 99
        assert song.title == "Minimal"
        assert song.artist is None
        assert song.album is None
        assert song.play_count == 0
        assert song.rating == 0

    def test_from_dict_empty(self):
        """Should create Song from empty dict with defaults"""
        song = Song.from_dict({})

        assert song.id == 0
        assert song.title == "Unknown"
        assert song.artist is None

    def test_to_dict_roundtrip(self):
        """Should survive from_dict -> to_dict roundtrip"""
        data = {
            "id": 5,
            "title": "Roundtrip",
            "artist": "Artist",
            "album": "Album",
            "year": 2023,
            "genre": "Pop",
            "duration": 200.0,
            "file_path": "/a.mp3",
            "bitrate": 256,
            "play_count": 3,
            "rating": 5,
            "date_added": None,
            "last_played": None,
        }
        song = Song.from_dict(data)
        result = song.to_dict()

        assert result["id"] == 5
        assert result["title"] == "Roundtrip"
        assert result["artist"] == "Artist"
        assert result["rating"] == 5


# ==========================================
# LibraryStats Dataclass Tests
# ==========================================


class TestLibraryStatsDataclass:
    """Test LibraryStats dataclass"""

    def test_from_dict(self):
        """Should create LibraryStats from dictionary"""
        data = {
            "total_songs": 100,
            "total_artists": 20,
            "total_albums": 30,
            "total_genres": 10,
            "total_duration_hours": 50.5,
            "total_size_mb": 2048.0,
        }
        stats = LibraryStats.from_dict(data)

        assert stats.total_songs == 100
        assert stats.total_artists == 20
        assert stats.total_duration_hours == 50.5

    def test_from_dict_empty(self):
        """Should default to zeros for empty dict"""
        stats = LibraryStats.from_dict({})

        assert stats.total_songs == 0
        assert stats.total_artists == 0
        assert stats.total_duration_hours == 0.0

    def test_defaults(self):
        """Should have zero defaults"""
        stats = LibraryStats()
        assert stats.total_songs == 0
        assert stats.total_size_mb == 0.0


# ==========================================
# LibraryService Tests (with mocked DB)
# ==========================================


@pytest.fixture
def mock_db():
    """Create a mock DatabaseManager"""
    db = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """Create LibraryService with mocked DB"""
    LibraryService.reset_instance()
    svc = LibraryService.__new__(LibraryService)
    # Manually init QObject-free for testing (avoid PySide6 requirement)
    svc._db_path = ":memory:"
    svc._db_manager = mock_db
    svc._stats_cache = None
    svc._stats_cache_time = None
    svc._stats_cache_ttl = 60
    # Mock signals
    svc.song_added = MagicMock()
    svc.song_updated = MagicMock()
    svc.song_deleted = MagicMock()
    svc.library_changed = MagicMock()
    svc.import_progress = MagicMock()
    svc.import_completed = MagicMock()
    svc.stats_updated = MagicMock()
    svc.error_occurred = MagicMock()
    return svc


class TestGetSong:
    """Test get_song method"""

    def test_get_song_found(self, service, mock_db):
        """Should return Song when found"""
        mock_db.fetch_one.return_value = {"id": 1, "title": "Found Song", "artist": "Artist"}
        result = service.get_song(1)

        assert result is not None
        assert result.title == "Found Song"
        mock_db.fetch_one.assert_called_once()

    def test_get_song_not_found(self, service, mock_db):
        """Should return None when song not found"""
        mock_db.fetch_one.return_value = None
        result = service.get_song(999)

        assert result is None

    def test_get_song_db_error(self, service, mock_db):
        """Should return None and emit error on DB failure"""
        mock_db.fetch_one.side_effect = sqlite3.Error("DB error")
        result = service.get_song(1)

        assert result is None
        service.error_occurred.emit.assert_called_once()


class TestGetSongByPath:
    """Test get_song_by_path method"""

    def test_found(self, service, mock_db):
        """Should return Song when path matches"""
        mock_db.fetch_one.return_value = {"id": 2, "title": "Path Song", "file_path": "/music/song.mp3"}
        result = service.get_song_by_path("/music/song.mp3")

        assert result is not None
        assert result.id == 2

    def test_not_found(self, service, mock_db):
        """Should return None for unknown path"""
        mock_db.fetch_one.return_value = None
        result = service.get_song_by_path("/nonexistent.mp3")

        assert result is None

    def test_db_error(self, service, mock_db):
        """Should return None on DB error"""
        mock_db.fetch_one.side_effect = sqlite3.Error("fail")
        result = service.get_song_by_path("/any.mp3")

        assert result is None


class TestAddSong:
    """Test add_song method"""

    def test_add_song_success(self, service, mock_db):
        """Should return song_id and emit signal"""
        mock_db.add_song.return_value = 42
        result = service.add_song({"title": "New Song", "artist": "Artist"})

        assert result == 42
        service.song_added.emit.assert_called_once_with(42)

    def test_add_song_returns_none_on_failure(self, service, mock_db):
        """Should return None when db.add_song fails"""
        mock_db.add_song.return_value = None
        result = service.add_song({"title": "Bad Song"})

        assert result is None
        service.song_added.emit.assert_not_called()

    def test_add_song_db_error(self, service, mock_db):
        """Should return None and emit error on DB exception"""
        mock_db.add_song.side_effect = sqlite3.Error("insert failed")
        result = service.add_song({"title": "Error Song"})

        assert result is None
        service.error_occurred.emit.assert_called_once()

    def test_add_song_invalidates_cache(self, service, mock_db):
        """Should invalidate stats cache after adding"""
        service._stats_cache = LibraryStats(total_songs=10)
        service._stats_cache_time = datetime.now()
        mock_db.add_song.return_value = 1

        service.add_song({"title": "New"})

        assert service._stats_cache is None
        assert service._stats_cache_time is None


class TestUpdateSong:
    """Test update_song method"""

    def test_update_success(self, service, mock_db):
        """Should delegate to db.update_song and emit signal"""
        mock_db.update_song.return_value = True
        result = service.update_song(1, {"title": "New Title", "artist": "New Artist"})

        assert result is True
        mock_db.update_song.assert_called_once_with(1, {"title": "New Title", "artist": "New Artist"})
        service.song_updated.emit.assert_called_once_with(1)

    def test_update_skips_invalid_fields(self, service, mock_db):
        """Should delegate to db.update_song which handles field validation"""
        mock_db.update_song.return_value = False
        result = service.update_song(1, {"hacker_field": "evil"})

        assert result is False

    def test_update_skips_id_field(self, service, mock_db):
        """Should filter out id field — empty after filter returns False"""
        result = service.update_song(1, {"id": 999})

        assert result is False
        mock_db.update_song.assert_not_called()

    def test_update_db_error(self, service, mock_db):
        """Should return False on DB error"""
        mock_db.update_song.side_effect = sqlite3.Error("update fail")
        result = service.update_song(1, {"title": "X"})

        assert result is False
        service.error_occurred.emit.assert_called_once()

    def test_update_empty_updates(self, service, mock_db):
        """Should return False for empty updates dict"""
        result = service.update_song(1, {})

        assert result is False


class TestDeleteSong:
    """Test delete_song and delete_songs methods"""

    def test_delete_song_success(self, service, mock_db):
        """Should delete and emit signal"""
        result = service.delete_song(1)

        assert result is True
        mock_db.execute_query.assert_called_once()
        service.song_deleted.emit.assert_called_once_with(1)

    def test_delete_song_db_error(self, service, mock_db):
        """Should return False on DB error"""
        mock_db.execute_query.side_effect = sqlite3.Error("delete fail")
        result = service.delete_song(1)

        assert result is False

    def test_delete_songs_multiple(self, service, mock_db):
        """Should delete multiple songs and return count"""
        result = service.delete_songs([1, 2, 3])

        assert result == 3
        service.library_changed.emit.assert_called_once()

    def test_delete_songs_empty_list(self, service, mock_db):
        """Should return 0 for empty list"""
        result = service.delete_songs([])

        assert result == 0
        service.library_changed.emit.assert_not_called()


class TestQueryOperations:
    """Test query/search methods"""

    def test_get_all_songs(self, service, mock_db):
        """Should return list of Song objects"""
        mock_db.fetch_all.return_value = [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}]
        result = service.get_all_songs()

        assert len(result) == 2
        assert all(isinstance(s, Song) for s in result)

    def test_get_all_songs_with_pagination(self, service, mock_db):
        """Should pass limit and offset to DB"""
        mock_db.fetch_all.return_value = []
        service.get_all_songs(limit=10, offset=20)

        args = mock_db.fetch_all.call_args
        assert 10 in args[0][1]
        assert 20 in args[0][1]

    def test_get_all_songs_db_error(self, service, mock_db):
        """Should return empty list on DB error"""
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        result = service.get_all_songs()

        assert result == []

    def test_search(self, service, mock_db):
        """Should delegate to db.search_songs"""
        mock_db.search_songs.return_value = [{"id": 1, "title": "Match"}]
        result = service.search("Match")

        assert len(result) == 1
        assert result[0].title == "Match"

    def test_search_empty_query(self, service, mock_db):
        """Should handle empty query"""
        mock_db.search_songs.return_value = []
        result = service.search("")

        assert result == []

    def test_get_by_artist(self, service, mock_db):
        """Should filter by artist"""
        mock_db.fetch_all.return_value = [{"id": 1, "title": "Song A", "artist": "Artist X"}]
        result = service.get_by_artist("Artist X")

        assert len(result) == 1

    def test_get_by_album_with_artist(self, service, mock_db):
        """Should filter by album and artist"""
        mock_db.fetch_all.return_value = []
        service.get_by_album("Album Y", artist="Artist Z")

        args = mock_db.fetch_all.call_args
        assert "Album Y" in args[0][1]
        assert "Artist Z" in args[0][1]

    def test_get_by_album_without_artist(self, service, mock_db):
        """Should filter by album only when no artist given"""
        mock_db.fetch_all.return_value = []
        service.get_by_album("Album Y")

        args = mock_db.fetch_all.call_args
        assert args[0][1] == ("Album Y",)

    def test_get_by_genre(self, service, mock_db):
        """Should filter by genre using LIKE"""
        mock_db.fetch_all.return_value = []
        service.get_by_genre("Rock")

        args = mock_db.fetch_all.call_args
        assert "%Rock%" in args[0][1][0]

    def test_get_most_played(self, service, mock_db):
        """Should return songs ordered by play_count"""
        mock_db.fetch_all.return_value = [{"id": 1, "title": "Top", "play_count": 100}]
        result = service.get_most_played(limit=5)

        assert len(result) == 1
        assert result[0].title == "Top"


class TestStatistics:
    """Test get_stats with caching"""

    def test_get_stats_fresh(self, service, mock_db):
        """Should fetch from DB when no cache"""
        mock_db.fetch_one.return_value = {
            "total_songs": 50,
            "total_artists": 10,
            "total_albums": 15,
            "total_genres": 5,
            "total_duration_hours": 25.0,
        }
        result = service.get_stats()

        assert result.total_songs == 50
        assert result.total_artists == 10
        service.stats_updated.emit.assert_called_once()

    def test_get_stats_cached(self, service, mock_db):
        """Should return cache when valid"""
        cached = LibraryStats(total_songs=99)
        service._stats_cache = cached
        service._stats_cache_time = datetime.now()

        result = service.get_stats()

        assert result.total_songs == 99
        mock_db.fetch_one.assert_not_called()

    def test_get_stats_cache_expired(self, service, mock_db):
        """Should refresh when cache is expired"""
        service._stats_cache = LibraryStats(total_songs=1)
        service._stats_cache_time = datetime.now() - timedelta(seconds=120)
        mock_db.fetch_one.return_value = {
            "total_songs": 50,
            "total_artists": 10,
            "total_albums": 15,
            "total_genres": 5,
            "total_duration_hours": 25.0,
        }

        result = service.get_stats()

        assert result.total_songs == 50
        mock_db.fetch_one.assert_called_once()

    def test_get_stats_force_refresh(self, service, mock_db):
        """Should force refresh even when cache is valid"""
        service._stats_cache = LibraryStats(total_songs=1)
        service._stats_cache_time = datetime.now()
        mock_db.fetch_one.return_value = {
            "total_songs": 200,
            "total_artists": 40,
            "total_albums": 60,
            "total_genres": 15,
            "total_duration_hours": 100.0,
        }

        result = service.get_stats(force_refresh=True)

        assert result.total_songs == 200

    def test_get_stats_db_error(self, service, mock_db):
        """Should return empty stats on DB error"""
        mock_db.fetch_one.side_effect = sqlite3.Error("fail")

        result = service.get_stats()

        assert result.total_songs == 0

    def test_get_stats_no_result(self, service, mock_db):
        """Should return empty stats when DB returns None"""
        mock_db.fetch_one.return_value = None

        result = service.get_stats()

        assert result.total_songs == 0


class TestPlaybackTracking:
    """Test play count and rating"""

    def test_increment_play_count(self, service, mock_db):
        """Should increment play count and emit signal"""
        result = service.increment_play_count(1)

        assert result is True
        mock_db.execute_query.assert_called_once()
        service.song_updated.emit.assert_called_once_with(1)

    def test_increment_play_count_db_error(self, service, mock_db):
        """Should return False on DB error"""
        mock_db.execute_query.side_effect = sqlite3.Error("fail")
        result = service.increment_play_count(1)

        assert result is False

    def test_set_rating_valid(self, service, mock_db):
        """Should accept valid rating 0-5"""
        mock_db.update_song.return_value = True
        result = service.set_rating(1, 4)
        assert result is True

    def test_set_rating_too_high(self, service, mock_db):
        """Should reject rating > 5"""
        result = service.set_rating(1, 6)
        assert result is False

    def test_set_rating_negative(self, service, mock_db):
        """Should reject negative rating"""
        result = service.set_rating(1, -1)
        assert result is False

    def test_set_rating_zero(self, service, mock_db):
        """Should accept rating of 0"""
        mock_db.update_song.return_value = True
        result = service.set_rating(1, 0)
        assert result is True


class TestUniqueValues:
    """Test get_all_artists/albums/genres"""

    def test_get_all_artists(self, service, mock_db):
        """Should return list of artist names"""
        mock_db.fetch_all.return_value = [{"artist": "Artist A"}, {"artist": "Artist B"}]
        result = service.get_all_artists()

        assert result == ["Artist A", "Artist B"]

    def test_get_all_artists_filters_none(self, service, mock_db):
        """Should filter out None artists"""
        mock_db.fetch_all.return_value = [{"artist": "Good"}, {"artist": None}]
        result = service.get_all_artists()

        assert result == ["Good"]

    def test_get_all_albums(self, service, mock_db):
        """Should return list of album names"""
        mock_db.fetch_all.return_value = [{"album": "Album 1"}]
        result = service.get_all_albums()

        assert result == ["Album 1"]

    def test_get_all_genres(self, service, mock_db):
        """Should return list of genre names"""
        mock_db.fetch_all.return_value = [{"genre": "Rock"}, {"genre": "Pop"}]
        result = service.get_all_genres()

        assert result == ["Rock", "Pop"]

    def test_get_all_artists_db_error(self, service, mock_db):
        """Should return empty list on DB error"""
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        result = service.get_all_artists()

        assert result == []


class TestSingleton:
    """Test singleton pattern"""

    def test_reset_instance(self):
        """Should reset singleton"""
        LibraryService._instance = "fake"
        LibraryService.reset_instance()

        assert LibraryService._instance is None


class TestCleanup:
    """Test cleanup method"""

    def test_cleanup_with_db(self, service, mock_db):
        """Should close DB manager"""
        service.cleanup()

        mock_db.close.assert_called_once()
        assert service._db_manager is None

    def test_cleanup_without_db(self, service):
        """Should handle cleanup when no DB loaded"""
        service._db_manager = None
        service.cleanup()  # Should not raise
