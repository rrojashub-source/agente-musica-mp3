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

from __future__ import annotations

import logging
from typing import Optional, Tuple

import keyring
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Import API clients at module level for testability
try:
    from api.spotify_search import SpotifySearcher
    from api.youtube_search import YouTubeSearcher
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

    def __init__(self, api_name: str, service_name: str = "nexus_music", keyring_key: str = "") -> None:
        """
        Initialize API tab

        Args:
            api_name: Display name (e.g., "YouTube", "Spotify")
            service_name: Keyring service identifier
            keyring_key: Explicit keyring key (overrides auto-generated name)
        """
        super().__init__()
        self.api_name: str = api_name
        self.service_name: str = service_name
        self.keyring_key: str = keyring_key or f"{api_name.lower()}_api_key"
        self.api_key_input: QLineEdit
        self.validate_button: QPushButton
        self.clear_button: QPushButton
        self.status_label: QLabel
        self._setup_ui()
        self._load_existing_key()

    def _setup_ui(self) -> None:
        """Setup UI components - Bilingual (ES/EN)"""
        layout = QVBoxLayout()

        # API Key input group
        input_group = QGroupBox(f"Configuración de {self.api_name} / {self.api_name} Configuration")
        input_layout = QVBoxLayout()

        # API Key input field
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText(
            f"Pega tu clave de {self.api_name} aquí / Paste your {self.api_name} API key here"
        )
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addWidget(QLabel(f"Clave API de {self.api_name} / {self.api_name} API Key:"))
        input_layout.addWidget(self.api_key_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.validate_button = QPushButton("Validar / Validate")
        self.validate_button.clicked.connect(self._on_validate_clicked)
        self.clear_button = QPushButton("Limpiar / Clear")
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
        self.status_label.setStyleSheet(
            """
            QLabel {
                padding: 10px;
                border-radius: 5px;
            }
        """
        )
        self.status_label.setProperty("class", "secondary")  # Use theme color
        layout.addWidget(self.status_label)

        # Instructions (detailed guide) - Bilingual
        if self.api_name == "YouTube":
            instructions_text = """
<b>📺 Cómo obtener clave de YouTube / How to get YouTube API key:</b>
<ol style="margin-left: -20px;">
<li>Ir a / Go to <a href="https://console.cloud.google.com/">Google Cloud Console</a></li>
<li>Crear proyecto nuevo (o seleccionar existente) / Create new project (or select existing)</li>
<li>Activar "YouTube Data API v3" / Enable "YouTube Data API v3"</li>
<li>Ir a "Credentials" → "Create Credentials" → "API Key"</li>
<li>Copiar la clave y pegarla arriba / Copy the API key and paste it above</li>
<li>Clic en "Validar" para probar / Click "Validate" to test</li>
</ol>
<p><b>💡 Consejo / Tip:</b> Nivel gratis = 10,000 unidades/día (≈ 100 búsquedas) / Free tier = 10,000 units/day (≈ 100 searches)</p>
<p><small>Para instrucciones detalladas: Ayuda → Guía API (F2) / For detailed instructions: Help → API Guide (F2)</small></p>
            """
        elif self.api_name == "Genius":
            instructions_text = """
<b>🎤 Cómo obtener token de Genius / How to get Genius API token:</b>
<ol style="margin-left: -20px;">
<li>Ir a / Go to <a href="https://genius.com/api-clients">Genius API Clients</a></li>
<li>Iniciar sesión con tu cuenta Genius / Log in with your Genius account</li>
<li>Crear nuevo cliente API / Create a new API client</li>
<li>Copiar "Client Access Token" / Copy the "Client Access Token"</li>
<li>Pegarlo arriba y clic en "Validar" / Paste it above and click "Validate"</li>
</ol>
<p><b>💡 Consejo / Tip:</b> Nivel gratis = búsquedas de letras ilimitadas / Free tier = unlimited lyrics searches</p>
<p><small>Para instrucciones detalladas: Ayuda → Guía API (F2) / For detailed instructions: Help → API Guide (F2)</small></p>
            """
        elif self.api_name == "AcoustID":
            instructions_text = """
<b>🎵 Cómo obtener clave de AcoustID / How to get AcoustID API key:</b>
<ol style="margin-left: -20px;">
<li>Ir a / Go to <a href="https://acoustid.org/new-application">AcoustID New Application</a></li>
<li>Registrarse o iniciar sesión / Register or log in</li>
<li>Completar / Fill in:
    <ul>
    <li>Application Name: "NEXUS Music Manager"</li>
    <li>Version: "2.0"</li>
    <li>Description: "Personal music library manager"</li>
    </ul>
</li>
<li>Enviar formulario / Submit the form</li>
<li>Copiar tu clave API (8+ caracteres) / Copy your API key (8+ characters)</li>
<li>Pegarla arriba y clic en "Validar" / Paste it above and click "Validate"</li>
</ol>
<p><b>💡 ¿Qué es AcoustID? / What is AcoustID?</b> Servicio de huellas de audio que identifica canciones por su firma acústica (similar a Shazam). / Audio fingerprinting service that identifies songs by their acoustic signature (similar to Shazam).</p>
<p><b>⚠️ Requisito / Prerequisite:</b> Requiere fpcalc.exe (Chromaprint) en carpeta tools/. / Requires fpcalc.exe (Chromaprint) in tools/ folder.</p>
<p><small>Para instrucciones detalladas: Ayuda → Guía API (F2) / For detailed instructions: Help → API Guide (F2)</small></p>
            """
        else:
            instructions_text = f"""
<b>Cómo obtener clave de {self.api_name} / How to get {self.api_name} API key:</b><br>
Clic en 'Validar' para probar tu clave. / Click 'Validate' to test your key.
<p><small>Para instrucciones detalladas: Ayuda → Guía API (F2) / For detailed instructions: Help → API Guide (F2)</small></p>
            """

        instructions = QLabel(instructions_text)
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True)  # Enable clickable links
        instructions.setStyleSheet(
            """
            QLabel {
                padding: 15px;
                border-radius: 5px;
            }
        """
        )
        instructions.setFrameStyle(QFrame.Shape.StyledPanel)  # Use themed border
        layout.addWidget(instructions)

        layout.addStretch()
        self.setLayout(layout)

    def _load_existing_key(self) -> None:
        """Load existing key from keyring"""
        try:
            key = keyring.get_password(self.service_name, self.keyring_key)
            if key:
                self.api_key_input.setText(key)
                self.status_label.setText("✅ Clave existente cargada / Existing key loaded")
                logger.info(f"{self.api_name} key loaded from keyring")
        except (RuntimeError, OSError) as e:
            logger.debug(f"No existing key for {self.api_name}: {e}")
            self.status_label.setText(
                "ℹ️ No hay clave guardada. Ingresa tu clave arriba. / No existing key. Please enter your API key above."
            )

    def _on_validate_clicked(self) -> None:
        """Validate API key by making test request"""
        api_key = self.api_key_input.text().strip()

        if not api_key:
            self.status_label.setText("❌ Por favor ingresa una clave / Please enter an API key")
            return

        self.status_label.setText("⏳ Validando... / Validating...")
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
            elif self.api_name == "AcoustID":
                self._validate_acoustid(api_key)
        except Exception as e:  # GUI error boundary - must not crash
            self.status_label.setText(f"❌ Inválida / Invalid: {e}")
            logger.error(f"{self.api_name} validation failed: {e}")
        finally:
            self.validate_button.setEnabled(True)

    def _validate_youtube(self, api_key: str) -> None:
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
                self.status_label.setText("✅ Válida - YouTube API funcionando! / Valid - YouTube API working!")
                logger.info("YouTube API key validated successfully")
            else:
                raise Exception("Sin resultados (posible límite de cuota) / No results (API may be quota-limited)")

        except ImportError:
            # Fallback: Just validate format
            if len(api_key) >= 30:
                self.status_label.setText("✅ Válida - Formato de clave correcto / Valid - API key format correct")
            else:
                raise Exception(
                    "Clave muy corta (esperado 30+ caracteres) / API key too short (expected 30+ characters)"
                )

    def _validate_spotify(self, client_id: str) -> None:
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
            self.status_label.setText("✅ Válida - Formato de Client ID correcto / Valid - Client ID format correct")
            logger.info("Spotify Client ID format validated")
        else:
            raise Exception(
                "Formato inválido (esperado 32 caracteres alfanuméricos) / Invalid format (expected 32 alphanumeric characters)"
            )

    def _validate_genius(self, api_key: str) -> None:
        """
        Validate Genius API token by making a test API call.

        Args:
            api_key: Genius API token

        Raises:
            Exception: If validation fails
        """
        if len(api_key) < 20:
            raise Exception("Token muy corto (esperado 20+ caracteres) / Token too short (expected 20+ characters)")

        import requests

        r = requests.get(
            "https://api.genius.com/search",
            params={"q": "test"},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if r.status_code == 200:
            self.status_label.setText("✅ Válida - Genius API funcionando! / Valid - Genius API working!")
            logger.info("Genius token validated successfully via API")
        elif r.status_code == 401:
            raise Exception("Token expirado o inválido / Token expired or invalid")
        else:
            raise Exception(f"Error HTTP {r.status_code}")

    def _validate_acoustid(self, api_key: str) -> None:
        """
        Validate AcoustID API key

        Args:
            api_key: AcoustID API key

        Raises:
            Exception: If validation fails
        """
        # AcoustID API key format: typically 8+ characters (alphanumeric, may include hyphens)
        # Examples: "8XaBELgH" or "abc123de-f456-7890-abcd-ef1234567890"
        # Remove hyphens and check if remaining chars are alphanumeric
        cleaned_key = api_key.replace("-", "").replace("_", "")

        if len(cleaned_key) >= 8 and cleaned_key.isalnum():
            self.status_label.setText("✅ Válida - Formato de clave correcto / Valid - API key format correct")
            logger.info("AcoustID API key format validated")
        else:
            raise Exception(
                f"Formato inválido (esperado 8+ caracteres, tienes {len(cleaned_key)}) / Invalid format (expected 8+ chars, got {len(cleaned_key)})"
            )

    def get_api_key(self) -> str:
        """
        Get current API key value

        Returns:
            str: API key (trimmed)
        """
        return self.api_key_input.text().strip()  # type: ignore[no-any-return]


class SpotifyTabWidget(QWidget):
    """
    Specialized tab for Spotify (needs Client ID + Client Secret)
    """

    def __init__(self, service_name: str = "nexus_music") -> None:
        super().__init__()
        self.service_name: str = service_name
        self.client_id_input: QLineEdit
        self.client_secret_input: QLineEdit
        self.validate_button: QPushButton
        self.clear_button: QPushButton
        self.status_label: QLabel
        self._setup_ui()
        self._load_existing_keys()

    def _setup_ui(self) -> None:
        """Setup UI with Client ID + Client Secret fields - Bilingual (ES/EN)"""
        layout = QVBoxLayout()

        # Spotify credentials group
        input_group = QGroupBox("Configuración de Spotify / Spotify Configuration")
        input_layout = QVBoxLayout()

        # Client ID field
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Pega tu Client ID aquí / Paste your Spotify Client ID here")
        self.client_id_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addWidget(QLabel("Spotify Client ID:"))
        input_layout.addWidget(self.client_id_input)

        # Client Secret field
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText(
            "Pega tu Client Secret aquí / Paste your Spotify Client Secret here"
        )
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addWidget(QLabel("Spotify Client Secret:"))
        input_layout.addWidget(self.client_secret_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.validate_button = QPushButton("Validar / Validate")
        self.validate_button.clicked.connect(self._on_validate_clicked)
        self.clear_button = QPushButton("Limpiar ambos / Clear Both")
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
        self.status_label.setStyleSheet(
            """
            QLabel {
                padding: 10px;
                border-radius: 5px;
            }
        """
        )
        self.status_label.setProperty("class", "secondary")  # Use theme color
        layout.addWidget(self.status_label)

        # Instructions (detailed guide) - Bilingual
        instructions_text = """
<b>🎵 Cómo obtener credenciales de Spotify / How to get Spotify credentials:</b>
<ol style="margin-left: -20px;">
<li>Ir a / Go to <a href="https://developer.spotify.com/dashboard">Spotify Developer Dashboard</a></li>
<li>Iniciar sesión con tu cuenta Spotify (cuenta gratis funciona) / Log in with your Spotify account (free account works)</li>
<li>Clic en "Create App" / Click "Create App"</li>
<li>Completar / Fill in:
    <ul>
    <li>App Name: "NEXUS Music Manager"</li>
    <li>App Description: "Personal music library"</li>
    <li>Redirect URI: http://localhost:8888/callback</li>
    <li>Marcar "Web API" / Check "Web API"</li>
    </ul>
</li>
<li>Clic en "Settings" en tu nueva app / Click "Settings" on your new app</li>
<li>Copiar "Client ID" y pegar arriba / Copy "Client ID" and paste above</li>
<li>Clic en "View client secret" y copiar / Click "View client secret" and copy</li>
<li>Clic en "Validar" para probar / Click "Validate" to test</li>
</ol>
<p><b>💡 Consejo / Tip:</b> Nivel gratis = búsquedas ilimitadas (con límite de velocidad) / Free tier = unlimited searches (rate limited)</p>
<p><small>Para instrucciones detalladas: Ayuda → Guía API (F2) / For detailed instructions: Help → API Guide (F2)</small></p>
        """

        instructions = QLabel(instructions_text)
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True)
        instructions.setStyleSheet(
            """
            QLabel {
                padding: 15px;
                border-radius: 5px;
            }
        """
        )
        instructions.setFrameStyle(QFrame.Shape.StyledPanel)  # Use themed border
        layout.addWidget(instructions)

        layout.addStretch()
        self.setLayout(layout)

    def _load_existing_keys(self) -> None:
        """Load existing Spotify credentials from keyring"""
        try:
            client_id = keyring.get_password(self.service_name, "spotify_client_id")
            client_secret = keyring.get_password(self.service_name, "spotify_client_secret")

            if client_id:
                self.client_id_input.setText(client_id)
            if client_secret:
                self.client_secret_input.setText(client_secret)

            if client_id and client_secret:
                self.status_label.setText("✅ Credenciales cargadas / Existing credentials loaded")
                logger.info("Spotify credentials loaded from keyring")
            elif client_id or client_secret:
                self.status_label.setText(
                    "⚠️ Credenciales parciales. Ingresa ambos. / Partial credentials. Please enter both."
                )
            else:
                self.status_label.setText(
                    "ℹ️ Sin credenciales. Ingresa ambas arriba. / No credentials. Please enter both above."
                )
        except (RuntimeError, OSError) as e:
            logger.debug(f"No existing Spotify credentials: {e}")
            self.status_label.setText(
                "ℹ️ Sin credenciales. Ingresa ambas arriba. / No credentials. Please enter both above."
            )

    def _clear_fields(self) -> None:
        """Clear both input fields"""
        self.client_id_input.clear()
        self.client_secret_input.clear()

    def _on_validate_clicked(self) -> None:
        """Validate Spotify credentials"""
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()

        if not client_id or not client_secret:
            self.status_label.setText(
                "❌ Por favor ingresa ambos Client ID y Secret / Please enter both Client ID and Secret"
            )
            return

        self.status_label.setText("⏳ Validando... / Validating...")
        self.validate_button.setEnabled(False)
        QApplication.processEvents()

        try:
            if SpotifySearcher is None:
                raise ImportError("SpotifySearcher not available")

            # Test Spotify authentication
            spotify = SpotifySearcher(client_id, client_secret)
            results = spotify.search_tracks("test", limit=1)

            if results:
                self.status_label.setText("✅ Válidas - Spotify API funcionando! / Valid - Spotify API working!")
                logger.info("Spotify credentials validated successfully")
            else:
                raise Exception("Sin resultados / No results returned")

        except ImportError:
            # Fallback: Just validate format
            if len(client_id) == 32 and client_id.isalnum():
                if len(client_secret) == 32 and client_secret.isalnum():
                    self.status_label.setText("✅ Válidas - Formato correcto / Valid - Format correct")
                else:
                    self.status_label.setText("❌ Formato de Client Secret inválido / Invalid Client Secret format")
            else:
                self.status_label.setText("❌ Formato de Client ID inválido / Invalid Client ID format")
        except Exception as e:  # GUI error boundary - must not crash
            self.status_label.setText(f"❌ Inválidas / Invalid: {e}")
            logger.error(f"Spotify validation failed: {e}")
        finally:
            self.validate_button.setEnabled(True)

    def get_credentials(self) -> Tuple[str, str]:
        """
        Get Spotify credentials

        Returns:
            tuple: (client_id, client_secret)
        """
        return (self.client_id_input.text().strip(), self.client_secret_input.text().strip())


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

    keys_saved = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize API Settings Dialog - Bilingual (ES/EN)

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.tab_widget: QTabWidget
        self.youtube_tab: APITabWidget
        self.spotify_tab: SpotifyTabWidget
        self.genius_tab: APITabWidget
        self.acoustid_tab: APITabWidget
        self.save_button: QPushButton
        self.cancel_button: QPushButton
        self.setWindowTitle("Configuración de API / API Settings")
        self.setMinimumSize(650, 550)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup dialog UI - Bilingual (ES/EN)"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("<h2>🔑 Configuración de API / API Configuration</h2>")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Tab widget for different APIs
        self.tab_widget = QTabWidget()

        # Create tabs
        self.youtube_tab = APITabWidget("YouTube", keyring_key="youtube_api_key")
        self.spotify_tab = SpotifyTabWidget()  # Specialized for Client ID + Secret
        self.genius_tab = APITabWidget("Genius", keyring_key="genius_token")
        self.acoustid_tab = APITabWidget("AcoustID", keyring_key="acoustid_api_key")

        self.tab_widget.addTab(self.youtube_tab, "📺 YouTube")
        self.tab_widget.addTab(self.spotify_tab, "🎵 Spotify")
        self.tab_widget.addTab(self.genius_tab, "🎤 Genius (Letras/Lyrics)")
        self.tab_widget.addTab(self.acoustid_tab, "🎧 AcoustID (Huellas/Fingerprint)")

        layout.addWidget(self.tab_widget)

        # Bottom buttons - Bilingual
        button_layout = QHBoxLayout()

        # Help button
        help_button = QPushButton("Ayuda / Help")
        help_button.clicked.connect(self._on_help_clicked)

        # Save button
        self.save_button = QPushButton("Guardar y Cerrar / Save & Close")
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setDefault(True)

        # Cancel button
        self.cancel_button = QPushButton("Cancelar / Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(help_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _on_help_clicked(self) -> None:
        """Show help dialog with instructions - Bilingual (ES/EN)"""
        from PySide6.QtWidgets import QMessageBox

        help_text = """
<h3>Cómo obtener claves de API / How to Get API Keys:</h3>

<b>YouTube Data API v3:</b><br>
1. Ir a / Go to: <a href="https://console.cloud.google.com">console.cloud.google.com</a><br>
2. Crear proyecto / Create a project<br>
3. Activar "YouTube Data API v3" / Enable "YouTube Data API v3"<br>
4. Crear credenciales → API Key / Create credentials → API Key<br>
5. Copiar y pegar arriba / Copy and paste above<br>
<br>

<b>Spotify Web API:</b><br>
1. Ir a / Go to: <a href="https://developer.spotify.com/dashboard">developer.spotify.com/dashboard</a><br>
2. Crear una app / Create an app<br>
3. Copiar Client ID y Client Secret / Copy Client ID and Client Secret<br>
<br>

<b>Genius API (Opcional / Optional):</b><br>
1. Ir a / Go to: <a href="https://genius.com/api-clients">genius.com/api-clients</a><br>
2. Crear cliente API / Create an API client<br>
3. Copiar Access Token / Copy Access Token<br>
<br>

<b>AcoustID (Opcional / Optional):</b><br>
1. Ir a / Go to: <a href="https://acoustid.org/new-application">acoustid.org/new-application</a><br>
2. Registrar aplicación / Register application<br>
3. Copiar API Key / Copy API Key<br>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Ayuda de API / API Help")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _on_save_clicked(self) -> None:
        """Save all API keys to keyring"""
        try:
            saved_count = 0

            # Save single-key tabs (YouTube, Genius, AcoustID)
            for tab in (self.youtube_tab, self.genius_tab, self.acoustid_tab):
                key = tab.get_api_key()
                if key:
                    keyring.set_password("nexus_music", tab.keyring_key, key)
                    logger.info(f"{tab.api_name} key saved to keyring ({tab.keyring_key})")
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
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Credenciales Spotify Incompletas / Incomplete Spotify Credentials",
                    "Por favor ingresa ambos Client ID y Client Secret, o deja ambos vacíos.\n\n"
                    "Please enter both Spotify Client ID and Client Secret, or leave both empty.",
                )

            if saved_count > 0:
                logger.info(f"Saved {saved_count} API key(s) to secure storage")
                self.keys_saved.emit()
                self.accept()
            else:
                # No keys entered
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Sin Claves / No Keys Entered",
                    "Por favor ingresa al menos una clave API antes de guardar.\n\n"
                    "Please enter at least one API key before saving.",
                )

        except (RuntimeError, OSError) as e:
            logger.error(f"Error saving keys to keyring: {e}")
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "Error al Guardar / Error Saving Keys",
                f"No se pudo guardar las claves API:\n{e}\n\n"
                f"Verifica el acceso al keyring del sistema.\n\n"
                f"Failed to save API keys. Please check system keyring access.",
            )


# Standalone test
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    dialog = APISettingsDialog()
    dialog.exec()

    sys.exit(app.exec())
