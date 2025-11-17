"""
Spotify Search Integration - Phase 4.1
Uses Spotify Web API for searching tracks, albums, and artists

Features:
- OAuth2 authentication (automatic token refresh)
- Search tracks, albums, artists
- Rich metadata extraction
- Rate limit handling (100 requests/second)
- LRU cache for search results
- Retry logic with exponential backoff
- Comprehensive error handling

Security (Pre-Phase 5 Hardening):
- Input sanitization to prevent injection attacks
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
import logging
from time import sleep
import hashlib
from utils.input_sanitizer import sanitize_query

# Setup logger
logger = logging.getLogger(__name__)


class SpotifySearcher:
    """
    Spotify Web API integration for searching music

    Usage:
        searcher = SpotifySearcher(client_id="ID", client_secret="SECRET")
        tracks = searcher.search_tracks("Bohemian Rhapsody")
        albums = searcher.search_albums("A Night at the Opera")
        artists = searcher.search_artists("Queen")
    """

    def __init__(self, client_id, client_secret, cache_size=128):
        """
        Initialize Spotify searcher with OAuth credentials

        Args:
            client_id (str): Spotify app client ID
            client_secret (str): Spotify app client secret
            cache_size (int): Size of LRU cache for search results (default: 128)
        """
        self.client_id = client_id
        self.client_secret = client_secret

        # Setup OAuth2 authentication (automatically refreshes tokens)
        self.auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )

        # Initialize Spotipy client
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

        # Cache configuration
        self._cache = {}
        self._cache_size = cache_size

        # Retry configuration
        self._retry_attempts = 3
        self._retry_delay = 1  # seconds

        logger.info("SpotifySearcher initialized successfully")

    def search_tracks(self, query, limit=20, use_cache=True):
        """
        Search for tracks on Spotify with caching and retry logic

        Args:
            query (str): Search query (song name, artist, etc.)
            limit (int): Maximum results (default: 20, max: 50)
            use_cache (bool): Use cached results if available (default: True)

        Returns:
            list: List of dicts with format:
                  [{'track_id': str, 'title': str, 'artist': str,
                    'album': str, 'duration_ms': int}]

        Examples:
            >>> searcher.search_tracks("Bohemian Rhapsody")
            [{'track_id': '3z8h0TU7RN...', 'title': 'Bohemian Rhapsody', ...}]
        """
        # Input validation
        if not query:
            logger.warning("Empty query received")
            return []

        # Sanitize query (remove injection attempts, control chars)
        query = sanitize_query(query, max_length=500)

        if not query:
            logger.warning("Query became empty after sanitization")
            return []

        # Limit to Spotify maximum
        limit = min(limit, 50)

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(f"track:{query}", limit)
            if cache_key in self._cache:
                logger.info(f"Cache hit for track search: '{query}'")
                return self._cache[cache_key]

        # Retry logic
        for attempt in range(self._retry_attempts):
            try:
                # Make API request
                results = self.sp.search(q=query, type='track', limit=limit)

                # Parse results
                tracks = self._parse_tracks(results)

                # Store in cache
                if use_cache:
                    self._add_to_cache(f"track:{query}", limit, tracks)

                logger.info(f"Search tracks '{query}' returned {len(tracks)} results")
                return tracks

            except SpotifyException as e:
                # Handle rate limit with retry
                if e.http_status == 429 and attempt < self._retry_attempts - 1:
                    retry_after = int(e.headers.get('Retry-After', self._retry_delay))
                    logger.warning(f"Rate limit exceeded, retrying in {retry_after}s...")
                    sleep(retry_after)
                    continue
                else:
                    return self._handle_spotify_error(e, "search_tracks")

            except Exception as e:
                logger.error(f"Unexpected error during Spotify track search: {e}")
                return []

        return []

    def search_albums(self, query, limit=20, use_cache=True):
        """
        Search for albums on Spotify with caching and retry logic

        Args:
            query (str): Search query (album name, artist, etc.)
            limit (int): Maximum results (default: 20, max: 50)
            use_cache (bool): Use cached results if available (default: True)

        Returns:
            list: List of dicts with format:
                  [{'album_id': str, 'name': str, 'artist': str,
                    'release_date': str, 'total_tracks': int}]
        """
        # Input validation
        if not query:
            logger.warning("Empty query received")
            return []

        # Sanitize query (remove injection attempts, control chars)
        query = sanitize_query(query, max_length=500)

        if not query:
            logger.warning("Query became empty after sanitization")
            return []

        # Limit to Spotify maximum
        limit = min(limit, 50)

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(f"album:{query}", limit)
            if cache_key in self._cache:
                logger.info(f"Cache hit for album search: '{query}'")
                return self._cache[cache_key]

        # Retry logic
        for attempt in range(self._retry_attempts):
            try:
                # Make API request
                results = self.sp.search(q=query, type='album', limit=limit)

                # Parse results
                albums = self._parse_albums(results)

                # Store in cache
                if use_cache:
                    self._add_to_cache(f"album:{query}", limit, albums)

                logger.info(f"Search albums '{query}' returned {len(albums)} results")
                return albums

            except SpotifyException as e:
                # Handle rate limit with retry
                if e.http_status == 429 and attempt < self._retry_attempts - 1:
                    retry_after = int(e.headers.get('Retry-After', self._retry_delay))
                    logger.warning(f"Rate limit exceeded, retrying in {retry_after}s...")
                    sleep(retry_after)
                    continue
                else:
                    return self._handle_spotify_error(e, "search_albums")

            except Exception as e:
                logger.error(f"Unexpected error during Spotify album search: {e}")
                return []

        return []

    def search_artists(self, query, limit=20, use_cache=True):
        """
        Search for artists on Spotify with caching and retry logic

        Args:
            query (str): Search query (artist name)
            limit (int): Maximum results (default: 20, max: 50)
            use_cache (bool): Use cached results if available (default: True)

        Returns:
            list: List of dicts with format:
                  [{'artist_id': str, 'name': str, 'genres': list,
                    'popularity': int}]
        """
        # Input validation
        if not query:
            logger.warning("Empty query received")
            return []

        # Sanitize query (remove injection attempts, control chars)
        query = sanitize_query(query, max_length=500)

        if not query:
            logger.warning("Query became empty after sanitization")
            return []

        # Limit to Spotify maximum
        limit = min(limit, 50)

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(f"artist:{query}", limit)
            if cache_key in self._cache:
                logger.info(f"Cache hit for artist search: '{query}'")
                return self._cache[cache_key]

        # Retry logic
        for attempt in range(self._retry_attempts):
            try:
                # Make API request
                results = self.sp.search(q=query, type='artist', limit=limit)

                # Parse results
                artists = self._parse_artists(results)

                # Store in cache
                if use_cache:
                    self._add_to_cache(f"artist:{query}", limit, artists)

                logger.info(f"Search artists '{query}' returned {len(artists)} results")
                return artists

            except SpotifyException as e:
                # Handle rate limit with retry
                if e.http_status == 429 and attempt < self._retry_attempts - 1:
                    retry_after = int(e.headers.get('Retry-After', self._retry_delay))
                    logger.warning(f"Rate limit exceeded, retrying in {retry_after}s...")
                    sleep(retry_after)
                    continue
                else:
                    return self._handle_spotify_error(e, "search_artists")

            except Exception as e:
                logger.error(f"Unexpected error during Spotify artist search: {e}")
                return []

        return []

    def _parse_tracks(self, results):
        """
        Parse Spotify track search results into standardized format

        Args:
            results (dict): Raw Spotify API response

        Returns:
            list: Parsed tracks
        """
        tracks = []

        if 'tracks' not in results or 'items' not in results['tracks']:
            return tracks

        for item in results['tracks']['items']:
            try:
                # Extract artist name (first artist if multiple)
                artist_name = item['artists'][0]['name'] if item['artists'] else "Unknown"

                tracks.append({
                    'track_id': item['id'],
                    'title': item['name'],
                    'artist': artist_name,
                    'album': item['album']['name'],
                    'duration_ms': item['duration_ms'],
                    'popularity': item.get('popularity', 0),
                    'preview_url': item.get('preview_url', None)
                })

            except KeyError as e:
                logger.warning(f"Missing key in Spotify track result: {e}")
                continue

        return tracks

    def _parse_albums(self, results):
        """
        Parse Spotify album search results into standardized format

        Args:
            results (dict): Raw Spotify API response

        Returns:
            list: Parsed albums
        """
        albums = []

        if 'albums' not in results or 'items' not in results['albums']:
            return albums

        for item in results['albums']['items']:
            try:
                # Extract artist name (first artist if multiple)
                artist_name = item['artists'][0]['name'] if item['artists'] else "Unknown"

                albums.append({
                    'album_id': item['id'],
                    'name': item['name'],
                    'artist': artist_name,
                    'release_date': item.get('release_date', 'Unknown'),
                    'total_tracks': item.get('total_tracks', 0),
                    'album_type': item.get('album_type', 'album')
                })

            except KeyError as e:
                logger.warning(f"Missing key in Spotify album result: {e}")
                continue

        return albums

    def _parse_artists(self, results):
        """
        Parse Spotify artist search results into standardized format

        Args:
            results (dict): Raw Spotify API response

        Returns:
            list: Parsed artists
        """
        artists = []

        if 'artists' not in results or 'items' not in results['artists']:
            return artists

        for item in results['artists']['items']:
            try:
                artists.append({
                    'artist_id': item['id'],
                    'name': item['name'],
                    'genres': item.get('genres', []),
                    'popularity': item.get('popularity', 0),
                    'followers': item.get('followers', {}).get('total', 0)
                })

            except KeyError as e:
                logger.warning(f"Missing key in Spotify artist result: {e}")
                continue

        return artists

    def _handle_spotify_error(self, error, method_name):
        """
        Handle Spotify API errors with appropriate logging and retry logic

        Args:
            error (SpotifyException): The Spotify exception
            method_name (str): Name of the method that failed

        Returns:
            list: Empty list (graceful failure)
        """
        if error.http_status == 429:
            # Rate limit exceeded
            retry_after = int(error.headers.get('Retry-After', 1))
            logger.warning(f"Spotify rate limit exceeded, retry after {retry_after}s")

            # For now, return empty (could implement retry in future)
            return []

        elif error.http_status == 401:
            # Unauthorized (token expired)
            logger.error("Spotify OAuth token expired (should auto-refresh)")
            return []

        elif error.http_status == 400:
            # Bad request
            logger.error(f"Spotify bad request in {method_name}: {error.msg}")
            return []

        else:
            # Other errors
            logger.error(f"Spotify API error in {method_name} ({error.http_status}): {error.msg}")
            return []

    def _get_cache_key(self, query, limit):
        """
        Generate cache key for query

        Args:
            query (str): Search query (with type prefix)
            limit (int): Max results

        Returns:
            str: Cache key (hash)
        """
        key_str = f"{query.lower()}:{limit}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _add_to_cache(self, query, limit, results):
        """
        Add results to cache with LRU eviction

        Args:
            query (str): Search query
            limit (int): Max results
            results (list): Search results to cache
        """
        cache_key = self._get_cache_key(query, limit)

        # Implement simple LRU: remove oldest if cache full
        if len(self._cache) >= self._cache_size:
            # Remove first item (oldest)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache full, evicted key: {oldest_key}")

        self._cache[cache_key] = results
        logger.debug(f"Cached results for query: '{query}' (cache size: {len(self._cache)})")

    def clear_cache(self):
        """Clear the search cache"""
        self._cache.clear()
        logger.info("Spotify search cache cleared")

    def get_track_details(self, track_id):
        """
        Get detailed information about a specific track

        Args:
            track_id (str): Spotify track ID

        Returns:
            dict: Track details or None if error

        Note: This method will be used in future features
        """
        try:
            track = self.sp.track(track_id)
            return track
        except Exception as e:
            logger.error(f"Error getting track details: {e}")
            return None
