"""
Playlist Widget - Phase 7.2 (Fixed)

GUI for managing playlists.

Features:
- Display all playlists in left panel
- Show songs of selected playlist in right panel
- Create/delete/rename playlists
- Add songs to playlists from library (WORKING)
- Import/export .m3u8 files
- Context menu for quick actions
- Double-click to play song from playlist
- Remove songs from playlist

Created: November 13, 2025
Updated: November 22, 2025 (Fixed song selection dialog)
"""
import logging
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QFileDialog,
    QHeaderView, QAbstractItemView, QLabel, QMenu, QDialog,
    QDialogButtonBox, QCheckBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from pathlib import Path

logger = logging.getLogger(__name__)


class SongSelectionDialog(QDialog):
    """Dialog to select songs from library to add to playlist"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_song_ids = []

        self.setWindowTitle("Select Songs to Add")
        self.setMinimumSize(600, 400)
        self._init_ui()
        self._load_songs()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Instructions
        label = QLabel("Select songs to add to playlist:")
        layout.addWidget(label)

        # Songs table with checkboxes
        self.songs_table = QTableWidget()
        self.songs_table.setColumnCount(4)
        self.songs_table.setHorizontalHeaderLabels(['Select', 'Title', 'Artist', 'Album'])
        self.songs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.songs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.songs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.songs_table)

        # Select all / none buttons
        select_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        select_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("Select None")
        self.select_none_btn.clicked.connect(self._select_none)
        select_layout.addWidget(self.select_none_btn)

        select_layout.addStretch()
        layout.addLayout(select_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_songs(self):
        """Load all songs from database"""
        try:
            songs = self.db_manager.get_all_songs()
            self.songs_table.setRowCount(len(songs))

            for row, song in enumerate(songs):
                # Checkbox
                checkbox = QCheckBox()
                checkbox.setProperty('song_id', song.get('id'))
                self.songs_table.setCellWidget(row, 0, checkbox)

                # Title
                self.songs_table.setItem(row, 1, QTableWidgetItem(song.get('title', 'Unknown')))

                # Artist
                self.songs_table.setItem(row, 2, QTableWidgetItem(song.get('artist', 'Unknown')))

                # Album
                self.songs_table.setItem(row, 3, QTableWidgetItem(song.get('album', 'Unknown')))

        except Exception as e:
            logger.error(f"Failed to load songs: {e}")

    def _select_all(self):
        """Select all songs"""
        for row in range(self.songs_table.rowCount()):
            checkbox = self.songs_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)

    def _select_none(self):
        """Deselect all songs"""
        for row in range(self.songs_table.rowCount()):
            checkbox = self.songs_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def _on_accept(self):
        """Collect selected song IDs and accept"""
        self.selected_song_ids = []
        for row in range(self.songs_table.rowCount()):
            checkbox = self.songs_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                song_id = checkbox.property('song_id')
                if song_id:
                    self.selected_song_ids.append(song_id)
        self.accept()

    def get_selected_songs(self) -> List[int]:
        """Get list of selected song IDs"""
        return self.selected_song_ids


class PlaylistWidget(QWidget):
    """
    Playlist management widget

    Left panel: List of all playlists
    Right panel: Songs in selected playlist

    Signals:
    - playlist_selected(playlist_id): Emitted when playlist is selected
    - playlist_created(playlist_id): Emitted when new playlist created
    - playlist_deleted(playlist_id): Emitted when playlist deleted
    """

    # Signals
    playlist_selected = pyqtSignal(int)
    playlist_created = pyqtSignal(int)
    playlist_deleted = pyqtSignal(int)
    play_song_requested = pyqtSignal(dict)  # Emitted when user wants to play a song from playlist

    def __init__(self, playlist_manager, db_manager, parent=None):
        """
        Initialize Playlist Widget

        Args:
            playlist_manager: PlaylistManager instance
            db_manager: Database manager instance
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.playlist_manager = playlist_manager
        self.db_manager = db_manager
        self.current_playlist_id = None
        self._current_playing_song_id = None  # Track currently playing song for highlight

        # No size restrictions - this is now a full tab

        self._init_ui()
        self.load_playlists()

        logger.info("PlaylistWidget initialized")

    def _init_ui(self):
        """Initialize UI components - Grid layout for playlists"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)

        # === TOP SECTION: Playlists Grid + Buttons ===
        top_section = QWidget()
        top_layout = QVBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Header with title and buttons
        header_layout = QHBoxLayout()

        title = QLabel("🎵 Your Playlists")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Buttons with clear text
        self.create_button = QPushButton("➕ Create Playlist")
        self.create_button.clicked.connect(self.create_playlist)
        header_layout.addWidget(self.create_button)

        self.delete_button = QPushButton("🗑️ Delete Playlist")
        self.delete_button.clicked.connect(self.delete_playlist)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)

        self.rename_button = QPushButton("✏️ Rename Playlist")
        self.rename_button.clicked.connect(self.rename_playlist)
        self.rename_button.setEnabled(False)
        header_layout.addWidget(self.rename_button)

        self.import_button = QPushButton("📥 Import Playlist (.m3u8)")
        self.import_button.clicked.connect(self.import_playlist)
        self.import_button.setToolTip("Import playlist from a .m3u8 file")
        header_layout.addWidget(self.import_button)

        self.export_button = QPushButton("📤 Export Playlist (.m3u8)")
        self.export_button.clicked.connect(self.export_playlist)
        self.export_button.setToolTip("Export selected playlist to a .m3u8 file")
        self.export_button.setEnabled(False)
        header_layout.addWidget(self.export_button)

        top_layout.addLayout(header_layout)

        # Playlists displayed as a table/grid (multiple columns)
        self.playlists_table = QTableWidget()
        self.playlists_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.playlists_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.playlists_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.playlists_table.itemClicked.connect(self._on_playlist_cell_clicked)
        self.playlists_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlists_table.customContextMenuRequested.connect(self._show_context_menu)
        self.playlists_table.setMaximumHeight(150)  # Compact grid
        self.playlists_table.horizontalHeader().setVisible(False)
        self.playlists_table.verticalHeader().setVisible(False)
        self.playlists_table.setShowGrid(True)
        top_layout.addWidget(self.playlists_table)

        # === BOTTOM SECTION: Songs in selected playlist ===
        bottom_section = self._create_songs_panel()

        # Vertical splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(top_section)
        splitter.addWidget(bottom_section)
        splitter.setSizes([200, 400])

        main_layout.addWidget(splitter)

    def _create_songs_panel(self) -> QWidget:
        """Create bottom panel with playlist songs"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        panel.setLayout(layout)

        # Header row with label and add button
        header_layout = QHBoxLayout()

        self.songs_label = QLabel("📋 Select a playlist above to see its songs")
        self.songs_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(self.songs_label)

        header_layout.addStretch()

        # Add songs button
        self.add_songs_button = QPushButton("➕ Add Songs from Library")
        self.add_songs_button.clicked.connect(self.add_songs_to_playlist)
        self.add_songs_button.setEnabled(False)
        header_layout.addWidget(self.add_songs_button)

        layout.addLayout(header_layout)

        # Songs table
        self.songs_table = QTableWidget()
        self.songs_table.setColumnCount(4)
        self.songs_table.setHorizontalHeaderLabels(['Title', 'Artist', 'Album', 'Duration'])
        self.songs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.songs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.songs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.songs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.songs_table.setColumnWidth(3, 80)
        self.songs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.songs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Double-click to play
        self.songs_table.itemDoubleClicked.connect(self._on_song_double_clicked)

        # Context menu for songs
        self.songs_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.songs_table.customContextMenuRequested.connect(self._show_songs_context_menu)

        layout.addWidget(self.songs_table)

        return panel

    # ========== PLAYLIST OPERATIONS ==========

    def load_playlists(self):
        """Load all playlists from database into grid"""
        try:
            playlists = self.playlist_manager.get_playlists()

            # Calculate grid dimensions (4 columns)
            num_cols = 4
            num_rows = (len(playlists) + num_cols - 1) // num_cols if playlists else 1

            self.playlists_table.setRowCount(num_rows)
            self.playlists_table.setColumnCount(num_cols)

            # Set column widths to stretch
            for col in range(num_cols):
                self.playlists_table.horizontalHeader().setSectionResizeMode(
                    col, QHeaderView.ResizeMode.Stretch
                )

            # Fill grid with playlists
            for i, playlist in enumerate(playlists):
                row = i // num_cols
                col = i % num_cols

                item_text = f"{playlist['name']}\n({playlist['song_count']} songs)"
                item = QTableWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, playlist['id'])
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.playlists_table.setItem(row, col, item)

            # Set row heights
            for row in range(num_rows):
                self.playlists_table.setRowHeight(row, 50)

            logger.info(f"Loaded {len(playlists)} playlists into grid")

        except Exception as e:
            logger.error(f"Failed to load playlists: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load playlists: {e}")

    def create_playlist(self):
        """Create new playlist"""
        try:
            # Get playlist name from user
            name, ok = QInputDialog.getText(self, "Create Playlist", "Playlist name:")

            if ok and name:
                # Create playlist
                playlist_id = self.playlist_manager.create_playlist(name)

                # Reload playlists
                self.load_playlists()

                # Emit signal
                self.playlist_created.emit(playlist_id)

                logger.info(f"Created playlist: {name} (ID: {playlist_id})")
                QMessageBox.information(self, "Success", f"Playlist '{name}' created!")

        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create playlist: {e}")

    def delete_playlist(self):
        """Delete selected playlist"""
        try:
            if not self.current_playlist_id:
                QMessageBox.warning(self, "No Selection", "Please select a playlist first")
                return

            playlist_name = self._get_current_playlist_name()

            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Delete Playlist",
                f"Are you sure you want to delete '{playlist_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                playlist_id = self.current_playlist_id

                # Delete playlist
                self.playlist_manager.delete_playlist(playlist_id)

                # Reload playlists
                self.load_playlists()

                # Clear songs panel
                self.songs_table.setRowCount(0)
                self.songs_label.setText("📋 Select a playlist above to see its songs")
                self.current_playlist_id = None
                self._current_playlist_item = None

                # Disable buttons
                self.delete_button.setEnabled(False)
                self.rename_button.setEnabled(False)
                self.export_button.setEnabled(False)
                self.add_songs_button.setEnabled(False)

                # Emit signal
                self.playlist_deleted.emit(playlist_id)

                logger.info(f"Deleted playlist: {playlist_name} (ID: {playlist_id})")
                QMessageBox.information(self, "Success", f"Playlist '{playlist_name}' deleted!")

        except Exception as e:
            logger.error(f"Failed to delete playlist: {e}")
            QMessageBox.warning(self, "Error", f"Failed to delete playlist: {e}")

    def rename_playlist(self):
        """Rename selected playlist"""
        try:
            if not self.current_playlist_id:
                QMessageBox.warning(self, "No Selection", "Please select a playlist first")
                return

            old_name = self._get_current_playlist_name()

            # Get new name from user
            new_name, ok = QInputDialog.getText(
                self,
                "Rename Playlist",
                "New playlist name:",
                text=old_name
            )

            if ok and new_name:
                # Update playlist name using manager
                success = self.playlist_manager.rename_playlist(self.current_playlist_id, new_name)

                if success:
                    # Reload playlists
                    self.load_playlists()

                    logger.info(f"Renamed playlist {self.current_playlist_id}: {old_name} → {new_name}")
                    QMessageBox.information(self, "Success", f"Playlist renamed to '{new_name}'!")
                else:
                    logger.error(f"Failed to rename playlist {self.current_playlist_id}")
                    QMessageBox.warning(self, "Error", f"Failed to rename playlist")

        except Exception as e:
            logger.error(f"Failed to rename playlist: {e}")
            QMessageBox.warning(self, "Error", f"Failed to rename playlist: {e}")

    def import_playlist(self):
        """Import playlist from .m3u8 file"""
        try:
            # Get file path from user
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Playlist",
                "",
                "M3U8 Files (*.m3u8);;All Files (*)"
            )

            if file_path:
                # Import playlist
                playlist_id = self.playlist_manager.load_playlist(file_path)

                if playlist_id:
                    # Reload playlists
                    self.load_playlists()

                    # Emit signal
                    self.playlist_created.emit(playlist_id)

                    logger.info(f"Imported playlist from {file_path}")
                    QMessageBox.information(self, "Success", "Playlist imported successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to import playlist")

        except Exception as e:
            logger.error(f"Failed to import playlist: {e}")
            QMessageBox.warning(self, "Error", f"Failed to import playlist: {e}")

    def export_playlist(self):
        """Export selected playlist to .m3u8 file"""
        try:
            if not self.current_playlist_id:
                QMessageBox.warning(self, "No Selection", "Please select a playlist first")
                return

            playlist_name = self._get_current_playlist_name()

            # Get save path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Playlist",
                f"{playlist_name}.m3u8",
                "M3U8 Files (*.m3u8);;All Files (*)"
            )

            if file_path:
                # Export playlist
                success = self.playlist_manager.save_playlist(self.current_playlist_id, file_path)

                if success:
                    logger.info(f"Exported playlist {self.current_playlist_id} to {file_path}")
                    QMessageBox.information(self, "Success", "Playlist exported successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to export playlist")

        except Exception as e:
            logger.error(f"Failed to export playlist: {e}")
            QMessageBox.warning(self, "Error", f"Failed to export playlist: {e}")

    # ========== SONG OPERATIONS ==========

    def add_songs_to_playlist(self):
        """Add songs to current playlist from library"""
        try:
            if not self.current_playlist_id:
                QMessageBox.warning(self, "No Playlist", "Please select a playlist first")
                return

            # Get song IDs from selection dialog
            song_ids = self.select_songs_dialog()

            if song_ids:
                # Add each song to playlist
                added_count = 0
                for song_id in song_ids:
                    if self.playlist_manager.add_song(self.current_playlist_id, song_id):
                        added_count += 1

                # Reload songs in the table
                self.load_playlist_songs(self.current_playlist_id)

                # Reload playlists grid to update song count
                self.load_playlists()

                logger.info(f"Added {added_count} songs to playlist {self.current_playlist_id}")
                QMessageBox.information(self, "Success", f"Added {added_count} songs to playlist!")

        except Exception as e:
            logger.error(f"Failed to add songs to playlist: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add songs: {e}")

    def select_songs_dialog(self) -> List[int]:
        """
        Open dialog to select songs from library

        Returns:
            List of selected song IDs
        """
        dialog = SongSelectionDialog(self.db_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_songs()
        return []

    # ========== EVENT HANDLERS ==========

    def _on_playlist_cell_clicked(self, item: QTableWidgetItem):
        """Handle playlist selection from grid"""
        if item is None:
            return

        try:
            playlist_id = item.data(Qt.ItemDataRole.UserRole)
            if playlist_id is None:
                return

            self.current_playlist_id = playlist_id
            self._current_playlist_item = item  # Store reference

            # Enable/disable buttons
            self.delete_button.setEnabled(True)
            self.rename_button.setEnabled(True)
            self.export_button.setEnabled(True)
            self.add_songs_button.setEnabled(True)

            # Load playlist songs
            self.load_playlist_songs(playlist_id)

            # Emit signal
            self.playlist_selected.emit(playlist_id)

        except Exception as e:
            logger.error(f"Failed to handle playlist selection: {e}")

    def _get_current_playlist_name(self) -> str:
        """Get name of currently selected playlist"""
        if hasattr(self, '_current_playlist_item') and self._current_playlist_item:
            text = self._current_playlist_item.text()
            # Name is before the newline
            return text.split('\n')[0] if '\n' in text else text.split(' (')[0]
        return "Unknown"

    def load_playlist_songs(self, playlist_id: int):
        """Load songs for selected playlist"""
        try:
            # Update label
            playlist_name = self._get_current_playlist_name()
            self.songs_label.setText(f"📋 Playlist: {playlist_name}")

            # Get playlist songs
            songs = self.playlist_manager.get_playlist_songs(playlist_id)

            # Populate table
            self.songs_table.setRowCount(len(songs))

            for row, song in enumerate(songs):
                song_id = song.get('id')

                # Title (store song_id in UserRole for later reference)
                title_item = QTableWidgetItem(song.get('title', 'Unknown'))
                title_item.setData(Qt.ItemDataRole.UserRole, song_id)
                self.songs_table.setItem(row, 0, title_item)

                # Artist
                self.songs_table.setItem(row, 1, QTableWidgetItem(song.get('artist', 'Unknown')))

                # Album
                self.songs_table.setItem(row, 2, QTableWidgetItem(song.get('album', 'Unknown')))

                # Duration (convert seconds to MM:SS)
                duration_sec = song.get('duration', 0)
                minutes = int(duration_sec // 60)
                seconds = int(duration_sec % 60)
                duration_str = f"{minutes}:{seconds:02d}"
                self.songs_table.setItem(row, 3, QTableWidgetItem(duration_str))

                # Apply highlight if this is the currently playing song
                if song_id == self._current_playing_song_id:
                    self._highlight_row(row, True)

            logger.info(f"Loaded {len(songs)} songs for playlist {playlist_id}")

        except Exception as e:
            logger.error(f"Failed to load playlist songs: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load songs: {e}")

    def _show_context_menu(self, position):
        """Show context menu for playlists grid"""
        try:
            item = self.playlists_table.itemAt(position)
            if not item:
                return

            # Select the item first
            self._on_playlist_cell_clicked(item)

            menu = QMenu(self)

            # Rename action
            rename_action = QAction("✏️ Rename Playlist", self)
            rename_action.triggered.connect(self.rename_playlist)
            menu.addAction(rename_action)

            # Delete action
            delete_action = QAction("🗑️ Delete Playlist", self)
            delete_action.triggered.connect(self.delete_playlist)
            menu.addAction(delete_action)

            menu.addSeparator()

            # Export action
            export_action = QAction("📤 Export to .m3u8", self)
            export_action.triggered.connect(self.export_playlist)
            menu.addAction(export_action)

            # Show menu at cursor position
            menu.exec(self.playlists_table.mapToGlobal(position))

        except Exception as e:
            logger.error(f"Failed to show context menu: {e}")

    def _on_song_double_clicked(self, item: QTableWidgetItem):
        """Handle double-click on song to play it"""
        try:
            row = item.row()
            songs = self.playlist_manager.get_playlist_songs(self.current_playlist_id)

            if row < len(songs):
                song = songs[row]
                # Get full song info from database
                song_info = self.db_manager.get_song_by_id(song['id'])
                if song_info:
                    logger.info(f"Playing song from playlist: {song_info.get('title')}")
                    self.play_song_requested.emit(song_info)
                else:
                    logger.error(f"Song not found in database: {song['id']}")

        except Exception as e:
            logger.error(f"Failed to play song: {e}")

    def _show_songs_context_menu(self, position):
        """Show context menu for songs table"""
        try:
            item = self.songs_table.itemAt(position)
            if not item or not self.current_playlist_id:
                return

            row = item.row()
            songs = self.playlist_manager.get_playlist_songs(self.current_playlist_id)

            if row >= len(songs):
                return

            song = songs[row]

            menu = QMenu(self)

            # Play action
            play_action = QAction("▶ Play", self)
            play_action.triggered.connect(lambda: self._play_song_at_row(row))
            menu.addAction(play_action)

            menu.addSeparator()

            # Remove from playlist action
            remove_action = QAction("🗑️ Remove from Playlist", self)
            remove_action.triggered.connect(lambda: self._remove_song_from_playlist(song['id'], row))
            menu.addAction(remove_action)

            # Show menu at cursor position
            menu.exec(self.songs_table.mapToGlobal(position))

        except Exception as e:
            logger.error(f"Failed to show songs context menu: {e}")

    def _play_song_at_row(self, row: int):
        """Play song at specified row"""
        try:
            songs = self.playlist_manager.get_playlist_songs(self.current_playlist_id)

            if row < len(songs):
                song = songs[row]
                song_info = self.db_manager.get_song_by_id(song['id'])
                if song_info:
                    logger.info(f"Playing song from playlist: {song_info.get('title')}")
                    self.play_song_requested.emit(song_info)

        except Exception as e:
            logger.error(f"Failed to play song at row {row}: {e}")

    def _remove_song_from_playlist(self, song_id: int, row: int):
        """Remove song from current playlist"""
        try:
            # Confirm removal
            title_item = self.songs_table.item(row, 0)
            song_title = title_item.text() if title_item else "Unknown"

            reply = QMessageBox.question(
                self,
                "Remove Song",
                f"Remove '{song_title}' from this playlist?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success = self.playlist_manager.remove_song(self.current_playlist_id, song_id)

                if success:
                    # Reload songs
                    self.load_playlist_songs(self.current_playlist_id)
                    # Reload playlists to update song count
                    self.load_playlists()
                    logger.info(f"Removed song {song_id} from playlist {self.current_playlist_id}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to remove song")

        except Exception as e:
            logger.error(f"Failed to remove song from playlist: {e}")
            QMessageBox.warning(self, "Error", f"Failed to remove song: {e}")

    # ========== PLAYBACK HIGHLIGHT ==========

    def highlight_playing_song(self, song_id: int):
        """
        Highlight the currently playing song in the songs table.

        Called from main.py when a song from this playlist starts playing.

        Args:
            song_id: ID of the song that is now playing
        """
        # Clear previous highlight
        self.clear_playing_highlight()

        # Store current playing song
        self._current_playing_song_id = song_id

        # Find and highlight the row with this song_id
        for row in range(self.songs_table.rowCount()):
            title_item = self.songs_table.item(row, 0)
            if title_item:
                row_song_id = title_item.data(Qt.ItemDataRole.UserRole)
                if row_song_id == song_id:
                    self._highlight_row(row, True)
                    # Scroll to make it visible
                    self.songs_table.scrollToItem(title_item)
                    logger.info(f"Highlighted playing song: row {row}, song_id {song_id}")
                    break

    def clear_playing_highlight(self):
        """
        Clear the playing song highlight.

        Called when playback stops or switches to library.
        """
        self._current_playing_song_id = None

        # Remove highlight from all rows
        for row in range(self.songs_table.rowCount()):
            self._highlight_row(row, False)

    def _highlight_row(self, row: int, highlight: bool):
        """
        Apply or remove highlight styling from a row.

        Args:
            row: Row index
            highlight: True to highlight, False to remove
        """
        from PyQt6.QtGui import QColor, QBrush

        if highlight:
            # Neon cyan highlight (matches app theme)
            bg_color = QColor(0, 180, 220, 60)  # Semi-transparent cyan
            text_color = QColor(0, 220, 255)     # Bright cyan text
        else:
            # Default colors (let theme handle it)
            bg_color = QColor(0, 0, 0, 0)  # Transparent
            text_color = None

        for col in range(self.songs_table.columnCount()):
            item = self.songs_table.item(row, col)
            if item:
                item.setBackground(QBrush(bg_color))
                if text_color and highlight:
                    item.setForeground(QBrush(text_color))
