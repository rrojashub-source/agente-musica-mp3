"""
Audio Embeddings - AI-Powered Audio Analysis (Phase 9)

Extract audio features and generate embeddings for "Find Similar Songs".
Also provides BPM detection and Mood/Energy classification.

Features:
- Extract audio features using FFT analysis (no librosa dependency)
- Generate compact 128D embeddings for each song
- Cosine similarity for finding similar songs
- BPM (tempo) detection via autocorrelation
- Mood/Energy classification (Energetic, Happy, Calm, Sad, Intense)
- SQLite cache for persistent embeddings

This is REAL AI: Uses signal processing + ML for audio analysis.
No external API required - works 100% offline.

Created: December 8, 2025
Updated: December 8, 2025 - Added BPM detection and Mood classification
Author: NEXUS + Ricardo
"""
import logging
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Check optional dependencies
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available - audio feature extraction limited")


class AudioEmbeddings:
    """
    AI-powered audio embeddings for similarity search.

    Extracts audio features and creates 128D embeddings that capture:
    - Spectral characteristics (brightness, rolloff)
    - Rhythmic patterns (tempo estimation)
    - Energy distribution across frequency bands
    - Timbral fingerprint

    Usage:
        embeddings = AudioEmbeddings(db_manager)

        # Generate embedding for a song
        embedding = embeddings.extract_embedding('/path/to/song.mp3')

        # Find similar songs
        similar = embeddings.find_similar(song_id, limit=10)
    """

    # Feature extraction constants
    EMBEDDING_DIM = 128  # Compact embedding dimension
    SAMPLE_RATE = 22050  # Standard sample rate for analysis
    FRAME_SIZE = 2048    # FFT frame size
    HOP_SIZE = 512       # FFT hop size
    NUM_BANDS = 24       # Mel-like frequency bands

    def __init__(self, db_manager=None):
        """
        Initialize AudioEmbeddings

        Args:
            db_manager: Optional DatabaseManager for caching embeddings
        """
        self.db_manager = db_manager
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

            # Index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_hash
                ON audio_embeddings(file_hash)
            """)

            conn.commit()
            logger.debug("Embeddings table ready")

        except Exception as e:
            logger.error(f"Failed to create embeddings table: {e}")

    def extract_embedding(self, file_path: str) -> Optional[np.ndarray]:
        """
        Extract 128D audio embedding from a song file.

        This is the core AI function that analyzes audio content.

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
            # Load audio file
            audio = AudioSegment.from_file(file_path)

            # Convert to mono and resample
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.SAMPLE_RATE)

            # Get raw samples as numpy array
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2 ** 15)  # Normalize to [-1, 1]

            # Extract features
            features = self._extract_audio_features(samples)

            if features is None:
                return None

            # Normalize to unit vector (for cosine similarity)
            norm = np.linalg.norm(features)
            if norm > 0:
                features = features / norm

            logger.debug(f"Extracted embedding for {Path(file_path).name}: {features.shape}")
            return features

        except Exception as e:
            logger.error(f"Failed to extract embedding from {file_path}: {e}")
            return None

    def _extract_audio_features(self, samples: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract audio features from raw samples using FFT analysis.

        Features extracted:
        - Spectral centroid (brightness)
        - Spectral rolloff
        - Spectral flatness
        - Band energy distribution (24 bands)
        - Zero crossing rate
        - RMS energy statistics
        - Temporal patterns

        Args:
            samples: Audio samples as numpy array

        Returns:
            128D feature vector
        """
        try:
            # Ensure we have enough samples
            min_samples = self.FRAME_SIZE * 10
            if len(samples) < min_samples:
                logger.warning("Audio too short for feature extraction")
                return None

            # Calculate number of frames
            num_frames = (len(samples) - self.FRAME_SIZE) // self.HOP_SIZE + 1

            # Initialize feature accumulators
            spectral_centroids = []
            spectral_rolloffs = []
            spectral_flatness = []
            band_energies = []
            zcrs = []
            rms_values = []

            # Process each frame
            for i in range(num_frames):
                start = i * self.HOP_SIZE
                end = start + self.FRAME_SIZE
                frame = samples[start:end]

                # Apply Hanning window
                window = np.hanning(len(frame))
                windowed_frame = frame * window

                # FFT
                fft = np.fft.rfft(windowed_frame)
                magnitude = np.abs(fft)

                # Frequency axis
                freqs = np.fft.rfftfreq(len(windowed_frame), 1/self.SAMPLE_RATE)

                # Spectral centroid (brightness)
                if np.sum(magnitude) > 0:
                    centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
                else:
                    centroid = 0
                spectral_centroids.append(centroid)

                # Spectral rolloff (frequency below which 85% of energy)
                cumsum = np.cumsum(magnitude)
                if cumsum[-1] > 0:
                    rolloff_idx = np.searchsorted(cumsum, 0.85 * cumsum[-1])
                    rolloff = freqs[min(rolloff_idx, len(freqs)-1)]
                else:
                    rolloff = 0
                spectral_rolloffs.append(rolloff)

                # Spectral flatness (tonality measure)
                eps = 1e-10
                geo_mean = np.exp(np.mean(np.log(magnitude + eps)))
                arith_mean = np.mean(magnitude)
                flatness = geo_mean / (arith_mean + eps)
                spectral_flatness.append(flatness)

                # Band energies (mel-like distribution)
                band_energy = self._compute_band_energies(magnitude, freqs)
                band_energies.append(band_energy)

                # Zero crossing rate
                zcr = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame))
                zcrs.append(zcr)

                # RMS energy
                rms = np.sqrt(np.mean(frame ** 2))
                rms_values.append(rms)

            # Aggregate features across time
            features = []

            # Spectral centroid statistics (4 features)
            sc = np.array(spectral_centroids)
            features.extend([np.mean(sc), np.std(sc), np.min(sc), np.max(sc)])

            # Spectral rolloff statistics (4 features)
            sr = np.array(spectral_rolloffs)
            features.extend([np.mean(sr), np.std(sr), np.min(sr), np.max(sr)])

            # Spectral flatness statistics (4 features)
            sf = np.array(spectral_flatness)
            features.extend([np.mean(sf), np.std(sf), np.min(sf), np.max(sf)])

            # ZCR statistics (4 features)
            z = np.array(zcrs)
            features.extend([np.mean(z), np.std(z), np.min(z), np.max(z)])

            # RMS energy statistics (4 features)
            r = np.array(rms_values)
            features.extend([np.mean(r), np.std(r), np.min(r), np.max(r)])

            # Band energy statistics (24 bands * 4 stats = 96 features)
            band_array = np.array(band_energies)
            for band_idx in range(self.NUM_BANDS):
                band = band_array[:, band_idx]
                features.extend([np.mean(band), np.std(band), np.min(band), np.max(band)])

            # Temporal patterns (12 features) - rhythm/tempo estimation
            temporal_features = self._extract_temporal_features(rms_values)
            features.extend(temporal_features)

            # Convert to numpy array
            feature_vector = np.array(features, dtype=np.float32)

            # Ensure exactly 128 dimensions
            if len(feature_vector) < self.EMBEDDING_DIM:
                # Pad with zeros
                feature_vector = np.pad(
                    feature_vector,
                    (0, self.EMBEDDING_DIM - len(feature_vector))
                )
            elif len(feature_vector) > self.EMBEDDING_DIM:
                # Truncate (shouldn't happen with correct feature count)
                feature_vector = feature_vector[:self.EMBEDDING_DIM]

            return feature_vector

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None

    def _compute_band_energies(
        self,
        magnitude: np.ndarray,
        freqs: np.ndarray
    ) -> np.ndarray:
        """
        Compute energy in mel-like frequency bands.

        Uses logarithmic frequency distribution similar to mel scale.

        Args:
            magnitude: FFT magnitude array
            freqs: Frequency axis

        Returns:
            Array of energies for each band
        """
        # Mel-like band boundaries (logarithmic)
        min_freq = 20
        max_freq = min(self.SAMPLE_RATE / 2, 8000)

        # Create logarithmic band boundaries
        mel_min = 2595 * np.log10(1 + min_freq / 700)
        mel_max = 2595 * np.log10(1 + max_freq / 700)
        mel_points = np.linspace(mel_min, mel_max, self.NUM_BANDS + 1)
        hz_points = 700 * (10 ** (mel_points / 2595) - 1)

        # Calculate energy in each band
        band_energies = np.zeros(self.NUM_BANDS)

        for i in range(self.NUM_BANDS):
            low_freq = hz_points[i]
            high_freq = hz_points[i + 1]

            # Find frequency indices in this band
            band_mask = (freqs >= low_freq) & (freqs < high_freq)

            if np.any(band_mask):
                band_energies[i] = np.sum(magnitude[band_mask] ** 2)

        # Normalize
        total_energy = np.sum(band_energies)
        if total_energy > 0:
            band_energies = band_energies / total_energy

        return band_energies

    def _extract_temporal_features(self, rms_values: List[float]) -> List[float]:
        """
        Extract temporal/rhythmic features from RMS envelope.

        Uses autocorrelation to estimate tempo-related patterns.

        Args:
            rms_values: List of RMS values per frame

        Returns:
            12 temporal features
        """
        rms = np.array(rms_values)

        features = []

        # Onset strength (differences in energy)
        onset = np.diff(rms)
        onset = np.maximum(onset, 0)  # Only positive changes

        # Onset statistics (4 features)
        features.extend([
            np.mean(onset),
            np.std(onset),
            np.max(onset) if len(onset) > 0 else 0,
            np.sum(onset > np.mean(onset))  # Number of onsets
        ])

        # Autocorrelation for tempo estimation (4 features)
        if len(rms) > 100:
            # Compute autocorrelation
            autocorr = np.correlate(rms - np.mean(rms), rms - np.mean(rms), mode='full')
            autocorr = autocorr[len(autocorr)//2:]  # Take positive lags

            # Normalize
            if autocorr[0] > 0:
                autocorr = autocorr / autocorr[0]

            # Find peaks (tempo candidates)
            # Typical tempo range: 60-180 BPM
            min_lag = int(60 / (180/60) * (self.SAMPLE_RATE / self.HOP_SIZE))
            max_lag = int(60 / (60/60) * (self.SAMPLE_RATE / self.HOP_SIZE))

            search_range = autocorr[min_lag:max_lag] if max_lag < len(autocorr) else autocorr

            if len(search_range) > 0:
                peak_idx = np.argmax(search_range)
                peak_val = search_range[peak_idx]

                features.extend([
                    peak_val,  # Tempo confidence
                    peak_idx / len(search_range),  # Relative tempo position
                    np.mean(autocorr[:50]),  # Short-term periodicity
                    np.std(autocorr[:100])   # Periodicity variation
                ])
            else:
                features.extend([0, 0, 0, 0])
        else:
            features.extend([0, 0, 0, 0])

        # Energy envelope shape (4 features)
        if len(rms) >= 4:
            quartile_size = len(rms) // 4
            q1_energy = np.mean(rms[:quartile_size])
            q2_energy = np.mean(rms[quartile_size:2*quartile_size])
            q3_energy = np.mean(rms[2*quartile_size:3*quartile_size])
            q4_energy = np.mean(rms[3*quartile_size:])

            features.extend([q1_energy, q2_energy, q3_energy, q4_energy])
        else:
            features.extend([0, 0, 0, 0])

        return features

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
        # Calculate file hash for cache invalidation
        file_hash = self._compute_file_hash(file_path)

        # Try to get from cache
        cached = self._get_cached_embedding(song_id, file_hash)
        if cached is not None:
            logger.debug(f"Using cached embedding for song {song_id}")
            return cached

        # Extract new embedding
        embedding = self.extract_embedding(file_path)

        if embedding is not None:
            # Save to cache
            self._cache_embedding(song_id, embedding, file_hash)

        return embedding

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute MD5 hash of file for cache invalidation"""
        try:
            # Use file size + first 4KB for fast hash
            path = Path(file_path)
            size = path.stat().st_size

            with open(path, 'rb') as f:
                first_chunk = f.read(4096)

            content = f"{size}:{first_chunk}".encode() if isinstance(first_chunk, str) else f"{size}:".encode() + first_chunk
            return hashlib.md5(content).hexdigest()

        except Exception:
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

        except Exception as e:
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

            # Upsert embedding
            cursor.execute("""
                INSERT OR REPLACE INTO audio_embeddings (song_id, embedding, file_hash)
                VALUES (?, ?, ?)
            """, (song_id, embedding.tobytes(), file_hash))

            self.db_manager.conn.commit()
            logger.debug(f"Cached embedding for song {song_id}")

        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")

    def find_similar(
        self,
        song_id: int,
        limit: int = 10,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Find songs similar to a given song using AI embeddings.

        This is the main similarity search function.

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

        # Get reference song
        ref_song = self.db_manager.get_song_by_id(song_id)
        if not ref_song:
            logger.error(f"Song {song_id} not found")
            return []

        # Get reference embedding
        ref_embedding = self.get_or_create_embedding(
            song_id,
            ref_song['file_path']
        )

        if ref_embedding is None:
            logger.error(f"Failed to get embedding for song {song_id}")
            return []

        # Get all songs from library
        all_songs = self.db_manager.get_all_songs()

        # Calculate similarities
        similar_songs = []

        for song in all_songs:
            if song['id'] == song_id:
                continue  # Skip reference song

            # Get or create embedding for this song
            embedding = self.get_or_create_embedding(
                song['id'],
                song['file_path']
            )

            if embedding is None:
                continue

            # Calculate cosine similarity
            similarity = self._cosine_similarity(ref_embedding, embedding)

            if similarity >= min_similarity:
                similar_songs.append({
                    'song': song,
                    'similarity': float(similarity)
                })

        # Sort by similarity (highest first)
        similar_songs.sort(key=lambda x: x['similarity'], reverse=True)

        # Return top results
        result = similar_songs[:limit]

        logger.info(
            f"Found {len(result)} similar songs to '{ref_song.get('title')}' "
            f"(threshold: {min_similarity})"
        )

        return result

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            a, b: Embedding vectors

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

    def batch_generate_embeddings(
        self,
        progress_callback=None
    ) -> Dict[str, int]:
        """
        Generate embeddings for all songs in library.

        Useful for pre-computing embeddings in background.

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

            # Check if already cached
            file_hash = self._compute_file_hash(song['file_path'])
            existing = self._get_cached_embedding(song['id'], file_hash)

            if existing is not None:
                cached += 1
                continue

            # Generate new embedding
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

            # Count cached embeddings
            cursor.execute("SELECT COUNT(*) FROM audio_embeddings")
            cached = cursor.fetchone()[0]

            # Count total songs
            cursor.execute("SELECT COUNT(*) FROM songs")
            total = cursor.fetchone()[0]

            coverage = (cached / total * 100) if total > 0 else 0

            return {
                'cached': cached,
                'total': total,
                'coverage': round(coverage, 1),
                'embedding_dim': self.EMBEDDING_DIM
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'total': 0, 'coverage': 0}

    # =========================================================================
    # BPM DETECTION
    # =========================================================================

    def detect_bpm(self, file_path: str) -> Optional[int]:
        """
        Detect BPM (beats per minute) of an audio file.

        Uses onset detection + autocorrelation for tempo estimation.

        Args:
            file_path: Path to audio file

        Returns:
            Estimated BPM (60-200 range), or None if detection failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("pydub required for BPM detection")
            return None

        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            # Load audio file
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.SAMPLE_RATE)

            # Get raw samples
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2 ** 15)

            # Use middle 30 seconds for more stable BPM
            sample_duration = 30 * self.SAMPLE_RATE
            if len(samples) > sample_duration:
                start = (len(samples) - sample_duration) // 2
                samples = samples[start:start + sample_duration]

            bpm = self._estimate_bpm(samples)

            logger.debug(f"Detected BPM for {Path(file_path).name}: {bpm}")
            return bpm

        except Exception as e:
            logger.error(f"BPM detection failed for {file_path}: {e}")
            return None

    def _estimate_bpm(self, samples: np.ndarray) -> Optional[int]:
        """
        Estimate BPM using onset detection and autocorrelation.

        Args:
            samples: Audio samples

        Returns:
            Estimated BPM or None
        """
        try:
            # Calculate onset envelope (energy changes over time)
            frame_length = 1024
            hop_length = 512

            num_frames = (len(samples) - frame_length) // hop_length + 1
            onset_env = []

            prev_energy = 0
            for i in range(num_frames):
                start = i * hop_length
                end = start + frame_length
                frame = samples[start:end]

                # RMS energy
                energy = np.sqrt(np.mean(frame ** 2))

                # Onset = positive energy difference
                onset = max(0, energy - prev_energy)
                onset_env.append(onset)
                prev_energy = energy

            onset_env = np.array(onset_env)

            # Normalize
            if np.max(onset_env) > 0:
                onset_env = onset_env / np.max(onset_env)

            # Autocorrelation for periodicity detection
            autocorr = np.correlate(onset_env, onset_env, mode='full')
            autocorr = autocorr[len(autocorr)//2:]

            # Normalize
            if autocorr[0] > 0:
                autocorr = autocorr / autocorr[0]

            # BPM search range: 60-200 BPM
            # Convert BPM to lag in frames
            fps = self.SAMPLE_RATE / hop_length  # frames per second

            min_bpm, max_bpm = 60, 200
            min_lag = int(fps * 60 / max_bpm)  # lag for max BPM
            max_lag = int(fps * 60 / min_bpm)  # lag for min BPM

            # Ensure we don't exceed array bounds
            max_lag = min(max_lag, len(autocorr) - 1)

            if max_lag <= min_lag:
                return None

            # Find peak in search range
            search_range = autocorr[min_lag:max_lag]
            peak_idx = np.argmax(search_range) + min_lag

            # Convert lag to BPM
            bpm = int(round(fps * 60 / peak_idx))

            # Sanity check
            if 60 <= bpm <= 200:
                return bpm

            # Try octave correction (common BPM detection issue)
            if bpm < 60:
                bpm *= 2
            elif bpm > 200:
                bpm //= 2

            if 60 <= bpm <= 200:
                return bpm

            return None

        except Exception as e:
            logger.error(f"BPM estimation failed: {e}")
            return None

    # =========================================================================
    # MOOD / ENERGY CLASSIFICATION
    # =========================================================================

    # Mood categories
    MOODS = ['Energetic', 'Happy', 'Calm', 'Sad', 'Intense']

    def classify_mood(self, file_path: str) -> Optional[Dict]:
        """
        Classify the mood/energy of an audio file.

        Uses audio features to classify into mood categories:
        - Energetic: High tempo, high energy, bright sound
        - Happy: Major key feel, moderate-high tempo, bright
        - Calm: Low tempo, low energy, warm sound
        - Sad: Minor key feel, slow tempo, dark sound
        - Intense: High energy, aggressive, loud

        Args:
            file_path: Path to audio file

        Returns:
            Dict with 'mood' (primary), 'energy' (0-100), 'valence' (0-100),
            and 'confidence' (0-100), or None if classification failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("pydub required for mood classification")
            return None

        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            # Load audio
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.SAMPLE_RATE)

            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2 ** 15)

            # Extract mood features
            mood_features = self._extract_mood_features(samples)

            if mood_features is None:
                return None

            # Classify based on features
            result = self._classify_mood_from_features(mood_features)

            logger.debug(f"Classified mood for {Path(file_path).name}: {result['mood']}")
            return result

        except Exception as e:
            logger.error(f"Mood classification failed for {file_path}: {e}")
            return None

    def _extract_mood_features(self, samples: np.ndarray) -> Optional[Dict]:
        """
        Extract features relevant to mood classification.

        Args:
            samples: Audio samples

        Returns:
            Dict with mood-relevant features
        """
        try:
            if len(samples) < self.FRAME_SIZE * 10:
                return None

            # Calculate various features
            num_frames = (len(samples) - self.FRAME_SIZE) // self.HOP_SIZE + 1

            spectral_centroids = []
            spectral_flatness_vals = []
            rms_values = []
            zcrs = []
            low_energy_ratios = []

            for i in range(num_frames):
                start = i * self.HOP_SIZE
                end = start + self.FRAME_SIZE
                frame = samples[start:end]

                window = np.hanning(len(frame))
                windowed = frame * window

                # FFT
                fft = np.fft.rfft(windowed)
                magnitude = np.abs(fft)
                freqs = np.fft.rfftfreq(len(windowed), 1/self.SAMPLE_RATE)

                # Spectral centroid (brightness)
                if np.sum(magnitude) > 0:
                    centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
                else:
                    centroid = 0
                spectral_centroids.append(centroid)

                # Spectral flatness (noisiness vs tonal)
                eps = 1e-10
                geo_mean = np.exp(np.mean(np.log(magnitude + eps)))
                arith_mean = np.mean(magnitude)
                flatness = geo_mean / (arith_mean + eps)
                spectral_flatness_vals.append(flatness)

                # RMS energy
                rms = np.sqrt(np.mean(frame ** 2))
                rms_values.append(rms)

                # Zero crossing rate
                zcr = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame))
                zcrs.append(zcr)

            # Low energy ratio (percentage of frames with below-average energy)
            avg_rms = np.mean(rms_values)
            low_energy_ratio = np.sum(np.array(rms_values) < avg_rms) / len(rms_values)

            # Tempo estimation
            bpm = self._estimate_bpm(samples)

            # Aggregate features
            return {
                'brightness': np.mean(spectral_centroids),
                'brightness_std': np.std(spectral_centroids),
                'flatness': np.mean(spectral_flatness_vals),
                'energy': np.mean(rms_values),
                'energy_std': np.std(rms_values),
                'zcr': np.mean(zcrs),
                'low_energy_ratio': low_energy_ratio,
                'tempo': bpm or 100,  # Default to 100 if detection failed
                'dynamic_range': np.max(rms_values) - np.min(rms_values)
            }

        except Exception as e:
            logger.error(f"Mood feature extraction failed: {e}")
            return None

    def _classify_mood_from_features(self, features: Dict) -> Dict:
        """
        Classify mood from extracted features using rule-based heuristics.

        This is a simplified classifier - could be replaced with ML model.

        Args:
            features: Dict of audio features

        Returns:
            Classification result with mood, energy, valence, confidence
        """
        # Normalize features to 0-100 scale
        brightness = min(100, features['brightness'] / 40)  # ~4000Hz max
        tempo = min(100, max(0, (features['tempo'] - 60) / 1.4))  # 60-200 BPM
        energy = min(100, features['energy'] * 500)  # RMS ~0-0.2
        flatness = min(100, features['flatness'] * 100)
        zcr = min(100, features['zcr'] * 1000)
        dynamics = min(100, features['dynamic_range'] * 500)

        # Calculate composite scores
        energy_score = (energy * 0.5 + tempo * 0.3 + dynamics * 0.2)
        valence_score = (brightness * 0.4 + (100 - flatness) * 0.3 + tempo * 0.3)

        # Mood classification rules
        mood_scores = {
            'Energetic': (tempo * 0.4 + energy * 0.4 + brightness * 0.2),
            'Happy': (valence_score * 0.5 + tempo * 0.3 + brightness * 0.2),
            'Calm': (100 - energy_score) * 0.5 + (100 - tempo) * 0.3 + (100 - brightness) * 0.2,
            'Sad': (100 - valence_score) * 0.4 + (100 - tempo) * 0.4 + flatness * 0.2,
            'Intense': energy * 0.4 + dynamics * 0.3 + zcr * 0.3
        }

        # Find primary mood
        primary_mood = max(mood_scores, key=mood_scores.get)
        confidence = min(100, mood_scores[primary_mood])

        return {
            'mood': primary_mood,
            'energy': int(energy_score),
            'valence': int(valence_score),
            'confidence': int(confidence),
            'bpm': features['tempo']
        }

    def analyze_song(self, file_path: str) -> Optional[Dict]:
        """
        Complete audio analysis: embedding, BPM, and mood.

        Convenience method that runs all analysis in one call.

        Args:
            file_path: Path to audio file

        Returns:
            Dict with 'bpm', 'mood', 'energy', 'valence', or None if failed
        """
        if not Path(file_path).exists():
            return None

        try:
            # Get mood classification (includes BPM)
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

        except Exception as e:
            logger.error(f"Song analysis failed: {e}")
            return None
