"""
Tests for utils/credentials.py — 4-tier credential loading.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import utils.credentials as creds_module
from utils.credentials import (
    KEYRING_SERVICE,
    _load_from_env,
    _load_from_json,
    _load_from_keyring,
    load_all_credentials,
    load_credential,
)


@pytest.fixture(autouse=True)
def _reset_caches():
    """Reset module-level caches between tests."""
    creds_module._json_cache = None
    creds_module._dotenv_loaded = False
    yield
    creds_module._json_cache = None
    creds_module._dotenv_loaded = False


class TestLoadFromKeyring:
    def test_returns_value_when_keyring_has_credential(self):
        mock_kr = MagicMock()
        mock_kr.get_password.return_value = "my-api-key"
        with patch.dict("sys.modules", {"keyring": mock_kr}):
            result = _load_from_keyring("youtube_api_key")
        assert result == "my-api-key"

    def test_returns_none_when_keyring_empty(self):
        mock_kr = MagicMock()
        mock_kr.get_password.return_value = None
        with patch.dict("sys.modules", {"keyring": mock_kr}):
            result = _load_from_keyring("youtube_api_key")
        assert result is None

    def test_returns_none_when_keyring_raises(self):
        """Keyring can raise RuntimeError or other errors at runtime."""
        mock_kr = MagicMock()
        mock_kr.get_password.side_effect = RuntimeError("No backend")
        with patch.dict("sys.modules", {"keyring": mock_kr}):
            result = _load_from_keyring("youtube_api_key")
        assert result is None


class TestLoadFromEnv:
    def test_returns_env_value(self):
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": "env-key-123"}):
            result = _load_from_env("YOUTUBE_API_KEY")
        assert result == "env-key-123"

    def test_returns_none_when_not_set(self):
        result = _load_from_env("NONEXISTENT_VAR_12345")
        assert result is None

    def test_returns_none_for_empty_string(self):
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            result = _load_from_env("EMPTY_VAR")
        assert result is None


class TestLoadFromJson:
    def test_loads_nested_value(self):
        creds_module._json_cache = {"apis": {"youtube": {"api_key": "json-key-456"}}}
        result = _load_from_json(("apis", "youtube", "api_key"))
        assert result == "json-key-456"

    def test_returns_none_for_missing_path(self):
        creds_module._json_cache = {"apis": {}}
        result = _load_from_json(("apis", "youtube", "api_key"))
        assert result is None

    def test_returns_none_for_non_string_value(self):
        creds_module._json_cache = {"apis": {"youtube": {"api_key": 12345}}}
        result = _load_from_json(("apis", "youtube", "api_key"))
        assert result is None

    def test_loads_from_file_on_first_call(self, tmp_path):
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"apis": {"genius": {"api_key": "genius-token"}}}))

        with patch.dict(os.environ, {"CREDENTIALS_PATH": str(creds_file)}):
            creds_module._json_cache = None
            result = _load_from_json(("apis", "genius", "api_key"))

        assert result == "genius-token"

    def test_handles_missing_file(self):
        with patch.dict(os.environ, {"CREDENTIALS_PATH": "/nonexistent/path.json"}):
            creds_module._json_cache = None
            result = _load_from_json(("apis", "youtube", "api_key"))
        assert result is None


class TestLoadCredential:
    def test_known_credential_uses_defaults(self):
        with patch("utils.credentials._load_from_keyring", return_value="kr-value"):
            result = load_credential("youtube_api_key")
        assert result == "kr-value"

    def test_falls_through_tiers(self):
        with (
            patch("utils.credentials._load_from_keyring", return_value=None),
            patch.dict(os.environ, {"YOUTUBE_API_KEY": "env-value"}),
        ):
            result = load_credential("youtube_api_key")
        assert result == "env-value"

    def test_returns_none_when_all_tiers_fail(self):
        with (
            patch("utils.credentials._load_from_keyring", return_value=None),
            patch("utils.credentials._load_from_json", return_value=None),
            patch("utils.credentials._ensure_dotenv"),
        ):
            result = load_credential("youtube_api_key")
        assert result is None

    def test_custom_overrides(self):
        with patch.dict(os.environ, {"CUSTOM_VAR": "custom-value"}):
            with patch("utils.credentials._load_from_keyring", return_value=None):
                result = load_credential(
                    "unknown_cred",
                    env_var="CUSTOM_VAR",
                )
        assert result == "custom-value"


class TestLoadAllCredentials:
    def test_returns_dict_with_all_known_keys(self):
        with patch("utils.credentials.load_credential", return_value=None) as mock_lc:
            result = load_all_credentials()

        assert "youtube_api_key" in result
        assert "spotify_client_id" in result
        assert "spotify_client_secret" in result
        assert "genius_token" in result
        assert "acoustid_api_key" in result
        assert mock_lc.call_count == 5
