"""
Unit tests for src/api/ module — mock-based, no network required.

Covers uncovered paths in:
- spotify_search.py: parse edge cases, error handling, clear_cache, get_track_details
- youtube_search.py: parse edge cases, error handling, clear_cache, get_video_metadata
- chords_client.py: _save_to_db, transpose ValueError, analyze error paths
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402


# ---------------------------------------------------------------------------
# SpotifySearcher unit tests (mock-based, no real API calls)
# ---------------------------------------------------------------------------
class TestSpotifyParseEdgeCases:
    """Test Spotify parse methods with edge-case data"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create SpotifySearcher with mocked spotipy"""
        with patch("api.spotify_search.SpotifyClientCredentials"), patch("api.spotify_search.spotipy.Spotify"):
            from api.spotify_search import SpotifySearcher

            self.searcher = SpotifySearcher("fake_id", "fake_secret")

    def test_parse_tracks_missing_key(self):
        """_parse_tracks handles items with missing keys gracefully"""
        raw = {
            "tracks": {
                "items": [
                    {  # Missing "artists" key entirely
                        "id": "t1",
                        "name": "Song",
                        "album": {"name": "Album"},
                        "duration_ms": 200000,
                    },
                    {  # Valid item
                        "id": "t2",
                        "name": "Good Song",
                        "artists": [{"name": "Artist"}],
                        "album": {"name": "Album2"},
                        "duration_ms": 180000,
                    },
                ]
            }
        }
        result = self.searcher._parse_tracks(raw)
        # First item should be skipped (KeyError on artists[0]["name"]),
        # second should succeed
        assert len(result) >= 1
        assert result[-1]["title"] == "Good Song"

    def test_parse_tracks_empty_response(self):
        """_parse_tracks returns empty list for missing 'tracks' key"""
        result = self.searcher._parse_tracks({})
        assert result == []

    def test_parse_albums_missing_key(self):
        """_parse_albums handles items with missing keys"""
        raw = {
            "albums": {
                "items": [
                    {  # Missing "id" key
                        "name": "Album",
                        "artists": [{"name": "Artist"}],
                    }
                ]
            }
        }
        result = self.searcher._parse_albums(raw)
        # Should skip item with KeyError
        assert result == []

    def test_parse_albums_empty_response(self):
        """_parse_albums returns empty list for missing 'albums' key"""
        result = self.searcher._parse_albums({})
        assert result == []

    def test_parse_artists_missing_key(self):
        """_parse_artists handles items with missing keys"""
        raw = {
            "artists": {
                "items": [
                    {  # Missing "id" key
                        "name": "Artist",
                    }
                ]
            }
        }
        result = self.searcher._parse_artists(raw)
        assert result == []

    def test_parse_artists_empty_response(self):
        """_parse_artists returns empty list for missing 'artists' key"""
        result = self.searcher._parse_artists({})
        assert result == []


class TestSpotifyErrorHandling:
    """Test Spotify error handling paths"""

    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("api.spotify_search.SpotifyClientCredentials"), patch("api.spotify_search.spotipy.Spotify"):
            from api.spotify_search import SpotifySearcher

            self.searcher = SpotifySearcher("fake_id", "fake_secret")

    def test_handle_spotify_error_429(self):
        """_handle_spotify_error returns [] for 429 rate limit"""
        from spotipy.exceptions import SpotifyException

        err = SpotifyException(http_status=429, code=-1, msg="Rate limit")
        err.headers = {"Retry-After": "1"}
        result = self.searcher._handle_spotify_error(err, "search_tracks")
        assert result == []

    def test_handle_spotify_error_401(self):
        """_handle_spotify_error returns [] for 401 unauthorized"""
        from spotipy.exceptions import SpotifyException

        err = SpotifyException(http_status=401, code=-1, msg="Unauthorized")
        result = self.searcher._handle_spotify_error(err, "search_tracks")
        assert result == []

    def test_handle_spotify_error_400(self):
        """_handle_spotify_error returns [] for 400 bad request"""
        from spotipy.exceptions import SpotifyException

        err = SpotifyException(http_status=400, code=-1, msg="Bad request")
        result = self.searcher._handle_spotify_error(err, "search_tracks")
        assert result == []

    def test_handle_spotify_error_500(self):
        """_handle_spotify_error returns [] for 500 server error"""
        from spotipy.exceptions import SpotifyException

        err = SpotifyException(http_status=500, code=-1, msg="Server error")
        result = self.searcher._handle_spotify_error(err, "search_tracks")
        assert result == []

    def test_search_network_error(self):
        """_search returns [] on network error"""
        import requests

        self.searcher.sp.search = MagicMock(side_effect=requests.RequestException("Network down"))
        result = self.searcher.search_tracks("test")
        assert result == []

    def test_search_returns_empty_after_all_retries(self):
        """_search returns [] when all retries are exhausted (line 178)"""
        from spotipy.exceptions import SpotifyException

        err = SpotifyException(http_status=429, code=-1, msg="Rate limit")
        err.headers = {"Retry-After": "0"}
        self.searcher.sp.search = MagicMock(side_effect=err)
        self.searcher._retry_attempts = 1  # Only 1 attempt
        result = self.searcher.search_tracks("test")
        assert result == []


class TestSpotifyClearCacheAndDetails:
    """Test clear_cache and get_track_details"""

    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("api.spotify_search.SpotifyClientCredentials"), patch("api.spotify_search.spotipy.Spotify"):
            from api.spotify_search import SpotifySearcher

            self.searcher = SpotifySearcher("fake_id", "fake_secret")

    def test_clear_cache(self):
        """clear_cache delegates to internal cache"""
        self.searcher._cache.put("test", 5, [{"id": 1}])
        self.searcher.clear_cache()
        assert self.searcher._cache.get("test", 5) is None

    def test_get_track_details_success(self):
        """get_track_details returns track data on success"""
        mock_track = {"id": "abc", "name": "Song", "artists": []}
        self.searcher.sp.track = MagicMock(return_value=mock_track)
        result = self.searcher.get_track_details("abc")
        assert result == mock_track
        self.searcher.sp.track.assert_called_once_with("abc")

    def test_get_track_details_error(self):
        """get_track_details returns None on error"""
        from spotipy.exceptions import SpotifyException

        self.searcher.sp.track = MagicMock(side_effect=SpotifyException(http_status=404, code=-1, msg="Not found"))
        result = self.searcher.get_track_details("bad_id")
        assert result is None


# ---------------------------------------------------------------------------
# YouTubeSearcher unit tests (mock-based)
# ---------------------------------------------------------------------------
class TestYouTubeParseEdgeCases:
    """Test YouTube parse methods with edge-case data"""

    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("api.youtube_search.build") as mock_build:
            mock_build.return_value = MagicMock()
            from api.youtube_search import YouTubeSearcher

            self.searcher = YouTubeSearcher("fake_key")

    def test_parse_empty_response(self):
        """_parse_search_results returns [] for response without 'items'"""
        result = self.searcher._parse_search_results({})
        assert result == []

    def test_parse_missing_key_in_item(self):
        """_parse_search_results skips items with missing keys"""
        response = {
            "items": [
                {"snippet": {"title": "Test", "thumbnails": {"default": {"url": "http://x"}}}},  # Missing "id" key
                {  # Valid
                    "id": {"videoId": "abc12345678"},
                    "snippet": {
                        "title": "Valid Video",
                        "thumbnails": {"high": {"url": "http://thumb.jpg"}},
                    },
                },
            ]
        }
        result = self.searcher._parse_search_results(response)
        assert len(result) == 1
        assert result[0]["title"] == "Valid Video"

    def test_parse_medium_thumbnail_fallback(self):
        """Uses medium thumbnail when high is missing"""
        response = {
            "items": [
                {
                    "id": {"videoId": "abc12345678"},
                    "snippet": {
                        "title": "Video",
                        "thumbnails": {"medium": {"url": "http://med.jpg"}},
                    },
                }
            ]
        }
        result = self.searcher._parse_search_results(response)
        assert result[0]["thumbnail_url"] == "http://med.jpg"

    def test_parse_default_thumbnail_fallback(self):
        """Uses default thumbnail when high and medium are missing"""
        response = {
            "items": [
                {
                    "id": {"videoId": "abc12345678"},
                    "snippet": {
                        "title": "Video",
                        "thumbnails": {"default": {"url": "http://def.jpg"}},
                    },
                }
            ]
        }
        result = self.searcher._parse_search_results(response)
        assert result[0]["thumbnail_url"] == "http://def.jpg"

    def test_clear_cache(self):
        """clear_cache delegates to internal cache"""
        self.searcher._cache.put("test", 5, [{"id": "v1"}])
        self.searcher.clear_cache()
        assert self.searcher._cache.get("test", 5) is None


class TestYouTubeGetVideoMetadata:
    """Test get_video_metadata"""

    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("api.youtube_search.build") as mock_build:
            self.mock_youtube = MagicMock()
            mock_build.return_value = self.mock_youtube
            from api.youtube_search import YouTubeSearcher

            self.searcher = YouTubeSearcher("fake_key")

    def test_get_video_metadata_success(self):
        """get_video_metadata returns first item on success"""
        mock_response = {"items": [{"id": "abc", "snippet": {"title": "Song"}}]}
        self.mock_youtube.videos().list().execute.return_value = mock_response
        result = self.searcher.get_video_metadata("abc12345678")
        assert result == {"id": "abc", "snippet": {"title": "Song"}}

    def test_get_video_metadata_not_found(self):
        """get_video_metadata returns None when no items"""
        self.mock_youtube.videos().list().execute.return_value = {"items": []}
        result = self.searcher.get_video_metadata("bad_id")
        assert result is None

    def test_get_video_metadata_error(self):
        """get_video_metadata returns None on API error"""
        from googleapiclient.errors import HttpError

        resp = MagicMock()
        resp.status = 404
        self.mock_youtube.videos().list().execute.side_effect = HttpError(resp, b"Not found")
        result = self.searcher.get_video_metadata("bad_id")
        assert result is None


# ---------------------------------------------------------------------------
# ChordsClient additional coverage
# ---------------------------------------------------------------------------
class TestChordsClientSaveToDb:
    """Test _save_to_db and _load_from_db error paths"""

    def test_save_to_db_success(self):
        """_save_to_db calls execute_query with JSON"""
        from api.chords_client import ChordsClient

        mock_db = MagicMock()
        client = ChordsClient(db_manager=mock_db)
        chords = [{"t": 0.0, "chord": "C"}]
        client._save_to_db(42, chords)
        mock_db.execute_query.assert_called_once_with(
            "UPDATE songs SET chords = ? WHERE id = ?",
            (json.dumps(chords), 42),
        )

    def test_save_to_db_error_handled(self):
        """_save_to_db handles DB errors gracefully"""
        from api.chords_client import ChordsClient

        mock_db = MagicMock()
        mock_db.execute_query.side_effect = OSError("disk full")
        client = ChordsClient(db_manager=mock_db)
        # Should not raise
        client._save_to_db(42, [{"t": 0.0, "chord": "C"}])

    def test_load_from_db_error_returns_none(self):
        """_load_from_db returns None on DB errors"""
        from api.chords_client import ChordsClient

        mock_db = MagicMock()
        mock_db.execute_query.side_effect = TypeError("bad data")
        client = ChordsClient(db_manager=mock_db)
        result = client._load_from_db(99)
        assert result is None


class TestChordsTransposeErrorPaths:
    """Test transpose_chords error handling"""

    def test_transpose_invalid_chord_kept_as_is(self):
        """Invalid chord names are kept unchanged during transposition"""
        from api.chords_client import ChordsClient

        chords = [{"t": 0.0, "chord": "C"}, {"t": 4.0, "chord": "XYZ_INVALID"}]

        # Mock pychord to raise ValueError on invalid chord
        mock_chord_cls = MagicMock()

        def chord_factory(name):
            if name == "XYZ_INVALID":
                raise ValueError(f"Unknown chord: {name}")
            mock = MagicMock()
            mock.__str__ = MagicMock(return_value="D")
            return mock

        mock_chord_cls.side_effect = chord_factory

        with patch.dict("sys.modules", {"pychord": MagicMock(Chord=mock_chord_cls)}):
            result = ChordsClient.transpose_chords(chords, 2)
            assert len(result) == 2
            # Valid chord was transposed
            assert result[0]["t"] == 0.0
            # Invalid chord kept as-is
            assert result[1] == {"t": 4.0, "chord": "XYZ_INVALID"}
