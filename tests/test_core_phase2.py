"""
Phase 2 Tests for src/core/ module — MAPS Round 27

Covers uncovered methods and branches in:
- SmartPlaylistEngine: CRUD, generate, builtin playlists, evaluate_rule branches, save/load
- LibraryOrganizer: organize (dry_run + real), build_path, rollback
- PlaylistManager: error paths, rename, add_song, reorder, save/load, duplicate, stats
- DuplicateDetector: detect_by_metadata, detect_by_filesize, detect_by_fingerprint
- MetadataTagger: lookup_and_tag, embed_album_art
- DownloadQueue: queue operations via QObject bypass

Pattern: module-level QApplication to bypass conftest qapp auto-skip.
"""

import os
import sqlite3
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Module-level QApplication (bypasses conftest qapp skip)
try:
    from PySide6.QtWidgets import QApplication

    _app = QApplication.instance()
    if _app is None:
        _app = QApplication(sys.argv)
except ImportError:
    pass


# ==========================================
# SmartPlaylistEngine Tests
# ==========================================


class TestSmartPlaylistEnginePhase2:
    """Tests for SmartPlaylistEngine — uncovered CRUD, generate, rules, persistence."""

    @pytest.fixture
    def engine(self):
        from core.smart_playlist import SmartPlaylistEngine

        mock_db = MagicMock()
        mock_db.get_all_songs.return_value = [
            {
                "id": 1,
                "title": "Rock Song",
                "artist": "Band A",
                "genre": "Rock",
                "year": 1985,
                "play_count": 10,
                "rating": 5,
                "duration": 240,
                "date_added": "2024-01-01",
                "last_played": "2024-06-01",
                "album": "Album1",
            },
            {
                "id": 2,
                "title": "Pop Song",
                "artist": "Singer B",
                "genre": "Pop",
                "year": 2020,
                "play_count": 0,
                "rating": 3,
                "duration": 180,
                "date_added": "2024-06-01",
                "last_played": None,
                "album": "Album2",
            },
            {
                "id": 3,
                "title": "Jazz Song",
                "artist": "Jazz C",
                "genre": "Jazz",
                "year": 1970,
                "play_count": 5,
                "rating": 4,
                "duration": 300,
                "date_added": "2023-01-01",
                "last_played": "2024-03-01",
                "album": "Album3",
            },
        ]
        return SmartPlaylistEngine(mock_db)

    @pytest.fixture
    def config(self):
        from core.smart_playlist import PlaylistRule, SmartPlaylistConfig

        return SmartPlaylistConfig(
            name="Test Playlist",
            rules=[PlaylistRule(field="genre", operator="contains", value="Rock")],
            combine_mode="all",
            limit=0,
        )

    # --- CRUD ---

    def test_create_playlist(self, engine, config):
        assert engine.create_playlist(config) is True
        assert "Test Playlist" in engine.list_playlists()

    def test_create_duplicate(self, engine, config):
        engine.create_playlist(config)
        assert engine.create_playlist(config) is False

    def test_update_playlist(self, engine, config):
        engine.create_playlist(config)
        config.description = "Updated"
        assert engine.update_playlist("Test Playlist", config) is True

    def test_update_playlist_rename(self, engine, config):
        engine.create_playlist(config)
        config.name = "Renamed"
        assert engine.update_playlist("Test Playlist", config) is True
        assert "Renamed" in engine.list_playlists()
        assert "Test Playlist" not in engine.list_playlists()

    def test_update_not_found(self, engine, config):
        assert engine.update_playlist("Nonexistent", config) is False

    def test_delete_playlist(self, engine, config):
        engine.create_playlist(config)
        assert engine.delete_playlist("Test Playlist") is True
        assert "Test Playlist" not in engine.list_playlists()

    def test_delete_not_found(self, engine):
        assert engine.delete_playlist("Nonexistent") is False

    def test_get_playlist(self, engine, config):
        engine.create_playlist(config)
        assert engine.get_playlist("Test Playlist") is config
        assert engine.get_playlist("Nonexistent") is None

    def test_set_library_db(self, engine):
        new_db = Mock()
        engine.set_library_db(new_db)
        assert engine.library_db is new_db

    # --- generate_playlist ---

    def test_generate_contains_rule(self, engine, config):
        songs = engine.generate_playlist(config)
        assert len(songs) == 1
        assert songs[0]["genre"] == "Rock"

    def test_generate_no_db(self):
        from core.smart_playlist import SmartPlaylistEngine

        engine = SmartPlaylistEngine(None)
        from core.smart_playlist import SmartPlaylistConfig

        config = SmartPlaylistConfig(name="Empty")
        assert engine.generate_playlist(config) == []

    def test_generate_no_songs(self, engine, config):
        engine.library_db.get_all_songs.return_value = []
        assert engine.generate_playlist(config) == []

    def test_generate_with_limit(self, engine):
        from core.smart_playlist import SmartPlaylistConfig

        config = SmartPlaylistConfig(name="Limited", limit=2)
        songs = engine.generate_playlist(config)
        assert len(songs) == 2

    def test_generate_cached(self, engine, config):
        songs1 = engine.generate_playlist(config)
        songs2 = engine.generate_playlist(config, use_cache=True)
        assert songs1 is songs2  # Same cached object

    def test_generate_any_mode(self, engine):
        from core.smart_playlist import PlaylistRule, SmartPlaylistConfig

        config = SmartPlaylistConfig(
            name="Any Mode",
            rules=[
                PlaylistRule(field="genre", operator="contains", value="Rock"),
                PlaylistRule(field="genre", operator="contains", value="Jazz"),
            ],
            combine_mode="any",
        )
        songs = engine.generate_playlist(config)
        assert len(songs) == 2  # Rock + Jazz

    # --- refresh ---

    def test_refresh_playlist(self, engine, config):
        engine.create_playlist(config)
        result = engine.refresh_playlist("Test Playlist")
        assert len(result) == 1

    def test_refresh_not_found(self, engine):
        assert engine.refresh_playlist("Nonexistent") == []

    def test_refresh_all(self, engine, config):
        engine.create_playlist(config)
        engine.refresh_all()  # Should not raise

    # --- _evaluate_rule branches ---

    def test_rule_equals(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="play_count", operator="equals", value=0)
        assert engine._evaluate_rule({"play_count": 0}, rule) is True
        assert engine._evaluate_rule({"play_count": 5}, rule) is False

    def test_rule_not_equals(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="genre", operator="not_equals", value="Rock")
        assert engine._evaluate_rule({"genre": "Pop"}, rule) is True

    def test_rule_not_contains(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="title", operator="not_contains", value="bad")
        assert engine._evaluate_rule({"title": "Good Song"}, rule) is True

    def test_rule_starts_with(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="title", operator="starts_with", value="rock")
        assert engine._evaluate_rule({"title": "Rock Song"}, rule) is True

    def test_rule_ends_with(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="title", operator="ends_with", value="song")
        assert engine._evaluate_rule({"title": "Rock Song"}, rule) is True

    def test_rule_greater_than(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="play_count", operator="greater_than", value=3)
        assert engine._evaluate_rule({"play_count": 5}, rule) is True
        assert engine._evaluate_rule({"play_count": 1}, rule) is False

    def test_rule_less_than(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="rating", operator="less_than", value=4)
        assert engine._evaluate_rule({"rating": 3}, rule) is True

    def test_rule_between(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="year", operator="between", value=1980, value2=1989)
        assert engine._evaluate_rule({"year": 1985}, rule) is True
        assert engine._evaluate_rule({"year": 1970}, rule) is False

    def test_rule_in_last_string_date(self, engine):
        from datetime import datetime

        from core.smart_playlist import PlaylistRule

        recent = datetime.now().isoformat()
        rule = PlaylistRule(field="date_added", operator="in_last", value=30)
        assert engine._evaluate_rule({"date_added": recent}, rule) is True
        assert engine._evaluate_rule({"date_added": "2000-01-01"}, rule) is False

    def test_rule_in_last_bad_date(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="date_added", operator="in_last", value=30)
        assert engine._evaluate_rule({"date_added": "not-a-date"}, rule) is False

    def test_rule_in_last_non_string(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="date_added", operator="in_last", value=30)
        assert engine._evaluate_rule({"date_added": 12345}, rule) is False

    def test_rule_is_empty(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="genre", operator="is_empty", value=None)
        assert engine._evaluate_rule({"genre": None}, rule) is True
        assert engine._evaluate_rule({"genre": ""}, rule) is True
        assert engine._evaluate_rule({"genre": "Rock"}, rule) is False

    def test_rule_is_not_empty(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="genre", operator="is_not_empty", value=None)
        assert engine._evaluate_rule({"genre": None}, rule) is False
        assert engine._evaluate_rule({"genre": "Rock"}, rule) is True

    def test_rule_value_error(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="play_count", operator="greater_than", value="not_a_number")
        assert engine._evaluate_rule({"play_count": "abc"}, rule) is False

    def test_rule_unknown_operator(self, engine):
        from core.smart_playlist import PlaylistRule

        rule = PlaylistRule(field="genre", operator="unknown_op", value="x")
        assert engine._evaluate_rule({"genre": "Rock"}, rule) is False

    # --- sort ---

    def test_sort_songs_error(self, engine):
        songs = [{"title": "A"}, {"title": None}]
        result = engine._sort_songs(songs, "title", True)
        assert len(result) == 2

    # --- builtin playlists ---

    def test_get_recently_added(self, engine):
        result = engine.get_recently_added(days=365)
        assert isinstance(result, list)

    def test_get_recently_played(self, engine):
        result = engine.get_recently_played(days=365)
        assert isinstance(result, list)

    def test_get_most_played(self, engine):
        result = engine.get_most_played(limit=10)
        assert isinstance(result, list)

    def test_get_never_played(self, engine):
        result = engine.get_never_played()
        assert len(result) == 1  # Song 2 has play_count=0

    def test_get_by_genre(self, engine):
        result = engine.get_by_genre("Rock")
        assert len(result) == 1

    def test_get_by_artist(self, engine):
        result = engine.get_by_artist("Band A")
        assert len(result) == 1

    def test_get_by_decade(self, engine):
        result = engine.get_by_decade(1980)
        assert len(result) == 1

    def test_get_top_rated(self, engine):
        result = engine.get_top_rated(min_rating=4)
        assert len(result) == 2  # Songs with rating 4 and 5

    # --- _get_all_songs fallbacks ---

    def test_get_all_songs_search_fallback(self):
        from core.smart_playlist import SmartPlaylistEngine

        mock_db = Mock(spec=["search"])
        mock_db.search.return_value = [{"id": 1}]
        engine = SmartPlaylistEngine(mock_db)
        assert engine._get_all_songs() == [{"id": 1}]

    def test_get_all_songs_unknown_type(self):
        from core.smart_playlist import SmartPlaylistEngine

        mock_db = Mock(spec=[])  # No get_all_songs, no search, no execute
        engine = SmartPlaylistEngine(mock_db)
        assert engine._get_all_songs() == []

    # --- save/load JSON ---

    def test_save_to_json(self, engine, config, tmp_path):
        engine.create_playlist(config)
        filepath = str(tmp_path / "playlists.json")
        assert engine.save_to_json(filepath) is True
        assert os.path.exists(filepath)

    def test_save_to_json_error(self, engine, config):
        engine.create_playlist(config)
        assert engine.save_to_json("/nonexistent/dir/file.json") is False

    def test_load_from_json(self, engine, config, tmp_path):
        engine.create_playlist(config)
        filepath = str(tmp_path / "playlists.json")
        engine.save_to_json(filepath)

        from core.smart_playlist import SmartPlaylistEngine

        engine2 = SmartPlaylistEngine(None)
        assert engine2.load_from_json(filepath) is True
        assert "Test Playlist" in engine2.list_playlists()

    def test_load_from_json_not_found(self, engine):
        assert engine.load_from_json("/nonexistent.json") is False

    def test_load_from_json_corrupt(self, engine, tmp_path):
        filepath = str(tmp_path / "bad.json")
        with open(filepath, "w") as f:
            f.write("not json")
        assert engine.load_from_json(filepath) is False


# ==========================================
# LibraryOrganizer Tests
# ==========================================


class TestLibraryOrganizerPhase2:
    """Tests for LibraryOrganizer — organize, build_path, rollback."""

    @pytest.fixture
    def organizer(self):
        from core.library_organizer import LibraryOrganizer

        return LibraryOrganizer(MagicMock())

    def test_build_path_basic(self, organizer):
        song = {
            "artist": "Beatles",
            "album": "Abbey Road",
            "title": "Come Together",
            "year": 1969,
            "genre": "Rock",
            "track": 1,
        }
        path = organizer.build_path("/music", "{artist}/{album}/{title}.mp3", song)
        assert "Beatles" in str(path)
        assert "Abbey Road" in str(path)

    def test_build_path_missing_key(self, organizer):
        song = {"artist": "Beatles", "title": "Song"}
        path = organizer.build_path("/music", "{artist}/{missing_key}/{title}.mp3", song)
        # Falls back to simple template
        assert "Beatles" in str(path)

    def test_sanitize_path_empty(self, organizer):
        assert organizer._sanitize_path("") == "Unknown"

    def test_sanitize_path_special_chars(self, organizer):
        result = organizer._sanitize_path('Bad:File*Name?"<>|')
        assert ":" not in result
        assert "*" not in result

    def test_sanitize_path_dots_spaces(self, organizer):
        result = organizer._sanitize_path("...name...")
        assert not result.startswith(".")

    def test_organize_dry_run(self, organizer):
        songs = [
            {"id": 1, "file_path": "/old/song.mp3", "artist": "A", "title": "Song"},
        ]
        result = organizer.organize("/music", "{artist}/{title}.mp3", songs, dry_run=True)
        assert result["success"] == 1
        assert len(result["preview"]) == 1

    def test_organize_move_success(self, organizer, tmp_path):
        # Create source file
        src = tmp_path / "old" / "song.mp3"
        src.parent.mkdir(parents=True)
        src.write_text("audio")

        songs = [{"id": 1, "file_path": str(src), "artist": "A", "title": "Song"}]
        result = organizer.organize(str(tmp_path / "new"), "{artist}/{title}.mp3", songs, move=True)
        assert result["success"] == 1

    def test_organize_copy_success(self, organizer, tmp_path):
        src = tmp_path / "old" / "song.mp3"
        src.parent.mkdir(parents=True)
        src.write_text("audio")

        songs = [{"id": 1, "file_path": str(src), "artist": "A", "title": "Song"}]
        result = organizer.organize(str(tmp_path / "new"), "{artist}/{title}.mp3", songs, move=False)
        assert result["success"] == 1

    def test_organize_file_not_found(self, organizer):
        songs = [{"id": 1, "file_path": "/nonexistent/song.mp3", "artist": "A", "title": "Song"}]
        result = organizer.organize("/music", "{artist}/{title}.mp3", songs, move=True)
        assert result["failed"] == 1

    def test_organize_exception(self, organizer):
        songs = [{"id": 1, "file_path": "/bad.mp3"}]  # Missing artist/title keys still works with defaults
        with patch("os.path.exists", side_effect=OSError("perm denied")):
            result = organizer.organize("/music", "{artist}/{title}.mp3", songs)
        assert result["failed"] == 1

    def test_organize_name_conflict(self, organizer, tmp_path):
        src = tmp_path / "song.mp3"
        src.write_text("audio")
        target_dir = tmp_path / "new" / "A"
        target_dir.mkdir(parents=True)
        (target_dir / "Song.mp3").write_text("existing")

        songs = [{"id": 1, "file_path": str(src), "artist": "A", "title": "Song"}]
        result = organizer.organize(str(tmp_path / "new"), "{artist}/{title}.mp3", songs, move=True)
        assert result["success"] == 1

    def test_rollback_no_history(self, organizer):
        result = organizer.rollback()
        assert result["success"] == 0
        assert len(result["errors"]) == 1

    def test_rollback_success(self, organizer, tmp_path):
        new_file = tmp_path / "new" / "song.mp3"
        new_file.parent.mkdir(parents=True)
        new_file.write_text("audio")
        old_dir = tmp_path / "old"
        old_dir.mkdir()

        organizer._history = [{"old": str(old_dir / "song.mp3"), "new": str(new_file), "song_id": 1}]
        result = organizer.rollback()
        assert result["success"] == 1

    def test_rollback_file_not_found(self, organizer):
        organizer._history = [{"old": "/old/song.mp3", "new": "/nonexistent/song.mp3", "song_id": 1}]
        result = organizer.rollback()
        assert result["failed"] == 1

    def test_move_file_error(self, organizer):
        with patch("shutil.move", side_effect=OSError("fail")):
            assert organizer._move_file("/src", "/dst") is False

    def test_copy_file_error(self, organizer):
        with patch("shutil.copy2", side_effect=OSError("fail")):
            assert organizer._copy_file("/src", "/dst") is False

    def test_update_database_path_error(self, organizer):
        organizer.db.update_song_path.side_effect = sqlite3.Error("fail")
        with pytest.raises(sqlite3.Error):
            organizer._update_database_path(1, "/new/path.mp3")


# ==========================================
# PlaylistManager Tests
# ==========================================


class TestPlaylistManagerPhase2:
    """Tests for PlaylistManager — uncovered error paths and methods."""

    @pytest.fixture
    def manager(self):
        from core.playlist_manager import PlaylistManager

        return PlaylistManager(MagicMock())

    def test_create_playlist(self, manager):
        manager.db_manager.execute_query.return_value = 42
        assert manager.create_playlist("My Playlist", "Desc") == 42

    def test_create_playlist_error(self, manager):
        manager.db_manager.execute_query.side_effect = sqlite3.Error("fail")
        with pytest.raises(sqlite3.Error):
            manager.create_playlist("Bad")

    def test_delete_playlist_success(self, manager):
        assert manager.delete_playlist(1) is True

    def test_delete_playlist_error(self, manager):
        manager.db_manager.execute_query.side_effect = sqlite3.Error("fail")
        assert manager.delete_playlist(1) is False

    def test_rename_playlist_success(self, manager):
        assert manager.rename_playlist(1, "New Name") is True

    def test_rename_playlist_error(self, manager):
        manager.db_manager.execute_query.side_effect = sqlite3.Error("fail")
        assert manager.rename_playlist(1, "Bad") is False

    def test_add_song_auto_position(self, manager):
        manager.db_manager.fetch_one.return_value = {"max_pos": 5}
        assert manager.add_song(1, 100) is True

    def test_add_song_null_position(self, manager):
        manager.db_manager.fetch_one.return_value = {"max_pos": None}
        assert manager.add_song(1, 100) is True

    def test_add_song_explicit_position(self, manager):
        assert manager.add_song(1, 100, position=3) is True

    def test_add_song_error(self, manager):
        manager.db_manager.fetch_one.side_effect = sqlite3.Error("fail")
        assert manager.add_song(1, 100) is False

    def test_remove_song_success(self, manager):
        manager.db_manager.fetch_all.return_value = [{"id": 1}, {"id": 2}]
        assert manager.remove_song(1, 100) is True

    def test_remove_song_error(self, manager):
        manager.db_manager.execute_query.side_effect = sqlite3.Error("fail")
        assert manager.remove_song(1, 100) is False

    def test_reorder_songs_success(self, manager):
        manager.db_manager.fetch_all.return_value = [
            {"id": 10, "song_id": 1, "position": 0},
            {"id": 11, "song_id": 2, "position": 1},
            {"id": 12, "song_id": 3, "position": 2},
        ]
        assert manager.reorder_songs(1, 0, 2) is True

    def test_reorder_songs_invalid_index(self, manager):
        manager.db_manager.fetch_all.return_value = [{"id": 1, "song_id": 1, "position": 0}]
        assert manager.reorder_songs(1, -1, 0) is False
        assert manager.reorder_songs(1, 0, 5) is False

    def test_reorder_songs_error(self, manager):
        manager.db_manager.fetch_all.side_effect = sqlite3.Error("fail")
        assert manager.reorder_songs(1, 0, 1) is False

    def test_get_playlists_success(self, manager):
        manager.db_manager.fetch_all.return_value = [{"id": 1, "name": "Favs"}]
        result = manager.get_playlists()
        assert len(result) == 1

    def test_get_playlists_error(self, manager):
        manager.db_manager.fetch_all.side_effect = sqlite3.Error("fail")
        assert manager.get_playlists() == []

    def test_get_playlist_songs_success(self, manager):
        manager.db_manager.fetch_all.return_value = [{"id": 1, "title": "Song"}]
        result = manager.get_playlist_songs(1)
        assert len(result) == 1

    def test_get_playlist_songs_error(self, manager):
        manager.db_manager.fetch_all.side_effect = sqlite3.Error("fail")
        assert manager.get_playlist_songs(1) == []

    def test_save_playlist(self, manager, tmp_path):
        manager.db_manager.fetch_all.return_value = [
            {
                "id": 1,
                "title": "Song 1",
                "artist": "Artist",
                "duration": 180,
                "file_path": "/music/song1.mp3",
                "position": 0,
            },
        ]
        filepath = str(tmp_path / "playlist.m3u8")
        assert manager.save_playlist(1, filepath) is True
        content = open(filepath).read()
        assert "#EXTM3U" in content
        assert "Artist" in content

    def test_save_playlist_error(self, manager):
        manager.db_manager.fetch_all.return_value = []
        assert manager.save_playlist(1, "/nonexistent/dir/p.m3u8") is False

    def test_load_playlist(self, manager, tmp_path):
        m3u = tmp_path / "test.m3u8"
        m3u.write_text("#EXTM3U\n#EXTINF:180,Artist - Song\n/music/song.mp3\n")
        manager.db_manager.execute_query.return_value = 10
        # Order: create_playlist calls execute_query (returns 10),
        # then fetch_one for SELECT id (song lookup), then add_song with explicit position (no max_pos query)
        manager.db_manager.fetch_one.side_effect = [
            {"id": 1},  # found in DB by file_path
        ]
        result = manager.load_playlist(str(m3u))
        assert result == 10

    def test_load_playlist_not_found(self, manager):
        assert manager.load_playlist("/nonexistent.m3u8") is None

    def test_load_playlist_auto_name(self, manager, tmp_path):
        m3u = tmp_path / "my_playlist.m3u8"
        m3u.write_text("#EXTM3U\n")
        manager.db_manager.execute_query.return_value = 5
        result = manager.load_playlist(str(m3u))
        assert result == 5

    def test_load_playlist_song_not_in_db(self, manager, tmp_path):
        m3u = tmp_path / "test.m3u8"
        m3u.write_text("#EXTM3U\n/unknown_song.mp3\n")
        manager.db_manager.execute_query.return_value = 10
        manager.db_manager.fetch_one.return_value = None  # Not found
        result = manager.load_playlist(str(m3u))
        assert result == 10

    def test_load_playlist_error(self, manager, tmp_path):
        m3u = tmp_path / "test.m3u8"
        m3u.write_text("#EXTM3U\n/song.mp3\n")
        manager.db_manager.execute_query.side_effect = sqlite3.Error("fail")
        assert manager.load_playlist(str(m3u)) is None

    def test_duplicate_playlist_success(self, manager):
        manager.db_manager.fetch_one.return_value = {"name": "Original", "description": "Desc"}
        manager.db_manager.execute_query.return_value = 20
        manager.db_manager.fetch_all.return_value = [
            {
                "id": 1,
                "title": "Song",
                "position": 0,
                "artist": "A",
                "album": "B",
                "duration": 180,
                "file_path": "/a.mp3",
            },
        ]
        result = manager.duplicate_playlist(1)
        assert result == 20

    def test_duplicate_playlist_not_found(self, manager):
        manager.db_manager.fetch_one.return_value = None
        assert manager.duplicate_playlist(999) is None

    def test_duplicate_playlist_error(self, manager):
        manager.db_manager.fetch_one.side_effect = sqlite3.Error("fail")
        assert manager.duplicate_playlist(1) is None

    def test_duplicate_custom_name(self, manager):
        manager.db_manager.fetch_one.return_value = {"name": "Orig", "description": ""}
        manager.db_manager.execute_query.return_value = 30
        manager.db_manager.fetch_all.return_value = []
        result = manager.duplicate_playlist(1, new_name="My Copy")
        assert result == 30

    def test_get_playlist_stats(self, manager):
        manager.db_manager.fetch_one.return_value = {"song_count": 10, "total_duration": 3600}
        stats = manager.get_playlist_stats(1)
        assert stats["song_count"] == 10

    def test_get_playlist_stats_error(self, manager):
        manager.db_manager.fetch_one.side_effect = sqlite3.Error("fail")
        stats = manager.get_playlist_stats(1)
        assert stats == {"song_count": 0, "total_duration": 0}

    def test_reorder_playlist_songs(self, manager):
        manager.db_manager.fetch_all.return_value = [{"id": 10}, {"id": 11}]
        manager._reorder_playlist_songs(1)
        assert manager.db_manager.execute_query.call_count == 2

    def test_reorder_playlist_songs_error(self, manager):
        manager.db_manager.fetch_all.side_effect = sqlite3.Error("fail")
        manager._reorder_playlist_songs(1)  # Should not raise


# ==========================================
# DuplicateDetector Tests
# ==========================================


class TestDuplicateDetectorPhase2:
    """Tests for DuplicateDetector — detect methods + similarity calc."""

    @pytest.fixture
    def detector(self):
        from core.duplicate_detector import DuplicateDetector

        with patch("core.duplicate_detector.FpcalcChecker") as MockFpc:
            MockFpc.return_value.is_available.return_value = False
            det = DuplicateDetector(MagicMock(), similarity_threshold=0.70)
        return det

    def test_scan_library_metadata(self, detector):
        detector.db.get_all_songs.return_value = [
            {"id": 1, "title": "Song A", "artist": "Artist", "duration": 180, "bitrate": 320},
            {"id": 2, "title": "Song A", "artist": "Artist", "duration": 181, "bitrate": 256},
        ]
        result = detector.scan_library("metadata")
        assert len(result) == 1
        assert result[0]["method"] == "metadata"

    def test_scan_library_unknown_method(self, detector):
        assert detector.scan_library("unknown") == []

    def test_detect_by_metadata_empty(self, detector):
        detector.db.get_all_songs.return_value = []
        assert detector.detect_by_metadata() == []

    def test_detect_by_metadata_single(self, detector):
        detector.db.get_all_songs.return_value = [{"id": 1, "title": "Only Song"}]
        assert detector.detect_by_metadata() == []

    def test_detect_by_metadata_no_duplicates(self, detector):
        detector.db.get_all_songs.return_value = [
            {"id": 1, "title": "Completely Different", "artist": "X", "duration": 100, "bitrate": 320},
            {"id": 2, "title": "Another Unique", "artist": "Y", "duration": 300, "bitrate": 320},
        ]
        result = detector.detect_by_metadata()
        assert len(result) == 0

    def test_detect_by_filesize(self, detector, tmp_path):
        f1 = tmp_path / "a.mp3"
        f2 = tmp_path / "b.mp3"
        f1.write_bytes(b"x" * 1000)
        f2.write_bytes(b"x" * 1000)

        detector.db.get_all_songs.return_value = [
            {"id": 1, "file_path": str(f1), "bitrate": 320},
            {"id": 2, "file_path": str(f2), "bitrate": 256},
        ]
        result = detector.scan_library("filesize")
        assert len(result) == 1
        assert result[0]["confidence"] == 0.70

    def test_detect_by_filesize_empty(self, detector):
        detector.db.get_all_songs.return_value = []
        assert detector.detect_by_filesize() == []

    def test_detect_by_filesize_missing_file(self, detector):
        detector.db.get_all_songs.return_value = [
            {"id": 1, "file_path": "/nonexistent.mp3", "bitrate": 320},
        ]
        result = detector.detect_by_filesize()
        assert len(result) == 0

    def test_detect_by_fingerprint_empty(self, detector):
        detector.db.get_all_songs.return_value = []
        assert detector.detect_by_fingerprint() == []

    def test_detect_by_fingerprint_no_fpcalc(self, detector):
        detector.db.get_all_songs.return_value = [
            {"id": 1, "file_path": "/a.mp3", "bitrate": 320},
        ]
        result = detector.detect_by_fingerprint()
        assert len(result) == 0

    def test_calculate_similarity_identical(self, detector):
        song = {"title": "Same Song", "artist": "Same Artist", "duration": 180}
        sim = detector._calculate_metadata_similarity(song, song)
        assert sim > 0.95

    def test_calculate_similarity_duration_medium(self, detector):
        s1 = {"title": "Song", "artist": "A", "duration": 180}
        s2 = {"title": "Song", "artist": "A", "duration": 187}  # 7s diff
        sim = detector._calculate_metadata_similarity(s1, s2)
        assert 0.5 < sim < 1.0

    def test_calculate_similarity_duration_far(self, detector):
        s1 = {"title": "Song", "artist": "A", "duration": 180}
        s2 = {"title": "Song", "artist": "A", "duration": 300}  # >10s diff
        sim = detector._calculate_metadata_similarity(s1, s2)
        assert sim < 1.0

    def test_sort_by_quality(self, detector):
        songs = [{"bitrate": 128}, {"bitrate": 320}, {"bitrate": 256}]
        result = detector._sort_by_quality(songs)
        assert result[0]["bitrate"] == 320


# ==========================================
# MetadataTagger Tests
# ==========================================


class TestMetadataTaggerPhase2:
    """Tests for MetadataTagger — lookup_and_tag and embed_album_art."""

    @pytest.fixture
    def tagger(self):
        from core.metadata_tagger import MetadataTagger

        with patch("core.metadata_tagger.MetadataAutocompleter"):
            t = MetadataTagger()
        return t

    def test_tag_file_success(self, tagger):
        mock_mp3 = MagicMock()
        mock_mp3.tags = MagicMock()
        with patch("core.metadata_tagger.MP3", return_value=mock_mp3):
            result = tagger.tag_file(
                "/test.mp3",
                {
                    "title": "Song",
                    "artist": "Artist",
                    "album": "Album",
                    "year": 2024,
                    "genre": "Rock",
                },
            )
        assert result is True
        mock_mp3.save.assert_called_once()

    def test_tag_file_not_found(self, tagger):
        with patch("core.metadata_tagger.MP3", side_effect=FileNotFoundError):
            assert tagger.tag_file("/missing.mp3", {"title": "X"}) is False

    def test_tag_file_mutagen_error(self, tagger):
        from mutagen import MutagenError

        with patch("core.metadata_tagger.MP3", side_effect=MutagenError("corrupt")):
            assert tagger.tag_file("/bad.mp3", {"title": "X"}) is False

    def test_lookup_and_tag_no_title(self, tagger):
        assert tagger.lookup_and_tag("/test.mp3", {}) is False

    def test_lookup_and_tag_no_matches(self, tagger):
        tagger.autocompleter.autocomplete_single.return_value = []
        with patch.object(tagger, "tag_file", return_value=True):
            result = tagger.lookup_and_tag("/test.mp3", {"title": "Unknown Song"})
        assert result is True

    def test_lookup_and_tag_low_confidence(self, tagger):
        tagger.autocompleter.autocomplete_single.return_value = [
            {"title": "Match", "artist": "A", "confidence": 50},
        ]
        with patch.object(tagger, "tag_file", return_value=True):
            result = tagger.lookup_and_tag("/test.mp3", {"title": "Song"}, min_confidence=80)
        assert result is True

    def test_lookup_and_tag_high_confidence(self, tagger):
        tagger.autocompleter.autocomplete_single.return_value = [
            {"title": "Perfect Match", "artist": "Artist", "confidence": 95},
        ]
        with patch.object(tagger, "tag_file", return_value=True):
            result = tagger.lookup_and_tag("/test.mp3", {"title": "Song"})
        assert result is True

    def test_lookup_and_tag_error(self, tagger):
        tagger.autocompleter.autocomplete_single.side_effect = ValueError("fail")
        assert tagger.lookup_and_tag("/test.mp3", {"title": "Song"}) is False

    def test_embed_album_art_success(self, tagger, tmp_path):
        img = tmp_path / "cover.jpg"
        img.write_bytes(b"\xff\xd8\xff\xe0")  # JPEG header

        mock_mp3 = MagicMock()
        mock_mp3.tags = MagicMock()
        with patch("core.metadata_tagger.MP3", return_value=mock_mp3):
            result = tagger.embed_album_art("/test.mp3", str(img))
        assert result is True

    def test_embed_album_art_png(self, tagger, tmp_path):
        img = tmp_path / "cover.png"
        img.write_bytes(b"\x89PNG")

        mock_mp3 = MagicMock()
        mock_mp3.tags = MagicMock()
        with patch("core.metadata_tagger.MP3", return_value=mock_mp3):
            result = tagger.embed_album_art("/test.mp3", str(img))
        assert result is True

    def test_embed_album_art_not_found(self, tagger):
        with patch("core.metadata_tagger.MP3", side_effect=FileNotFoundError):
            assert tagger.embed_album_art("/missing.mp3", "/missing.jpg") is False

    def test_embed_album_art_error(self, tagger):
        from mutagen import MutagenError

        with patch("core.metadata_tagger.MP3", side_effect=MutagenError("err")):
            assert tagger.embed_album_art("/test.mp3", "/img.jpg") is False


# ==========================================
# DownloadQueue Tests (QObject-based)
# ==========================================


class TestDownloadQueuePhase2:
    """Tests for DownloadQueue — queue operations via QObject bypass."""

    @pytest.fixture
    def queue(self):
        import threading

        from core.download_queue import DownloadQueue

        q = DownloadQueue.__new__(DownloadQueue)
        q._items = {}
        q._workers = {}
        q.max_concurrent = 2
        q.max_retries = 3
        q.db_manager = None
        q.config_manager = None
        q._running = False
        q._lock = threading.RLock()
        q._allowed_domains = ["youtube.com", "youtu.be", "music.youtube.com"]
        q.on_complete = None
        # Mock signals to avoid QObject issues
        q.item_added = MagicMock()
        q.item_started = MagicMock()
        q.item_progress = MagicMock()
        q.item_completed = MagicMock()
        q.item_failed = MagicMock()
        q.queue_completed = MagicMock()
        return q

    def test_init(self):
        from core.download_queue import DownloadQueue

        with patch("core.download_queue.QObject.__init__"):
            q = DownloadQueue(max_concurrent=3)
        assert q.max_concurrent == 3

    def test_add_item(self, queue):
        item_id = queue.add(
            video_url="https://www.youtube.com/watch?v=abc123",
            metadata={"title": "Test"},
        )
        assert item_id is not None
        assert item_id in queue._items
        assert queue._items[item_id]["status"] == "pending"
        queue.item_added.emit.assert_called_once()

    def test_add_invalid_url(self, queue):
        with pytest.raises(ValueError, match="Invalid video URL"):
            queue.add(video_url="", metadata={})

    def test_get_all_items(self, queue):
        queue._items = {"a": {"id": "a", "status": "pending"}}
        result = queue.get_all_items()
        assert "a" in result

    def test_get_item(self, queue):
        queue._items = {"a": {"id": "a", "status": "pending"}}
        assert queue.get_item("a") is not None
        assert queue.get_item("nonexistent") is None

    def test_cancel_item(self, queue):
        queue._items = {"a": {"id": "a", "status": "pending"}}
        result = queue.cancel("a")
        assert result is True
        assert queue._items["a"]["status"] == "canceled"

    def test_cancel_nonexistent(self, queue):
        result = queue.cancel("nonexistent")
        assert result is False

    def test_clear_completed(self, queue):
        queue._items = {
            "a": {"id": "a", "status": "completed"},
            "b": {"id": "b", "status": "pending"},
        }
        count = queue.clear_completed()
        assert count == 1
        assert "a" not in queue._items
        assert "b" in queue._items

    def test_clear_all(self, queue):
        queue._items = {
            "a": {"id": "a", "status": "pending"},
            "b": {"id": "b", "status": "completed"},
        }
        count = queue.clear_all()
        assert count == 2
        assert len(queue._items) == 0

    def test_pause_resume(self, queue):
        queue._items = {"a": {"id": "a", "status": "pending"}}
        assert queue.pause("a") is True
        assert queue._items["a"]["status"] == "paused"
        assert queue.resume("a") is True
        assert queue._items["a"]["status"] == "pending"

    def test_pause_nonexistent(self, queue):
        assert queue.pause("nonexistent") is False

    def test_resume_nonexistent(self, queue):
        assert queue.resume("nonexistent") is False

    def test_retry(self, queue):
        queue._items = {"a": {"id": "a", "status": "failed", "error": "net", "progress": 50}}
        assert queue.retry("a") is True
        assert queue._items["a"]["status"] == "pending"
        assert queue._items["a"]["progress"] == 0
        assert queue._items["a"]["error"] is None

    def test_retry_not_failed(self, queue):
        queue._items = {"a": {"id": "a", "status": "pending", "error": None, "progress": 0}}
        assert queue.retry("a") is False

    def test_start_stop(self, queue):
        queue._process_next = MagicMock()
        queue.start()
        assert queue._running is True
        queue.stop()
        assert queue._running is False

    def test_add_auto_start_when_running(self, queue):
        """Test that add() calls _process_next when queue is running."""
        queue._running = True
        queue._process_next = MagicMock()
        queue.add(
            video_url="https://www.youtube.com/watch?v=test",
            metadata={"title": "Auto"},
        )
        queue._process_next.assert_called_once()

    def test_mark_failed_with_retry(self, queue):
        """Test _mark_failed auto-retries when retry_count < max_retries."""
        queue._items = {
            "a": {"id": "a", "status": "downloading", "retry_count": 0, "error": None, "progress": 50},
        }
        queue._process_next = MagicMock()
        queue._mark_failed("a", "Connection error")
        assert queue._items["a"]["status"] == "pending"
        assert queue._items["a"]["retry_count"] == 1
        assert queue._items["a"]["progress"] == 0

    def test_mark_failed_max_retries(self, queue):
        """Test _mark_failed marks as failed when max retries reached."""
        queue._items = {
            "a": {"id": "a", "status": "downloading", "retry_count": 2, "error": None, "progress": 50},
        }
        queue._process_next = MagicMock()
        queue._mark_failed("a", "Final error")
        assert queue._items["a"]["status"] == "failed"
        queue.item_failed.emit.assert_called_once_with("a", "Final error")

    def test_normalize_path_for_platform(self):
        """Test path normalization (static method)."""
        from core.download_queue import DownloadQueue

        # Non-Windows path should pass through
        with patch("core.download_queue.os.name", "nt"):
            result = DownloadQueue._normalize_path_for_platform("C:\\Users\\test")
            assert str(result) == "C:\\Users\\test"

    def test_find_downloaded_file_exists(self, queue, tmp_path):
        """Test _find_downloaded_file when file exists."""
        test_file = tmp_path / "song.mp3"
        test_file.write_bytes(b"fake mp3")
        result = queue._find_downloaded_file(str(test_file))
        assert result is not None
        assert result.name == "song.mp3"

    def test_find_downloaded_file_not_found(self, queue, tmp_path):
        """Test _find_downloaded_file when file doesn't exist."""
        result = queue._find_downloaded_file(str(tmp_path / "nonexistent.mp3"))
        assert result is None

    def test_process_next_max_concurrent(self, queue):
        """Test _process_next stops when max concurrent reached."""
        queue._items = {
            "a": {"id": "a", "status": "downloading"},
            "b": {"id": "b", "status": "downloading"},
            "c": {"id": "c", "status": "pending"},
        }
        queue.max_concurrent = 2
        queue._process_next()
        # Item c should still be pending (max concurrent reached)
        assert queue._items["c"]["status"] == "pending"

    def test_on_worker_progress(self, queue):
        """Test _on_worker_progress updates and emits."""
        queue._items = {"a": {"id": "a", "status": "downloading", "progress": 0}}
        queue._on_worker_progress("a", 75)
        assert queue._items["a"]["progress"] == 75
        queue.item_progress.emit.assert_called_once_with("a", 75)

    def test_is_running(self, queue):
        assert queue.is_running() is False
        queue._running = True
        assert queue.is_running() is True

    def test_get_active_downloads(self, queue):
        queue._items = {
            "a": {"id": "a", "status": "downloading"},
            "b": {"id": "b", "status": "pending"},
        }
        active = queue.get_active_downloads()
        assert len(active) == 1
        assert active[0]["id"] == "a"

    def test_update_progress(self, queue):
        queue._items = {"a": {"id": "a", "status": "downloading", "progress": 0}}
        queue.update_progress("a", 50)
        assert queue._items["a"]["progress"] == 50

    def test_mark_completed(self, queue):
        queue._items = {
            "a": {
                "id": "a",
                "status": "downloading",
                "progress": 50,
                "metadata": {"title": "Test"},
            }
        }
        queue.mark_completed("a", {"output_path": "/test.mp3"})
        assert queue._items["a"]["status"] == "completed"
        assert queue._items["a"]["progress"] == 100
        queue.item_completed.emit.assert_called_once()

    def test_save_load(self, queue, tmp_path):
        queue._items = {
            "a": {"id": "a", "status": "pending", "progress": 0},
        }
        filepath = str(tmp_path / "queue.json")
        queue.save(filepath)
        queue._items.clear()
        queue.load(filepath)
        assert "a" in queue._items


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
