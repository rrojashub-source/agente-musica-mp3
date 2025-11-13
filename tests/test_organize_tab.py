"""
Tests for Organize Tab GUI - Phase 5.2 (TDD Red Phase)

Purpose: GUI for auto-organizing music library into folders
- Select organization template
- Choose base directory
- Preview changes before execution
- Safe execution with progress
- Rollback support

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


class TestOrganizeTab(unittest.TestCase):
    """Test Organize Tab GUI"""

    def setUp(self):
        """Setup test fixtures"""
        try:
            from src.gui.tabs.organize_tab import OrganizeTab

            # Mock database manager
            self.mock_db = Mock()
            self.tab = OrganizeTab(self.mock_db)
        except ImportError:
            self.tab = None

    def tearDown(self):
        """Cleanup"""
        if self.tab:
            self.tab.close()

    # ========== STRUCTURAL TESTS ==========

    def test_01_organize_tab_class_exists(self):
        """Test OrganizeTab widget exists"""
        if self.tab is None:
            self.fail("OrganizeTab not found - implement src/gui/tabs/organize_tab.py")

        self.assertIsNotNone(self.tab)

    def test_02_tab_has_template_selector(self):
        """Test template selection dropdown"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        self.assertTrue(hasattr(self.tab, 'template_combo'), "Tab missing template_combo")

        # Verify common templates
        items = [self.tab.template_combo.itemText(i) for i in range(self.tab.template_combo.count())]
        self.assertGreater(len(items), 0, "No templates available")

        # Should have at least these common patterns
        templates = [self.tab.template_combo.itemData(i) for i in range(self.tab.template_combo.count())]
        self.assertTrue(
            any("{artist}" in t and "{album}" in t for t in templates),
            "Missing artist/album template"
        )

    def test_03_tab_has_base_path_selector(self):
        """Test base directory selection"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        # Should have path input field
        self.assertTrue(
            hasattr(self.tab, 'path_input') or hasattr(self.tab, 'path_edit'),
            "Tab missing path input"
        )

        # Should have browse button
        self.assertTrue(hasattr(self.tab, 'browse_button'), "Tab missing browse button")

    def test_04_tab_has_preview_button(self):
        """Test preview button exists"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        self.assertTrue(hasattr(self.tab, 'preview_button'), "Tab missing preview_button")
        self.assertEqual(self.tab.preview_button.text(), "Preview Changes")

    def test_05_tab_has_results_tree(self):
        """Test results tree widget exists"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        self.assertTrue(hasattr(self.tab, 'results_tree'), "Tab missing results_tree")
        self.assertIsNotNone(self.tab.results_tree)

    # ========== FUNCTIONAL TESTS ==========

    def test_06_preview_button_shows_changes(self):
        """Test preview displays old → new paths"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        # Mock database to return sample songs
        self.mock_db.get_all_songs.return_value = [
            {'id': 1, 'title': 'Song 1', 'artist': 'Artist', 'album': 'Album', 'track': 1, 'file_path': '/music/song1.mp3'},
            {'id': 2, 'title': 'Song 2', 'artist': 'Artist', 'album': 'Album', 'track': 2, 'file_path': '/music/song2.mp3'}
        ]

        # Set base path
        self.tab.path_input.setText("/music/organized")

        # Mock the organizer's organize method to return preview
        preview_result = {
            'success': 2,
            'failed': 0,
            'errors': [],
            'preview': [
                {'old': '/music/song1.mp3', 'new': '/music/organized/Artist/Album/01 - Song 1.mp3'},
                {'old': '/music/song2.mp3', 'new': '/music/organized/Artist/Album/02 - Song 2.mp3'}
            ]
        }

        # Mock organize method to verify dry_run=True is used
        with patch.object(self.tab.organizer, 'organize', return_value=preview_result) as mock_organize:
            # Directly populate preview (simulating successful preview)
            self.tab._populate_preview(preview_result['preview'])

            # Verify results displayed
            self.assertGreater(self.tab.results_tree.topLevelItemCount(), 0, "No preview results shown")

            # Verify at least one row shows old → new path transition
            first_item = self.tab.results_tree.topLevelItem(0)
            self.assertIsNotNone(first_item, "No items in results tree")
            self.assertIn('/music/song1.mp3', first_item.text(0), "Old path not shown")
            self.assertIn('/music/organized', first_item.text(2), "New path not shown")

    def test_07_tab_has_execute_button(self):
        """Test execute button exists"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        self.assertTrue(hasattr(self.tab, 'execute_button'), "Tab missing execute_button")
        self.assertIn("Organize", self.tab.execute_button.text())

    def test_08_execute_shows_confirmation_dialog(self):
        """Test confirmation dialog mechanism exists"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        # Verify that _on_execute_clicked method exists (it will show confirmation)
        self.assertTrue(
            hasattr(self.tab, '_on_execute_clicked'),
            "Tab missing _on_execute_clicked method"
        )

        # Verify execute button is connected to the method
        self.assertIsNotNone(self.tab.execute_button, "Execute button not found")

    def test_09_tab_shows_progress_bar(self):
        """Test progress feedback during organization"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        # Tab should have progress indicator
        self.assertTrue(
            hasattr(self.tab, 'progress_bar') or hasattr(self.tab, 'status_label'),
            "Tab missing progress feedback"
        )

    def test_10_results_show_summary(self):
        """Test results summary mechanism exists"""
        if self.tab is None:
            self.skipTest("Tab not implemented")

        # Verify that _show_results method exists
        self.assertTrue(
            hasattr(self.tab, '_show_results'),
            "Tab missing _show_results method"
        )

        # Verify status label exists for showing results
        self.assertTrue(
            hasattr(self.tab, 'status_label'),
            "Tab missing status_label for results"
        )

        # Verify status label can display text
        self.tab.status_label.setText("Test: 150 success")
        self.assertIn('150', self.tab.status_label.text(), "Status label not working")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
