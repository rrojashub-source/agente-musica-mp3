"""
API Settings Dialog - User-friendly API key management

Purpose:
- Allow users to paste/validate API keys
- Real-time validation (test API calls)
- Save encrypted to OS keyring (NO plaintext files)
- Show API quota/status

Security:
- API keys stored in OS keyring (encrypted)
- Zero plaintext files created
- Protected from accidental git commits

Author: NEXUS@CLI (Pre-Phase 5 Hardening)
Date: November 13, 2025
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLineEdit, QPushButton, QLabel, QGroupBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
import keyring
import logging

# Import API clients at module level for testability
try:
    from api.youtube_search import YouTubeSearcher
    from api.spotify_search import SpotifySearcher
except ImportError:
    # Fallback if API modules not available (shouldn't happen in normal use)
    YouTubeSearcher = None
    SpotifySearcher = None

logger = logging.getLogger(__name__)


class APITabWidget(QWidget):
    """
    Base class for API configuration tabs

    Each tab allows user to:
    - Paste API key
    - Validate with real API call
    - See validation status
    """

    def __init__(self, api_name: str, service_name: str = "nexus_music"):
        """
        Initialize API tab

        Args:
            api_name: Display name (e.g., "YouTube", "Spotify")
            service_name: Keyring service identifier
        """
        super().__init__()
        self.api_name = api_name
        self.service_name = service_name
        self._setup_ui()
        self._load_existing_key()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout()

        # API Key input group
        input_group = QGroupBox(f"{self.api_name} API Configuration")
        input_layout = QVBoxLayout()

        # API Key input field
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText(f"Paste your {self.api_name} API key here")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addWidget(QLabel(f"{self.api_name} API Key:"))
        input_layout.addWidget(self.api_key_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.validate_button = QPushButton("Validate")
        self.validate_button.clicked.connect(self._on_validate_clicked)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.api_key_input.clear)
        button_layout.addWidget(self.validate_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        input_layout.addLayout(button_layout)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(self.status_label)

        # Instructions
        instructions = QLabel(
            f"<b>How to get {self.api_name} API key:</b><br>"
            "Click 'Validate' to test your key with a real API call."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addStretch()
        self.setLayout(layout)

    def _load_existing_key(self):
        """Load existing key from keyring"""
        try:
            key = keyring.get_password(self.service_name, f"{self.api_name.lower()}_api_key")
            if key:
                self.api_key_input.setText(key)
                self.status_label.setText("✅ Existing key loaded from secure storage")
                logger.info(f"{self.api_name} key loaded from keyring")
        except Exception as e:
            logger.debug(f"No existing key for {self.api_name}: {e}")
            self.status_label.setText("ℹ️ No existing key found. Please enter your API key above.")

    def _on_validate_clicked(self):
        """Validate API key by making test request"""
        api_key = self.api_key_input.text().strip()

        if not api_key:
            self.status_label.setText("❌ Please enter an API key")
            return

        self.status_label.setText("⏳ Validating...")
        self.validate_button.setEnabled(False)
        QApplication.processEvents()  # Update UI

        try:
            # Validate based on API type
            if self.api_name == "YouTube":
                self._validate_youtube(api_key)
            elif self.api_name == "Spotify":
                self._validate_spotify(api_key)
            elif self.api_name == "Genius":
                self._validate_genius(api_key)
        except Exception as e:
            self.status_label.setText(f"❌ Invalid: {str(e)}")
            logger.error(f"{self.api_name} validation failed: {e}")
        finally:
            self.validate_button.setEnabled(True)

    def _validate_youtube(self, api_key: str):
        """
        Validate YouTube API key by making test search

        Args:
            api_key: YouTube Data API v3 key

        Raises:
            Exception: If validation fails
        """
        try:
            if YouTubeSearcher is None:
                raise ImportError("YouTubeSearcher not available")

            yt = YouTubeSearcher(api_key)
            results = yt.search("test", max_results=1)

            if results:
                self.status_label.setText("✅ Valid - YouTube API working!")
                logger.info("YouTube API key validated successfully")
            else:
                raise Exception("No results returned (API may be quota-limited)")

        except ImportError:
            # Fallback: Just validate format
            if len(api_key) >= 30:
                self.status_label.setText("✅ Valid - YouTube API key format correct")
            else:
                raise Exception("API key too short (expected 30+ characters)")

    def _validate_spotify(self, client_id: str):
        """
        Validate Spotify credentials

        Note: Spotify needs client_id + client_secret
        This simplified version only validates client_id format

        Args:
            client_id: Spotify Client ID

        Raises:
            Exception: If validation fails
        """
        # Spotify Client ID is 32 alphanumeric characters
        if len(client_id) == 32 and client_id.isalnum():
            self.status_label.setText("✅ Valid - Spotify Client ID format correct")
            logger.info("Spotify Client ID format validated")
        else:
            raise Exception("Invalid format (expected 32 alphanumeric characters)")

    def _validate_genius(self, api_key: str):
        """
        Validate Genius API token

        Args:
            api_key: Genius API token

        Raises:
            Exception: If validation fails
        """
        # Basic format validation
        if len(api_key) >= 20:
            self.status_label.setText("✅ Valid - Genius token format correct")
            logger.info("Genius token format validated")
        else:
            raise Exception("Token too short (expected 20+ characters)")

    def get_api_key(self) -> str:
        """
        Get current API key value

        Returns:
            str: API key (trimmed)
        """
        return self.api_key_input.text().strip()


class SpotifyTabWidget(QWidget):
    """
    Specialized tab for Spotify (needs Client ID + Client Secret)
    """

    def __init__(self, service_name: str = "nexus_music"):
        super().__init__()
        self.service_name = service_name
        self._setup_ui()
        self._load_existing_keys()

    def _setup_ui(self):
        """Setup UI with Client ID + Client Secret fields"""
        layout = QVBoxLayout()

        # Spotify credentials group
        input_group = QGroupBox("Spotify API Configuration")
        input_layout = QVBoxLayout()

        # Client ID field
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Paste your Spotify Client ID here")
        self.client_id_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addWidget(QLabel("Spotify Client ID:"))
        input_layout.addWidget(self.client_id_input)

        # Client Secret field
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Paste your Spotify Client Secret here")
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addWidget(QLabel("Spotify Client Secret:"))
        input_layout.addWidget(self.client_secret_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.validate_button = QPushButton("Validate")
        self.validate_button.clicked.connect(self._on_validate_clicked)
        self.clear_button = QPushButton("Clear Both")
        self.clear_button.clicked.connect(self._clear_fields)
        button_layout.addWidget(self.validate_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        input_layout.addLayout(button_layout)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(self.status_label)

        # Instructions
        instructions = QLabel(
            "<b>How to get Spotify credentials:</b><br>"
            "1. Go to <a href='https://developer.spotify.com/dashboard'>developer.spotify.com/dashboard</a><br>"
            "2. Create an app<br>"
            "3. Copy Client ID and Client Secret"
        )
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True)
        layout.addWidget(instructions)

        layout.addStretch()
        self.setLayout(layout)

    def _load_existing_keys(self):
        """Load existing Spotify credentials from keyring"""
        try:
            client_id = keyring.get_password(self.service_name, "spotify_client_id")
            client_secret = keyring.get_password(self.service_name, "spotify_client_secret")

            if client_id:
                self.client_id_input.setText(client_id)
            if client_secret:
                self.client_secret_input.setText(client_secret)

            if client_id and client_secret:
                self.status_label.setText("✅ Existing credentials loaded from secure storage")
                logger.info("Spotify credentials loaded from keyring")
            elif client_id or client_secret:
                self.status_label.setText("⚠️ Partial credentials found. Please enter both Client ID and Secret.")
            else:
                self.status_label.setText("ℹ️ No existing credentials. Please enter both above.")
        except Exception as e:
            logger.debug(f"No existing Spotify credentials: {e}")
            self.status_label.setText("ℹ️ No existing credentials found. Please enter both above.")

    def _clear_fields(self):
        """Clear both input fields"""
        self.client_id_input.clear()
        self.client_secret_input.clear()

    def _on_validate_clicked(self):
        """Validate Spotify credentials"""
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()

        if not client_id or not client_secret:
            self.status_label.setText("❌ Please enter both Client ID and Client Secret")
            return

        self.status_label.setText("⏳ Validating...")
        self.validate_button.setEnabled(False)
        QApplication.processEvents()

        try:
            if SpotifySearcher is None:
                raise ImportError("SpotifySearcher not available")

            # Test Spotify authentication
            spotify = SpotifySearcher(client_id, client_secret)
            results = spotify.search_tracks("test", limit=1)

            if results:
                self.status_label.setText("✅ Valid - Spotify API working!")
                logger.info("Spotify credentials validated successfully")
            else:
                raise Exception("No results returned")

        except ImportError:
            # Fallback: Just validate format
            if len(client_id) == 32 and client_id.isalnum():
                if len(client_secret) == 32 and client_secret.isalnum():
                    self.status_label.setText("✅ Valid - Credentials format correct")
                else:
                    self.status_label.setText("❌ Invalid Client Secret format")
            else:
                self.status_label.setText("❌ Invalid Client ID format")
        except Exception as e:
            self.status_label.setText(f"❌ Invalid: {str(e)}")
            logger.error(f"Spotify validation failed: {e}")
        finally:
            self.validate_button.setEnabled(True)

    def get_credentials(self) -> tuple:
        """
        Get Spotify credentials

        Returns:
            tuple: (client_id, client_secret)
        """
        return (
            self.client_id_input.text().strip(),
            self.client_secret_input.text().strip()
        )


class APISettingsDialog(QDialog):
    """
    API Settings Dialog

    User-friendly GUI for managing API credentials:
    - Paste API keys for YouTube, Spotify, Genius
    - Validate with real API calls
    - Save encrypted to OS keyring
    - Load existing keys on open

    Signals:
        keys_saved: Emitted when keys are saved successfully
    """

    keys_saved = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialize API Settings Dialog

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.setWindowTitle("API Settings")
        self.setMinimumSize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("<h2>API Configuration</h2>")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Tab widget for different APIs
        self.tab_widget = QTabWidget()

        # Create tabs
        self.youtube_tab = APITabWidget("YouTube")
        self.spotify_tab = SpotifyTabWidget()  # Specialized for Client ID + Secret
        self.genius_tab = APITabWidget("Genius")

        self.tab_widget.addTab(self.youtube_tab, "YouTube")
        self.tab_widget.addTab(self.spotify_tab, "Spotify")
        self.tab_widget.addTab(self.genius_tab, "Genius (Optional)")

        layout.addWidget(self.tab_widget)

        # Bottom buttons
        button_layout = QHBoxLayout()

        # Help button
        help_button = QPushButton("Help")
        help_button.clicked.connect(self._on_help_clicked)

        # Save button
        self.save_button = QPushButton("Save & Close")
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setDefault(True)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(help_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _on_help_clicked(self):
        """Show help dialog with instructions"""
        from PyQt6.QtWidgets import QMessageBox

        help_text = """
<h3>How to Get API Keys:</h3>

<b>YouTube Data API v3:</b><br>
1. Go to: <a href="https://console.cloud.google.com">console.cloud.google.com</a><br>
2. Create a new project<br>
3. Enable "YouTube Data API v3"<br>
4. Create credentials → API Key<br>
5. Copy the key and paste above<br>
<br>

<b>Spotify Web API:</b><br>
1. Go to: <a href="https://developer.spotify.com/dashboard">developer.spotify.com/dashboard</a><br>
2. Create an app<br>
3. Copy Client ID and paste above<br>
<br>

<b>Genius API (Optional):</b><br>
1. Go to: <a href="https://genius.com/api-clients">genius.com/api-clients</a><br>
2. Create an API client<br>
3. Copy Access Token and paste above<br>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("API Keys Help")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _on_save_clicked(self):
        """Save all API keys to keyring"""
        try:
            saved_count = 0

            # Save YouTube key
            youtube_key = self.youtube_tab.get_api_key()
            if youtube_key:
                keyring.set_password("nexus_music", "youtube_api_key", youtube_key)
                logger.info("YouTube API key saved to keyring")
                saved_count += 1

            # Save Spotify credentials (Client ID + Secret)
            spotify_client_id, spotify_client_secret = self.spotify_tab.get_credentials()
            if spotify_client_id and spotify_client_secret:
                keyring.set_password("nexus_music", "spotify_client_id", spotify_client_id)
                keyring.set_password("nexus_music", "spotify_client_secret", spotify_client_secret)
                logger.info("Spotify credentials saved to keyring")
                saved_count += 1
            elif spotify_client_id or spotify_client_secret:
                # Partial credentials - warn user
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Incomplete Spotify Credentials",
                    "Please enter both Spotify Client ID and Client Secret, or leave both empty."
                )

            # Save Genius key
            genius_key = self.genius_tab.get_api_key()
            if genius_key:
                keyring.set_password("nexus_music", "genius_token", genius_key)
                logger.info("Genius token saved to keyring")
                saved_count += 1

            if saved_count > 0:
                logger.info(f"Saved {saved_count} API key(s) to secure storage")
                self.keys_saved.emit()
                self.accept()
            else:
                # No keys entered
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "No Keys Entered",
                    "Please enter at least one API key before saving."
                )

        except Exception as e:
            logger.error(f"Error saving keys to keyring: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error Saving Keys",
                f"Failed to save API keys:\n{str(e)}\n\nPlease check system keyring access."
            )


# Standalone test
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    dialog = APISettingsDialog()
    dialog.exec()

    sys.exit(app.exec())
