"""
Tests for Spotify Search Integration (Phase 4.1)
TDD: Write tests FIRST, then implement src/api/spotify_search.py
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSpotifySearch:
    """Test Spotify Web API integration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        # Load test credentials from secrets
        secrets_path = Path.home() / ".claude" / "secrets" / "credentials.json"
        with open(secrets_path) as f:
            secrets = json.load(f)

        self.client_id = secrets["apis"]["spotify"]["client_id"]
        self.client_secret = secrets["apis"]["spotify"]["client_secret"]

        # Import the class we're testing (will fail initially - expected in TDD Red phase)
        try:
            from src.api.spotify_search import SpotifySearcher

            self.searcher = SpotifySearcher(self.client_id, self.client_secret)
        except ImportError:
            self.searcher = None  # Expected to fail initially

    def test_spotify_api_connection(self):
        """Test successful OAuth connection to Spotify API"""
        if self.searcher is None:
            pytest.fail("SpotifySearcher class not found - implement src/api/spotify_search.py")

        # Test that the searcher was initialized correctly
        assert self.searcher is not None
        assert self.searcher.sp is not None  # Spotipy client
        assert self.searcher._client_id == self.client_id

    def test_search_tracks(self):
        """Test search for tracks"""
        if self.searcher is None:
            pytest.fail("SpotifySearcher class not found")

        # Search for "Bohemian Rhapsody"
        results = self.searcher.search_tracks("Bohemian Rhapsody", limit=5)

        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0
        assert len(results) <= 5

        # Verify each result has required fields
        for result in results:
            assert "track_id" in result
            assert "title" in result
            assert "artist" in result
            assert "album" in result
            assert "duration_ms" in result

            # Verify fields are not empty
            assert result["track_id"]
            assert result["title"]
            assert result["artist"]

    def test_search_albums(self):
        """Test search for albums"""
        if self.searcher is None:
            pytest.fail("SpotifySearcher class not found")

        # Search for "A Night at the Opera"
        results = self.searcher.search_albums("A Night at the Opera", limit=3)

        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0

        # Verify each result has required fields
        for result in results:
            assert "album_id" in result
            assert "name" in result
            assert "artist" in result
            assert "release_date" in result
            assert "total_tracks" in result

    def test_search_artists(self):
        """Test search for artists"""
        if self.searcher is None:
            pytest.fail("SpotifySearcher class not found")

        # Search for "Queen"
        results = self.searcher.search_artists("Queen", limit=3)

        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0

        # Verify each result has required fields
        for result in results:
            assert "artist_id" in result
            assert "name" in result
            assert "genres" in result
            assert "popularity" in result

            # Verify types
            assert isinstance(result["genres"], list)
            assert isinstance(result["popularity"], int)

    def test_metadata_extraction(self):
        """Test metadata extraction from search results"""
        if self.searcher is None:
            pytest.fail("SpotifySearcher class not found")

        # Search and get detailed metadata
        results = self.searcher.search_tracks("test", limit=1)

        # Expected format: {'title', 'artist', 'album', 'year', 'duration_ms'}
        assert isinstance(results, list)

        if len(results) > 0:
            track = results[0]

            # Required fields
            assert "track_id" in track
            assert "title" in track
            assert "artist" in track
            assert "album" in track
            assert "duration_ms" in track

            # Field types
            assert isinstance(track["track_id"], str)
            assert isinstance(track["title"], str)
            assert isinstance(track["artist"], str)
            assert isinstance(track["album"], str)
            assert isinstance(track["duration_ms"], int)

            # Duration should be positive
            assert track["duration_ms"] > 0

    def test_rate_limit_handling(self):
        """Test handling of rate limit (100 requests/second)"""
        if self.searcher is None:
            pytest.fail("SpotifySearcher class not found")

        # Mock Spotipy to simulate rate limit
        with patch.object(self.searcher.sp, "search") as mock_search:
            from spotipy.exceptions import SpotifyException

            # Simulate 429 rate limit error
            mock_search.side_effect = SpotifyException(
                http_status=429, code=-1, msg="Rate limit exceeded", reason="TOO_MANY_REQUESTS"
            )

            # Should handle rate limit gracefully
            try:
                results = self.searcher.search_tracks("test")
                # If no exception, should return empty list
                assert results == []
            except Exception as e:
                # If exception, should be a meaningful one
                assert "rate" in str(e).lower()

    def test_oauth_token_refresh(self):
        """Test OAuth token refresh when expired"""
        if self.searcher is None:
            pytest.fail("SpotifySearcher class not found")

        # Note: Spotipy handles token refresh automatically
        # This test verifies that the auth manager is configured correctly

        # Verify auth manager exists
        assert self.searcher.auth_manager is not None

        # Verify credentials are set
        assert self.searcher.auth_manager.client_id is not None
        assert self.searcher.auth_manager.client_secret is not None

        # Token should be obtainable (this triggers OAuth)
        token = self.searcher.auth_manager.get_access_token(as_dict=False)
        assert token is not None
