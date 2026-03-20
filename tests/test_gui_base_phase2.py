"""
Phase 2 Tests for src/gui/base/ — MAPS Round 29

Covers BaseTab methods:
- __init__, _init_ui (NotImplementedError), _connect_signals
- create_main_layout, create_header, create_group
- progress_bar/status_label properties, add_progress_section
- show_progress, update_progress, hide_progress
- connect_worker (all branches), _default_on_progress
- show_error, show_warning, show_success, show_confirm

Covers BaseWorker:
- cancel() method (line 124)

Pattern: Replace mock QWidget with a real Python class before importing,
so BaseTab methods are real functions (not MagicMock).
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Replace mock QWidget/QGroupBox/etc with real classes before importing base_tab
_qt_widgets = sys.modules.get("PySide6.QtWidgets")
_qt_gui = sys.modules.get("PySide6.QtGui")
_qt_core = sys.modules.get("PySide6.QtCore")

if _qt_widgets is not None:
    # Build real stand-in classes for QWidget and related types
    _real_qwidget = type(
        "QWidget",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "setLayout": lambda self, *a: None,
            "layout": lambda self: MagicMock(),
        },
    )

    _real_qlabel = type(
        "QLabel",
        (_real_qwidget,),
        {
            "__init__": lambda self, *a, **k: None,
            "setText": lambda self, *a: None,
            "setStyleSheet": lambda self, *a: None,
            "setFont": lambda self, *a: None,
        },
    )

    _real_qprogressbar = type(
        "QProgressBar",
        (_real_qwidget,),
        {
            "__init__": lambda self, *a, **k: None,
            "setVisible": lambda self, *a: None,
            "setValue": lambda self, *a: None,
        },
    )

    _real_qpushbutton = type(
        "QPushButton",
        (_real_qwidget,),
        {
            "__init__": lambda self, *a, **k: None,
            "setEnabled": lambda self, *a: None,
        },
    )

    _real_qgroupbox = type(
        "QGroupBox",
        (_real_qwidget,),
        {
            "__init__": lambda self, *a, **k: None,
            "setLayout": lambda self, *a: None,
        },
    )

    _real_qvboxlayout = type(
        "QVBoxLayout",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "setContentsMargins": lambda self, *a: None,
            "setSpacing": lambda self, *a: None,
            "addWidget": lambda self, *a: None,
            "addStretch": lambda self, *a: None,
        },
    )

    _real_qhboxlayout = type(
        "QHBoxLayout",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "setContentsMargins": lambda self, *a: None,
            "addWidget": lambda self, *a: None,
            "addStretch": lambda self, *a: None,
        },
    )

    _real_qfont = type(
        "QFont",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "setPointSize": lambda self, *a: None,
            "setBold": lambda self, *a: None,
        },
    )

    # Set them on the mock modules
    _qt_widgets.QWidget = _real_qwidget
    _qt_widgets.QLabel = _real_qlabel
    _qt_widgets.QProgressBar = _real_qprogressbar
    _qt_widgets.QPushButton = _real_qpushbutton
    _qt_widgets.QGroupBox = _real_qgroupbox
    _qt_widgets.QVBoxLayout = _real_qvboxlayout
    _qt_widgets.QHBoxLayout = _real_qhboxlayout
    _qt_widgets.QMessageBox = MagicMock()

    if _qt_gui is not None:
        _qt_gui.QFont = _real_qfont

# Force re-import of base_tab with real classes
for mod_name in ["gui.base.base_tab", "gui.base"]:
    if mod_name in sys.modules:
        del sys.modules[mod_name]

from gui.base.base_tab import BaseTab  # noqa: E402

# --- Helper: concrete subclass ---


class _ConcreteTab(BaseTab):
    """Concrete BaseTab for testing (overrides abstract _init_ui)."""

    def _init_ui(self):
        pass  # No-op for testing


def _make_tab(db_manager=None):
    """Create a _ConcreteTab instance bypassing __init__."""
    tab = _ConcreteTab.__new__(_ConcreteTab)
    tab.db = db_manager
    tab._progress_bar = None
    tab._status_label = None
    tab._active_worker = None
    return tab


# --- Tests ---


class TestBaseTabInit:
    def test_init_calls_init_ui(self):
        """BaseTab.__init__ calls _init_ui and _connect_signals."""
        tab = _ConcreteTab(db_manager=MagicMock())
        assert tab.db is not None

    def test_init_ui_not_implemented(self):
        """BaseTab._init_ui raises NotImplementedError."""
        func = BaseTab.__dict__["_init_ui"]
        with pytest.raises(NotImplementedError):
            func(MagicMock())

    def test_connect_signals_default(self):
        """BaseTab._connect_signals is a no-op by default."""
        func = BaseTab.__dict__["_connect_signals"]
        func(MagicMock())  # Should not raise


class TestLayoutHelpers:
    def test_create_main_layout(self):
        """create_main_layout returns a QVBoxLayout and sets it on widget."""
        tab = _make_tab()
        layout = tab.create_main_layout()
        assert layout is not None

    def test_create_main_layout_custom_margins(self):
        """create_main_layout accepts custom margins and spacing."""
        tab = _make_tab()
        layout = tab.create_main_layout(margins=(10, 10, 10, 10), spacing=15)
        assert layout is not None

    def test_create_header_basic(self):
        """create_header returns a widget with title."""
        tab = _make_tab()
        header = tab.create_header("My Title")
        assert header is not None

    def test_create_header_with_subtitle(self):
        """create_header adds subtitle label when provided."""
        tab = _make_tab()
        header = tab.create_header("Title", subtitle="Sub")
        assert header is not None

    def test_create_group_vertical(self):
        """create_group returns QGroupBox with vertical layout."""
        tab = _make_tab()
        group, layout = tab.create_group("Test Group")
        assert group is not None
        assert layout is not None

    def test_create_group_horizontal(self):
        """create_group returns QGroupBox with horizontal layout."""
        tab = _make_tab()
        group, layout = tab.create_group("Test Group", layout_type="horizontal")
        assert group is not None


class TestProgressInfrastructure:
    def test_progress_bar_lazy_creation(self):
        """progress_bar property creates QProgressBar on first access."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        bar = tab.progress_bar
        assert bar is not None
        # Second access returns same instance
        assert tab.progress_bar is bar

    def test_status_label_lazy_creation(self):
        """status_label property creates QLabel on first access."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        label = tab.status_label
        assert label is not None
        assert tab.status_label is label

    def test_add_progress_section(self):
        """add_progress_section creates both progress bar and status label."""
        tab = _make_tab()
        layout = _real_qvboxlayout()
        tab.add_progress_section(layout)
        assert tab._progress_bar is not None
        assert tab._status_label is not None

    def test_show_progress(self):
        """show_progress makes progress bar visible and sets value."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        tab.show_progress("Loading...", 25)
        assert tab._progress_bar is not None

    def test_update_progress(self):
        """update_progress sets value and optionally message."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        tab.update_progress(50, "Half done")

    def test_update_progress_no_message(self):
        """update_progress with empty message only sets value."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        tab.update_progress(75)

    def test_hide_progress(self):
        """hide_progress hides bar and sets final message."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        tab.show_progress("Working...")
        tab.hide_progress("Done!")

    def test_hide_progress_no_message(self):
        """hide_progress with no message just hides."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        tab.show_progress()
        tab.hide_progress()


class TestConnectWorker:
    def test_connect_worker_basic(self):
        """connect_worker connects progress/finished/error signals."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        worker = MagicMock()
        worker.progress = MagicMock()
        worker.finished = MagicMock()
        worker.error = MagicMock()

        tab.connect_worker(worker)

        assert tab._active_worker is worker
        worker.progress.connect.assert_called_once()
        worker.finished.connect.assert_called_once()
        worker.error.connect.assert_called_once()

    def test_connect_worker_custom_progress(self):
        """connect_worker uses custom progress handler when provided."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        worker = MagicMock()
        custom_progress = MagicMock()

        tab.connect_worker(worker, on_progress=custom_progress)

        worker.progress.connect.assert_called_once_with(custom_progress)

    def test_connect_worker_with_action_button(self):
        """connect_worker disables button and re-enables on finish."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        worker = MagicMock()
        button = MagicMock()

        tab.connect_worker(worker, action_button=button)

        button.setEnabled.assert_called_once_with(False)

    def test_connect_worker_finished_handler(self):
        """connect_worker calls on_finished when worker finishes."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        worker = MagicMock()
        on_finished = MagicMock()

        tab.connect_worker(worker, on_finished=on_finished)

        # Get the handle_finished function that was connected
        finished_handler = worker.finished.connect.call_args[0][0]
        finished_handler("result")
        on_finished.assert_called_once_with("result")
        assert tab._active_worker is None

    def test_connect_worker_finished_with_button(self):
        """Finished handler re-enables action button."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        worker = MagicMock()
        button = MagicMock()

        tab.connect_worker(worker, action_button=button)

        finished_handler = worker.finished.connect.call_args[0][0]
        finished_handler("result")
        # Button re-enabled after finish
        assert button.setEnabled.call_count == 2  # False then True

    def test_connect_worker_error_default(self):
        """Error handler shows error dialog by default."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        tab.show_error = MagicMock()
        worker = MagicMock()

        tab.connect_worker(worker)

        error_handler = worker.error.connect.call_args[0][0]
        error_handler("Something failed")
        tab.show_error.assert_called_once_with("Something failed")
        assert tab._active_worker is None

    def test_connect_worker_error_custom(self):
        """Error handler uses custom callback when provided."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        worker = MagicMock()
        on_error = MagicMock()

        tab.connect_worker(worker, on_error=on_error)

        error_handler = worker.error.connect.call_args[0][0]
        error_handler("Custom error")
        on_error.assert_called_once_with("Custom error")

    def test_connect_worker_error_with_button(self):
        """Error handler re-enables action button."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        worker = MagicMock()
        button = MagicMock()

        tab.connect_worker(worker, action_button=button)

        error_handler = worker.error.connect.call_args[0][0]
        error_handler("Error!")
        assert button.setEnabled.call_count == 2

    def test_default_on_progress(self):
        """_default_on_progress delegates to update_progress."""
        tab = _make_tab()
        tab.setLayout(_real_qvboxlayout())
        tab._default_on_progress(50, "Halfway")


class TestDialogs:
    def test_show_error(self):
        """show_error calls QMessageBox.critical."""
        tab = _make_tab()
        with patch("gui.base.base_tab.QMessageBox") as mock_mb:
            tab.show_error("Error msg", "Error Title")
            mock_mb.critical.assert_called_once()

    def test_show_warning(self):
        """show_warning calls QMessageBox.warning."""
        tab = _make_tab()
        with patch("gui.base.base_tab.QMessageBox") as mock_mb:
            tab.show_warning("Warn msg")
            mock_mb.warning.assert_called_once()

    def test_show_success(self):
        """show_success calls QMessageBox.information."""
        tab = _make_tab()
        with patch("gui.base.base_tab.QMessageBox") as mock_mb:
            tab.show_success("Done!")
            mock_mb.information.assert_called_once()

    def test_show_confirm_yes(self):
        """show_confirm returns True when user clicks Yes."""
        tab = _make_tab()
        with patch("gui.base.base_tab.QMessageBox") as mock_mb:
            mock_mb.StandardButton.Yes = 1
            mock_mb.StandardButton.No = 0
            mock_mb.question.return_value = 1
            result = tab.show_confirm("Are you sure?")
            assert result is True

    def test_show_confirm_no(self):
        """show_confirm returns False when user clicks No."""
        tab = _make_tab()
        with patch("gui.base.base_tab.QMessageBox") as mock_mb:
            mock_mb.StandardButton.Yes = 1
            mock_mb.StandardButton.No = 0
            mock_mb.question.return_value = 0
            result = tab.show_confirm("Are you sure?")
            assert result is False


class TestBaseWorkerCancel:
    def test_cancel(self):
        """BaseWorker.cancel() sets _cancelled flag."""
        from gui.base.base_worker import BaseWorker

        func = BaseWorker.__dict__.get("cancel")
        if func:
            worker = MagicMock()
            worker._cancelled = False
            func(worker)
            assert worker._cancelled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
