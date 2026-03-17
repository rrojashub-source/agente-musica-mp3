"""
Rate Limiter Utility - Phase 5
Provides rate limiting for API calls to prevent bans and quota exhaustion

Features:
- Per-service rate limits (YouTube, Spotify, MusicBrainz, Genius)
- Token bucket algorithm for smooth rate limiting
- Automatic backoff on 429 errors
- Thread-safe implementation
- Configurable limits per service

Usage:
    from utils.rate_limiter import RateLimiter, rate_limited

    # Decorator approach
    @rate_limited('youtube')
    def search_youtube(query):
        ...

    # Manual approach
    limiter = RateLimiter.get_instance()
    limiter.wait('spotify')
    # make API call
"""

import logging
import threading
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

from utils.constants import API_MAX_RETRIES

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm

    Default limits (requests per second):
    - YouTube: 10 req/s (quota is daily, but burst protection)
    - Spotify: 30 req/s (official limit is 100, we're conservative)
    - MusicBrainz: 1 req/s (strict limit)
    - Genius: 5 req/s (undocumented, conservative)
    - AcoustID: 3 req/s (free tier limit)
    """

    _instance: Optional["RateLimiter"] = None
    _lock = threading.Lock()

    # Default rate limits (requests per second)
    DEFAULT_LIMITS: Dict[str, float] = {
        "youtube": 10.0,  # 10 requests/second
        "spotify": 30.0,  # 30 requests/second
        "musicbrainz": 1.0,  # 1 request/second (strict!)
        "genius": 5.0,  # 5 requests/second
        "acoustid": 3.0,  # 3 requests/second
        "default": 5.0,  # fallback
    }

    # Burst allowance (max tokens in bucket)
    DEFAULT_BURST: Dict[str, int] = {
        "youtube": 20,
        "spotify": 50,
        "musicbrainz": 2,
        "genius": 10,
        "acoustid": 5,
        "default": 10,
    }

    def __init__(self) -> None:
        """Initialize rate limiter (use get_instance() for singleton)"""
        self._buckets: Dict[str, float] = {}  # Current tokens per service
        self._last_update: Dict[str, float] = {}  # Last update time per service
        self._limits: Dict[str, float] = self.DEFAULT_LIMITS.copy()
        self._burst: Dict[str, int] = self.DEFAULT_BURST.copy()
        self._service_locks: Dict[str, threading.Lock] = {}

    @classmethod
    def get_instance(cls) -> "RateLimiter":
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _get_service_lock(self, service: str) -> threading.Lock:
        """Get or create lock for service"""
        if service not in self._service_locks:
            with self._lock:
                if service not in self._service_locks:
                    self._service_locks[service] = threading.Lock()
        return self._service_locks[service]

    def _refill_tokens(self, service: str) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()

        if service not in self._last_update:
            self._last_update[service] = now
            self._buckets[service] = float(self._burst.get(service, self.DEFAULT_BURST["default"]))
            return

        elapsed = now - self._last_update[service]
        rate = self._limits.get(service, self.DEFAULT_LIMITS["default"])
        max_tokens = float(self._burst.get(service, self.DEFAULT_BURST["default"]))

        # Add tokens based on time elapsed
        new_tokens = self._buckets.get(service, max_tokens) + (elapsed * rate)
        self._buckets[service] = min(new_tokens, max_tokens)
        self._last_update[service] = now

    def wait(self, service: str, tokens: int = 1) -> float:
        """
        Wait until rate limit allows request

        Args:
            service: Service name (youtube, spotify, etc.)
            tokens: Number of tokens to consume (default: 1)

        Returns:
            float: Time waited in seconds
        """
        service = service.lower()
        lock = self._get_service_lock(service)
        wait_time = 0.0

        with lock:
            self._refill_tokens(service)

            while self._buckets.get(service, 0) < tokens:
                # Calculate wait time
                rate = self._limits.get(service, self.DEFAULT_LIMITS["default"])
                needed = tokens - self._buckets.get(service, 0)
                sleep_time = needed / rate

                logger.debug(f"Rate limit: waiting {sleep_time:.2f}s for {service}")
                time.sleep(sleep_time)
                wait_time += sleep_time

                self._refill_tokens(service)

            # Consume tokens
            self._buckets[service] = self._buckets.get(service, 0) - tokens

        if wait_time > 0:
            logger.info(f"Rate limiter: waited {wait_time:.2f}s for {service}")

        return wait_time

    def try_acquire(self, service: str, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting

        Args:
            service: Service name
            tokens: Number of tokens to consume

        Returns:
            bool: True if tokens acquired, False if rate limited
        """
        service = service.lower()
        lock = self._get_service_lock(service)

        with lock:
            self._refill_tokens(service)

            if self._buckets.get(service, 0) >= tokens:
                self._buckets[service] = self._buckets.get(service, 0) - tokens
                return True

        return False

    def set_limit(self, service: str, requests_per_second: float, burst: Optional[int] = None) -> None:
        """
        Set custom rate limit for service

        Args:
            service: Service name
            requests_per_second: Maximum requests per second
            burst: Maximum burst size (default: 2x rate)
        """
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        service = service.lower()
        # Clamp to safe range to prevent bypass or DoS
        requests_per_second = max(0.01, min(requests_per_second, 100.0))
        self._limits[service] = requests_per_second
        self._burst[service] = burst or int(requests_per_second * 2)
        logger.info(f"Rate limit set: {service} = {requests_per_second} req/s, burst={self._burst[service]}")

    def get_stats(self, service: str) -> Dict[str, Any]:
        """Get rate limiter stats for service"""
        service = service.lower()
        self._refill_tokens(service)

        return {
            "service": service,
            "tokens_available": self._buckets.get(service, 0),
            "max_tokens": self._burst.get(service, self.DEFAULT_BURST["default"]),
            "rate_limit": self._limits.get(service, self.DEFAULT_LIMITS["default"]),
        }

    def reset(self, service: Optional[str] = None) -> None:
        """Reset rate limiter (for testing or error recovery)"""
        if service:
            service = service.lower()
            self._buckets[service] = float(self._burst.get(service, self.DEFAULT_BURST["default"]))
            self._last_update[service] = time.time()
        else:
            self._buckets.clear()
            self._last_update.clear()


def rate_limited(service: str, tokens: int = 1) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to rate limit function calls

    Args:
        service: Service name (youtube, spotify, musicbrainz, genius, acoustid)
        tokens: Number of tokens to consume per call (default: 1)

    Usage:
        @rate_limited('youtube')
        def search_youtube(query):
            ...

        @rate_limited('musicbrainz', tokens=2)  # Heavy operation
        def fetch_full_metadata(mbid):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            limiter = RateLimiter.get_instance()
            limiter.wait(service, tokens)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def with_retry_on_rate_limit(
    service: str, max_retries: int = API_MAX_RETRIES, base_delay: float = 1.0
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to retry on rate limit errors (429)

    Args:
        service: Service name for logging
        max_retries: Maximum retry attempts
        base_delay: Base delay for exponential backoff

    Usage:
        @with_retry_on_rate_limit('youtube', max_retries=3)
        def search_youtube(query):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # retry decorator - must catch all to evaluate retry logic
                    error_str = str(e).lower()

                    # Check if it's a rate limit error
                    is_rate_limit = any(
                        x in error_str
                        for x in ["429", "rate limit", "quota", "too many requests", "ratelimit", "throttl"]
                    )

                    if is_rate_limit and attempt < max_retries:
                        delay = base_delay * (2**attempt)  # Exponential backoff
                        logger.warning(
                            f"{service} rate limit hit, retry {attempt + 1}/{max_retries} " f"after {delay:.1f}s"
                        )
                        time.sleep(delay)
                        last_exception = e
                    else:
                        raise

            # If we exhausted retries, raise last exception
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


# Convenience functions for common services
def youtube_rate_limit() -> None:
    """Wait for YouTube rate limit"""
    RateLimiter.get_instance().wait("youtube")


def spotify_rate_limit() -> None:
    """Wait for Spotify rate limit"""
    RateLimiter.get_instance().wait("spotify")


def musicbrainz_rate_limit() -> None:
    """Wait for MusicBrainz rate limit"""
    RateLimiter.get_instance().wait("musicbrainz")


def genius_rate_limit() -> None:
    """Wait for Genius rate limit"""
    RateLimiter.get_instance().wait("genius")


def acoustid_rate_limit() -> None:
    """Wait for AcoustID rate limit"""
    RateLimiter.get_instance().wait("acoustid")
