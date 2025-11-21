"""
Spectrum Extraction Worker - Asynchronous FFT Processing

Background thread for extracting spectrum data without blocking UI.

Created: November 20, 2025
"""
import logging
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class SpectrumWorker(QThread):
    """
    Background worker for spectrum extraction

    Signals:
        progress: Emits progress updates (int: 0-100)
        finished: Emits when extraction complete (spectrum_data, duration)
        error: Emits error message if extraction fails (str)
    """

    # Signals
    progress = pyqtSignal(int)  # Progress percentage (0-100)
    finished = pyqtSignal(object, float)  # (spectrum_data, duration)
    error = pyqtSignal(str)  # Error message

    def __init__(self, waveform_extractor, file_path: str, num_bars: int = 60):
        """
        Initialize spectrum worker

        Args:
            waveform_extractor: WaveformExtractor instance
            file_path: Path to audio file
            num_bars: Number of frequency bars (default: 60)
        """
        super().__init__()
        self.waveform_extractor = waveform_extractor
        self.file_path = file_path
        self.num_bars = num_bars

    def run(self):
        """
        Run spectrum extraction in background thread

        DO NOT call directly - use start() instead
        """
        try:
            logger.info(f"Starting spectrum extraction: {Path(self.file_path).name}")
            self.progress.emit(10)

            # Extract spectrum data (FFT analysis)
            spectrum_result = self.waveform_extractor.extract_spectrum(
                self.file_path,
                num_bars=self.num_bars,
                window_size_ms=50
            )

            self.progress.emit(90)

            if spectrum_result:
                spectrum_data, duration = spectrum_result
                logger.info(
                    f"Spectrum extracted: {len(spectrum_data)} windows, "
                    f"{duration:.1f}s, {self.num_bars} bars"
                )
                self.progress.emit(100)
                self.finished.emit(spectrum_data, duration)
            else:
                error_msg = "Failed to extract spectrum data"
                logger.warning(error_msg)
                self.error.emit(error_msg)

        except Exception as e:
            error_msg = f"Spectrum extraction error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
