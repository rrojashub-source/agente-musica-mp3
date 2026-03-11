"""
Audio Embeddings - AI-Powered Audio Analysis (Phase 9)

Facade that orchestrates audio feature extraction, BPM detection,
mood classification, embedding caching, and similarity search.

Delegates to:
- AudioFeatureExtractor: FFT-based 128D feature extraction
- BPMDetector: Tempo detection via onset + autocorrelation
- MoodClassifier: Mood/energy classification

Public API unchanged — consumers import AudioEmbeddings as before.

Created: December 8, 2025
Updated: 2026-03-11 - Split into 3 specialized classes (Phase 2.3)
Author: NEXUS + Ricardo
"""
import logging
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

from core.audio_feature_extractor import (
    AudioFeatureExtractor,
    EMBEDDING_DIM, SAMPLE_RATE, FRAME_SIZE, HOP_SIZE, NUM_BANDS,
)
from core.bpm_detector import BPMDetector
from core.mood_classifier import MoodClassifier, MOODS as _MOODS
from utils.constants import FILE_HASH_CHUNK_SIZE

logger = logging.getLogger(__name__)

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available - audio feature extraction limited")


class AudioEmbeddings:
    """
    AI-powered audio embeddings for similarity search.

    Facade that delegates to AudioFeatureExtractor, BPMDetector,
    and MoodClassifier while managing caching and similarity search.

    Usage:
        embeddings = AudioEmbeddings(db_manager)
        embedding = embeddings.extract_embedding('/path/to/song.mp3')
        similar = embeddings.find_similar(song_id, limit=10)
    """

    # Constants (re-exported for backward compat)
    EMBEDDING_DIM = EMBEDDING_DIM
    SAMPLE_RATE = SAMPLE_RATE
    FRAME_SIZE = FRAME_SIZE
    HOP_SIZE = HOP_SIZE
    NUM_BANDS = NUM_BANDS
    MOODS = _MOODS

    def __init__(self, db_manager=None):
        """
        Initialize AudioEmbeddings.

        Args:
            db_manager: Optional DatabaseManager for caching embeddings
        """
        self.db_manager = db_manager
        self._feature_extractor = AudioFeatureExtractor()
        self._bpm_detector = BPMDetector()
        self._mood_classifier = MoodClassifier(bpm_detector=self._bpm_detector)
        self._ensure_embeddings_table()
        logger.info("AudioEmbeddings initialized (AI-powered similarity search)")

    def _ensure_embeddings_table(self):
        """Create embeddings cache table if it doesn't exist"""
        if not self.db_manager:
            return

        try:
            conn = self.db_manager.conn
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_embeddings (
                    song_id INTEGER PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    file_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (song_id) REFERENCES songs(id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_hash
                ON audio_embeddings(file_hash)
            """)

            conn.commit()
            logger.debug("Embeddings table ready")

        except sqlite3.Error as e:
            logger.error(f"Failed to create embeddings table: {e}")

    # =========================================================================
    # EMBEDDING EXTRACTION
    # =========================================================================

    def extract_embedding(self, file_path: str) -> Optional[np.ndarray]:
        """
        Extract 128D audio embedding from a song file.

        Args:
            file_path: Path to audio file (MP3, WAV, FLAC, etc.)

        Returns:
            128D numpy array embedding, or None if extraction failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("pydub required for audio embedding extraction")
            return None

        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.SAMPLE_RATE)

            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2 ** 15)  # Normalize to [-1, 1]

            features = self._feature_extractor.extract_features(samples)

            if features is None:
                return None

            # Normalize to unit vector (for cosine similarity)
            norm = np.linalg.norm(features)
            if norm > 0:
                features = features / norm

            logger.debug(f"Extracted embedding for {Path(file_path).name}: {features.shape}")
            return features

        except (OSError, ValueError) as e:
            logger.error(f"Failed to extract embedding from {file_path}: {e}")
            return None

    # =========================================================================
    # CACHING
    # =========================================================================

    def get_or_create_embedding(
        self,
        song_id: int,
        file_path: str
    ) -> Optional[np.ndarray]:
        """
        Get cached embedding or create new one.

        Args:
            song_id: Database song ID
            file_path: Path to audio file

        Returns:
            128D embedding array or None
        """
        file_hash = self._compute_file_hash(file_path)

        cached = self._get_cached_embedding(song_id, file_hash)
        if cached is not None:
            logger.debug(f"Using cached embedding for song {song_id}")
            return cached

        embedding = self.extract_embedding(file_path)

        if embedding is not None:
            self._cache_embedding(song_id, embedding, file_hash)

        return embedding

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute MD5 hash of file for cache invalidation"""
        try:
            path = Path(file_path)
            size = path.stat().st_size

            with open(path, 'rb') as f:
                first_chunk = f.read(FILE_HASH_CHUNK_SIZE)

            content = f"{size}:".encode() + first_chunk
            return hashlib.md5(content).hexdigest()

        except OSError:
            return ""

    def _get_cached_embedding(
        self,
        song_id: int,
        file_hash: str
    ) -> Optional[np.ndarray]:
        """Get embedding from cache if valid"""
        if not self.db_manager:
            return None

        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT embedding FROM audio_embeddings
                WHERE song_id = ? AND file_hash = ?
            """, (song_id, file_hash))

            row = cursor.fetchone()
            if row:
                return np.frombuffer(row[0], dtype=np.float32)

        except sqlite3.Error as e:
            logger.debug(f"Cache lookup failed: {e}")

        return None

    def _cache_embedding(
        self,
        song_id: int,
        embedding: np.ndarray,
        file_hash: str
    ):
        """Save embedding to cache"""
        if not self.db_manager:
            return

        try:
            cursor = self.db_manager.conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO audio_embeddings (song_id, embedding, file_hash)
                VALUES (?, ?, ?)
            """, (song_id, embedding.tobytes(), file_hash))

            self.db_manager.conn.commit()
            logger.debug(f"Cached embedding for song {song_id}")

        except sqlite3.Error as e:
            logger.error(f"Failed to cache embedding: {e}")

    # =========================================================================
    # SIMILARITY SEARCH
    # =========================================================================

    def find_similar(
        self,
        song_id: int,
        limit: int = 10,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Find songs similar to a given song using AI embeddings.

        Args:
            song_id: ID of the reference song
            limit: Maximum number of similar songs to return
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of dicts with 'song' and 'similarity' keys,
            sorted by similarity (highest first)
        """
        if not self.db_manager:
            logger.error("Database manager required for similarity search")
            return []

        ref_song = self.db_manager.get_song_by_id(song_id)
        if not ref_song:
            logger.error(f"Song {song_id} not found")
            return []

        ref_embedding = self.get_or_create_embedding(
            song_id,
            ref_song['file_path']
        )

        if ref_embedding is None:
            logger.error(f"Failed to get embedding for song {song_id}")
            return []

        all_songs = self.db_manager.get_all_songs()
        similar_songs = []

        for song in all_songs:
            if song['id'] == song_id:
                continue

            embedding = self.get_or_create_embedding(
                song['id'],
                song['file_path']
            )

            if embedding is None:
                continue

            similarity = self._cosine_similarity(ref_embedding, embedding)

            if similarity >= min_similarity:
                similar_songs.append({
                    'song': song,
                    'similarity': float(similarity)
                })

        similar_songs.sort(key=lambda x: x['similarity'], reverse=True)
        result = similar_songs[:limit]

        logger.info(
            f"Found {len(result)} similar songs to '{ref_song.get('title')}' "
            f"(threshold: {min_similarity})"
        )

        return result

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Returns:
            Similarity score (0.0-1.0, higher = more similar)
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        # Cosine similarity is in [-1, 1], normalize to [0, 1]
        similarity = dot_product / (norm_a * norm_b)
        return (similarity + 1) / 2

    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================

    def batch_generate_embeddings(
        self,
        progress_callback=None
    ) -> Dict[str, int]:
        """
        Generate embeddings for all songs in library.

        Args:
            progress_callback: Optional callback(current, total) for progress

        Returns:
            Dict with 'processed', 'cached', 'failed' counts
        """
        if not self.db_manager:
            return {'processed': 0, 'cached': 0, 'failed': 0}

        all_songs = self.db_manager.get_all_songs()
        total = len(all_songs)

        processed = 0
        cached = 0
        failed = 0

        for i, song in enumerate(all_songs):
            if progress_callback:
                progress_callback(i + 1, total)

            file_hash = self._compute_file_hash(song['file_path'])
            existing = self._get_cached_embedding(song['id'], file_hash)

            if existing is not None:
                cached += 1
                continue

            embedding = self.extract_embedding(song['file_path'])

            if embedding is not None:
                self._cache_embedding(song['id'], embedding, file_hash)
                processed += 1
            else:
                failed += 1

        logger.info(
            f"Batch embedding complete: {processed} processed, "
            f"{cached} cached, {failed} failed"
        )

        return {
            'processed': processed,
            'cached': cached,
            'failed': failed
        }

    def get_embedding_stats(self) -> Dict:
        """
        Get statistics about cached embeddings.

        Returns:
            Dict with embedding statistics
        """
        if not self.db_manager:
            return {'total': 0, 'coverage': 0}

        try:
            cursor = self.db_manager.conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM audio_embeddings")
            cached = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM songs")
            total = cursor.fetchone()[0]

            coverage = (cached / total * 100) if total > 0 else 0

            return {
                'cached': cached,
                'total': total,
                'coverage': round(coverage, 1),
                'embedding_dim': self.EMBEDDING_DIM
            }

        except sqlite3.Error as e:
            logger.error(f"Failed to get stats: {e}")
            return {'total': 0, 'coverage': 0}

    # =========================================================================
    # BPM + MOOD (delegated)
    # =========================================================================

    def detect_bpm(self, file_path: str) -> Optional[int]:
        """Detect BPM (beats per minute) of an audio file."""
        return self._bpm_detector.detect(file_path)

    def classify_mood(self, file_path: str) -> Optional[Dict]:
        """Classify the mood/energy of an audio file."""
        return self._mood_classifier.classify(file_path)

    def analyze_song(self, file_path: str) -> Optional[Dict]:
        """
        Complete audio analysis: embedding, BPM, and mood.

        Args:
            file_path: Path to audio file

        Returns:
            Dict with 'bpm', 'mood', 'energy', 'valence', or None if failed
        """
        if not Path(file_path).exists():
            return None

        try:
            mood_result = self.classify_mood(file_path)

            if mood_result:
                return {
                    'bpm': mood_result.get('bpm'),
                    'mood': mood_result.get('mood'),
                    'energy': mood_result.get('energy'),
                    'valence': mood_result.get('valence'),
                    'confidence': mood_result.get('confidence')
                }

            # Fallback: just BPM
            bpm = self.detect_bpm(file_path)
            return {
                'bpm': bpm,
                'mood': None,
                'energy': None,
                'valence': None,
                'confidence': None
            }

        except (OSError, ValueError) as e:
            logger.error(f"Song analysis failed: {e}")
            return None

    # =========================================================================
    # DELEGATION (backward compat for tests/consumers accessing internals)
    # =========================================================================

    def _extract_audio_features(self, samples: np.ndarray) -> Optional[np.ndarray]:
        return self._feature_extractor.extract_features(samples)

    def _compute_band_energies(self, magnitude: np.ndarray, freqs: np.ndarray) -> np.ndarray:
        return self._feature_extractor.compute_band_energies(magnitude, freqs)

    def _extract_temporal_features(self, rms_values) -> list:
        return self._feature_extractor.extract_temporal_features(rms_values)

    def _estimate_bpm(self, samples: np.ndarray) -> Optional[int]:
        return self._bpm_detector.estimate_bpm(samples)

    def _extract_mood_features(self, samples: np.ndarray) -> Optional[Dict]:
        return self._mood_classifier.extract_mood_features(samples)

    def _classify_mood_from_features(self, features: Dict) -> Dict:
        return self._mood_classifier.classify_from_features(features)
