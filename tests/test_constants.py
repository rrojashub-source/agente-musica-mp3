"""
Tests for Application Constants

Validates that all constants are defined, have correct types,
and contain reasonable values.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from utils.constants import (
    ALBUM_ART_THUMBNAIL_SIZE,
    ANIMATION_FRAME_INTERVAL_MS,
    API_CACHE_SIZE,
    API_DEFAULT_RESULTS,
    API_DEFAULT_TIMEOUT,
    API_MAX_RESULTS,
    API_MAX_RETRIES,
    API_QUERY_MAX_LENGTH,
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    CONFIDENCE_THRESHOLD_DEFAULT,
    DB_CONNECTION_TIMEOUT,
    DEFAULT_REMOTE_PORT,
    FILE_HASH_CHUNK_SIZE,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_WIDTH,
    MAX_CONCURRENT_DOWNLOADS,
    MAX_DOWNLOAD_RETRIES,
    PORT_RANGE_MAX,
    PORT_RANGE_MIN,
    POSITION_UPDATE_INTERVAL_MS,
    REMOTE_UPDATE_INTERVAL_MS,
    TRACK_END_CHECK_INTERVAL_MS,
    VISUALIZER_FRAME_INTERVAL_MS,
)


class TestAudioConstants:
    """Test audio-related constants"""

    def test_sample_rate_is_standard(self):
        """Sample rate should be a standard audio rate"""
        assert AUDIO_SAMPLE_RATE in (22050, 44100, 48000, 96000)

    def test_channels_is_stereo(self):
        """Default audio channels should be stereo (2)"""
        assert AUDIO_CHANNELS == 2

    def test_hash_chunk_size_is_power_of_two(self):
        """File hash chunk size should be a power of 2 for efficiency"""
        assert FILE_HASH_CHUNK_SIZE > 0
        assert (FILE_HASH_CHUNK_SIZE & (FILE_HASH_CHUNK_SIZE - 1)) == 0


class TestAPIConstants:
    """Test API / network constants"""

    def test_all_api_constants_are_positive_integers(self):
        """All API constants must be positive integers"""
        api_values = [
            API_CACHE_SIZE,
            API_DEFAULT_RESULTS,
            API_MAX_RESULTS,
            API_QUERY_MAX_LENGTH,
            API_DEFAULT_TIMEOUT,
            API_MAX_RETRIES,
        ]
        for val in api_values:
            assert isinstance(val, int), f"Expected int, got {type(val)} for {val}"
            assert val > 0, f"Expected positive, got {val}"

    def test_default_results_less_than_max(self):
        """Default results should not exceed max results"""
        assert API_DEFAULT_RESULTS <= API_MAX_RESULTS

    def test_timeout_reasonable_range(self):
        """API timeout should be between 1 and 120 seconds"""
        assert 1 <= API_DEFAULT_TIMEOUT <= 120

    def test_retries_reasonable(self):
        """Retry count should be between 1 and 10"""
        assert 1 <= API_MAX_RETRIES <= 10


class TestDatabaseConstants:
    """Test database constants"""

    def test_db_timeout_positive_float(self):
        """DB connection timeout must be a positive number"""
        assert DB_CONNECTION_TIMEOUT > 0
        assert isinstance(DB_CONNECTION_TIMEOUT, (int, float))

    def test_concurrent_downloads_reasonable(self):
        """Max concurrent downloads should be between 1 and 100"""
        assert 1 <= MAX_CONCURRENT_DOWNLOADS <= 100

    def test_download_retries_reasonable(self):
        """Download retries should be between 1 and 10"""
        assert 1 <= MAX_DOWNLOAD_RETRIES <= 10


class TestTimerConstants:
    """Test timer/interval constants"""

    def test_all_intervals_are_positive_integers(self):
        """All timer intervals must be positive integers (milliseconds)"""
        intervals = [
            POSITION_UPDATE_INTERVAL_MS,
            REMOTE_UPDATE_INTERVAL_MS,
            TRACK_END_CHECK_INTERVAL_MS,
            VISUALIZER_FRAME_INTERVAL_MS,
            ANIMATION_FRAME_INTERVAL_MS,
        ]
        for val in intervals:
            assert isinstance(val, int), f"Expected int, got {type(val)}"
            assert val > 0, f"Expected positive, got {val}"

    def test_animation_faster_than_visualizer(self):
        """Animation frame interval should be <= visualizer (higher FPS)"""
        assert ANIMATION_FRAME_INTERVAL_MS <= VISUALIZER_FRAME_INTERVAL_MS

    def test_visualizer_achieves_at_least_20fps(self):
        """Visualizer interval should produce at least 20 FPS"""
        fps = 1000 / VISUALIZER_FRAME_INTERVAL_MS
        assert fps >= 20


class TestUIConstants:
    """Test UI default constants"""

    def test_window_dimensions_reasonable(self):
        """Main window size should be reasonable for a desktop app"""
        assert 800 <= MAIN_WINDOW_WIDTH <= 3840
        assert 600 <= MAIN_WINDOW_HEIGHT <= 2160

    def test_port_range_valid(self):
        """Port range must be valid (1024-65535 for non-privileged)"""
        assert PORT_RANGE_MIN >= 1024
        assert PORT_RANGE_MAX <= 65535
        assert PORT_RANGE_MIN < PORT_RANGE_MAX

    def test_default_port_within_range(self):
        """Default remote port must be within the allowed range"""
        assert PORT_RANGE_MIN <= DEFAULT_REMOTE_PORT <= PORT_RANGE_MAX

    def test_thumbnail_size_positive(self):
        """Album art thumbnail size must be positive"""
        assert ALBUM_ART_THUMBNAIL_SIZE > 0

    def test_confidence_threshold_is_percentage(self):
        """Confidence threshold should be 0-100 range"""
        assert 0 <= CONFIDENCE_THRESHOLD_DEFAULT <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
