"""
Tests for Genius API Client - Feature #2
TDD Phase: RED (tests written before implementation)

Created: November 17, 2025
"""

import sys
from unittest.mock import MagicMock

import pytest
import requests


class TestGeniusClient:
    """Test Genius API client functionality"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.test_token = "test_genius_token_12345"
        self.test_title = "Bohemian Rhapsody"
        self.test_artist = "Queen"
        self.test_lyrics = "Is this the real life?\nIs this just fantasy?"

        # Mock lyricsgenius module in sys.modules BEFORE importing GeniusClient.
        # The real lyricsgenius is not installed; the import happens inside
        # __init__(), so we must pre-populate sys.modules so that
        # `import lyricsgenius` inside __init__ resolves to our mock.
        self.mock_lyricsgenius = MagicMock()
        self.mock_genius_instance = MagicMock()
        self.mock_lyricsgenius.Genius.return_value = self.mock_genius_instance
        sys.modules["lyricsgenius"] = self.mock_lyricsgenius

        # Force reimport of GeniusClient so it picks up the mocked module.
        for key in list(sys.modules.keys()):
            if key in ("api.genius_client", "src.api.genius_client"):
                del sys.modules[key]

        yield

        # Remove the lyricsgenius mock from sys.modules after each test.
        sys.modules.pop("lyricsgenius", None)
        for key in list(sys.modules.keys()):
            if key in ("api.genius_client", "src.api.genius_client"):
                del sys.modules[key]

    # ------------------------------------------------------------------
    # Helper: import GeniusClient (handles both PYTHONPATH layouts)
    # ------------------------------------------------------------------

    def _get_client_class(self):
        try:
            from api.genius_client import GeniusClient

            return GeniusClient
        except ImportError:
            from src.api.genius_client import GeniusClient

            return GeniusClient

    def test_01_client_initialization_with_token(self):
        """GeniusClient should initialize with valid token"""
        GeniusClient = self._get_client_class()

        client = GeniusClient(self.test_token)

        assert client is not None
        assert client._access_token == self.test_token
        assert client._cache is not None
        assert len(client._cache) == 0

    def test_02_client_initialization_without_token(self):
        """GeniusClient should raise error without token"""
        GeniusClient = self._get_client_class()

        with pytest.raises(ValueError):
            GeniusClient(None)

        with pytest.raises(ValueError):
            GeniusClient("")

    def test_03_search_lyrics_success(self):
        """Should return lyrics for valid song"""
        GeniusClient = self._get_client_class()

        mock_song = MagicMock()
        mock_song.lyrics = self.test_lyrics
        self.mock_genius_instance.search_song.return_value = mock_song

        client = GeniusClient(self.test_token)
        result = client.search_lyrics(self.test_title, self.test_artist)

        assert result == self.test_lyrics
        self.mock_genius_instance.search_song.assert_called_once_with(self.test_title, self.test_artist)

    def test_04_search_lyrics_not_found(self):
        """Should return None when lyrics not found"""
        GeniusClient = self._get_client_class()

        self.mock_genius_instance.search_song.return_value = None

        client = GeniusClient(self.test_token)
        result = client.search_lyrics("NonexistentSong", "UnknownArtist")

        assert result is None

    def test_05_search_lyrics_api_error(self):
        """Should handle API errors gracefully"""
        GeniusClient = self._get_client_class()

        # Use a RequestException subclass — that is what search_lyrics explicitly catches.
        self.mock_genius_instance.search_song.side_effect = requests.exceptions.ConnectionError("API Error")

        client = GeniusClient(self.test_token)
        result = client.search_lyrics(self.test_title, self.test_artist)

        assert result is None

    def test_06_cache_lyrics(self):
        """Should cache lyrics to avoid repeated API calls"""
        GeniusClient = self._get_client_class()

        mock_song = MagicMock()
        mock_song.lyrics = self.test_lyrics
        self.mock_genius_instance.search_song.return_value = mock_song

        client = GeniusClient(self.test_token)

        # First call - should hit API
        result1 = client.search_lyrics(self.test_title, self.test_artist)
        assert result1 == self.test_lyrics
        assert self.mock_genius_instance.search_song.call_count == 1

        # Second call - should use cache
        result2 = client.search_lyrics(self.test_title, self.test_artist)
        assert result2 == self.test_lyrics
        assert self.mock_genius_instance.search_song.call_count == 1  # Still 1 (cached)

    def test_07_cache_case_insensitive(self):
        """Cache should be case-insensitive"""
        GeniusClient = self._get_client_class()

        mock_song = MagicMock()
        mock_song.lyrics = self.test_lyrics
        self.mock_genius_instance.search_song.return_value = mock_song

        client = GeniusClient(self.test_token)

        # First call with lowercase
        result1 = client.search_lyrics("bohemian rhapsody", "queen")
        assert result1 == self.test_lyrics

        # Second call with different case - should use cache
        result2 = client.search_lyrics("Bohemian Rhapsody", "QUEEN")
        assert result2 == self.test_lyrics
        assert self.mock_genius_instance.search_song.call_count == 1  # Cached

    def test_08_empty_title_or_artist(self):
        """Should handle empty title or artist"""
        GeniusClient = self._get_client_class()

        client = GeniusClient(self.test_token)

        # Empty title
        result1 = client.search_lyrics("", self.test_artist)
        assert result1 is None

        # Empty artist
        result2 = client.search_lyrics(self.test_title, "")
        assert result2 is None

        # Both empty
        result3 = client.search_lyrics("", "")
        assert result3 is None

    def test_09_clear_cache(self):
        """Should be able to clear cache"""
        GeniusClient = self._get_client_class()

        mock_song = MagicMock()
        mock_song.lyrics = self.test_lyrics
        self.mock_genius_instance.search_song.return_value = mock_song

        client = GeniusClient(self.test_token)

        # Search and cache
        client.search_lyrics(self.test_title, self.test_artist)
        assert len(client._cache) == 1

        # Clear cache
        client.clear_cache()
        assert len(client._cache) == 0

        # Search again - should hit API
        client.search_lyrics(self.test_title, self.test_artist)
        assert self.mock_genius_instance.search_song.call_count == 2

    def test_10_song_without_lyrics(self):
        """Should handle songs that exist but have no lyrics"""
        GeniusClient = self._get_client_class()

        mock_song = MagicMock()
        mock_song.lyrics = None  # Song exists but no lyrics
        self.mock_genius_instance.search_song.return_value = mock_song

        client = GeniusClient(self.test_token)
        result = client.search_lyrics(self.test_title, self.test_artist)

        assert result is None
