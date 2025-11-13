"""
Playlist Manager - Phase 7.1

Core playlist management system for creating, editing, and managing playlists.

Features:
- Create/delete playlists
- Add/remove/reorder songs in playlists
- Save/load playlists to/from .m3u8 files
- Duplicate playlists
- Playlist statistics
- Database integration

Created: November 13, 2025
"""
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class PlaylistManager:
    """
    Playlist management system

    Handles all playlist operations:
    - Create/delete/update playlists
    - Manage songs in playlists
    - Import/export .m3u8 files
    - Playlist statistics

    Usage:
        manager = PlaylistManager(db_manager)

        # Create playlist
        playlist_id = manager.create_playlist("My Favorites", "Best songs")

        # Add songs
        manager.add_song(playlist_id, song_id=100)
        manager.add_song(playlist_id, song_id=200)

        # Export
        manager.save_playlist(playlist_id, "/path/to/playlist.m3u8")
    """

    def __init__(self, db_manager):
        """
        Initialize Playlist Manager

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        logger.info("PlaylistManager initialized")

    def create_playlist(self, name: str, description: str = "") -> int:
        """
        Create new playlist

        Args:
            name: Playlist name
            description: Optional description

        Returns:
            New playlist ID
        """
        try:
            query = """
            INSERT INTO playlists (name, description)
            VALUES (?, ?)
            """
            playlist_id = self.db_manager.execute_query(query, (name, description))
            logger.info(f"Created playlist: {name} (ID: {playlist_id})")
            return playlist_id

        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            raise

    def delete_playlist(self, playlist_id: int) -> bool:
        """
        Delete playlist and all associated songs

        Args:
            playlist_id: Playlist ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete playlist (CASCADE will delete playlist_songs)
            query = "DELETE FROM playlists WHERE id = ?"
            self.db_manager.execute_query(query, (playlist_id,))
            logger.info(f"Deleted playlist ID: {playlist_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete playlist: {e}")
            return False

    def add_song(self, playlist_id: int, song_id: int, position: Optional[int] = None) -> bool:
        """
        Add song to playlist

        Args:
            playlist_id: Playlist ID
            song_id: Song ID to add
            position: Optional position (defaults to end)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current max position if not specified
            if position is None:
                query = "SELECT MAX(position) as max_pos FROM playlist_songs WHERE playlist_id = ?"
                result = self.db_manager.fetch_one(query, (playlist_id,))
                position = (result['max_pos'] + 1) if result and result['max_pos'] is not None else 0

            # Insert song
            query = """
            INSERT INTO playlist_songs (playlist_id, song_id, position)
            VALUES (?, ?, ?)
            """
            self.db_manager.execute_query(query, (playlist_id, song_id, position))
            logger.debug(f"Added song {song_id} to playlist {playlist_id} at position {position}")
            return True

        except Exception as e:
            logger.error(f"Failed to add song to playlist: {e}")
            return False

    def remove_song(self, playlist_id: int, song_id: int) -> bool:
        """
        Remove song from playlist

        Args:
            playlist_id: Playlist ID
            song_id: Song ID to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            query = "DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?"
            self.db_manager.execute_query(query, (playlist_id, song_id))
            logger.debug(f"Removed song {song_id} from playlist {playlist_id}")

            # Reorder remaining songs
            self._reorder_playlist_songs(playlist_id)
            return True

        except Exception as e:
            logger.error(f"Failed to remove song from playlist: {e}")
            return False

    def reorder_songs(self, playlist_id: int, old_index: int, new_index: int) -> bool:
        """
        Reorder songs in playlist (move song from old_index to new_index)

        Args:
            playlist_id: Playlist ID
            old_index: Current position
            new_index: New position

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all songs in order
            query = """
            SELECT id, song_id, position
            FROM playlist_songs
            WHERE playlist_id = ?
            ORDER BY position
            """
            songs = self.db_manager.fetch_all(query, (playlist_id,))

            if old_index < 0 or old_index >= len(songs):
                return False
            if new_index < 0 or new_index >= len(songs):
                return False

            # Move song
            song_to_move = songs.pop(old_index)
            songs.insert(new_index, song_to_move)

            # Update positions
            for i, song in enumerate(songs):
                update_query = "UPDATE playlist_songs SET position = ? WHERE id = ?"
                self.db_manager.execute_query(update_query, (i, song['id']))

            logger.debug(f"Reordered playlist {playlist_id}: moved position {old_index} → {new_index}")
            return True

        except Exception as e:
            logger.error(f"Failed to reorder songs: {e}")
            return False

    def get_playlists(self) -> List[Dict]:
        """
        Get all playlists with song counts

        Returns:
            List of playlist dictionaries
        """
        try:
            query = """
            SELECT
                p.id,
                p.name,
                p.description,
                p.created_date,
                p.modified_date,
                COUNT(ps.song_id) as song_count
            FROM playlists p
            LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
            GROUP BY p.id
            ORDER BY p.name
            """
            playlists = self.db_manager.fetch_all(query)
            return playlists or []

        except Exception as e:
            logger.error(f"Failed to get playlists: {e}")
            return []

    def get_playlist_songs(self, playlist_id: int) -> List[Dict]:
        """
        Get all songs in playlist

        Args:
            playlist_id: Playlist ID

        Returns:
            List of song dictionaries with metadata
        """
        try:
            query = """
            SELECT
                s.id,
                s.title,
                s.artist,
                s.album,
                s.duration,
                s.file_path,
                ps.position
            FROM playlist_songs ps
            JOIN songs s ON ps.song_id = s.id
            WHERE ps.playlist_id = ?
            ORDER BY ps.position
            """
            songs = self.db_manager.fetch_all(query, (playlist_id,))
            return songs or []

        except Exception as e:
            logger.error(f"Failed to get playlist songs: {e}")
            return []

    def save_playlist(self, playlist_id: int, file_path: str) -> bool:
        """
        Save playlist to .m3u8 file

        Args:
            playlist_id: Playlist ID to export
            file_path: Output file path (.m3u8)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get playlist songs
            songs = self.get_playlist_songs(playlist_id)

            # Write .m3u8 file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')

                for song in songs:
                    duration = int(song.get('duration', 0))
                    artist = song.get('artist', 'Unknown Artist')
                    title = song.get('title', 'Unknown')
                    file_path_song = song.get('file_path', '')

                    # Write extended info
                    f.write(f'#EXTINF:{duration},{artist} - {title}\n')
                    f.write(f'{file_path_song}\n')

            logger.info(f"Saved playlist {playlist_id} to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save playlist: {e}")
            return False

    def load_playlist(self, file_path: str, name: Optional[str] = None) -> Optional[int]:
        """
        Load playlist from .m3u8 file

        Args:
            file_path: Path to .m3u8 file
            name: Optional playlist name (defaults to filename)

        Returns:
            New playlist ID if successful, None otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None

            # Generate playlist name from filename if not provided
            if name is None:
                name = Path(file_path).stem

            # Create new playlist
            playlist_id = self.create_playlist(name, f"Imported from {Path(file_path).name}")

            # Parse .m3u8 file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            position = 0
            for i, line in enumerate(lines):
                line = line.strip()

                # Skip comments except #EXTINF
                if line.startswith('#') and not line.startswith('#EXTINF'):
                    continue

                # Skip empty lines
                if not line:
                    continue

                # Process file path lines
                if not line.startswith('#'):
                    song_path = line

                    # Try to find song in database by file path
                    query = "SELECT id FROM songs WHERE file_path = ?"
                    result = self.db_manager.fetch_one(query, (song_path,))

                    if result:
                        song_id = result['id']
                        self.add_song(playlist_id, song_id, position)
                        position += 1
                    else:
                        logger.warning(f"Song not found in database: {song_path}")

            logger.info(f"Loaded playlist from {file_path} (ID: {playlist_id}, {position} songs)")
            return playlist_id

        except Exception as e:
            logger.error(f"Failed to load playlist: {e}")
            return None

    def duplicate_playlist(self, playlist_id: int, new_name: Optional[str] = None) -> Optional[int]:
        """
        Duplicate existing playlist

        Args:
            playlist_id: Playlist ID to duplicate
            new_name: Optional name for new playlist (defaults to "Copy of [name]")

        Returns:
            New playlist ID if successful, None otherwise
        """
        try:
            # Get original playlist
            query = "SELECT * FROM playlists WHERE id = ?"
            original = self.db_manager.fetch_one(query, (playlist_id,))

            if not original:
                logger.error(f"Playlist not found: {playlist_id}")
                return None

            # Generate new name
            if new_name is None:
                new_name = f"Copy of {original['name']}"

            # Create new playlist
            new_id = self.create_playlist(new_name, original.get('description', ''))

            # Copy all songs
            songs = self.get_playlist_songs(playlist_id)
            for song in songs:
                self.add_song(new_id, song['id'], song['position'])

            logger.info(f"Duplicated playlist {playlist_id} → {new_id}")
            return new_id

        except Exception as e:
            logger.error(f"Failed to duplicate playlist: {e}")
            return None

    def get_playlist_stats(self, playlist_id: int) -> Dict:
        """
        Get playlist statistics

        Args:
            playlist_id: Playlist ID

        Returns:
            Dictionary with statistics (song_count, total_duration)
        """
        try:
            query = """
            SELECT
                COUNT(ps.song_id) as song_count,
                COALESCE(SUM(s.duration), 0) as total_duration
            FROM playlist_songs ps
            LEFT JOIN songs s ON ps.song_id = s.id
            WHERE ps.playlist_id = ?
            """
            result = self.db_manager.fetch_one(query, (playlist_id,))

            return {
                'song_count': result['song_count'] if result else 0,
                'total_duration': result['total_duration'] if result else 0
            }

        except Exception as e:
            logger.error(f"Failed to get playlist stats: {e}")
            return {'song_count': 0, 'total_duration': 0}

    def _reorder_playlist_songs(self, playlist_id: int):
        """
        Internal: Reorder playlist songs to fill gaps in positions

        Args:
            playlist_id: Playlist ID
        """
        try:
            # Get all songs ordered by position
            query = """
            SELECT id FROM playlist_songs
            WHERE playlist_id = ?
            ORDER BY position
            """
            songs = self.db_manager.fetch_all(query, (playlist_id,))

            # Update positions sequentially
            for i, song in enumerate(songs):
                update_query = "UPDATE playlist_songs SET position = ? WHERE id = ?"
                self.db_manager.execute_query(update_query, (i, song['id']))

        except Exception as e:
            logger.error(f"Failed to reorder playlist songs: {e}")
