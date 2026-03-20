"""
Spectrum Extraction Worker - Asynchronous FFT Processing

Background thread for extracting spectrum data without blocking UI.

Created: November 20, 2025
Migrated to BaseWorker pattern (Phase 4 polish).
"""

import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal

from gui.base.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class SpectrumWorker(BaseWorker):
    """
    Background worker for spectrum extraction

    Signals:
        progress: Emits progress updates (int: 0-100)
        finished: Emits when extraction complete (spectrum_data, duration)
        raw_audio_ready: Emits raw samples for real-time FFT
        error: Emits error message if extraction fails (str)

    Note: finished and progress have custom signatures that differ from
    BaseWorker defaults, so run() is overridden to handle emission.
    """

    # Custom signal overrides -- callers expect progress(int) and finished(object, float)
    progress = Signal(int)  # Progress percentage (0-100)
    finished = Signal(object, float)  # (spectrum_data, duration)
    raw_audio_ready = Signal(object, int)  # (samples_ndarray, sample_rate)

    def __init__(self, waveform_extractor: Any, file_path: str, num_bars: int = 60) -> None:
        """
        Initialize spectrum worker

        Args:
            waveform_extractor: WaveformExtractor instance
            file_path: Path to audio file
            num_bars: Number of frequency bars (default: 60)
        """
        super().__init__()
        self.waveform_extractor: Any = waveform_extractor
        self.file_path: str = file_path
        self.num_bars: int = num_bars

    def run(self) -> None:
        """Override BaseWorker.run() because finished signal has custom signature (object, float).

        DO NOT call directly - use start() instead.
        """
        try:
            self.do_work()
        except Exception as e:  # worker thread boundary - must report all errors via signal
            logger.error(f"{self.__class__.__name__} error: {e}")
            self.error.emit(str(e))

    def do_work(self) -> None:
        """
        Run spectrum extraction in background thread.

        Emits finished(spectrum_data, duration) directly because the signal
        has a two-argument signature incompatible with BaseWorker's default
        finished(object) emission.
        """
        logger.info(f"Starting spectrum extraction: {Path(self.file_path).name}")
        self.progress.emit(10)

        if self.is_cancelled:
            return None

        # Extract spectrum data (FFT analysis)
        spectrum_result = self.waveform_extractor.extract_spectrum(
            self.file_path, num_bars=self.num_bars, window_size_ms=50
        )

        self.progress.emit(90)

        if spectrum_result:
            spectrum_data, duration = spectrum_result
            logger.info(f"Spectrum extracted: {len(spectrum_data)} windows, {duration:.1f}s, {self.num_bars} bars")
            self.progress.emit(95)

            if not self.is_cancelled:
                self.finished.emit(spectrum_data, duration)

            # Also extract raw samples for real-time FFT (organic visualizer)
            raw_result = self.waveform_extractor.extract_raw_samples(self.file_path)
            if raw_result:
                samples, sample_rate = raw_result
                self.raw_audio_ready.emit(samples, sample_rate)
                logger.info(f"Raw audio ready for real-time FFT ({sample_rate}Hz)")

            self.progress.emit(100)
        else:
            error_msg = "Failed to extract spectrum data"
            logger.warning(error_msg)
            self.error.emit(error_msg)

        return None
