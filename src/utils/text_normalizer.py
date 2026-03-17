"""Shared text normalization utilities for YouTube artifact stripping."""

from __future__ import annotations

import re

# YouTube artifacts — brackets/parentheses containing video/audio type labels
_YOUTUBE_ARTIFACTS: re.Pattern[str] = re.compile(
    r"\s*[\(\[](Official\s*)?(Music\s*)?Video[\)\]]|"
    r"\s*[\(\[]Official\s*Audio[\)\]]|"
    r"\s*[\(\[]Audio[\)\]]|"
    r"\s*[\(\[]Lyric[s]?\s*Video[\)\]]|"
    r"\s*[\(\[]Visuali[zs]er[\)\]]|"
    r"\s*[\(\[]Live[\)\]]|"
    r"\s*[\(\[]Remaster(ed)?[\)\]]|"
    r"\s*[\(\[](HD|HQ|4K|1080p)[\)\]]",
    re.IGNORECASE,
)

# Artist channel suffixes (e.g., "ArtistVEVO", "Artist - Topic")
_ARTIST_SUFFIX: re.Pattern[str] = re.compile(
    r"\s*(Official|VEVO)$|" r"\s*-\s*Topic$",
    re.IGNORECASE,
)


def strip_youtube_artifacts(text: str) -> str:
    """Remove YouTube video/audio type labels from a title string.

    Strips patterns like (Official Video), [Audio], [HD], [Remastered], etc.
    """
    return _YOUTUBE_ARTIFACTS.sub("", text).strip()


def strip_artist_suffix(artist: str) -> str:
    """Remove YouTube channel suffixes from an artist name.

    Strips patterns like 'VEVO', 'Official', '- Topic'.
    """
    return _ARTIST_SUFFIX.sub("", artist).strip()
