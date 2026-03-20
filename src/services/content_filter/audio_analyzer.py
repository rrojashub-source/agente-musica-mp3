"""
Audio Analyzer - Tier 3 content classification using audio features

Analyzes audio characteristics to detect:
- Energy level (calm vs intense)
- Valence (happy vs sad)
- Children's music patterns
- Speechiness (vocal content)

Dependencies:
    pip install librosa numpy

Created: December 8, 2025
"""

import logging
from typing import Any, Optional

from .classifier import ContentScore

logger = logging.getLogger(__name__)

# Check if librosa is available
try:
    import librosa
    import numpy as np

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    librosa: Any = None  # type: ignore[no-redef]
    np: Any = None  # type: ignore[no-redef]
    logger.warning("librosa not available: pip install librosa numpy")


class AudioAnalyzer:
    """
    Analyzes audio features for content classification.

    Requires librosa and numpy to be installed.
    Raises ImportError on instantiation if dependencies are missing.
    """

    def __init__(self) -> None:
        if not LIBROSA_AVAILABLE:
            raise ImportError("librosa is required: pip install librosa numpy")

    def analyze(self, file_path: str, duration: float = 30.0) -> Optional[ContentScore]:
        """
        Analyze audio file for content characteristics

        Args:
            file_path: Path to audio file
            duration: Seconds to analyze (default 30s for speed)

        Returns:
            ContentScore or None on error
        """
        try:
            # Load audio (first 30 seconds for speed)
            y, sr = librosa.load(file_path, duration=duration, sr=22050)

            if len(y) == 0:
                logger.warning(f"Empty audio file: {file_path}")
                return None

            # Extract features
            features = self._extract_features(y, sr)  # type: ignore[arg-type]

            # Convert to content score
            return self._features_to_score(features)

        except Exception as e:  # librosa raises diverse errors on corrupt/unsupported audio
            logger.error(f"Audio analysis failed for {file_path}: {e}")
            return None

    def _extract_features(self, y: Any, sr: int) -> dict[str, Any]:
        """Extract audio features similar to Spotify's API"""
        features: dict[str, Any] = {}

        # Tempo (BPM)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features["tempo"] = float(tempo)

        # RMS Energy
        rms = librosa.feature.rms(y=y)[0]
        features["energy"] = float(np.mean(rms))
        features["energy_std"] = float(np.std(rms))

        # Spectral centroid (brightness)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        features["brightness"] = float(np.mean(centroid))

        # Zero crossing rate (noisiness/texture)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        features["noisiness"] = float(np.mean(zcr))

        # Spectral rolloff
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        features["rolloff"] = float(np.mean(rolloff))

        # MFCC (timbre characteristics)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features["mfcc_mean"] = [float(np.mean(m)) for m in mfccs]  # type: ignore[assignment]

        # Chroma features (harmonic content)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features["chroma_std"] = float(np.std(chroma))  # Harmonic complexity

        # Estimate valence from mode and chroma
        # Major key = happier, Minor key = sadder (simplified)
        features["harmonic_brightness"] = float(np.mean(chroma[0:6]))  # Major scale notes
        features["harmonic_darkness"] = float(np.mean(chroma[6:12]))  # Minor scale notes

        # Onset strength (rhythm prominence)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        features["onset_strength"] = float(np.mean(onset_env))

        # Pitch analysis for children's music detection
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)

        if pitch_values:
            features["pitch_mean"] = float(np.mean(pitch_values))
            features["pitch_std"] = float(np.std(pitch_values))
            # High pitch ratio (voices > 500Hz typically)
            high_pitches = [p for p in pitch_values if p > 500]
            features["high_pitch_ratio"] = len(high_pitches) / len(pitch_values)
        else:
            features["pitch_mean"] = 0
            features["pitch_std"] = 0
            features["high_pitch_ratio"] = 0

        return features

    def _features_to_score(self, features: dict[str, Any]) -> ContentScore:
        """Convert audio features to ContentScore"""
        score = ContentScore(source="audio")

        # Normalize energy (0-1 scale)
        energy = min(1.0, features["energy"] / 0.3)  # 0.3 is typical max RMS

        # Estimate valence (happiness) from harmonic content
        # Higher major-key presence = happier
        harmonic_ratio = features["harmonic_brightness"] / (features["harmonic_darkness"] + 0.001)
        valence = min(1.0, harmonic_ratio / 2.0)

        # Children's music detection
        children_score = 0.0

        # Children's music characteristics:
        # 1. Moderate tempo (100-130 BPM typical)
        tempo = features["tempo"]
        if 90 <= tempo <= 140:
            children_score += 0.3

        # 2. High pitch content (children's voices)
        if features["high_pitch_ratio"] > 0.4:
            children_score += 0.3

        # 3. Simple harmonic structure (low chroma std)
        if features["chroma_std"] < 0.15:
            children_score += 0.2

        # 4. High valence (happy)
        if valence > 0.6:
            children_score += 0.2

        score.children_score = min(1.0, children_score)

        # Explicit music often has:
        # - High energy
        # - Strong bass (low brightness)
        # - High onset strength (aggressive rhythm)

        aggressive_score = 0.0
        if energy > 0.7:
            aggressive_score += 0.3
        if features["brightness"] < 2000:  # Low brightness = heavy bass
            aggressive_score += 0.2
        if features["onset_strength"] > 1.5:
            aggressive_score += 0.2
        if features["noisiness"] > 0.1:
            aggressive_score += 0.1

        # Note: Audio alone can't detect explicit lyrics
        # This is more about "aggressive" vs "gentle" music
        score.explicit_score = min(0.5, aggressive_score)  # Cap at 0.5 - needs lyrics to confirm

        # Clean music characteristics
        # - Moderate energy
        # - High valence
        # - Not aggressive
        clean_indicators = 0.0
        if 0.2 <= energy <= 0.6:
            clean_indicators += 0.3
        if valence > 0.5:
            clean_indicators += 0.3
        if aggressive_score < 0.3:
            clean_indicators += 0.4

        score.clean_score = min(1.0, clean_indicators)

        # Positive messages (approximated by valence)
        score.positive_messages = valence

        # Confidence is lower for audio-only analysis
        score.confidence = 0.5  # Audio gives hints but can't confirm content

        # Add reasons
        score.reasons.append(f"Tempo: {tempo:.0f} BPM")
        score.reasons.append(f"Energy: {energy:.2f}")
        score.reasons.append(f"Valence (estimated): {valence:.2f}")
        score.reasons.append(f"High pitch ratio: {features['high_pitch_ratio']:.2f}")

        if score.children_score > 0.5:
            score.reasons.append("Audio patterns suggest children's music")
        if aggressive_score > 0.5:
            score.reasons.append("Audio patterns suggest aggressive/intense music")

        return score

    def get_audio_features(self, file_path: str) -> Optional[dict[str, Any]]:
        """
        Get raw audio features for a file

        Useful for debugging or advanced analysis
        """
        try:
            y, sr = librosa.load(file_path, duration=30.0, sr=22050)
            return self._extract_features(y, sr)  # type: ignore[arg-type]
        except Exception as e:  # librosa raises diverse errors on corrupt/unsupported audio
            logger.error(f"Feature extraction failed: {e}")
            return None
