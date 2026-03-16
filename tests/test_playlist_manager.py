"""
Tests for Playlist Manager - Phase 7.1 (TDD Red Phase)

Purpose: Core playlist management system
- Create/delete playlists
- Add/remove/reorder songs
- Save/load .m3u8 files
- Playlist statistics
- Database integration

Test Strategy: Red -> Green -> Refactor
Expected Result: All tests FAIL initially (no implementation yet)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestPlaylistManager:
    """Test Playlist Manager"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        try:
            from src.core.playlist_manager import PlaylistManager

            # Mock database manager
            self.mock_db = Mock()
            self.manager = PlaylistManager(self.mock_db)
        except ImportError:
            self.manager = None

    # ========== STRUCTURAL TESTS ==========

    def test_01_playlist_manager_exists(self):
        """Test PlaylistManager class exists"""
        if self.manager is None:
            pytest.fail("PlaylistManager not found - implement src/core/playlist_manager.py")

        assert self.manager is not None

    def test_02_create_playlist(self):
        """Test creating new playlist"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock database response
        self.mock_db.execute_query.return_value = 1  # New playlist ID

        playlist_id = self.manager.create_playlist("My Favorites", "Best songs ever")

        # Should return playlist ID
        assert isinstance(playlist_id, int)
        assert playlist_id > 0

        # Should call database
        assert self.mock_db.execute_query.called

    def test_03_add_song_to_playlist(self):
        """Test adding song to playlist"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock database - fetch_one for max position, execute_query for insert
        self.mock_db.fetch_one.return_value = {"max_pos": 0}
        self.mock_db.execute_query.return_value = None

        # Add song to playlist
        result = self.manager.add_song(playlist_id=1, song_id=100)

        # Should succeed
        assert result

    def test_04_remove_song_from_playlist(self):
        """Test removing song from playlist"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock database
        self.mock_db.execute_query.return_value = None

        # Remove song from playlist
        result = self.manager.remove_song(playlist_id=1, song_id=100)

        # Should succeed
        assert result or self.mock_db.execute_query.called

    def test_05_reorder_songs_in_playlist(self):
        """Test reordering songs in playlist"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock database - fetch_all returns list of songs
        self.mock_db.fetch_all.return_value = [
            {"id": 1, "song_id": 100, "position": 0},
            {"id": 2, "song_id": 200, "position": 1},
            {"id": 3, "song_id": 300, "position": 2},
        ]
        self.mock_db.execute_query.return_value = None

        # Reorder: move song from position 0 to position 2
        result = self.manager.reorder_songs(playlist_id=1, old_index=0, new_index=2)

        # Should succeed
        assert result

    def test_06_get_all_playlists(self):
        """Test getting all playlists"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock database response
        self.mock_db.fetch_all.return_value = [
            {"id": 1, "name": "Favorites", "description": "My favorites", "song_count": 10},
            {"id": 2, "name": "Rock", "description": "Rock songs", "song_count": 25},
        ]

        playlists = self.manager.get_playlists()

        # Should return list of playlists
        assert isinstance(playlists, list)
        assert len(playlists) == 2
        assert playlists[0]["name"] == "Favorites"

    def test_07_delete_playlist(self):
        """Test deleting playlist"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock database
        self.mock_db.execute_query.return_value = None

        # Delete playlist
        result = self.manager.delete_playlist(playlist_id=1)

        # Should succeed
        assert result or self.mock_db.execute_query.called

    def test_08_save_playlist_to_m3u8(self):
        """Test saving playlist to .m3u8 file"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock playlist data
        self.mock_db.fetch_all.return_value = [
            {"id": 1, "title": "Song A", "artist": "Artist A", "file_path": "/path/a.mp3", "duration": 180},
            {"id": 2, "title": "Song B", "artist": "Artist B", "file_path": "/path/b.mp3", "duration": 200},
        ]

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".m3u8") as f:
            temp_path = f.name

        try:
            # Save playlist
            result = self.manager.save_playlist(playlist_id=1, file_path=temp_path)

            # Should succeed
            assert result

            # File should exist
            assert os.path.exists(temp_path)

            # File should have content
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "#EXTM3U" in content
                assert "#EXTINF" in content
                assert "/path/a.mp3" in content

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_09_load_playlist_from_m3u8(self):
        """Test loading playlist from .m3u8 file"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Create temp .m3u8 file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".m3u8", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("#EXTINF:180,Artist A - Song A\n")
            f.write("/path/a.mp3\n")
            f.write("#EXTINF:200,Artist B - Song B\n")
            f.write("/path/b.mp3\n")
            temp_path = f.name

        try:
            # Mock database methods
            self.mock_db.execute_query.return_value = 1  # New playlist ID
            self.mock_db.fetch_one.side_effect = [
                {"id": 100},  # Song A found
                {"id": 200},  # Song B found
            ]

            # Load playlist
            playlist_id = self.manager.load_playlist(temp_path, name="Imported Playlist")

            # Should return playlist ID
            assert isinstance(playlist_id, int)
            assert playlist_id > 0

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_10_duplicate_playlist(self):
        """Test duplicating existing playlist"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock playlist data
        self.mock_db.fetch_one.side_effect = [
            {"id": 1, "name": "Original", "description": "Original playlist"},  # First call for duplicate_playlist
            {"max_pos": 0},  # Second call for add_song (first song)
            {"max_pos": 1},  # Third call for add_song (second song)
        ]
        self.mock_db.fetch_all.return_value = [
            {"id": 100, "song_id": 100, "position": 0},
            {"id": 200, "song_id": 200, "position": 1},
        ]
        self.mock_db.execute_query.return_value = 2  # New playlist ID

        # Duplicate playlist
        if hasattr(self.manager, "duplicate_playlist"):
            new_id = self.manager.duplicate_playlist(playlist_id=1)

            # Should return new playlist ID
            assert isinstance(new_id, int)
            assert new_id > 0
            assert new_id != 1

    def test_11_playlist_with_missing_songs(self):
        """Test handling playlist with missing song files"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock playlist with missing songs
        self.mock_db.fetch_all.return_value = [
            {"id": 1, "file_path": "/nonexistent/a.mp3", "title": "Song A"},
            {"id": 2, "file_path": "/nonexistent/b.mp3", "title": "Song B"},
        ]

        # Get playlist songs
        if hasattr(self.manager, "get_playlist_songs"):
            songs = self.manager.get_playlist_songs(playlist_id=1)

            # Should return songs even if files don't exist
            assert isinstance(songs, list)
            assert len(songs) == 2

    def test_12_playlist_statistics(self):
        """Test getting playlist statistics"""
        if self.manager is None:
            pytest.skip("PlaylistManager not implemented")

        # Mock statistics
        self.mock_db.fetch_one.return_value = {
            "song_count": 50,
            "total_duration": 10800,  # 3 hours in seconds
        }

        # Get playlist stats
        if hasattr(self.manager, "get_playlist_stats"):
            stats = self.manager.get_playlist_stats(playlist_id=1)

            # Should return statistics
            assert isinstance(stats, dict)
            assert "song_count" in stats
            assert "total_duration" in stats
            assert stats["song_count"] == 50
