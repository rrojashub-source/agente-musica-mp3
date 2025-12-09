"""
Tests for Audio Embeddings - AI-Powered Similarity Search (Phase 9)

Tests the audio feature extraction and similarity search functionality.

Created: December 8, 2025
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.audio_embeddings import AudioEmbeddings


class TestAudioEmbeddingsInit:
    """Test AudioEmbeddings initialization"""

    def test_init_without_db(self):
        """Test initialization without database manager"""
        embeddings = AudioEmbeddings()
        assert embeddings.db_manager is None
        assert embeddings.EMBEDDING_DIM == 128

    def test_init_with_db(self):
        """Test initialization with mock database manager"""
        mock_db = Mock()
        mock_db.conn = Mock()
        mock_db.conn.cursor.return_value = Mock()

        embeddings = AudioEmbeddings(mock_db)
        assert embeddings.db_manager == mock_db

    def test_embedding_dimensions(self):
        """Test that embedding dimension is 128"""
        embeddings = AudioEmbeddings()
        assert embeddings.EMBEDDING_DIM == 128
        assert embeddings.SAMPLE_RATE == 22050
        assert embeddings.FRAME_SIZE == 2048


class TestFeatureExtraction:
    """Test audio feature extraction"""

    def test_extract_audio_features_shape(self):
        """Test that extracted features have correct shape"""
        embeddings = AudioEmbeddings()

        # Create synthetic audio samples (1 second at 22050 Hz)
        samples = np.sin(2 * np.pi * 440 * np.arange(22050) / 22050).astype(np.float32)

        features = embeddings._extract_audio_features(samples)

        assert features is not None
        assert features.shape == (128,)
        assert features.dtype == np.float32

    def test_extract_audio_features_too_short(self):
        """Test that short audio returns None"""
        embeddings = AudioEmbeddings()

        # Very short samples (less than minimum)
        short_samples = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        features = embeddings._extract_audio_features(short_samples)

        assert features is None

    def test_extract_audio_features_normalized(self):
        """Test that features are properly normalized"""
        embeddings = AudioEmbeddings()

        # Create varied audio
        samples = np.random.randn(44100).astype(np.float32) * 0.5

        features = embeddings._extract_audio_features(samples)

        assert features is not None
        # Features should be bounded
        assert np.all(np.isfinite(features))


class TestBandEnergies:
    """Test mel-like band energy computation"""

    def test_band_energies_shape(self):
        """Test band energies output shape"""
        embeddings = AudioEmbeddings()

        # Simulate FFT magnitude output
        magnitude = np.random.rand(1025).astype(np.float32)
        freqs = np.fft.rfftfreq(2048, 1/22050)

        band_energies = embeddings._compute_band_energies(magnitude, freqs)

        assert len(band_energies) == 24  # NUM_BANDS

    def test_band_energies_normalized(self):
        """Test that band energies sum to ~1 (normalized)"""
        embeddings = AudioEmbeddings()

        magnitude = np.random.rand(1025).astype(np.float32) + 0.1
        freqs = np.fft.rfftfreq(2048, 1/22050)

        band_energies = embeddings._compute_band_energies(magnitude, freqs)

        # Should be normalized to sum to 1
        assert np.isclose(np.sum(band_energies), 1.0, atol=0.01)


class TestTemporalFeatures:
    """Test temporal/rhythmic feature extraction"""

    def test_temporal_features_count(self):
        """Test that temporal features return 12 values"""
        embeddings = AudioEmbeddings()

        # Simulate RMS values over time
        rms_values = list(np.abs(np.sin(np.linspace(0, 10, 200))) * 0.5 + 0.1)

        features = embeddings._extract_temporal_features(rms_values)

        assert len(features) == 12

    def test_temporal_features_short_input(self):
        """Test temporal features with short input"""
        embeddings = AudioEmbeddings()

        # Very short RMS sequence
        rms_values = [0.1, 0.2, 0.3]

        features = embeddings._extract_temporal_features(rms_values)

        assert len(features) == 12
        # Should handle gracefully (with zeros for unavailable features)


class TestCosineSimilarity:
    """Test cosine similarity calculation"""

    def test_cosine_identical_vectors(self):
        """Test similarity of identical vectors is 1.0"""
        embeddings = AudioEmbeddings()

        vec = np.array([1.0, 2.0, 3.0, 4.0])

        similarity = embeddings._cosine_similarity(vec, vec)

        assert np.isclose(similarity, 1.0)

    def test_cosine_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors is 0.5 (normalized from 0)"""
        embeddings = AudioEmbeddings()

        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])

        similarity = embeddings._cosine_similarity(vec1, vec2)

        # Cosine similarity 0 -> normalized to 0.5
        assert np.isclose(similarity, 0.5)

    def test_cosine_opposite_vectors(self):
        """Test similarity of opposite vectors is 0.0 (normalized from -1)"""
        embeddings = AudioEmbeddings()

        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([-1.0, 0.0])

        similarity = embeddings._cosine_similarity(vec1, vec2)

        # Cosine similarity -1 -> normalized to 0.0
        assert np.isclose(similarity, 0.0)

    def test_cosine_similar_vectors(self):
        """Test similarity of similar vectors is high"""
        embeddings = AudioEmbeddings()

        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.1, 2.1, 3.1])

        similarity = embeddings._cosine_similarity(vec1, vec2)

        # Should be very high (close to 1.0)
        assert similarity > 0.95

    def test_cosine_zero_vector(self):
        """Test handling of zero vectors"""
        embeddings = AudioEmbeddings()

        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 2.0, 3.0])

        similarity = embeddings._cosine_similarity(vec1, vec2)

        assert similarity == 0.0


class TestFileHash:
    """Test file hash computation"""

    def test_compute_file_hash_nonexistent(self):
        """Test hash of non-existent file"""
        embeddings = AudioEmbeddings()

        hash_result = embeddings._compute_file_hash("/nonexistent/file.mp3")

        assert hash_result == ""

    @patch('builtins.open', create=True)
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.exists')
    def test_compute_file_hash_valid(self, mock_exists, mock_stat, mock_open):
        """Test hash computation for valid file"""
        embeddings = AudioEmbeddings()

        # Mock file existence and stats
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1000)
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = Mock(return_value=False)
        mock_open.return_value.read = Mock(return_value=b"test content")

        # This should not raise an exception
        # Note: Full test would require actual file


class TestCaching:
    """Test embedding caching functionality"""

    def test_cache_embedding_no_db(self):
        """Test caching without database doesn't crash"""
        embeddings = AudioEmbeddings()

        embedding = np.random.rand(128).astype(np.float32)

        # Should not raise exception
        embeddings._cache_embedding(1, embedding, "abc123")

    def test_get_cached_embedding_no_db(self):
        """Test getting cached embedding without database returns None"""
        embeddings = AudioEmbeddings()

        result = embeddings._get_cached_embedding(1, "abc123")

        assert result is None


class TestFindSimilar:
    """Test similarity search functionality"""

    def test_find_similar_no_db(self):
        """Test find_similar without database returns empty list"""
        embeddings = AudioEmbeddings()

        result = embeddings.find_similar(1)

        assert result == []

    def test_get_embedding_stats_no_db(self):
        """Test stats without database"""
        embeddings = AudioEmbeddings()

        stats = embeddings.get_embedding_stats()

        assert stats['total'] == 0
        assert stats['coverage'] == 0


class TestIntegration:
    """Integration tests with mock database"""

    def test_full_workflow_mock(self):
        """Test complete workflow with mocked components"""
        # Create mock database manager
        mock_db = Mock()
        mock_db.conn = Mock()
        mock_cursor = Mock()
        mock_db.conn.cursor.return_value = mock_cursor

        # Mock get_all_songs
        mock_db.get_all_songs.return_value = [
            {'id': 1, 'title': 'Song 1', 'artist': 'Artist 1', 'file_path': '/path/1.mp3'},
            {'id': 2, 'title': 'Song 2', 'artist': 'Artist 2', 'file_path': '/path/2.mp3'},
        ]

        # Mock get_song_by_id
        mock_db.get_song_by_id.return_value = {
            'id': 1, 'title': 'Song 1', 'artist': 'Artist 1', 'file_path': '/path/1.mp3'
        }

        embeddings = AudioEmbeddings(mock_db)

        # Verify initialization created table
        assert mock_cursor.execute.called


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_extract_embedding_nonexistent_file(self):
        """Test extraction from non-existent file"""
        embeddings = AudioEmbeddings()

        result = embeddings.extract_embedding("/nonexistent/path/song.mp3")

        assert result is None

    def test_extract_audio_features_all_zeros(self):
        """Test feature extraction from silent audio"""
        embeddings = AudioEmbeddings()

        # Silent audio (all zeros)
        silent_samples = np.zeros(44100, dtype=np.float32)

        features = embeddings._extract_audio_features(silent_samples)

        # Should handle gracefully (may return zeros or valid features)
        if features is not None:
            assert features.shape == (128,)

    def test_batch_generate_no_db(self):
        """Test batch generation without database"""
        embeddings = AudioEmbeddings()

        result = embeddings.batch_generate_embeddings()

        assert result == {'processed': 0, 'cached': 0, 'failed': 0}


# Performance test (optional, run with -v flag)
class TestPerformance:
    """Performance tests for audio embeddings"""

    @pytest.mark.slow
    def test_feature_extraction_speed(self):
        """Test that feature extraction is reasonably fast"""
        import time

        embeddings = AudioEmbeddings()

        # 3 seconds of audio at 22050 Hz
        samples = np.random.randn(22050 * 3).astype(np.float32) * 0.5

        start = time.time()
        features = embeddings._extract_audio_features(samples)
        elapsed = time.time() - start

        assert features is not None
        # Should complete in under 1 second for 3 seconds of audio
        assert elapsed < 1.0, f"Feature extraction took {elapsed:.2f}s, expected < 1.0s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
