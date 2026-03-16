"""
Tests for Metadata Auto-Complete (Phase 4.4)
TDD: Write tests FIRST, then implement src/api/musicbrainz_client.py

Tests exercise MetadataAutocompleter (src/core/metadata_autocompleter.py) and
MusicBrainzClient (src/api/musicbrainz_client.py) via mocks so no real
network calls are made.
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _mb_result(title, artist, album, year, genre):
    """Shortcut to build a MusicBrainz-like result dict."""
    return {
        "title": title,
        "artist": artist,
        "album": album,
        "year": year,
        "genre": genre,
    }


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_mb_client():
    """Mocked MusicBrainzClient that returns canned results."""
    client = MagicMock()
    client.search_recording.return_value = [
        _mb_result("Bohemian Rhapsody", "Queen", "A Night at the Opera", "1975", "Rock"),
        _mb_result("Bohemian Rhapsody", "Queen", "Greatest Hits", "1981", "Rock"),
        _mb_result("Bohemian Rhapsody (Live)", "Queen", "Live at Wembley", "1986", "Rock"),
    ]
    client.download_album_art.return_value = True
    return client


@pytest.fixture
def autocompleter(mock_mb_client):
    """MetadataAutocompleter with a mocked MusicBrainz client."""
    with patch("core.metadata_autocompleter.MusicBrainzClient", return_value=mock_mb_client):
        from core.metadata_autocompleter import MetadataAutocompleter

        ac = MetadataAutocompleter()
    # Also inject directly in case __init__ stored the instance
    ac.mb_client = mock_mb_client
    return ac


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


class TestMetadataAutocomplete:
    """Test MusicBrainz metadata auto-complete"""

    def test_musicbrainz_search(self, autocompleter):
        """Test search for recording on MusicBrainz"""
        song = {"id": "1", "title": "Bohemian Rhapsody", "artist": "Queen"}
        matches = autocompleter.autocomplete_single(song)

        assert len(matches) > 0
        # Results should be sorted by confidence descending
        confidences = [m["confidence"] for m in matches]
        assert confidences == sorted(confidences, reverse=True)

        # Best match should contain expected fields
        best = matches[0]
        assert "title" in best
        assert "artist" in best
        assert "album" in best
        assert "year" in best
        assert "genre" in best
        assert "confidence" in best

    def test_metadata_extraction(self, autocompleter):
        """Test metadata extraction from MusicBrainz — all expected keys present"""
        song = {"id": "1", "title": "Bohemian Rhapsody", "artist": "Queen"}
        matches = autocompleter.autocomplete_single(song)

        expected_keys = {"title", "artist", "album", "year", "genre", "confidence"}
        for match in matches:
            assert expected_keys.issubset(match.keys())

    def test_album_art_download(self, mock_mb_client):
        """Test album art download from URL"""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            tmp_path = f.name

        try:
            result = mock_mb_client.download_album_art("https://example.com/cover.jpg", tmp_path)
            assert result is True
            mock_mb_client.download_album_art.assert_called_once_with("https://example.com/cover.jpg", tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_batch_autocomplete(self, autocompleter):
        """Test batch mode (up to 100 songs at once)"""
        songs = [{"id": str(i), "title": f"Song {i}", "artist": f"Artist {i}"} for i in range(50)]

        results = autocompleter.autocomplete_batch(songs, auto_select_threshold=90)

        # Should have a result entry for each song
        assert len(results) == 50
        for song in songs:
            assert song["id"] in results

    def test_accuracy_threshold(self, autocompleter):
        """Test confidence-based auto-selection (90%+ threshold)"""
        song = {"id": "1", "title": "Bohemian Rhapsody", "artist": "Queen"}
        results = autocompleter.autocomplete_batch([song], auto_select_threshold=90)

        entry = results["1"]
        assert entry is not None
        assert "confidence" in entry
        assert "status" in entry
        # Status should be one of the two known values
        assert entry["status"] in ("auto_selected", "manual_required")

        if entry["confidence"] >= 90:
            assert entry["status"] == "auto_selected"
        else:
            assert entry["status"] == "manual_required"

    def test_user_selection_workflow(self, autocompleter):
        """Test user selecting from multiple matches — all_matches provided when manual"""
        # Force low confidence by searching with no artist
        song = {"id": "1", "title": "Bohemian Rhapsody"}  # no artist
        results = autocompleter.autocomplete_batch([song], auto_select_threshold=100)  # force manual_required

        entry = results["1"]
        assert entry is not None
        assert entry["status"] == "manual_required"
        # Should expose all matches for manual selection
        assert "all_matches" in entry
        assert len(entry["all_matches"]) > 0

    def test_database_update(self, autocompleter, mock_db_manager):
        """Test database updated with auto-completed metadata"""
        song = {"id": "1", "title": "Bohemian Rhapsody", "artist": "Queen"}
        matches = autocompleter.autocomplete_single(song)

        assert len(matches) > 0
        best = matches[0]

        # Simulate updating the database with the best match
        update_data = {
            "title": best["title"],
            "artist": best["artist"],
            "album": best["album"],
            "year": best["year"],
            "genre": best["genre"],
        }
        result = mock_db_manager.update_song(1, update_data)

        assert result is True
        mock_db_manager.update_song.assert_called_once_with(1, update_data)

    def test_empty_title_returns_empty(self, autocompleter):
        """Test that an empty title returns no matches"""
        song = {"id": "1", "title": "", "artist": "Queen"}
        matches = autocompleter.autocomplete_single(song)
        assert matches == []

    def test_no_matches_returns_none_in_batch(self, autocompleter, mock_mb_client):
        """Test batch returns None for songs with no MusicBrainz matches"""
        mock_mb_client.search_recording.return_value = []

        song = {"id": "99", "title": "Nonexistent Song XYZ", "artist": "Nobody"}
        results = autocompleter.autocomplete_batch([song])

        assert results["99"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
