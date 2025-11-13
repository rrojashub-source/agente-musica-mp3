-- Migration 007: Create Playlists Tables for Phase 7.1
-- Created: November 13, 2025
-- Purpose: Support playlist management functionality

-- Playlists table
CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Playlist songs junction table
CREATE TABLE IF NOT EXISTS playlist_songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    song_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE (playlist_id, song_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_playlist_songs_playlist_id ON playlist_songs(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_songs_song_id ON playlist_songs(song_id);
CREATE INDEX IF NOT EXISTS idx_playlist_songs_position ON playlist_songs(playlist_id, position);

-- Trigger to update modified_date on playlist changes
CREATE TRIGGER IF NOT EXISTS update_playlist_modified_date
AFTER UPDATE ON playlists
BEGIN
    UPDATE playlists SET modified_date = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger to update playlist modified_date when songs added/removed
CREATE TRIGGER IF NOT EXISTS update_playlist_modified_on_song_change
AFTER INSERT ON playlist_songs
BEGIN
    UPDATE playlists SET modified_date = CURRENT_TIMESTAMP WHERE id = NEW.playlist_id;
END;
