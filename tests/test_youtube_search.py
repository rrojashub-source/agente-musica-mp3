"""
Tests for YouTube Search Integration (Phase 4.1)
TDD: Write tests FIRST, then implement src/api/youtube_search.py
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestYouTubeSearch:
    """Test YouTube Data API v3 integration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        # Load test API key from secrets
        secrets_path = Path.home() / ".claude" / "secrets" / "credentials.json"
        with open(secrets_path) as f:
            secrets = json.load(f)

        self.test_api_key = secrets["apis"]["youtube"]["api_key"]

        # Import the class we're testing (will fail initially - that's expected in TDD Red phase)
        try:
            from src.api.youtube_search import YouTubeSearcher

            self.searcher = YouTubeSearcher(self.test_api_key)
        except ImportError:
            self.searcher = None  # Expected to fail initially

    def test_youtube_api_connection(self):
        """Test successful connection to YouTube API"""
        if self.searcher is None:
            pytest.fail("YouTubeSearcher class not found - implement src/api/youtube_search.py")

        # Test that the searcher was initialized correctly
        assert self.searcher is not None
        assert self.searcher.api_key == self.test_api_key

    def test_search_by_artist(self):
        """Test search by artist name"""
        if self.searcher is None:
            pytest.fail("YouTubeSearcher class not found")

        # Search for "The Beatles" (use_cache=False ensures fresh API call for test reliability)
        results = self.searcher.search("The Beatles", max_results=5, use_cache=False)

        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0
        assert len(results) <= 5

        # Verify each result has required fields
        for result in results:
            assert "video_id" in result
            assert "title" in result
            assert "thumbnail_url" in result

            # Verify video_id is not empty
            assert result["video_id"]
            assert result["title"]

    def test_search_by_song(self):
        """Test search by song title"""
        if self.searcher is None:
            pytest.fail("YouTubeSearcher class not found")

        # Search for specific song
        results = self.searcher.search("Bohemian Rhapsody Queen", max_results=3)

        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0

        # First result should be relevant (contain "Bohemian" or "Queen")
        first_result = results[0]
        title_lower = first_result["title"].lower()
        assert (
            "bohemian" in title_lower or "queen" in title_lower
        ), f"First result title '{first_result['title']}' not relevant"

    def test_search_results_format(self):
        """Test search results return correct format"""
        if self.searcher is None:
            pytest.fail("YouTubeSearcher class not found")

        # Search and verify format
        results = self.searcher.search("test", max_results=1)

        # Expected format: [{'video_id', 'title', 'thumbnail_url'}]
        assert isinstance(results, list)

        if len(results) > 0:
            result = results[0]

            # Required fields
            assert "video_id" in result
            assert "title" in result
            assert "thumbnail_url" in result

            # Field types
            assert isinstance(result["video_id"], str)
            assert isinstance(result["title"], str)
            assert isinstance(result["thumbnail_url"], str)

            # video_id should be 11 characters (YouTube standard)
            assert len(result["video_id"]) == 11

            # thumbnail_url should be a valid URL
            assert result["thumbnail_url"].startswith("http")

    def test_search_timeout_handling(self):
        """Test handling of API timeout"""
        if self.searcher is None:
            pytest.fail("YouTubeSearcher class not found")

        # Mock the API call to simulate timeout
        with patch.object(self.searcher, "_make_api_request") as mock_request:
            from requests.exceptions import Timeout

            mock_request.side_effect = Timeout("API request timed out")

            # Should handle timeout gracefully (return empty list or raise custom exception)
            try:
                results = self.searcher.search("test")
                # If no exception, should return empty list
                assert results == []
            except Exception as e:
                # If exception, should be a custom one (not raw Timeout)
                assert not isinstance(e, Timeout)

    def test_search_rate_limit_handling(self):
        """Test handling of rate limit (10,000 requests/day)"""
        if self.searcher is None:
            pytest.fail("YouTubeSearcher class not found")

        # Mock API response with rate limit error (403)
        with patch.object(self.searcher, "_make_api_request") as mock_request:
            # Simulate YouTube quota exceeded error
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.json.return_value = {
                "error": {
                    "code": 403,
                    "message": "The request cannot be completed because you have exceeded your quota.",
                }
            }
            mock_request.return_value = mock_response

            # Should handle rate limit gracefully
            try:
                results = self.searcher.search("test")
                # If no exception, should return empty list
                assert results == []
            except Exception as e:
                # If exception, should be a meaningful one
                assert "quota" in str(e).lower()

    def test_invalid_query_handling(self):
        """Test handling of empty/invalid queries"""
        if self.searcher is None:
            pytest.fail("YouTubeSearcher class not found")

        # Test empty string
        results_empty = self.searcher.search("")
        assert results_empty == [], "Empty query should return empty list"

        # Test None
        results_none = self.searcher.search(None)
        assert results_none == [], "None query should return empty list"

        # Test very long query (500+ characters)
        long_query = "a" * 600
        results_long = self.searcher.search(long_query)
        # Should either truncate or return empty, not crash
        assert isinstance(results_long, list)

        # Test special characters (should not crash)
        special_query = "test <>&\"'!@#$%"
        results_special = self.searcher.search(special_query)
        assert isinstance(results_special, list)
