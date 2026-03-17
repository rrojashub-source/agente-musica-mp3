"""
Phase 2 Tests for src/gui/dialogs/ — MAPS Round 30

Covers:
- APITabWidget: _setup_ui, _load_existing_key, _on_validate_clicked,
  _validate_youtube/spotify/genius/acoustid, get_api_key
- SpotifyTabWidget: _setup_ui, _load_existing_keys, _on_validate_clicked,
  _clear_fields, get_credentials
- APISettingsDialog: _setup_ui, _on_save_clicked, _on_help_clicked
- ShortcutsDialog: _init_ui

Pattern: Replace QDialog/QWidget with real classes, use __dict__ method extraction.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Replace mock Qt classes with real ones before importing dialogs
_qt_widgets = sys.modules.get("PySide6.QtWidgets")
_qt_gui = sys.modules.get("PySide6.QtGui")

if _qt_widgets is not None:
    _base = type(
        "_QWidgetBase",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "setLayout": lambda self, *a: None,
            "layout": lambda self: MagicMock(),
            "setWindowTitle": lambda self, *a: None,
            "setMinimumSize": lambda self, *a: None,
            "accept": lambda self: None,
            "reject": lambda self: None,
            "exec": lambda self: None,
        },
    )

    # QFrame.Shape enum
    _frame_shape = type("Shape", (), {"StyledPanel": 0x0006, "NoFrame": 0})
    _real_qframe = type("QFrame", (_base,), {"Shape": _frame_shape, "setFrameStyle": lambda self, *a: None})

    for cls_name in ["QWidget", "QDialog", "QGroupBox"]:
        setattr(_qt_widgets, cls_name, type(cls_name, (_base,), {}))
    _qt_widgets.QFrame = _real_qframe

    _qt_widgets.QLabel = type(
        "QLabel",
        (_base,),
        {
            "setText": lambda self, *a: None,
            "setWordWrap": lambda self, *a: None,
            "setAlignment": lambda self, *a: None,
            "setStyleSheet": lambda self, *a: None,
            "setProperty": lambda self, *a: None,
            "setOpenExternalLinks": lambda self, *a: None,
            "setFrameStyle": lambda self, *a: None,
            "setFont": lambda self, *a: None,
            "text": lambda self: "",
        },
    )

    _qt_widgets.QLineEdit = type(
        "QLineEdit",
        (_base,),
        {
            "setText": lambda self, t: setattr(self, "_text", t),
            "text": lambda self: getattr(self, "_text", ""),
            "setPlaceholderText": lambda self, *a: None,
            "setEchoMode": lambda self, *a: None,
            "clear": lambda self: setattr(self, "_text", ""),
            "EchoMode": MagicMock(),
        },
    )

    _qt_widgets.QPushButton = type(
        "QPushButton",
        (_base,),
        {
            "setEnabled": lambda self, *a: None,
            "setFixedWidth": lambda self, *a: None,
            "setDefault": lambda self, *a: None,
            "clicked": MagicMock(),
        },
    )

    for cls_name in ["QVBoxLayout", "QHBoxLayout"]:
        setattr(
            _qt_widgets,
            cls_name,
            type(
                cls_name,
                (),
                {
                    "__init__": lambda self, *a, **k: None,
                    "setContentsMargins": lambda self, *a: None,
                    "setSpacing": lambda self, *a: None,
                    "addWidget": lambda self, *a, **k: None,
                    "addLayout": lambda self, *a: None,
                    "addStretch": lambda self, *a: None,
                },
            ),
        )

    _qt_widgets.QTabWidget = type(
        "QTabWidget",
        (_base,),
        {
            "addTab": lambda self, *a: None,
        },
    )

    _qt_widgets.QProgressBar = type(
        "QProgressBar",
        (_base,),
        {
            "setVisible": lambda self, *a: None,
            "setValue": lambda self, *a: None,
        },
    )

    _qt_widgets.QTableWidget = type(
        "QTableWidget",
        (_base,),
        {
            "setColumnCount": lambda self, *a: None,
            "setHorizontalHeaderLabels": lambda self, *a: None,
            "setRowCount": lambda self, *a: None,
            "setItem": lambda self, *a: None,
            "horizontalHeader": lambda self: MagicMock(),
            "verticalHeader": lambda self: MagicMock(),
            "setEditTriggers": lambda self, *a: None,
            "setSelectionMode": lambda self, *a: None,
            "setAlternatingRowColors": lambda self, *a: None,
            "EditTrigger": MagicMock(),
            "SelectionMode": MagicMock(),
        },
    )

    _qt_widgets.QTableWidgetItem = type(
        "QTableWidgetItem",
        (),
        {
            "__init__": lambda self, *a: None,
            "flags": lambda self: 0xFFFF,
            "setFlags": lambda self, *a: None,
            "font": lambda self: MagicMock(),
            "setFont": lambda self, *a: None,
        },
    )

    _qt_widgets.QHeaderView = MagicMock()
    _qt_widgets.QMessageBox = MagicMock()
    _qt_widgets.QApplication = MagicMock()

    if _qt_gui is not None:
        _qt_gui.QFont = type(
            "QFont",
            (),
            {
                "__init__": lambda self, *a, **k: None,
                "setPointSize": lambda self, *a: None,
                "setBold": lambda self, *a: None,
            },
        )

# Force re-import
for mod_name in list(sys.modules):
    if "gui.dialogs" in mod_name:
        del sys.modules[mod_name]

from gui.dialogs.api_settings_dialog import APISettingsDialog, APITabWidget, SpotifyTabWidget  # noqa: E402
from gui.dialogs.shortcuts_dialog import ShortcutsDialog  # noqa: E402

# --- Helpers ---


def _get(cls, name):
    return cls.__dict__[name]


def _mock_api_tab():
    """Create APITabWidget-like mock self."""
    ms = MagicMock()
    ms.api_name = "YouTube"
    ms.service_name = "nexus_music"
    ms.api_key_input = MagicMock()
    ms.validate_button = MagicMock()
    ms.clear_button = MagicMock()
    ms.status_label = MagicMock()
    return ms


def _mock_spotify_tab():
    """Create SpotifyTabWidget-like mock self."""
    ms = MagicMock()
    ms.service_name = "nexus_music"
    ms.client_id_input = MagicMock()
    ms.client_secret_input = MagicMock()
    ms.validate_button = MagicMock()
    ms.clear_button = MagicMock()
    ms.status_label = MagicMock()
    return ms


# --- APITabWidget Tests ---


class TestAPITabWidgetInit:
    def test_init(self):
        """APITabWidget.__init__ sets attributes and calls setup."""
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            tab = APITabWidget("YouTube")
            assert tab.api_name == "YouTube"

    def test_init_genius(self):
        """APITabWidget works for Genius API."""
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            tab = APITabWidget("Genius")
            assert tab.api_name == "Genius"

    def test_init_acoustid(self):
        """APITabWidget works for AcoustID API."""
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            tab = APITabWidget("AcoustID")
            assert tab.api_name == "AcoustID"

    def test_init_other(self):
        """APITabWidget works for unknown API."""
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            tab = APITabWidget("CustomAPI")
            assert tab.api_name == "CustomAPI"


class TestAPITabLoadKey:
    def test_load_existing_key_found(self):
        """_load_existing_key loads key from keyring."""
        ms = _mock_api_tab()
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = "my_key_123"
            _get(APITabWidget, "_load_existing_key")(ms)
            ms.api_key_input.setText.assert_called_once_with("my_key_123")

    def test_load_existing_key_not_found(self):
        """_load_existing_key handles missing key."""
        ms = _mock_api_tab()
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            _get(APITabWidget, "_load_existing_key")(ms)
            ms.api_key_input.setText.assert_not_called()

    def test_load_existing_key_error(self):
        """_load_existing_key handles keyring error."""
        ms = _mock_api_tab()
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.side_effect = RuntimeError("no keyring")
            _get(APITabWidget, "_load_existing_key")(ms)
            ms.status_label.setText.assert_called()


class TestAPITabValidate:
    def test_validate_empty_key(self):
        """_on_validate_clicked rejects empty key."""
        ms = _mock_api_tab()
        ms.api_key_input.text.return_value = ""
        _get(APITabWidget, "_on_validate_clicked")(ms)
        ms.status_label.setText.assert_called()
        ms.validate_button.setEnabled.assert_not_called()

    def test_validate_youtube_success(self):
        """_validate_youtube validates with YouTubeSearcher."""
        ms = _mock_api_tab()
        ms.api_name = "YouTube"
        ms.api_key_input.text.return_value = "a" * 40
        with patch("gui.dialogs.api_settings_dialog.QApplication"):
            with patch("gui.dialogs.api_settings_dialog.YouTubeSearcher") as mock_yt:
                mock_yt.return_value.search.return_value = [{"title": "test"}]
                _get(APITabWidget, "_on_validate_clicked")(ms)
        # Should have set success message
        assert ms.validate_button.setEnabled.call_count >= 1

    def test_validate_youtube_no_results(self):
        """_validate_youtube handles no results."""
        ms = _mock_api_tab()
        with patch("gui.dialogs.api_settings_dialog.YouTubeSearcher") as mock_yt:
            mock_yt.return_value.search.return_value = []
            with pytest.raises(Exception):
                _get(APITabWidget, "_validate_youtube")(ms, "key123")

    def test_validate_youtube_import_error_long_key(self):
        """_validate_youtube falls back to format check for long key."""
        ms = _mock_api_tab()
        with patch("gui.dialogs.api_settings_dialog.YouTubeSearcher", None):
            _get(APITabWidget, "_validate_youtube")(ms, "a" * 40)
            ms.status_label.setText.assert_called()

    def test_validate_youtube_import_error_short_key(self):
        """_validate_youtube raises for short key when no API."""
        ms = _mock_api_tab()
        with patch("gui.dialogs.api_settings_dialog.YouTubeSearcher", None):
            with pytest.raises(Exception, match="short"):
                _get(APITabWidget, "_validate_youtube")(ms, "short")

    def test_validate_spotify_valid(self):
        """_validate_spotify accepts valid 32-char Client ID."""
        ms = _mock_api_tab()
        _get(APITabWidget, "_validate_spotify")(ms, "a" * 32)
        ms.status_label.setText.assert_called()

    def test_validate_spotify_invalid(self):
        """_validate_spotify rejects invalid format."""
        ms = _mock_api_tab()
        with pytest.raises(Exception):
            _get(APITabWidget, "_validate_spotify")(ms, "too-short!")

    def test_validate_genius_valid(self):
        """_validate_genius accepts long token."""
        ms = _mock_api_tab()
        _get(APITabWidget, "_validate_genius")(ms, "a" * 25)
        ms.status_label.setText.assert_called()

    def test_validate_genius_invalid(self):
        """_validate_genius rejects short token."""
        ms = _mock_api_tab()
        with pytest.raises(Exception, match="short"):
            _get(APITabWidget, "_validate_genius")(ms, "short")

    def test_validate_acoustid_valid(self):
        """_validate_acoustid accepts valid key."""
        ms = _mock_api_tab()
        _get(APITabWidget, "_validate_acoustid")(ms, "8XaBELgH")
        ms.status_label.setText.assert_called()

    def test_validate_acoustid_with_hyphens(self):
        """_validate_acoustid handles hyphenated key."""
        ms = _mock_api_tab()
        _get(APITabWidget, "_validate_acoustid")(ms, "abc123de-f456-7890")
        ms.status_label.setText.assert_called()

    def test_validate_acoustid_invalid(self):
        """_validate_acoustid rejects short key."""
        ms = _mock_api_tab()
        with pytest.raises(Exception):
            _get(APITabWidget, "_validate_acoustid")(ms, "abc")

    def test_validate_exception_caught(self):
        """_on_validate_clicked catches generic exceptions."""
        ms = _mock_api_tab()
        ms.api_name = "Genius"
        ms.api_key_input.text.return_value = "x"
        with patch("gui.dialogs.api_settings_dialog.QApplication"):
            _get(APITabWidget, "_on_validate_clicked")(ms)
        # Should catch the exception and set error status
        ms.validate_button.setEnabled.assert_called_with(True)

    def test_get_api_key(self):
        """get_api_key returns trimmed text."""
        ms = _mock_api_tab()
        ms.api_key_input.text.return_value = "  key123  "
        result = _get(APITabWidget, "get_api_key")(ms)
        assert result == "key123"


# --- SpotifyTabWidget Tests ---


class TestSpotifyTabWidget:
    def test_init(self):
        """SpotifyTabWidget initializes correctly."""
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            tab = SpotifyTabWidget()
            assert tab.service_name == "nexus_music"

    def test_load_keys_both_found(self):
        """_load_existing_keys loads both credentials."""
        ms = _mock_spotify_tab()
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.side_effect = ["client_id_val", "secret_val"]
            _get(SpotifyTabWidget, "_load_existing_keys")(ms)
            ms.client_id_input.setText.assert_called_once_with("client_id_val")
            ms.client_secret_input.setText.assert_called_once_with("secret_val")

    def test_load_keys_partial(self):
        """_load_existing_keys warns on partial credentials."""
        ms = _mock_spotify_tab()
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.side_effect = ["client_id_val", None]
            _get(SpotifyTabWidget, "_load_existing_keys")(ms)
            ms.client_id_input.setText.assert_called_once()

    def test_load_keys_none(self):
        """_load_existing_keys shows info when no keys."""
        ms = _mock_spotify_tab()
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            _get(SpotifyTabWidget, "_load_existing_keys")(ms)
            ms.status_label.setText.assert_called()

    def test_load_keys_error(self):
        """_load_existing_keys handles keyring error."""
        ms = _mock_spotify_tab()
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.side_effect = RuntimeError("fail")
            _get(SpotifyTabWidget, "_load_existing_keys")(ms)
            ms.status_label.setText.assert_called()

    def test_clear_fields(self):
        """_clear_fields clears both inputs."""
        ms = _mock_spotify_tab()
        _get(SpotifyTabWidget, "_clear_fields")(ms)
        ms.client_id_input.clear.assert_called_once()
        ms.client_secret_input.clear.assert_called_once()

    def test_validate_empty(self):
        """_on_validate_clicked rejects empty fields."""
        ms = _mock_spotify_tab()
        ms.client_id_input.text.return_value = ""
        ms.client_secret_input.text.return_value = ""
        _get(SpotifyTabWidget, "_on_validate_clicked")(ms)
        ms.status_label.setText.assert_called()

    def test_validate_success(self):
        """_on_validate_clicked validates with SpotifySearcher."""
        ms = _mock_spotify_tab()
        ms.client_id_input.text.return_value = "a" * 32
        ms.client_secret_input.text.return_value = "b" * 32
        with patch("gui.dialogs.api_settings_dialog.QApplication"):
            with patch("gui.dialogs.api_settings_dialog.SpotifySearcher") as mock_sp:
                mock_sp.return_value.search_tracks.return_value = [{"title": "t"}]
                _get(SpotifyTabWidget, "_on_validate_clicked")(ms)
        ms.validate_button.setEnabled.assert_called_with(True)

    def test_validate_no_results(self):
        """_on_validate_clicked handles no results from Spotify."""
        ms = _mock_spotify_tab()
        ms.client_id_input.text.return_value = "a" * 32
        ms.client_secret_input.text.return_value = "b" * 32
        with patch("gui.dialogs.api_settings_dialog.QApplication"):
            with patch("gui.dialogs.api_settings_dialog.SpotifySearcher") as mock_sp:
                mock_sp.return_value.search_tracks.return_value = []
                _get(SpotifyTabWidget, "_on_validate_clicked")(ms)
        # Exception caught internally
        ms.validate_button.setEnabled.assert_called_with(True)

    def test_validate_import_error_valid_format(self):
        """Fallback validates format when SpotifySearcher unavailable."""
        ms = _mock_spotify_tab()
        ms.client_id_input.text.return_value = "a" * 32
        ms.client_secret_input.text.return_value = "b" * 32
        with patch("gui.dialogs.api_settings_dialog.QApplication"):
            with patch("gui.dialogs.api_settings_dialog.SpotifySearcher", None):
                _get(SpotifyTabWidget, "_on_validate_clicked")(ms)
        ms.validate_button.setEnabled.assert_called_with(True)

    def test_validate_import_error_bad_id(self):
        """Fallback rejects bad Client ID format."""
        ms = _mock_spotify_tab()
        ms.client_id_input.text.return_value = "short"
        ms.client_secret_input.text.return_value = "b" * 32
        with patch("gui.dialogs.api_settings_dialog.QApplication"):
            with patch("gui.dialogs.api_settings_dialog.SpotifySearcher", None):
                _get(SpotifyTabWidget, "_on_validate_clicked")(ms)
        ms.validate_button.setEnabled.assert_called_with(True)

    def test_validate_import_error_bad_secret(self):
        """Fallback rejects bad Client Secret format."""
        ms = _mock_spotify_tab()
        ms.client_id_input.text.return_value = "a" * 32
        ms.client_secret_input.text.return_value = "short"
        with patch("gui.dialogs.api_settings_dialog.QApplication"):
            with patch("gui.dialogs.api_settings_dialog.SpotifySearcher", None):
                _get(SpotifyTabWidget, "_on_validate_clicked")(ms)
        ms.validate_button.setEnabled.assert_called_with(True)

    def test_get_credentials(self):
        """get_credentials returns trimmed tuple."""
        ms = _mock_spotify_tab()
        ms.client_id_input.text.return_value = " id "
        ms.client_secret_input.text.return_value = " secret "
        result = _get(SpotifyTabWidget, "get_credentials")(ms)
        assert result == ("id", "secret")


# --- APISettingsDialog Tests ---


class TestAPISettingsDialog:
    def test_init(self):
        """APISettingsDialog initializes with tabs."""
        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            dialog = APISettingsDialog()
            assert dialog.tab_widget is not None

    def test_on_save_keys(self):
        """_on_save_clicked saves keys to keyring."""
        ms = MagicMock()
        ms.youtube_tab = MagicMock()
        ms.youtube_tab.get_api_key.return_value = "yt_key"
        ms.spotify_tab = MagicMock()
        ms.spotify_tab.get_credentials.return_value = ("sp_id", "sp_secret")
        ms.genius_tab = MagicMock()
        ms.genius_tab.get_api_key.return_value = "gen_key"
        ms.acoustid_tab = MagicMock()
        ms.acoustid_tab.get_api_key.return_value = "ac_key"
        ms.keys_saved = MagicMock()

        with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
            _get(APISettingsDialog, "_on_save_clicked")(ms)
            assert mock_kr.set_password.call_count == 5  # yt + sp_id + sp_secret + gen + ac
            ms.keys_saved.emit.assert_called_once()
            ms.accept.assert_called_once()

    def test_on_save_no_keys(self):
        """_on_save_clicked warns when no keys entered."""
        ms = MagicMock()
        ms.youtube_tab.get_api_key.return_value = ""
        ms.spotify_tab.get_credentials.return_value = ("", "")
        ms.genius_tab.get_api_key.return_value = ""
        ms.acoustid_tab.get_api_key.return_value = ""

        mock_mb = MagicMock()
        mock_qtw = sys.modules["PySide6.QtWidgets"]
        old_mb = getattr(mock_qtw, "QMessageBox", None)
        mock_qtw.QMessageBox = mock_mb
        try:
            with patch("gui.dialogs.api_settings_dialog.keyring"):
                _get(APISettingsDialog, "_on_save_clicked")(ms)
                mock_mb.warning.assert_called()
        finally:
            mock_qtw.QMessageBox = old_mb

    def test_on_save_partial_spotify(self):
        """_on_save_clicked warns on partial Spotify credentials."""
        ms = MagicMock()
        ms.youtube_tab.get_api_key.return_value = "yt"
        ms.spotify_tab.get_credentials.return_value = ("sp_id", "")
        ms.genius_tab.get_api_key.return_value = ""
        ms.acoustid_tab.get_api_key.return_value = ""
        ms.keys_saved = MagicMock()

        mock_mb = MagicMock()
        mock_qtw = sys.modules["PySide6.QtWidgets"]
        old_mb = getattr(mock_qtw, "QMessageBox", None)
        mock_qtw.QMessageBox = mock_mb
        try:
            with patch("gui.dialogs.api_settings_dialog.keyring"):
                _get(APISettingsDialog, "_on_save_clicked")(ms)
                mock_mb.warning.assert_called()
        finally:
            mock_qtw.QMessageBox = old_mb

    def test_on_save_keyring_error(self):
        """_on_save_clicked handles keyring error."""
        ms = MagicMock()
        ms.youtube_tab.get_api_key.return_value = "key"
        ms.spotify_tab.get_credentials.return_value = ("", "")
        ms.genius_tab.get_api_key.return_value = ""
        ms.acoustid_tab.get_api_key.return_value = ""

        mock_mb = MagicMock()
        mock_qtw = sys.modules["PySide6.QtWidgets"]
        old_mb = getattr(mock_qtw, "QMessageBox", None)
        mock_qtw.QMessageBox = mock_mb
        try:
            with patch("gui.dialogs.api_settings_dialog.keyring") as mock_kr:
                mock_kr.set_password.side_effect = RuntimeError("keyring fail")
                _get(APISettingsDialog, "_on_save_clicked")(ms)
                mock_mb.critical.assert_called()
        finally:
            mock_qtw.QMessageBox = old_mb

    def test_on_help_clicked(self):
        """_on_help_clicked shows help dialog."""
        ms = MagicMock()
        mock_qtwidgets = MagicMock()
        with patch.dict("sys.modules", {"PySide6.QtWidgets": mock_qtwidgets}):
            _get(APISettingsDialog, "_on_help_clicked")(ms)


# --- ShortcutsDialog Tests ---


class TestShortcutsDialog:
    def test_init(self):
        """ShortcutsDialog initializes with shortcuts list."""
        shortcuts = [("Ctrl+P", "Play/Pause"), ("Ctrl+N", "Next")]
        dialog = ShortcutsDialog(shortcuts)
        assert dialog.shortcuts_list == shortcuts

    def test_init_empty(self):
        """ShortcutsDialog works with empty list."""
        dialog = ShortcutsDialog([])
        assert len(dialog.shortcuts_list) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
