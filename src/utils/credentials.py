"""
Centralized credential loading utility.

Provides a single entry point for loading API credentials with a 4-tier
fallback strategy:
    1. OS Keyring (most secure — production)
    2. Environment variables
    3. .env file (via python-dotenv)
    4. credentials.json (development fallback)

Usage::

    from utils.credentials import load_credential, load_all_credentials

    # Single credential
    youtube_key = load_credential("youtube_api_key", env_var="YOUTUBE_API_KEY")

    # All credentials at once
    creds = load_all_credentials()
    spotify_id = creds.get("spotify_client_id")
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Service name used in OS keyring
KEYRING_SERVICE = "nexus_music"

# Mapping: credential_name -> (keyring_key, env_var, credentials.json path)
_CREDENTIAL_MAP: Dict[str, Dict[str, Any]] = {
    "youtube_api_key": {
        "keyring_key": "youtube_api_key",
        "env_var": "YOUTUBE_API_KEY",
        "json_path": ("apis", "youtube", "api_key"),
    },
    "spotify_client_id": {
        "keyring_key": "spotify_client_id",
        "env_var": "SPOTIFY_CLIENT_ID",
        "json_path": ("apis", "spotify", "client_id"),
    },
    "spotify_client_secret": {
        "keyring_key": "spotify_client_secret",
        "env_var": "SPOTIFY_CLIENT_SECRET",
        "json_path": ("apis", "spotify", "client_secret"),
    },
    "genius_token": {
        "keyring_key": "genius_token",
        "env_var": "GENIUS_ACCESS_TOKEN",
        "json_path": ("apis", "genius", "api_key"),
    },
    "acoustid_api_key": {
        "keyring_key": "acoustid_api_key",
        "env_var": "ACOUSTID_API_KEY",
        "json_path": ("apis", "acoustid", "api_key"),
    },
}

# Cached credentials.json content (loaded once)
_json_cache: Optional[Dict[str, Any]] = None
_dotenv_loaded: bool = False


def _load_from_keyring(key: str) -> Optional[str]:
    """Try to load a credential from OS keyring."""
    try:
        import keyring as kr

        value = kr.get_password(KEYRING_SERVICE, key)
        if value:
            return value
    except (ImportError, RuntimeError, Exception):  # keyring may not be available
        pass
    return None


def _load_from_env(env_var: str) -> Optional[str]:
    """Try to load a credential from environment variable."""
    return os.environ.get(env_var) or None


def _ensure_dotenv() -> None:
    """Load .env file once if python-dotenv is available."""
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True
    try:
        from dotenv import load_dotenv

        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug("Loaded .env file")
    except ImportError:
        pass


def _load_from_json(json_path: tuple[str, ...]) -> Optional[str]:
    """Try to load a credential from credentials.json."""
    global _json_cache
    if _json_cache is None:
        creds_file = os.getenv("CREDENTIALS_PATH") or str(Path.home() / ".claude" / "secrets" / "credentials.json")
        try:
            with open(creds_file) as f:
                _json_cache = json.load(f)
            logger.debug(f"Loaded credentials from {creds_file}")
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            _json_cache = {}

    # Navigate nested dict
    node: Any = _json_cache
    for key in json_path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node if isinstance(node, str) else None


def load_credential(
    name: str,
    *,
    keyring_key: Optional[str] = None,
    env_var: Optional[str] = None,
    json_path: Optional[tuple[str, ...]] = None,
) -> Optional[str]:
    """Load a single API credential using the 4-tier fallback strategy.

    If ``name`` is a known credential (in _CREDENTIAL_MAP), its defaults
    are used automatically.  Override any tier with explicit keyword args.

    Args:
        name: Credential name (e.g. "youtube_api_key").
        keyring_key: Override keyring key name.
        env_var: Override environment variable name.
        json_path: Override JSON path tuple.

    Returns:
        The credential string, or None if not found.
    """
    defaults = _CREDENTIAL_MAP.get(name, {})
    kr_key = keyring_key or defaults.get("keyring_key", name)
    ev = env_var or defaults.get("env_var")
    jp = json_path or defaults.get("json_path")

    # 1. Keyring
    value = _load_from_keyring(kr_key)
    if value:
        return value

    # 2. Environment variable
    if ev:
        value = _load_from_env(ev)
        if value:
            return value

    # 3. .env file (loads into os.environ, then re-check)
    _ensure_dotenv()
    if ev:
        value = _load_from_env(ev)
        if value:
            return value

    # 4. credentials.json
    if jp:
        value = _load_from_json(jp)
        if value:
            return value

    return None


def load_all_credentials() -> Dict[str, Optional[str]]:
    """Load all known credentials at once.

    Returns:
        Dict mapping credential name to value (or None if not found).
    """
    return {name: load_credential(name) for name in _CREDENTIAL_MAP}
