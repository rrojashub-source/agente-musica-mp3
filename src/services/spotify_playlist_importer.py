"""
Spotify Playlist Importer Service

Import playlists from Spotify to local library.
Searches each track on YouTube for download.

Features:
- Parse Spotify playlist URLs
- Fetch playlist tracks via API
- Convert to YouTube search queries
- Add to download queue
- Track import progress

Created: December 12, 2025
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SpotifyTrack:
    """Track from Spotify playlist"""

    track_id: str
    title: str
    artist: str
    album: str
    duration_ms: int
    position: int  # Position in playlist

    @property
    def search_query(self) -> str:
        """Generate YouTube search query"""
        return f"{self.artist} - {self.title}"

    @property
    def duration_seconds(self) -> int:
        """Duration in seconds"""
        return self.duration_ms // 1000


@dataclass
class SpotifyPlaylist:
    """Spotify playlist metadata"""

    playlist_id: str
    name: str
    description: str
    owner: str
    total_tracks: int
    tracks: List[SpotifyTrack]
    image_url: Optional[str] = None


class SpotifyPlaylistImporter:
    """
    Import Spotify playlists for download

    Usage:
        importer = SpotifyPlaylistImporter(spotify_client)

        # Parse URL
        playlist_id = importer.parse_playlist_url(url)

        # Fetch playlist
        playlist = importer.fetch_playlist(playlist_id)

        # Add to download queue
        importer.add_to_queue(playlist, download_queue, progress_callback)
    """

    # URL patterns
    PLAYLIST_URL_PATTERN: re.Pattern[str] = re.compile(r"(?:https?://)?(?:open\.)?spotify\.com/playlist/([a-zA-Z0-9]+)")
    PLAYLIST_URI_PATTERN: re.Pattern[str] = re.compile(r"spotify:playlist:([a-zA-Z0-9]+)")

    def __init__(self, spotify_client: Any) -> None:
        """
        Initialize importer

        Args:
            spotify_client: Spotipy client instance or SpotifySearcher
        """
        self.sp: Any = spotify_client

        # Handle SpotifySearcher wrapper
        if hasattr(spotify_client, "sp"):
            self.sp = spotify_client.sp

        logger.info("SpotifyPlaylistImporter initialized")

    def parse_playlist_url(self, url_or_uri: str) -> Optional[str]:
        """
        Extract playlist ID from URL or URI

        Args:
            url_or_uri: Spotify playlist URL or URI

        Returns:
            Playlist ID or None if invalid

        Examples:
            >>> parse_playlist_url("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
            "37i9dQZF1DXcBWIGoYBM5M"

            >>> parse_playlist_url("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")
            "37i9dQZF1DXcBWIGoYBM5M"
        """
        if not url_or_uri:
            return None

        # Try URL pattern
        match = self.PLAYLIST_URL_PATTERN.search(url_or_uri)
        if match:
            return match.group(1)

        # Try URI pattern
        match = self.PLAYLIST_URI_PATTERN.search(url_or_uri)
        if match:
            return match.group(1)

        # Maybe it's just the ID
        if re.match(r"^[a-zA-Z0-9]{22}$", url_or_uri):
            return url_or_uri

        logger.warning(f"Could not parse playlist URL/URI: {url_or_uri}")
        return None

    def fetch_playlist(self, playlist_id: str) -> Optional[SpotifyPlaylist]:
        """
        Fetch playlist metadata and tracks

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            SpotifyPlaylist object or None if error
        """
        try:
            # Get playlist metadata
            playlist_data = self.sp.playlist(playlist_id)

            if not playlist_data:
                logger.error(f"Playlist not found: {playlist_id}")
                return None

            # Extract tracks
            tracks = self._fetch_all_tracks(playlist_id, playlist_data)

            # Build playlist object
            playlist = SpotifyPlaylist(
                playlist_id=playlist_id,
                name=playlist_data.get("name", "Unknown Playlist"),
                description=playlist_data.get("description", ""),
                owner=playlist_data.get("owner", {}).get("display_name", "Unknown"),
                total_tracks=playlist_data.get("tracks", {}).get("total", 0),
                tracks=tracks,
                image_url=self._get_image_url(playlist_data),
            )

            logger.info(f"Fetched playlist '{playlist.name}' with {len(tracks)} tracks")
            return playlist

        except (KeyError, ValueError, AttributeError, TypeError) as e:
            logger.error(f"Error fetching playlist {playlist_id}: {e}")
            return None

    def _fetch_all_tracks(self, playlist_id: str, playlist_data: Dict[str, Any]) -> List[SpotifyTrack]:
        """
        Fetch all tracks from playlist (handles pagination)

        Args:
            playlist_id: Playlist ID
            playlist_data: Initial playlist API response

        Returns:
            List of SpotifyTrack objects
        """
        tracks = []
        position = 0

        # Process first batch from initial response
        items = playlist_data.get("tracks", {}).get("items", [])
        for item in items:
            track = self._parse_track(item, position)
            if track:
                tracks.append(track)
                position += 1

        # Fetch remaining pages if more than 100 tracks
        next_url = playlist_data.get("tracks", {}).get("next")

        while next_url:
            try:
                results = self.sp.next(playlist_data["tracks"])
                if not results:
                    break

                items = results.get("items", [])
                for item in items:
                    track = self._parse_track(item, position)
                    if track:
                        tracks.append(track)
                        position += 1

                next_url = results.get("next")
                playlist_data["tracks"] = results

            except (KeyError, ValueError, AttributeError) as e:
                logger.error(f"Error fetching playlist page: {e}")
                break

        return tracks

    def _parse_track(self, item: Dict[str, Any], position: int) -> Optional[SpotifyTrack]:
        """
        Parse track from playlist item

        Args:
            item: Track item from API response
            position: Position in playlist

        Returns:
            SpotifyTrack object or None if invalid
        """
        try:
            track_data = item.get("track")
            if not track_data:
                return None

            # Skip local files (not on Spotify)
            if track_data.get("is_local", False):
                logger.debug(f"Skipping local track at position {position}")
                return None

            # Get artist name
            artists = track_data.get("artists", [])
            artist = artists[0]["name"] if artists else "Unknown Artist"

            return SpotifyTrack(
                track_id=track_data.get("id", ""),
                title=track_data.get("name", "Unknown"),
                artist=artist,
                album=track_data.get("album", {}).get("name", "Unknown"),
                duration_ms=track_data.get("duration_ms", 0),
                position=position,
            )

        except (KeyError, IndexError, ValueError) as e:
            logger.warning(f"Error parsing track at position {position}: {e}")
            return None

    def _get_image_url(self, playlist_data: Dict[str, Any]) -> Optional[str]:
        """Get playlist cover image URL"""
        images = playlist_data.get("images", [])
        if images:
            return images[0].get("url")  # type: ignore[no-any-return]
        return None

    def add_to_queue(
        self,
        playlist: SpotifyPlaylist,
        download_queue: Any,
        youtube_searcher: Any = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> int:
        """
        Add playlist tracks to download queue

        Args:
            playlist: SpotifyPlaylist object
            download_queue: DownloadQueue instance
            youtube_searcher: YouTubeSearcher instance (optional)
            progress_callback: Callback(current, total, track_name) for progress

        Returns:
            Number of tracks added to queue
        """
        added = 0
        total = len(playlist.tracks)

        for i, track in enumerate(playlist.tracks):
            try:
                # Report progress
                if progress_callback:
                    progress_callback(i + 1, total, track.title)

                # Create queue item
                item = {
                    "id": f"spotify_{track.track_id}",
                    "title": track.title,
                    "artist": track.artist,
                    "album": track.album,
                    "duration": track.duration_seconds,
                    "source": "spotify",
                    "search_query": track.search_query,
                    "metadata": {
                        "title": track.title,
                        "artist": track.artist,
                        "album": track.album,
                        "spotify_id": track.track_id,
                        "playlist_name": playlist.name,
                        "playlist_position": track.position,
                    },
                }

                # If YouTube searcher available, search for YouTube URL
                if youtube_searcher:
                    try:
                        results = youtube_searcher.search(track.search_query, max_results=1)
                        if results:
                            item["url"] = results[0].get("url")
                            item["video_id"] = results[0].get("video_id")
                    except (ConnectionError, OSError, KeyError, ValueError) as e:
                        logger.warning(f"YouTube search failed for '{track.search_query}': {e}")

                # Add to queue
                download_queue.add(item)
                added += 1

                logger.debug(f"Added to queue: {track.search_query}")

            except (KeyError, ValueError, AttributeError, RuntimeError) as e:
                logger.error(f"Failed to add track '{track.title}': {e}")

        logger.info(f"Added {added}/{total} tracks from playlist '{playlist.name}'")
        return added

    def get_tracks_for_download(self, playlist: SpotifyPlaylist) -> List[Dict[str, Any]]:
        """
        Convert playlist tracks to download items

        Args:
            playlist: SpotifyPlaylist object

        Returns:
            List of download item dicts ready for queue
        """
        items = []

        for track in playlist.tracks:
            items.append(
                {
                    "id": f"spotify_{track.track_id}",
                    "title": track.title,
                    "artist": track.artist,
                    "album": track.album,
                    "duration": track.duration_seconds,
                    "source": "spotify",
                    "search_query": track.search_query,
                    "metadata": {
                        "title": track.title,
                        "artist": track.artist,
                        "album": track.album,
                        "spotify_id": track.track_id,
                        "playlist_name": playlist.name,
                    },
                }
            )

        return items


def parse_spotify_url(url: str) -> Optional[str]:
    """Convenience function to parse playlist URL"""
    return SpotifyPlaylistImporter(None).parse_playlist_url(url)
