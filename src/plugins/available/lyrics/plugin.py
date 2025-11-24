"""
Lyrics Plugin for NEXUS Music Manager
Fetches and displays song lyrics from multiple sources

Requirements:
    pip install lyricsgenius beautifulsoup4 requests

Features:
- Fetch lyrics from Genius API
- Fallback to web scraping (AZLyrics)
- Cache lyrics locally
- Display synchronized lyrics (if available)
- Save lyrics to file alongside MP3

Created: November 24, 2025
"""

import logging
import json
import hashlib
import re
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from plugins.plugin_base import Plugin, PluginMetadata, PluginHook

logger = logging.getLogger(__name__)

# Check for dependencies
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import lyricsgenius
    HAS_GENIUS = True
except ImportError:
    HAS_GENIUS = False


@dataclass
class LyricsResult:
    """Result from lyrics search"""
    title: str
    artist: str
    lyrics: str
    source: str
    url: Optional[str] = None
    synced: bool = False


class LyricsPlugin(Plugin):
    """
    Lyrics Plugin

    Automatically fetches lyrics when a song plays.
    Supports Genius API and web scraping fallbacks.
    """

    def __init__(self):
        super().__init__()

        self._cache_dir: Optional[Path] = None
        self._genius_client = None
        self._current_lyrics: Optional[LyricsResult] = None
        self._fetch_thread: Optional[threading.Thread] = None
        self._lyrics_callbacks: List[callable] = []

    # Settings schema (used by GUI)
    SETTINGS_SCHEMA = {
        "genius_api_key": {
            "type": "string",
            "label": "Genius API Key",
            "description": "API key from genius.com/developers (optional)",
            "default": "",
            "secret": True
        },
        "auto_fetch": {
            "type": "bool",
            "label": "Auto-Fetch Lyrics",
            "description": "Automatically fetch lyrics when song plays",
            "default": True
        },
        "save_to_file": {
            "type": "bool",
            "label": "Save Lyrics to File",
            "description": "Save .lrc file alongside MP3",
            "default": False
        },
        "cache_lyrics": {
            "type": "bool",
            "label": "Cache Lyrics",
            "description": "Cache lyrics locally for faster access",
            "default": True
        }
    }

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="lyrics",
            display_name="Lyrics",
            version="1.0.0",
            author="NEXUS Team",
            description="Fetch and display song lyrics",
            dependencies=[],
            hooks=[PluginHook.ON_SONG_PLAY]
        )

    def on_enable(self) -> bool:
        """Enable plugin"""
        if not HAS_REQUESTS:
            logger.error("Cannot enable Lyrics: requests not installed")
            return False

        # Setup cache directory
        self._cache_dir = Path.home() / ".nexus_music" / "lyrics_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Genius client if API key provided
        api_key = self.get_setting("genius_api_key", "")
        if api_key and HAS_GENIUS:
            try:
                self._genius_client = lyricsgenius.Genius(api_key, verbose=False)
                self._genius_client.remove_section_headers = True
                logger.info("Genius API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Genius client: {e}")

        # Register hooks
        self.register_hook(PluginHook.ON_SONG_PLAY, self._on_song_play)

        logger.info("Lyrics plugin enabled")
        return True

    def on_disable(self) -> bool:
        """Disable plugin"""
        if self._fetch_thread and self._fetch_thread.is_alive():
            self._fetch_thread.join(timeout=2)

        self._genius_client = None
        logger.info("Lyrics plugin disabled")
        return True

    def register_lyrics_callback(self, callback: callable):
        """Register callback for when lyrics are fetched"""
        self._lyrics_callbacks.append(callback)

    def _on_song_play(self, song_data: Dict[str, Any]):
        """Handle song play event"""
        if not self.get_setting("auto_fetch", True):
            return

        title = song_data.get('title', '')
        artist = song_data.get('artist', '')

        if not title:
            return

        # Fetch lyrics in background thread
        self._fetch_thread = threading.Thread(
            target=self._fetch_lyrics_async,
            args=(title, artist, song_data.get('file_path')),
            daemon=True,
            name="Lyrics-Fetch"
        )
        self._fetch_thread.start()

    def _fetch_lyrics_async(self, title: str, artist: str, file_path: str = None):
        """Fetch lyrics asynchronously"""
        try:
            result = self.fetch_lyrics(title, artist)

            if result:
                self._current_lyrics = result
                logger.info(f"Lyrics found for: {title} - {artist}")

                # Save to file if enabled
                if self.get_setting("save_to_file", False) and file_path:
                    self._save_lyrics_file(result, file_path)

                # Notify callbacks
                for callback in self._lyrics_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"Lyrics callback error: {e}")
            else:
                logger.debug(f"No lyrics found for: {title} - {artist}")

        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")

    def fetch_lyrics(self, title: str, artist: str) -> Optional[LyricsResult]:
        """
        Fetch lyrics for a song

        Args:
            title: Song title
            artist: Artist name

        Returns:
            LyricsResult if found, None otherwise
        """
        # Check cache first
        if self.get_setting("cache_lyrics", True):
            cached = self._get_cached_lyrics(title, artist)
            if cached:
                return cached

        result = None

        # Try Genius API first
        if self._genius_client:
            result = self._fetch_from_genius(title, artist)

        # Fallback to web scraping
        if not result and HAS_BS4:
            result = self._fetch_from_azlyrics(title, artist)

        # Cache result
        if result and self.get_setting("cache_lyrics", True):
            self._cache_lyrics(result)

        return result

    def _fetch_from_genius(self, title: str, artist: str) -> Optional[LyricsResult]:
        """Fetch lyrics from Genius API"""
        if not self._genius_client:
            return None

        try:
            song = self._genius_client.search_song(title, artist)
            if song and song.lyrics:
                # Clean up lyrics
                lyrics = song.lyrics
                # Remove [Verse], [Chorus] etc if configured
                lyrics = re.sub(r'\[.*?\]', '', lyrics).strip()

                return LyricsResult(
                    title=song.title,
                    artist=song.artist,
                    lyrics=lyrics,
                    source="Genius",
                    url=song.url
                )
        except Exception as e:
            logger.debug(f"Genius API error: {e}")

        return None

    def _fetch_from_azlyrics(self, title: str, artist: str) -> Optional[LyricsResult]:
        """Fetch lyrics from AZLyrics (scraping)"""
        if not HAS_BS4 or not HAS_REQUESTS:
            return None

        try:
            # Format artist and title for URL
            artist_clean = re.sub(r'[^a-z0-9]', '', artist.lower())
            title_clean = re.sub(r'[^a-z0-9]', '', title.lower())

            url = f"https://www.azlyrics.com/lyrics/{artist_clean}/{title_clean}.html"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find lyrics div (AZLyrics structure)
                lyrics_div = soup.find('div', class_=None, id=None)
                if lyrics_div:
                    # Look for the specific lyrics container
                    for div in soup.find_all('div'):
                        if div.get('class') is None and div.get('id') is None:
                            text = div.get_text().strip()
                            if len(text) > 100:  # Likely lyrics
                                return LyricsResult(
                                    title=title,
                                    artist=artist,
                                    lyrics=text,
                                    source="AZLyrics",
                                    url=url
                                )

        except requests.RequestException as e:
            logger.debug(f"AZLyrics request error: {e}")
        except Exception as e:
            logger.debug(f"AZLyrics parse error: {e}")

        return None

    def _get_cache_key(self, title: str, artist: str) -> str:
        """Generate cache key for lyrics"""
        key_str = f"{title.lower()}|{artist.lower()}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cached_lyrics(self, title: str, artist: str) -> Optional[LyricsResult]:
        """Get lyrics from cache"""
        if not self._cache_dir:
            return None

        cache_key = self._get_cache_key(title, artist)
        cache_file = self._cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding='utf-8'))
                return LyricsResult(**data)
            except Exception as e:
                logger.debug(f"Cache read error: {e}")

        return None

    def _cache_lyrics(self, result: LyricsResult):
        """Cache lyrics result"""
        if not self._cache_dir:
            return

        cache_key = self._get_cache_key(result.title, result.artist)
        cache_file = self._cache_dir / f"{cache_key}.json"

        try:
            data = {
                'title': result.title,
                'artist': result.artist,
                'lyrics': result.lyrics,
                'source': result.source,
                'url': result.url,
                'synced': result.synced
            }
            cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        except Exception as e:
            logger.debug(f"Cache write error: {e}")

    def _save_lyrics_file(self, result: LyricsResult, mp3_path: str):
        """Save lyrics to .lrc file alongside MP3"""
        try:
            mp3_path = Path(mp3_path)
            lrc_path = mp3_path.with_suffix('.lrc')

            # Simple LRC format (unsynchronized)
            content = f"[ti:{result.title}]\n"
            content += f"[ar:{result.artist}]\n"
            content += f"[by:NEXUS Music Manager]\n"
            content += f"[re:Lyrics from {result.source}]\n\n"
            content += result.lyrics

            lrc_path.write_text(content, encoding='utf-8')
            logger.debug(f"Saved lyrics to: {lrc_path}")

        except Exception as e:
            logger.error(f"Failed to save lyrics file: {e}")

    def get_current_lyrics(self) -> Optional[LyricsResult]:
        """Get lyrics for currently playing song"""
        return self._current_lyrics

    def search_lyrics(self, title: str, artist: str = "") -> Optional[LyricsResult]:
        """
        Manual lyrics search

        Args:
            title: Song title
            artist: Artist name (optional)

        Returns:
            LyricsResult if found
        """
        return self.fetch_lyrics(title, artist)


# Export plugin class
__plugin_class__ = LyricsPlugin
