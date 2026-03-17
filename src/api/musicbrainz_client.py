"""
MusicBrainz Client - Phase 4.3
Interface to MusicBrainz API for metadata search and album art downloads

Features:
- Recording search with fuzzy matching
- Genre extraction from tags
- Album art downloads
- Rate limiting (1 request/second)
- User agent configuration
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import musicbrainzngs
import requests  # type: ignore[import-untyped]

from utils.constants import API_DEFAULT_TIMEOUT, DEFAULT_ALBUM, DEFAULT_ARTIST, DEFAULT_GENRE
from utils.rate_limiter import RateLimiter

# Allowed domains for album art downloads (SSRF prevention)
_ALLOWED_ART_DOMAINS = {"coverartarchive.org", "archive.org", "musicbrainz.org", "i.scdn.co", "is1-ssl.mzstatic.com"}

# Setup logger
logger = logging.getLogger(__name__)


class MusicBrainzClient:
    """
    MusicBrainz API client for music metadata search

    Usage:
        client = MusicBrainzClient(app_name="NexusMusicManager", app_version="1.0")
        results = client.search_recording("Bohemian Rhapsody", artist="Queen")
        client.download_album_art(url, "cover.jpg")
    """

    def __init__(self, app_name: str = "NexusMusicManager", app_version: str = "1.0", contact: str = "") -> None:
        """
        Initialize MusicBrainz client

        Args:
            app_name (str): Application name for user agent
            app_version (str): Application version
            contact (str): Contact email (optional)
        """
        self.app_name: str = app_name
        self.app_version: str = app_version
        self.contact: str = contact

        # Set user agent (required by MusicBrainz)
        musicbrainzngs.set_useragent(app_name, app_version, contact)

        # Rate limiting (MusicBrainz allows 1 request/second)
        self._rate_limiter: bool = True

        logger.info(f"MusicBrainzClient initialized: {app_name} v{app_version}")

    def search_recording(self, title: str, artist: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for recordings on MusicBrainz

        Args:
            title (str): Song title
            artist (str): Artist name (optional, improves accuracy)
            limit (int): Maximum results (default: 5)

        Returns:
            list: List of dicts with format:
                  [{'title', 'artist', 'album', 'year', 'genre'}]

        Examples:
            >>> client.search_recording("Bohemian Rhapsody", artist="Queen")
            [{'title': 'Bohemian Rhapsody', 'artist': 'Queen', ...}]
        """
        # Input validation
        if not title:
            logger.warning("Empty title received")
            return []

        # Enforce rate limit
        self._enforce_rate_limit()

        try:
            # Build query
            if artist:
                query = f'recording:"{title}" AND artist:"{artist}"'
            else:
                query = f'recording:"{title}"'

            # Search MusicBrainz
            result = musicbrainzngs.search_recordings(query=query, limit=min(limit, 5))  # Limit to max 5

            # Parse results
            recordings = self._parse_recordings(result)

            # Ensure max 5 results
            recordings = recordings[:limit]

            logger.info(f"Search '{title}' returned {len(recordings)} results")
            return recordings

        except (musicbrainzngs.WebServiceError, musicbrainzngs.UsageError) as e:
            logger.error(f"MusicBrainz search error: {e}")
            return []

    def download_album_art(self, url: str, output_path: str) -> bool:
        """
        Download album art from URL

        Args:
            url (str): Image URL (must be from allowed domains)
            output_path (str): Local path to save image (must have image extension)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate URL domain (SSRF prevention)
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                logger.warning("Album art URL rejected: invalid scheme")
                return False

            domain = parsed.hostname or ""
            if not any(domain == d or domain.endswith("." + d) for d in _ALLOWED_ART_DOMAINS):
                logger.warning(f"Album art URL rejected: domain not allowed ({domain})")
                return False

            # Validate output path (path traversal prevention)
            out = Path(output_path).resolve()
            if out.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"):
                logger.warning("Album art output rejected: invalid file extension")
                return False

            # Download image
            response = requests.get(url, timeout=API_DEFAULT_TIMEOUT)

            if response.status_code == 200:
                # Validate content-type
                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    logger.warning(f"Album art rejected: unexpected Content-Type ({content_type})")
                    return False

                # Save to file
                out.parent.mkdir(parents=True, exist_ok=True)
                with open(out, "wb") as f:
                    f.write(response.content)

                logger.info("Album art downloaded successfully")
                return True
            else:
                logger.warning(f"Failed to download album art: HTTP {response.status_code}")
                return False

        except (requests.RequestException, OSError) as e:
            logger.error(f"Error downloading album art: {e}")
            return False

    def _parse_recordings(self, result: dict) -> List[Dict[str, Any]]:
        """
        Parse MusicBrainz recording search results

        Args:
            result (dict): Raw MusicBrainz API response

        Returns:
            list: Parsed recordings
        """
        recordings: list[dict[str, Any]] = []

        if "recording-list" not in result:
            return recordings

        for item in result["recording-list"]:
            try:
                # Extract artist
                artist = DEFAULT_ARTIST
                if "artist-credit" in item and item["artist-credit"]:
                    artist = item["artist-credit"][0]["artist"]["name"]

                # Extract album and year
                album = DEFAULT_ALBUM
                year = "Unknown"
                if "release-list" in item and item["release-list"]:
                    release = item["release-list"][0]
                    album = release.get("title", DEFAULT_ALBUM)
                    year = release.get("date", "Unknown")[:4]  # Extract year only

                # Extract genre from tags
                genre = self._extract_genre(item.get("tag-list", []))

                # Build recording dict
                recording = {"title": item["title"], "artist": artist, "album": album, "year": year, "genre": genre}

                recordings.append(recording)

            except KeyError as e:
                logger.warning(f"Missing key in MusicBrainz result: {e}")
                continue

        return recordings

    def _extract_genre(self, tag_list: List[Dict[str, Any]]) -> str:
        """
        Extract most popular genre from tag list

        Args:
            tag_list (list): MusicBrainz tag list

        Returns:
            str: Genre name or "Unknown"
        """
        if not tag_list:
            result: str = DEFAULT_GENRE
            return result

        # Sort by count (most popular first), return top genre
        sorted_tags = sorted(tag_list, key=lambda x: x.get("count", 0), reverse=True)
        genre: str = sorted_tags[0]["name"]
        return genre

    def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limit (1 request/second for MusicBrainz)
        Uses centralized RateLimiter for consistent behavior across all APIs
        """
        if not self._rate_limiter:
            return

        # Use centralized rate limiter (MusicBrainz: 1 req/s)
        RateLimiter.get_instance().wait("musicbrainz")
