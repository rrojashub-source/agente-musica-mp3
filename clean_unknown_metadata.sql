-- Clean Unknown Artist/Album from contaminated database
-- This will revert songs with 'Unknown Artist' or 'Unknown Album'
-- back to their original values before the bad update

-- First, let's see how many songs are affected
SELECT COUNT(*) as contaminated_songs
FROM songs
WHERE artist = 'Unknown Artist' OR album = 'Unknown Album';

-- Update: Set artist back to extracted from title if possible
-- Title format: "Artist - Song"
UPDATE songs
SET artist = CASE
    WHEN artist = 'Unknown Artist' AND title LIKE '%-%'
    THEN TRIM(SUBSTR(title, 1, INSTR(title, ' - ') - 1))
    ELSE artist
END
WHERE artist = 'Unknown Artist' AND title LIKE '%-%';

-- For album, if it's Unknown, leave it as is (we don't have good data)
-- Or we could set it to empty string
UPDATE songs
SET album = ''
WHERE album = 'Unknown Album';

-- Show results
SELECT
    COUNT(*) as total_songs,
    SUM(CASE WHEN artist = 'Unknown Artist' THEN 1 ELSE 0 END) as still_unknown_artist,
    SUM(CASE WHEN album = 'Unknown Album' THEN 1 ELSE 0 END) as still_unknown_album
FROM songs;
