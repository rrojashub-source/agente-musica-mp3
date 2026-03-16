"""
Tests for ChordsClient — Offline chord detection

Tests chord detection, caching, deduplication, transposition,
and error handling with all heavy dependencies mocked.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import MagicMock, PropertyMock, patch

import numpy as np
import pytest

from api.chords_client import ChordsClient


class TestChordsClientInit:
    """Test ChordsClient initialization"""

    def test_init_without_db(self):
        """Test initialization without database manager"""
        client = ChordsClient()
        assert client.db_manager is None
        assert client._cache == {}
        assert client._librosa is None
        assert client._np is None

    def test_init_with_db(self):
        """Test initialization with database manager"""
        mock_db = MagicMock()
        client = ChordsClient(db_manager=mock_db)
        assert client.db_manager is mock_db


class TestChordsClientConstants:
    """Test that class constants are defined correctly"""

    def test_chroma_labels_length(self):
        """CHROMA_LABELS must have exactly 12 notes"""
        assert len(ChordsClient.CHROMA_LABELS) == 12

    def test_chroma_labels_start_with_c(self):
        """CHROMA_LABELS starts with C (standard chromatic scale)"""
        assert ChordsClient.CHROMA_LABELS[0] == "C"
        assert ChordsClient.CHROMA_LABELS[-1] == "B"

    def test_analysis_parameters_positive(self):
        """All analysis parameters should be positive"""
        assert ChordsClient.HOP_LENGTH > 0
        assert ChordsClient.BLOCK_SECONDS > 0
        assert ChordsClient.SAMPLE_RATE > 0
        assert ChordsClient.MIN_ENERGY > 0


class TestDeduplicate:
    """Test chord deduplication logic"""

    def test_empty_list(self):
        """Deduplicating empty list returns empty list"""
        assert ChordsClient._deduplicate([]) == []

    def test_no_duplicates(self):
        """List with no consecutive duplicates is unchanged"""
        chords = [
            {"t": 0.0, "chord": "C"},
            {"t": 4.0, "chord": "Am"},
            {"t": 8.0, "chord": "F"},
        ]
        result = ChordsClient._deduplicate(chords)
        assert len(result) == 3

    def test_consecutive_duplicates_removed(self):
        """Consecutive identical chords are collapsed to the first"""
        chords = [
            {"t": 0.0, "chord": "C"},
            {"t": 4.0, "chord": "C"},
            {"t": 8.0, "chord": "C"},
            {"t": 12.0, "chord": "Am"},
            {"t": 16.0, "chord": "Am"},
        ]
        result = ChordsClient._deduplicate(chords)
        assert len(result) == 2
        assert result[0] == {"t": 0.0, "chord": "C"}
        assert result[1] == {"t": 12.0, "chord": "Am"}

    def test_non_consecutive_duplicates_kept(self):
        """Non-consecutive duplicates (A-B-A pattern) are preserved"""
        chords = [
            {"t": 0.0, "chord": "C"},
            {"t": 4.0, "chord": "G"},
            {"t": 8.0, "chord": "C"},
        ]
        result = ChordsClient._deduplicate(chords)
        assert len(result) == 3

    def test_single_chord(self):
        """Single chord list returns unchanged"""
        chords = [{"t": 0.0, "chord": "Dm"}]
        result = ChordsClient._deduplicate(chords)
        assert result == chords


class TestDetectChord:
    """Test chord detection from chroma vectors"""

    def setup_method(self):
        """Create client with numpy loaded"""
        self.client = ChordsClient()
        self.client._np = np

    def test_c_major_detection(self):
        """A strong C-E-G chroma vector should detect C major"""
        chroma = np.zeros(12)
        chroma[0] = 1.0  # C
        chroma[4] = 0.9  # E
        chroma[7] = 0.8  # G
        result = self.client._detect_chord(chroma)
        assert result == "C"

    def test_a_minor_detection(self):
        """A strong A-C-E chroma vector should detect Am"""
        chroma = np.zeros(12)
        chroma[9] = 1.0  # A
        chroma[0] = 0.9  # C  (A + 3 semitones)
        chroma[4] = 0.8  # E  (A + 7 semitones)
        result = self.client._detect_chord(chroma)
        assert result == "Am"

    def test_silence_returns_no_chord(self):
        """A zero vector (silence) returns 'N' (no chord)"""
        chroma = np.zeros(12)
        result = self.client._detect_chord(chroma)
        assert result == "N"

    def test_dominant_seventh_detection(self):
        """A G-B-D-F chroma vector should detect G7 when 7th is strong"""
        chroma = np.zeros(12)
        chroma[7] = 1.0  # G (root)
        chroma[11] = 0.8  # B (major 3rd, G+4)
        chroma[2] = 0.7  # D (fifth, G+7)
        chroma[5] = 0.5  # F (minor 7th, G+10)
        result = self.client._detect_chord(chroma)
        assert result == "G7"


class TestGetChords:
    """Test get_chords with caching layers"""

    def setup_method(self):
        self.client = ChordsClient()

    def test_returns_from_memory_cache(self):
        """get_chords returns cached result without re-analyzing"""
        cached = [{"t": 0.0, "chord": "C"}]
        self.client._cache[42] = cached

        result = self.client.get_chords("/fake/path.mp3", song_id=42)
        assert result is cached

    def test_returns_from_db_cache(self):
        """get_chords loads from DB when not in memory cache"""
        mock_db = MagicMock()
        db_chords = [{"t": 0.0, "chord": "G"}, {"t": 4.0, "chord": "D"}]
        mock_db.execute_query.return_value = [(json.dumps(db_chords),)]

        self.client.db_manager = mock_db
        result = self.client.get_chords("/fake/path.mp3", song_id=99)

        assert result == db_chords
        # Should also be stored in memory cache
        assert self.client._cache[99] == db_chords

    def test_analyze_called_when_no_cache(self):
        """get_chords calls analyze_file when nothing is cached"""
        analyzed = [{"t": 0.0, "chord": "Em"}]
        self.client.analyze_file = MagicMock(return_value=analyzed)

        result = self.client.get_chords("/some/file.mp3", song_id=7)
        self.client.analyze_file.assert_called_once_with("/some/file.mp3")
        assert result == analyzed
        assert self.client._cache[7] == analyzed

    def test_returns_none_on_analysis_failure(self):
        """get_chords returns None when analyze_file fails"""
        self.client.analyze_file = MagicMock(return_value=None)
        result = self.client.get_chords("/bad/file.mp3")
        assert result is None


class TestAnalyzeFile:
    """Test analyze_file with mocked librosa"""

    def test_file_not_found_returns_none(self):
        """analyze_file returns None for non-existent file"""
        client = ChordsClient()
        client._librosa = MagicMock()
        client._np = np
        result = client.analyze_file("/nonexistent/file.mp3")
        assert result is None

    def test_import_error_returns_none(self):
        """analyze_file returns None when librosa is not installed"""
        client = ChordsClient()
        # Force _ensure_libs to raise ImportError
        client._ensure_libs = MagicMock(side_effect=ImportError("no librosa"))
        # analyze_file catches ImportError internally, but _ensure_libs is
        # called before the try block wraps it. Let's test the real path:
        with patch.dict("sys.modules", {"librosa": None}):
            client2 = ChordsClient()
            # Simulate librosa not loadable
            result = client2.analyze_file("/nonexistent/anyway.mp3")
            assert result is None


class TestTransposeChords:
    """Test chord transposition"""

    def test_zero_semitones_unchanged(self):
        """Transposing by 0 semitones returns the same list"""
        chords = [{"t": 0.0, "chord": "C"}, {"t": 4.0, "chord": "G"}]
        result = ChordsClient.transpose_chords(chords, 0)
        assert result is chords  # Same object, no processing

    def test_transpose_with_pychord(self):
        """Transposing chords delegates to pychord.Chord"""
        mock_chord_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.__str__ = MagicMock(return_value="D")
        mock_chord_class.return_value = mock_instance

        with patch.dict("sys.modules", {"pychord": MagicMock(Chord=mock_chord_class)}):
            chords = [{"t": 0.0, "chord": "C"}]
            result = ChordsClient.transpose_chords(chords, 2)
            assert len(result) == 1
            assert result[0]["t"] == 0.0
            # pychord was called
            mock_chord_class.assert_called_once_with("C")
            mock_instance.transpose.assert_called_once_with(2)

    def test_transpose_pychord_missing_returns_original(self):
        """When pychord is not installed, returns original chords"""
        chords = [{"t": 0.0, "chord": "C"}]
        with patch.dict("sys.modules", {"pychord": None}):
            # Force fresh import to fail
            import importlib

            # The method catches ImportError and returns chords as-is
            # We simulate by removing pychord from available modules
            with patch("builtins.__import__", side_effect=ImportError):
                result = ChordsClient.transpose_chords(chords, 3)
                assert result == chords


class TestClearCache:
    """Test cache clearing"""

    def test_clear_cache_empties_memory(self):
        """clear_cache removes all entries from memory cache"""
        client = ChordsClient()
        client._cache = {1: [{"t": 0, "chord": "C"}], 2: [{"t": 0, "chord": "D"}]}
        client.clear_cache()
        assert client._cache == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
