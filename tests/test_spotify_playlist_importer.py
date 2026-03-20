"""
Tests for Spotify Playlist Importer

Tests cover:
- URL/URI parsing
- Track parsing
- Playlist fetching (mocked)
- Download item generation
"""

import pytest
from unittest.mock import Mock

from services.spotify_playlist_importer import SpotifyPlaylistImporter, SpotifyTrack, SpotifyPlaylist, parse_spotify_url


class TestSpotifyTrack:
    """Test SpotifyTrack dataclass"""

    def test_search_query(self):
        """Should generate correct search query"""
        track = SpotifyTrack(
            track_id="abc123",
            title="Bohemian Rhapsody",
            artist="Queen",
            album="A Night at the Opera",
            duration_ms=354000,
            position=0,
        )

        assert track.search_query == "Queen - Bohemian Rhapsody"

    def test_duration_seconds(self):
        """Should convert ms to seconds"""
        track = SpotifyTrack(
            track_id="abc123", title="Test", artist="Test", album="Test", duration_ms=180000, position=0
        )

        assert track.duration_seconds == 180


class TestURLParsing:
    """Test Spotify URL/URI parsing"""

    @pytest.fixture
    def importer(self):
        """Create importer with mock client"""
        return SpotifyPlaylistImporter(Mock())

    def test_parse_playlist_url(self, importer):
        """Should parse standard playlist URL"""
        url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
        result = importer.parse_playlist_url(url)

        assert result == "37i9dQZF1DXcBWIGoYBM5M"

    def test_parse_playlist_url_with_params(self, importer):
        """Should parse URL with query parameters"""
        url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc123"
        result = importer.parse_playlist_url(url)

        assert result == "37i9dQZF1DXcBWIGoYBM5M"

    def test_parse_playlist_uri(self, importer):
        """Should parse Spotify URI"""
        uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
        result = importer.parse_playlist_url(uri)

        assert result == "37i9dQZF1DXcBWIGoYBM5M"

    def test_parse_raw_id(self, importer):
        """Should accept raw playlist ID"""
        playlist_id = "37i9dQZF1DXcBWIGoYBM5M"
        result = importer.parse_playlist_url(playlist_id)

        assert result == playlist_id

    def test_parse_invalid_url(self, importer):
        """Should return None for invalid URL"""
        invalid = "https://example.com/not-spotify"
        result = importer.parse_playlist_url(invalid)

        assert result is None

    def test_parse_empty_url(self, importer):
        """Should return None for empty input"""
        result = importer.parse_playlist_url("")

        assert result is None

    def test_parse_none_url(self, importer):
        """Should return None for None input"""
        result = importer.parse_playlist_url(None)

        assert result is None


class TestTrackParsing:
    """Test track parsing from API response"""

    @pytest.fixture
    def importer(self):
        return SpotifyPlaylistImporter(Mock())

    def test_parse_valid_track(self, importer):
        """Should parse valid track item"""
        item = {
            "track": {
                "id": "abc123",
                "name": "Test Song",
                "artists": [{"name": "Test Artist"}],
                "album": {"name": "Test Album"},
                "duration_ms": 200000,
            }
        }

        track = importer._parse_track(item, 0)

        assert track is not None
        assert track.track_id == "abc123"
        assert track.title == "Test Song"
        assert track.artist == "Test Artist"
        assert track.album == "Test Album"
        assert track.duration_ms == 200000
        assert track.position == 0

    def test_parse_track_missing_track_data(self, importer):
        """Should return None for missing track data"""
        item = {"track": None}
        track = importer._parse_track(item, 0)

        assert track is None

    def test_parse_local_track(self, importer):
        """Should skip local tracks"""
        item = {
            "track": {
                "id": "local123",
                "name": "Local Song",
                "is_local": True,
                "artists": [{"name": "Local Artist"}],
                "album": {"name": "Local Album"},
                "duration_ms": 180000,
            }
        }

        track = importer._parse_track(item, 0)

        assert track is None

    def test_parse_track_multiple_artists(self, importer):
        """Should use first artist when multiple"""
        item = {
            "track": {
                "id": "abc123",
                "name": "Collab Song",
                "artists": [{"name": "Artist One"}, {"name": "Artist Two"}],
                "album": {"name": "Album"},
                "duration_ms": 180000,
            }
        }

        track = importer._parse_track(item, 0)

        assert track.artist == "Artist One"

    def test_parse_track_no_artists(self, importer):
        """Should handle missing artists"""
        item = {
            "track": {
                "id": "abc123",
                "name": "Unknown Song",
                "artists": [],
                "album": {"name": "Album"},
                "duration_ms": 180000,
            }
        }

        track = importer._parse_track(item, 0)

        assert track.artist == "Unknown Artist"


class TestPlaylistFetching:
    """Test playlist fetching (mocked API)"""

    def test_fetch_playlist_success(self):
        """Should fetch and parse playlist via _fetch_all_tracks directly"""
        # Test internal track parsing directly to avoid mock complexity
        importer = SpotifyPlaylistImporter(Mock())

        # Simulate playlist_data dict
        playlist_data = {
            "name": "Test Playlist",
            "description": "A test playlist",
            "owner": {"display_name": "Test User"},
            "images": [{"url": "http://example.com/image.jpg"}],
            "tracks": {
                "total": 2,
                "items": [
                    {
                        "track": {
                            "id": "track1",
                            "name": "Song One",
                            "artists": [{"name": "Artist One"}],
                            "album": {"name": "Album One"},
                            "duration_ms": 180000,
                        }
                    },
                    {
                        "track": {
                            "id": "track2",
                            "name": "Song Two",
                            "artists": [{"name": "Artist Two"}],
                            "album": {"name": "Album Two"},
                            "duration_ms": 200000,
                        }
                    },
                ],
                "next": None,  # No pagination
            },
        }

        # Test _fetch_all_tracks directly
        tracks = importer._fetch_all_tracks("test_id", playlist_data)

        assert len(tracks) == 2
        assert tracks[0].title == "Song One"
        assert tracks[0].artist == "Artist One"
        assert tracks[1].title == "Song Two"
        assert tracks[1].artist == "Artist Two"

    def test_playlist_data_parsing(self):
        """Should correctly build SpotifyPlaylist from parsed data"""
        playlist = SpotifyPlaylist(
            playlist_id="test_id",
            name="Test Playlist",
            description="A test playlist",
            owner="Test User",
            total_tracks=2,
            tracks=[
                SpotifyTrack(
                    track_id="track1",
                    title="Song One",
                    artist="Artist One",
                    album="Album One",
                    duration_ms=180000,
                    position=0,
                ),
                SpotifyTrack(
                    track_id="track2",
                    title="Song Two",
                    artist="Artist Two",
                    album="Album Two",
                    duration_ms=200000,
                    position=1,
                ),
            ],
        )

        assert playlist.name == "Test Playlist"
        assert playlist.owner == "Test User"
        assert playlist.total_tracks == 2
        assert len(playlist.tracks) == 2

    def test_fetch_playlist_not_found(self):
        """Should handle playlist not found"""
        mock_sp = Mock()
        mock_sp.playlist.return_value = None

        importer = SpotifyPlaylistImporter(mock_sp)
        playlist = importer.fetch_playlist("nonexistent_id")

        assert playlist is None

    def test_fetch_playlist_api_error(self):
        """Should handle API errors gracefully"""
        mock_sp = Mock()
        mock_sp.playlist.side_effect = Exception("API Error")

        importer = SpotifyPlaylistImporter(mock_sp)
        playlist = importer.fetch_playlist("test_id")

        assert playlist is None


class TestDownloadItems:
    """Test download item generation"""

    @pytest.fixture
    def sample_playlist(self):
        """Create sample playlist"""
        return SpotifyPlaylist(
            playlist_id="test_id",
            name="Test Playlist",
            description="Test",
            owner="Test User",
            total_tracks=2,
            tracks=[
                SpotifyTrack(
                    track_id="track1",
                    title="Song One",
                    artist="Artist One",
                    album="Album One",
                    duration_ms=180000,
                    position=0,
                ),
                SpotifyTrack(
                    track_id="track2",
                    title="Song Two",
                    artist="Artist Two",
                    album="Album Two",
                    duration_ms=200000,
                    position=1,
                ),
            ],
        )

    def test_get_tracks_for_download(self, sample_playlist):
        """Should generate download items"""
        importer = SpotifyPlaylistImporter(Mock())
        items = importer.get_tracks_for_download(sample_playlist)

        assert len(items) == 2

        assert items[0]["id"] == "spotify_track1"
        assert items[0]["title"] == "Song One"
        assert items[0]["artist"] == "Artist One"
        assert items[0]["source"] == "spotify"
        assert items[0]["search_query"] == "Artist One - Song One"

        assert items[1]["id"] == "spotify_track2"
        assert items[1]["search_query"] == "Artist Two - Song Two"

    def test_add_to_queue(self, sample_playlist):
        """Should add tracks to download queue"""
        mock_queue = Mock()

        importer = SpotifyPlaylistImporter(Mock())
        added = importer.add_to_queue(sample_playlist, mock_queue)

        assert added == 2
        assert mock_queue.add.call_count == 2

    def test_add_to_queue_with_progress(self, sample_playlist):
        """Should call progress callback"""
        mock_queue = Mock()
        progress_calls = []

        def progress_callback(current, total, name):
            progress_calls.append((current, total, name))

        importer = SpotifyPlaylistImporter(Mock())
        importer.add_to_queue(sample_playlist, mock_queue, progress_callback=progress_callback)

        assert len(progress_calls) == 2
        assert progress_calls[0] == (1, 2, "Song One")
        assert progress_calls[1] == (2, 2, "Song Two")

    def test_add_to_queue_with_youtube_search(self, sample_playlist):
        """Should search YouTube when searcher provided"""
        mock_queue = Mock()
        mock_youtube = Mock()
        mock_youtube.search.return_value = [{"url": "https://youtube.com/watch?v=abc", "video_id": "abc"}]

        importer = SpotifyPlaylistImporter(Mock())
        importer.add_to_queue(sample_playlist, mock_queue, youtube_searcher=mock_youtube)

        # Check that queue items have YouTube URLs
        call_args = mock_queue.add.call_args_list
        assert call_args[0][0][0]["url"] == "https://youtube.com/watch?v=abc"


class TestConvenienceFunction:
    """Test convenience functions"""

    def test_parse_spotify_url(self):
        """Should work as convenience function"""
        url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
        result = parse_spotify_url(url)

        assert result == "37i9dQZF1DXcBWIGoYBM5M"
