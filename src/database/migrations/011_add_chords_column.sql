-- Migration 011: Add chords column for caching detected chord data
-- Stores JSON: [{"t": 0.0, "chord": "C"}, {"t": 2.5, "chord": "Am"}, ...]
ALTER TABLE songs ADD COLUMN chords TEXT DEFAULT NULL;
