-- Migration 010: Create play history table for statistics
-- Purpose: Track detailed listening history for analytics dashboard
-- Created: December 11, 2025

-- Play history table - stores each play event
CREATE TABLE IF NOT EXISTS play_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_played INTEGER DEFAULT 0,  -- Seconds actually played
    completed BOOLEAN DEFAULT 0,         -- Did user listen to full song?
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

-- Indexes for efficient statistics queries
CREATE INDEX IF NOT EXISTS idx_play_history_song_id ON play_history(song_id);
CREATE INDEX IF NOT EXISTS idx_play_history_played_at ON play_history(played_at);
CREATE INDEX IF NOT EXISTS idx_play_history_date ON play_history(date(played_at));

-- Daily aggregates table for faster dashboard loading
CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,           -- YYYY-MM-DD format
    total_plays INTEGER DEFAULT 0,
    total_duration INTEGER DEFAULT 0,    -- Total seconds played
    unique_songs INTEGER DEFAULT 0,
    unique_artists INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);
