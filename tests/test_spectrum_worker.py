"""
Tests for Spectrum Worker — Asynchronous FFT processing in QThread.

Tests the SpectrumWorker class which runs spectrum extraction in a
background thread, emitting progress/finished/error signals.

Created: 2026-03-15
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import numpy as np
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock PySide6 before importing SpectrumWorker so the module loads
# even when PySide6 is not installed in the test environment.
_mock_qtcore = MagicMock()
_mock_qtcore.QThread = type("QThread", (), {"__init__": lambda self, *a, **kw: None})
_mock_qtcore.Signal = lambda *a, **kw: Mock()
sys.modules.setdefault("PySide6", MagicMock())
sys.modules.setdefault("PySide6.QtCore", _mock_qtcore)
sys.modules.setdefault("PySide6.QtWidgets", MagicMock())
sys.modules.setdefault("PySide6.QtGui", MagicMock())

from core.spectrum_worker import SpectrumWorker


class TestSpectrumWorkerInit:
    """Test SpectrumWorker initialization"""

    def test_init_stores_parameters(self):
        """Test that constructor stores extractor, file path, and num_bars."""
        mock_extractor = Mock()
        worker = SpectrumWorker(mock_extractor, "/path/to/song.mp3", num_bars=40)
        assert worker.waveform_extractor is mock_extractor
        assert worker.file_path == "/path/to/song.mp3"
        assert worker.num_bars == 40

    def test_init_default_num_bars(self):
        """Test that default num_bars is 60."""
        mock_extractor = Mock()
        worker = SpectrumWorker(mock_extractor, "/path/to/song.mp3")
        assert worker.num_bars == 60


class TestSpectrumWorkerRun:
    """Test the run method (spectrum extraction logic)"""

    def test_successful_extraction(self):
        """Test run emits finished signal on successful spectrum extraction."""
        mock_extractor = Mock()
        spectrum_data = [[0.1, 0.2], [0.3, 0.4]]
        duration = 3.5
        mock_extractor.extract_spectrum.return_value = (spectrum_data, duration)
        mock_extractor.extract_raw_samples.return_value = (np.zeros(1000), 22050)

        worker = SpectrumWorker(mock_extractor, "/path/song.mp3", num_bars=2)

        # Mock signals
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        worker.raw_audio_ready = Mock()

        worker.run()

        # Should emit progress at 10, 90, 95, 100
        assert worker.progress.emit.call_count == 4
        worker.finished.emit.assert_called_once_with(spectrum_data, duration)
        worker.error.emit.assert_not_called()
        worker.raw_audio_ready.emit.assert_called_once()

    def test_extraction_returns_none(self):
        """Test run emits error signal when extraction returns None."""
        mock_extractor = Mock()
        mock_extractor.extract_spectrum.return_value = None

        worker = SpectrumWorker(mock_extractor, "/path/song.mp3")
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        worker.raw_audio_ready = Mock()

        worker.run()

        worker.finished.emit.assert_not_called()
        worker.error.emit.assert_called_once()
        error_msg = worker.error.emit.call_args[0][0]
        assert "Failed" in error_msg

    def test_extraction_raises_exception(self):
        """Test run emits error signal when extraction raises an exception."""
        mock_extractor = Mock()
        mock_extractor.extract_spectrum.side_effect = OSError("file corrupt")

        worker = SpectrumWorker(mock_extractor, "/path/song.mp3")
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        worker.raw_audio_ready = Mock()

        worker.run()

        worker.finished.emit.assert_not_called()
        worker.error.emit.assert_called_once()
        error_msg = worker.error.emit.call_args[0][0]
        assert "file corrupt" in error_msg

    def test_raw_audio_not_emitted_on_failure(self):
        """Test raw_audio_ready is not emitted when spectrum extraction fails."""
        mock_extractor = Mock()
        mock_extractor.extract_spectrum.return_value = None

        worker = SpectrumWorker(mock_extractor, "/path/song.mp3")
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        worker.raw_audio_ready = Mock()

        worker.run()

        worker.raw_audio_ready.emit.assert_not_called()

    def test_raw_audio_extraction_failure_non_fatal(self):
        """Test that failure in raw sample extraction does not cause error signal."""
        mock_extractor = Mock()
        mock_extractor.extract_spectrum.return_value = ([[0.5]], 1.0)
        mock_extractor.extract_raw_samples.return_value = None

        worker = SpectrumWorker(mock_extractor, "/path/song.mp3", num_bars=1)
        worker.progress = Mock()
        worker.finished = Mock()
        worker.error = Mock()
        worker.raw_audio_ready = Mock()

        worker.run()

        worker.finished.emit.assert_called_once()
        worker.raw_audio_ready.emit.assert_not_called()
        worker.error.emit.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
