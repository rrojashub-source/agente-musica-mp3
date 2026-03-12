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
import re
import requests
from typing import Optional
from utils.rate_limiter import RateLimiter
from utils.constants import API_DEFAULT_TIMEOUT

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
            self.genius.timeout = API_DEFAULT_TIMEOUT
            logger.info("GeniusClient initialized successfully")
        except ImportError:
            logger.error("lyricsgenius library not installed - run: pip install lyricsgenius")
            raise
        except (ConnectionError, OSError, RuntimeError) as e:
            logger.error(f"Failed to initialize Genius API: {e}")
            raise

    @staticmethod
    def _clean_title_for_search(title: str, artist: str) -> str:
        """Clean YouTube-style titles for better Genius search results.

        Removes artist prefix, video type suffixes, and other noise that
        causes lyricsgenius to match editorial pages instead of lyrics.

        Examples:
            "Michael Jackson - The Girl Is Mine (Audio)" -> "The Girl Is Mine"
            "Queen - Somebody To Love (Official Video)" -> "Somebody To Love"
            "Paradise City (Official Music Video)" -> "Paradise City"
        """
        cleaned = title.strip()

        # Remove "Artist - " prefix if title starts with artist name
        if artist:
            artist_clean = artist.strip()
            # Build list of artist name variants to try
            artist_variants = [artist_clean]
            # Also try without common channel suffixes
            for suffix in [' Official', ' Music', ' VEVO', ' Records', ' Band']:
                stripped = re.sub(re.escape(suffix) + '$', '', artist_clean, flags=re.IGNORECASE).strip()
                if stripped and stripped != artist_clean:
                    artist_variants.append(stripped)

            for variant in artist_variants:
                prefix_pattern = re.compile(
                    r'^' + re.escape(variant) + r'\s*[-–—:]\s*',
                    re.IGNORECASE
                )
                new_cleaned = prefix_pattern.sub('', cleaned)
                if new_cleaned != cleaned:
                    cleaned = new_cleaned
                    break

        # Remove common YouTube suffixes in parentheses/brackets
        noise_patterns = [
            r'\s*\(Official\s*(Music\s*)?Video\)',
            r'\s*\(Official\s*Audio\)',
            r'\s*\(Audio\)',
            r'\s*\(Lyric[s]?\s*Video\)',
            r'\s*\(Visuali[zs]er\)',
            r'\s*\(Live\)',
            r'\s*\(HD\)',
            r'\s*\(HQ\)',
            r'\s*\(Remaster(ed)?\)',
            r'\s*\[Official\s*(Music\s*)?Video\]',
            r'\s*\[Official\s*Audio\]',
            r'\s*\[Audio\]',
            r'\s*\[Lyric[s]?\s*Video\]',
            r'\s*\[HD\]',
            r'\s*\[HQ\]',
            r'\s*\[Remaster(ed)?\]',
        ]
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.strip()

        if cleaned != title:
            logger.info(f"Cleaned title for Genius search: '{title}' -> '{cleaned}'")

        return cleaned if cleaned else title

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
            - YouTube-style titles are cleaned before search
        """
        # Validate input
        if not title or not title.strip():
            logger.warning("Empty title provided")
            return None

        if not artist or not artist.strip():
            logger.warning("Empty artist provided")
            return None

        # Clean YouTube-style title noise before searching
        clean_title = self._clean_title_for_search(title, artist)

        # Also clean artist (remove " - Topic" YouTube suffix)
        clean_artist = re.sub(r'\s*-\s*Topic$', '', artist.strip(), flags=re.IGNORECASE)
        # Remove "Official" suffix from artist name
        clean_artist = re.sub(r'\s+Official$', '', clean_artist, flags=re.IGNORECASE)

        # Normalize for cache lookup (case-insensitive)
        title_normalized = clean_title.strip().lower()
        artist_normalized = clean_artist.strip().lower()
        cache_key = (title_normalized, artist_normalized)

        # Check cache first
        if cache_key in self._cache:
            logger.debug(f"Lyrics found in cache: {clean_title} - {clean_artist}")
            return self._cache[cache_key]

        # Search Genius API
        try:
            # Apply rate limiting before API call
            RateLimiter.get_instance().wait('genius')

            logger.info(f"Searching Genius for: {clean_title} - {clean_artist}")
            song = self.genius.search_song(clean_title, clean_artist)

            if song and song.lyrics:
                lyrics = song.lyrics
                logger.info(f"Lyrics found ({len(lyrics)} chars): {title} - {artist}")

                # Cache for future requests
                self._cache[cache_key] = lyrics
                return lyrics
            else:
                logger.warning(f"Lyrics not found: {title} - {artist}")
                return None

        except (requests.RequestException, AttributeError, ValueError) as e:
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
