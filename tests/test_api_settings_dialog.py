"""
Tests for API Settings Dialog (TDD Red Phase)

Purpose: User-friendly GUI for API key management
- Paste API keys
- Validate with real API calls
- Save encrypted to OS keyring

Test Strategy: Red → Green → Refactor
Expected Result: All tests FAIL initially (no implementation yet)
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
import sys

# Ensure QApplication exists for PyQt6 tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestAPISettingsDialog(unittest.TestCase):
    """Test API Settings Dialog GUI"""

    def setUp(self):
        """Setup test fixtures"""
        try:
            from src.gui.dialogs.api_settings_dialog import APISettingsDialog
            self.dialog = APISettingsDialog()
        except ImportError:
            self.dialog = None

    def tearDown(self):
        """Cleanup"""
        if self.dialog:
            self.dialog.close()

    # ========== STRUCTURAL TESTS ==========

    def test_01_dialog_exists(self):
        """Test APISettingsDialog class exists"""
        if self.dialog is None:
            self.fail("APISettingsDialog not found - implement src/gui/dialogs/api_settings_dialog.py")

        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.windowTitle(), "API Settings")

    def test_02_dialog_has_tabs(self):
        """Test dialog has tabs for YouTube, Spotify, Genius"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        self.assertTrue(hasattr(self.dialog, 'tab_widget'), "Dialog missing tab_widget")
        self.assertEqual(self.dialog.tab_widget.count(), 3, "Expected 3 tabs (YouTube, Spotify, Genius)")

        # Verify tab names
        tab_names = [self.dialog.tab_widget.tabText(i) for i in range(3)]
        self.assertIn("YouTube", tab_names)
        self.assertIn("Spotify", tab_names)

    def test_03_youtube_tab_has_input_field(self):
        """Test YouTube tab has API key input field"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        youtube_tab = self.dialog.youtube_tab
        self.assertTrue(hasattr(youtube_tab, 'api_key_input'), "YouTube tab missing api_key_input")
        self.assertIsNotNone(youtube_tab.api_key_input)

        # Verify input field properties
        self.assertEqual(youtube_tab.api_key_input.placeholderText(), "Paste your YouTube API key here")

    def test_04_validate_button_exists(self):
        """Test Validate button exists"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        youtube_tab = self.dialog.youtube_tab
        self.assertTrue(hasattr(youtube_tab, 'validate_button'), "YouTube tab missing validate_button")
        self.assertEqual(youtube_tab.validate_button.text(), "Validate")

    def test_05_status_label_exists(self):
        """Test status label for showing validation result"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        youtube_tab = self.dialog.youtube_tab
        self.assertTrue(hasattr(youtube_tab, 'status_label'), "YouTube tab missing status_label")
        self.assertIsNotNone(youtube_tab.status_label)

    def test_06_save_button_exists(self):
        """Test Save & Close button exists"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        self.assertTrue(hasattr(self.dialog, 'save_button'), "Dialog missing save_button")
        self.assertEqual(self.dialog.save_button.text(), "Save & Close")

    # ========== FUNCTIONAL TESTS ==========

    def test_07_validate_youtube_key_success(self):
        """Test validating valid YouTube API key - mocks YouTube API"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        # Mock the YouTube API inside the api module
        with patch('src.api.youtube_search.YouTubeSearcher') as MockYT:
            # Setup mock to return valid results
            mock_instance = MockYT.return_value
            mock_instance.search.return_value = [{'video_id': 'abc123', 'title': 'Test Video'}]

            # Enter valid key (30+ chars to pass format validation)
            self.dialog.youtube_tab.api_key_input.setText("a" * 35)  # 35 chars

            # Click validate
            QTest.mouseClick(self.dialog.youtube_tab.validate_button, Qt.MouseButton.LeftButton)

            # Process events
            QApplication.processEvents()

            # Verify status shows success
            status_text = self.dialog.youtube_tab.status_label.text()
            self.assertIn("Valid", status_text, f"Expected 'Valid' in status, got: {status_text}")
            self.assertIn("✅", status_text, "Expected success icon (✅)")

    def test_08_validate_youtube_key_failure(self):
        """Test validating invalid YouTube API key"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        # Test with short key (< 30 chars) - should fail format validation
        # No need to mock YouTube API, format validation happens first

        # Enter invalid key (too short)
        self.dialog.youtube_tab.api_key_input.setText("short")

        # Click validate
        QTest.mouseClick(self.dialog.youtube_tab.validate_button, Qt.MouseButton.LeftButton)

        # Process events
        QApplication.processEvents()

        # Verify status shows error
        status_text = self.dialog.youtube_tab.status_label.text()
        self.assertIn("Invalid", status_text, f"Expected 'Invalid' in status, got: {status_text}")
        self.assertIn("❌", status_text, "Expected error icon (❌)")

    def test_09_save_to_keyring(self):
        """Test saving API keys to OS keyring"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        # Mock keyring
        with patch('keyring.set_password') as mock_set:
            # Enter keys
            self.dialog.youtube_tab.api_key_input.setText("youtube_key_123")
            self.dialog.spotify_tab.api_key_input.setText("spotify_client_id_456")

            # Click save
            QTest.mouseClick(self.dialog.save_button, Qt.MouseButton.LeftButton)

            # Process events
            QApplication.processEvents()

            # Verify keyring.set_password was called for each API
            calls = mock_set.call_args_list
            self.assertGreaterEqual(len(calls), 2, "Expected at least 2 keyring.set_password calls")

            # Verify YouTube key saved
            youtube_call = [c for c in calls if "youtube_api_key" in str(c)]
            self.assertTrue(len(youtube_call) > 0, "YouTube key not saved to keyring")

            # Verify Spotify key saved
            spotify_call = [c for c in calls if "spotify_client_id" in str(c)]
            self.assertTrue(len(spotify_call) > 0, "Spotify key not saved to keyring")

    def test_10_load_existing_keys(self):
        """Test loading existing keys from keyring on dialog open"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        # Mock keyring with existing keys
        def mock_get_password(service, key):
            if key == "youtube_api_key":
                return "existing_youtube_key_789"
            elif key == "spotify_client_id":
                return "existing_spotify_id_012"
            return None

        with patch('keyring.get_password', side_effect=mock_get_password):
            # Create NEW dialog (should load keys)
            from src.gui.dialogs.api_settings_dialog import APISettingsDialog
            new_dialog = APISettingsDialog()

            # Verify keys loaded
            self.assertEqual(
                new_dialog.youtube_tab.api_key_input.text(),
                "existing_youtube_key_789",
                "YouTube key not loaded from keyring"
            )

            new_dialog.close()

    def test_11_empty_key_validation(self):
        """Test validation with empty API key shows error"""
        if self.dialog is None:
            self.skipTest("Dialog not implemented yet")

        # Clear input
        self.dialog.youtube_tab.api_key_input.clear()

        # Click validate
        QTest.mouseClick(self.dialog.youtube_tab.validate_button, Qt.MouseButton.LeftButton)

        # Process events
        QApplication.processEvents()

        # Verify error message
        status_text = self.dialog.youtube_tab.status_label.text()
        self.assertIn("Please enter", status_text, "Expected 'Please enter' message for empty key")
        self.assertIn("❌", status_text, "Expected error icon")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
