"""
Tests for Gapless Playback Feature (python-mpv)
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_mpv():
    """Create mock mpv module"""
    mock_module = MagicMock()
    mock_instance = MagicMock()
    mock_module.MPV.return_value = mock_instance
    mock_instance.time_pos = 0.0
    mock_instance.duration = 0.0
    mock_instance.volume = 100.0
    mock_instance.core_idle = False
    mock_instance.pause = False
    return mock_module, mock_instance


@pytest.fixture
def player_with_mock(mock_mpv):
    """Create AudioPlayer with mocked mpv"""
    mock_module, mock_instance = mock_mpv
    with patch.dict("sys.modules", {"mpv": mock_module}):
        import importlib
        import core.audio_player as ap

        importlib.reload(ap)

        player = ap.AudioPlayer()
        return player


class TestGaplessPlaybackMocked:
    """Test gapless playback with mocked mpv"""

    def test_gapless_enabled_by_default(self, player_with_mock):
        """Test that gapless is enabled by default"""
        assert player_with_mock.is_gapless_enabled() is True

    def test_toggle_gapless(self, player_with_mock):
        """Test enabling/disabling gapless"""
        player = player_with_mock

        player.set_gapless_enabled(False)
        assert player.is_gapless_enabled() is False

        player.set_gapless_enabled(True)
        assert player.is_gapless_enabled() is True

    def test_queue_next_requires_file(self, player_with_mock):
        """Test queue_next fails with non-existent file"""
        player = player_with_mock

        result = player.queue_next("/non/existent/file.mp3")
        assert result is False

    def test_queue_next_with_valid_file(self, player_with_mock, tmp_path):
        """Test queue_next succeeds with valid file"""
        player = player_with_mock

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake mp3 data")

        result = player.queue_next(str(test_file))
        assert result is True
        assert player.get_queued_file() == str(test_file)

    def test_clear_queue(self, player_with_mock, tmp_path):
        """Test clearing the queue"""
        player = player_with_mock

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake mp3 data")
        player.queue_next(str(test_file))

        player.clear_queue()
        assert player.get_queued_file() is None

    def test_queue_disabled_when_gapless_off(self, player_with_mock, tmp_path):
        """Test that queue fails when gapless is disabled"""
        player = player_with_mock
        player.set_gapless_enabled(False)

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake mp3 data")

        result = player.queue_next(str(test_file))
        assert result is False

    def test_crossfade_settings(self, player_with_mock):
        """Test crossfade duration settings"""
        player = player_with_mock

        assert player.get_crossfade() == 0

        player.set_crossfade(500)
        assert player.get_crossfade() == 500

        player.set_crossfade(-100)
        assert player.get_crossfade() == 0


class TestTrackEndCallbacks:
    """Test track end callback system"""

    def test_register_callback(self, player_with_mock):
        """Test registering track end callback"""
        player = player_with_mock
        callback = Mock()

        player.on_track_end(callback)
        assert callback in player._on_track_end_callbacks

    def test_remove_callback(self, player_with_mock):
        """Test removing track end callback"""
        player = player_with_mock
        callback = Mock()

        player.on_track_end(callback)
        player.remove_track_end_callback(callback)
        assert callback not in player._on_track_end_callbacks

    def test_callback_not_duplicated(self, player_with_mock):
        """Test that same callback isn't added twice"""
        player = player_with_mock
        callback = Mock()

        player.on_track_end(callback)
        player.on_track_end(callback)

        assert player._on_track_end_callbacks.count(callback) == 1

    def test_callback_invoked_on_notify(self, player_with_mock):
        """Test callback is called when _notify_track_end is called"""
        player = player_with_mock
        callback = Mock()

        player.on_track_end(callback)
        player._notify_track_end("/test/song.mp3")

        callback.assert_called_once_with("/test/song.mp3")

    def test_callback_error_handled(self, player_with_mock):
        """Test that callback errors don't crash the player"""
        player = player_with_mock

        def bad_callback(file_path):
            raise Exception("Callback error")

        good_callback = Mock()

        player.on_track_end(bad_callback)
        player.on_track_end(good_callback)

        # Should not raise
        player._notify_track_end("/test/song.mp3")
        good_callback.assert_called_once_with("/test/song.mp3")


class TestGaplessTransition:
    """Test gapless transition behavior"""

    def test_gapless_transition_updates_current_file(self, player_with_mock, mock_mpv):
        """Test that gapless transition updates current file"""
        _, mock_instance = mock_mpv
        player = player_with_mock

        player._current_file = "/path/to/song1.mp3"
        player._queued_file = "/path/to/song2.mp3"
        player._queued_duration = 180.0

        from core.audio_player import PlaybackState

        player._state = PlaybackState.PLAYING
        mock_instance.core_idle = True

        player.check_track_end()

        assert player._current_file == "/path/to/song2.mp3"
        assert player._duration == 180.0
        assert player._queued_file is None

    def test_no_queue_stops_playback(self, player_with_mock, mock_mpv):
        """Test that playback stops when no queued track"""
        _, mock_instance = mock_mpv
        player = player_with_mock

        player._current_file = "/path/to/song.mp3"
        player._queued_file = None

        from core.audio_player import PlaybackState

        player._state = PlaybackState.PLAYING
        mock_instance.core_idle = True

        player.check_track_end()

        assert player._state == PlaybackState.STOPPED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
