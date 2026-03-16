"""
Mock PySide6 module for tests that need to import service modules
without PySide6 actually installed.

Provides a real QObject base class and Signal descriptor so that
service classes inherit properly and class methods work.
Any unknown attribute on mock submodules returns a MagicMock, so that
`from PySide6.QtWidgets import QApplication` etc. succeed at import time.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock


class _MockModule(ModuleType):
    """Module that returns MagicMock for any missing attribute."""

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def __getattr__(self, name: str) -> MagicMock:
        # Return a fresh MagicMock for any unknown attribute
        mock = MagicMock()
        setattr(self, name, mock)
        return mock


def install():
    """Install PySide6 mocks into sys.modules if PySide6 is not available."""
    try:
        import PySide6  # noqa: F401

        # Real PySide6 is installed — don't mock
        return
    except ImportError:
        pass

    class _Signal:
        """Mock Signal descriptor that works as a class variable."""

        def __init__(self, *args, **kwargs):
            pass

        def __set_name__(self, owner, name):
            self._name = name

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            # Return a per-instance MagicMock so .emit() etc. can be asserted
            attr = f"_signal_{self._name}"
            if not hasattr(obj, attr):
                setattr(obj, attr, MagicMock())
            return getattr(obj, attr)

    class _QObject:
        """Minimal QObject stand-in."""

        def __init__(self, *args, **kwargs):
            pass

    class _QThread(_QObject):
        """Minimal QThread stand-in for BaseWorker inheritance."""

        def start(self, *args):
            pass

        def wait(self, *args):
            pass

        def isRunning(self):
            return False

    class _QTimer:
        """Minimal QTimer stand-in."""

        def __init__(self, *args, **kwargs):
            self._interval = 0
            self.timeout = MagicMock()

        def start(self, *args):
            pass

        def stop(self):
            pass

        def setInterval(self, ms):
            self._interval = ms

    # Build mock modules using _MockModule so unknown attrs return MagicMock
    qt_core = _MockModule("PySide6.QtCore")
    qt_core.QObject = _QObject
    qt_core.QThread = _QThread
    qt_core.Signal = _Signal
    qt_core.QTimer = _QTimer

    qt_widgets = _MockModule("PySide6.QtWidgets")
    qt_gui = _MockModule("PySide6.QtGui")
    qt_opengl = _MockModule("PySide6.QtOpenGL")
    qt_opengl_widgets = _MockModule("PySide6.QtOpenGLWidgets")
    qt_test = _MockModule("PySide6.QtTest")

    pyside6 = _MockModule("PySide6")
    pyside6.QtCore = qt_core
    pyside6.QtWidgets = qt_widgets
    pyside6.QtGui = qt_gui
    pyside6.QtOpenGL = qt_opengl
    pyside6.QtOpenGLWidgets = qt_opengl_widgets
    pyside6.QtTest = qt_test

    sys.modules["PySide6"] = pyside6
    sys.modules["PySide6.QtCore"] = qt_core
    sys.modules["PySide6.QtWidgets"] = qt_widgets
    sys.modules["PySide6.QtGui"] = qt_gui
    sys.modules["PySide6.QtOpenGL"] = qt_opengl
    sys.modules["PySide6.QtOpenGLWidgets"] = qt_opengl_widgets
    sys.modules["PySide6.QtTest"] = qt_test
