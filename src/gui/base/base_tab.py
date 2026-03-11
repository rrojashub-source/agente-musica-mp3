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
import logging
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QMessageBox, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QFont

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

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db = db_manager

        # Progress infrastructure (created on demand)
        self._progress_bar = None
        self._status_label = None

        # Active worker reference
        self._active_worker = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Build the tab UI. Subclasses MUST override this."""
        raise NotImplementedError("Subclasses must implement _init_ui()")

    def _connect_signals(self):
        """Connect signals. Subclasses MAY override (call super first)."""
        pass

    # ==========================================
    # Layout Helpers
    # ==========================================

    def create_main_layout(self, margins=(0, 0, 0, 0), spacing=5):
        """Create and set the main vertical layout.

        Returns:
            QVBoxLayout set as this widget's layout.
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        self.setLayout(layout)
        return layout

    def create_header(self, title, subtitle=""):
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
            sub_label.setStyleSheet("color: #888;")
            layout.addWidget(sub_label)

        layout.addStretch()
        return header

    def create_group(self, title, layout_type="vertical"):
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
    def progress_bar(self):
        """Lazy-create progress bar on first access."""
        if self._progress_bar is None:
            self._progress_bar = QProgressBar()
            self._progress_bar.setVisible(False)
            # Try to add to existing layout
            if self.layout():
                self.layout().addWidget(self._progress_bar)
        return self._progress_bar

    @property
    def status_label(self):
        """Lazy-create status label on first access."""
        if self._status_label is None:
            self._status_label = QLabel("")
            if self.layout():
                self.layout().addWidget(self._status_label)
        return self._status_label

    def add_progress_section(self, layout):
        """Add progress bar + status label to a layout.

        Call this in _init_ui() to place progress at a specific position.
        """
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

    def show_progress(self, message="Working...", value=0):
        """Show progress bar with message."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def update_progress(self, percentage, message=""):
        """Update progress bar value and message."""
        self.progress_bar.setValue(percentage)
        if message:
            self.status_label.setText(message)

    def hide_progress(self, message=""):
        """Hide progress bar and optionally set final status."""
        self.progress_bar.setVisible(False)
        if message:
            self.status_label.setText(message)

    # ==========================================
    # Worker Integration
    # ==========================================

    def connect_worker(self, worker, on_finished=None, on_error=None,
                       on_progress=None, action_button=None):
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
        if hasattr(worker, 'progress'):
            if on_progress:
                worker.progress.connect(on_progress)
            else:
                worker.progress.connect(self._default_on_progress)

        # Finished
        if hasattr(worker, 'finished'):
            def handle_finished(*args):
                self.hide_progress()
                if action_button:
                    action_button.setEnabled(True)
                if on_finished:
                    on_finished(*args)
                self._active_worker = None

            worker.finished.connect(handle_finished)

        # Error
        if hasattr(worker, 'error'):
            def handle_error(error_msg):
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

    def _default_on_progress(self, percentage, message):
        """Default progress handler for workers."""
        self.update_progress(percentage, message)

    # ==========================================
    # Common Dialogs
    # ==========================================

    def show_error(self, message, title="Error"):
        """Show error dialog."""
        QMessageBox.critical(self, title, message)
        logger.error(f"[{self.__class__.__name__}] {message}")

    def show_warning(self, message, title="Warning"):
        """Show warning dialog."""
        QMessageBox.warning(self, title, message)
        logger.warning(f"[{self.__class__.__name__}] {message}")

    def show_success(self, message, title="Success"):
        """Show success/info dialog."""
        QMessageBox.information(self, title, message)

    def show_confirm(self, message, title="Confirm"):
        """Show confirmation dialog.

        Returns:
            True if user clicked Yes, False otherwise.
        """
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
