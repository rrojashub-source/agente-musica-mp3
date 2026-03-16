"""
BPM Detector — Tempo detection via onset detection + autocorrelation.

Analyzes audio to estimate beats per minute (60-200 BPM range).
Uses the middle 30 seconds for stable estimation.

Part of the AudioEmbeddings split (Phase 2.3).

Created: 2026-03-11 (extracted from audio_embeddings.py)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from core.audio_feature_extractor import SAMPLE_RATE


class BPMDetector:
    """
    BPM detection using onset detection + autocorrelation.

    Analyzes the middle 30 seconds of audio for stable tempo estimation.
    Returns BPM in the 60-200 range with octave correction.
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE) -> None:
        self.sample_rate: int = sample_rate

    def detect(self, file_path: str) -> Optional[int]:
        """
        Detect BPM (beats per minute) of an audio file.

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
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.sample_rate)

            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2**15)  # type: ignore[assignment]

            # Use middle 30 seconds for more stable BPM
            sample_duration = 30 * self.sample_rate
            if len(samples) > sample_duration:
                start = (len(samples) - sample_duration) // 2
                samples = samples[start : start + sample_duration]

            bpm = self.estimate_bpm(samples)

            logger.debug(f"Detected BPM for {Path(file_path).name}: {bpm}")
            return bpm

        except (OSError, ValueError) as e:
            logger.error(f"BPM detection failed for {file_path}: {e}")
            return None

    def estimate_bpm(self, samples: Any) -> Optional[int]:
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

                energy = np.sqrt(np.mean(frame**2))
                onset = max(0, energy - prev_energy)
                onset_env.append(onset)
                prev_energy = energy

            onset_env = np.array(onset_env)  # type: ignore[assignment]

            if np.max(onset_env) > 0:
                onset_env = onset_env / np.max(onset_env)

            # Autocorrelation for periodicity detection
            autocorr = np.correlate(onset_env, onset_env, mode="full")
            autocorr = autocorr[len(autocorr) // 2 :]

            if autocorr[0] > 0:
                autocorr = autocorr / autocorr[0]

            # BPM search range: 60-200 BPM
            fps = self.sample_rate / hop_length

            min_bpm, max_bpm = 60, 200
            min_lag = int(fps * 60 / max_bpm)
            max_lag = int(fps * 60 / min_bpm)

            max_lag = min(max_lag, len(autocorr) - 1)

            if max_lag <= min_lag:
                return None

            # Find peak in search range
            search_range = autocorr[min_lag:max_lag]
            peak_idx = np.argmax(search_range) + min_lag

            # Convert lag to BPM
            bpm = int(round(fps * 60 / peak_idx))

            if 60 <= bpm <= 200:
                return bpm

            # Octave correction (common BPM detection issue)
            if bpm < 60:
                bpm *= 2
            elif bpm > 200:
                bpm //= 2

            if 60 <= bpm <= 200:
                return bpm

            return None

        except (ValueError, TypeError, IndexError) as e:
            logger.error(f"BPM estimation failed: {e}")
            return None
