"""
Metadata Cleaner - Intelligent metadata normalization

Purpose: Clean corrupted metadata from MP3 files
- Remove timestamps (_20251013_232019)
- Remove repeated track numbers (00 - 00 - 00)
- Remove concatenated metadata
- Normalize artist/album/title fields
- Detect and flag low-quality metadata

Created: November 18, 2025
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from utils.constants import DEFAULT_ALBUM, DEFAULT_ARTIST
from utils.text_normalizer import _ARTIST_SUFFIX, _YOUTUBE_ARTIFACTS

logger = logging.getLogger(__name__)


class MetadataCleaner:
    """
    Intelligent metadata cleaner and normalizer

    Detects and cleans common metadata corruption patterns:
    - Timestamp suffixes: _YYYYMMDD_HHMMSS
    - Repeated track numbers: 00 - 00 - Artist - Title
    - Concatenated fields: Unknown Artist - Unknown Album - Title
    - YouTube artifacts: [Official Video], (Official Audio), etc.
    """

    def __init__(self) -> None:
        """Initialize metadata cleaner with common patterns"""

        # Patterns to detect and remove
        self.timestamp_pattern: re.Pattern[str] = re.compile(r"_\d{8}_\d{6}")
        self.repeated_track_pattern: re.Pattern[str] = re.compile(r"^(\d+\s*-\s*)+")
        # YouTube artifact and artist suffix patterns from shared utility
        self.youtube_artifacts_pattern: re.Pattern[str] = _YOUTUBE_ARTIFACTS
        self.artist_suffix_pattern: re.Pattern[str] = _ARTIST_SUFFIX

        # Known garbage prefixes/suffixes
        self.garbage_phrases: List[str] = [
            "Unknown Artist - Unknown Album - ",
            "Unknown Artist - ",
            "Unknown Album - ",
            "00 - Unknown Artist - ",
            "00 - ",
        ]

        logger.info("MetadataCleaner initialized")

    def clean_title(self, title: str, artist: Optional[str] = None) -> Tuple[str, List[str]]:
        """
        Clean corrupted title field

        Args:
            title: Original title string
            artist: Artist name (optional) — used to strip "Artist - Title" prefix

        Returns:
            Tuple of (cleaned_title, list_of_issues_found)
        """
        if not title:
            return "Unknown", ["empty_title"]

        original = title
        issues = []

        # Remove timestamps
        if self.timestamp_pattern.search(title):
            title = self.timestamp_pattern.sub("", title)
            issues.append("timestamp_suffix")

        # Remove repeated track numbers
        if self.repeated_track_pattern.search(title):
            title = self.repeated_track_pattern.sub("", title)
            issues.append("repeated_track_numbers")

        # Remove garbage prefixes
        for garbage in self.garbage_phrases:
            if title.startswith(garbage):
                title = title[len(garbage) :]
                issues.append("garbage_prefix")

        # Strip "Artist - Title" prefix when artist is known
        if artist and artist.lower() not in ("unknown", "unknown artist"):
            # Clean artist first (strip VEVO/Official) for matching
            clean_artist = self.artist_suffix_pattern.sub("", artist).strip()
            prefix = re.compile(r"^" + re.escape(clean_artist) + r"\s*[-\u2013\u2014:]\s*", re.IGNORECASE)
            new_title = prefix.sub("", title)
            if new_title != title and new_title.strip():
                title = new_title
                issues.append("artist_prefix")

        # Remove YouTube artifacts
        if self.youtube_artifacts_pattern.search(title):
            title = self.youtube_artifacts_pattern.sub("", title)
            issues.append("youtube_artifacts")

        # Clean up spacing
        title = re.sub(r"\s+", " ", title).strip()
        title = re.sub(r"\s*-\s*$", "", title)  # Remove trailing dash

        # Fallback if empty after cleaning
        if not title:
            title = "Unknown"
            issues.append("empty_after_cleaning")

        if title != original:
            logger.debug(f"Cleaned title: '{original}' → '{title}'")

        return title, issues

    def clean_artist(self, artist: str) -> Tuple[str, List[str]]:
        """
        Clean corrupted artist field

        Args:
            artist: Original artist string

        Returns:
            Tuple of (cleaned_artist, list_of_issues_found)
        """
        if not artist or artist.lower() in ["unknown", "unknown artist"]:
            return DEFAULT_ARTIST, ["missing_artist"]

        original = artist
        issues = []

        # Remove timestamps
        if self.timestamp_pattern.search(artist):
            artist = self.timestamp_pattern.sub("", artist)
            issues.append("timestamp_suffix")

        # Remove YouTube channel suffixes (Official, VEVO, - Topic)
        new_artist = self.artist_suffix_pattern.sub("", artist).strip()
        if new_artist and new_artist != artist:
            artist = new_artist
            issues.append("youtube_channel_suffix")

        # Clean up spacing
        artist = re.sub(r"\s+", " ", artist).strip()

        if artist != original:
            logger.debug(f"Cleaned artist: '{original}' → '{artist}'")

        return artist, issues

    def clean_album(self, album: str) -> Tuple[str, List[str]]:
        """
        Clean corrupted album field

        Args:
            album: Original album string

        Returns:
            Tuple of (cleaned_album, list_of_issues_found)
        """
        if not album or album.lower() in ["unknown", "unknown album"]:
            return DEFAULT_ALBUM, ["missing_album"]

        original = album
        issues = []

        # Remove timestamps
        if self.timestamp_pattern.search(album):
            album = self.timestamp_pattern.sub("", album)
            issues.append("timestamp_suffix")

        # Clean up spacing
        album = re.sub(r"\s+", " ", album).strip()

        if album != original:
            logger.debug(f"Cleaned album: '{original}' → '{album}'")

        return album, issues

    def clean_metadata(self, metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
        """
        Clean all metadata fields in a song dictionary

        Args:
            metadata: Song metadata dictionary (title, artist, album, etc.)

        Returns:
            Tuple of (cleaned_metadata, issues_dict)
        """
        cleaned = metadata.copy()
        all_issues = {}

        # Clean title
        if "title" in cleaned:
            cleaned["title"], issues = self.clean_title(cleaned["title"])
            if issues:
                all_issues["title"] = issues

        # Clean artist
        if "artist" in cleaned:
            cleaned["artist"], issues = self.clean_artist(cleaned["artist"])
            if issues:
                all_issues["artist"] = issues

        # Clean album
        if "album" in cleaned:
            cleaned["album"], issues = self.clean_album(cleaned["album"])
            if issues:
                all_issues["album"] = issues

        return cleaned, all_issues

    def detect_corruption_level(self, metadata: Dict[str, Any]) -> str:
        """
        Detect severity of metadata corruption

        Args:
            metadata: Song metadata dictionary

        Returns:
            Corruption level: "clean", "minor", "moderate", "severe"
        """
        issues_count = 0

        title = metadata.get("title", "")
        artist = metadata.get("artist", "")
        album = metadata.get("album", "")

        # Check for timestamps
        if self.timestamp_pattern.search(title):
            issues_count += 2
        if self.timestamp_pattern.search(artist):
            issues_count += 2
        if self.timestamp_pattern.search(album):
            issues_count += 1

        # Check for repeated track numbers
        if self.repeated_track_pattern.search(title):
            issues_count += 1

        # Check for unknown values
        if not artist or artist.lower() in ["unknown", "unknown artist"]:
            issues_count += 2
        if not album or album.lower() in ["unknown", "unknown album"]:
            issues_count += 1

        # Check for YouTube artifacts
        if self.youtube_artifacts_pattern.search(title):
            issues_count += 1

        # Check for garbage prefixes
        for garbage in self.garbage_phrases:
            if title.startswith(garbage):
                issues_count += 2
                break

        # Determine severity
        if issues_count == 0:
            return "clean"
        elif issues_count <= 2:
            return "minor"
        elif issues_count <= 4:
            return "moderate"
        else:
            return "severe"

    def analyze_library(self, songs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze entire library for metadata corruption

        Args:
            songs: List of song dictionaries

        Returns:
            Analysis report with statistics and problematic songs
        """
        report: Dict[str, Any] = {
            "total_songs": len(songs),
            "clean": 0,
            "minor": 0,
            "moderate": 0,
            "severe": 0,
            "issues_by_type": {},
            "problematic_songs": [],
        }

        for song in songs:
            level = self.detect_corruption_level(song)
            report[level] += 1  # type: ignore[operator]

            if level in ["moderate", "severe"]:
                report["problematic_songs"].append(
                    {  # type: ignore[union-attr]
                        "id": song.get("id"),
                        "title": song.get("title"),
                        "artist": song.get("artist"),
                        "corruption_level": level,
                    }
                )

        logger.info(
            f"Library analysis: {report['clean']} clean, "
            f"{report['minor']} minor, {report['moderate']} moderate, "
            f"{report['severe']} severe"
        )

        return report


def normalize_for_comparison(text: str) -> str:
    """
    Normalize text for fuzzy comparison (duplicate detection)

    Removes common variations that shouldn't affect matching:
    - Timestamps
    - Whitespace variations
    - Case differences
    - Special characters

    Args:
        text: Original text

    Returns:
        Normalized text for comparison
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove timestamps
    text = re.sub(r"_\d{8}_\d{6}", "", text)

    # Remove special characters
    text = re.sub(r"[^\w\s]", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
