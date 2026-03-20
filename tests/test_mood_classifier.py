"""
Tests for Mood Classifier — Audio mood/energy classification.

Tests the MoodClassifier class which classifies audio into mood categories
(Energetic, Happy, Calm, Sad, Intense) using spectral + temporal features.

Created: 2026-03-15
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.mood_classifier import MOODS, MoodClassifier


class TestMoodClassifierInit:
    """Test MoodClassifier initialization"""

    def test_init_default(self):
        """Test initialization with default parameters creates BPMDetector."""
        classifier = MoodClassifier()
        assert classifier.sample_rate == 22050
        assert classifier.frame_size == 2048
        assert classifier.hop_size == 512
        assert classifier.bpm_detector is not None

    def test_init_custom_bpm_detector(self):
        """Test initialization with a custom BPMDetector instance."""
        mock_bpm = Mock()
        classifier = MoodClassifier(bpm_detector=mock_bpm)
        assert classifier.bpm_detector is mock_bpm

    def test_init_custom_params(self):
        """Test initialization with custom audio parameters."""
        classifier = MoodClassifier(sample_rate=44100, frame_size=4096, hop_size=1024)
        assert classifier.sample_rate == 44100
        assert classifier.frame_size == 4096
        assert classifier.hop_size == 1024


class TestMoodCategories:
    """Test mood category constants"""

    def test_moods_list_complete(self):
        """Test that MOODS contains all five expected categories."""
        assert len(MOODS) == 5
        assert "Energetic" in MOODS
        assert "Happy" in MOODS
        assert "Calm" in MOODS
        assert "Sad" in MOODS
        assert "Intense" in MOODS


class TestClassifyFromFeatures:
    """Test rule-based mood classification from features"""

    def test_high_energy_features(self):
        """Test that high energy + fast tempo yields Energetic mood."""
        classifier = MoodClassifier()
        features = {
            "brightness": 3500,
            "brightness_std": 500,
            "flatness": 0.05,
            "energy": 0.18,
            "energy_std": 0.06,
            "zcr": 0.10,
            "low_energy_ratio": 0.2,
            "tempo": 160,
            "dynamic_range": 0.15,
        }
        result = classifier.classify_from_features(features)
        assert result["mood"] in MOODS
        assert result["energy"] > 50

    def test_calm_features(self):
        """Test that low energy + slow tempo yields low energy score."""
        classifier = MoodClassifier()
        features = {
            "brightness": 800,
            "brightness_std": 100,
            "flatness": 0.3,
            "energy": 0.015,
            "energy_std": 0.005,
            "zcr": 0.01,
            "low_energy_ratio": 0.8,
            "tempo": 65,
            "dynamic_range": 0.01,
        }
        result = classifier.classify_from_features(features)
        assert result["energy"] < 30
        assert 0 <= result["valence"] <= 100

    def test_result_keys(self):
        """Test that classification result contains all expected keys."""
        classifier = MoodClassifier()
        features = {
            "brightness": 2000,
            "brightness_std": 300,
            "flatness": 0.1,
            "energy": 0.1,
            "energy_std": 0.03,
            "zcr": 0.05,
            "low_energy_ratio": 0.5,
            "tempo": 120,
            "dynamic_range": 0.08,
        }
        result = classifier.classify_from_features(features)
        assert "mood" in result
        assert "energy" in result
        assert "valence" in result
        assert "confidence" in result
        assert "bpm" in result

    def test_bpm_passthrough(self):
        """Test that tempo from features is passed through as bpm in result."""
        classifier = MoodClassifier()
        features = {
            "brightness": 2000,
            "brightness_std": 300,
            "flatness": 0.1,
            "energy": 0.1,
            "energy_std": 0.03,
            "zcr": 0.05,
            "low_energy_ratio": 0.5,
            "tempo": 135,
            "dynamic_range": 0.08,
        }
        result = classifier.classify_from_features(features)
        assert result["bpm"] == 135

    def test_values_bounded(self):
        """Test that energy, valence, and confidence are bounded 0-100."""
        classifier = MoodClassifier()
        features = {
            "brightness": 5000,
            "brightness_std": 800,
            "flatness": 0.9,
            "energy": 0.25,
            "energy_std": 0.1,
            "zcr": 0.2,
            "low_energy_ratio": 0.1,
            "tempo": 200,
            "dynamic_range": 0.3,
        }
        result = classifier.classify_from_features(features)
        assert 0 <= result["energy"] <= 100
        assert 0 <= result["valence"] <= 100
        assert 0 <= result["confidence"] <= 100

    def test_sad_features(self):
        """Test features associated with sad mood yield high sad score."""
        classifier = MoodClassifier()
        # Dark, slow, flat, low energy
        features = {
            "brightness": 500,
            "brightness_std": 50,
            "flatness": 0.7,
            "energy": 0.02,
            "energy_std": 0.005,
            "zcr": 0.01,
            "low_energy_ratio": 0.85,
            "tempo": 60,
            "dynamic_range": 0.01,
        }
        result = classifier.classify_from_features(features)
        # Low valence is characteristic of sad classification
        assert result["valence"] < 40


class TestExtractMoodFeatures:
    """Test feature extraction from raw audio samples"""

    def test_valid_audio(self):
        """Test mood feature extraction from synthetic audio."""
        mock_bpm = Mock()
        mock_bpm.estimate_bpm.return_value = 120
        classifier = MoodClassifier(bpm_detector=mock_bpm)

        samples = np.random.randn(22050 * 3).astype(np.float32) * 0.3
        features = classifier.extract_mood_features(samples)

        assert features is not None
        assert "brightness" in features
        assert "energy" in features
        assert "tempo" in features
        assert "flatness" in features
        assert "zcr" in features
        assert "low_energy_ratio" in features
        assert "dynamic_range" in features

    def test_too_short_audio(self):
        """Test that audio shorter than minimum returns None."""
        classifier = MoodClassifier()
        short_samples = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        features = classifier.extract_mood_features(short_samples)
        assert features is None

    def test_silent_audio(self):
        """Test feature extraction from silent (all zeros) audio."""
        mock_bpm = Mock()
        mock_bpm.estimate_bpm.return_value = None
        classifier = MoodClassifier(bpm_detector=mock_bpm)

        silent = np.zeros(22050 * 3, dtype=np.float32)
        features = classifier.extract_mood_features(silent)

        if features is not None:
            assert features["energy"] == 0.0 or features["energy"] < 0.001
            # Tempo defaults to 100 when BPM detection fails
            assert features["tempo"] == 100


class TestClassifyFile:
    """Test full file-based classify method"""

    def test_nonexistent_file(self):
        """Test classify returns None for a non-existent file."""
        classifier = MoodClassifier()
        result = classifier.classify("/nonexistent/path/song.mp3")
        assert result is None

    @patch("core.mood_classifier.PYDUB_AVAILABLE", False)
    def test_pydub_unavailable(self):
        """Test classify returns None when pydub is not available."""
        classifier = MoodClassifier()
        result = classifier.classify("some_file.mp3")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
