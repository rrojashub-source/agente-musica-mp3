"""
Metadata Tagger - Phase 4.9
Auto-tag MP3 files with metadata using Mutagen + MusicBrainz

Features:
- Write ID3v2.3 tags (title, artist, album, year, genre)
- MusicBrainz metadata lookup with confidence scoring
- Embed album art (optional)
- Handle missing/corrupt files gracefully
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from mutagen import MutagenError
from mutagen.id3 import APIC, ID3, TALB, TCON, TDRC, TIT2, TPE1
from mutagen.id3 import error as ID3Error
from mutagen.mp3 import MP3

from core.metadata_autocompleter import MetadataAutocompleter

# Setup logger
logger = logging.getLogger(__name__)


class MetadataTagger:
    """
    Auto-tag MP3 files with metadata

    Usage:
        tagger = MetadataTagger()

        # Direct tagging with known metadata
        metadata = {'title': 'Song', 'artist': 'Artist', 'album': 'Album'}
        tagger.tag_file('song.mp3', metadata)

        # Lookup and tag (MusicBrainz search)
        partial_metadata = {'title': 'Bohemian Rhapsody'}
        tagger.lookup_and_tag('song.mp3', partial_metadata)
    """

    def __init__(self) -> None:
        """
        Initialize metadata tagger
        """
        self.autocompleter: MetadataAutocompleter = MetadataAutocompleter()
        logger.info("MetadataTagger initialized")

    def tag_file(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Tag MP3 file with metadata

        Args:
            file_path (str): Path to MP3 file
            metadata (dict): Metadata dict with keys:
                            'title', 'artist', 'album', 'year', 'genre'

        Returns:
            bool: True if successful, False otherwise

        Examples:
            >>> tagger.tag_file('song.mp3', {'title': 'Test', 'artist': 'Artist'})
            True
        """
        try:
            # Load MP3 file
            audio = MP3(file_path, ID3=ID3)

            # Add ID3 tag if not present
            try:
                audio.add_tags()
            except ID3Error:
                pass  # Tags already exist

            assert audio.tags is not None  # Tags guaranteed after add_tags()

            # Write title (TIT2)
            if "title" in metadata and metadata["title"]:
                audio.tags["TIT2"] = TIT2(encoding=3, text=metadata["title"])  # type: ignore[index]
                logger.debug(f"Tagged title: {metadata['title']}")

            # Write artist (TPE1)
            if "artist" in metadata and metadata["artist"]:
                audio.tags["TPE1"] = TPE1(encoding=3, text=metadata["artist"])  # type: ignore[index]
                logger.debug(f"Tagged artist: {metadata['artist']}")

            # Write album (TALB)
            if "album" in metadata and metadata["album"]:
                audio.tags["TALB"] = TALB(encoding=3, text=metadata["album"])  # type: ignore[index]
                logger.debug(f"Tagged album: {metadata['album']}")

            # Write year (TDRC)
            if "year" in metadata and metadata["year"]:
                audio.tags["TDRC"] = TDRC(encoding=3, text=str(metadata["year"]))  # type: ignore[index]
                logger.debug(f"Tagged year: {metadata['year']}")

            # Write genre (TCON)
            if "genre" in metadata and metadata["genre"]:
                audio.tags["TCON"] = TCON(encoding=3, text=metadata["genre"])  # type: ignore[index]
                logger.debug(f"Tagged genre: {metadata['genre']}")

            # Save tags
            audio.save()

            logger.info(f"Successfully tagged: {file_path}")
            return True

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False

        except (OSError, MutagenError) as e:
            logger.error(f"Error tagging file {file_path}: {e}")
            return False

    def lookup_and_tag(self, file_path: str, metadata: Dict[str, Any], min_confidence: int = 80) -> bool:
        """
        Lookup metadata on MusicBrainz and tag file

        Args:
            file_path (str): Path to MP3 file
            metadata (dict): Partial metadata (at least 'title')
            min_confidence (int): Minimum confidence score (0-100) to use lookup result

        Returns:
            bool: True if successful, False otherwise

        Examples:
            >>> tagger.lookup_and_tag('song.mp3', {'title': 'Bohemian Rhapsody'})
            True
        """
        try:
            # Validate minimum metadata
            if "title" not in metadata or not metadata["title"]:
                logger.warning("No title provided for lookup")
                return False

            # Search MusicBrainz
            matches = self.autocompleter.autocomplete_single(metadata)

            if not matches:
                logger.warning(f"No MusicBrainz matches for: {metadata.get('title')}")
                # Fallback: tag with what we have
                return self.tag_file(file_path, metadata)

            # Get best match
            best_match = matches[0]

            # Check confidence threshold
            if best_match["confidence"] < min_confidence:
                logger.info(f"Low confidence ({best_match['confidence']}%), using original metadata only")
                return self.tag_file(file_path, metadata)

            # Use high-confidence match
            logger.info(
                f"High confidence match ({best_match['confidence']}%): {best_match['title']} - {best_match['artist']}"
            )

            # Merge original metadata with MusicBrainz data
            # (Prefer MusicBrainz data for missing fields)
            merged_metadata = {**best_match, **metadata}

            # Remove confidence key (not an ID3 tag)
            merged_metadata.pop("confidence", None)

            # Tag file with merged metadata
            return self.tag_file(file_path, merged_metadata)

        except (OSError, ValueError, KeyError, MutagenError) as e:
            logger.error(f"Error in lookup_and_tag: {e}")
            return False

    def embed_album_art(self, file_path: str, image_path: str) -> bool:
        """
        Embed album art in MP3 file

        Args:
            file_path (str): Path to MP3 file
            image_path (str): Path to image file (JPG/PNG)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load MP3 file
            audio = MP3(file_path, ID3=ID3)

            # Add ID3 tag if not present
            try:
                audio.add_tags()
            except ID3Error:
                pass

            assert audio.tags is not None  # Tags guaranteed after add_tags()

            # Read image data
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()

            # Determine MIME type
            if image_path.lower().endswith(".png"):
                mime = "image/png"
            else:
                mime = "image/jpeg"

            # Embed cover art (APIC frame)
            audio.tags["APIC"] = APIC(  # type: ignore[index]
                encoding=3, mime=mime, type=3, desc="Cover", data=img_data  # Cover (front)
            )

            # Save
            audio.save()

            logger.info(f"Embedded album art: {file_path}")
            return True

        except FileNotFoundError:
            logger.error(f"File not found: {file_path} or {image_path}")
            return False

        except (OSError, MutagenError) as e:
            logger.error(f"Error embedding album art: {e}")
            return False
