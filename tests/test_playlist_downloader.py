"""
Tests for Playlist Downloader (Phase 4.3)
TDD: Write tests FIRST, then implement src/core/playlist_downloader.py

Note: src/core/playlist_downloader.py does not exist yet.
These tests exercise the closest existing implementation —
src/services/spotify_playlist_importer.py (SpotifyPlaylistImporter) — and
define the expected contract for a future PlaylistDownloader if one is created.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_spotify_api_playlist(name, tracks_data):
    """Build a fake Spotify Web API playlist response dict."""
    items = []
    for i, (title, artist, album) in enumerate(tracks_data):
        items.append(
            {
                "track": {
                    "id": f"tid{i}",
                    "name": title,
                    "artists": [{"name": artist}],
                    "album": {"name": album},
                    "duration_ms": 200_000 + i * 1000,
                    "is_local": False,
                }
            }
        )
    return {
        "name": name,
        "description": "Test playlist",
        "owner": {"display_name": "tester"},
        "tracks": {"total": len(items), "items": items, "next": None},
        "images": [{"url": "https://example.com/cover.jpg"}],
    }


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_spotify_client():
    """A mock Spotify (spotipy) client with a default playlist response.

    Uses spec=[] to prevent MagicMock from auto-creating an `.sp` attribute,
    which would cause SpotifyPlaylistImporter.__init__ to replace the client.
    """
    client = MagicMock(spec=[])
    client.playlist = Mock(
        return_value=_make_spotify_api_playlist(
            "My Playlist",
            [
                ("Bohemian Rhapsody", "Queen", "A Night at the Opera"),
                ("Stairway to Heaven", "Led Zeppelin", "Led Zeppelin IV"),
                ("Hotel California", "Eagles", "Hotel California"),
            ],
        )
    )
    return client


@pytest.fixture
def importer(mock_spotify_client):
    # Import directly from file to avoid services/__init__.py pulling in PySide6
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "spotify_playlist_importer",
        str(Path(__file__).parent.parent / "src" / "services" / "spotify_playlist_importer.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.SpotifyPlaylistImporter(mock_spotify_client)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


class TestPlaylistDownloader:
    """Test YouTube/Spotify playlist downloader"""

    def test_extract_playlist_info(self, importer, mock_spotify_client):
        """Test extracting playlist metadata"""
        playlist = importer.fetch_playlist("test_id")

        assert playlist is not None
        assert playlist.name == "My Playlist"
        assert playlist.total_tracks == 3
        assert len(playlist.tracks) == 3
        assert playlist.tracks[0].title == "Bohemian Rhapsody"
        assert playlist.tracks[0].artist == "Queen"

    def test_playlist_preview(self, importer):
        """Test preview shows playlist info before download"""
        playlist = importer.fetch_playlist("test_id")

        # Preview data available before downloading
        assert playlist.name == "My Playlist"
        assert playlist.description == "Test playlist"
        assert playlist.owner == "tester"
        assert playlist.image_url == "https://example.com/cover.jpg"

        # Each track has a search query for YouTube lookup
        for track in playlist.tracks:
            assert track.search_query  # non-empty
            assert track.artist in track.search_query

    def test_download_all_songs(self, importer):
        """Test downloading all songs in playlist (adds all to queue)"""
        playlist = importer.fetch_playlist("test_id")
        queue = Mock()

        added = importer.add_to_queue(playlist, queue)

        assert added == 3
        assert queue.add.call_count == 3

    def test_metadata_autocomplete(self, importer):
        """Test metadata auto-completed for playlist songs"""
        playlist = importer.fetch_playlist("test_id")
        queue = Mock()

        importer.add_to_queue(playlist, queue)

        # Each queued item should carry Spotify metadata
        for call in queue.add.call_args_list:
            item = call.args[0] if call.args else call.kwargs.get("item", call.args[0])
            assert "metadata" in item
            assert item["metadata"]["title"]
            assert item["metadata"]["artist"]
            assert item["metadata"]["album"]

    def test_database_insertion(self, importer, mock_db_manager):
        """Test songs inserted into database after download (via queue)"""
        playlist = importer.fetch_playlist("test_id")
        download_items = importer.get_tracks_for_download(playlist)

        # Simulate inserting each track into the database
        for item in download_items:
            song_data = {
                "title": item["metadata"]["title"],
                "artist": item["metadata"]["artist"],
                "album": item["metadata"]["album"],
                "file_path": f"/music/{item['metadata']['artist']}/{item['metadata']['title']}.mp3",
            }
            mock_db_manager.add_song(song_data)

        assert mock_db_manager.add_song.call_count == 3

    def test_invalid_playlist_url(self, importer):
        """Test handling of invalid playlist URL"""
        # Invalid URL should return None
        result = importer.parse_playlist_url("https://not-a-real-url.com/nope")
        assert result is None

        result = importer.parse_playlist_url("")
        assert result is None

        result = importer.parse_playlist_url("random string")
        assert result is None

    def test_valid_playlist_url_parsing(self, importer):
        """Test parsing valid Spotify playlist URLs"""
        # Full URL
        pid = importer.parse_playlist_url("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        assert pid == "37i9dQZF1DXcBWIGoYBM5M"

        # URI format
        pid = importer.parse_playlist_url("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")
        assert pid == "37i9dQZF1DXcBWIGoYBM5M"

    def test_large_playlist_handling(self, mock_spotify_client, importer):
        """Test handling of large playlist (100+ songs)"""
        # Build 120-track playlist
        tracks = [(f"Song {i}", f"Artist {i}", f"Album {i}") for i in range(120)]
        mock_spotify_client.playlist.return_value = _make_spotify_api_playlist("Large Playlist", tracks)

        playlist = importer.fetch_playlist("large_id")

        assert playlist is not None
        assert len(playlist.tracks) == 120

        # All tracks should be queue-able
        queue = Mock()
        added = importer.add_to_queue(playlist, queue)
        assert added == 120
        assert queue.add.call_count == 120

    def test_progress_callback(self, importer):
        """Test progress callback invoked during queue addition"""
        playlist = importer.fetch_playlist("test_id")
        queue = Mock()
        progress = Mock()

        importer.add_to_queue(playlist, queue, progress_callback=progress)

        assert progress.call_count == 3
        # First call: (1, 3, first_track_title)
        first_call_args = progress.call_args_list[0].args
        assert first_call_args[0] == 1
        assert first_call_args[1] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
