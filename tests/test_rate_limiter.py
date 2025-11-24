"""
Tests for Rate Limiter Utility
"""
import sys
import os
import time
import threading

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from utils.rate_limiter import (
    RateLimiter, rate_limited, with_retry_on_rate_limit,
    youtube_rate_limit, spotify_rate_limit, musicbrainz_rate_limit
)


class TestRateLimiter:
    """Test suite for RateLimiter class"""

    def setup_method(self):
        """Reset rate limiter before each test"""
        RateLimiter.get_instance().reset()

    def test_singleton_pattern(self):
        """Test that RateLimiter is a singleton"""
        limiter1 = RateLimiter.get_instance()
        limiter2 = RateLimiter.get_instance()
        assert limiter1 is limiter2

    def test_default_limits(self):
        """Test default rate limits are set correctly"""
        limiter = RateLimiter.get_instance()
        assert limiter.DEFAULT_LIMITS['youtube'] == 10.0
        assert limiter.DEFAULT_LIMITS['spotify'] == 30.0
        assert limiter.DEFAULT_LIMITS['musicbrainz'] == 1.0
        assert limiter.DEFAULT_LIMITS['genius'] == 5.0
        assert limiter.DEFAULT_LIMITS['acoustid'] == 3.0

    def test_wait_immediate_if_tokens_available(self):
        """Test that wait returns immediately if tokens are available"""
        limiter = RateLimiter.get_instance()

        start = time.time()
        limiter.wait('youtube')
        elapsed = time.time() - start

        # Should be very fast (< 10ms) since tokens are available
        assert elapsed < 0.1

    def test_wait_blocks_when_rate_limited(self):
        """Test that wait blocks when rate limited"""
        limiter = RateLimiter.get_instance()

        # Set very strict limit for testing (1 req/s, burst=1)
        limiter.set_limit('test_service', 1.0, burst=1)

        # First request should be immediate
        start = time.time()
        limiter.wait('test_service')
        first_elapsed = time.time() - start
        assert first_elapsed < 0.1

        # Second request should wait ~1 second
        start = time.time()
        limiter.wait('test_service')
        second_elapsed = time.time() - start

        # Should wait approximately 1 second (with some tolerance)
        assert second_elapsed >= 0.9
        assert second_elapsed < 1.5

    def test_try_acquire_returns_false_when_limited(self):
        """Test that try_acquire returns False when rate limited"""
        limiter = RateLimiter.get_instance()
        limiter.set_limit('test_service2', 1.0, burst=1)

        # First acquire should succeed
        assert limiter.try_acquire('test_service2') is True

        # Second immediate acquire should fail
        assert limiter.try_acquire('test_service2') is False

    def test_set_custom_limit(self):
        """Test setting custom rate limits"""
        limiter = RateLimiter.get_instance()

        # Set custom limit
        limiter.set_limit('custom_api', 100.0, burst=200)

        # Verify stats
        stats = limiter.get_stats('custom_api')
        assert stats['rate_limit'] == 100.0
        assert stats['max_tokens'] == 200

    def test_get_stats(self):
        """Test getting rate limiter stats"""
        limiter = RateLimiter.get_instance()

        stats = limiter.get_stats('youtube')
        assert 'service' in stats
        assert 'tokens_available' in stats
        assert 'max_tokens' in stats
        assert 'rate_limit' in stats
        assert stats['service'] == 'youtube'

    def test_reset_specific_service(self):
        """Test resetting specific service"""
        limiter = RateLimiter.get_instance()
        limiter.set_limit('reset_test', 1.0, burst=1)

        # Consume token
        limiter.wait('reset_test')

        # Should not have tokens
        assert limiter.try_acquire('reset_test') is False

        # Reset
        limiter.reset('reset_test')

        # Should have tokens again
        assert limiter.try_acquire('reset_test') is True

    def test_case_insensitive_service_names(self):
        """Test that service names are case insensitive"""
        limiter = RateLimiter.get_instance()

        # Should all work the same
        stats1 = limiter.get_stats('YouTube')
        stats2 = limiter.get_stats('youtube')
        stats3 = limiter.get_stats('YOUTUBE')

        assert stats1['service'] == 'youtube'
        assert stats2['service'] == 'youtube'
        assert stats3['service'] == 'youtube'


class TestRateLimitedDecorator:
    """Test suite for @rate_limited decorator"""

    def setup_method(self):
        """Reset rate limiter before each test"""
        RateLimiter.get_instance().reset()

    def test_decorator_applies_rate_limit(self):
        """Test that decorator applies rate limiting"""
        limiter = RateLimiter.get_instance()
        limiter.set_limit('decorator_test', 2.0, burst=1)

        call_count = 0

        @rate_limited('decorator_test')
        def test_func():
            nonlocal call_count
            call_count += 1
            return call_count

        # First call should be fast
        start = time.time()
        result1 = test_func()
        first_time = time.time() - start

        # Second call should be rate limited
        start = time.time()
        result2 = test_func()
        second_time = time.time() - start

        assert result1 == 1
        assert result2 == 2
        assert first_time < 0.1
        assert second_time >= 0.4  # Should wait ~0.5s for 2 req/s

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring"""
        @rate_limited('youtube')
        def my_function():
            """My docstring"""
            pass

        assert my_function.__name__ == 'my_function'
        assert 'My docstring' in my_function.__doc__


class TestConvenienceFunctions:
    """Test convenience rate limit functions"""

    def setup_method(self):
        """Reset rate limiter before each test"""
        RateLimiter.get_instance().reset()

    def test_youtube_rate_limit(self):
        """Test youtube_rate_limit function"""
        start = time.time()
        youtube_rate_limit()
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be immediate with tokens available

    def test_spotify_rate_limit(self):
        """Test spotify_rate_limit function"""
        start = time.time()
        spotify_rate_limit()
        elapsed = time.time() - start
        assert elapsed < 0.1

    def test_musicbrainz_rate_limit(self):
        """Test musicbrainz_rate_limit function"""
        start = time.time()
        musicbrainz_rate_limit()
        elapsed = time.time() - start
        assert elapsed < 0.1


class TestThreadSafety:
    """Test thread safety of rate limiter"""

    def setup_method(self):
        """Reset rate limiter before each test"""
        RateLimiter.get_instance().reset()

    def test_concurrent_access(self):
        """Test that rate limiter handles concurrent access correctly"""
        limiter = RateLimiter.get_instance()
        limiter.set_limit('concurrent_test', 10.0, burst=10)

        results = []
        errors = []

        def worker():
            try:
                limiter.wait('concurrent_test')
                results.append(1)
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(20)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all to complete
        for t in threads:
            t.join()

        # All should succeed
        assert len(results) == 20
        assert len(errors) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
