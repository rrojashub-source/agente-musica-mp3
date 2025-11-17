"""
Tests for KeyboardShortcutManager

This module tests the global keyboard shortcut system.

Test Strategy:
1. Manager creation and singleton pattern
2. Event filter functionality
3. Shortcut signal emissions
4. Typing context detection
5. Shortcut listing
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QLineEdit, QWidget
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtTest import QTest


class TestKeyboardShortcutManager(unittest.TestCase):
    """Test keyboard shortcut manager"""

    @classmethod
    def setUpClass(cls):
        """Create QApplication instance (required for Qt widgets)"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures"""
        # Import here to avoid import errors before QApplication exists
        from core.keyboard_shortcuts import KeyboardShortcutManager

        # Create fresh instance for each test
        self.manager = KeyboardShortcutManager()

    def tearDown(self):
        """Clean up after tests"""
        pass  # Nothing to clean up

    def _create_key_event(self, key, modifiers=Qt.KeyboardModifier.NoModifier):
        """Helper to create QKeyEvent"""
        return QKeyEvent(
            QEvent.Type.KeyPress,
            key,
            modifiers
        )

    def test_01_manager_class_exists(self):
        """KeyboardShortcutManager class should exist"""
        from core.keyboard_shortcuts import KeyboardShortcutManager
        self.assertIsNotNone(KeyboardShortcutManager)

    def test_02_manager_is_instantiable(self):
        """Manager should be instantiable multiple times (for testing)"""
        from core.keyboard_shortcuts import KeyboardShortcutManager

        manager1 = KeyboardShortcutManager()
        manager2 = KeyboardShortcutManager()

        # For tests, we allow multiple instances
        # In production, app creates only one instance
        self.assertIsNotNone(manager1)
        self.assertIsNotNone(manager2)

    def test_03_manager_has_event_filter(self):
        """Manager should have eventFilter method"""
        self.assertTrue(
            hasattr(self.manager, 'eventFilter'),
            "Manager should have eventFilter method"
        )
        self.assertTrue(
            callable(self.manager.eventFilter),
            "eventFilter should be callable"
        )

    def test_04_space_triggers_play_pause_signal(self):
        """Pressing Space should emit play_pause_requested signal"""
        # Create a mock to capture signal emission
        signal_mock = Mock()
        self.manager.play_pause_requested.connect(signal_mock)

        # Create key event for Space
        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_Space)

        # Manually call event filter (simulating global filter)
        self.manager.eventFilter(widget, event)

        # Verify signal was emitted
        signal_mock.assert_called_once()

    def test_05_left_arrow_triggers_seek_backward(self):
        """Left arrow should emit seek_backward_requested(5)"""
        signal_mock = Mock()
        self.manager.seek_backward_requested.connect(signal_mock)

        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_Left)

        self.manager.eventFilter(widget, event)

        signal_mock.assert_called_once_with(5)

    def test_06_right_arrow_triggers_seek_forward(self):
        """Right arrow should emit seek_forward_requested(5)"""
        signal_mock = Mock()
        self.manager.seek_forward_requested.connect(signal_mock)

        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_Right)

        self.manager.eventFilter(widget, event)

        signal_mock.assert_called_once_with(5)

    def test_07_up_arrow_triggers_volume_up(self):
        """Up arrow should emit volume_change_requested(+10)"""
        signal_mock = Mock()
        self.manager.volume_change_requested.connect(signal_mock)

        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_Up)

        self.manager.eventFilter(widget, event)

        signal_mock.assert_called_once_with(10)

    def test_08_down_arrow_triggers_volume_down(self):
        """Down arrow should emit volume_change_requested(-10)"""
        signal_mock = Mock()
        self.manager.volume_change_requested.connect(signal_mock)

        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_Down)

        self.manager.eventFilter(widget, event)

        signal_mock.assert_called_once_with(-10)

    def test_09_m_triggers_mute_toggle(self):
        """M key should emit mute_toggled signal"""
        signal_mock = Mock()
        self.manager.mute_toggled.connect(signal_mock)

        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_M)

        self.manager.eventFilter(widget, event)

        signal_mock.assert_called_once()

    def test_10_ctrl_f_triggers_focus_search(self):
        """Ctrl+F should emit focus_search_requested"""
        signal_mock = Mock()
        self.manager.focus_search_requested.connect(signal_mock)

        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)

        self.manager.eventFilter(widget, event)

        signal_mock.assert_called_once()

    def test_11_ctrl_l_switches_to_library_tab(self):
        """Ctrl+L should emit switch_to_tab_requested('library')"""
        signal_mock = Mock()
        self.manager.switch_to_tab_requested.connect(signal_mock)

        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)

        self.manager.eventFilter(widget, event)

        signal_mock.assert_called_once_with('library')

    def test_12_ctrl_d_switches_to_queue_tab(self):
        """Ctrl+D should emit switch_to_tab_requested('queue')"""
        signal_mock = Mock()
        self.manager.switch_to_tab_requested.connect(signal_mock)

        widget = QWidget()
        event = self._create_key_event(Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)

        self.manager.eventFilter(widget, event)

        signal_mock.assert_called_once_with('queue')

    def test_13_typing_context_ignored(self):
        """Keys should be ignored when QLineEdit has focus"""
        signal_mock = Mock()
        self.manager.play_pause_requested.connect(signal_mock)

        # Create QLineEdit (typing context)
        line_edit = QLineEdit()
        event = self._create_key_event(Qt.Key.Key_Space)

        # Event filter should return False (not consumed)
        result = self.manager.eventFilter(line_edit, event)

        self.assertFalse(result, "Should not consume event in typing context")
        signal_mock.assert_not_called()

    def test_14_all_shortcuts_listed(self):
        """get_shortcuts() should return list of all shortcuts"""
        shortcuts = self.manager.get_shortcuts()

        self.assertIsInstance(shortcuts, list)
        self.assertGreater(len(shortcuts), 0, "Should have at least one shortcut")

        # Verify format: list of tuples (key, description)
        for item in shortcuts:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2, "Each shortcut should be (key, description)")
            self.assertIsInstance(item[0], str, "Key should be string")
            self.assertIsInstance(item[1], str, "Description should be string")

        # Verify essential shortcuts are listed
        shortcut_keys = [s[0] for s in shortcuts]
        self.assertIn("Space", shortcut_keys)
        self.assertIn("Ctrl+F", shortcut_keys)
        self.assertIn("Ctrl+L", shortcut_keys)


if __name__ == '__main__':
    unittest.main()
