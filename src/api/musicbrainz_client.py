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
import musicbrainzngs
import requests
import logging
import time
from typing import List, Dict, Optional
from pathlib import Path

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

    def __init__(self, app_name="NexusMusicManager", app_version="1.0", contact=""):
        """
        Initialize MusicBrainz client

        Args:
            app_name (str): Application name for user agent
            app_version (str): Application version
            contact (str): Contact email (optional)
        """
        self.app_name = app_name
        self.app_version = app_version
        self.contact = contact

        # Set user agent (required by MusicBrainz)
        musicbrainzngs.set_useragent(app_name, app_version, contact)

        # Rate limiting (MusicBrainz allows 1 request/second)
        self._last_request_time = 0
        self._rate_limiter = True

        logger.info(f"MusicBrainzClient initialized: {app_name} v{app_version}")

    def search_recording(self, title: str, artist: Optional[str] = None, limit: int = 5) -> List[Dict]:
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
            result = musicbrainzngs.search_recordings(
                query=query,
                limit=min(limit, 5)  # Limit to max 5
            )

            # Parse results
            recordings = self._parse_recordings(result)

            # Ensure max 5 results
            recordings = recordings[:limit]

            logger.info(f"Search '{title}' returned {len(recordings)} results")
            return recordings

        except Exception as e:
            logger.error(f"MusicBrainz search error: {e}")
            return []

    def download_album_art(self, url: str, output_path: str) -> bool:
        """
        Download album art from URL

        Args:
            url (str): Image URL
            output_path (str): Local path to save image

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Download image
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                # Save to file
                with open(output_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"Album art downloaded: {output_path}")
                return True
            else:
                logger.warning(f"Failed to download album art: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error downloading album art: {e}")
            return False

    def _parse_recordings(self, result: dict) -> List[Dict]:
        """
        Parse MusicBrainz recording search results

        Args:
            result (dict): Raw MusicBrainz API response

        Returns:
            list: Parsed recordings
        """
        recordings = []

        if 'recording-list' not in result:
            return recordings

        for item in result['recording-list']:
            try:
                # Extract artist
                artist = "Unknown"
                if 'artist-credit' in item and item['artist-credit']:
                    artist = item['artist-credit'][0]['artist']['name']

                # Extract album and year
                album = "Unknown"
                year = "Unknown"
                if 'release-list' in item and item['release-list']:
                    release = item['release-list'][0]
                    album = release.get('title', 'Unknown')
                    year = release.get('date', 'Unknown')[:4]  # Extract year only

                # Extract genre from tags
                genre = self._extract_genre(item.get('tag-list', []))

                # Build recording dict
                recording = {
                    'title': item['title'],
                    'artist': artist,
                    'album': album,
                    'year': year,
                    'genre': genre
                }

                recordings.append(recording)

            except KeyError as e:
                logger.warning(f"Missing key in MusicBrainz result: {e}")
                continue

        return recordings

    def _extract_genre(self, tag_list: List[Dict]) -> str:
        """
        Extract most popular genre from tag list

        Args:
            tag_list (list): MusicBrainz tag list

        Returns:
            str: Genre name or "Unknown"
        """
        if not tag_list:
            return "Unknown"

        # Sort by count (most popular first)
        sorted_tags = sorted(tag_list, key=lambda x: x.get('count', 0), reverse=True)

        # Return most popular genre
        if sorted_tags:
            return sorted_tags[0]['name']

        return "Unknown"

    def _enforce_rate_limit(self):
        """
        Enforce rate limit (1 request/second for MusicBrainz)
        """
        if not self._rate_limiter:
            return

        # Calculate time since last request
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        # If less than 1 second, wait
        if time_since_last < 1.0:
            wait_time = 1.0 - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)

        # Update last request time
        self._last_request_time = time.time()
