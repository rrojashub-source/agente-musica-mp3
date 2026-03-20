"""
Tests for Service Layer
Tests LibraryService, DownloadService, and PlayerService
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Skip all if PySide6 not available
try:
    from PySide6.QtCore import QCoreApplication

    HAS_QT = True
except ImportError:
    HAS_QT = False

pytestmark = pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")


@pytest.fixture(scope="module")
def qapp():
    """Create QCoreApplication for signal testing"""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


# ==========================================
# LibraryService Tests
# ==========================================


class TestLibraryService:
    """Tests for LibraryService"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        from services.library_service import LibraryService

        LibraryService.reset_instance()
        yield
        LibraryService.reset_instance()

    @pytest.fixture
    def mock_db(self):
        """Create mock database manager"""
        mock = MagicMock()
        mock.fetch_one.return_value = {
            "id": 1,
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "year": 2023,
            "genre": "Rock",
            "duration": 180,
            "play_count": 5,
            "rating": 4,
        }
        mock.fetch_all.return_value = [
            {"id": 1, "title": "Song 1", "artist": "Artist 1"},
            {"id": 2, "title": "Song 2", "artist": "Artist 2"},
        ]
        mock.add_song.return_value = 1
        mock.search_songs.return_value = [{"id": 1, "title": "Found Song", "artist": "Found Artist"}]
        return mock

    def test_singleton_pattern(self, qapp):
        """Test LibraryService is singleton"""
        from services.library_service import LibraryService

        service1 = LibraryService.get_instance("test.db")
        service2 = LibraryService.get_instance("other.db")

        assert service1 is service2

    def test_song_dataclass(self):
        """Test Song dataclass conversion"""
        from services.library_service import Song

        data = {"id": 1, "title": "Test", "artist": "Artist", "album": "Album", "year": 2023, "genre": "Rock"}
        song = Song.from_dict(data)

        assert song.id == 1
        assert song.title == "Test"
        assert song.artist == "Artist"

        # Test to_dict roundtrip
        result = song.to_dict()
        assert result["title"] == "Test"

    def test_library_stats_dataclass(self):
        """Test LibraryStats dataclass"""
        from services.library_service import LibraryStats

        data = {
            "total_songs": 100,
            "total_artists": 20,
            "total_albums": 15,
            "total_genres": 5,
            "total_duration_hours": 50.5,
        }
        stats = LibraryStats.from_dict(data)

        assert stats.total_songs == 100
        assert stats.total_artists == 20
        assert stats.total_duration_hours == 50.5

    def test_get_song(self, qapp, mock_db):
        """Test getting a song by ID"""
        from services.library_service import LibraryService

        with patch("services.library_service.LibraryService.db", mock_db):
            service = LibraryService.get_instance("test.db")
            service._db_manager = mock_db

            song = service.get_song(1)

            assert song is not None
            assert song.title == "Test Song"
            mock_db.fetch_one.assert_called()

    def test_add_song_emits_signal(self, qapp, mock_db):
        """Test adding song emits signal"""
        from services.library_service import LibraryService

        service = LibraryService.get_instance("test.db")
        service._db_manager = mock_db

        # Track signal emission
        signal_received = []
        service.song_added.connect(lambda x: signal_received.append(x))

        song_id = service.add_song({"title": "New Song", "artist": "New Artist"})

        assert song_id == 1
        assert len(signal_received) == 1
        assert signal_received[0] == 1

    def test_search_songs(self, qapp, mock_db):
        """Test searching songs"""
        from services.library_service import LibraryService

        service = LibraryService.get_instance("test.db")
        service._db_manager = mock_db

        results = service.search("test")

        assert len(results) == 1
        assert results[0].title == "Found Song"

    def test_stats_caching(self, qapp, mock_db):
        """Test statistics are cached"""
        from services.library_service import LibraryService

        mock_db.fetch_one.return_value = {
            "total_songs": 100,
            "total_artists": 20,
            "total_albums": 15,
            "total_genres": 5,
            "total_duration_hours": 50.0,
        }

        service = LibraryService.get_instance("test.db")
        service._db_manager = mock_db

        # First call
        stats1 = service.get_stats()
        # Second call (should be cached)
        stats2 = service.get_stats()

        assert stats1.total_songs == 100
        assert stats1 is stats2  # Same cached object
        # DB should only be called once (cached)
        assert mock_db.fetch_one.call_count == 1

    def test_increment_play_count(self, qapp, mock_db):
        """Test incrementing play count"""
        from services.library_service import LibraryService

        service = LibraryService.get_instance("test.db")
        service._db_manager = mock_db

        result = service.increment_play_count(1)

        assert result is True
        mock_db.execute_query.assert_called()


# ==========================================
# DownloadService Tests
# ==========================================


class TestDownloadService:
    """Tests for DownloadService"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        from services.download_service import DownloadService

        DownloadService.reset_instance()
        yield
        DownloadService.reset_instance()

    @pytest.fixture
    def mock_queue(self):
        """Create mock download queue"""
        mock = MagicMock()
        mock.add.return_value = "item-123"
        mock.get_all_items.return_value = {
            "item-1": {"id": "item-1", "status": "pending", "title": "Song 1"},
            "item-2": {"id": "item-2", "status": "downloading", "title": "Song 2"},
            "item-3": {"id": "item-3", "status": "completed", "title": "Song 3"},
        }
        return mock

    def test_singleton_pattern(self, qapp):
        """Test DownloadService is singleton"""
        from services.download_service import DownloadService

        service1 = DownloadService.get_instance("/tmp/downloads")
        service2 = DownloadService.get_instance("/other/path")

        assert service1 is service2

    def test_download_item_dataclass(self):
        """Test DownloadItem dataclass"""
        from services.download_service import DownloadItem, DownloadStatus

        data = {
            "id": "test-123",
            "url": "https://youtube.com/watch?v=test",
            "title": "Test Video",
            "status": "downloading",
            "progress": 50.0,
        }
        item = DownloadItem.from_dict(data)

        assert item.id == "test-123"
        assert item.title == "Test Video"
        assert item.status == DownloadStatus.DOWNLOADING
        assert item.progress == 50.0

    def test_add_download(self, qapp, mock_queue):
        """Test adding a download"""
        from services.download_service import DownloadService

        service = DownloadService.get_instance("/tmp/downloads")
        service._queue = mock_queue

        # Track signal
        signal_received = []
        service.download_added.connect(lambda x: signal_received.append(x))

        item_id = service.add_download(
            url="https://youtube.com/watch?v=test", metadata={"title": "Test", "artist": "Artist"}
        )

        assert item_id == "item-123"
        assert len(signal_received) == 1
        mock_queue.add.assert_called_once()

    def test_get_pending_count(self, qapp, mock_queue):
        """Test getting pending count"""
        from services.download_service import DownloadService

        service = DownloadService.get_instance("/tmp/downloads")
        service._queue = mock_queue

        count = service.get_pending_count()

        assert count == 1  # Only item-1 is pending

    def test_get_active_count(self, qapp, mock_queue):
        """Test getting active count"""
        from services.download_service import DownloadService

        service = DownloadService.get_instance("/tmp/downloads")
        service._queue = mock_queue

        count = service.get_active_count()

        assert count == 1  # Only item-2 is downloading

    def test_get_completed_count(self, qapp, mock_queue):
        """Test getting completed count"""
        from services.download_service import DownloadService

        service = DownloadService.get_instance("/tmp/downloads")
        service._queue = mock_queue

        count = service.get_completed_count()

        assert count == 1  # Only item-3 is completed

    def test_cancel_download(self, qapp, mock_queue):
        """Test canceling a download"""
        from services.download_service import DownloadService

        mock_queue._items = {"item-1": {"status": "pending"}}
        service = DownloadService.get_instance("/tmp/downloads")
        service._queue = mock_queue

        signal_received = []
        service.download_canceled.connect(lambda x: signal_received.append(x))

        result = service.cancel("item-1")

        assert result is True
        assert len(signal_received) == 1

    def test_download_dir_property(self, qapp):
        """Test download directory property"""
        from services.download_service import DownloadService

        service = DownloadService.get_instance("/tmp/test_downloads")

        assert service.download_dir == "/tmp/test_downloads"

        service.download_dir = "/tmp/new_downloads"
        assert service.download_dir == "/tmp/new_downloads"


# ==========================================
# PlayerService Tests
# ==========================================


class TestPlayerService:
    """Tests for PlayerService"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        from services.player_service import PlayerService

        PlayerService.reset_instance()
        yield
        PlayerService.reset_instance()

    @pytest.fixture
    def mock_player(self):
        """Create mock audio player"""
        mock = MagicMock()
        mock.load.return_value = True
        mock.play.return_value = True
        mock.pause.return_value = True
        mock.stop.return_value = True
        mock.seek.return_value = True
        mock.set_volume.return_value = True
        mock.get_position.return_value = 30.0
        mock.get_duration.return_value = 180.0
        mock.is_gapless_enabled.return_value = True
        mock.get_crossfade.return_value = 0
        mock.queue_next.return_value = True
        return mock

    def test_singleton_pattern(self, qapp):
        """Test PlayerService is singleton"""
        from services.player_service import PlayerService

        service1 = PlayerService.get_instance()
        service2 = PlayerService.get_instance()

        assert service1 is service2

    def test_playback_state_enum(self):
        """Test PlaybackState enum"""
        from services.player_service import PlaybackState

        assert PlaybackState.STOPPED.value == "stopped"
        assert PlaybackState.PLAYING.value == "playing"
        assert PlaybackState.PAUSED.value == "paused"

    def test_repeat_mode_enum(self):
        """Test RepeatMode enum"""
        from services.player_service import RepeatMode

        assert RepeatMode.OFF.value == "off"
        assert RepeatMode.ONE.value == "one"
        assert RepeatMode.ALL.value == "all"

    def test_now_playing_dataclass(self):
        """Test NowPlaying dataclass"""
        from services.player_service import NowPlaying, PlaybackState

        np = NowPlaying(
            song_id=1,
            title="Test Song",
            artist="Test Artist",
            duration=180.0,
            position=45.0,
            state=PlaybackState.PLAYING,
        )

        assert np.title == "Test Song"
        assert np.duration == 180.0

        result = np.to_dict()
        assert result["title"] == "Test Song"
        assert result["state"] == "playing"

    def test_play_file(self, qapp, mock_player):
        """Test playing a file"""
        from services.player_service import PlayerService, PlaybackState

        service = PlayerService.get_instance()
        service._player = mock_player

        # Track signal
        state_changes = []
        service.state_changed.connect(lambda x: state_changes.append(x))

        result = service.play(
            file_path="/path/to/song.mp3", metadata={"title": "Test", "artist": "Artist", "duration": 180}
        )

        assert result is True
        assert service.is_playing()
        assert PlaybackState.PLAYING in state_changes

    def test_pause_resume(self, qapp, mock_player):
        """Test pause and resume"""
        from services.player_service import PlayerService

        service = PlayerService.get_instance()
        service._player = mock_player

        # Start playing
        service.play("/path/to/song.mp3", metadata={"title": "Test"})

        # Pause
        result = service.pause()
        assert result is True
        assert service.is_paused()

        # Resume
        result = service.play()
        assert result is True
        assert service.is_playing()

    def test_toggle_play_pause(self, qapp, mock_player):
        """Test toggle play/pause"""
        from services.player_service import PlayerService

        service = PlayerService.get_instance()
        service._player = mock_player

        # Start playing
        service.play("/path/to/song.mp3", metadata={"title": "Test"})
        assert service.is_playing()

        # Toggle to pause
        service.toggle_play_pause()
        assert service.is_paused()

        # Toggle back to play
        service.toggle_play_pause()
        assert service.is_playing()

    def test_volume_control(self, qapp, mock_player):
        """Test volume control"""
        from services.player_service import PlayerService

        service = PlayerService.get_instance()
        service._player = mock_player

        # Track signal
        volume_changes = []
        service.volume_changed.connect(lambda x: volume_changes.append(x))

        service.set_volume(75)

        assert service.get_volume() == 75
        assert 75 in volume_changes
        mock_player.set_volume.assert_called_with(0.75)

    def test_queue_management(self, qapp, mock_player):
        """Test play queue management"""
        from services.player_service import PlayerService

        service = PlayerService.get_instance()
        service._player = mock_player

        songs = [
            {"id": 1, "file_path": "/path/1.mp3", "title": "Song 1"},
            {"id": 2, "file_path": "/path/2.mp3", "title": "Song 2"},
            {"id": 3, "file_path": "/path/3.mp3", "title": "Song 3"},
        ]

        service.set_queue(songs)

        queue = service.get_queue()
        assert len(queue) == 3
        assert service.get_queue_index() == 0  # First song playing

    def test_next_previous(self, qapp, mock_player):
        """Test next/previous navigation"""
        from services.player_service import PlayerService

        service = PlayerService.get_instance()
        service._player = mock_player

        songs = [
            {"id": 1, "file_path": "/path/1.mp3", "title": "Song 1"},
            {"id": 2, "file_path": "/path/2.mp3", "title": "Song 2"},
        ]

        service.set_queue(songs)
        assert service.get_queue_index() == 0

        # Next
        service.next()
        assert service.get_queue_index() == 1

        # Previous (but we're at position 0, so just restart)
        service._now_playing.position = 0  # Simulate start of track
        service.previous()
        assert service.get_queue_index() == 0

    def test_shuffle_toggle(self, qapp, mock_player):
        """Test shuffle toggle"""
        from services.player_service import PlayerService

        service = PlayerService.get_instance()
        service._player = mock_player

        assert not service.is_shuffle_enabled()

        service.set_shuffle(True)
        assert service.is_shuffle_enabled()

        service.set_shuffle(False)
        assert not service.is_shuffle_enabled()

    def test_repeat_cycle(self, qapp, mock_player):
        """Test repeat mode cycling"""
        from services.player_service import PlayerService, RepeatMode

        service = PlayerService.get_instance()
        service._player = mock_player

        assert service.get_repeat() == RepeatMode.OFF

        service.cycle_repeat()
        assert service.get_repeat() == RepeatMode.ALL

        service.cycle_repeat()
        assert service.get_repeat() == RepeatMode.ONE

        service.cycle_repeat()
        assert service.get_repeat() == RepeatMode.OFF

    def test_gapless_playback(self, qapp, mock_player):
        """Test gapless playback check"""
        from services.player_service import PlayerService

        service = PlayerService.get_instance()
        service._player = mock_player

        assert service.is_gapless_enabled() is True

    def test_crossfade_settings(self, qapp, mock_player):
        """Test crossfade settings"""
        from services.player_service import PlayerService

        service = PlayerService.get_instance()
        service._player = mock_player

        service.set_crossfade(500)
        mock_player.set_crossfade.assert_called_with(500)


# ==========================================
# Integration Tests
# ==========================================


class TestServiceIntegration:
    """Integration tests across services"""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset all singletons"""
        from services.library_service import LibraryService
        from services.download_service import DownloadService
        from services.player_service import PlayerService

        LibraryService.reset_instance()
        DownloadService.reset_instance()
        PlayerService.reset_instance()
        yield
        LibraryService.reset_instance()
        DownloadService.reset_instance()
        PlayerService.reset_instance()

    def test_all_services_import(self, qapp):
        """Test all services can be imported"""
        from services import LibraryService, DownloadService, PlayerService

        assert LibraryService is not None
        assert DownloadService is not None
        assert PlayerService is not None

    def test_services_are_independent_singletons(self, qapp):
        """Test each service has its own singleton"""
        from services import LibraryService, DownloadService, PlayerService

        lib1 = LibraryService.get_instance("test.db")
        lib2 = LibraryService.get_instance("test.db")
        dl1 = DownloadService.get_instance("/tmp")
        dl2 = DownloadService.get_instance("/tmp")
        pl1 = PlayerService.get_instance()
        pl2 = PlayerService.get_instance()

        assert lib1 is lib2
        assert dl1 is dl2
        assert pl1 is pl2
        assert lib1 is not dl1
        assert dl1 is not pl1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
