"""
Tests for Smart Playlist Engine
"""
import sys
import os
import tempfile
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from core.smart_playlist import (
    SmartPlaylistEngine, SmartPlaylistConfig, PlaylistRule,
    RuleOperator, RuleField, CombineMode,
    create_genre_playlist, create_decade_playlist, create_artist_playlist
)


class MockLibraryDB:
    """Mock library database for testing"""

    def __init__(self):
        self.songs = [
            {
                'id': 1, 'title': 'Bohemian Rhapsody', 'artist': 'Queen',
                'album': 'A Night at the Opera', 'genre': 'Rock',
                'year': 1975, 'play_count': 50, 'rating': 5,
                'date_added': datetime.now().isoformat(),
                'last_played': datetime.now().isoformat()
            },
            {
                'id': 2, 'title': 'Stairway to Heaven', 'artist': 'Led Zeppelin',
                'album': 'Led Zeppelin IV', 'genre': 'Rock',
                'year': 1971, 'play_count': 45, 'rating': 5,
                'date_added': (datetime.now() - timedelta(days=10)).isoformat(),
                'last_played': (datetime.now() - timedelta(days=5)).isoformat()
            },
            {
                'id': 3, 'title': 'Billie Jean', 'artist': 'Michael Jackson',
                'album': 'Thriller', 'genre': 'Pop',
                'year': 1982, 'play_count': 30, 'rating': 4,
                'date_added': (datetime.now() - timedelta(days=60)).isoformat(),
                'last_played': (datetime.now() - timedelta(days=30)).isoformat()
            },
            {
                'id': 4, 'title': 'Smells Like Teen Spirit', 'artist': 'Nirvana',
                'album': 'Nevermind', 'genre': 'Grunge Rock',
                'year': 1991, 'play_count': 25, 'rating': 4,
                'date_added': (datetime.now() - timedelta(days=90)).isoformat(),
                'last_played': None
            },
            {
                'id': 5, 'title': 'New Song', 'artist': 'Unknown Artist',
                'album': 'Unknown Album', 'genre': 'Electronic',
                'year': 2023, 'play_count': 0, 'rating': 0,
                'date_added': datetime.now().isoformat(),
                'last_played': None
            },
        ]

    def get_all_songs(self):
        return self.songs


class TestPlaylistRule:
    """Test PlaylistRule dataclass"""

    def test_create_rule(self):
        """Test creating a rule"""
        rule = PlaylistRule(
            field=RuleField.GENRE.value,
            operator=RuleOperator.CONTAINS.value,
            value="Rock"
        )
        assert rule.field == "genre"
        assert rule.operator == "contains"
        assert rule.value == "Rock"

    def test_rule_serialization(self):
        """Test rule to/from dict"""
        rule = PlaylistRule(
            field="year",
            operator="between",
            value=1980,
            value2=1989
        )

        rule_dict = rule.to_dict()
        assert rule_dict['field'] == "year"
        assert rule_dict['value'] == 1980
        assert rule_dict['value2'] == 1989

        restored = PlaylistRule.from_dict(rule_dict)
        assert restored.field == rule.field
        assert restored.value == rule.value


class TestSmartPlaylistConfig:
    """Test SmartPlaylistConfig dataclass"""

    def test_create_config(self):
        """Test creating a config"""
        config = SmartPlaylistConfig(
            name="Test Playlist",
            rules=[
                PlaylistRule("genre", "contains", "Rock")
            ],
            limit=50
        )
        assert config.name == "Test Playlist"
        assert len(config.rules) == 1
        assert config.limit == 50

    def test_config_serialization(self):
        """Test config to/from dict"""
        config = SmartPlaylistConfig(
            name="80s Rock",
            rules=[
                PlaylistRule("genre", "contains", "Rock"),
                PlaylistRule("year", "between", 1980, 1989)
            ],
            combine_mode="all",
            limit=100,
            sort_by="play_count",
            sort_ascending=False
        )

        config_dict = config.to_dict()
        assert config_dict['name'] == "80s Rock"
        assert len(config_dict['rules']) == 2

        restored = SmartPlaylistConfig.from_dict(config_dict)
        assert restored.name == config.name
        assert len(restored.rules) == len(config.rules)


class TestSmartPlaylistEngine:
    """Test SmartPlaylistEngine class"""

    @pytest.fixture
    def engine(self):
        """Create engine with mock database"""
        db = MockLibraryDB()
        return SmartPlaylistEngine(db)

    def test_create_playlist(self, engine):
        """Test creating a playlist"""
        config = SmartPlaylistConfig(
            name="Test",
            rules=[PlaylistRule("genre", "contains", "Rock")]
        )

        assert engine.create_playlist(config) is True
        assert "Test" in engine.list_playlists()

    def test_create_duplicate_fails(self, engine):
        """Test creating duplicate playlist fails"""
        config = SmartPlaylistConfig(name="Test", rules=[])

        engine.create_playlist(config)
        assert engine.create_playlist(config) is False

    def test_delete_playlist(self, engine):
        """Test deleting a playlist"""
        config = SmartPlaylistConfig(name="ToDelete", rules=[])
        engine.create_playlist(config)

        assert engine.delete_playlist("ToDelete") is True
        assert "ToDelete" not in engine.list_playlists()

    def test_generate_genre_playlist(self, engine):
        """Test generating playlist by genre"""
        config = SmartPlaylistConfig(
            name="Rock",
            rules=[PlaylistRule("genre", "contains", "Rock")]
        )

        results = engine.generate_playlist(config)

        # Should find Bohemian Rhapsody, Stairway to Heaven, Smells Like Teen Spirit
        assert len(results) == 3
        titles = [r['title'] for r in results]
        assert 'Bohemian Rhapsody' in titles
        assert 'Stairway to Heaven' in titles

    def test_generate_year_between(self, engine):
        """Test year between filter"""
        config = SmartPlaylistConfig(
            name="70s",
            rules=[PlaylistRule("year", "between", 1970, 1979)]
        )

        results = engine.generate_playlist(config)

        # Should find Bohemian Rhapsody (1975) and Stairway to Heaven (1971)
        assert len(results) == 2

    def test_combine_mode_all(self, engine):
        """Test AND combination of rules"""
        config = SmartPlaylistConfig(
            name="70s Rock",
            rules=[
                PlaylistRule("genre", "contains", "Rock"),
                PlaylistRule("year", "between", 1970, 1979)
            ],
            combine_mode="all"
        )

        results = engine.generate_playlist(config)

        # Only songs that are BOTH Rock AND from 70s
        assert len(results) == 2

    def test_combine_mode_any(self, engine):
        """Test OR combination of rules"""
        config = SmartPlaylistConfig(
            name="70s or Pop",
            rules=[
                PlaylistRule("year", "between", 1970, 1979),
                PlaylistRule("genre", "equals", "Pop")
            ],
            combine_mode="any"
        )

        results = engine.generate_playlist(config)

        # Songs from 70s OR Pop genre
        # 70s: Bohemian Rhapsody, Stairway to Heaven
        # Pop: Billie Jean
        assert len(results) == 3

    def test_limit_results(self, engine):
        """Test limiting results"""
        config = SmartPlaylistConfig(
            name="Limited Rock",
            rules=[PlaylistRule("genre", "contains", "Rock")],
            limit=2
        )

        results = engine.generate_playlist(config)
        assert len(results) == 2

    def test_sort_by_play_count(self, engine):
        """Test sorting by play count descending"""
        config = SmartPlaylistConfig(
            name="Most Played Rock",
            rules=[PlaylistRule("genre", "contains", "Rock")],
            sort_by="play_count",
            sort_ascending=False
        )

        results = engine.generate_playlist(config)

        # Should be sorted by play_count descending
        play_counts = [r['play_count'] for r in results]
        assert play_counts == sorted(play_counts, reverse=True)


class TestBuiltInPlaylists:
    """Test built-in smart playlists"""

    @pytest.fixture
    def engine(self):
        """Create engine with mock database"""
        db = MockLibraryDB()
        return SmartPlaylistEngine(db)

    def test_get_recently_added(self, engine):
        """Test recently added playlist"""
        results = engine.get_recently_added(days=30)

        # Should include songs added in last 30 days
        # Bohemian Rhapsody, Stairway to Heaven, New Song
        assert len(results) >= 2

    def test_get_most_played(self, engine):
        """Test most played playlist"""
        results = engine.get_most_played(limit=3)

        assert len(results) == 3
        # First should be Bohemian Rhapsody (50 plays)
        assert results[0]['title'] == 'Bohemian Rhapsody'

    def test_get_never_played(self, engine):
        """Test never played playlist"""
        results = engine.get_never_played()

        # Should include New Song (play_count=0)
        titles = [r['title'] for r in results]
        assert 'New Song' in titles

    def test_get_by_genre(self, engine):
        """Test genre filter"""
        results = engine.get_by_genre("Pop")

        assert len(results) == 1
        assert results[0]['title'] == 'Billie Jean'

    def test_get_by_decade(self, engine):
        """Test decade filter"""
        results = engine.get_by_decade(1980)

        # 80s songs: Billie Jean (1982)
        assert len(results) == 1
        assert results[0]['year'] == 1982

    def test_get_top_rated(self, engine):
        """Test top rated filter"""
        results = engine.get_top_rated(min_rating=5)

        # Should include Bohemian Rhapsody and Stairway to Heaven (both 5 stars)
        assert len(results) == 2


class TestPersistence:
    """Test saving/loading playlists"""

    @pytest.fixture
    def engine(self):
        """Create engine with mock database"""
        return SmartPlaylistEngine(MockLibraryDB())

    def test_save_and_load(self, engine):
        """Test saving and loading playlists"""
        # Create some playlists
        engine.create_playlist(SmartPlaylistConfig(
            name="Rock Classics",
            rules=[PlaylistRule("genre", "contains", "Rock")]
        ))
        engine.create_playlist(SmartPlaylistConfig(
            name="80s Pop",
            rules=[
                PlaylistRule("genre", "contains", "Pop"),
                PlaylistRule("year", "between", 1980, 1989)
            ]
        ))

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            assert engine.save_to_json(filepath) is True

            # Create new engine and load
            new_engine = SmartPlaylistEngine(MockLibraryDB())
            assert new_engine.load_from_json(filepath) is True

            # Verify playlists loaded
            assert "Rock Classics" in new_engine.list_playlists()
            assert "80s Pop" in new_engine.list_playlists()

            # Verify rules preserved
            rock_config = new_engine.get_playlist("Rock Classics")
            assert len(rock_config.rules) == 1
            assert rock_config.rules[0].value == "Rock"

        finally:
            os.unlink(filepath)


class TestConvenienceFunctions:
    """Test convenience functions for creating playlist configs"""

    def test_create_genre_playlist(self):
        """Test genre playlist factory"""
        config = create_genre_playlist("Jazz")

        assert config.name == "Jazz Music"
        assert len(config.rules) == 1
        assert config.rules[0].field == "genre"
        assert config.rules[0].value == "Jazz"

    def test_create_decade_playlist(self):
        """Test decade playlist factory"""
        config = create_decade_playlist(1990)

        assert config.name == "The 1990s"
        assert len(config.rules) == 1
        assert config.rules[0].operator == "between"
        assert config.rules[0].value == 1990
        assert config.rules[0].value2 == 1999

    def test_create_artist_playlist(self):
        """Test artist playlist factory"""
        config = create_artist_playlist("The Beatles")

        assert config.name == "Best of The Beatles"
        assert config.rules[0].value == "The Beatles"
        assert config.sort_by == "play_count"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
