"""
Tests for ThemeManager - Dark/Light theme management

Tests cover:
- Singleton pattern
- Theme loading and application
- Theme toggling
- Config persistence
- Error handling
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.theme_manager import ThemeManager


class TestThemeManager(unittest.TestCase):
    """Test suite for ThemeManager"""

    def setUp(self):
        """Set up test fixtures"""
        # Use temporary config directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"

        # Reset singleton instance
        ThemeManager._instance = None

        # Create mock QApplication
        self.mock_qapp = MagicMock()

    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Reset singleton
        ThemeManager._instance = None

    @patch('src.core.theme_manager.QApplication')
    def test_singleton_pattern(self, mock_qapp_class):
        """ThemeManager should implement singleton pattern"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager1 = ThemeManager()
            manager2 = ThemeManager()

            self.assertIs(manager1, manager2)

    @patch('src.core.theme_manager.QApplication')
    def test_default_theme_is_dark(self, mock_qapp_class):
        """Default theme should be 'dark'"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()

            self.assertEqual(manager.current_theme, "dark")

    @patch('src.core.theme_manager.QApplication')
    def test_get_current_theme(self, mock_qapp_class):
        """get_current_theme() should return current theme name"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()

            self.assertEqual(manager.get_current_theme(), "dark")

    @patch('src.core.theme_manager.QApplication')
    def test_apply_dark_theme(self, mock_qapp_class):
        """apply_theme('dark') should load and apply dark.qss"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()

            # Mock _load_qss to return test stylesheet
            with patch.object(manager, '_load_qss', return_value="/* dark theme */"):
                manager.apply_theme("dark")

                # Should call setStyleSheet on QApplication
                self.mock_qapp.setStyleSheet.assert_called_with("/* dark theme */")

                # Current theme should update
                self.assertEqual(manager.current_theme, "dark")

    @patch('src.core.theme_manager.QApplication')
    def test_apply_light_theme(self, mock_qapp_class):
        """apply_theme('light') should load and apply light.qss"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()

            # Mock _load_qss to return test stylesheet
            with patch.object(manager, '_load_qss', return_value="/* light theme */"):
                manager.apply_theme("light")

                # Should call setStyleSheet on QApplication
                self.mock_qapp.setStyleSheet.assert_called_with("/* light theme */")

                # Current theme should update
                self.assertEqual(manager.current_theme, "light")

    @patch('src.core.theme_manager.QApplication')
    def test_toggle_theme_dark_to_light(self, mock_qapp_class):
        """toggle_theme() should switch from dark to light"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()
            manager.current_theme = "dark"

            with patch.object(manager, 'apply_theme'):
                new_theme = manager.toggle_theme()

                # Should call apply_theme with 'light'
                manager.apply_theme.assert_called_with("light")

                # Should return new theme
                self.assertEqual(new_theme, "light")

    @patch('src.core.theme_manager.QApplication')
    def test_toggle_theme_light_to_dark(self, mock_qapp_class):
        """toggle_theme() should switch from light to dark"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()
            manager.current_theme = "light"

            with patch.object(manager, 'apply_theme'):
                new_theme = manager.toggle_theme()

                # Should call apply_theme with 'dark'
                manager.apply_theme.assert_called_with("dark")

                # Should return new theme
                self.assertEqual(new_theme, "dark")

    @patch('src.core.theme_manager.QApplication')
    def test_save_preference_to_config(self, mock_qapp_class):
        """_save_preference() should write theme to config.json"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()
            manager.current_theme = "light"

            manager._save_preference()

            # Config file should exist
            self.assertTrue(self.config_path.exists())

            # Should contain theme setting
            with open(self.config_path) as f:
                config = json.load(f)

            self.assertEqual(config['theme'], 'light')
            self.assertIn('version', config)
            self.assertIn('last_updated', config)

    @patch('src.core.theme_manager.QApplication')
    def test_load_preference_from_config(self, mock_qapp_class):
        """_load_preference() should read theme from config.json"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        # Create config file with light theme
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump({
                'theme': 'light',
                'version': '1.0',
                'last_updated': '2025-11-17T09:30:00'
            }, f)

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()

            # Should load light theme from config
            self.assertEqual(manager.current_theme, 'light')

    @patch('src.core.theme_manager.QApplication')
    def test_invalid_theme_raises_error(self, mock_qapp_class):
        """apply_theme() with invalid theme should raise ValueError"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()

            with self.assertRaises(ValueError) as cm:
                manager.apply_theme("invalid_theme")

            self.assertIn("invalid_theme", str(cm.exception))

    @patch('src.core.theme_manager.QApplication')
    def test_missing_qss_file_fallback(self, mock_qapp_class):
        """_load_qss() should return empty string if QSS file missing"""
        mock_qapp_class.instance.return_value = self.mock_qapp

        with patch.object(ThemeManager, 'config_path', self.config_path):
            manager = ThemeManager()

            # Mock Path.exists to return False
            with patch('pathlib.Path.exists', return_value=False):
                qss_content = manager._load_qss("dark")

                # Should return empty string as fallback
                self.assertEqual(qss_content, "")


if __name__ == '__main__':
    unittest.main()
