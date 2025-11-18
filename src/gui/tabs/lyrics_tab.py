"""
Lyrics Tab - Feature #2
Display song lyrics with auto-search from Genius API

Features:
- Auto-search lyrics when song changes
- Manual search button (fallback)
- Background worker (non-blocking UI)
- Professional formatting
- Error handling with user-friendly messages

Created: November 17, 2025
"""
import logging
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton,
    QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class LyricsSearchWorker(QThread):
    """Background worker for lyrics search (non-blocking)"""

    finished = pyqtSignal(str)  # lyrics_text
    error = pyqtSignal(str)  # error_message

    def __init__(self, genius_client, title: str, artist: str):
        """
        Initialize search worker

        Args:
            genius_client: GeniusClient instance
            title: Song title
            artist: Artist name
        """
        super().__init__()
        self.genius_client = genius_client
        self.title = title
        self.artist = artist

    def run(self):
        """Execute background search"""
        try:
            logger.info(f"Worker searching: {self.title} - {self.artist}")
            lyrics = self.genius_client.search_lyrics(self.title, self.artist)

            if lyrics:
                self.finished.emit(lyrics)
            else:
                self.error.emit("Lyrics not found on Genius")

        except Exception as e:
            logger.error(f"Worker error: {e}")
            self.error.emit(f"Search failed: {str(e)}")


class LyricsTab(QWidget):
    """
    Tab for displaying song lyrics

    Features:
    - Auto-search when song changes
    - Manual search button
    - Scrollable lyrics display
    - Loading states
    - Error messages
    """

    def __init__(self, genius_client=None):
        """
        Initialize Lyrics tab

        Args:
            genius_client: GeniusClient instance (optional)
        """
        super().__init__()
        self.genius_client = genius_client
        self.current_song = None
        self._worker = None
        self._init_ui()

        logger.info("LyricsTab initialized")

    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # ========== Header Section ==========
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)

        # Song info label
        self.header_label = QLabel("🎵 No song playing")
        self.header_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                padding: 5px;
            }
        """)
        self.header_label.setWordWrap(True)
        header_layout.addWidget(self.header_label)

        # Status label (searching, found, error)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                padding: 2px;
            }
        """)
        self.status_label.setProperty("class", "secondary")  # Use theme color
        header_layout.addWidget(self.status_label)

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        # ========== Lyrics Display ==========
        self.lyrics_text = QTextEdit()
        self.lyrics_text.setReadOnly(True)
        self.lyrics_text.setPlaceholderText(
            "🎵 Play a song to see lyrics...\n\n"
            "Lyrics will automatically load from Genius.com"
        )

        # Professional monospace font for lyrics
        font = QFont("Consolas", 11)
        if not font.exactMatch():
            font = QFont("Courier New", 11)
        self.lyrics_text.setFont(font)

        # Let theme handle colors, only set padding
        self.lyrics_text.setStyleSheet("""
            QTextEdit {
                padding: 15px;
                line-height: 1.6;
            }
        """)

        layout.addWidget(self.lyrics_text)

        # ========== Bottom Controls ==========
        controls_layout = QHBoxLayout()

        # Manual search button
        self.search_button = QPushButton("🔍 Manual Search")
        self.search_button.setToolTip("Re-search for lyrics manually")
        self.search_button.clicked.connect(self._on_manual_search)
        self.search_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 10pt;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.search_button)

        # Copy button
        self.copy_button = QPushButton("📋 Copy Lyrics")
        self.copy_button.setToolTip("Copy lyrics to clipboard")
        self.copy_button.clicked.connect(self._on_copy_lyrics)
        self.copy_button.setEnabled(False)
        self.copy_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 10pt;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.copy_button)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        self.setLayout(layout)

    def on_song_changed(self, song_info: Dict):
        """
        Called when a new song starts playing

        Args:
            song_info: Dictionary with 'title', 'artist', 'album', etc.
        """
        self.current_song = song_info

        # Update header
        title = song_info.get('title', 'Unknown')
        artist = song_info.get('artist', 'Unknown Artist')
        self.header_label.setText(f"🎵 {title} - {artist}")

        # Auto-search lyrics
        logger.info(f"Song changed: {title} - {artist}")
        self._search_lyrics(title, artist)

    def _search_lyrics(self, title: str, artist: str):
        """
        Search for lyrics (background thread)

        Args:
            title: Song title
            artist: Artist name
        """
        # Check if Genius client available
        if not self.genius_client:
            self.lyrics_text.setPlainText(
                "❌ Genius API not configured\n\n"
                "To enable lyrics:\n"
                "1. Go to Settings → API Setup → Genius tab\n"
                "2. Get your free API token from genius.com/api-clients\n"
                "3. Paste token and save\n"
                "4. Restart the application"
            )
            self.status_label.setText("⚠️ API not configured")
            self.search_button.setEnabled(False)
            self.copy_button.setEnabled(False)
            return

        # Show loading state
        self.lyrics_text.setPlainText("⏳ Searching for lyrics on Genius...")
        self.status_label.setText("🔍 Searching...")
        self.search_button.setEnabled(False)
        self.copy_button.setEnabled(False)

        # Cancel previous search if still running
        if self._worker and self._worker.isRunning():
            logger.debug("Cancelling previous lyrics search")
            self._worker.quit()
            # Wait max 2 seconds, then force terminate
            if not self._worker.wait(2000):
                logger.warning("Previous search didn't stop, terminating")
                self._worker.terminate()
                self._worker.wait()

        # Start background search
        self._worker = LyricsSearchWorker(self.genius_client, title, artist)
        self._worker.finished.connect(self._on_lyrics_found)
        self._worker.error.connect(self._on_lyrics_error)
        self._worker.start()
        logger.debug("Started lyrics search worker")

    def _on_lyrics_found(self, lyrics: str):
        """
        Display found lyrics

        Args:
            lyrics: Lyrics text from Genius
        """
        self.lyrics_text.setPlainText(lyrics)
        self.status_label.setText("✅ Lyrics loaded from Genius")
        self.search_button.setEnabled(True)
        self.copy_button.setEnabled(True)

        logger.info(f"Lyrics displayed ({len(lyrics)} chars)")

    def _on_lyrics_error(self, error: str):
        """
        Show error message

        Args:
            error: Error message
        """
        self.lyrics_text.setPlainText(
            f"❌ {error}\n\n"
            "Possible reasons:\n"
            "• Song not found on Genius database\n"
            "• Artist/title mismatch\n"
            "• Network connection issue\n"
            "• Genius API rate limit\n\n"
            "Try:\n"
            "• Click 'Manual Search' to retry\n"
            "• Check your internet connection\n"
            "• Wait a moment and try again"
        )
        self.status_label.setText(f"❌ {error}")
        self.search_button.setEnabled(True)
        self.copy_button.setEnabled(False)

        logger.warning(f"Lyrics error: {error}")

    def _on_manual_search(self):
        """Manual search triggered by button"""
        if self.current_song:
            title = self.current_song.get('title', '')
            artist = self.current_song.get('artist', '')

            if title and artist:
                logger.info(f"Manual search: {title} - {artist}")
                self._search_lyrics(title, artist)
            else:
                self.status_label.setText("⚠️ No song loaded")
        else:
            self.status_label.setText("⚠️ Play a song first")

    def _on_copy_lyrics(self):
        """Copy lyrics to clipboard"""
        from PyQt6.QtWidgets import QApplication

        lyrics = self.lyrics_text.toPlainText()
        if lyrics and not lyrics.startswith("❌") and not lyrics.startswith("⏳"):
            clipboard = QApplication.clipboard()
            clipboard.setText(lyrics)
            self.status_label.setText("✅ Lyrics copied to clipboard")
            logger.info("Lyrics copied to clipboard")
        else:
            self.status_label.setText("⚠️ No lyrics to copy")
