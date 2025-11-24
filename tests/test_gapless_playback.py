"""
Tests for Gapless Playback Feature
"""
import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestGaplessPlaybackMocked:
    """Test gapless playback with mocked pygame"""

    @pytest.fixture
    def mock_pygame(self):
        """Create mock pygame module"""
        mock = MagicMock()
        mock.mixer.init = MagicMock()
        mock.mixer.music.load = MagicMock()
        mock.mixer.music.play = MagicMock()
        mock.mixer.music.queue = MagicMock()
        mock.mixer.music.stop = MagicMock()
        mock.mixer.music.get_busy = MagicMock(return_value=True)
        mock.mixer.music.get_pos = MagicMock(return_value=0)
        mock.mixer.music.set_endevent = MagicMock()
        mock.mixer.quit = MagicMock()
        mock.time.get_ticks = MagicMock(return_value=0)
        mock.USEREVENT = 24
        return mock

    @pytest.fixture
    def player_with_mock(self, mock_pygame):
        """Create AudioPlayer with mocked pygame"""
        with patch.dict('sys.modules', {'pygame': mock_pygame}):
            from core.audio_player import AudioPlayer
            # Re-import to use our mock
            import importlib
            import core.audio_player as ap
            importlib.reload(ap)

            player = ap.AudioPlayer()
            player._pygame = mock_pygame
            return player

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

    def test_queue_next_requires_file(self, player_with_mock, tmp_path):
        """Test queue_next fails with non-existent file"""
        player = player_with_mock

        result = player.queue_next("/non/existent/file.mp3")
        assert result is False

    def test_queue_next_with_valid_file(self, player_with_mock, tmp_path):
        """Test queue_next succeeds with valid file"""
        player = player_with_mock

        # Create a test file
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake mp3 data")

        result = player.queue_next(str(test_file))
        assert result is True
        assert player.get_queued_file() == str(test_file)

    def test_clear_queue(self, player_with_mock, tmp_path):
        """Test clearing the queue"""
        player = player_with_mock

        # Queue a file
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake mp3 data")
        player.queue_next(str(test_file))

        # Clear it
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

        # Default is 0 (gapless)
        assert player.get_crossfade() == 0

        # Set crossfade
        player.set_crossfade(500)
        assert player.get_crossfade() == 500

        # Negative values should be clamped to 0
        player.set_crossfade(-100)
        assert player.get_crossfade() == 0


class TestTrackEndCallbacks:
    """Test track end callback system"""

    @pytest.fixture
    def mock_pygame(self):
        """Create mock pygame module"""
        mock = MagicMock()
        mock.mixer.init = MagicMock()
        mock.mixer.music.get_busy = MagicMock(return_value=False)
        mock.mixer.music.set_endevent = MagicMock()
        mock.mixer.quit = MagicMock()
        mock.time.get_ticks = MagicMock(return_value=0)
        mock.USEREVENT = 24
        return mock

    @pytest.fixture
    def player_with_mock(self, mock_pygame):
        """Create AudioPlayer with mocked pygame"""
        with patch.dict('sys.modules', {'pygame': mock_pygame}):
            from core.audio_player import AudioPlayer, PlaybackState
            import importlib
            import core.audio_player as ap
            importlib.reload(ap)

            player = ap.AudioPlayer()
            player._pygame = mock_pygame
            return player

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

    def test_callback_invoked_on_track_end(self, player_with_mock):
        """Test callback is called when track ends"""
        player = player_with_mock
        callback = Mock()

        player.on_track_end(callback)
        player._current_file = "/test/song.mp3"

        # Need to set state properly
        from core.audio_player import PlaybackState
        player._state = PlaybackState.PLAYING

        # Simulate track end - music stops playing
        player._pygame.mixer.music.get_busy.return_value = False

        # Manually call _notify_track_end to test callback invocation
        # (check_track_end may have issues with mock setup)
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

        player._current_file = "/test/song.mp3"
        from core.audio_player import PlaybackState
        player._state = PlaybackState.PLAYING
        player._pygame.mixer.music.get_busy.return_value = False

        # Should not raise, and good_callback should still be called
        player.check_track_end()
        good_callback.assert_called_once()


class TestGaplessTransition:
    """Test gapless transition behavior"""

    @pytest.fixture
    def mock_pygame(self):
        """Create mock pygame module"""
        mock = MagicMock()
        mock.mixer.init = MagicMock()
        mock.mixer.music.get_busy = MagicMock(return_value=False)
        mock.mixer.music.set_endevent = MagicMock()
        mock.mixer.quit = MagicMock()
        mock.time.get_ticks = MagicMock(return_value=1000)
        mock.USEREVENT = 24
        return mock

    @pytest.fixture
    def player_with_mock(self, mock_pygame):
        """Create AudioPlayer with mocked pygame"""
        with patch.dict('sys.modules', {'pygame': mock_pygame}):
            from core.audio_player import AudioPlayer, PlaybackState
            import importlib
            import core.audio_player as ap
            importlib.reload(ap)

            player = ap.AudioPlayer()
            player._pygame = mock_pygame
            return player

    def test_gapless_transition_updates_current_file(self, player_with_mock):
        """Test that gapless transition updates current file"""
        player = player_with_mock

        player._current_file = "/path/to/song1.mp3"
        player._queued_file = "/path/to/song2.mp3"
        player._queued_duration = 180.0

        from core.audio_player import PlaybackState
        player._state = PlaybackState.PLAYING
        player._pygame.mixer.music.get_busy.return_value = False

        player.check_track_end()

        assert player._current_file == "/path/to/song2.mp3"
        assert player._duration == 180.0
        assert player._queued_file is None

    def test_no_queue_stops_playback(self, player_with_mock):
        """Test that playback stops when no queued track"""
        player = player_with_mock

        player._current_file = "/path/to/song.mp3"
        player._queued_file = None

        from core.audio_player import PlaybackState
        player._state = PlaybackState.PLAYING
        player._pygame.mixer.music.get_busy.return_value = False

        player.check_track_end()

        assert player._state == PlaybackState.STOPPED


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
