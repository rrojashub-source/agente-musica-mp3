"""
Tests for Waveform Extractor — Audio waveform and spectrum extraction.

Tests the WaveformExtractor class which extracts waveform data,
frequency spectrum, and raw samples from audio files for visualization.

Created: 2026-03-15
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.waveform_extractor import WaveformExtractor


class TestWaveformExtractorInit:
    """Test WaveformExtractor initialization"""

    def test_init_creates_empty_cache(self):
        """Test that initialization creates an empty cache dict."""
        extractor = WaveformExtractor()
        assert extractor.cache == {}
        assert extractor.get_cache_size() == 0


class TestExtract:
    """Test waveform extraction"""

    def test_nonexistent_file(self):
        """Test extract returns None for a non-existent file."""
        extractor = WaveformExtractor()
        result = extractor.extract("/nonexistent/path/song.mp3")
        assert result is None

    def test_cache_hit(self):
        """Test that cached waveforms are returned without re-extraction."""
        extractor = WaveformExtractor()
        fake_waveform = [0.1, 0.5, 0.3, 0.8]
        extractor.cache["test_file.mp3_1000"] = fake_waveform

        result = extractor.extract("test_file.mp3", num_points=1000)
        assert result is fake_waveform

    @patch("core.waveform_extractor.PYDUB_AVAILABLE", True)
    @patch("core.waveform_extractor.AudioSegment")
    def test_extract_with_pydub(self, mock_audio_segment, tmp_path):
        """Test waveform extraction via pydub produces valid output."""
        fake_file = tmp_path / "test.mp3"
        fake_file.write_bytes(b"\x00" * 100)

        # Create mock audio with known samples
        num_samples = 44100
        mock_audio = Mock()
        mock_audio.channels = 1
        mock_audio.sample_width = 2
        mock_audio.frame_rate = 44100
        mock_audio.set_channels.return_value = mock_audio
        raw_samples = (np.sin(np.linspace(0, 10, num_samples)) * 16000).astype(np.int16)
        mock_audio.get_array_of_samples.return_value = raw_samples.tolist()
        mock_audio_segment.from_file.return_value = mock_audio

        extractor = WaveformExtractor()
        result = extractor.extract(str(fake_file), num_points=100)

        assert result is not None
        assert len(result) <= 100
        # All values should be in [-1.0, 1.0]
        assert all(-1.0 <= v <= 1.0 for v in result)

    @patch("core.waveform_extractor.PYDUB_AVAILABLE", True)
    @patch("core.waveform_extractor.AudioSegment")
    def test_extract_caches_result(self, mock_audio_segment, tmp_path):
        """Test that extracted waveform is stored in cache."""
        fake_file = tmp_path / "cache_test.mp3"
        fake_file.write_bytes(b"\x00" * 100)

        mock_audio = Mock()
        mock_audio.channels = 1
        mock_audio.sample_width = 2
        mock_audio.set_channels.return_value = mock_audio
        samples = (np.random.randn(22050) * 10000).astype(np.int16)
        mock_audio.get_array_of_samples.return_value = samples.tolist()
        mock_audio_segment.from_file.return_value = mock_audio

        extractor = WaveformExtractor()
        result = extractor.extract(str(fake_file), num_points=50)

        assert result is not None
        assert extractor.get_cache_size() == 1


class TestDistributeIntoBars:
    """Test logarithmic frequency bar distribution"""

    def test_correct_number_of_bars(self):
        """Test that output has the requested number of bars."""
        extractor = WaveformExtractor()
        magnitudes = np.random.rand(513)  # Typical rfft output for 1024 samples
        bars = extractor._distribute_into_bars(magnitudes, num_bars=32)
        assert len(bars) == 32

    def test_bar_values_are_floats(self):
        """Test that bar magnitudes are Python floats."""
        extractor = WaveformExtractor()
        magnitudes = np.random.rand(513)
        bars = extractor._distribute_into_bars(magnitudes, num_bars=10)
        assert all(isinstance(b, float) for b in bars)


class TestCacheManagement:
    """Test cache operations"""

    def test_clear_cache(self):
        """Test that clear_cache empties the cache."""
        extractor = WaveformExtractor()
        extractor.cache["key1"] = [0.1, 0.2]
        extractor.cache["key2"] = [0.3, 0.4]
        assert extractor.get_cache_size() == 2

        extractor.clear_cache()
        assert extractor.get_cache_size() == 0

    def test_get_cache_size(self):
        """Test cache size reporting."""
        extractor = WaveformExtractor()
        assert extractor.get_cache_size() == 0
        extractor.cache["a"] = []
        assert extractor.get_cache_size() == 1


class TestExtractSpectrum:
    """Test spectrum extraction"""

    def test_nonexistent_file(self):
        """Test extract_spectrum returns None for non-existent file."""
        extractor = WaveformExtractor()
        result = extractor.extract_spectrum("/nonexistent/path/song.mp3")
        assert result is None

    @patch("core.waveform_extractor.PYDUB_AVAILABLE", False)
    def test_pydub_unavailable(self):
        """Test extract_spectrum returns None when pydub is unavailable."""
        extractor = WaveformExtractor()
        # Need a file that exists but pydub is unavailable
        # Since PYDUB_AVAILABLE is False, it returns None regardless
        result = extractor.extract_spectrum("any_file.mp3")
        assert result is None


class TestExtractRawSamples:
    """Test raw sample extraction"""

    def test_nonexistent_file(self):
        """Test extract_raw_samples returns None for non-existent file."""
        extractor = WaveformExtractor()
        result = extractor.extract_raw_samples("/nonexistent/path/song.mp3")
        assert result is None

    @patch("core.waveform_extractor.PYDUB_AVAILABLE", False)
    def test_pydub_unavailable(self):
        """Test extract_raw_samples returns None when pydub unavailable."""
        extractor = WaveformExtractor()
        result = extractor.extract_raw_samples("any_file.mp3")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
