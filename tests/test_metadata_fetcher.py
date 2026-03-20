"""
Tests for MetadataFetcher - Intelligent metadata search and matching

Tests cover:
- Searching from MusicBrainz and Spotify sources
- Mock API responses and result parsing
- Error handling (network errors, no results, malformed data)
- Match scoring (title/artist/duration weights)
- Result merging and priority (best match selection)
- Edge cases (empty inputs, missing clients)
"""

from unittest.mock import Mock, patch

import pytest
import requests

from core.metadata_fetcher import MetadataFetcher

# ─── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def mock_mb_client():
    """Mock MusicBrainz client"""
    return Mock()


@pytest.fixture
def mock_spotify_client():
    """Mock Spotify client"""
    return Mock()


@pytest.fixture
def fetcher(mock_mb_client, mock_spotify_client):
    """MetadataFetcher with both mock clients"""
    return MetadataFetcher(musicbrainz_client=mock_mb_client, spotify_client=mock_spotify_client)


@pytest.fixture
def fetcher_mb_only(mock_mb_client):
    """MetadataFetcher with MusicBrainz only"""
    return MetadataFetcher(musicbrainz_client=mock_mb_client)


@pytest.fixture
def fetcher_no_clients():
    """MetadataFetcher with no clients"""
    return MetadataFetcher()


@pytest.fixture
def mb_recording_bohemian():
    """Sample MusicBrainz recording for Bohemian Rhapsody"""
    return {
        "title": "Bohemian Rhapsody",
        "artist-credit": [{"name": "Queen"}],
        "releases": [{"title": "A Night at the Opera", "date": "1975-10-31"}],
        "length": 354000,  # milliseconds
    }


@pytest.fixture
def spotify_track_bohemian():
    """Sample Spotify track for Bohemian Rhapsody"""
    return {
        "name": "Bohemian Rhapsody",
        "artists": [{"name": "Queen"}],
        "album": {"name": "A Night at the Opera", "release_date": "1975-10-31"},
        "duration_ms": 354000,
    }


# ─── Tests: Initialization ─────────────────────────────────────────────


class TestMetadataFetcherInit:
    def test_init_with_both_clients(self, mock_mb_client, mock_spotify_client):
        fetcher = MetadataFetcher(mock_mb_client, mock_spotify_client)
        assert fetcher.musicbrainz_client is mock_mb_client
        assert fetcher.spotify_client is mock_spotify_client

    def test_init_with_no_clients(self):
        fetcher = MetadataFetcher()
        assert fetcher.musicbrainz_client is None
        assert fetcher.spotify_client is None


# ─── Tests: MusicBrainz search ─────────────────────────────────────────


class TestMusicBrainzSearch:
    @patch("core.metadata_fetcher.sanitize_query", side_effect=lambda x: x)
    def test_search_musicbrainz_returns_results(self, mock_sanitize, fetcher, mock_mb_client, mb_recording_bohemian):
        """MusicBrainz search returns properly formatted results"""
        mock_mb_client.search_recordings.return_value = [mb_recording_bohemian]

        results = fetcher.search_by_title_artist("Bohemian Rhapsody", "Queen")

        assert len(results) >= 1
        mb_result = next(r for r in results if r["source"] == "musicbrainz")
        assert mb_result["title"] == "Bohemian Rhapsody"
        assert mb_result["artist"] == "Queen"
        assert mb_result["album"] == "A Night at the Opera"
        assert mb_result["year"] == 1975
        assert mb_result["duration"] == 354  # ms -> seconds

    @patch("core.metadata_fetcher.sanitize_query", side_effect=lambda x: x)
    def test_search_musicbrainz_no_results(self, mock_sanitize, fetcher, mock_mb_client):
        """MusicBrainz search returns empty list when no matches found"""
        mock_mb_client.search_recordings.return_value = []

        results = fetcher._search_musicbrainz("Nonexistent Song", "Nobody")
        assert results == []

    @patch("core.metadata_fetcher.sanitize_query", side_effect=lambda x: x)
    def test_search_musicbrainz_network_error(self, mock_sanitize, fetcher, mock_mb_client):
        """MusicBrainz network error is handled gracefully"""
        mock_mb_client.search_recordings.side_effect = requests.RequestException("timeout")

        results = fetcher.search_by_title_artist("Song", "Artist")
        # Should not raise; MB results empty, spotify results may exist
        assert isinstance(results, list)

    @patch("core.metadata_fetcher.sanitize_query", side_effect=lambda x: x)
    def test_search_musicbrainz_missing_fields(self, mock_sanitize, fetcher, mock_mb_client):
        """MusicBrainz recording with missing optional fields is handled"""
        incomplete_recording = {
            "title": "Some Song",
            # No artist-credit, no releases, no length
        }
        mock_mb_client.search_recordings.return_value = [incomplete_recording]

        results = fetcher._search_musicbrainz("Some Song", "Artist")
        assert len(results) == 1
        assert results[0]["artist"] == "Unknown Artist"
        assert results[0]["album"] == "Unknown Album"
        assert results[0]["year"] is None
        assert results[0]["duration"] == 0


# ─── Tests: Spotify search ─────────────────────────────────────────────


class TestSpotifySearch:
    def test_search_spotify_returns_results(self, fetcher, mock_spotify_client, spotify_track_bohemian):
        """Spotify search returns properly formatted results"""
        mock_spotify_client.search_tracks.return_value = [spotify_track_bohemian]

        results = fetcher._search_spotify("Bohemian Rhapsody", "Queen")

        assert len(results) == 1
        assert results[0]["title"] == "Bohemian Rhapsody"
        assert results[0]["artist"] == "Queen"
        assert results[0]["album"] == "A Night at the Opera"
        assert results[0]["year"] == 1975
        assert results[0]["duration"] == 354
        assert results[0]["source"] == "spotify"

    def test_search_spotify_adapter_format(self, fetcher, mock_spotify_client):
        """Spotify adapter format with dict album is handled correctly"""
        adapter_track = {
            "title": "Song Title",
            "artist": "Artist Name",
            "album": {"name": "Album Name", "release_date": "2020-01-01"},
            "duration": 200,  # already in seconds (adapter format)
        }
        mock_spotify_client.search_tracks.return_value = [adapter_track]

        results = fetcher._search_spotify("Song Title", "Artist Name")

        assert len(results) == 1
        assert results[0]["title"] == "Song Title"
        assert results[0]["artist"] == "Artist Name"
        assert results[0]["album"] == "Album Name"
        assert results[0]["duration"] == 200
        assert results[0]["year"] == 2020

    def test_search_spotify_no_client(self, fetcher_no_clients):
        """Spotify search returns empty when no client configured"""
        results = fetcher_no_clients._search_spotify("Song", "Artist")
        assert results == []


# ─── Tests: Match scoring ──────────────────────────────────────────────


class TestMatchScoring:
    def test_perfect_match_score(self, fetcher):
        """Perfect title+artist+duration match scores near 100"""
        score = fetcher._calculate_match_score(
            query_title="Bohemian Rhapsody",
            query_artist="Queen",
            query_duration=354,
            result_title="Bohemian Rhapsody",
            result_artist="Queen",
            result_duration=354,
        )
        assert score == 100.0

    def test_no_duration_match_caps_at_80(self, fetcher):
        """Without duration info, max score is 80 (title 50 + artist 30)"""
        score = fetcher._calculate_match_score(
            query_title="Bohemian Rhapsody",
            query_artist="Queen",
            query_duration=None,
            result_title="Bohemian Rhapsody",
            result_artist="Queen",
            result_duration=354,
        )
        assert score == 80.0

    def test_partial_title_match(self, fetcher):
        """Partial title match gets proportional score"""
        score = fetcher._calculate_match_score(
            query_title="Bohemian Rhapsody",
            query_artist="Queen",
            query_duration=None,
            result_title="Bohemian Rhapsody (Remastered)",
            result_artist="Queen",
            result_duration=0,
        )
        # Title similarity < 1.0, artist = 1.0
        assert 50.0 < score < 80.0

    def test_empty_strings_score_zero(self, fetcher):
        """Empty query/result strings produce zero similarity"""
        score = fetcher._calculate_match_score(
            query_title="",
            query_artist="",
            query_duration=None,
            result_title="Anything",
            result_artist="Anyone",
            result_duration=0,
        )
        assert score == 0.0

    def test_duration_close_match_scoring(self, fetcher):
        """Duration within 3 seconds gets full 20 points"""
        score_exact = fetcher._calculate_match_score("S", "A", 200, "S", "A", 200)
        score_close = fetcher._calculate_match_score("S", "A", 200, "S", "A", 203)
        score_far = fetcher._calculate_match_score("S", "A", 200, "S", "A", 250)

        assert score_exact > score_close or score_exact == score_close  # both get 20
        assert score_exact > score_far


# ─── Tests: Result merging and best match ──────────────────────────────


class TestBestMatch:
    def test_get_best_match_returns_highest_score(self, fetcher):
        """get_best_match returns result with highest score"""
        results = [
            {"title": "A", "artist": "X", "score": 95.0, "source": "musicbrainz"},
            {"title": "B", "artist": "Y", "score": 60.0, "source": "spotify"},
        ]
        best = fetcher.get_best_match(results, min_confidence=50.0)
        assert best["title"] == "A"
        assert best["score"] == 95.0

    def test_get_best_match_below_threshold_returns_none(self, fetcher):
        """get_best_match returns None when best score < min_confidence"""
        results = [
            {"title": "A", "artist": "X", "score": 55.0, "source": "musicbrainz"},
        ]
        best = fetcher.get_best_match(results, min_confidence=70.0)
        assert best is None

    def test_get_best_match_empty_results(self, fetcher):
        """get_best_match returns None for empty result list"""
        assert fetcher.get_best_match([], min_confidence=0.0) is None

    @patch("core.metadata_fetcher.sanitize_query", side_effect=lambda x: x)
    def test_fetch_metadata_oneshot(self, mock_sanitize, fetcher, mock_mb_client, mb_recording_bohemian):
        """fetch_metadata combines search + best match in one call"""
        mock_mb_client.search_recordings.return_value = [mb_recording_bohemian]

        result = fetcher.fetch_metadata(title="Bohemian Rhapsody", artist="Queen", duration=354, min_confidence=50.0)
        assert result is not None
        assert result["title"] == "Bohemian Rhapsody"
        assert result["source"] == "musicbrainz"

    @patch("core.metadata_fetcher.sanitize_query", side_effect=lambda x: x)
    def test_results_sorted_by_score(self, mock_sanitize, fetcher, mock_mb_client, mock_spotify_client):
        """Combined results from all sources are sorted by score descending"""
        mock_mb_client.search_recordings.return_value = [
            {"title": "Low Match", "artist-credit": [{"name": "Wrong"}], "releases": [], "length": 100000}
        ]
        mock_spotify_client.search_tracks.return_value = [
            {
                "name": "Bohemian Rhapsody",
                "artists": [{"name": "Queen"}],
                "album": {"name": "Album", "release_date": "1975"},
                "duration_ms": 354000,
            }
        ]

        results = fetcher.search_by_title_artist("Bohemian Rhapsody", "Queen", duration=354)
        # Results should be sorted by score descending
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
