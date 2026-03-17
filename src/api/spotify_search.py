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

from __future__ import annotations

import logging
from time import sleep
from typing import Any, Callable, Dict, List, Optional

import requests  # type: ignore[import-untyped]
import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials

from api._cache import APICache
from api._validation import validate_search_query
from utils.constants import API_CACHE_SIZE, API_DEFAULT_RESULTS, DEFAULT_ARTIST
from utils.rate_limiter import RateLimiter

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

    def __init__(self, client_id: str, client_secret: str, cache_size: int = API_CACHE_SIZE) -> None:
        """
        Initialize Spotify searcher with OAuth credentials

        Args:
            client_id (str): Spotify app client ID
            client_secret (str): Spotify app client secret
            cache_size (int): Size of LRU cache for search results (default: 128)
        """
        self._client_id: str = client_id
        self._client_secret: str = client_secret

        # Setup OAuth2 authentication (automatically refreshes tokens)
        self.auth_manager: SpotifyClientCredentials = SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )

        # Initialize Spotipy client
        self.sp: spotipy.Spotify = spotipy.Spotify(auth_manager=self.auth_manager)

        # Cache configuration
        self._cache = APICache(max_size=cache_size)

        # Retry configuration
        self._retry_attempts: int = 3
        self._retry_delay: int = 1  # seconds

        logger.info("SpotifySearcher initialized successfully")

    def search_tracks(
        self, query: str, limit: int = API_DEFAULT_RESULTS, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for tracks on Spotify

        Args:
            query: Search query (song name, artist, etc.)
            limit: Maximum results (default: 20, max: 50)
            use_cache: Use cached results if available

        Returns:
            List of track dicts with keys: track_id, title, artist, album, duration_ms
        """
        return self._search("track", query, limit, use_cache, self._parse_tracks)

    def search_albums(
        self, query: str, limit: int = API_DEFAULT_RESULTS, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for albums on Spotify

        Args:
            query: Search query (album name, artist, etc.)
            limit: Maximum results (default: 20, max: 50)
            use_cache: Use cached results if available

        Returns:
            List of album dicts with keys: album_id, name, artist, release_date, total_tracks
        """
        return self._search("album", query, limit, use_cache, self._parse_albums)

    def search_artists(
        self, query: str, limit: int = API_DEFAULT_RESULTS, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for artists on Spotify

        Args:
            query: Search query (artist name)
            limit: Maximum results (default: 20, max: 50)
            use_cache: Use cached results if available

        Returns:
            List of artist dicts with keys: artist_id, name, genres, popularity
        """
        return self._search("artist", query, limit, use_cache, self._parse_artists)

    def _search(
        self,
        entity_type: str,
        query: str,
        limit: int,
        use_cache: bool,
        parse_fn: Callable[[Dict[str, Any]], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Generic Spotify search with validation, caching, rate limiting, and retry.

        Args:
            entity_type: Spotify search type ("track", "album", "artist")
            query: Search query
            limit: Maximum results
            use_cache: Use cached results if available
            parse_fn: Function to parse raw Spotify API response
        """
        validated, limit = validate_search_query(query, limit)
        if validated is None:
            return []
        query = validated

        cache_key = f"{entity_type}:{query}"
        method_name = f"search_{entity_type}s"

        if use_cache:
            cached: Optional[List[Dict[str, Any]]] = self._cache.get(cache_key, limit)
            if cached is not None:
                return cached

        for attempt in range(self._retry_attempts):
            try:
                RateLimiter.get_instance().wait("spotify")
                results = self.sp.search(q=query, type=entity_type, limit=limit)
                parsed = parse_fn(results)

                if use_cache:
                    self._cache.put(cache_key, limit, parsed)

                logger.info(f"Search {entity_type}s '{query}' returned {len(parsed)} results")
                return parsed

            except SpotifyException as e:
                if self._should_retry_rate_limit(e, attempt):
                    continue
                return self._handle_spotify_error(e, method_name)

            except (requests.RequestException, ConnectionError) as e:
                logger.error(f"Unexpected error during Spotify {entity_type} search: {e}")
                return []

        return []

    def _parse_tracks(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Spotify track search results into standardized format

        Args:
            results (dict): Raw Spotify API response

        Returns:
            list: Parsed tracks
        """
        tracks: list[dict[str, Any]] = []

        if "tracks" not in results or "items" not in results["tracks"]:
            return tracks

        for item in results["tracks"]["items"]:
            try:
                # Extract artist name (first artist if multiple)
                artist_name = item["artists"][0]["name"] if item["artists"] else DEFAULT_ARTIST

                tracks.append(
                    {
                        "track_id": item["id"],
                        "title": item["name"],
                        "artist": artist_name,
                        "album": item["album"]["name"],
                        "duration_ms": item["duration_ms"],
                        "popularity": item.get("popularity", 0),
                        "preview_url": item.get("preview_url", None),
                    }
                )

            except KeyError as e:
                logger.warning(f"Missing key in Spotify track result: {e}")
                continue

        return tracks

    def _parse_albums(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Spotify album search results into standardized format

        Args:
            results (dict): Raw Spotify API response

        Returns:
            list: Parsed albums
        """
        albums: list[dict[str, Any]] = []

        if "albums" not in results or "items" not in results["albums"]:
            return albums

        for item in results["albums"]["items"]:
            try:
                # Extract artist name (first artist if multiple)
                artist_name = item["artists"][0]["name"] if item["artists"] else DEFAULT_ARTIST

                albums.append(
                    {
                        "album_id": item["id"],
                        "name": item["name"],
                        "artist": artist_name,
                        "release_date": item.get("release_date", "Unknown"),
                        "total_tracks": item.get("total_tracks", 0),
                        "album_type": item.get("album_type", "album"),
                    }
                )

            except KeyError as e:
                logger.warning(f"Missing key in Spotify album result: {e}")
                continue

        return albums

    def _parse_artists(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Spotify artist search results into standardized format

        Args:
            results (dict): Raw Spotify API response

        Returns:
            list: Parsed artists
        """
        artists: list[dict[str, Any]] = []

        if "artists" not in results or "items" not in results["artists"]:
            return artists

        for item in results["artists"]["items"]:
            try:
                artists.append(
                    {
                        "artist_id": item["id"],
                        "name": item["name"],
                        "genres": item.get("genres", []),
                        "popularity": item.get("popularity", 0),
                        "followers": item.get("followers", {}).get("total", 0),
                    }
                )

            except KeyError as e:
                logger.warning(f"Missing key in Spotify artist result: {e}")
                continue

        return artists

    _MAX_RETRY_AFTER: int = 60  # Cap server-supplied Retry-After to prevent DoS

    def _should_retry_rate_limit(self, error: SpotifyException, attempt: int) -> bool:
        """Check if rate-limited and sleep before retry. Returns True if should retry."""
        if error.http_status == 429 and attempt < self._retry_attempts - 1:
            retry_after = min(int(error.headers.get("Retry-After", self._retry_delay)), self._MAX_RETRY_AFTER)
            logger.warning(f"Rate limit exceeded, retrying in {retry_after}s...")
            sleep(retry_after)
            return True
        return False

    def _handle_spotify_error(self, error: SpotifyException, method_name: str) -> List[Dict[str, Any]]:
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
            retry_after = min(int(error.headers.get("Retry-After", 1)), self._MAX_RETRY_AFTER)
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

    def clear_cache(self) -> None:
        """Clear the search cache"""
        self._cache.clear()

    def get_track_details(self, track_id: str) -> Optional[Dict[str, Any]]:
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
            return track  # type: ignore[no-any-return]
        except (SpotifyException, requests.RequestException) as e:
            logger.error(f"Error getting track details: {e}")
            return None
