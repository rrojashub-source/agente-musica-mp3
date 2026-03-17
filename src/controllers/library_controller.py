"""
Library Controller — Phase 2.1

Handles library navigation: album selection, recommendations routing,
search focus, tab switching, empty library check.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtWidgets import QMessageBox, QStatusBar, QTabWidget, QWidget

from database.manager import DatabaseManager

logger = logging.getLogger(__name__)


class LibraryController:
    """Manages library navigation and cross-component routing"""

    def __init__(self, db_manager: DatabaseManager, status_bar: Optional[QStatusBar] = None) -> None:
        self.db_manager: DatabaseManager = db_manager
        self.status_bar: Optional[QStatusBar] = status_bar

        # Late-bound widget references
        self.tabs: Optional[QTabWidget] = None
        self.library_tab: Optional[QWidget] = None
        self.search_tab: Optional[QWidget] = None
        self.recommendations_widget: Optional[QWidget] = None

    def set_widgets(
        self,
        tabs: Optional[QTabWidget] = None,
        library_tab: Optional[QWidget] = None,
        search_tab: Optional[QWidget] = None,
        recommendations_widget: Optional[QWidget] = None,
        status_bar: Optional[QStatusBar] = None,
    ) -> None:
        """Set widget references created after controller init"""
        if tabs is not None:
            self.tabs = tabs
        if library_tab is not None:
            self.library_tab = library_tab
        if search_tab is not None:
            self.search_tab = search_tab
        if recommendations_widget is not None:
            self.recommendations_widget = recommendations_widget
        if status_bar is not None:
            self.status_bar = status_bar

    def on_album_selected(self, album_data: dict[str, Any]) -> None:
        """Handle album selection from grid — switch to library and filter"""
        album_name = album_data.get("album", "")
        artist_name = album_data.get("artist", "")

        if self.library_tab and self.tabs:
            self.tabs.setCurrentWidget(self.library_tab)

            if hasattr(self.library_tab, "search_box"):
                self.library_tab.search_box.setText(album_name)
                self.library_tab.search_box.returnPressed.emit()

            if self.status_bar:
                self.status_bar.showMessage(f"Showing album: {album_name}", 3000)
            logger.info(f"Album selected: {album_name} by {artist_name}")

    def update_recommendations(self, song_data: dict[str, Any]) -> None:
        """Update recommendations based on current song"""
        if self.recommendations_widget:
            self.recommendations_widget.set_current_song(song_data)

    def on_find_similar_requested(self, song_data: dict[str, Any]) -> None:
        """Handle find similar songs request — update Brain AI panel"""
        if self.recommendations_widget:
            self.recommendations_widget.set_current_song(song_data)
            if self.status_bar:
                self.status_bar.showMessage(f"Finding similar to: {song_data.get('title', 'Unknown')}", 3000)

    def handle_focus_search(self) -> None:
        """Handle Ctrl+F — Focus search tab and input"""
        if self.search_tab and self.tabs:
            self.tabs.setCurrentWidget(self.search_tab)
            if hasattr(self.search_tab, "search_box"):
                self.search_tab.search_box.setFocus()
                logger.debug("Shortcut: Focused search")

    def handle_switch_tab(self, tab_name: str) -> None:
        """Handle Ctrl+L/D — Switch to named tab"""
        if not self.tabs:
            return

        if tab_name == "library" and self.library_tab:
            self.tabs.setCurrentWidget(self.library_tab)
            logger.debug("Shortcut: Switched to Library tab")
        elif tab_name == "queue":
            # Find queue widget by checking tab texts
            for i in range(self.tabs.count()):
                if "Queue" in self.tabs.tabText(i) or "Cola" in self.tabs.tabText(i):
                    self.tabs.setCurrentIndex(i)
                    logger.debug("Shortcut: Switched to Queue tab")
                    break

    def check_empty_library(self, parent_window: QWidget) -> None:
        """Check if library is empty and suggest importing music"""
        try:
            song_count = self.db_manager.get_song_count()

            if song_count == 0:
                logger.info("Library is empty, showing import suggestion")

                QMessageBox.information(
                    parent_window,
                    "Welcome to NEXUS Music Manager",
                    "Your music library is empty.\n\n"
                    "Would you like to import your MP3 collection now?\n\n"
                    "Go to the '📥 Import Library' tab to get started.",
                    QMessageBox.StandardButton.Ok,
                )

                # Switch to Import tab
                if self.tabs:
                    for i in range(self.tabs.count()):
                        if "Import" in self.tabs.tabText(i):
                            self.tabs.setCurrentIndex(i)
                            logger.info("Switched to Import tab automatically")
                            break

        except Exception as e:  # GUI error boundary - DB/Qt errors must not crash startup
            logger.error(f"Error checking library status: {e}")
