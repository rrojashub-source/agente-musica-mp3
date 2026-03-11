"""
Audio Feature Extractor — FFT-based audio analysis.

Extracts spectral, temporal, and energy features from raw audio samples
to produce a compact 128D embedding vector.

Part of the AudioEmbeddings split (Phase 2.3).

Created: 2026-03-11 (extracted from audio_embeddings.py)
"""
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Shared constants (canonical definitions)
EMBEDDING_DIM = 128
SAMPLE_RATE = 22050
FRAME_SIZE = 2048
HOP_SIZE = 512
NUM_BANDS = 24


class AudioFeatureExtractor:
    """
    Extracts audio features from raw samples using FFT analysis.

    Produces a 128D feature vector capturing:
    - Spectral characteristics (brightness, rolloff, flatness)
    - Energy distribution across 24 mel-like frequency bands
    - Zero crossing rate and RMS energy statistics
    - Temporal/rhythmic patterns via autocorrelation
    """

    def __init__(
        self,
        embedding_dim: int = EMBEDDING_DIM,
        sample_rate: int = SAMPLE_RATE,
        frame_size: int = FRAME_SIZE,
        hop_size: int = HOP_SIZE,
        num_bands: int = NUM_BANDS,
    ):
        self.embedding_dim = embedding_dim
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.hop_size = hop_size
        self.num_bands = num_bands

    def extract_features(self, samples: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract audio features from raw samples.

        Features extracted (128D total):
        - Spectral centroid statistics (4)
        - Spectral rolloff statistics (4)
        - Spectral flatness statistics (4)
        - ZCR statistics (4)
        - RMS energy statistics (4)
        - Band energy statistics (24 bands * 4 = 96)
        - Temporal patterns (12)

        Args:
            samples: Audio samples as numpy array

        Returns:
            128D feature vector, or None if extraction failed
        """
        try:
            min_samples = self.frame_size * 10
            if len(samples) < min_samples:
                logger.warning("Audio too short for feature extraction")
                return None

            num_frames = (len(samples) - self.frame_size) // self.hop_size + 1

            spectral_centroids = []
            spectral_rolloffs = []
            spectral_flatness = []
            band_energies = []
            zcrs = []
            rms_values = []

            for i in range(num_frames):
                start = i * self.hop_size
                end = start + self.frame_size
                frame = samples[start:end]

                window = np.hanning(len(frame))
                windowed_frame = frame * window

                fft = np.fft.rfft(windowed_frame)
                magnitude = np.abs(fft)
                freqs = np.fft.rfftfreq(len(windowed_frame), 1/self.sample_rate)

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
                band_energy = self.compute_band_energies(magnitude, freqs)
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
            for band_idx in range(self.num_bands):
                band = band_array[:, band_idx]
                features.extend([np.mean(band), np.std(band), np.min(band), np.max(band)])

            # Temporal patterns (12 features)
            temporal_features = self.extract_temporal_features(rms_values)
            features.extend(temporal_features)

            feature_vector = np.array(features, dtype=np.float32)

            # Ensure exactly 128 dimensions
            if len(feature_vector) < self.embedding_dim:
                feature_vector = np.pad(
                    feature_vector,
                    (0, self.embedding_dim - len(feature_vector))
                )
            elif len(feature_vector) > self.embedding_dim:
                feature_vector = feature_vector[:self.embedding_dim]

            return feature_vector

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None

    def compute_band_energies(
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
            Array of energies for each band (normalized to sum to 1)
        """
        min_freq = 20
        max_freq = min(self.sample_rate / 2, 8000)

        # Create logarithmic band boundaries
        mel_min = 2595 * np.log10(1 + min_freq / 700)
        mel_max = 2595 * np.log10(1 + max_freq / 700)
        mel_points = np.linspace(mel_min, mel_max, self.num_bands + 1)
        hz_points = 700 * (10 ** (mel_points / 2595) - 1)

        band_energies = np.zeros(self.num_bands)

        for i in range(self.num_bands):
            low_freq = hz_points[i]
            high_freq = hz_points[i + 1]
            band_mask = (freqs >= low_freq) & (freqs < high_freq)

            if np.any(band_mask):
                band_energies[i] = np.sum(magnitude[band_mask] ** 2)

        # Normalize
        total_energy = np.sum(band_energies)
        if total_energy > 0:
            band_energies = band_energies / total_energy

        return band_energies

    def extract_temporal_features(self, rms_values: List[float]) -> List[float]:
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

        # Onset strength (positive energy differences)
        onset = np.diff(rms)
        onset = np.maximum(onset, 0)

        # Onset statistics (4 features)
        features.extend([
            np.mean(onset),
            np.std(onset),
            np.max(onset) if len(onset) > 0 else 0,
            np.sum(onset > np.mean(onset))  # Number of onsets
        ])

        # Autocorrelation for tempo estimation (4 features)
        if len(rms) > 100:
            autocorr = np.correlate(rms - np.mean(rms), rms - np.mean(rms), mode='full')
            autocorr = autocorr[len(autocorr)//2:]

            if autocorr[0] > 0:
                autocorr = autocorr / autocorr[0]

            # Typical tempo range: 60-180 BPM
            min_lag = int(60 / (180/60) * (self.sample_rate / self.hop_size))
            max_lag = int(60 / (60/60) * (self.sample_rate / self.hop_size))

            search_range = autocorr[min_lag:max_lag] if max_lag < len(autocorr) else autocorr

            if len(search_range) > 0:
                peak_idx = np.argmax(search_range)
                peak_val = search_range[peak_idx]

                features.extend([
                    peak_val,                          # Tempo confidence
                    peak_idx / len(search_range),      # Relative tempo position
                    np.mean(autocorr[:50]),             # Short-term periodicity
                    np.std(autocorr[:100])              # Periodicity variation
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
