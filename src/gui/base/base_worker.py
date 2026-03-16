"""
BaseWorker -- Common base class for background QThread workers.

Eliminates boilerplate duplication across tab workers by providing:
- Standard signals: progress(int, str), finished(object), error(str)
- Abstract do_work() method for subclasses to implement
- run() with standard try/except/emit pattern
- Optional cancellation support via cancel() / is_cancelled

Subclasses override do_work() and return the result, which is emitted
via the finished signal. Progress can be reported by calling
self.progress.emit(percentage, message) inside do_work().

Subclasses that need different signal signatures (e.g. progress with
different argument types) can redeclare the signal -- PySide6 allows
overriding class-level Signal declarations in subclasses.

Phase 2 -- Structural Refactoring
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any, Optional

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class BaseWorker(QThread):
    """Base class for background worker threads.

    Provides the standard signal/slot pattern used across all tab workers:
    - progress(int, str): percentage (0-100) and status message
    - finished(object): result of do_work(), emitted on success
    - error(str): error message, emitted on exception

    Subclasses MUST override do_work() and return the result object.

    Usage::

        class ScanWorker(BaseWorker):
            def __init__(self, detector, method):
                super().__init__()
                self.detector = detector
                self.method = method

            def do_work(self):
                self.report_progress(10, "Initializing scan...")
                results = self.detector.scan_library(method=self.method)
                self.report_progress(90, "Processing results...")
                return results

    Cancellation::

        worker = ScanWorker(detector, method)
        worker.start()
        # later:
        worker.cancel()

        # Inside do_work():
        def do_work(self):
            for item in items:
                if self.is_cancelled:
                    return None  # or partial results
                self.process(item)
    """

    # Standard signals -- subclasses may redeclare with different signatures
    progress = Signal(int, str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, parent: Optional[QThread] = None) -> None:
        super().__init__(parent)
        self._cancelled: bool = False

    def run(self) -> None:
        """Execute do_work() with standard error handling.

        Do NOT override this method. Override do_work() instead.
        """
        try:
            result = self.do_work()
            if not self._cancelled:
                self.finished.emit(result)
        except Exception as e:  # worker thread boundary - must report all errors via signal
            logger.error(f"{self.__class__.__name__} error: {e}")
            self.error.emit(str(e))

    @abstractmethod
    def do_work(self) -> Any:
        """Perform the actual work in the background thread.

        Must be implemented by subclasses. Return the result object,
        which will be emitted via the finished signal.

        Use self.report_progress(pct, msg) to emit progress updates.
        Check self.is_cancelled periodically for long operations.

        Returns:
            The result object to emit via finished signal.
        """
        ...

    def report_progress(self, percentage: int, message: str = "") -> None:
        """Convenience method to emit the progress signal.

        Args:
            percentage: Progress percentage (0-100).
            message: Human-readable status message.
        """
        self.progress.emit(percentage, message)

    def cancel(self) -> None:
        """Request cancellation of the worker.

        The worker should check self.is_cancelled periodically
        inside do_work() and return early if True.
        """
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Whether cancellation has been requested."""
        return self._cancelled
