"""
ThemeManager - Dark/Light theme management for NEXUS Music Manager

Features:
- Singleton pattern (one instance globally)
- Load/apply QSS stylesheets
- Toggle between dark and light themes
- Persist user preference to config file
- Support for custom themes (future)
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class ThemeManager:
    """
    Manages application themes (dark/light mode)

    Singleton pattern ensures only one instance exists globally.
    Themes are defined as QSS (Qt Style Sheets) files.

    Usage:
        manager = ThemeManager()
        manager.apply_theme("dark")
        manager.toggle_theme()  # Switch to light
    """

    _instance: Optional['ThemeManager'] = None

    # Config path (can be overridden in tests)
    config_path = Path.home() / ".nexus_music" / "config.json"

    # Available themes
    THEMES = ["dark", "light"]

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize theme manager"""
        # Only initialize once (singleton)
        if hasattr(self, '_initialized'):
            return

        self.current_theme = "dark"  # Default theme
        self._load_preference()

        self._initialized = True

        logger.info(f"ThemeManager initialized (theme: {self.current_theme})")

    def get_current_theme(self) -> str:
        """
        Get current theme name

        Returns:
            str: Current theme name ('dark' or 'light')
        """
        return self.current_theme

    def apply_theme(self, theme_name: str) -> None:
        """
        Apply theme to application

        Args:
            theme_name: Name of theme to apply ('dark' or 'light')

        Raises:
            ValueError: If theme_name is not valid
        """
        if theme_name not in self.THEMES:
            raise ValueError(f"Invalid theme: {theme_name}. Valid themes: {self.THEMES}")

        # Load QSS stylesheet
        qss_content = self._load_qss(theme_name)

        # Apply to QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss_content)

        # Update current theme
        self.current_theme = theme_name

        # Save preference
        self._save_preference()

        logger.info(f"Applied theme: {theme_name}")

    def toggle_theme(self) -> str:
        """
        Toggle between dark and light themes

        Returns:
            str: New theme name after toggle
        """
        # Toggle logic
        new_theme = "light" if self.current_theme == "dark" else "dark"

        # Apply new theme
        self.apply_theme(new_theme)

        return new_theme

    def _load_qss(self, theme_name: str) -> str:
        """
        Load QSS stylesheet from file

        Args:
            theme_name: Name of theme to load

        Returns:
            str: QSS content (or empty string if file not found)
        """
        # Path to QSS file
        themes_dir = Path(__file__).parent.parent / "gui" / "themes"
        qss_file = themes_dir / f"{theme_name}.qss"

        # Read QSS file
        if qss_file.exists():
            try:
                with open(qss_file, 'r', encoding='utf-8') as f:
                    qss_content = f.read()

                logger.debug(f"Loaded QSS: {qss_file} ({len(qss_content)} chars)")
                return qss_content

            except Exception as e:
                logger.error(f"Failed to load QSS {qss_file}: {e}")
                return ""
        else:
            logger.warning(f"QSS file not found: {qss_file}")
            return ""

    def _save_preference(self) -> None:
        """Save current theme preference to config file"""
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare config data
        config = {
            'theme': self.current_theme,
            'version': '1.0',
            'last_updated': datetime.now().isoformat()
        }

        # Write to temp file first (atomic write)
        temp_path = self.config_path.with_suffix('.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            # Rename temp file to actual config (atomic on most filesystems)
            temp_path.replace(self.config_path)

            logger.debug(f"Saved theme preference: {self.current_theme}")

        except Exception as e:
            logger.error(f"Failed to save theme preference: {e}")

            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    def _load_preference(self) -> None:
        """Load theme preference from config file"""
        if not self.config_path.exists():
            logger.debug("Config file not found, using default theme")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Load theme setting
            theme = config.get('theme', 'dark')

            # Validate theme
            if theme in self.THEMES:
                self.current_theme = theme
                logger.info(f"Loaded theme preference: {theme}")
            else:
                logger.warning(f"Invalid theme in config: {theme}, using default")

        except Exception as e:
            logger.error(f"Failed to load theme preference: {e}")
