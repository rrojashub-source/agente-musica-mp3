"""
Tests for Spotify Search Integration (Phase 4.1)
TDD: Write tests FIRST, then implement src/api/spotify_search.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path


class TestSpotifySearch(unittest.TestCase):
    """Test Spotify Web API integration"""

    def setUp(self):
        """Setup test fixtures"""
        # Load test credentials from secrets
        secrets_path = Path.home() / ".claude" / "secrets" / "credentials.json"
        with open(secrets_path) as f:
            secrets = json.load(f)

        self.client_id = secrets['apis']['spotify']['client_id']
        self.client_secret = secrets['apis']['spotify']['client_secret']

        # Import the class we're testing (will fail initially - expected in TDD Red phase)
        try:
            from src.api.spotify_search import SpotifySearcher
            self.searcher = SpotifySearcher(self.client_id, self.client_secret)
        except ImportError:
            self.searcher = None  # Expected to fail initially

    def test_spotify_api_connection(self):
        """Test successful OAuth connection to Spotify API"""
        if self.searcher is None:
            self.fail("SpotifySearcher class not found - implement src/api/spotify_search.py")

        # Test that the searcher was initialized correctly
        self.assertIsNotNone(self.searcher)
        self.assertIsNotNone(self.searcher.sp)  # Spotipy client
        self.assertEqual(self.searcher.client_id, self.client_id)

    def test_search_tracks(self):
        """Test search for tracks"""
        if self.searcher is None:
            self.fail("SpotifySearcher class not found")

        # Search for "Bohemian Rhapsody"
        results = self.searcher.search_tracks("Bohemian Rhapsody", limit=5)

        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 5)

        # Verify each result has required fields
        for result in results:
            self.assertIn('track_id', result)
            self.assertIn('title', result)
            self.assertIn('artist', result)
            self.assertIn('album', result)
            self.assertIn('duration_ms', result)

            # Verify fields are not empty
            self.assertTrue(result['track_id'])
            self.assertTrue(result['title'])
            self.assertTrue(result['artist'])

    def test_search_albums(self):
        """Test search for albums"""
        if self.searcher is None:
            self.fail("SpotifySearcher class not found")

        # Search for "A Night at the Opera"
        results = self.searcher.search_albums("A Night at the Opera", limit=3)

        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        # Verify each result has required fields
        for result in results:
            self.assertIn('album_id', result)
            self.assertIn('name', result)
            self.assertIn('artist', result)
            self.assertIn('release_date', result)
            self.assertIn('total_tracks', result)

    def test_search_artists(self):
        """Test search for artists"""
        if self.searcher is None:
            self.fail("SpotifySearcher class not found")

        # Search for "Queen"
        results = self.searcher.search_artists("Queen", limit=3)

        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        # Verify each result has required fields
        for result in results:
            self.assertIn('artist_id', result)
            self.assertIn('name', result)
            self.assertIn('genres', result)
            self.assertIn('popularity', result)

            # Verify types
            self.assertIsInstance(result['genres'], list)
            self.assertIsInstance(result['popularity'], int)

    def test_metadata_extraction(self):
        """Test metadata extraction from search results"""
        if self.searcher is None:
            self.fail("SpotifySearcher class not found")

        # Search and get detailed metadata
        results = self.searcher.search_tracks("test", limit=1)

        # Expected format: {'title', 'artist', 'album', 'year', 'duration_ms'}
        self.assertIsInstance(results, list)

        if len(results) > 0:
            track = results[0]

            # Required fields
            self.assertIn('track_id', track)
            self.assertIn('title', track)
            self.assertIn('artist', track)
            self.assertIn('album', track)
            self.assertIn('duration_ms', track)

            # Field types
            self.assertIsInstance(track['track_id'], str)
            self.assertIsInstance(track['title'], str)
            self.assertIsInstance(track['artist'], str)
            self.assertIsInstance(track['album'], str)
            self.assertIsInstance(track['duration_ms'], int)

            # Duration should be positive
            self.assertGreater(track['duration_ms'], 0)

    def test_rate_limit_handling(self):
        """Test handling of rate limit (100 requests/second)"""
        if self.searcher is None:
            self.fail("SpotifySearcher class not found")

        # Mock Spotipy to simulate rate limit
        with patch.object(self.searcher.sp, 'search') as mock_search:
            from spotipy.exceptions import SpotifyException

            # Simulate 429 rate limit error
            mock_search.side_effect = SpotifyException(
                http_status=429,
                code=-1,
                msg="Rate limit exceeded",
                reason="TOO_MANY_REQUESTS"
            )

            # Should handle rate limit gracefully
            try:
                results = self.searcher.search_tracks("test")
                # If no exception, should return empty list
                self.assertEqual(results, [])
            except Exception as e:
                # If exception, should be a meaningful one
                self.assertIn('rate', str(e).lower())

    def test_oauth_token_refresh(self):
        """Test OAuth token refresh when expired"""
        if self.searcher is None:
            self.fail("SpotifySearcher class not found")

        # Note: Spotipy handles token refresh automatically
        # This test verifies that the auth manager is configured correctly

        # Verify auth manager exists
        self.assertIsNotNone(self.searcher.auth_manager)

        # Verify credentials are set
        self.assertIsNotNone(self.searcher.auth_manager.client_id)
        self.assertIsNotNone(self.searcher.auth_manager.client_secret)

        # Token should be obtainable (this triggers OAuth)
        token = self.searcher.auth_manager.get_access_token(as_dict=False)
        self.assertIsNotNone(token)


if __name__ == "__main__":
    unittest.main()
