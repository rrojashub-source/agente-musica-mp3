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
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from requests.exceptions import Timeout
from functools import lru_cache
from time import sleep
import logging
import hashlib
from src.utils.input_sanitizer import sanitize_query

# Setup logger
logger = logging.getLogger(__name__)


class YouTubeSearcher:
    """
    YouTube Data API v3 integration for searching music videos

    Usage:
        searcher = YouTubeSearcher(api_key="YOUR_API_KEY")
        results = searcher.search("The Beatles", max_results=10)
    """

    def __init__(self, api_key, cache_size=128):
        """
        Initialize YouTube searcher with API key

        Args:
            api_key (str): YouTube Data API v3 key
            cache_size (int): Size of LRU cache for search results (default: 128)
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self._cache = {}
        self._cache_size = cache_size
        self._retry_attempts = 3
        self._retry_delay = 1  # seconds

    def search(self, query, max_results=20, use_cache=True):
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
        original_query = query
        query = sanitize_query(query, max_length=500)

        if not query:
            logger.warning("Query became empty after sanitization")
            return []

        # Limit max_results to YouTube API maximum
        max_results = min(max_results, 50)

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(query, max_results)
            if cache_key in self._cache:
                logger.info(f"Cache hit for query: '{query}'")
                return self._cache[cache_key]

        # Make API request with retry logic
        for attempt in range(self._retry_attempts):
            try:
                # Make API request
                response = self._make_api_request(query, max_results)

                # Parse response
                results = self._parse_search_results(response)

                # Store in cache
                if use_cache:
                    self._add_to_cache(query, max_results, results)

                logger.info(f"Search '{query}' returned {len(results)} results")
                return results

            except HttpError as e:
                # Handle YouTube API errors
                if e.resp.status == 403:
                    error_msg = str(e)
                    if 'quota' in error_msg.lower():
                        logger.error("YouTube API quota exceeded - cannot retry")
                        return []
                    else:
                        logger.error(f"YouTube API 403 error: {error_msg}")
                        # Retry with exponential backoff
                        if attempt < self._retry_attempts - 1:
                            delay = self._retry_delay * (2 ** attempt)
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
                        delay = self._retry_delay * (2 ** attempt)
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

            except Exception as e:
                # Handle any other errors
                logger.error(f"Unexpected error during YouTube search: {e}")
                return []

        return []

    def _make_api_request(self, query, max_results):
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
            part='snippet',
            q=query,
            type='video',
            maxResults=max_results,
            videoCategoryId='10',  # Music category
            videoDefinition='any',
            relevanceLanguage='en'
        )

        return request.execute()

    def _parse_search_results(self, response):
        """
        Parse YouTube API response into standardized format

        Args:
            response (dict): Raw YouTube API response

        Returns:
            list: Parsed results [{'video_id', 'title', 'thumbnail_url'}]
        """
        results = []

        if 'items' not in response:
            return results

        for item in response['items']:
            try:
                video_id = item['id']['videoId']
                title = item['snippet']['title']

                # Get best thumbnail available
                thumbnails = item['snippet']['thumbnails']
                if 'high' in thumbnails:
                    thumbnail_url = thumbnails['high']['url']
                elif 'medium' in thumbnails:
                    thumbnail_url = thumbnails['medium']['url']
                else:
                    thumbnail_url = thumbnails['default']['url']

                results.append({
                    'video_id': video_id,
                    'title': title,
                    'thumbnail_url': thumbnail_url
                })

            except KeyError as e:
                logger.warning(f"Missing key in YouTube result: {e}")
                continue

        return results

    def _get_cache_key(self, query, max_results):
        """
        Generate cache key for query

        Args:
            query (str): Search query
            max_results (int): Max results

        Returns:
            str: Cache key (hash)
        """
        key_str = f"{query.lower()}:{max_results}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _add_to_cache(self, query, max_results, results):
        """
        Add results to cache with LRU eviction

        Args:
            query (str): Search query
            max_results (int): Max results
            results (list): Search results to cache
        """
        cache_key = self._get_cache_key(query, max_results)

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
        logger.info("Search cache cleared")

    def get_video_metadata(self, video_id):
        """
        Get detailed metadata for a specific video

        Args:
            video_id (str): YouTube video ID (11 characters)

        Returns:
            dict: Video metadata (title, duration, description, etc.)

        Note: This method will be used in future features
        """
        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            )

            response = request.execute()

            if 'items' in response and len(response['items']) > 0:
                return response['items'][0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return None
