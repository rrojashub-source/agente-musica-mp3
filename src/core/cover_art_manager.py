"""
Cover Art Manager - Automatic cover art downloading

Purpose: Download and manage album art from Cover Art Archive
Created: November 18, 2025
"""
import requests
import logging
from pathlib import Path
from typing import Optional, Dict
import musicbrainzngs

logger = logging.getLogger(__name__)


class CoverArtManager:
    """
    Manage cover art downloading from Cover Art Archive

    Uses Cover Art Archive API (no API key needed):
    https://coverartarchive.org/
    """

    def __init__(self, cover_art_dir: str = None):
        """
        Initialize cover art manager

        Args:
            cover_art_dir: Directory to save covers (default: downloads/covers/)
        """
        if cover_art_dir:
            self.cover_dir = Path(cover_art_dir)
        else:
            # Default: downloads/covers/
            self.cover_dir = Path("downloads") / "covers"

        # Create directory if doesn't exist
        self.cover_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"CoverArtManager initialized: {self.cover_dir}")

    def get_cover_url(self, artist: str, album: str) -> Optional[str]:
        """
        Get cover art URL from Cover Art Archive

        Args:
            artist: Artist name
            album: Album name

        Returns:
            str or None: URL to front cover image
        """
        try:
            # Search for release
            result = musicbrainzngs.search_releases(
                artist=artist,
                release=album,
                limit=1
            )

            if not result or 'release-list' not in result:
                logger.debug(f"No release found for: {artist} - {album}")
                return None

            releases = result['release-list']
            if not releases:
                return None

            # Get first release ID
            release_id = releases[0]['id']

            # Get cover art URL from Cover Art Archive
            cover_url = f"https://coverartarchive.org/release/{release_id}/front"

            logger.info(f"Found cover URL for {artist} - {album}")
            return cover_url

        except Exception as e:
            logger.warning(f"Failed to get cover URL for {artist} - {album}: {e}")
            return None

    def download_cover(self, artist: str, album: str, save_path: Optional[str] = None) -> bool:
        """
        Download cover art for artist/album

        Args:
            artist: Artist name
            album: Album name
            save_path: Optional custom save path (default: auto-generated)

        Returns:
            bool: True if successful
        """
        try:
            # Get cover URL
            cover_url = self.get_cover_url(artist, album)

            if not cover_url:
                logger.debug(f"No cover found for: {artist} - {album}")
                return False

            # Generate save path if not provided
            if not save_path:
                # Create artist/album directory structure
                artist_dir = self.cover_dir / self._sanitize_filename(artist)
                album_dir = artist_dir / self._sanitize_filename(album)
                album_dir.mkdir(parents=True, exist_ok=True)

                save_path = album_dir / "cover.jpg"

            # Download cover
            response = requests.get(cover_url, timeout=10)

            if response.status_code == 200:
                # Save image
                with open(save_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"Cover downloaded: {save_path}")
                return True
            else:
                logger.warning(f"Failed to download cover: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error downloading cover for {artist} - {album}: {e}")
            return False

    def download_cover_from_mbid(self, release_mbid: str, save_path: str) -> bool:
        """
        Download cover art using MusicBrainz Release ID

        Args:
            release_mbid: MusicBrainz Release ID
            save_path: Path to save cover

        Returns:
            bool: True if successful
        """
        try:
            cover_url = f"https://coverartarchive.org/release/{release_mbid}/front"

            response = requests.get(cover_url, timeout=10)

            if response.status_code == 200:
                # Create directory if needed
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)

                # Save image
                with open(save_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"Cover downloaded from MBID: {save_path}")
                return True
            else:
                logger.warning(f"No cover found for MBID {release_mbid}")
                return False

        except Exception as e:
            logger.error(f"Error downloading cover for MBID {release_mbid}: {e}")
            return False

    def get_cover_path(self, artist: str, album: str) -> Path:
        """
        Get expected cover path for artist/album

        Args:
            artist: Artist name
            album: Album name

        Returns:
            Path: Expected cover file path
        """
        artist_dir = self.cover_dir / self._sanitize_filename(artist)
        album_dir = artist_dir / self._sanitize_filename(album)
        return album_dir / "cover.jpg"

    def has_cover(self, artist: str, album: str) -> bool:
        """
        Check if cover already exists

        Args:
            artist: Artist name
            album: Album name

        Returns:
            bool: True if cover exists
        """
        cover_path = self.get_cover_path(artist, album)
        return cover_path.exists()

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename to remove invalid characters

        Args:
            name: Original name

        Returns:
            str: Sanitized name safe for filesystem
        """
        # Remove/replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = name

        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')

        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized.strip()

    def get_stats(self) -> Dict:
        """
        Get cover art statistics

        Returns:
            dict: Stats about covers
        """
        total_covers = 0
        total_artists = 0

        if self.cover_dir.exists():
            # Count artist directories
            artist_dirs = [d for d in self.cover_dir.iterdir() if d.is_dir()]
            total_artists = len(artist_dirs)

            # Count cover files
            for artist_dir in artist_dirs:
                for album_dir in artist_dir.iterdir():
                    if album_dir.is_dir():
                        cover_file = album_dir / "cover.jpg"
                        if cover_file.exists():
                            total_covers += 1

        return {
            'total_covers': total_covers,
            'total_artists': total_artists,
            'cover_dir': str(self.cover_dir)
        }
