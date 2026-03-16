"""
Tests for Player Service

Tests cover:
- PlaybackState and RepeatMode enums
- NowPlaying dataclass
- Playback control (play, pause, resume, stop, seek)
- Volume control
- Queue management (set, add, insert, remove, clear, next, previous)
- Shuffle and repeat modes
- State getters
- Track end handling
- Edge cases (empty queue, boundary conditions)
"""

import os
import sys
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

# Add src and tests to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

# Mock PySide6 if not available (allows tests to run without GUI framework)
import _mock_pyside6

_mock_pyside6.install()

from services.player_service import NowPlaying, PlaybackState, PlayerService, RepeatMode

# ==========================================
# Enum Tests
# ==========================================


class TestPlaybackState:
    """Test PlaybackState enum"""

    def test_values(self):
        assert PlaybackState.STOPPED.value == "stopped"
        assert PlaybackState.PLAYING.value == "playing"
        assert PlaybackState.PAUSED.value == "paused"
        assert PlaybackState.LOADING.value == "loading"


class TestRepeatMode:
    """Test RepeatMode enum"""

    def test_values(self):
        assert RepeatMode.OFF.value == "off"
        assert RepeatMode.ONE.value == "one"
        assert RepeatMode.ALL.value == "all"


# ==========================================
# NowPlaying Dataclass Tests
# ==========================================


class TestNowPlaying:
    """Test NowPlaying dataclass"""

    def test_defaults(self):
        """Should have sensible defaults"""
        np = NowPlaying()
        assert np.song_id is None
        assert np.file_path is None
        assert np.duration == 0.0
        assert np.position == 0.0
        assert np.state == PlaybackState.STOPPED

    def test_to_dict(self):
        """Should convert to dictionary"""
        np = NowPlaying(
            song_id=1, title="Test", artist="Artist", duration=180.0, position=45.0, state=PlaybackState.PLAYING
        )
        d = np.to_dict()

        assert d["song_id"] == 1
        assert d["title"] == "Test"
        assert d["state"] == "playing"
        assert d["duration"] == 180.0
        assert d["position"] == 45.0


# ==========================================
# PlayerService Tests (with mocked player)
# ==========================================


@pytest.fixture
def mock_player():
    """Create a mock AudioPlayer"""
    player = MagicMock()
    player.load.return_value = True
    player.play.return_value = True
    player.pause.return_value = True
    player.stop.return_value = True
    player.seek.return_value = True
    player.set_volume.return_value = True
    player.get_position.return_value = 0.0
    player.get_duration.return_value = 180.0
    player.is_gapless_enabled.return_value = False
    player.get_crossfade.return_value = 0
    return player


@pytest.fixture
def service(mock_player):
    """Create PlayerService with mocked internals"""
    PlayerService.reset_instance()
    svc = PlayerService.__new__(PlayerService)
    svc._player = mock_player
    svc._now_playing = NowPlaying()
    svc._play_queue = []
    svc._queue_index = -1
    svc._shuffle = False
    svc._repeat = RepeatMode.OFF
    svc._volume = 100
    svc._position_timer = MagicMock()
    # Mock signals
    svc.state_changed = MagicMock()
    svc.track_changed = MagicMock()
    svc.position_changed = MagicMock()
    svc.volume_changed = MagicMock()
    svc.track_ended = MagicMock()
    svc.queue_changed = MagicMock()
    svc.error_occurred = MagicMock()
    return svc


class TestPlaybackControl:
    """Test play, pause, resume, stop, seek"""

    def test_play_new_track(self, service, mock_player):
        """Should load and play a new track"""
        result = service.play(
            file_path="/music/song.mp3", song_id=1, metadata={"title": "Song", "artist": "Artist", "duration": 200}
        )

        assert result is True
        mock_player.load.assert_called_once_with("/music/song.mp3")
        mock_player.play.assert_called_once()
        service.state_changed.emit.assert_called_with(PlaybackState.PLAYING)
        service.track_changed.emit.assert_called_once()
        service._position_timer.start.assert_called_once()

    def test_play_updates_now_playing(self, service, mock_player):
        """Should update NowPlaying info"""
        service.play(
            file_path="/music/song.mp3", song_id=42, metadata={"title": "My Song", "artist": "Me", "album": "Album"}
        )

        np = service._now_playing
        assert np.song_id == 42
        assert np.title == "My Song"
        assert np.artist == "Me"
        assert np.state == PlaybackState.PLAYING

    def test_play_without_metadata(self, service, mock_player):
        """Should use filename as title when no metadata"""
        service.play(file_path="/music/my_song.mp3")

        assert service._now_playing.title == "my_song"

    def test_play_load_failure(self, service, mock_player):
        """Should return False and emit error when load fails"""
        mock_player.load.return_value = False

        result = service.play(file_path="/bad/path.mp3")

        assert result is False
        service.error_occurred.emit.assert_called_once()

    def test_play_start_failure(self, service, mock_player):
        """Should return False when play() fails"""
        mock_player.play.return_value = False

        result = service.play(file_path="/music/song.mp3")

        assert result is False

    def test_play_resume_without_file(self, service, mock_player):
        """Should resume current track when no file_path given"""
        service._now_playing.state = PlaybackState.PAUSED

        result = service.play()

        assert result is True
        mock_player.load.assert_not_called()
        mock_player.play.assert_called_once()

    def test_play_exception(self, service, mock_player):
        """Should handle exceptions gracefully"""
        mock_player.load.side_effect = OSError("file not found")

        result = service.play(file_path="/missing.mp3")

        assert result is False
        service.error_occurred.emit.assert_called_once()

    def test_pause(self, service, mock_player):
        """Should pause and update state"""
        result = service.pause()

        assert result is True
        assert service._now_playing.state == PlaybackState.PAUSED
        service.state_changed.emit.assert_called_with(PlaybackState.PAUSED)
        service._position_timer.stop.assert_called_once()

    def test_pause_failure(self, service, mock_player):
        """Should return False when player.pause fails"""
        mock_player.pause.return_value = False

        result = service.pause()

        assert result is False

    def test_resume(self, service, mock_player):
        """Should call play() to resume"""
        result = service.resume()

        assert result is True

    def test_toggle_play_pause_from_playing(self, service, mock_player):
        """Should pause when currently playing"""
        service._now_playing.state = PlaybackState.PLAYING

        result = service.toggle_play_pause()

        assert result is True
        mock_player.pause.assert_called_once()

    def test_toggle_play_pause_from_paused(self, service, mock_player):
        """Should resume when currently paused"""
        service._now_playing.state = PlaybackState.PAUSED

        result = service.toggle_play_pause()

        assert result is True
        mock_player.play.assert_called_once()

    def test_toggle_play_pause_from_stopped(self, service, mock_player):
        """Should return False when stopped"""
        service._now_playing.state = PlaybackState.STOPPED

        result = service.toggle_play_pause()

        assert result is False

    def test_stop(self, service, mock_player):
        """Should stop and reset state"""
        result = service.stop()

        assert result is True
        mock_player.stop.assert_called_once()
        assert service._now_playing.state == PlaybackState.STOPPED
        assert service._now_playing.position == 0.0
        service._position_timer.stop.assert_called_once()

    def test_seek(self, service, mock_player):
        """Should seek and update position"""
        result = service.seek(60.0)

        assert result is True
        mock_player.seek.assert_called_once_with(60.0)
        assert service._now_playing.position == 60.0
        service.position_changed.emit.assert_called_with(60.0)

    def test_seek_failure(self, service, mock_player):
        """Should return False when seek fails"""
        mock_player.seek.return_value = False

        result = service.seek(60.0)

        assert result is False

    def test_seek_relative_forward(self, service, mock_player):
        """Should seek forward relative to current position"""
        service._now_playing.position = 30.0
        service._now_playing.duration = 180.0

        service.seek_relative(10.0)

        mock_player.seek.assert_called_once_with(40.0)

    def test_seek_relative_backward_clamped(self, service, mock_player):
        """Should not seek below 0"""
        service._now_playing.position = 5.0
        service._now_playing.duration = 180.0

        service.seek_relative(-20.0)

        mock_player.seek.assert_called_once_with(0)

    def test_seek_relative_clamped_to_duration(self, service, mock_player):
        """Should not seek past duration"""
        service._now_playing.position = 170.0
        service._now_playing.duration = 180.0

        service.seek_relative(20.0)

        mock_player.seek.assert_called_once_with(180.0)


class TestVolumeControl:
    """Test volume methods"""

    def test_set_volume(self, service, mock_player):
        """Should set volume and emit signal"""
        result = service.set_volume(75)

        assert result is True
        mock_player.set_volume.assert_called_once_with(0.75)
        assert service._volume == 75
        service.volume_changed.emit.assert_called_with(75)

    def test_set_volume_clamp_high(self, service, mock_player):
        """Should clamp volume to 100"""
        service.set_volume(150)

        mock_player.set_volume.assert_called_once_with(1.0)
        assert service._volume == 100

    def test_set_volume_clamp_low(self, service, mock_player):
        """Should clamp volume to 0"""
        service.set_volume(-10)

        mock_player.set_volume.assert_called_once_with(0.0)
        assert service._volume == 0

    def test_get_volume(self, service):
        """Should return current volume"""
        service._volume = 50
        assert service.get_volume() == 50

    def test_mute(self, service, mock_player):
        """Should set volume to 0"""
        service.mute()

        mock_player.set_volume.assert_called_once_with(0.0)

    def test_set_volume_failure(self, service, mock_player):
        """Should return False when player fails"""
        mock_player.set_volume.return_value = False

        result = service.set_volume(50)

        assert result is False


class TestQueueManagement:
    """Test queue operations"""

    def test_set_queue(self, service, mock_player):
        """Should set queue and start playing"""
        songs = [
            {"file_path": "/a.mp3", "id": 1, "title": "A"},
            {"file_path": "/b.mp3", "id": 2, "title": "B"},
        ]
        service.set_queue(songs)

        assert len(service._play_queue) == 2
        service.queue_changed.emit.assert_called()
        # Should start playing first song (next() increments from -1 to 0)
        mock_player.load.assert_called()

    def test_set_queue_empty(self, service, mock_player):
        """Should handle empty queue"""
        service.set_queue([])

        assert service._play_queue == []
        mock_player.load.assert_not_called()

    def test_set_queue_copies_list(self, service, mock_player):
        """Should copy the list, not reference it"""
        songs = [{"file_path": "/a.mp3", "id": 1, "title": "A"}]
        service.set_queue(songs)
        songs.append({"file_path": "/b.mp3", "id": 2, "title": "B"})

        assert len(service._play_queue) == 1

    def test_add_to_queue(self, service):
        """Should append to queue"""
        service.add_to_queue({"file_path": "/x.mp3", "title": "X"})

        assert len(service._play_queue) == 1
        service.queue_changed.emit.assert_called_once()

    def test_insert_next(self, service):
        """Should insert after current index"""
        service._play_queue = [{"title": "A"}, {"title": "B"}, {"title": "C"}]
        service._queue_index = 0

        service.insert_next({"title": "Inserted"})

        assert service._play_queue[1]["title"] == "Inserted"
        assert len(service._play_queue) == 4

    def test_remove_from_queue_valid(self, service):
        """Should remove song at index"""
        service._play_queue = [{"title": "A"}, {"title": "B"}, {"title": "C"}]
        service._queue_index = 2

        result = service.remove_from_queue(1)

        assert result is True
        assert len(service._play_queue) == 2
        # Index should adjust since removed index < current
        assert service._queue_index == 1

    def test_remove_from_queue_invalid_index(self, service):
        """Should return False for invalid index"""
        service._play_queue = [{"title": "A"}]

        result = service.remove_from_queue(5)

        assert result is False

    def test_remove_from_queue_negative_index(self, service):
        """Should return False for negative index"""
        result = service.remove_from_queue(-1)
        assert result is False

    def test_clear_queue(self, service):
        """Should clear queue and reset index"""
        service._play_queue = [{"title": "A"}, {"title": "B"}]
        service._queue_index = 1

        service.clear_queue()

        assert service._play_queue == []
        assert service._queue_index == -1
        service.queue_changed.emit.assert_called_once()

    def test_get_queue_returns_copy(self, service):
        """Should return a copy of the queue"""
        service._play_queue = [{"title": "A"}]
        q = service.get_queue()
        q.append({"title": "B"})

        assert len(service._play_queue) == 1

    def test_get_queue_index(self, service):
        """Should return current index"""
        service._queue_index = 3
        assert service.get_queue_index() == 3


class TestNextPrevious:
    """Test next and previous track navigation"""

    def test_next_plays_next_song(self, service, mock_player):
        """Should advance and play next song"""
        service._play_queue = [
            {"file_path": "/a.mp3", "id": 1, "title": "A"},
            {"file_path": "/b.mp3", "id": 2, "title": "B"},
        ]
        service._queue_index = 0

        result = service.next()

        assert result is True
        assert service._queue_index == 1
        mock_player.load.assert_called_with("/b.mp3")

    def test_next_empty_queue(self, service, mock_player):
        """Should return False for empty queue"""
        service._play_queue = []

        result = service.next()

        assert result is False

    def test_next_at_end_no_repeat(self, service, mock_player):
        """Should return False at end with repeat off"""
        service._play_queue = [{"file_path": "/a.mp3", "id": 1, "title": "A"}]
        service._queue_index = 0

        result = service.next()

        assert result is False

    def test_next_at_end_repeat_all(self, service, mock_player):
        """Should wrap around with repeat all"""
        service._play_queue = [
            {"file_path": "/a.mp3", "id": 1, "title": "A"},
            {"file_path": "/b.mp3", "id": 2, "title": "B"},
        ]
        service._queue_index = 1
        service._repeat = RepeatMode.ALL

        result = service.next()

        assert result is True
        assert service._queue_index == 0

    def test_previous_plays_previous_song(self, service, mock_player):
        """Should go back to previous song"""
        service._play_queue = [
            {"file_path": "/a.mp3", "id": 1, "title": "A"},
            {"file_path": "/b.mp3", "id": 2, "title": "B"},
        ]
        service._queue_index = 1
        service._now_playing.position = 1.0  # Under 3 seconds

        result = service.previous()

        assert result is True
        assert service._queue_index == 0

    def test_previous_restarts_if_past_3_seconds(self, service, mock_player):
        """Should restart track if position > 3 seconds"""
        service._play_queue = [{"file_path": "/a.mp3", "id": 1, "title": "A"}]
        service._queue_index = 0
        service._now_playing.position = 5.0

        result = service.previous()

        assert result is True
        mock_player.seek.assert_called_once_with(0)

    def test_previous_empty_queue(self, service, mock_player):
        """Should return False for empty queue"""
        service._play_queue = []

        result = service.previous()

        assert result is False

    def test_previous_at_start_repeat_all(self, service, mock_player):
        """Should wrap to end with repeat all"""
        service._play_queue = [
            {"file_path": "/a.mp3", "id": 1, "title": "A"},
            {"file_path": "/b.mp3", "id": 2, "title": "B"},
        ]
        service._queue_index = 0
        service._now_playing.position = 1.0
        service._repeat = RepeatMode.ALL

        result = service.previous()

        assert result is True
        assert service._queue_index == 1


class TestShuffleRepeat:
    """Test shuffle and repeat modes"""

    def test_set_shuffle_on(self, service):
        """Should enable shuffle"""
        service.set_shuffle(True)
        assert service._shuffle is True

    def test_set_shuffle_off(self, service):
        """Should disable shuffle"""
        service._shuffle = True
        service.set_shuffle(False)
        assert service._shuffle is False

    def test_is_shuffle_enabled(self, service):
        """Should report shuffle state"""
        service._shuffle = True
        assert service.is_shuffle_enabled() is True

    def test_set_repeat(self, service):
        """Should set repeat mode"""
        service.set_repeat(RepeatMode.ONE)
        assert service._repeat == RepeatMode.ONE

    def test_get_repeat(self, service):
        """Should return repeat mode"""
        service._repeat = RepeatMode.ALL
        assert service.get_repeat() == RepeatMode.ALL

    def test_cycle_repeat(self, service):
        """Should cycle OFF -> ALL -> ONE -> OFF"""
        service._repeat = RepeatMode.OFF
        assert service.cycle_repeat() == RepeatMode.ALL
        assert service.cycle_repeat() == RepeatMode.ONE
        assert service.cycle_repeat() == RepeatMode.OFF

    def test_shuffle_queue_preserves_current(self, service):
        """Should keep current song in place when shuffling"""
        service._play_queue = [
            {"title": "Current"},
            {"title": "B"},
            {"title": "C"},
            {"title": "D"},
        ]
        service._queue_index = 0

        service._shuffle_queue()

        assert service._play_queue[0]["title"] == "Current"


class TestStateGetters:
    """Test state getter methods"""

    def test_get_state(self, service):
        """Should return current state"""
        service._now_playing.state = PlaybackState.PLAYING
        assert service.get_state() == PlaybackState.PLAYING

    def test_get_now_playing(self, service):
        """Should return NowPlaying object"""
        result = service.get_now_playing()
        assert isinstance(result, NowPlaying)

    def test_get_position(self, service):
        """Should return current position"""
        service._now_playing.position = 42.5
        assert service.get_position() == 42.5

    def test_get_duration(self, service):
        """Should return current duration"""
        service._now_playing.duration = 180.0
        assert service.get_duration() == 180.0

    def test_is_playing(self, service):
        """Should return True when playing"""
        service._now_playing.state = PlaybackState.PLAYING
        assert service.is_playing() is True

        service._now_playing.state = PlaybackState.PAUSED
        assert service.is_playing() is False

    def test_is_paused(self, service):
        """Should return True when paused"""
        service._now_playing.state = PlaybackState.PAUSED
        assert service.is_paused() is True

        service._now_playing.state = PlaybackState.PLAYING
        assert service.is_paused() is False


class TestTrackEndHandling:
    """Test _on_track_end behavior"""

    def test_track_end_repeat_one(self, service, mock_player):
        """Should replay same track on REPEAT ONE"""
        service._repeat = RepeatMode.ONE
        service._now_playing.song_id = None  # Skip play count tracking

        service._on_track_end()

        service.track_ended.emit.assert_called_once()
        mock_player.play.assert_called_once()

    def test_track_end_has_next(self, service, mock_player):
        """Should play next when queue has more songs"""
        service._repeat = RepeatMode.OFF
        service._play_queue = [
            {"file_path": "/a.mp3", "id": 1, "title": "A"},
            {"file_path": "/b.mp3", "id": 2, "title": "B"},
        ]
        service._queue_index = 0
        service._now_playing.song_id = None

        service._on_track_end()

        assert service._queue_index == 1

    def test_track_end_end_of_queue_repeat_all(self, service, mock_player):
        """Should restart queue on REPEAT ALL at end"""
        service._repeat = RepeatMode.ALL
        service._play_queue = [
            {"file_path": "/a.mp3", "id": 1, "title": "A"},
        ]
        service._queue_index = 0
        service._now_playing.song_id = None

        service._on_track_end()

        assert service._queue_index == 0

    def test_track_end_stop_at_end(self, service, mock_player):
        """Should stop when at end with repeat off"""
        service._repeat = RepeatMode.OFF
        service._play_queue = [
            {"file_path": "/a.mp3", "id": 1, "title": "A"},
        ]
        service._queue_index = 0
        service._now_playing.song_id = None

        service._on_track_end()

        mock_player.stop.assert_called_once()


class TestGaplessPlayback:
    """Test gapless playback methods"""

    def test_is_gapless_enabled(self, service, mock_player):
        """Should delegate to player"""
        mock_player.is_gapless_enabled.return_value = True
        assert service.is_gapless_enabled() is True

    def test_set_gapless(self, service, mock_player):
        """Should delegate to player"""
        service.set_gapless(True)
        mock_player.set_gapless.assert_called_once_with(True)

    def test_set_crossfade(self, service, mock_player):
        """Should delegate to player"""
        service.set_crossfade(500)
        mock_player.set_crossfade.assert_called_once_with(500)

    def test_get_crossfade(self, service, mock_player):
        """Should delegate to player"""
        mock_player.get_crossfade.return_value = 200
        assert service.get_crossfade() == 200


class TestSingleton:
    """Test singleton pattern"""

    def test_reset_instance(self):
        """Should reset singleton"""
        PlayerService._instance = "fake"
        PlayerService.reset_instance()
        assert PlayerService._instance is None


class TestCleanup:
    """Test cleanup method"""

    def test_cleanup_with_player(self, service, mock_player):
        """Should stop timer and cleanup player"""
        service.cleanup()

        service._position_timer.stop.assert_called_once()
        mock_player.cleanup.assert_called_once()
        assert service._player is None

    def test_cleanup_no_player(self, service):
        """Should handle cleanup when no player loaded"""
        service._player = None
        service.cleanup()  # Should not raise

    def test_cleanup_no_timer(self, service, mock_player):
        """Should handle cleanup when no timer"""
        service._position_timer = None
        service.cleanup()  # Should not raise
