"""
LRC Parser - Synchronized Lyrics Support

Parses LRC (LyRiCs) format for synchronized lyrics display.
Supports standard LRC format with timestamps.

LRC Format Example:
    [00:12.00]Line 1 lyrics
    [00:15.50]Line 2 lyrics
    [00:18.25]Line 3 lyrics

Features:
- Parse LRC files and strings
- Extract timed lyrics lines
- Find current line by position
- Support for metadata tags ([ar:Artist], [ti:Title], etc.)
- Generate LRC from plain lyrics with timing

Created: December 12, 2025
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LRCLine:
    """Single line of synchronized lyrics"""

    time_ms: int  # Timestamp in milliseconds
    text: str  # Lyrics text

    @property
    def time_seconds(self) -> float:
        """Get time in seconds"""
        return self.time_ms / 1000.0

    @property
    def time_formatted(self) -> str:
        """Get time as [MM:SS.xx] format"""
        total_seconds = self.time_ms / 1000.0
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"[{minutes:02d}:{seconds:05.2f}]"

    def __str__(self) -> str:
        return f"{self.time_formatted}{self.text}"


@dataclass
class LRCMetadata:
    """LRC file metadata"""

    artist: Optional[str] = None
    title: Optional[str] = None
    album: Optional[str] = None
    author: Optional[str] = None  # Lyrics author
    length: Optional[str] = None  # Song length
    offset: int = 0  # Timing offset in ms


class LRCParser:
    """
    Parser for LRC (synchronized lyrics) format

    Usage:
        parser = LRCParser()

        # Parse LRC content
        lines, metadata = parser.parse(lrc_content)

        # Find current line for playback position
        current_line = parser.get_current_line(lines, position_ms=45000)

        # Generate LRC from plain text
        lrc_content = parser.generate_lrc(plain_lyrics, timings)
    """

    # Regex patterns
    TIME_PATTERN = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\]")
    METADATA_PATTERN = re.compile(r"\[([a-z]+):(.*?)\]", re.IGNORECASE)

    def __init__(self) -> None:
        logger.debug("LRCParser initialized")

    def parse(self, content: str) -> Tuple[List[LRCLine], LRCMetadata]:
        """
        Parse LRC content into structured data

        Args:
            content: LRC file content as string

        Returns:
            Tuple of (list of LRCLine, LRCMetadata)
        """
        lines: List[LRCLine] = []
        metadata = LRCMetadata()

        if not content:
            return lines, metadata

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check for metadata tags first
            meta_match = self.METADATA_PATTERN.match(line)
            if meta_match and not self.TIME_PATTERN.match(line):
                tag, value = meta_match.groups()
                self._parse_metadata_tag(metadata, tag.lower(), value.strip())
                continue

            # Parse timed lyrics
            parsed_lines = self._parse_timed_line(line)
            lines.extend(parsed_lines)

        # Sort by timestamp
        lines.sort(key=lambda x: x.time_ms)

        # Apply offset if specified
        if metadata.offset != 0:
            for lrc_line in lines:
                lrc_line.time_ms += metadata.offset

        logger.debug(f"Parsed {len(lines)} lyrics lines")
        return lines, metadata

    def _parse_metadata_tag(self, metadata: LRCMetadata, tag: str, value: str) -> None:
        """Parse metadata tag and update metadata object"""
        tag_mapping = {
            "ar": "artist",
            "ti": "title",
            "al": "album",
            "au": "author",
            "length": "length",
            "offset": "offset",
        }

        if tag in tag_mapping:
            attr = tag_mapping[tag]
            if attr == "offset":
                try:
                    metadata.offset = int(value)
                except ValueError:
                    pass
            else:
                setattr(metadata, attr, value)

    def _parse_timed_line(self, line: str) -> List[LRCLine]:
        """
        Parse a single line which may have multiple timestamps

        Example: [00:12.00][00:24.00]Repeated lyrics
        """
        result: list[LRCLine] = []

        # Find all timestamps
        timestamps = []
        for match in self.TIME_PATTERN.finditer(line):
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            centiseconds = match.group(3)

            # Handle both 2-digit and 3-digit centiseconds
            if len(centiseconds) == 2:
                ms = int(centiseconds) * 10
            else:
                ms = int(centiseconds)

            total_ms = (minutes * 60 + seconds) * 1000 + ms
            timestamps.append(total_ms)

        if not timestamps:
            return result  # type: ignore[return-value]

        # Get text after all timestamps
        text = self.TIME_PATTERN.sub("", line).strip()

        # Create LRCLine for each timestamp
        for time_ms in timestamps:
            result.append(LRCLine(time_ms=time_ms, text=text))  # type: ignore[arg-type]

        return result  # type: ignore[return-value]

    def parse_file(self, filepath: str) -> Tuple[List[LRCLine], LRCMetadata]:
        """
        Parse LRC file from disk

        Args:
            filepath: Path to .lrc file

        Returns:
            Tuple of (list of LRCLine, LRCMetadata)
        """
        path = Path(filepath)

        if not path.exists():
            logger.warning(f"LRC file not found: {filepath}")
            return [], LRCMetadata()

        # Try different encodings
        for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin-1"]:
            try:
                content = path.read_text(encoding=encoding)
                return self.parse(content)
            except UnicodeDecodeError:
                continue

        logger.error(f"Failed to decode LRC file: {filepath}")
        return [], LRCMetadata()

    def get_current_line(self, lines: List[LRCLine], position_ms: int) -> Optional[LRCLine]:
        """
        Get the current lyrics line for a playback position

        Args:
            lines: List of LRCLine objects
            position_ms: Current playback position in milliseconds

        Returns:
            Current LRCLine or None if before first line
        """
        if not lines:
            return None

        current = None
        for line in lines:
            if line.time_ms <= position_ms:
                current = line
            else:
                break

        return current

    def get_current_index(self, lines: List[LRCLine], position_ms: int) -> int:
        """
        Get the index of current lyrics line

        Args:
            lines: List of LRCLine objects
            position_ms: Current playback position in milliseconds

        Returns:
            Index of current line, or -1 if before first line
        """
        if not lines:
            return -1

        current_idx = -1
        for i, line in enumerate(lines):
            if line.time_ms <= position_ms:
                current_idx = i
            else:
                break

        return current_idx

    def get_surrounding_lines(
        self, lines: List[LRCLine], position_ms: int, before: int = 3, after: int = 5
    ) -> Tuple[List[LRCLine], int]:
        """
        Get lines surrounding current position for display

        Args:
            lines: List of LRCLine objects
            position_ms: Current playback position
            before: Number of lines to show before current
            after: Number of lines to show after current

        Returns:
            Tuple of (list of surrounding lines, index of current line in that list)
        """
        current_idx = self.get_current_index(lines, position_ms)

        if current_idx < 0:
            # Before first line - show first few lines
            return lines[: before + after + 1], -1

        start = max(0, current_idx - before)
        end = min(len(lines), current_idx + after + 1)

        surrounding = lines[start:end]
        relative_idx = current_idx - start

        return surrounding, relative_idx

    def generate_lrc(
        self, lyrics: str, timings: Optional[List[int]] = None, metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate LRC content from plain lyrics and timings

        Args:
            lyrics: Plain text lyrics (one line per verse)
            timings: List of timestamps in milliseconds (same length as lines)
            metadata: Optional metadata dict with keys: artist, title, album

        Returns:
            LRC formatted string
        """
        lines = [l.strip() for l in lyrics.split("\n") if l.strip()]

        result = []

        # Add metadata header
        if metadata:
            if "title" in metadata:
                result.append(f"[ti:{metadata['title']}]")
            if "artist" in metadata:
                result.append(f"[ar:{metadata['artist']}]")
            if "album" in metadata:
                result.append(f"[al:{metadata['album']}]")
            result.append("")  # Empty line after metadata

        # Add timed lyrics
        if timings and len(timings) == len(lines):
            for i, line in enumerate(lines):
                lrc_line = LRCLine(time_ms=timings[i], text=line)
                result.append(str(lrc_line))
        else:
            # No timings - generate with 5-second intervals (placeholder)
            for i, line in enumerate(lines):
                time_ms = i * 5000  # 5 seconds per line
                lrc_line = LRCLine(time_ms=time_ms, text=line)
                result.append(str(lrc_line))

        return "\n".join(result)

    def find_lrc_file(self, audio_path: str) -> Optional[str]:
        """
        Find LRC file for an audio file

        Searches for:
        1. Same name with .lrc extension
        2. Same name in a 'lyrics' subfolder

        Args:
            audio_path: Path to audio file

        Returns:
            Path to LRC file if found, None otherwise
        """
        audio = Path(audio_path)

        # Same directory, same name
        lrc_path = audio.with_suffix(".lrc")
        if lrc_path.exists():
            return str(lrc_path)

        # Lyrics subfolder
        lyrics_folder = audio.parent / "lyrics"
        lrc_in_folder = lyrics_folder / f"{audio.stem}.lrc"
        if lrc_in_folder.exists():
            return str(lrc_in_folder)

        # Case-insensitive search
        for ext in [".lrc", ".LRC", ".Lrc"]:
            lrc_path = audio.with_suffix(ext)
            if lrc_path.exists():
                return str(lrc_path)

        return None


# Convenience functions
def parse_lrc(content: str) -> Tuple[List[LRCLine], LRCMetadata]:
    """Parse LRC content - convenience function"""
    return LRCParser().parse(content)


def load_lrc(filepath: str) -> Tuple[List[LRCLine], LRCMetadata]:
    """Load and parse LRC file - convenience function"""
    return LRCParser().parse_file(filepath)
