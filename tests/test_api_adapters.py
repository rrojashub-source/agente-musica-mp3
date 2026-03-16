"""
Tests for API Adapters - MusicBrainzAdapter and SpotifyAdapter
Tests adapter pattern, data transformation, and error handling.
"""

from unittest.mock import MagicMock

import pytest

from src.core.api_adapters import MusicBrainzAdapter, SpotifyAdapter

# ===========================================================================
# MusicBrainzAdapter
# ===========================================================================


class TestMusicBrainzAdapter:

    @pytest.fixture
    def mb_client(self):
        return MagicMock()

    @pytest.fixture
    def adapter(self, mb_client):
        return MusicBrainzAdapter(mb_client)

    def test_search_transforms_to_metadata_format(self, adapter, mb_client):
        """Results are converted to the nested dict format MetadataFetcher expects."""
        mb_client.search_recording.return_value = [
            {"title": "Clavaito", "artist": "Chanel", "album": "Agua", "year": 2024},
        ]
        query = 'recording:"Clavaito" AND artist:"Chanel"'
        results = adapter.search_recordings(query, limit=5)

        assert len(results) == 1
        r = results[0]
        assert r["title"] == "Clavaito"
        assert r["artist-credit"][0]["name"] == "Chanel"
        assert r["releases"][0]["title"] == "Agua"
        assert r["releases"][0]["date"] == "2024-01-01"
        assert "length" in r

    def test_search_no_title_returns_empty(self, adapter):
        """Query without recording: prefix returns empty list."""
        results = adapter.search_recordings("random text without pattern")
        assert results == []

    def test_search_without_artist_still_works(self, adapter, mb_client):
        """Query with only title (no artist:) should still query the client."""
        mb_client.search_recording.return_value = [
            {"title": "Imagine", "artist": "John Lennon", "album": "Imagine"},
        ]
        query = 'recording:"Imagine"'
        results = adapter.search_recordings(query)
        mb_client.search_recording.assert_called_once_with("Imagine", artist=None, limit=5)
        assert len(results) == 1

    def test_search_empty_results(self, adapter, mb_client):
        mb_client.search_recording.return_value = []
        query = 'recording:"Nonexistent" AND artist:"Nobody"'
        assert adapter.search_recordings(query) == []


# ===========================================================================
# SpotifyAdapter
# ===========================================================================


class TestSpotifyAdapter:

    @pytest.fixture
    def sp_searcher(self):
        return MagicMock()

    @pytest.fixture
    def adapter(self, sp_searcher):
        return SpotifyAdapter(sp_searcher)

    def test_search_transforms_to_spotify_format(self, adapter, sp_searcher):
        """Results are converted to the Spotify-style dict MetadataFetcher expects."""
        sp_searcher.search_tracks.return_value = [
            {"title": "SloMo", "artist": "Chanel", "album": "Agua", "year": "2022", "duration": 180},
        ]
        query = "track:SloMo artist:Chanel"
        results = adapter.search_tracks(query, limit=5)

        assert len(results) == 1
        r = results[0]
        assert r["name"] == "SloMo"
        assert r["artists"][0]["name"] == "Chanel"
        assert r["album"]["name"] == "Agua"
        assert r["duration_ms"] == 180_000  # seconds -> ms

    def test_search_no_track_returns_empty(self, adapter):
        results = adapter.search_tracks("random text")
        assert results == []

    def test_search_error_returns_empty(self, adapter, sp_searcher):
        """Exceptions from the searcher should be caught, returning []."""
        sp_searcher.search_tracks.side_effect = TypeError("bad data")
        results = adapter.search_tracks("track:Test artist:X")
        assert results == []

    def test_search_empty_results(self, adapter, sp_searcher):
        sp_searcher.search_tracks.return_value = []
        results = adapter.search_tracks("track:Nothing artist:Nobody")
        assert results == []
