"""
YouTube Search Integration - Phase 4.1
Uses YouTube Data API v3 for searching videos

Optimizations:
- LRU cache for search results (avoid duplicate API calls)
- Exponential backoff for rate limits
- Request timeout handling
- Comprehensive error logging

Security (Pre-Phase 5 Hardening):
- Input sanitization to prevent injection attacks
"""

from __future__ import annotations

import logging
from time import sleep
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import Error as GoogleApiError
from googleapiclient.errors import HttpError
from requests.exceptions import ConnectionError as RequestsConnectionError  # type: ignore[import-untyped]
from requests.exceptions import Timeout

from api._cache import APICache
from utils.constants import API_CACHE_SIZE, API_DEFAULT_RESULTS, API_MAX_RESULTS, API_QUERY_MAX_LENGTH
from utils.input_sanitizer import sanitize_query
from utils.rate_limiter import RateLimiter

# Setup logger
logger = logging.getLogger(__name__)


class YouTubeSearcher:
    """
    YouTube Data API v3 integration for searching music videos

    Usage:
        searcher = YouTubeSearcher(api_key="YOUR_API_KEY")
        results = searcher.search("The Beatles", max_results=10)
    """

    def __init__(self, api_key: str, cache_size: int = API_CACHE_SIZE) -> None:
        """
        Initialize YouTube searcher with API key

        Args:
            api_key (str): YouTube Data API v3 key
            cache_size (int): Size of LRU cache for search results (default: 128)
        """
        self.api_key: str = api_key
        self.youtube: Any = build("youtube", "v3", developerKey=api_key)
        self._cache = APICache(max_size=cache_size)
        self._retry_attempts: int = 3
        self._retry_delay: int = 1  # seconds

    def search(
        self, query: str, max_results: int = API_DEFAULT_RESULTS, use_cache: bool = True
    ) -> List[Dict[str, str]]:
        """
        Search for videos on YouTube with caching and retry logic

        Args:
            query (str): Search query (artist, song, etc.)
            max_results (int): Maximum number of results (default: 20, max: 50)
            use_cache (bool): Use cached results if available (default: True)

        Returns:
            list: List of dicts with format:
                  [{'video_id': str, 'title': str, 'thumbnail_url': str}]

        Examples:
            >>> searcher.search("Bohemian Rhapsody Queen")
            [{'video_id': 'fJ9rUzIMcZQ', 'title': 'Queen - Bohemian Rhapsody', ...}]
        """
        # Input validation
        if not query or query is None:
            logger.warning("Empty or None query received")
            return []

        # Sanitize query (remove injection attempts, control chars, truncate)
        query = sanitize_query(query, max_length=API_QUERY_MAX_LENGTH)

        if not query:
            logger.warning("Query became empty after sanitization")
            return []

        # Limit max_results to YouTube API maximum
        max_results = min(max_results, API_MAX_RESULTS)

        # Check cache first
        if use_cache:
            cached: Optional[List[Dict[str, str]]] = self._cache.get(query, max_results)
            if cached is not None:
                return cached

        # Make API request with retry logic
        for attempt in range(self._retry_attempts):
            try:
                # Apply rate limiting before API call
                RateLimiter.get_instance().wait("youtube")

                # Make API request
                response = self._make_api_request(query, max_results)

                # Parse response
                results = self._parse_search_results(response)

                # Store in cache
                if use_cache:
                    self._cache.put(query, max_results, results)

                logger.info(f"Search '{query}' returned {len(results)} results")
                return results

            except HttpError as e:
                # Handle YouTube API errors
                if e.resp.status == 403:
                    error_msg = str(e)
                    if "quota" in error_msg.lower():
                        logger.error("YouTube API quota exceeded - cannot retry")
                        return []
                    else:
                        logger.error(f"YouTube API 403 error: {error_msg}")
                        # Retry with exponential backoff
                        if attempt < self._retry_attempts - 1:
                            delay = self._retry_delay * (2**attempt)
                            logger.info(f"Retrying in {delay}s... (attempt {attempt + 1}/{self._retry_attempts})")
                            sleep(delay)
                            continue
                        else:
                            return []
                elif e.resp.status == 400:
                    logger.error(f"YouTube API bad request: {e}")
                    return []  # Don't retry on bad requests
                else:
                    logger.error(f"YouTube API error ({e.resp.status}): {e}")
                    # Retry for other errors
                    if attempt < self._retry_attempts - 1:
                        delay = self._retry_delay * (2**attempt)
                        sleep(delay)
                        continue
                    else:
                        return []

            except Timeout:
                # Handle timeout with retry
                logger.warning(f"YouTube API request timed out (attempt {attempt + 1}/{self._retry_attempts})")
                if attempt < self._retry_attempts - 1:
                    sleep(self._retry_delay)
                    continue
                else:
                    logger.error("YouTube API request timed out after all retries")
                    return []

            except (GoogleApiError, RequestsConnectionError, OSError) as e:
                # Handle any other errors
                logger.error(f"Unexpected error during YouTube search: {e}")
                return []

        return []

    def _make_api_request(self, query: str, max_results: int) -> Dict[str, Any]:
        """
        Make actual API request to YouTube

        Args:
            query (str): Search query
            max_results (int): Max results

        Returns:
            dict: YouTube API response

        Note: This method is separated to allow mocking in tests
        """
        request = self.youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results,
            videoCategoryId="10",  # Music category
            videoDefinition="any",
            relevanceLanguage="en",
        )

        return request.execute()  # type: ignore[no-any-return]

    def _parse_search_results(self, response: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Parse YouTube API response into standardized format

        Args:
            response (dict): Raw YouTube API response

        Returns:
            list: Parsed results [{'video_id', 'title', 'thumbnail_url'}]
        """
        results: list[dict[str, Any]] = []

        if "items" not in response:
            return results

        for item in response["items"]:
            try:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]

                # Get best thumbnail available
                thumbnails = item["snippet"]["thumbnails"]
                if "high" in thumbnails:
                    thumbnail_url = thumbnails["high"]["url"]
                elif "medium" in thumbnails:
                    thumbnail_url = thumbnails["medium"]["url"]
                else:
                    thumbnail_url = thumbnails["default"]["url"]

                results.append({"video_id": video_id, "title": title, "thumbnail_url": thumbnail_url})

            except KeyError as e:
                logger.warning(f"Missing key in YouTube result: {e}")
                continue

        return results

    def clear_cache(self) -> None:
        """Clear the search cache"""
        self._cache.clear()

    def get_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed metadata for a specific video

        Args:
            video_id (str): YouTube video ID (11 characters)

        Returns:
            dict: Video metadata (title, duration, description, etc.)

        Note: This method will be used in future features
        """
        try:
            request = self.youtube.videos().list(part="snippet,contentDetails,statistics", id=video_id)

            response = request.execute()

            if "items" in response and len(response["items"]) > 0:
                return response["items"][0]  # type: ignore[no-any-return]
            else:
                return None

        except (HttpError, RequestsConnectionError, OSError) as e:
            logger.error(f"Error getting video metadata: {e}")
            return None
