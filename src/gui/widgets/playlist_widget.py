"""
Playlist Widget - Phase 7.2

GUI for managing playlists.

Features:
- Display all playlists in left panel
- Show songs of selected playlist in right panel
- Create/delete/rename playlists
- Add songs to playlists from library
- Import/export .m3u8 files
- Context menu for quick actions

Created: November 13, 2025
"""
import logging
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QFileDialog,
    QHeaderView, QAbstractItemView, QLabel, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from pathlib import Path

logger = logging.getLogger(__name__)


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

        self._init_ui()
        self.load_playlists()

        logger.info("PlaylistWidget initialized")

    def _init_ui(self):
        """Initialize UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Title
        title = QLabel("Playlists")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title)

        # Splitter for left/right panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel: Playlists list
        left_panel = self._create_playlists_panel()
        splitter.addWidget(left_panel)

        # Right panel: Playlist songs
        right_panel = self._create_songs_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions (30% left, 70% right)
        splitter.setSizes([300, 700])

    def _create_playlists_panel(self) -> QWidget:
        """Create left panel with playlists list"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Label
        label = QLabel("Your Playlists")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        # Playlists list
        self.playlists_list = QListWidget()
        self.playlists_list.itemClicked.connect(self._on_playlist_selected)
        self.playlists_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlists_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.playlists_list)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.create_playlist)
        self.create_button.setToolTip("Create new playlist")
        buttons_layout.addWidget(self.create_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_playlist)
        self.delete_button.setToolTip("Delete selected playlist")
        self.delete_button.setEnabled(False)
        buttons_layout.addWidget(self.delete_button)

        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self.rename_playlist)
        self.rename_button.setToolTip("Rename selected playlist")
        self.rename_button.setEnabled(False)
        buttons_layout.addWidget(self.rename_button)

        layout.addLayout(buttons_layout)

        # Import/Export buttons
        io_layout = QHBoxLayout()

        self.import_button = QPushButton("Import .m3u8")
        self.import_button.clicked.connect(self.import_playlist)
        self.import_button.setToolTip("Import playlist from .m3u8 file")
        io_layout.addWidget(self.import_button)

        self.export_button = QPushButton("Export .m3u8")
        self.export_button.clicked.connect(self.export_playlist)
        self.export_button.setToolTip("Export playlist to .m3u8 file")
        self.export_button.setEnabled(False)
        io_layout.addWidget(self.export_button)

        layout.addLayout(io_layout)

        return panel

    def _create_songs_panel(self) -> QWidget:
        """Create right panel with playlist songs"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Label
        self.songs_label = QLabel("Select a playlist")
        self.songs_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.songs_label)

        # Songs table
        self.songs_table = QTableWidget()
        self.songs_table.setColumnCount(5)
        self.songs_table.setHorizontalHeaderLabels(['Title', 'Artist', 'Album', 'Duration', 'Position'])
        self.songs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.songs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.songs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.songs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.songs_table)

        # Add songs button
        self.add_songs_button = QPushButton("Add Songs from Library")
        self.add_songs_button.clicked.connect(self.add_songs_to_playlist)
        self.add_songs_button.setToolTip("Add songs to this playlist")
        self.add_songs_button.setEnabled(False)
        layout.addWidget(self.add_songs_button)

        return panel

    # ========== PLAYLIST OPERATIONS ==========

    def load_playlists(self):
        """Load all playlists from database"""
        try:
            playlists = self.playlist_manager.get_playlists()

            self.playlists_list.clear()

            for playlist in playlists:
                item_text = f"{playlist['name']} ({playlist['song_count']} songs)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, playlist['id'])
                self.playlists_list.addItem(item)

            logger.info(f"Loaded {len(playlists)} playlists")

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
            # Get selected playlist
            current_item = self.playlists_list.currentItem()
            if not current_item:
                return

            playlist_id = current_item.data(Qt.ItemDataRole.UserRole)
            playlist_name = current_item.text().split(' (')[0]

            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Delete Playlist",
                f"Are you sure you want to delete '{playlist_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Delete playlist
                self.playlist_manager.delete_playlist(playlist_id)

                # Reload playlists
                self.load_playlists()

                # Clear songs panel
                self.songs_table.setRowCount(0)
                self.songs_label.setText("Select a playlist")
                self.current_playlist_id = None

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
            # Get selected playlist
            current_item = self.playlists_list.currentItem()
            if not current_item:
                return

            playlist_id = current_item.data(Qt.ItemDataRole.UserRole)
            old_name = current_item.text().split(' (')[0]

            # Get new name from user
            new_name, ok = QInputDialog.getText(
                self,
                "Rename Playlist",
                "New playlist name:",
                text=old_name
            )

            if ok and new_name:
                # Update playlist name
                query = "UPDATE playlists SET name = ? WHERE id = ?"
                self.db_manager.execute_query(query, (new_name, playlist_id))

                # Reload playlists
                self.load_playlists()

                logger.info(f"Renamed playlist {playlist_id}: {old_name} → {new_name}")
                QMessageBox.information(self, "Success", f"Playlist renamed to '{new_name}'!")

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
            # Get selected playlist
            current_item = self.playlists_list.currentItem()
            if not current_item:
                return

            playlist_id = current_item.data(Qt.ItemDataRole.UserRole)
            playlist_name = current_item.text().split(' (')[0]

            # Get save path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Playlist",
                f"{playlist_name}.m3u8",
                "M3U8 Files (*.m3u8);;All Files (*)"
            )

            if file_path:
                # Export playlist
                success = self.playlist_manager.save_playlist(playlist_id, file_path)

                if success:
                    logger.info(f"Exported playlist {playlist_id} to {file_path}")
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
                return

            # Get song IDs from selection dialog
            # (This method should be implemented by parent widget or passed as callback)
            song_ids = self.select_songs_dialog()

            if song_ids:
                # Add each song to playlist
                for song_id in song_ids:
                    self.playlist_manager.add_song(self.current_playlist_id, song_id)

                # Reload songs
                self.load_playlist_songs(self.current_playlist_id)

                logger.info(f"Added {len(song_ids)} songs to playlist {self.current_playlist_id}")
                QMessageBox.information(self, "Success", f"Added {len(song_ids)} songs to playlist!")

        except Exception as e:
            logger.error(f"Failed to add songs to playlist: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add songs: {e}")

    def select_songs_dialog(self) -> List[int]:
        """
        Open dialog to select songs from library

        This is a placeholder method that should be overridden or connected
        to a real song selection dialog.

        Returns:
            List of selected song IDs
        """
        # Placeholder - should be implemented by parent or via callback
        logger.warning("select_songs_dialog not implemented - returning empty list")
        return []

    # ========== EVENT HANDLERS ==========

    def _on_playlist_selected(self, item: QListWidgetItem):
        """Handle playlist selection"""
        try:
            playlist_id = item.data(Qt.ItemDataRole.UserRole)
            self.current_playlist_id = playlist_id

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

    def load_playlist_songs(self, playlist_id: int):
        """Load songs for selected playlist"""
        try:
            # Update label
            playlist_name = self.playlists_list.currentItem().text().split(' (')[0]
            self.songs_label.setText(f"Playlist: {playlist_name}")

            # Get playlist songs
            songs = self.playlist_manager.get_playlist_songs(playlist_id)

            # Populate table
            self.songs_table.setRowCount(len(songs))

            for row, song in enumerate(songs):
                # Title
                self.songs_table.setItem(row, 0, QTableWidgetItem(song.get('title', 'Unknown')))

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

                # Position
                self.songs_table.setItem(row, 4, QTableWidgetItem(str(song.get('position', row))))

            logger.info(f"Loaded {len(songs)} songs for playlist {playlist_id}")

        except Exception as e:
            logger.error(f"Failed to load playlist songs: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load songs: {e}")

    def _show_context_menu(self, position):
        """Show context menu for playlists"""
        try:
            item = self.playlists_list.itemAt(position)
            if not item:
                return

            menu = QMenu(self)

            # Rename action
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(self.rename_playlist)
            menu.addAction(rename_action)

            # Delete action
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_playlist)
            menu.addAction(delete_action)

            menu.addSeparator()

            # Export action
            export_action = QAction("Export to .m3u8", self)
            export_action.triggered.connect(self.export_playlist)
            menu.addAction(export_action)

            # Show menu at cursor position
            menu.exec(self.playlists_list.mapToGlobal(position))

        except Exception as e:
            logger.error(f"Failed to show context menu: {e}")
