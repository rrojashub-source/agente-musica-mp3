"""
KeyboardShortcutManager - Global keyboard shortcut handler

Features:
- Singleton pattern (single global instance)
- Global event filter (works from any widget)
- Context-aware (ignores shortcuts when typing in text fields)
- Signal-based dispatch (clean separation of concerns)
- Configurable shortcuts list for help dialog

Usage:
    manager = KeyboardShortcutManager()
    QApplication.instance().installEventFilter(manager)
    manager.play_pause_requested.connect(audio_player.toggle_play_pause)
"""

import logging
from PyQt6.QtCore import QObject, Qt, QEvent, pyqtSignal
from PyQt6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit
from PyQt6.QtGui import QAction, QKeySequence

logger = logging.getLogger(__name__)


class KeyboardShortcutManager(QObject):
    """
    Manages global keyboard shortcuts for the application

    Uses Qt's event filter system to intercept key presses before they reach widgets.
    Emits signals when shortcuts are triggered, allowing clean decoupling from handlers.

    Note: Singleton pattern can be implemented at application level by creating
    only one instance. For testing, each test creates its own instance.
    """

    # Signals
    play_pause_requested = pyqtSignal()
    seek_backward_requested = pyqtSignal(int)  # seconds
    seek_forward_requested = pyqtSignal(int)   # seconds
    volume_change_requested = pyqtSignal(int)  # delta percentage
    mute_toggled = pyqtSignal()
    focus_search_requested = pyqtSignal()
    switch_to_tab_requested = pyqtSignal(str)  # tab name

    _instance = None  # For optional singleton at app level

    def __init__(self, parent=None):
        """Initialize keyboard shortcuts manager"""
        super().__init__(parent)
        self._actions = []  # Store QAction instances
        logger.info("KeyboardShortcutManager initialized")

    def setup_shortcuts(self, main_window):
        """
        Setup application-wide shortcuts using QAction (high priority)

        Args:
            main_window: Main window widget to attach actions to

        Note: QAction shortcuts are more robust than QShortcut for arrow keys
              and work reliably even when tables/lists have focus
        """
        # Seek Left (←)
        seek_left_action = QAction("Seek Backward", main_window)
        seek_left_action.setShortcut(QKeySequence(Qt.Key.Key_Left))
        seek_left_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_left_action.triggered.connect(lambda: self._on_seek_left_activated())
        main_window.addAction(seek_left_action)
        self._actions.append(seek_left_action)
        logger.info(f"Seek left action created: {seek_left_action.shortcut().toString()}")

        # Seek Right (→)
        seek_right_action = QAction("Seek Forward", main_window)
        seek_right_action.setShortcut(QKeySequence(Qt.Key.Key_Right))
        seek_right_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        seek_right_action.triggered.connect(lambda: self._on_seek_right_activated())
        main_window.addAction(seek_right_action)
        self._actions.append(seek_right_action)
        logger.info(f"Seek right action created: {seek_right_action.shortcut().toString()}")

        logger.info("QAction-based shortcuts configured (Left/Right seek)")

    def _on_seek_left_activated(self):
        """Handle Left arrow shortcut activation"""
        logger.debug("ACTION: Left Arrow activated (Seek -5s)")
        self.seek_backward_requested.emit(5)

    def _on_seek_right_activated(self):
        """Handle Right arrow shortcut activation"""
        logger.debug("ACTION: Right Arrow activated (Seek +5s)")
        self.seek_forward_requested.emit(5)

    def eventFilter(self, obj, event):
        """
        Global event filter for keyboard shortcuts

        Args:
            obj: The object that received the event
            event: The event to filter

        Returns:
            bool: True if event was consumed, False otherwise
        """
        # Only process key press events
        if event.type() != QEvent.Type.KeyPress:
            return False

        # Ignore shortcuts when typing in text fields
        if self._is_typing_context(obj):
            return False

        key = event.key()
        modifiers = event.modifiers()

        # Handle Ctrl+Key shortcuts
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if self._handle_ctrl_shortcut(key):
                return True  # Consume event

        # Handle plain key shortcuts
        elif self._handle_shortcut(key):
            return True  # Consume event

        return False  # Let event propagate

    def _is_typing_context(self, widget):
        """
        Check if user is typing in a text field

        Args:
            widget: Widget to check

        Returns:
            bool: True if widget or its parent is a text field
        """
        focus_widget = widget
        while focus_widget:
            if isinstance(focus_widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
                return True
            focus_widget = focus_widget.parent()
        return False

    def _handle_shortcut(self, key):
        """
        Handle plain key shortcuts (no modifiers)

        Args:
            key: Qt key code

        Returns:
            bool: True if shortcut was handled

        Note: Left/Right are handled by QShortcut (setup_shortcuts) for higher priority
        """
        if key == Qt.Key.Key_Space:
            self.play_pause_requested.emit()
            logger.debug("Shortcut: Space (Play/Pause)")
            return True

        # Left/Right handled by QShortcut (see setup_shortcuts)
        # This avoids conflicts with table/list navigation

        elif key == Qt.Key.Key_Up:
            self.volume_change_requested.emit(10)
            logger.debug("Shortcut: Up Arrow (Volume +10%)")
            return True

        elif key == Qt.Key.Key_Down:
            self.volume_change_requested.emit(-10)
            logger.debug("Shortcut: Down Arrow (Volume -10%)")
            return True

        elif key == Qt.Key.Key_M:
            self.mute_toggled.emit()
            logger.debug("Shortcut: M (Mute Toggle)")
            return True

        return False

    def _handle_ctrl_shortcut(self, key):
        """
        Handle Ctrl+Key shortcuts

        Args:
            key: Qt key code

        Returns:
            bool: True if shortcut was handled
        """
        if key == Qt.Key.Key_F:
            self.focus_search_requested.emit()
            logger.debug("Shortcut: Ctrl+F (Focus Search)")
            return True

        elif key == Qt.Key.Key_L:
            self.switch_to_tab_requested.emit('library')
            logger.debug("Shortcut: Ctrl+L (Library Tab)")
            return True

        elif key == Qt.Key.Key_D:
            self.switch_to_tab_requested.emit('queue')
            logger.debug("Shortcut: Ctrl+D (Queue Tab)")
            return True

        return False

    def get_shortcuts(self):
        """
        Get list of all shortcuts for display in help dialog

        Returns:
            list: List of tuples (key_combination, description)
        """
        shortcuts_list = [
            # Playback controls
            ("Space", "Play/Pause"),
            ("← (Left)", "Seek Backward 5s"),
            ("→ (Right)", "Seek Forward 5s"),
            ("↑ (Up)", "Volume +10%"),
            ("↓ (Down)", "Volume -10%"),
            ("M", "Mute/Unmute"),

            # Navigation
            ("Ctrl+F", "Focus Search"),
            ("Ctrl+L", "Library Tab"),
            ("Ctrl+D", "Queue Tab"),

            # Application (existing)
            ("Ctrl+T", "Toggle Theme"),
            ("Ctrl+Q", "Quit"),
        ]

        return shortcuts_list
