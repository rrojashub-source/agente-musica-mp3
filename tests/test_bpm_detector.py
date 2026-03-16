"""
Tests for BPM Detector — Tempo detection via onset detection + autocorrelation.

Tests the BPMDetector class which estimates beats per minute (60-200 range)
from audio data using onset envelope and autocorrelation analysis.

Created: 2026-03-15
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.bpm_detector import BPMDetector


class TestBPMDetectorInit:
    """Test BPMDetector initialization"""

    def test_init_default_sample_rate(self):
        """Test initialization uses default sample rate of 22050."""
        detector = BPMDetector()
        assert detector.sample_rate == 22050

    def test_init_custom_sample_rate(self):
        """Test initialization with custom sample rate."""
        detector = BPMDetector(sample_rate=44100)
        assert detector.sample_rate == 44100


class TestEstimateBPM:
    """Test BPM estimation from raw samples"""

    def test_periodic_signal_120bpm(self):
        """Test BPM estimation with a clear 120 BPM periodic signal."""
        detector = BPMDetector()
        sr = 22050
        duration = 10
        bpm_target = 120
        beat_interval_samples = int(sr * 60 / bpm_target)

        samples = np.zeros(duration * sr, dtype=np.float32)
        for i in range(0, len(samples), beat_interval_samples):
            end = min(i + 500, len(samples))
            samples[i:end] = 0.8

        estimated = detector.estimate_bpm(samples)
        assert estimated is not None
        assert 90 <= estimated <= 150, f"Expected ~120 BPM, got {estimated}"

    def test_periodic_signal_80bpm(self):
        """Test BPM estimation with a slow 80 BPM periodic signal."""
        detector = BPMDetector()
        sr = 22050
        duration = 10
        bpm_target = 80
        beat_interval_samples = int(sr * 60 / bpm_target)

        samples = np.zeros(duration * sr, dtype=np.float32)
        for i in range(0, len(samples), beat_interval_samples):
            end = min(i + 500, len(samples))
            samples[i:end] = 0.8

        estimated = detector.estimate_bpm(samples)
        assert estimated is not None
        assert 60 <= estimated <= 200

    def test_bpm_in_valid_range(self):
        """Test that any returned BPM falls within 60-200 range."""
        detector = BPMDetector()
        samples = np.random.randn(22050 * 5).astype(np.float32) * 0.3
        bpm = detector.estimate_bpm(samples)
        if bpm is not None:
            assert 60 <= bpm <= 200

    def test_very_short_audio(self):
        """Test BPM estimation with audio too short for meaningful analysis."""
        detector = BPMDetector()
        samples = np.random.randn(500).astype(np.float32)
        bpm = detector.estimate_bpm(samples)
        # Should return None for audio shorter than one frame
        assert bpm is None

    def test_silent_audio(self):
        """Test BPM estimation with completely silent audio."""
        detector = BPMDetector()
        samples = np.zeros(22050 * 5, dtype=np.float32)
        bpm = detector.estimate_bpm(samples)
        # Silent audio has no onsets; result may be None or a default
        if bpm is not None:
            assert 60 <= bpm <= 200

    def test_returns_integer(self):
        """Test that estimated BPM is an integer when not None."""
        detector = BPMDetector()
        sr = 22050
        beat_interval_samples = int(sr * 60 / 100)
        samples = np.zeros(sr * 8, dtype=np.float32)
        for i in range(0, len(samples), beat_interval_samples):
            end = min(i + 400, len(samples))
            samples[i:end] = 0.7

        bpm = detector.estimate_bpm(samples)
        if bpm is not None:
            assert isinstance(bpm, int)


class TestDetectFromFile:
    """Test file-based BPM detection"""

    def test_nonexistent_file(self):
        """Test detect returns None for a non-existent file."""
        detector = BPMDetector()
        result = detector.detect("/nonexistent/path/song.mp3")
        assert result is None

    @patch("core.bpm_detector.PYDUB_AVAILABLE", False)
    def test_pydub_unavailable(self):
        """Test detect returns None when pydub is not available."""
        detector = BPMDetector()
        result = detector.detect("some_file.mp3")
        assert result is None

    @patch("core.bpm_detector.PYDUB_AVAILABLE", True)
    @patch("core.bpm_detector.AudioSegment")
    def test_detect_calls_estimate_bpm(self, mock_audio_segment, tmp_path):
        """Test that detect() loads audio and delegates to estimate_bpm."""
        # Create a temporary file so Path.exists() passes
        fake_file = tmp_path / "test.mp3"
        fake_file.write_bytes(b"\x00" * 100)

        # Mock AudioSegment chain
        mock_audio = Mock()
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.get_array_of_samples.return_value = list(np.zeros(22050 * 5, dtype=np.int16))
        mock_audio_segment.from_file.return_value = mock_audio

        detector = BPMDetector()
        # Patch estimate_bpm to control the return
        detector.estimate_bpm = Mock(return_value=120)

        result = detector.detect(str(fake_file))
        assert result == 120
        detector.estimate_bpm.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
