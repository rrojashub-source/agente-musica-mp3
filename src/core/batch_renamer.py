"""
Batch Renamer - Phase 5.3

Batch rename MP3 files based on metadata patterns:
- Template-based filename generation
- Find/replace operations
- Case conversion (UPPER, lower, Title Case)
- Number sequences (001, 002, ...)
- Preview changes before applying
- Safe renaming with conflict resolution
- Database path updates

Created: November 13, 2025
"""
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class BatchRenamer:
    """
    Batch rename files based on metadata templates

    Templates support placeholders:
    - {artist}: Artist name
    - {album}: Album name
    - {title}: Song title
    - {year}: Release year
    - {genre}: Music genre
    - {track:02d}: Track number (zero-padded)
    - {seq:03d}: Sequence number (for custom numbering)

    Example templates:
    1. "{track:02d} - {artist} - {title}.mp3"
    2. "{artist} - {album} - {track:02d} - {title}.mp3"
    3. "{seq:03d} - {title}.mp3"

    Usage:
        renamer = BatchRenamer(db_manager)

        # Preview changes
        preview = renamer.rename_batch(
            songs=songs,
            template="{track:02d} - {title}.mp3",
            dry_run=True
        )

        # Apply renames
        result = renamer.rename_batch(
            songs=songs,
            template="{track:02d} - {title}.mp3",
            dry_run=False
        )
    """

    def __init__(self, db_manager):
        """
        Initialize batch renamer

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        logger.info("BatchRenamer initialized")

    def rename_batch(self, songs: List[Dict], template: str,
                     find: str = "", replace: str = "",
                     case: str = "none", dry_run: bool = False) -> Dict:
        """
        Rename multiple files in batch

        Args:
            songs: List of song dictionaries
            template: Filename template string
            find: Find string for find/replace (optional)
            replace: Replace string for find/replace (optional)
            case: Case conversion ("none", "upper", "lower", "title")
            dry_run: If True, preview without actual changes

        Returns:
            {
                'success': 150,
                'failed': 0,
                'errors': [],
                'preview': [{'old': '...', 'new': '...'}]  # If dry_run
            }
        """
        logger.info(f"Renaming {len(songs)} songs (dry_run={dry_run})")

        result = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'preview': []
        }

        for seq, song in enumerate(songs, 1):
            try:
                old_path = song.get('file_path', '')

                if not os.path.exists(old_path):
                    result['failed'] += 1
                    result['errors'].append(f"File not found: {old_path}")
                    continue

                # Build new filename
                new_filename = self.build_filename(template, song, seq=seq)

                # Apply find/replace if specified
                if find:
                    new_filename = self.apply_find_replace(new_filename, find, replace)

                # Apply case conversion if specified
                if case != "none":
                    new_filename = self.apply_case_conversion(new_filename, case)

                # Build full new path
                directory = os.path.dirname(old_path)
                new_path = os.path.join(directory, new_filename)

                if dry_run:
                    # Preview mode - don't rename files
                    result['preview'].append({
                        'old': old_path,
                        'new': new_path,
                        'song': song
                    })
                    result['success'] += 1
                else:
                    # Actually rename file
                    # Handle name conflicts
                    if os.path.exists(new_path) and new_path != old_path:
                        new_path = self._handle_name_conflict(new_path)

                    # Rename file
                    success = self._rename_file(old_path, new_path)

                    if success:
                        # Update database
                        self._update_database_path(song['id'], new_path)
                        result['success'] += 1
                    else:
                        result['failed'] += 1
                        result['errors'].append(f"Failed to rename: {old_path}")

            except Exception as e:
                result['failed'] += 1
                result['errors'].append(f"Error: {song.get('file_path', 'unknown')}: {str(e)}")
                logger.error(f"Rename error: {e}")

        logger.info(f"Rename complete: {result['success']} success, {result['failed']} failed")
        return result

    def build_filename(self, template: str, song: Dict, seq: int = 0) -> str:
        """
        Build filename from template and song metadata

        Args:
            template: Filename template
            song: Song metadata dictionary
            seq: Sequence number (for {seq:NNd} placeholder)

        Returns:
            Sanitized filename string
        """
        # Get metadata with fallbacks
        metadata = {
            'artist': song.get('artist', 'Unknown Artist'),
            'album': song.get('album', 'Unknown Album'),
            'title': song.get('title', 'Unknown'),
            'year': song.get('year', 'Unknown'),
            'genre': song.get('genre', 'Unknown'),
            'track': song.get('track', 0),
            'seq': seq
        }

        # Format template
        try:
            filename = template.format(**metadata)
        except KeyError as e:
            logger.warning(f"Missing template key: {e}, using fallback")
            # Fallback to simple template
            filename = f"{metadata['track']:02d} - {metadata['title']}.mp3"

        # Sanitize filename
        filename = self._sanitize_filename(filename)

        return filename

    def apply_find_replace(self, filename: str, find: str, replace: str) -> str:
        """
        Apply find/replace operation to filename

        Args:
            filename: Original filename
            find: String to find
            replace: String to replace with

        Returns:
            Modified filename
        """
        return filename.replace(find, replace)

    def apply_case_conversion(self, filename: str, case: str) -> str:
        """
        Apply case conversion to filename

        Args:
            filename: Original filename
            case: Conversion type ("upper", "lower", "title")

        Returns:
            Converted filename
        """
        # Separate extension to preserve it
        path = Path(filename)
        stem = path.stem
        suffix = path.suffix

        if case == "upper":
            converted_stem = stem.upper()
            converted_suffix = suffix.upper()
        elif case == "lower":
            converted_stem = stem.lower()
            converted_suffix = suffix.lower()
        elif case == "title":
            converted_stem = stem.title()
            converted_suffix = suffix.lower()  # Keep extension lowercase
        else:
            return filename

        return converted_stem + converted_suffix

    def _sanitize_filename(self, text: str) -> str:
        """
        Sanitize text for use in filenames

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

    def _rename_file(self, old_path: str, new_path: str) -> bool:
        """
        Rename file from old_path to new_path

        Args:
            old_path: Current file path
            new_path: New file path

        Returns:
            True if successful
        """
        try:
            os.rename(old_path, new_path)
            logger.debug(f"Renamed: {old_path} -> {new_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to rename {old_path} to {new_path}: {e}")
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
