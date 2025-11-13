-- Migration 001: Create songs table
-- Phase 1-3: Core library management

CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT,
    album TEXT,
    year INTEGER,
    genre TEXT,
    duration INTEGER,  -- Duration in seconds
    file_path TEXT NOT NULL UNIQUE,
    file_size INTEGER,
    bitrate INTEGER,
    sample_rate INTEGER,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    play_count INTEGER DEFAULT 0,
    last_played TIMESTAMP
);

-- Create indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist);
CREATE INDEX IF NOT EXISTS idx_songs_album ON songs(album);
CREATE INDEX IF NOT EXISTS idx_songs_genre ON songs(genre);
CREATE INDEX IF NOT EXISTS idx_songs_year ON songs(year);
CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title);

-- Create FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS songs_fts USING fts5(
    title,
    artist,
    album,
    genre,
    content=songs,
    content_rowid=id
);

-- Triggers to keep FTS5 in sync
CREATE TRIGGER IF NOT EXISTS songs_ai AFTER INSERT ON songs BEGIN
    INSERT INTO songs_fts(rowid, title, artist, album, genre)
    VALUES (new.id, new.title, new.artist, new.album, new.genre);
END;

CREATE TRIGGER IF NOT EXISTS songs_ad AFTER DELETE ON songs BEGIN
    DELETE FROM songs_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS songs_au AFTER UPDATE ON songs BEGIN
    UPDATE songs_fts SET
        title = new.title,
        artist = new.artist,
        album = new.album,
        genre = new.genre
    WHERE rowid = new.id;
END;

-- Trigger to update modified_date
CREATE TRIGGER IF NOT EXISTS update_songs_modified_date
AFTER UPDATE ON songs
BEGIN
    UPDATE songs SET modified_date = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
