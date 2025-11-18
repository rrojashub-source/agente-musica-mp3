"""
Tests for Genius API Client - Feature #2
TDD Phase: RED (tests written before implementation)

Created: November 17, 2025
"""
import unittest
from unittest.mock import Mock, patch, MagicMock


class TestGeniusClient(unittest.TestCase):
    """Test Genius API client functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_token = "test_genius_token_12345"
        self.test_title = "Bohemian Rhapsody"
        self.test_artist = "Queen"
        self.test_lyrics = "Is this the real life?\nIs this just fantasy?"

    def test_01_client_initialization_with_token(self):
        """GeniusClient should initialize with valid token"""
        from api.genius_client import GeniusClient

        client = GeniusClient(self.test_token)

        self.assertIsNotNone(client)
        self.assertEqual(client.access_token, self.test_token)
        self.assertIsNotNone(client._cache)
        self.assertEqual(len(client._cache), 0)

    def test_02_client_initialization_without_token(self):
        """GeniusClient should raise error without token"""
        from api.genius_client import GeniusClient

        with self.assertRaises(ValueError):
            GeniusClient(None)

        with self.assertRaises(ValueError):
            GeniusClient("")

    @patch('api.genius_client.lyricsgenius.Genius')
    def test_03_search_lyrics_success(self, mock_genius_class):
        """Should return lyrics for valid song"""
        from api.genius_client import GeniusClient

        # Mock Genius API response
        mock_genius = MagicMock()
        mock_song = MagicMock()
        mock_song.lyrics = self.test_lyrics
        mock_genius.search_song.return_value = mock_song
        mock_genius_class.return_value = mock_genius

        client = GeniusClient(self.test_token)
        result = client.search_lyrics(self.test_title, self.test_artist)

        self.assertEqual(result, self.test_lyrics)
        mock_genius.search_song.assert_called_once_with(self.test_title, self.test_artist)

    @patch('api.genius_client.lyricsgenius.Genius')
    def test_04_search_lyrics_not_found(self, mock_genius_class):
        """Should return None when lyrics not found"""
        from api.genius_client import GeniusClient

        # Mock Genius API response - no results
        mock_genius = MagicMock()
        mock_genius.search_song.return_value = None
        mock_genius_class.return_value = mock_genius

        client = GeniusClient(self.test_token)
        result = client.search_lyrics("NonexistentSong", "UnknownArtist")

        self.assertIsNone(result)

    @patch('api.genius_client.lyricsgenius.Genius')
    def test_05_search_lyrics_api_error(self, mock_genius_class):
        """Should handle API errors gracefully"""
        from api.genius_client import GeniusClient

        # Mock Genius API error
        mock_genius = MagicMock()
        mock_genius.search_song.side_effect = Exception("API Error")
        mock_genius_class.return_value = mock_genius

        client = GeniusClient(self.test_token)
        result = client.search_lyrics(self.test_title, self.test_artist)

        self.assertIsNone(result)

    @patch('api.genius_client.lyricsgenius.Genius')
    def test_06_cache_lyrics(self, mock_genius_class):
        """Should cache lyrics to avoid repeated API calls"""
        from api.genius_client import GeniusClient

        # Mock Genius API response
        mock_genius = MagicMock()
        mock_song = MagicMock()
        mock_song.lyrics = self.test_lyrics
        mock_genius.search_song.return_value = mock_song
        mock_genius_class.return_value = mock_genius

        client = GeniusClient(self.test_token)

        # First call - should hit API
        result1 = client.search_lyrics(self.test_title, self.test_artist)
        self.assertEqual(result1, self.test_lyrics)
        self.assertEqual(mock_genius.search_song.call_count, 1)

        # Second call - should use cache
        result2 = client.search_lyrics(self.test_title, self.test_artist)
        self.assertEqual(result2, self.test_lyrics)
        self.assertEqual(mock_genius.search_song.call_count, 1)  # Still 1 (cached)

    @patch('api.genius_client.lyricsgenius.Genius')
    def test_07_cache_case_insensitive(self, mock_genius_class):
        """Cache should be case-insensitive"""
        from api.genius_client import GeniusClient

        # Mock Genius API response
        mock_genius = MagicMock()
        mock_song = MagicMock()
        mock_song.lyrics = self.test_lyrics
        mock_genius.search_song.return_value = mock_song
        mock_genius_class.return_value = mock_genius

        client = GeniusClient(self.test_token)

        # First call with lowercase
        result1 = client.search_lyrics("bohemian rhapsody", "queen")
        self.assertEqual(result1, self.test_lyrics)

        # Second call with different case - should use cache
        result2 = client.search_lyrics("Bohemian Rhapsody", "QUEEN")
        self.assertEqual(result2, self.test_lyrics)
        self.assertEqual(mock_genius.search_song.call_count, 1)  # Cached

    @patch('api.genius_client.lyricsgenius.Genius')
    def test_08_empty_title_or_artist(self, mock_genius_class):
        """Should handle empty title or artist"""
        from api.genius_client import GeniusClient

        mock_genius = MagicMock()
        mock_genius_class.return_value = mock_genius

        client = GeniusClient(self.test_token)

        # Empty title
        result1 = client.search_lyrics("", self.test_artist)
        self.assertIsNone(result1)

        # Empty artist
        result2 = client.search_lyrics(self.test_title, "")
        self.assertIsNone(result2)

        # Both empty
        result3 = client.search_lyrics("", "")
        self.assertIsNone(result3)

    @patch('api.genius_client.lyricsgenius.Genius')
    def test_09_clear_cache(self, mock_genius_class):
        """Should be able to clear cache"""
        from api.genius_client import GeniusClient

        # Mock Genius API response
        mock_genius = MagicMock()
        mock_song = MagicMock()
        mock_song.lyrics = self.test_lyrics
        mock_genius.search_song.return_value = mock_song
        mock_genius_class.return_value = mock_genius

        client = GeniusClient(self.test_token)

        # Search and cache
        client.search_lyrics(self.test_title, self.test_artist)
        self.assertEqual(len(client._cache), 1)

        # Clear cache
        client.clear_cache()
        self.assertEqual(len(client._cache), 0)

        # Search again - should hit API
        client.search_lyrics(self.test_title, self.test_artist)
        self.assertEqual(mock_genius.search_song.call_count, 2)

    @patch('api.genius_client.lyricsgenius.Genius')
    def test_10_song_without_lyrics(self, mock_genius_class):
        """Should handle songs that exist but have no lyrics"""
        from api.genius_client import GeniusClient

        # Mock song found but no lyrics attribute
        mock_genius = MagicMock()
        mock_song = MagicMock()
        mock_song.lyrics = None  # Song exists but no lyrics
        mock_genius.search_song.return_value = mock_song
        mock_genius_class.return_value = mock_genius

        client = GeniusClient(self.test_token)
        result = client.search_lyrics(self.test_title, self.test_artist)

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
