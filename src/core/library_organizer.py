"""
Library Organizer - Phase 5.2

Organize music library into structured folder hierarchy:
- Template-based path generation
- Safe file moving/copying
- Database path updates
- Conflict resolution
- Rollback support

Created: November 13, 2025
"""
import logging
import os
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LibraryOrganizer:
    """
    Organize music library into structured folders

    Templates support placeholders:
    - {artist}: Artist name
    - {album}: Album name
    - {title}: Song title
    - {year}: Release year
    - {genre}: Music genre
    - {track:02d}: Track number (zero-padded)

    Example templates:
    1. "{genre}/{artist}/{album} ({year})/{track:02d} - {title}.mp3"
    2. "{artist}/{album}/{track:02d} - {title}.mp3"
    3. "{artist}/{track:02d} - {title}.mp3"

    Usage:
        organizer = LibraryOrganizer(db_manager)

        # Preview changes
        preview = organizer.organize(
            base_path="/music",
            template="{artist}/{album}/{title}.mp3",
            songs=songs,
            dry_run=True
        )

        # Actually organize
        result = organizer.organize(
            base_path="/music",
            template="{artist}/{album}/{title}.mp3",
            songs=songs,
            move=True
        )
    """

    def __init__(self, db_manager):
        """
        Initialize library organizer

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self._history = []  # For rollback
        logger.info("LibraryOrganizer initialized")

    def organize(self, base_path: str, template: str, songs: List[Dict],
                 move: bool = True, dry_run: bool = False) -> Dict:
        """
        Organize songs into folder structure

        Args:
            base_path: Root directory (e.g., /music/organized)
            template: Path template string
            songs: List of song dictionaries
            move: True = move files, False = copy files
            dry_run: If True, preview without actual changes

        Returns:
            {
                'success': 150,
                'failed': 0,
                'errors': [],
                'preview': [{'old': '...', 'new': '...'}]  # If dry_run
            }
        """
        logger.info(f"Organizing {len(songs)} songs (dry_run={dry_run})")

        result = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'preview': []
        }

        self._history = []

        for song in songs:
            try:
                # Build target path
                target_path = self.build_path(base_path, template, song)

                old_path = song.get('file_path', '')

                if dry_run:
                    # Preview mode - don't move files
                    result['preview'].append({
                        'old': old_path,
                        'new': str(target_path),
                        'song': song
                    })
                    result['success'] += 1
                else:
                    # Actually move/copy file
                    if os.path.exists(old_path):
                        # Create target directory
                        self._create_directories(os.path.dirname(target_path))

                        # Handle name conflicts
                        if os.path.exists(target_path):
                            target_path = self._handle_name_conflict(target_path)

                        # Move or copy
                        if move:
                            success = self._move_file(old_path, str(target_path))
                        else:
                            success = self._copy_file(old_path, str(target_path))

                        if success:
                            # Update database
                            self._update_database_path(song['id'], str(target_path))

                            # Store for rollback
                            self._history.append({
                                'old': old_path,
                                'new': str(target_path),
                                'song_id': song['id']
                            })

                            result['success'] += 1
                        else:
                            result['failed'] += 1
                            result['errors'].append(f"Failed to move: {old_path}")
                    else:
                        result['failed'] += 1
                        result['errors'].append(f"File not found: {old_path}")

            except Exception as e:
                result['failed'] += 1
                result['errors'].append(f"Error: {song.get('file_path', 'unknown')}: {str(e)}")
                logger.error(f"Organization error: {e}")

        logger.info(f"Organization complete: {result['success']} success, {result['failed']} failed")
        return result

    def build_path(self, base_path: str, template: str, song: Dict) -> Path:
        """
        Build target path from template and song metadata

        Args:
            base_path: Root directory
            template: Path template
            song: Song metadata dictionary

        Returns:
            Path object for target file
        """
        # Get metadata with fallbacks
        metadata = {
            'artist': self._sanitize_path(song.get('artist', 'Unknown Artist')),
            'album': self._sanitize_path(song.get('album', 'Unknown Album')),
            'title': self._sanitize_path(song.get('title', 'Unknown')),
            'year': song.get('year', 'Unknown'),
            'genre': self._sanitize_path(song.get('genre', 'Unknown')),
            'track': song.get('track', 0)
        }

        # Format template
        try:
            relative_path = template.format(**metadata)
        except KeyError as e:
            logger.warning(f"Missing template key: {e}, using fallback")
            # Fallback to simple template
            relative_path = f"{metadata['artist']}/{metadata['title']}.mp3"

        # Combine with base path
        full_path = Path(base_path) / relative_path

        return full_path

    def _sanitize_path(self, text: str) -> str:
        """
        Sanitize text for use in file paths

        Args:
            text: Raw text

        Returns:
            Sanitized text safe for filenames
        """
        if not text:
            return "Unknown"

        # Remove/replace invalid filesystem characters
        # Invalid: / \ : * ? " < > |
        text = re.sub(r'[/\\:*?"<>|]', '_', text)

        # Remove leading/trailing dots and spaces
        text = text.strip('. ')

        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        if not text:
            return "Unknown"

        return text

    def _create_directories(self, directory: str):
        """
        Create directory structure

        Args:
            directory: Directory path to create
        """
        try:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise

    def _move_file(self, source: str, target: str) -> bool:
        """
        Move file from source to target

        Args:
            source: Source file path
            target: Target file path

        Returns:
            True if successful
        """
        try:
            # Create target directory if needed
            target_dir = os.path.dirname(target)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            shutil.move(source, target)
            logger.debug(f"Moved: {source} -> {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to move {source} to {target}: {e}")
            return False

    def _copy_file(self, source: str, target: str) -> bool:
        """
        Copy file from source to target

        Args:
            source: Source file path
            target: Target file path

        Returns:
            True if successful
        """
        try:
            shutil.copy2(source, target)
            logger.debug(f"Copied: {source} -> {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy {source} to {target}: {e}")
            return False

    def _update_database_path(self, song_id: int, new_path: str):
        """
        Update song file path in database

        Args:
            song_id: Song ID
            new_path: New file path
        """
        try:
            self.db.update_song_path(song_id, new_path)
            logger.debug(f"Updated database: song {song_id} -> {new_path}")
        except Exception as e:
            logger.error(f"Failed to update database for song {song_id}: {e}")
            raise

    def _handle_name_conflict(self, file_path: str) -> str:
        """
        Generate unique filename if conflict exists

        Args:
            file_path: Desired file path

        Returns:
            Unique file path
        """
        path = Path(file_path)
        stem = path.stem
        suffix = path.suffix
        directory = path.parent

        counter = 1
        while True:
            new_path = directory / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                logger.debug(f"Resolved conflict: {file_path} -> {new_path}")
                return str(new_path)
            counter += 1

            if counter > 1000:
                # Safety limit
                raise ValueError(f"Too many conflicts for: {file_path}")

    def rollback(self):
        """
        Rollback last organization operation

        Moves files back to their original locations.
        """
        if not self._history:
            logger.warning("No history to rollback")
            return {
                'success': 0,
                'failed': 0,
                'errors': ['No history to rollback']
            }

        logger.info(f"Rolling back {len(self._history)} operations")

        result = {
            'success': 0,
            'failed': 0,
            'errors': []
        }

        # Reverse history
        for operation in reversed(self._history):
            try:
                new_path = operation['new']
                old_path = operation['old']
                song_id = operation['song_id']

                if os.path.exists(new_path):
                    # Create original directory if needed
                    os.makedirs(os.path.dirname(old_path), exist_ok=True)

                    # Move back
                    shutil.move(new_path, old_path)

                    # Update database
                    self.db.update_song_path(song_id, old_path)

                    result['success'] += 1
                else:
                    result['failed'] += 1
                    result['errors'].append(f"File not found for rollback: {new_path}")

            except Exception as e:
                result['failed'] += 1
                result['errors'].append(f"Rollback error: {str(e)}")
                logger.error(f"Rollback error: {e}")

        logger.info(f"Rollback complete: {result['success']} restored, {result['failed']} failed")

        # Clear history
        self._history = []

        return result
