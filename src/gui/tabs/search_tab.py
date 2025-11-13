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

        # Load API credentials
        secrets_path = Path.home() / ".claude" / "secrets" / "credentials.json"
        try:
            with open(secrets_path) as f:
                secrets = json.load(f)

            youtube_api_key = secrets['apis']['youtube']['api_key']
            spotify_client_id = secrets['apis']['spotify']['client_id']
            spotify_client_secret = secrets['apis']['spotify']['client_secret']

            self.youtube_searcher = YouTubeSearcher(youtube_api_key)
            self.spotify_searcher = SpotifySearcher(spotify_client_id, spotify_client_secret)

        except Exception as e:
            logger.error(f"Failed to load API credentials: {e}")
            # Create mock searchers for testing
            self.youtube_searcher = None
            self.spotify_searcher = None

        # Download queue
        self.download_queue = download_queue

        # Selected songs
        self.selected_songs = []

        # Setup UI
        self._setup_ui()

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
            item = QListWidgetItem(f"{result['title']}")
            item.setData(Qt.ItemDataRole.UserRole, result)
            self.youtube_results.addItem(item)

        logger.info(f"Displayed {len(results)} YouTube results")

    def _display_spotify_results(self, results: list):
        """
        Display Spotify results in UI

        Args:
            results (list): Spotify search results
        """
        for result in results:
            item = QListWidgetItem(f"{result['artist']} - {result['title']}")
            item.setData(Qt.ItemDataRole.UserRole, result)
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
            return

        if not self.download_queue:
            logger.warning("No download queue available")
            return

        # Add each song to download queue
        for song in self.selected_songs:
            try:
                # Determine URL based on source
                if song['source'] == 'youtube':
                    video_url = f"https://www.youtube.com/watch?v={song['video_id']}"
                elif song['source'] == 'spotify':
                    # For Spotify, we'll need to search YouTube for the song
                    # For now, just log
                    logger.info(f"Spotify song needs YouTube conversion: {song['title']}")
                    continue
                else:
                    logger.warning(f"Unknown source: {song['source']}")
                    continue

                # Add to queue
                self.download_queue.add(
                    video_url=video_url,
                    metadata=song
                )

                logger.info(f"Added to queue: {song['title']}")

            except Exception as e:
                logger.error(f"Failed to add song to queue: {e}")

        # Clear selection
        self.selected_songs = []
        self._update_selected_count()

        logger.info(f"Added {len(self.selected_songs)} songs to download queue")
