-- Migration 009: Add index for file_path column
-- Purpose: Improve performance of duplicate detection and file lookups
-- Created: December 11, 2025

-- Add index on file_path for faster duplicate detection
-- This significantly improves song_exists() and duplicate checking performance
CREATE INDEX IF NOT EXISTS idx_songs_file_path ON songs(file_path);

-- Add index on artist for faster artist filtering
CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist);

-- Add index on album for faster album filtering
CREATE INDEX IF NOT EXISTS idx_songs_album ON songs(album);

-- Add composite index for common queries (artist + album)
CREATE INDEX IF NOT EXISTS idx_songs_artist_album ON songs(artist, album);
