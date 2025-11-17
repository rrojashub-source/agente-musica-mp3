"""
Search Tab GUI - Phase 4.4
PyQt6 widget for searching music on YouTube and Spotify

Features:
- Dual source search (YouTube + Spotify)
- Split view results
- Song selection
- Add to download queue
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QCheckBox, QListWidget, QLabel, QSplitter, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
import logging
from api.youtube_search import YouTubeSearcher
from api.spotify_search import SpotifySearcher

# Setup logger
logger = logging.getLogger(__name__)


class SearchTab(QWidget):
    """
    Search tab for YouTube and Spotify music search

    Layout:
    +----------------------------------+
    | [Search Box] [Buscar]           |
    | [x] YouTube  [x] Spotify         |
    +----------------------------------+
    | YouTube Results      | Spotify   |
    | - Song 1 [+]        | - Song 1  |
    | - Song 2 [+]        | - Song 2  |
    +----------------------------------+
    | Selected: 5 songs   [Add to Lib]|
    +----------------------------------+
    """

    def __init__(self, download_queue=None):
        """
        Initialize search tab

        Args:
            download_queue (DownloadQueue): Download queue instance (optional)
        """
        super().__init__()

        # Initialize API searchers
        from pathlib import Path
        import json
        import os

        # Load API credentials (try multiple sources)
        youtube_api_key = None
        spotify_client_id = None
        spotify_client_secret = None

        # Priority 0: OS Keyring (most secure, used by API Settings dialog)
        try:
            import keyring
            youtube_api_key = keyring.get_password("nexus_music", "youtube_api_key")
            spotify_client_id = keyring.get_password("nexus_music", "spotify_client_id")
            spotify_client_secret = keyring.get_password("nexus_music", "spotify_client_secret")
            if youtube_api_key or spotify_client_id or spotify_client_secret:
                logger.info("Loaded credentials from OS keyring")
        except ImportError:
            logger.debug("keyring module not available")
        except Exception as e:
            logger.warning(f"Failed to load from keyring: {e}")

        # Priority 1: Environment variables
        youtube_api_key = youtube_api_key or os.getenv('YOUTUBE_API_KEY')
        spotify_client_id = spotify_client_id or os.getenv('SPOTIFY_CLIENT_ID')
        spotify_client_secret = spotify_client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')

        # Priority 2: .env file (if python-dotenv is available)
        if not all([youtube_api_key, spotify_client_id, spotify_client_secret]):
            try:
                from dotenv import load_dotenv
                env_path = Path('.env')
                if env_path.exists():
                    load_dotenv(env_path)
                    youtube_api_key = youtube_api_key or os.getenv('YOUTUBE_API_KEY')
                    spotify_client_id = spotify_client_id or os.getenv('SPOTIFY_CLIENT_ID')
                    spotify_client_secret = spotify_client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
                    logger.info("Loaded credentials from .env file")
            except ImportError:
                logger.debug("python-dotenv not available, skipping .env file")

        # Priority 3: Credentials file (fallback for development)
        if not all([youtube_api_key, spotify_client_id, spotify_client_secret]):
            credentials_path = os.getenv('CREDENTIALS_PATH') or str(Path.home() / ".claude" / "secrets" / "credentials.json")
            try:
                with open(credentials_path) as f:
                    secrets = json.load(f)

                youtube_api_key = youtube_api_key or secrets['apis']['youtube']['api_key']
                spotify_client_id = spotify_client_id or secrets['apis']['spotify']['client_id']
                spotify_client_secret = spotify_client_secret or secrets['apis']['spotify']['client_secret']
                logger.info(f"Loaded credentials from {credentials_path}")

            except FileNotFoundError:
                logger.warning(f"Credentials file not found: {credentials_path}")
            except KeyError as e:
                logger.error(f"Missing key in credentials file: {e}")
            except Exception as e:
                logger.error(f"Failed to load credentials file: {e}")

        # Initialize searchers if credentials available
        if youtube_api_key and spotify_client_id and spotify_client_secret:
            try:
                self.youtube_searcher = YouTubeSearcher(youtube_api_key)
                self.spotify_searcher = SpotifySearcher(spotify_client_id, spotify_client_secret)
                logger.info("API searchers initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize API searchers: {e}")
                self.youtube_searcher = None
                self.spotify_searcher = None
        else:
            logger.warning("Missing API credentials - Search functionality will be limited")
            logger.warning("Set YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET")
            logger.warning("Or create .env file (see .env.example)")
            self.youtube_searcher = None
            self.spotify_searcher = None

        # Download queue
        self.download_queue = download_queue

        # Selected songs
        self.selected_songs = []

        # Track if credentials are missing
        self._credentials_missing = not (youtube_api_key and spotify_client_id and spotify_client_secret)

        # Setup UI
        self._setup_ui()

        # Show API configuration dialog if credentials missing
        if self._credentials_missing:
            self._show_missing_credentials_prompt()

        logger.info("SearchTab initialized")

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search for songs...")
        self.search_box.returnPressed.connect(self.on_search_clicked)

        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.on_search_clicked)

        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        # Source checkboxes
        checkbox_layout = QHBoxLayout()

        self.youtube_checkbox = QCheckBox("YouTube")
        self.youtube_checkbox.setChecked(True)

        self.spotify_checkbox = QCheckBox("Spotify")
        self.spotify_checkbox.setChecked(True)

        checkbox_layout.addWidget(self.youtube_checkbox)
        checkbox_layout.addWidget(self.spotify_checkbox)
        checkbox_layout.addStretch()

        layout.addLayout(checkbox_layout)

        # Results split view
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # YouTube results
        youtube_widget = QWidget()
        youtube_layout = QVBoxLayout()
        youtube_label = QLabel("YouTube Results")
        self.youtube_results = QListWidget()
        self.youtube_results.itemDoubleClicked.connect(self._on_youtube_item_clicked)
        youtube_layout.addWidget(youtube_label)
        youtube_layout.addWidget(self.youtube_results)
        youtube_widget.setLayout(youtube_layout)

        # Spotify results
        spotify_widget = QWidget()
        spotify_layout = QVBoxLayout()
        spotify_label = QLabel("Spotify Results")
        self.spotify_results = QListWidget()
        self.spotify_results.itemDoubleClicked.connect(self._on_spotify_item_clicked)
        spotify_layout.addWidget(spotify_label)
        spotify_layout.addWidget(self.spotify_results)
        spotify_widget.setLayout(spotify_layout)

        splitter.addWidget(youtube_widget)
        splitter.addWidget(spotify_widget)

        layout.addWidget(splitter)

        # Bottom bar
        bottom_layout = QHBoxLayout()

        self.selected_count_label = QLabel("Selected: 0 songs")

        self.add_to_library_button = QPushButton("Add to Library")
        self.add_to_library_button.clicked.connect(self.on_add_to_library_clicked)

        bottom_layout.addWidget(self.selected_count_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.add_to_library_button)

        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    def on_search_clicked(self):
        """
        Handle search button click

        Searches YouTube and/or Spotify based on checkbox selection
        """
        query = self.search_box.text().strip()

        if not query:
            logger.warning("Empty search query")
            return False

        # Clear previous results
        self.youtube_results.clear()
        self.spotify_results.clear()

        # Search enabled sources
        if self.youtube_checkbox.isChecked() and self.youtube_searcher:
            self._search_youtube(query)

        if self.spotify_checkbox.isChecked() and self.spotify_searcher:
            self._search_spotify(query)

        logger.info(f"Search completed for: {query}")
        return True

    def _search_youtube(self, query: str):
        """
        Search YouTube

        Args:
            query (str): Search query
        """
        try:
            results = self.youtube_searcher.search(query, max_results=10)
            self._display_youtube_results(results)
        except Exception as e:
            logger.error(f"YouTube search error: {e}")

    def _search_spotify(self, query: str):
        """
        Search Spotify

        Args:
            query (str): Search query
        """
        try:
            results = self.spotify_searcher.search_tracks(query, limit=10)
            self._display_spotify_results(results)
        except Exception as e:
            logger.error(f"Spotify search error: {e}")

    def _display_youtube_results(self, results: list):
        """
        Display YouTube results in UI

        Args:
            results (list): YouTube search results
        """
        for result in results:
            # Add visual indicator for YouTube
            item = QListWidgetItem(f"▶️ {result['title']}")
            item.setData(Qt.ItemDataRole.UserRole, result)
            item.setToolTip("YouTube video - Click 'Add to Library' to download")
            self.youtube_results.addItem(item)

        logger.info(f"Displayed {len(results)} YouTube results")

    def _display_spotify_results(self, results: list):
        """
        Display Spotify results in UI

        Args:
            results (list): Spotify search results
        """
        for result in results:
            # Add visual indicator for Spotify (now with auto-conversion)
            item = QListWidgetItem(f"🎵 {result['artist']} - {result['title']}")
            item.setData(Qt.ItemDataRole.UserRole, result)
            item.setToolTip("Spotify track - Will auto-convert to YouTube for download")
            self.spotify_results.addItem(item)

        logger.info(f"Displayed {len(results)} Spotify results")

    def _on_youtube_item_clicked(self, item):
        """Handle YouTube item selection"""
        data = item.data(Qt.ItemDataRole.UserRole)
        data['source'] = 'youtube'
        self._add_to_selection(data)

    def _on_spotify_item_clicked(self, item):
        """Handle Spotify item selection"""
        data = item.data(Qt.ItemDataRole.UserRole)
        data['source'] = 'spotify'
        self._add_to_selection(data)

    def _add_to_selection(self, song_data: dict):
        """
        Add song to selection

        Args:
            song_data (dict): Song data
        """
        self.selected_songs.append(song_data)
        self._update_selected_count()
        logger.info(f"Added to selection: {song_data.get('title', 'Unknown')}")

    def _convert_spotify_to_youtube(self, spotify_song: dict) -> dict:
        """
        Convert Spotify song to YouTube video by searching

        Args:
            spotify_song (dict): Spotify song metadata with 'artist' and 'title'

        Returns:
            dict: YouTube video data, or None if not found
        """
        if not self.youtube_searcher:
            logger.error("YouTube searcher not available for Spotify conversion")
            return None

        try:
            # Build search query from Spotify metadata
            artist = spotify_song.get('artist', '')
            title = spotify_song.get('title', '')
            search_query = f"{artist} {title}".strip()

            if not search_query:
                logger.warning("Empty search query for Spotify conversion")
                return None

            logger.info(f"Converting Spotify to YouTube: '{search_query}'")

            # Search YouTube for this song
            youtube_results = self.youtube_searcher.search(search_query, max_results=1)

            if youtube_results and len(youtube_results) > 0:
                youtube_video = youtube_results[0]
                logger.info(f"Found YouTube match: {youtube_video['title']}")

                # Merge Spotify metadata with YouTube video_id
                converted = {
                    'source': 'spotify_converted',
                    'video_id': youtube_video['video_id'],
                    'title': title,  # Use Spotify title (cleaner)
                    'artist': artist,  # Use Spotify artist (cleaner)
                    'youtube_title': youtube_video['title'],  # Keep original for reference
                    'spotify_metadata': spotify_song  # Keep full Spotify metadata
                }

                return converted
            else:
                logger.warning(f"No YouTube results found for: {search_query}")
                return None

        except Exception as e:
            logger.error(f"Error converting Spotify to YouTube: {e}")
            return None

    def _update_selected_count(self):
        """Update selected songs counter"""
        count = len(self.selected_songs)
        self.selected_count_label.setText(f"Selected: {count} songs")

    def on_add_to_library_clicked(self):
        """
        Handle 'Add to Library' button click

        Adds selected songs to download queue
        """
        if not self.selected_songs:
            logger.warning("No songs selected")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "No Songs Selected",
                "Please select songs first by double-clicking on them."
            )
            return

        if not self.download_queue:
            logger.warning("No download queue available")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Download Queue Error",
                "Download queue is not available. Please restart the application."
            )
            return

        # Count successful additions
        added_count = 0
        total_selected = len(self.selected_songs)

        # Track conversion stats
        spotify_converted = 0
        spotify_failed = 0

        # Add each song to download queue
        for song in self.selected_songs:
            try:
                video_url = None
                metadata = song

                # Determine URL based on source
                if song['source'] == 'youtube':
                    # Direct YouTube download
                    video_url = f"https://www.youtube.com/watch?v={song['video_id']}"

                elif song['source'] == 'spotify':
                    # Convert Spotify to YouTube
                    logger.info(f"Converting Spotify song: {song.get('artist', '')} - {song.get('title', '')}")
                    converted = self._convert_spotify_to_youtube(song)

                    if converted:
                        video_url = f"https://www.youtube.com/watch?v={converted['video_id']}"
                        metadata = converted  # Use converted metadata (has both Spotify + YouTube data)
                        spotify_converted += 1
                        logger.info(f"Spotify converted successfully: {converted['title']}")
                    else:
                        spotify_failed += 1
                        logger.warning(f"Failed to convert Spotify song: {song.get('title', 'Unknown')}")
                        continue

                else:
                    logger.warning(f"Unknown source: {song['source']}")
                    continue

                # Add to queue if we have a valid URL
                if video_url:
                    self.download_queue.add(
                        video_url=video_url,
                        metadata=metadata
                    )

                    logger.info(f"Added to queue: {metadata.get('title', 'Unknown')}")
                    added_count += 1

            except Exception as e:
                logger.error(f"Failed to add song to queue: {e}")

        # Clear selection (both data and visual)
        self.selected_songs = []
        self._update_selected_count()

        # Clear visual selection from both lists
        self.youtube_results.clearSelection()
        self.spotify_results.clearSelection()

        # Show confirmation
        if added_count > 0:
            from PyQt6.QtWidgets import QMessageBox
            message = f"Added {added_count} song(s) to download queue!\n\n"

            # Show conversion stats
            if spotify_converted > 0:
                message += f"✅ Spotify songs converted: {spotify_converted}\n"
            if spotify_failed > 0:
                message += f"⚠️ Spotify songs failed to convert: {spotify_failed}\n"

            if spotify_converted > 0 or spotify_failed > 0:
                message += "\n"

            message += "Check the '📥 Queue' tab to see download progress."

            QMessageBox.information(self, "Success", message)
            logger.info(f"Added {added_count} songs to download queue (Spotify converted: {spotify_converted}, failed: {spotify_failed})")
        else:
            from PyQt6.QtWidgets import QMessageBox
            message = "No songs were added to the queue.\n\n"

            if spotify_failed > 0:
                message += f"⚠️ {spotify_failed} Spotify song(s) could not be converted to YouTube.\n\n"
                message += "This can happen if:\n"
                message += "• The song is not available on YouTube\n"
                message += "• The search didn't find a good match\n\n"
                message += "Try selecting different songs or using YouTube search directly."
            else:
                message += "Please select some songs first by double-clicking on them."

            QMessageBox.warning(self, "No Songs Added", message)

    def _show_missing_credentials_prompt(self):
        """
        Show prompt to configure API keys when credentials are missing

        Uses QTimer to delay dialog until UI is fully initialized
        """
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QMessageBox

        def show_dialog():
            # Show informative message first
            reply = QMessageBox.information(
                self,
                "API Configuration Required",
                "To use the Search & Download feature, you need to configure your API keys:\n\n"
                "• YouTube Data API v3 key\n"
                "• Spotify Client ID and Client Secret\n\n"
                "Would you like to configure them now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Import and show API settings dialog
                from gui.dialogs.api_settings_dialog import APISettingsDialog

                dialog = APISettingsDialog(self)
                dialog.keys_saved.connect(self._on_keys_saved)

                if dialog.exec():
                    logger.info("API settings dialog closed - credentials may have been saved")

        # Delay dialog until UI is ready (500ms)
        QTimer.singleShot(500, show_dialog)

    def _on_keys_saved(self):
        """
        Handle keys saved event - reload credentials and initialize searchers
        """
        import keyring

        logger.info("API keys saved - reloading credentials")

        try:
            # Load from keyring
            youtube_api_key = keyring.get_password("nexus_music", "youtube_api_key")
            spotify_client_id = keyring.get_password("nexus_music", "spotify_client_id")
            spotify_client_secret = keyring.get_password("nexus_music", "spotify_client_secret")

            # Re-initialize searchers
            if youtube_api_key and spotify_client_id and spotify_client_secret:
                self.youtube_searcher = YouTubeSearcher(youtube_api_key)
                self.spotify_searcher = SpotifySearcher(spotify_client_id, spotify_client_secret)
                self._credentials_missing = False

                logger.info("API searchers re-initialized successfully")

                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Success",
                    "API credentials configured successfully!\n\nYou can now search for music."
                )
            else:
                logger.warning("Some credentials still missing after save")

        except Exception as e:
            logger.error(f"Error reloading credentials: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to reload credentials:\n{str(e)}"
            )
