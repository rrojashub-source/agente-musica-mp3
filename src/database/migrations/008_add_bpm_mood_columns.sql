-- Migration 008: Add BPM and Mood columns for AI analysis
-- Phase 9: AI-powered audio analysis features

-- Add BPM column (beats per minute, typically 60-200)
ALTER TABLE songs ADD COLUMN bpm INTEGER;

-- Add Mood column (Energetic, Happy, Calm, Sad, Intense)
ALTER TABLE songs ADD COLUMN mood TEXT;

-- Add Energy score (0-100, composite of tempo + loudness + dynamics)
ALTER TABLE songs ADD COLUMN energy INTEGER;

-- Add Valence score (0-100, musical positiveness/happiness)
ALTER TABLE songs ADD COLUMN valence INTEGER;

-- Create indexes for filtering by mood/energy
CREATE INDEX IF NOT EXISTS idx_songs_bpm ON songs(bpm);
CREATE INDEX IF NOT EXISTS idx_songs_mood ON songs(mood);
CREATE INDEX IF NOT EXISTS idx_songs_energy ON songs(energy);
