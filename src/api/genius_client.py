"""
Genius API Client - Feature #2
Client for fetching song lyrics from Genius.com API

Features:
- Search lyrics by title and artist
- In-memory caching to avoid repeated API calls
- Error handling for API failures
- Case-insensitive cache lookups

API Documentation: https://docs.genius.com/

Created: November 17, 2025
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GeniusClient:
    """
    Client for Genius API lyrics fetching

    Usage:
        client = GeniusClient("your_access_token")
        lyrics = client.search_lyrics("Bohemian Rhapsody", "Queen")
        if lyrics:
            print(lyrics)
    """

    def __init__(self, access_token: str):
        """
        Initialize Genius API client

        Args:
            access_token: Genius API Client Access Token

        Raises:
            ValueError: If access_token is None or empty
        """
        if not access_token or not access_token.strip():
            raise ValueError("Genius API access token is required")

        self.access_token = access_token.strip()
        self._cache = {}  # {(title_lower, artist_lower): lyrics}

        # Initialize lyricsgenius
        try:
            import lyricsgenius
            self.genius = lyricsgenius.Genius(self.access_token)
            self.genius.verbose = False  # Disable console output
            self.genius.remove_section_headers = True  # Clean lyrics
            self.genius.timeout = 10  # 10 second timeout to prevent freezing
            logger.info("GeniusClient initialized successfully")
        except ImportError:
            logger.error("lyricsgenius library not installed - run: pip install lyricsgenius")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Genius API: {e}")
            raise

    def search_lyrics(self, title: str, artist: str) -> Optional[str]:
        """
        Search for song lyrics on Genius

        Args:
            title: Song title
            artist: Artist name

        Returns:
            Lyrics text if found, None otherwise

        Note:
            - Results are cached in memory (case-insensitive)
            - Returns None on API errors (logged)
            - Empty title/artist returns None
        """
        # Validate input
        if not title or not title.strip():
            logger.warning("Empty title provided")
            return None

        if not artist or not artist.strip():
            logger.warning("Empty artist provided")
            return None

        # Normalize for cache lookup (case-insensitive)
        title_normalized = title.strip().lower()
        artist_normalized = artist.strip().lower()
        cache_key = (title_normalized, artist_normalized)

        # Check cache first
        if cache_key in self._cache:
            logger.debug(f"Lyrics found in cache: {title} - {artist}")
            return self._cache[cache_key]

        # Search Genius API
        try:
            logger.info(f"Searching Genius for: {title} - {artist}")
            song = self.genius.search_song(title, artist)

            if song and song.lyrics:
                lyrics = song.lyrics
                logger.info(f"Lyrics found ({len(lyrics)} chars): {title} - {artist}")

                # Cache for future requests
                self._cache[cache_key] = lyrics
                return lyrics
            else:
                logger.warning(f"Lyrics not found: {title} - {artist}")
                return None

        except Exception as e:
            logger.error(f"Genius API error for '{title} - {artist}': {e}")
            return None

    def clear_cache(self):
        """Clear the lyrics cache"""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared lyrics cache ({cache_size} entries)")

    def get_cache_size(self) -> int:
        """
        Get number of cached lyrics

        Returns:
            Number of songs in cache
        """
        return len(self._cache)
