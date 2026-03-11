"""
Playback Controller — Phase 2.1

Routes playback commands between library and playlist sources.
Handles seek, volume, mute keyboard shortcuts.
"""
import logging
from pathlib import Path
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class PlaybackController(QObject):
    """Routes playback to correct source (library tab or playlist widget)"""

    def __init__(self, audio_player, now_playing, playlist_manager, db_manager, parent=None):
        super().__init__(parent)
        self.audio_player = audio_player
        self.now_playing = now_playing
        self.playlist_manager = playlist_manager
        self.db_manager = db_manager

        # Late-bound widget references (set after UI build)
        self.library_tab = None
        self.playlist_widget = None
        self.status_bar = None

        # Playback source tracking
        self._playback_source = None
        self._current_playlist_id = None
        self._current_playlist_songs = []
        self._current_playlist_index = -1
        self._previous_volume = 0.7

    def set_widgets(self, library_tab=None, playlist_widget=None, status_bar=None):
        """Set widget references created after controller init"""
        if library_tab is not None:
            self.library_tab = library_tab
        if playlist_widget is not None:
            self.playlist_widget = playlist_widget
        if status_bar is not None:
            self.status_bar = status_bar

    # ==========================================
    # Playback Source Routing
    # ==========================================

    def on_library_playback_started(self):
        """Handle playback started from library — update source tracking"""
        self._playback_source = 'library'
        self._current_playlist_id = None
        self._current_playlist_songs = []
        self._current_playlist_index = -1

        if self.playlist_widget:
            self.playlist_widget.clear_playing_highlight()

        logger.info("Playback source set to: library")

    def on_global_next_clicked(self):
        """Handle next button — route to correct source"""
        if self._playback_source == 'playlist':
            logger.info("Next clicked (playlist mode)")
            self._play_next_from_playlist()
        else:
            logger.info("Next clicked (library mode)")
            if self.library_tab:
                self.library_tab._on_next_clicked()

    def on_global_prev_clicked(self):
        """Handle prev button — route to correct source"""
        if self._playback_source == 'playlist':
            logger.info("Prev clicked (playlist mode)")
            self._play_prev_from_playlist()
        else:
            logger.info("Prev clicked (library mode)")
            if self.library_tab:
                self.library_tab._on_prev_clicked()

    def on_global_song_ended(self):
        """Handle song ended — route to correct source for auto-play"""
        if self._playback_source == 'playlist':
            logger.info("Song ended (playlist mode) - auto-playing next")
            self._play_next_from_playlist()
        else:
            logger.info("Song ended (library mode)")
            if self.library_tab:
                self.library_tab._on_song_ended()

    # ==========================================
    # Playlist Playback
    # ==========================================

    def play_song_from_playlist(self, song_info: dict):
        """Play song from playlist widget"""
        try:
            file_path = song_info.get('file_path')
            if not file_path:
                logger.error("Song has no file path")
                return

            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                QMessageBox.warning(
                    self.parent(), "File Not Found",
                    f"The music file could not be found:\n{file_path}"
                )
                return

            success = self.audio_player.load(file_path)
            if success:
                self.audio_player.play()
                self.now_playing.load_song(song_info)
                self.now_playing.set_playing(True)

                # Track playback source as playlist
                self._playback_source = 'playlist'
                self._current_playlist_id = (
                    self.playlist_widget.current_playlist_id if self.playlist_widget else None
                )

                # Get current playlist songs and find index
                if self._current_playlist_id:
                    self._current_playlist_songs = self.playlist_manager.get_playlist_songs(
                        self._current_playlist_id
                    )
                    song_id = song_info.get('id')
                    for i, s in enumerate(self._current_playlist_songs):
                        if s.get('id') == song_id:
                            self._current_playlist_index = i
                            break

                    if song_id and self.playlist_widget:
                        self.playlist_widget.highlight_playing_song(song_id)

                logger.info(
                    f"Playing from playlist: {song_info.get('title', 'Unknown')} "
                    f"(index {self._current_playlist_index}/{len(self._current_playlist_songs)})"
                )
            else:
                logger.error(f"Failed to load: {file_path}")

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error playing song from playlist: {e}")

    def _play_next_from_playlist(self):
        """Play next song in current playlist"""
        if not self._current_playlist_songs:
            logger.warning("No playlist songs loaded")
            return

        next_index = self._current_playlist_index + 1

        if next_index >= len(self._current_playlist_songs):
            logger.info("Reached end of playlist")
            if self.status_bar:
                self.status_bar.showMessage("End of playlist", 2000)
            return

        next_song = self._current_playlist_songs[next_index]
        song_info = self.db_manager.get_song_by_id(next_song['id'])

        if song_info:
            self._current_playlist_index = next_index
            self.play_song_from_playlist(song_info)
            logger.info(f"Playing next in playlist: {song_info.get('title')}")
        else:
            logger.error(f"Song not found: {next_song['id']}")

    def _play_prev_from_playlist(self):
        """Play previous song in current playlist"""
        if not self._current_playlist_songs:
            logger.warning("No playlist songs loaded")
            return

        prev_index = self._current_playlist_index - 1

        if prev_index < 0:
            logger.info("Already at beginning of playlist")
            if self.status_bar:
                self.status_bar.showMessage("Beginning of playlist", 2000)
            return

        prev_song = self._current_playlist_songs[prev_index]
        song_info = self.db_manager.get_song_by_id(prev_song['id'])

        if song_info:
            self._current_playlist_index = prev_index
            self.play_song_from_playlist(song_info)
            logger.info(f"Playing previous in playlist: {song_info.get('title')}")
        else:
            logger.error(f"Song not found: {prev_song['id']}")

    def play_recommended_song(self, song_data: dict):
        """Play a song selected from recommendations"""
        try:
            file_path = song_data.get('file_path')
            if not file_path:
                logger.error("Recommended song has no file path")
                return

            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                QMessageBox.warning(
                    self.parent(), "File Not Found",
                    f"The music file could not be found:\n{file_path}"
                )
                return

            success = self.audio_player.load(file_path)
            if success:
                self.audio_player.play()
                self.now_playing.load_song(song_data)
                self.now_playing.set_playing(True)
                self._playback_source = 'library'

                logger.info(f"Playing recommended: {song_data.get('title')}")
                if self.status_bar:
                    self.status_bar.showMessage(
                        f"Playing recommendation: {song_data.get('title')}", 3000
                    )
            else:
                logger.error(f"Failed to load: {file_path}")

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error playing recommended song: {e}")

    # ==========================================
    # Keyboard Shortcut Handlers
    # ==========================================

    def handle_play_pause(self):
        """Handle Space key — Play/Pause"""
        self.now_playing._on_play_clicked()
        logger.debug("Shortcut: Play/Pause toggled")

    def handle_seek_backward(self, seconds):
        """Handle Left arrow — Seek backward"""
        current = self.audio_player.get_position()
        new_pos = max(0, current - seconds)
        logger.debug(f"Seek backward: current={current:.2f}s, new_pos={new_pos:.2f}s")
        self.audio_player.seek(new_pos)

    def handle_seek_forward(self, seconds):
        """Handle Right arrow — Seek forward"""
        current = self.audio_player.get_position()
        duration = self.audio_player.get_duration()
        new_pos = min(duration, current + seconds)
        logger.debug(f"Seek forward: current={current:.2f}s, new_pos={new_pos:.2f}s")
        self.audio_player.seek(new_pos)

    def handle_volume_change(self, delta):
        """Handle Up/Down arrows — Volume change"""
        try:
            import pygame
            current = pygame.mixer.music.get_volume()
            new_volume = max(0.0, min(1.0, current + (delta / 100.0)))
            self.audio_player.set_volume(new_volume)

            percentage = int(new_volume * 100)
            if hasattr(self.now_playing, 'volume_slider'):
                self.now_playing.volume_slider.blockSignals(True)
                self.now_playing.volume_slider.setValue(percentage)
                self.now_playing.volume_slider.blockSignals(False)
                if hasattr(self.now_playing, 'volume_label_value'):
                    self.now_playing.volume_label_value.setText(f"{percentage}%")

            if self.status_bar:
                self.status_bar.showMessage(f"Volume: {percentage}%", 1000)
            logger.debug(f"Shortcut: Volume {percentage}%")
        except (RuntimeError, AttributeError) as e:
            logger.error(f"Volume change failed: {e}")

    def handle_mute_toggle(self):
        """Handle M key — Mute/Unmute"""
        try:
            import pygame
            current = pygame.mixer.music.get_volume()

            if current > 0:
                self._previous_volume = current
                self.audio_player.set_volume(0.0)

                if hasattr(self.now_playing, 'volume_slider'):
                    self.now_playing.volume_slider.blockSignals(True)
                    self.now_playing.volume_slider.setValue(0)
                    self.now_playing.volume_slider.blockSignals(False)
                    if hasattr(self.now_playing, 'volume_label_value'):
                        self.now_playing.volume_label_value.setText("0%")

                if self.status_bar:
                    self.status_bar.showMessage("Muted", 1000)
                logger.debug("Shortcut: Muted")
            else:
                volume = self._previous_volume
                self.audio_player.set_volume(volume)

                percentage = int(volume * 100)
                if hasattr(self.now_playing, 'volume_slider'):
                    self.now_playing.volume_slider.blockSignals(True)
                    self.now_playing.volume_slider.setValue(percentage)
                    self.now_playing.volume_slider.blockSignals(False)
                    if hasattr(self.now_playing, 'volume_label_value'):
                        self.now_playing.volume_label_value.setText(f"{percentage}%")

                if self.status_bar:
                    self.status_bar.showMessage(f"Volume: {percentage}%", 1000)
                logger.debug(f"Shortcut: Unmuted to {percentage}%")
        except (RuntimeError, AttributeError) as e:
            logger.error(f"Mute toggle failed: {e}")
