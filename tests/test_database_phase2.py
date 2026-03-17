"""
Phase 2 coverage tests for src/database/manager.py

Covers uncovered CRUD paths: update_song, delete_song, update_song_path,
find_by_metadata, cleanup_orphans, context manager, LIKE fallback,
close error handling, edge cases.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402

from database.manager import ALLOWED_SONG_FIELDS, DatabaseManager  # noqa: E402


@pytest.fixture
def db(tmp_path):
    """Create a temp database with proper cleanup"""
    db_path = str(tmp_path / "test.db")
    mgr = DatabaseManager(db_path)
    yield mgr
    mgr.close()


@pytest.fixture
def db_with_song(db):
    """DB with one song already added"""
    song_id = db.add_song(
        {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "year": 2025,
            "genre": "Pop",
            "duration": 200,
            "bitrate": 320000,
            "sample_rate": 44100,
            "file_path": "/music/test_song.mp3",
            "file_size": 5000000,
        }
    )
    return db, song_id


# ==========================================
# update_song tests (lines 448-475)
# ==========================================
class TestUpdateSong:
    """Cover update_song paths"""

    def test_update_song_success(self, db_with_song) -> None:
        """Update valid fields on existing song"""
        db, song_id = db_with_song
        result = db.update_song(song_id, {"title": "New Title", "artist": "New Artist"})
        assert result is True

        song = db.get_song_by_id(song_id)
        assert song["title"] == "New Title"
        assert song["artist"] == "New Artist"

    def test_update_song_not_found(self, db) -> None:
        """Update returns False for non-existent song"""
        result = db.update_song(99999, {"title": "X"})
        assert result is False

    def test_update_song_invalid_field_skipped(self, db_with_song) -> None:
        """Invalid field names are skipped"""
        db, song_id = db_with_song
        result = db.update_song(song_id, {"INVALID_FIELD": "val", "title": "Valid"})
        assert result is True

        song = db.get_song_by_id(song_id)
        assert song["title"] == "Valid"

    def test_update_song_no_valid_fields(self, db_with_song) -> None:
        """Update with only invalid fields returns False"""
        db, song_id = db_with_song
        result = db.update_song(song_id, {"BAD_FIELD": "x"})
        assert result is False


# ==========================================
# delete_song tests (lines 553-568)
# ==========================================
class TestDeleteSong:
    """Cover delete_song paths"""

    def test_delete_song_success(self, db_with_song) -> None:
        """Delete existing song succeeds"""
        db, song_id = db_with_song
        result = db.delete_song(song_id)
        assert result is True
        assert db.get_song_by_id(song_id) is None

    def test_delete_song_not_found(self, db) -> None:
        """Delete non-existent song returns False"""
        result = db.delete_song(99999)
        assert result is False


# ==========================================
# update_song_path tests (lines 523-541)
# ==========================================
class TestUpdateSongPath:
    """Cover update_song_path paths"""

    def test_update_path_success(self, db_with_song) -> None:
        """Update path for existing song"""
        db, song_id = db_with_song
        result = db.update_song_path(song_id, "/music/new_path.mp3")
        assert result is True

    def test_update_path_not_found(self, db) -> None:
        """Update path for non-existent song returns False"""
        result = db.update_song_path(99999, "/music/x.mp3")
        assert result is False


# ==========================================
# find_by_metadata tests (lines 493-510)
# ==========================================
class TestFindByMetadata:
    """Cover find_by_metadata paths"""

    def test_find_by_metadata_match(self, db_with_song) -> None:
        """Find song by title, artist, duration"""
        db, song_id = db_with_song
        result = db.find_by_metadata("Test Song", "Test Artist", 200)
        assert result is not None
        assert result["id"] == song_id

    def test_find_by_metadata_with_tolerance(self, db_with_song) -> None:
        """Find song with duration within tolerance"""
        db, song_id = db_with_song
        result = db.find_by_metadata("Test Song", "Test Artist", 202, tolerance=5)
        assert result is not None

    def test_find_by_metadata_no_match(self, db_with_song) -> None:
        """Return None when no match found"""
        db, _ = db_with_song
        result = db.find_by_metadata("Nonexistent", "Nobody", 100)
        assert result is None

    def test_find_by_metadata_case_insensitive(self, db_with_song) -> None:
        """Search is case-insensitive"""
        db, song_id = db_with_song
        result = db.find_by_metadata("TEST SONG", "TEST ARTIST", 200)
        assert result is not None
        assert result["id"] == song_id


# ==========================================
# cleanup_orphans tests (lines 583-636)
# ==========================================
class TestCleanupOrphans:
    """Cover cleanup_orphans paths"""

    def test_cleanup_no_orphans(self, db_with_song, tmp_path) -> None:
        """No orphans when all files exist"""
        db, song_id = db_with_song
        # Create the file so it's not an orphan
        real_file = tmp_path / "real_song.mp3"
        real_file.touch()
        db.update_song_path(song_id, str(real_file))

        stats = db.cleanup_orphans()
        assert stats["total_checked"] == 1
        assert stats["orphans_found"] == 0
        assert stats["orphans_deleted"] == 0

    def test_cleanup_deletes_orphans(self, db) -> None:
        """Orphan songs (missing files) are deleted"""
        # Add songs with non-existent file paths
        db.add_song({"title": "Orphan1", "file_path": "/nonexistent/a.mp3"})
        db.add_song({"title": "Orphan2", "file_path": "/nonexistent/b.mp3"})

        stats = db.cleanup_orphans()
        assert stats["orphans_found"] == 2
        assert stats["orphans_deleted"] == 2
        assert db.get_song_count() == 0

    def test_cleanup_empty_db(self, db) -> None:
        """Cleanup on empty db returns zero counts"""
        stats = db.cleanup_orphans()
        assert stats["total_checked"] == 0
        assert stats["orphans_found"] == 0


# ==========================================
# Context manager tests (lines 658, 664)
# ==========================================
class TestContextManager:
    """Cover __enter__ and __exit__"""

    def test_context_manager(self, tmp_path) -> None:
        """Context manager opens and closes properly"""
        db_path = str(tmp_path / "ctx.db")
        with DatabaseManager(db_path) as db:
            assert db is not None
            db.add_song({"title": "CTX Song", "file_path": "/ctx/song.mp3"})
            assert db.get_song_count() == 1


# ==========================================
# close error handling (lines 646-647)
# ==========================================
class TestCloseErrorHandling:
    """Cover close connection error path"""

    def test_close_already_closed_connection(self, tmp_path) -> None:
        """Closing already-closed connection doesn't crash"""
        db_path = str(tmp_path / "close_test.db")
        db = DatabaseManager(db_path)
        # Close the internal connection manually
        for conn in db._connections:
            conn.close()
        # close() should handle the error gracefully
        db.close()

    def test_close_with_broken_connection(self, tmp_path) -> None:
        """Close handles sqlite3.Error from broken connection"""
        import sqlite3
        from unittest.mock import MagicMock

        db_path = str(tmp_path / "broken.db")
        db = DatabaseManager(db_path)
        # Replace one connection with a mock that raises on close
        mock_conn = MagicMock()
        mock_conn.close.side_effect = sqlite3.Error("disk I/O error")
        db._connections.append(mock_conn)
        # Should not raise
        db.close()


# ==========================================
# song_exists edge cases (lines 418, 423-425)
# ==========================================
class TestSongExistsEdgeCases:
    """Cover edge cases in song_exists"""

    def test_song_exists_empty_path(self, db) -> None:
        """song_exists returns False for empty string"""
        assert db.song_exists("") is False

    def test_add_song_no_file_path(self, db) -> None:
        """add_song returns None when file_path is missing"""
        result = db.add_song({"title": "No Path"})
        assert result is None

    def test_add_song_duplicate_detected(self, db_with_song) -> None:
        """add_song returns None for duplicate file_path"""
        db, _ = db_with_song
        result = db.add_song({"title": "Dup", "file_path": "/music/test_song.mp3"})
        assert result is None


# ==========================================
# search_songs LIKE fallback (lines 267-278)
# ==========================================
class TestSearchLikeFallback:
    """Cover FTS5 fallback to LIKE search"""

    def test_search_with_empty_fts5_query(self, db_with_song) -> None:
        """Sanitized query that becomes empty returns safely"""
        db, _ = db_with_song
        result = db.search_songs("!@#$%^&*()")
        assert isinstance(result, list)

    def test_sanitize_fts5_empty_tokens(self) -> None:
        """_sanitize_fts5_query returns '\"\"' when all tokens are removed"""
        result = DatabaseManager._sanitize_fts5_query("!@#$%")
        assert result == '""'

    def test_search_like_fallback(self, db_with_song) -> None:
        """When FTS5 is unavailable, LIKE search is used as fallback"""
        import sqlite3
        from unittest.mock import patch

        db, _ = db_with_song
        original_fetch_all = db.fetch_all

        call_count = 0

        def mock_fetch_all(sql, params=()):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and "MATCH" in sql:
                raise sqlite3.OperationalError("no such table: songs_fts")
            return original_fetch_all(sql, params)

        with patch.object(db, "fetch_all", side_effect=mock_fetch_all):
            results = db.search_songs("Test")
            assert isinstance(results, list)


# ==========================================
# ALLOWED_SONG_FIELDS sanity
# ==========================================
class TestAllowedFields:
    """Verify ALLOWED_SONG_FIELDS is correct"""

    def test_core_fields_present(self) -> None:
        """Core metadata fields are in allowlist"""
        for field in ["title", "artist", "album", "year", "genre", "duration", "file_path"]:
            assert field in ALLOWED_SONG_FIELDS

    def test_ai_fields_present(self) -> None:
        """AI analysis fields are in allowlist"""
        for field in ["bpm", "mood", "energy", "valence", "embedding"]:
            assert field in ALLOWED_SONG_FIELDS
