#!/usr/bin/env python3
"""
API Configuration Wizard - Interactive setup for all 3 APIs
Project: AGENTE_MUSICA_MP3_001
Purpose: Guide user through YouTube, Spotify, and Genius API setup
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextBrowser, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class APIConfigWizard(QWizard):
    """
    Interactive wizard to configure all 3 APIs:
    - YouTube Data API v3
    - Spotify Web API
    - Genius API
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("🔑 API Configuration Wizard")
        self.setGeometry(200, 100, 800, 600)

        # Pages
        self.addPage(WelcomePage())
        self.addPage(YouTubeAPIPage())
        self.addPage(SpotifyAPIPage())
        self.addPage(GeniusAPIPage())
        self.addPage(CompletionPage())

        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        # Buttons
        self.setButtonText(QWizard.WizardButton.NextButton, "Next ➡️")
        self.setButtonText(QWizard.WizardButton.BackButton, "⬅️ Back")
        self.setButtonText(QWizard.WizardButton.FinishButton, "✅ Finish")
        self.setButtonText(QWizard.WizardButton.CancelButton, "❌ Cancel")


class WelcomePage(QWizardPage):
    """Welcome page explaining the wizard"""

    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to API Configuration")
        self.setSubTitle("Let's set up your API keys for enhanced features")

        layout = QVBoxLayout(self)

        # Explanation
        info = QTextBrowser()
        info.setOpenExternalLinks(True)
        info.setHtml("""
        <html>
        <body style='font-family: Arial; font-size: 12px;'>
            <h2>🎵 NEXUS Music Manager - API Setup</h2>

            <p>This wizard will help you configure <b>3 API keys</b> to unlock all features:</p>

            <h3>1. 🔴 YouTube Data API v3</h3>
            <ul>
                <li><b>Purpose:</b> Search and download music from YouTube</li>
                <li><b>Cost:</b> FREE (10,000 queries/day)</li>
                <li><b>Required for:</b> Search & Download, Playlist Downloader</li>
            </ul>

            <h3>2. 🟢 Spotify Web API</h3>
            <ul>
                <li><b>Purpose:</b> Search Spotify catalog for metadata</li>
                <li><b>Cost:</b> FREE (100 requests/second)</li>
                <li><b>Required for:</b> Search & Download (alternative source)</li>
            </ul>

            <h3>3. 🟡 Genius API</h3>
            <ul>
                <li><b>Purpose:</b> Fetch song lyrics</li>
                <li><b>Cost:</b> FREE (unlimited)</li>
                <li><b>Required for:</b> Music Player lyrics display</li>
            </ul>

            <hr>

            <p><b>⏱️ Time required:</b> ~10-15 minutes total</p>
            <p><b>📝 Note:</b> You can skip any API and configure it later</p>

            <br>
            <p style='text-align:center;'>
                <i>Click <b>Next</b> to start configuration ➡️</i>
            </p>
        </body>
        </html>
        """)
        layout.addWidget(info)


class YouTubeAPIPage(QWizardPage):
    """YouTube API configuration"""

    def __init__(self):
        super().__init__()
        self.setTitle("🔴 YouTube Data API v3")
        self.setSubTitle("Get your free YouTube API key")

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QTextBrowser()
        instructions.setOpenExternalLinks(True)
        instructions.setMaximumHeight(250)
        instructions.setHtml("""
        <html>
        <body style='font-family: Arial; font-size: 11px;'>
            <h3>How to get your YouTube API key:</h3>
            <ol>
                <li>Go to <a href='https://console.developers.google.com/'>Google Cloud Console</a></li>
                <li>Create a new project or select existing</li>
                <li>Enable <b>YouTube Data API v3</b></li>
                <li>Go to <b>Credentials</b> → Create Credentials → <b>API Key</b></li>
                <li>Copy your API key and paste below</li>
            </ol>

            <p><b>📹 Video Tutorial:</b> <a href='https://www.youtube.com/watch?v=5sZ8m0kN_gg'>
            Watch on YouTube</a></p>
        </body>
        </html>
        """)
        layout.addWidget(instructions)

        # Input
        input_layout = QHBoxLayout()
        input_label = QLabel("API Key:")
        input_label.setFixedWidth(80)
        input_layout.addWidget(input_label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("AIzaSy...")
        self.api_key_input.textChanged.connect(self.validate_input)
        input_layout.addWidget(self.api_key_input)

        self.test_btn = QPushButton("🧪 Test")
        self.test_btn.clicked.connect(self.test_api_key)
        self.test_btn.setEnabled(False)
        input_layout.addWidget(self.test_btn)

        layout.addLayout(input_layout)

        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Skip option
        self.skip_checkbox = QCheckBox("Skip YouTube API (configure later)")
        layout.addWidget(self.skip_checkbox)

        layout.addStretch()

        # Register field
        self.registerField("youtube_api_key", self.api_key_input)

    def validate_input(self, text: str):
        """Enable test button when input is valid"""
        self.test_btn.setEnabled(len(text) > 10)

    def test_api_key(self):
        """Test YouTube API key"""
        api_key = self.api_key_input.text().strip()

        try:
            from googleapiclient.discovery import build

            youtube = build('youtube', 'v3', developerKey=api_key)
            request = youtube.search().list(q="test", part="id", maxResults=1)
            request.execute()

            self.status_label.setText("✅ YouTube API key is valid!")
            self.status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "Success", "YouTube API key works!")

        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.warning(self, "Invalid Key", f"API key test failed:\n{str(e)}")


class SpotifyAPIPage(QWizardPage):
    """Spotify API configuration"""

    def __init__(self):
        super().__init__()
        self.setTitle("🟢 Spotify Web API")
        self.setSubTitle("Get your free Spotify API credentials")

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QTextBrowser()
        instructions.setOpenExternalLinks(True)
        instructions.setMaximumHeight(250)
        instructions.setHtml("""
        <html>
        <body style='font-family: Arial; font-size: 11px;'>
            <h3>How to get your Spotify API credentials:</h3>
            <ol>
                <li>Go to <a href='https://developer.spotify.com/dashboard'>Spotify Developer Dashboard</a></li>
                <li>Log in with your Spotify account (or create one)</li>
                <li>Click <b>Create an App</b></li>
                <li>Fill in app name and description (anything works)</li>
                <li>Copy <b>Client ID</b> and <b>Client Secret</b></li>
            </ol>

            <p><b>📹 Video Tutorial:</b> <a href='https://www.youtube.com/watch?v=WAmEZBEeNmg'>
            Watch on YouTube</a></p>
        </body>
        </html>
        """)
        layout.addWidget(instructions)

        # Client ID
        client_id_layout = QHBoxLayout()
        client_id_label = QLabel("Client ID:")
        client_id_label.setFixedWidth(100)
        client_id_layout.addWidget(client_id_label)

        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("abc123...")
        client_id_layout.addWidget(self.client_id_input)

        layout.addLayout(client_id_layout)

        # Client Secret
        client_secret_layout = QHBoxLayout()
        client_secret_label = QLabel("Client Secret:")
        client_secret_label.setFixedWidth(100)
        client_secret_layout.addWidget(client_secret_label)

        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("xyz789...")
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        client_secret_layout.addWidget(self.client_secret_input)

        self.show_password_btn = QPushButton("👁️")
        self.show_password_btn.setFixedWidth(40)
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        client_secret_layout.addWidget(self.show_password_btn)

        layout.addLayout(client_secret_layout)

        # Test button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_btn = QPushButton("🧪 Test Credentials")
        self.test_btn.clicked.connect(self.test_credentials)
        test_layout.addWidget(self.test_btn)
        layout.addLayout(test_layout)

        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Skip option
        self.skip_checkbox = QCheckBox("Skip Spotify API (configure later)")
        layout.addWidget(self.skip_checkbox)

        layout.addStretch()

        # Register fields
        self.registerField("spotify_client_id", self.client_id_input)
        self.registerField("spotify_client_secret", self.client_secret_input)

    def toggle_password_visibility(self, checked: bool):
        """Toggle password visibility"""
        if checked:
            self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("👁️")

    def test_credentials(self):
        """Test Spotify credentials"""
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()

        if not client_id or not client_secret:
            QMessageBox.warning(self, "Missing Info", "Please enter both Client ID and Secret")
            return

        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials

            auth_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            sp = spotipy.Spotify(auth_manager=auth_manager)

            # Test search
            sp.search(q="test", limit=1)

            self.status_label.setText("✅ Spotify credentials are valid!")
            self.status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "Success", "Spotify API credentials work!")

        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.warning(self, "Invalid Credentials", f"Test failed:\n{str(e)}")


class GeniusAPIPage(QWizardPage):
    """Genius API configuration"""

    def __init__(self):
        super().__init__()
        self.setTitle("🟡 Genius API")
        self.setSubTitle("Get your free Genius API token")

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QTextBrowser()
        instructions.setOpenExternalLinks(True)
        instructions.setMaximumHeight(250)
        instructions.setHtml("""
        <html>
        <body style='font-family: Arial; font-size: 11px;'>
            <h3>How to get your Genius API token:</h3>
            <ol>
                <li>Go to <a href='https://genius.com/api-clients'>Genius API Clients</a></li>
                <li>Log in with your account (or create one - it's free!)</li>
                <li>Click <b>New API Client</b></li>
                <li>Fill in app name and website (any values work)</li>
                <li>Click <b>Generate Access Token</b></li>
                <li>Copy your <b>Client Access Token</b></li>
            </ol>

            <p><b>Note:</b> This enables lyrics display in the music player</p>
        </body>
        </html>
        """)
        layout.addWidget(instructions)

        # Input
        input_layout = QHBoxLayout()
        input_label = QLabel("Access Token:")
        input_label.setFixedWidth(100)
        input_layout.addWidget(input_label)

        self.api_token_input = QLineEdit()
        self.api_token_input.setPlaceholderText("Your Genius access token...")
        input_layout.addWidget(self.api_token_input)

        self.test_btn = QPushButton("🧪 Test")
        self.test_btn.clicked.connect(self.test_token)
        input_layout.addWidget(self.test_btn)

        layout.addLayout(input_layout)

        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Skip option
        self.skip_checkbox = QCheckBox("Skip Genius API (configure later)")
        layout.addWidget(self.skip_checkbox)

        layout.addStretch()

        # Register field
        self.registerField("genius_access_token", self.api_token_input)

    def test_token(self):
        """Test Genius API token"""
        token = self.api_token_input.text().strip()

        if not token:
            QMessageBox.warning(self, "Missing Token", "Please enter your access token")
            return

        try:
            import requests

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                "https://api.genius.com/search?q=test",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self.status_label.setText("✅ Genius API token is valid!")
                self.status_label.setStyleSheet("color: green;")
                QMessageBox.information(self, "Success", "Genius API token works!")
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.warning(self, "Invalid Token", f"Test failed:\n{str(e)}")


class CompletionPage(QWizardPage):
    """Completion page with summary"""

    def __init__(self):
        super().__init__()
        self.setTitle("✅ Configuration Complete!")
        self.setSubTitle("Your API keys have been saved")

        layout = QVBoxLayout(self)

        # Summary
        self.summary_browser = QTextBrowser()
        layout.addWidget(self.summary_browser)

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        self.open_config_btn = QPushButton("📝 Open Config File")
        self.open_config_btn.clicked.connect(self.open_config_file)
        save_layout.addWidget(self.open_config_btn)

        layout.addLayout(save_layout)

    def initializePage(self):
        """Called when page is displayed"""
        # Get field values
        youtube_key = self.field("youtube_api_key") or ""
        spotify_id = self.field("spotify_client_id") or ""
        spotify_secret = self.field("spotify_client_secret") or ""
        genius_token = self.field("genius_access_token") or ""

        # Save to config file
        config_file = Path(__file__).parent / "api_keys_config.txt"

        with open(config_file, 'w') as f:
            f.write("# NEXUS Music Manager - API Configuration\n")
            f.write("# Generated by API Configuration Wizard\n\n")

            f.write("# YouTube Data API v3\n")
            f.write(f"YOUTUBE_API_KEY={youtube_key}\n\n")

            f.write("# Spotify Web API\n")
            f.write(f"SPOTIFY_CLIENT_ID={spotify_id}\n")
            f.write(f"SPOTIFY_CLIENT_SECRET={spotify_secret}\n\n")

            f.write("# Genius API\n")
            f.write(f"GENIUS_ACCESS_TOKEN={genius_token}\n")

        # Generate summary
        configured = []
        skipped = []

        if youtube_key:
            configured.append("🔴 YouTube Data API")
        else:
            skipped.append("YouTube")

        if spotify_id and spotify_secret:
            configured.append("🟢 Spotify Web API")
        else:
            skipped.append("Spotify")

        if genius_token:
            configured.append("🟡 Genius API")
        else:
            skipped.append("Genius")

        summary_html = f"""
        <html>
        <body style='font-family: Arial; font-size: 12px;'>
            <h2>✅ Configuration Saved!</h2>

            <h3>Configured APIs:</h3>
            <ul>
                {''.join(f'<li>{api}</li>' for api in configured) if configured else '<li><i>None</i></li>'}
            </ul>

            <h3>Skipped (can configure later):</h3>
            <ul>
                {''.join(f'<li>{api}</li>' for api in skipped) if skipped else '<li><i>None</i></li>'}
            </ul>

            <hr>

            <p><b>📁 Config file location:</b><br>
            <code>{config_file}</code></p>

            <p><b>🔧 To reconfigure later:</b><br>
            Go to Help tab → API Configuration</p>

            <br>
            <p style='text-align:center; color:green;'>
                <b>🎉 You're all set! Click Finish to close.</b>
            </p>
        </body>
        </html>
        """

        self.summary_browser.setHtml(summary_html)

    def open_config_file(self):
        """Open config file in system editor"""
        import subprocess
        import platform

        config_file = Path(__file__).parent / "api_keys_config.txt"

        system = platform.system()

        try:
            if system == "Windows":
                subprocess.run(["notepad", str(config_file)])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(config_file)])
            else:  # Linux
                subprocess.run(["xdg-open", str(config_file)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file:\n{str(e)}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    wizard = APIConfigWizard()
    wizard.show()
    sys.exit(app.exec())
