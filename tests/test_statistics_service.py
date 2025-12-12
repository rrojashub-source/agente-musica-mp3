"""
Tests for Statistics Service

Tests cover:
- Library overview statistics
- Top charts (artists, songs, genres)
- Decade breakdown
- Quality distribution
- Play recording
"""
import pytest
import tempfile
import os
from pathlib import Path

from database.manager import DatabaseManager
from services.statistics_service import StatisticsService, ListeningStats


@pytest.fixture
def temp_db():
    """Create temporary database with test data"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_stats.db")

    db = DatabaseManager(db_path)

    # Add test songs
    test_songs = [
        {'title': 'Song 1', 'artist': 'Artist A', 'album': 'Album 1', 'year': 2020,
         'genre': 'Rock', 'duration': 180, 'bitrate': 320, 'file_path': '/test/song1.mp3'},
        {'title': 'Song 2', 'artist': 'Artist A', 'album': 'Album 1', 'year': 2020,
         'genre': 'Rock', 'duration': 200, 'bitrate': 256, 'file_path': '/test/song2.mp3'},
        {'title': 'Song 3', 'artist': 'Artist B', 'album': 'Album 2', 'year': 2015,
         'genre': 'Pop', 'duration': 210, 'bitrate': 192, 'file_path': '/test/song3.mp3'},
        {'title': 'Song 4', 'artist': 'Artist B', 'album': 'Album 2', 'year': 2015,
         'genre': 'Pop', 'duration': 190, 'bitrate': 320, 'file_path': '/test/song4.mp3'},
        {'title': 'Song 5', 'artist': 'Artist C', 'album': 'Album 3', 'year': 1985,
         'genre': 'Jazz', 'duration': 300, 'bitrate': 128, 'file_path': '/test/song5.mp3'},
    ]

    for song in test_songs:
        db.add_song(song)

    # Add some play counts
    db.execute_query("UPDATE songs SET play_count = 10 WHERE title = 'Song 1'")
    db.execute_query("UPDATE songs SET play_count = 5 WHERE title = 'Song 2'")
    db.execute_query("UPDATE songs SET play_count = 3 WHERE title = 'Song 3'")

    yield db

    # Cleanup
    db.close()
    import shutil
    shutil.rmtree(temp_dir)


class TestLibraryOverview:
    """Test library overview statistics"""

    def test_total_songs(self, temp_db):
        """Should count total songs"""
        stats = StatisticsService(temp_db)
        overview = stats.get_library_overview()

        assert overview['total_songs'] == 5

    def test_unique_artists(self, temp_db):
        """Should count unique artists"""
        stats = StatisticsService(temp_db)
        overview = stats.get_library_overview()

        assert overview['total_artists'] == 3  # A, B, C

    def test_unique_albums(self, temp_db):
        """Should count unique albums"""
        stats = StatisticsService(temp_db)
        overview = stats.get_library_overview()

        assert overview['total_albums'] == 3

    def test_unique_genres(self, temp_db):
        """Should count unique genres"""
        stats = StatisticsService(temp_db)
        overview = stats.get_library_overview()

        assert overview['total_genres'] == 3  # Rock, Pop, Jazz

    def test_total_plays(self, temp_db):
        """Should sum play counts"""
        stats = StatisticsService(temp_db)
        overview = stats.get_library_overview()

        assert overview['total_plays'] == 18  # 10 + 5 + 3


class TestTopCharts:
    """Test top charts functionality"""

    def test_top_artists(self, temp_db):
        """Should rank artists by plays"""
        stats = StatisticsService(temp_db)
        top = stats.get_top_artists(limit=3)

        assert len(top) == 3
        # Artist A has most plays (10 + 5 = 15)
        assert top[0]['artist'] == 'Artist A'
        assert top[0]['total_plays'] == 15

    def test_top_songs(self, temp_db):
        """Should rank songs by play count"""
        stats = StatisticsService(temp_db)
        top = stats.get_top_songs(limit=3)

        assert len(top) == 3
        assert top[0]['title'] == 'Song 1'
        assert top[0]['play_count'] == 10

    def test_top_genres(self, temp_db):
        """Should rank genres by song count"""
        stats = StatisticsService(temp_db)
        top = stats.get_top_genres(limit=3)

        assert len(top) == 3
        # Rock and Pop have 2 songs each
        assert top[0]['song_count'] == 2

    def test_empty_database(self):
        """Should handle empty database"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "empty.db")
        db = DatabaseManager(db_path)

        stats = StatisticsService(db)
        overview = stats.get_library_overview()

        assert overview.get('total_songs', 0) == 0

        db.close()
        import shutil
        shutil.rmtree(temp_dir)


class TestDecadeBreakdown:
    """Test decade breakdown functionality"""

    def test_decades(self, temp_db):
        """Should group by decade"""
        stats = StatisticsService(temp_db)
        decades = stats.get_decade_breakdown()

        assert len(decades) == 3  # 2020s, 2010s, 1980s

        # Check we have expected decades
        decades_years = [d['decade_year'] for d in decades]
        assert 2020 in decades_years
        assert 2010 in decades_years
        assert 1980 in decades_years


class TestQualityDistribution:
    """Test quality distribution statistics"""

    def test_bitrate_groups(self, temp_db):
        """Should group by bitrate quality"""
        stats = StatisticsService(temp_db)
        quality = stats.get_bitrate_distribution()

        assert len(quality) > 0

        # Should have high quality (320 kbps)
        qualities = [q['quality'] for q in quality]
        assert any('High' in q for q in qualities)


class TestMetadataCompleteness:
    """Test metadata completeness statistics"""

    def test_completeness(self, temp_db):
        """Should calculate field completeness"""
        stats = StatisticsService(temp_db)
        meta = stats.get_metadata_completeness()

        assert meta['total'] == 5

        # All songs have artist
        assert meta['fields']['artist']['percentage'] == 100.0


class TestPlayRecording:
    """Test play event recording"""

    def test_record_play_increments_count(self, temp_db):
        """Recording play should increment play_count"""
        stats = StatisticsService(temp_db)

        # Get song 5 (no plays yet)
        song_before = temp_db.fetch_one("SELECT play_count FROM songs WHERE title = 'Song 5'")
        assert song_before['play_count'] == 0

        # Record play
        song = temp_db.fetch_one("SELECT id FROM songs WHERE title = 'Song 5'")
        stats.record_play(song['id'])

        # Check incremented
        song_after = temp_db.fetch_one("SELECT play_count FROM songs WHERE title = 'Song 5'")
        assert song_after['play_count'] == 1

    def test_record_play_updates_last_played(self, temp_db):
        """Recording play should update last_played"""
        stats = StatisticsService(temp_db)

        song = temp_db.fetch_one("SELECT id FROM songs WHERE title = 'Song 5'")
        stats.record_play(song['id'])

        song_after = temp_db.fetch_one("SELECT last_played FROM songs WHERE title = 'Song 5'")
        assert song_after['last_played'] is not None


class TestRecentActivity:
    """Test recent activity functions"""

    def test_recently_added(self, temp_db):
        """Should return recently added songs"""
        stats = StatisticsService(temp_db)
        recent = stats.get_recently_added(limit=3)

        assert len(recent) == 3
        # All should have added_date
        assert all('added_date' in s for s in recent)

    def test_recently_played(self, temp_db):
        """Should return recently played songs"""
        stats = StatisticsService(temp_db)

        # Record some plays first
        song = temp_db.fetch_one("SELECT id FROM songs WHERE title = 'Song 5'")
        stats.record_play(song['id'])

        recent = stats.get_recently_played(limit=3)

        # Should include Song 5 now
        titles = [s['title'] for s in recent]
        assert 'Song 5' in titles


class TestListeningStats:
    """Test ListeningStats dataclass"""

    def test_total_hours(self):
        """Should calculate hours from seconds"""
        stats = ListeningStats(total_duration_seconds=7200)
        assert stats.total_hours == 2.0

    def test_total_days(self):
        """Should calculate days from seconds"""
        stats = ListeningStats(total_duration_seconds=86400)
        assert stats.total_days == 1.0


class TestSummaryStats:
    """Test summary statistics aggregation"""

    def test_get_summary(self, temp_db):
        """Should return comprehensive summary"""
        stats = StatisticsService(temp_db)
        summary = stats.get_summary_stats()

        assert 'overview' in summary
        assert 'top_artists' in summary
        assert 'top_songs' in summary
        assert 'top_genres' in summary
        assert 'decades' in summary
        assert 'quality' in summary
        assert 'metadata' in summary
