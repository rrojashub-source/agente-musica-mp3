"""
Tests for MetadataCleaner - Intelligent metadata normalization

Tests cover:
- Cleaning title fields (timestamps, track numbers, YouTube artifacts)
- Cleaning artist fields (VEVO, Official, Topic suffixes)
- Cleaning album fields (timestamps, unknown values)
- Batch metadata cleaning
- Corruption level detection
- Library analysis
- Edge cases (empty strings, None values)
- The normalize_for_comparison standalone function
"""

import pytest

from core.metadata_cleaner import MetadataCleaner, normalize_for_comparison


@pytest.fixture
def cleaner():
    return MetadataCleaner()


# ─── Tests: clean_title ────────────────────────────────────────────────


class TestCleanTitle:
    def test_remove_timestamp_suffix(self, cleaner):
        """Timestamps like _20251013_232019 are removed from titles"""
        title, issues = cleaner.clean_title("Song Name_20251013_232019")
        assert title == "Song Name"
        assert "timestamp_suffix" in issues

    def test_remove_repeated_track_numbers(self, cleaner):
        """Repeated track numbers like '00 - 00 - ' are removed"""
        title, issues = cleaner.clean_title("00 - 00 - Song Title")
        assert title == "Song Title"
        assert "repeated_track_numbers" in issues

    def test_remove_youtube_artifacts(self, cleaner):
        """YouTube markers like [Official Video] are stripped"""
        title, issues = cleaner.clean_title("Song Name [Official Video]")
        assert title == "Song Name"
        assert "youtube_artifacts" in issues

    def test_remove_multiple_youtube_artifacts(self, cleaner):
        """Multiple YouTube artifacts are all removed"""
        title, issues = cleaner.clean_title("Song (Official Audio) [HD]")
        assert "Official Audio" not in title
        assert "HD" not in title
        assert "youtube_artifacts" in issues

    def test_strip_artist_prefix_when_known(self, cleaner):
        """'Artist - Title' prefix is removed when artist is provided"""
        title, issues = cleaner.clean_title("Queen - Bohemian Rhapsody", artist="Queen")
        assert title == "Bohemian Rhapsody"
        assert "artist_prefix" in issues

    def test_remove_garbage_prefix(self, cleaner):
        """Garbage prefixes like 'Unknown Artist - Unknown Album - ' are removed"""
        title, issues = cleaner.clean_title("Unknown Artist - Unknown Album - Real Song Title")
        assert title == "Real Song Title"
        assert "garbage_prefix" in issues

    def test_empty_title_returns_unknown(self, cleaner):
        """Empty or None title returns 'Unknown' with issue flag"""
        title, issues = cleaner.clean_title("")
        assert title == "Unknown"
        assert "empty_title" in issues

        title2, issues2 = cleaner.clean_title(None)
        assert title2 == "Unknown"
        assert "empty_title" in issues2

    def test_clean_title_unchanged(self, cleaner):
        """Already clean title is returned unchanged with no issues"""
        title, issues = cleaner.clean_title("Perfectly Fine Title")
        assert title == "Perfectly Fine Title"
        assert issues == []


# ─── Tests: clean_artist ───────────────────────────────────────────────


class TestCleanArtist:
    def test_remove_vevo_suffix(self, cleaner):
        """VEVO suffix is removed from artist names"""
        artist, issues = cleaner.clean_artist("ArtistVEVO")
        assert "VEVO" not in artist
        assert "youtube_channel_suffix" in issues

    def test_remove_topic_suffix(self, cleaner):
        """' - Topic' suffix is removed from artist names"""
        artist, issues = cleaner.clean_artist("Queen - Topic")
        assert artist == "Queen"
        assert "youtube_channel_suffix" in issues

    def test_unknown_artist_normalized(self, cleaner):
        """Unknown/empty artist is normalized to 'Unknown Artist'"""
        artist, issues = cleaner.clean_artist("unknown")
        assert artist == "Unknown Artist"
        assert "missing_artist" in issues

        artist2, issues2 = cleaner.clean_artist("")
        assert artist2 == "Unknown Artist"
        assert "missing_artist" in issues2

        artist3, issues3 = cleaner.clean_artist(None)
        assert artist3 == "Unknown Artist"
        assert "missing_artist" in issues3

    def test_clean_artist_unchanged(self, cleaner):
        """Already clean artist name is returned unchanged"""
        artist, issues = cleaner.clean_artist("Pink Floyd")
        assert artist == "Pink Floyd"
        assert issues == []


# ─── Tests: clean_album ────────────────────────────────────────────────


class TestCleanAlbum:
    def test_remove_timestamp_from_album(self, cleaner):
        """Timestamps are removed from album names"""
        album, issues = cleaner.clean_album("Album_20251013_232019")
        assert album == "Album"
        assert "timestamp_suffix" in issues

    def test_unknown_album_normalized(self, cleaner):
        """Unknown/empty album is normalized to 'Unknown Album'"""
        album, issues = cleaner.clean_album("unknown album")
        assert album == "Unknown Album"
        assert "missing_album" in issues

    def test_clean_album_unchanged(self, cleaner):
        """Already clean album is returned unchanged"""
        album, issues = cleaner.clean_album("The Dark Side of the Moon")
        assert album == "The Dark Side of the Moon"
        assert issues == []


# ─── Tests: clean_metadata (batch) ─────────────────────────────────────


class TestCleanMetadata:
    def test_clean_all_fields(self, cleaner):
        """clean_metadata processes title, artist, and album together"""
        metadata = {"title": "Song_20251013_232019 [Official Video]", "artist": "ArtistVEVO", "album": "unknown album"}
        cleaned, all_issues = cleaner.clean_metadata(metadata)

        assert cleaned["title"] == "Song"
        assert "VEVO" not in cleaned["artist"]
        assert cleaned["album"] == "Unknown Album"
        assert "title" in all_issues
        assert "artist" in all_issues
        assert "album" in all_issues

    def test_clean_metadata_preserves_extra_fields(self, cleaner):
        """Fields not cleaned (e.g. duration, id) are preserved"""
        metadata = {"id": 42, "title": "Good Title", "artist": "Good Artist", "album": "Good Album", "duration": 300}
        cleaned, all_issues = cleaner.clean_metadata(metadata)
        assert cleaned["id"] == 42
        assert cleaned["duration"] == 300
        assert all_issues == {}


# ─── Tests: detect_corruption_level ────────────────────────────────────


class TestCorruptionLevel:
    def test_clean_metadata_detected(self, cleaner):
        """Clean metadata is classified as 'clean'"""
        metadata = {"title": "Good Song", "artist": "Good Artist", "album": "Good Album"}
        assert cleaner.detect_corruption_level(metadata) == "clean"

    def test_minor_corruption_detected(self, cleaner):
        """Single YouTube artifact is classified as minor"""
        metadata = {"title": "Song [Official Video]", "artist": "Artist", "album": "Album"}
        assert cleaner.detect_corruption_level(metadata) == "minor"

    def test_severe_corruption_detected(self, cleaner):
        """Multiple issues (timestamp + unknown artist + garbage prefix) is severe"""
        metadata = {"title": "Unknown Artist - Unknown Album - Song_20251013_232019", "artist": "", "album": "unknown"}
        level = cleaner.detect_corruption_level(metadata)
        assert level in ("moderate", "severe")


# ─── Tests: analyze_library ────────────────────────────────────────────


class TestAnalyzeLibrary:
    def test_analyze_library_counts(self, cleaner):
        """Library analysis returns correct counts per corruption level"""
        songs = [
            {"id": 1, "title": "Good Song", "artist": "Artist", "album": "Album"},
            {"id": 2, "title": "Song [Official Video]", "artist": "Artist", "album": "Album"},
            {"id": 3, "title": "Unknown Artist - Song_20251013_232019", "artist": "", "album": "unknown"},
        ]
        report = cleaner.analyze_library(songs)

        assert report["total_songs"] == 3
        assert report["clean"] >= 1
        # Problematic songs list should contain moderate/severe entries
        assert isinstance(report["problematic_songs"], list)

    def test_analyze_empty_library(self, cleaner):
        """Empty library analysis returns zeros"""
        report = cleaner.analyze_library([])
        assert report["total_songs"] == 0
        assert report["clean"] == 0
        assert report["problematic_songs"] == []


# ─── Tests: normalize_for_comparison ───────────────────────────────────


class TestNormalizeForComparison:
    def test_removes_timestamps(self):
        assert "song" in normalize_for_comparison("Song_20251013_232019")
        assert "20251013" not in normalize_for_comparison("Song_20251013_232019")

    def test_lowercases(self):
        assert normalize_for_comparison("HELLO") == "hello"

    def test_removes_special_characters(self):
        result = normalize_for_comparison("Hello, World! (feat. Artist)")
        assert "," not in result
        assert "!" not in result
        assert "(" not in result

    def test_normalizes_whitespace(self):
        assert normalize_for_comparison("  multiple   spaces  ") == "multiple spaces"

    def test_empty_input(self):
        assert normalize_for_comparison("") == ""
        assert normalize_for_comparison(None) == ""
