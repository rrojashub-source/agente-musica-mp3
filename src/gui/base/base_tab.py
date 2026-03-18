"""
BaseTab — Common base class for all NEXUS Music Manager tabs.

Provides:
- Standard init pattern (db_manager, _init_ui, _connect_signals)
- Progress bar infrastructure (show/hide/update)
- Status label infrastructure
- Worker connection helper (progress/finished/error signals)
- Common dialog methods (show_error, show_success, show_confirm)
- Logging setup

Tabs inherit from BaseTab and override _init_ui() to build their UI.
All utility methods are optional — tabs use what they need.

Phase 2.2 — Structural Refactoring
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional, Tuple, Union

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.themes.style_constants import Styles

logger = logging.getLogger(__name__)


class BaseTab(QWidget):
    """Base class for all tab widgets in NEXUS Music Manager.

    Subclasses MUST override _init_ui() to build their UI.
    Subclasses MAY override _connect_signals() for signal wiring.

    Usage:
        class MyTab(BaseTab):
            def __init__(self, db_manager, parent=None):
                super().__init__(db_manager=db_manager, parent=parent)

            def _init_ui(self):
                layout = self.create_main_layout()
                # ... build UI using layout ...
    """

    # Emitted when this tab modifies DB data (library refresh trigger)
    data_changed = Signal()

    def __init__(self, db_manager: Any = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db: Any = db_manager

        # Progress infrastructure (created on demand)
        self._progress_bar: Optional[QProgressBar] = None
        self._status_label: Optional[QLabel] = None

        # Active worker reference
        self._active_worker: Optional[QThread] = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Build the tab UI. Subclasses MUST override this."""
        raise NotImplementedError("Subclasses must implement _init_ui()")

    def _connect_signals(self) -> None:
        """Connect signals. Subclasses MAY override (call super first)."""
        pass

    # ==========================================
    # Layout Helpers
    # ==========================================

    def create_main_layout(self, margins: Tuple[int, int, int, int] = (0, 0, 0, 0), spacing: int = 5) -> QVBoxLayout:
        """Create and set the main vertical layout.

        Returns:
            QVBoxLayout set as this widget's layout.
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        self.setLayout(layout)
        return layout

    def create_header(self, title: str, subtitle: str = "") -> QWidget:
        """Create a standard header widget with title and optional subtitle.

        Returns:
            QWidget containing the header.
        """
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(5, 5, 5, 0)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet(Styles.TEXT_MUTED)
            layout.addWidget(sub_label)

        layout.addStretch()
        return header

    def create_group(
        self, title: str, layout_type: str = "vertical"
    ) -> Tuple[QGroupBox, Union[QVBoxLayout, QHBoxLayout]]:
        """Create a QGroupBox with layout.

        Args:
            title: Group box title.
            layout_type: "vertical" or "horizontal".

        Returns:
            Tuple of (QGroupBox, layout).
        """
        group = QGroupBox(title)
        if layout_type == "horizontal":
            layout = QHBoxLayout()
        else:
            layout = QVBoxLayout()
        group.setLayout(layout)
        return group, layout

    # ==========================================
    # Progress Infrastructure
    # ==========================================

    @property
    def progress_bar(self) -> QProgressBar:
        """Lazy-create progress bar on first access."""
        if self._progress_bar is None:
            self._progress_bar = QProgressBar()
            self._progress_bar.setVisible(False)
            # Try to add to existing layout
            if self.layout():
                self.layout().addWidget(self._progress_bar)
        return self._progress_bar

    @progress_bar.setter
    def progress_bar(self, value: QProgressBar) -> None:
        """Allow subclasses to assign their own progress bar."""
        self._progress_bar = value

    @property
    def status_label(self) -> QLabel:
        """Lazy-create status label on first access."""
        if self._status_label is None:
            self._status_label = QLabel("")
            if self.layout():
                self.layout().addWidget(self._status_label)
        return self._status_label

    @status_label.setter
    def status_label(self, value: QLabel) -> None:
        """Allow subclasses to assign their own status label."""
        self._status_label = value

    def add_progress_section(self, layout: QVBoxLayout) -> None:
        """Add progress bar + status label to a layout.

        Call this in _init_ui() to place progress at a specific position.
        """
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

    def show_progress(self, message: str = "Working...", value: int = 0) -> None:
        """Show progress bar with message."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def update_progress(self, percentage: int, message: str = "") -> None:
        """Update progress bar value and message."""
        self.progress_bar.setValue(percentage)
        if message:
            self.status_label.setText(message)

    def hide_progress(self, message: str = "") -> None:
        """Hide progress bar and optionally set final status."""
        self.progress_bar.setVisible(False)
        if message:
            self.status_label.setText(message)

    # ==========================================
    # Worker Integration
    # ==========================================

    def connect_worker(
        self,
        worker: QThread,
        on_finished: Optional[Callable[..., Any]] = None,
        on_error: Optional[Callable[[str], Any]] = None,
        on_progress: Optional[Callable[[int, str], Any]] = None,
        action_button: Optional[QPushButton] = None,
    ) -> None:
        """Connect a QThread worker's standard signals.

        Handles the common pattern:
        - progress(int, str) → update progress bar
        - finished(result) → hide progress, call handler
        - error(str) → hide progress, show error dialog

        Args:
            worker: QThread with progress/finished/error signals.
            on_finished: Callback for finished signal (receives result).
            on_error: Custom error handler (receives str). Default shows QMessageBox.
            on_progress: Custom progress handler. Default updates progress bar.
            action_button: Button to disable during work and re-enable after.
        """
        self._active_worker = worker

        # Progress
        if hasattr(worker, "progress"):
            if on_progress:
                worker.progress.connect(on_progress)
            else:
                worker.progress.connect(self._default_on_progress)

        # Finished
        if hasattr(worker, "finished"):

            def handle_finished(*args: object) -> None:
                self.hide_progress()
                if action_button:
                    action_button.setEnabled(True)
                if on_finished:
                    on_finished(*args)
                self._active_worker = None

            worker.finished.connect(handle_finished)

        # Error
        if hasattr(worker, "error"):

            def handle_error(error_msg: str) -> None:
                self.hide_progress(f"Error: {error_msg}")
                if action_button:
                    action_button.setEnabled(True)
                if on_error:
                    on_error(error_msg)
                else:
                    self.show_error(error_msg)
                self._active_worker = None

            worker.error.connect(handle_error)

        # Disable action button during work
        if action_button:
            action_button.setEnabled(False)

        # Show progress
        self.show_progress("Starting...")

    def _default_on_progress(self, percentage: int, message: str) -> None:
        """Default progress handler for workers."""
        self.update_progress(percentage, message)

    # ==========================================
    # Common Dialogs
    # ==========================================

    def show_error(self, message: str, title: str = "Error") -> None:
        """Show error dialog."""
        QMessageBox.critical(self, title, message)
        logger.error(f"[{self.__class__.__name__}] {message}")

    def show_warning(self, message: str, title: str = "Warning") -> None:
        """Show warning dialog."""
        QMessageBox.warning(self, title, message)
        logger.warning(f"[{self.__class__.__name__}] {message}")

    def show_success(self, message: str, title: str = "Success") -> None:
        """Show success/info dialog."""
        QMessageBox.information(self, title, message)

    def show_confirm(self, message: str, title: str = "Confirm") -> bool:
        """Show confirmation dialog.

        Returns:
            True if user clicked Yes, False otherwise.
        """
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes  # type: ignore[no-any-return]
