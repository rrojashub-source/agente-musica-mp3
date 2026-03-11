"""
Mood Classifier — Audio mood/energy classification.

Classifies audio into mood categories using spectral + temporal features
and rule-based heuristics.

Part of the AudioEmbeddings split (Phase 2.3).

Created: 2026-03-11 (extracted from audio_embeddings.py)
"""
import logging
from pathlib import Path
from typing import Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from core.audio_feature_extractor import SAMPLE_RATE, FRAME_SIZE, HOP_SIZE
from core.bpm_detector import BPMDetector

# Mood categories
MOODS = ['Energetic', 'Happy', 'Calm', 'Sad', 'Intense']


class MoodClassifier:
    """
    Audio mood/energy classifier.

    Uses spectral + temporal features to classify audio into:
    - Energetic: High tempo, high energy, bright sound
    - Happy: Major key feel, moderate-high tempo, bright
    - Calm: Low tempo, low energy, warm sound
    - Sad: Minor key feel, slow tempo, dark sound
    - Intense: High energy, aggressive, loud
    """

    def __init__(
        self,
        bpm_detector: BPMDetector = None,
        sample_rate: int = SAMPLE_RATE,
        frame_size: int = FRAME_SIZE,
        hop_size: int = HOP_SIZE,
    ):
        self.bpm_detector = bpm_detector or BPMDetector(sample_rate)
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.hop_size = hop_size

    def classify(self, file_path: str) -> Optional[Dict]:
        """
        Classify the mood/energy of an audio file.

        Args:
            file_path: Path to audio file

        Returns:
            Dict with 'mood', 'energy' (0-100), 'valence' (0-100),
            'confidence' (0-100), and 'bpm', or None if failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("pydub required for mood classification")
            return None

        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.sample_rate)

            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2 ** 15)

            mood_features = self.extract_mood_features(samples)

            if mood_features is None:
                return None

            result = self.classify_from_features(mood_features)

            logger.debug(f"Classified mood for {Path(file_path).name}: {result['mood']}")
            return result

        except Exception as e:
            logger.error(f"Mood classification failed for {file_path}: {e}")
            return None

    def extract_mood_features(self, samples: np.ndarray) -> Optional[Dict]:
        """
        Extract features relevant to mood classification.

        Args:
            samples: Audio samples

        Returns:
            Dict with mood-relevant features, or None if audio too short
        """
        try:
            if len(samples) < self.frame_size * 10:
                return None

            num_frames = (len(samples) - self.frame_size) // self.hop_size + 1

            spectral_centroids = []
            spectral_flatness_vals = []
            rms_values = []
            zcrs = []

            for i in range(num_frames):
                start = i * self.hop_size
                end = start + self.frame_size
                frame = samples[start:end]

                window = np.hanning(len(frame))
                windowed = frame * window

                fft = np.fft.rfft(windowed)
                magnitude = np.abs(fft)
                freqs = np.fft.rfftfreq(len(windowed), 1/self.sample_rate)

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
            bpm = self.bpm_detector.estimate_bpm(samples)

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

    def classify_from_features(self, features: Dict) -> Dict:
        """
        Classify mood from extracted features using rule-based heuristics.

        Args:
            features: Dict of audio features

        Returns:
            Dict with mood, energy (0-100), valence (0-100),
            confidence (0-100), bpm
        """
        # Normalize features to 0-100 scale
        brightness = min(100, features['brightness'] / 40)     # ~4000Hz max
        tempo = min(100, max(0, (features['tempo'] - 60) / 1.4))  # 60-200 BPM
        energy = min(100, features['energy'] * 500)              # RMS ~0-0.2
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

        primary_mood = max(mood_scores, key=mood_scores.get)
        confidence = min(100, mood_scores[primary_mood])

        return {
            'mood': primary_mood,
            'energy': int(energy_score),
            'valence': int(valence_score),
            'confidence': int(confidence),
            'bpm': features['tempo']
        }
