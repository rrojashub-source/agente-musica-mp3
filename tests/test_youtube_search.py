"""
Tests for YouTube Search Integration (Phase 4.1)
TDD: Write tests FIRST, then implement src/api/youtube_search.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path


class TestYouTubeSearch(unittest.TestCase):
    """Test YouTube Data API v3 integration"""

    def setUp(self):
        """Setup test fixtures"""
        # Load test API key from secrets
        secrets_path = Path.home() / ".claude" / "secrets" / "credentials.json"
        with open(secrets_path) as f:
            secrets = json.load(f)

        self.test_api_key = secrets['apis']['youtube']['api_key']

        # Import the class we're testing (will fail initially - that's expected in TDD Red phase)
        try:
            from src.api.youtube_search import YouTubeSearcher
            self.searcher = YouTubeSearcher(self.test_api_key)
        except ImportError:
            self.searcher = None  # Expected to fail initially

    def test_youtube_api_connection(self):
        """Test successful connection to YouTube API"""
        if self.searcher is None:
            self.fail("YouTubeSearcher class not found - implement src/api/youtube_search.py")

        # Test that the searcher was initialized correctly
        self.assertIsNotNone(self.searcher)
        self.assertEqual(self.searcher.api_key, self.test_api_key)

    def test_search_by_artist(self):
        """Test search by artist name"""
        if self.searcher is None:
            self.fail("YouTubeSearcher class not found")

        # Search for "The Beatles" (use_cache=False ensures fresh API call for test reliability)
        results = self.searcher.search("The Beatles", max_results=5, use_cache=False)

        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 5)

        # Verify each result has required fields
        for result in results:
            self.assertIn('video_id', result)
            self.assertIn('title', result)
            self.assertIn('thumbnail_url', result)

            # Verify video_id is not empty
            self.assertTrue(result['video_id'])
            self.assertTrue(result['title'])

    def test_search_by_song(self):
        """Test search by song title"""
        if self.searcher is None:
            self.fail("YouTubeSearcher class not found")

        # Search for specific song
        results = self.searcher.search("Bohemian Rhapsody Queen", max_results=3)

        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        # First result should be relevant (contain "Bohemian" or "Queen")
        first_result = results[0]
        title_lower = first_result['title'].lower()
        self.assertTrue(
            'bohemian' in title_lower or 'queen' in title_lower,
            f"First result title '{first_result['title']}' not relevant"
        )

    def test_search_results_format(self):
        """Test search results return correct format"""
        if self.searcher is None:
            self.fail("YouTubeSearcher class not found")

        # Search and verify format
        results = self.searcher.search("test", max_results=1)

        # Expected format: [{'video_id', 'title', 'thumbnail_url'}]
        self.assertIsInstance(results, list)

        if len(results) > 0:
            result = results[0]

            # Required fields
            self.assertIn('video_id', result)
            self.assertIn('title', result)
            self.assertIn('thumbnail_url', result)

            # Field types
            self.assertIsInstance(result['video_id'], str)
            self.assertIsInstance(result['title'], str)
            self.assertIsInstance(result['thumbnail_url'], str)

            # video_id should be 11 characters (YouTube standard)
            self.assertEqual(len(result['video_id']), 11)

            # thumbnail_url should be a valid URL
            self.assertTrue(result['thumbnail_url'].startswith('http'))

    def test_search_timeout_handling(self):
        """Test handling of API timeout"""
        if self.searcher is None:
            self.fail("YouTubeSearcher class not found")

        # Mock the API call to simulate timeout
        with patch.object(self.searcher, '_make_api_request') as mock_request:
            from requests.exceptions import Timeout
            mock_request.side_effect = Timeout("API request timed out")

            # Should handle timeout gracefully (return empty list or raise custom exception)
            try:
                results = self.searcher.search("test")
                # If no exception, should return empty list
                self.assertEqual(results, [])
            except Exception as e:
                # If exception, should be a custom one (not raw Timeout)
                self.assertNotIsInstance(e, Timeout)

    def test_search_rate_limit_handling(self):
        """Test handling of rate limit (10,000 requests/day)"""
        if self.searcher is None:
            self.fail("YouTubeSearcher class not found")

        # Mock API response with rate limit error (403)
        with patch.object(self.searcher, '_make_api_request') as mock_request:
            # Simulate YouTube quota exceeded error
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.json.return_value = {
                'error': {
                    'code': 403,
                    'message': 'The request cannot be completed because you have exceeded your quota.'
                }
            }
            mock_request.return_value = mock_response

            # Should handle rate limit gracefully
            try:
                results = self.searcher.search("test")
                # If no exception, should return empty list
                self.assertEqual(results, [])
            except Exception as e:
                # If exception, should be a meaningful one
                self.assertIn('quota', str(e).lower())

    def test_invalid_query_handling(self):
        """Test handling of empty/invalid queries"""
        if self.searcher is None:
            self.fail("YouTubeSearcher class not found")

        # Test empty string
        results_empty = self.searcher.search("")
        self.assertEqual(results_empty, [], "Empty query should return empty list")

        # Test None
        results_none = self.searcher.search(None)
        self.assertEqual(results_none, [], "None query should return empty list")

        # Test very long query (500+ characters)
        long_query = "a" * 600
        results_long = self.searcher.search(long_query)
        # Should either truncate or return empty, not crash
        self.assertIsInstance(results_long, list)

        # Test special characters (should not crash)
        special_query = "test <>&\"'!@#$%"
        results_special = self.searcher.search(special_query)
        self.assertIsInstance(results_special, list)


if __name__ == "__main__":
    unittest.main()
