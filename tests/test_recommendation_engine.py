"""
Tests for RecommendationEngine - Song Recommendations
Tests scoring, filtering, edge cases, and playlist generation.
"""

from unittest.mock import MagicMock

import pytest

from src.core.recommendation_engine import RecommendationEngine

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Create a mock DatabaseManager."""
    return MagicMock()


@pytest.fixture
def engine(mock_db):
    """Create a RecommendationEngine with a mocked DB."""
    return RecommendationEngine(mock_db)


@pytest.fixture
def library_songs():
    """A small library of songs for testing."""
    return [
        {
            "id": 1,
            "title": "Clavaito",
            "artist": "Chanel",
            "album": "Agua",
            "genre": "Latin Pop",
            "year": 2024,
        },
        {
            "id": 2,
            "title": "SloMo",
            "artist": "Chanel",
            "album": "Agua",
            "genre": "Latin Pop",
            "year": 2022,
        },
        {
            "id": 3,
            "title": "Despacito",
            "artist": "Luis Fonsi",
            "album": "Vida",
            "genre": "Latin Pop",
            "year": 2017,
        },
        {
            "id": 4,
            "title": "Bohemian Rhapsody",
            "artist": "Queen",
            "album": "A Night at the Opera",
            "genre": "Rock",
            "year": 1975,
        },
        {
            "id": 5,
            "title": "Somebody to Love",
            "artist": "Queen",
            "album": "A Day at the Races",
            "genre": "Rock",
            "year": 1976,
        },
        {
            "id": 6,
            "title": "Stairway to Heaven",
            "artist": "Led Zeppelin",
            "album": "IV",
            "genre": "Rock",
            "year": 1971,
        },
    ]


@pytest.fixture
def current_song():
    """The song we are getting recommendations for."""
    return {
        "id": 1,
        "title": "Clavaito",
        "artist": "Chanel",
        "album": "Agua",
        "genre": "Latin Pop",
        "year": 2024,
    }


# ---------------------------------------------------------------------------
# get_recommendations
# ---------------------------------------------------------------------------


class TestGetRecommendations:

    def test_empty_library_returns_empty(self, engine, mock_db, current_song):
        """No songs in library -> no recommendations."""
        mock_db.get_all_songs.return_value = []
        result = engine.get_recommendations(current_song)
        assert result == []

    def test_none_current_song_returns_empty(self, engine):
        """Passing None as current song returns empty list."""
        assert engine.get_recommendations(None) == []
        assert engine.get_recommendations({}) == []

    def test_single_song_library_same_as_current(self, engine, mock_db, current_song):
        """Library contains only the current song -> excluded -> no results."""
        mock_db.get_all_songs.return_value = [current_song]
        result = engine.get_recommendations(current_song)
        assert result == []

    def test_same_artist_scores_highest(self, engine, mock_db, library_songs, current_song):
        """Songs by the same artist should rank highest."""
        mock_db.get_all_songs.return_value = library_songs
        recs = engine.get_recommendations(current_song, limit=10)

        # SloMo by Chanel (same artist+album+genre+year-close) should be first
        assert len(recs) > 0
        assert recs[0]["artist"] == "Chanel"
        assert recs[0]["id"] == 2

    def test_excludes_specified_ids(self, engine, mock_db, library_songs, current_song):
        """Songs in exclude_ids should not appear."""
        mock_db.get_all_songs.return_value = library_songs
        recs = engine.get_recommendations(current_song, exclude_ids=[2])
        rec_ids = [r["id"] for r in recs]
        assert 2 not in rec_ids
        # Current song (id=1) is also excluded automatically
        assert 1 not in rec_ids

    def test_limit_respected(self, engine, mock_db, library_songs, current_song):
        """Returned list should not exceed the limit."""
        mock_db.get_all_songs.return_value = library_songs
        recs = engine.get_recommendations(current_song, limit=2)
        assert len(recs) <= 2

    def test_zero_score_songs_excluded(self, engine, mock_db, current_song):
        """Songs with no metadata overlap should not appear."""
        mock_db.get_all_songs.return_value = [
            {
                "id": 99,
                "title": "Random",
                "artist": "Nobody",
                "album": "Nothing",
                "genre": "Noise",
                "year": 1900,
            }
        ]
        recs = engine.get_recommendations(current_song)
        assert recs == []

    def test_year_scoring_within_five_years(self, engine, mock_db):
        """Year within 5 years adds 2 points; within 10 adds 1."""
        current = {
            "id": 10,
            "title": "A",
            "artist": "X",
            "album": "B",
            "genre": "Pop",
            "year": 2020,
        }
        songs = [
            # Same genre (+3), year diff=3 (+2) => 5
            {"id": 11, "title": "B", "artist": "Y", "album": "C", "genre": "Pop", "year": 2023},
            # Same genre (+3), year diff=8 (+1) => 4
            {"id": 12, "title": "C", "artist": "Z", "album": "D", "genre": "Pop", "year": 2012},
        ]
        mock_db.get_all_songs.return_value = songs
        recs = engine.get_recommendations(current, limit=10)
        assert len(recs) == 2
        # Higher-scored song (id=11, 5 pts) must come first
        assert recs[0]["id"] == 11

    def test_handles_missing_metadata_gracefully(self, engine, mock_db):
        """Songs with None/empty fields should not crash the engine."""
        current = {"id": 1, "title": "A", "artist": None, "album": None, "genre": None, "year": None}
        songs = [
            {"id": 2, "title": "B", "artist": None, "album": None, "genre": None, "year": None},
        ]
        mock_db.get_all_songs.return_value = songs
        # Should not raise, but score=0 means no recommendations
        recs = engine.get_recommendations(current)
        assert recs == []


# ---------------------------------------------------------------------------
# get_random_from_genre / get_random_from_artist
# ---------------------------------------------------------------------------


class TestGenreAndArtistRandom:

    def test_random_from_genre_filters_correctly(self, engine, mock_db, library_songs):
        mock_db.get_all_songs.return_value = library_songs
        recs = engine.get_random_from_genre("Rock", limit=10)
        assert all(r["genre"] == "Rock" for r in recs)
        assert len(recs) == 3  # Queen x2 + Led Zeppelin

    def test_random_from_genre_empty_string(self, engine):
        assert engine.get_random_from_genre("") == []

    def test_random_from_artist(self, engine, mock_db, library_songs):
        mock_db.get_all_songs.return_value = library_songs
        recs = engine.get_random_from_artist("Queen", limit=5)
        assert all(r["artist"] == "Queen" for r in recs)
        assert len(recs) == 2

    def test_random_from_artist_empty_string(self, engine):
        assert engine.get_random_from_artist("") == []


# ---------------------------------------------------------------------------
# get_discover_playlist
# ---------------------------------------------------------------------------


class TestDiscoverPlaylist:

    def test_discover_empty_library(self, engine, mock_db):
        mock_db.get_all_songs.return_value = []
        assert engine.get_discover_playlist() == []

    def test_discover_respects_limit(self, engine, mock_db, library_songs):
        mock_db.get_all_songs.return_value = library_songs
        result = engine.get_discover_playlist(limit=3)
        assert len(result) <= 3

    def test_discover_includes_multiple_genres(self, engine, mock_db, library_songs):
        """Discover playlist should pull from different genres."""
        mock_db.get_all_songs.return_value = library_songs
        result = engine.get_discover_playlist(limit=20)
        genres = {(r.get("genre") or "Unknown").lower() for r in result}
        # Library has Latin Pop and Rock
        assert len(genres) >= 2
