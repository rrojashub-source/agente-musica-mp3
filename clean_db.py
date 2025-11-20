"""
Clean Unknown Artist/Album from database
Extracts artist from title format "Artist - Song"
"""
import sqlite3

db_path = "music_library.db"

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count contaminated songs
cursor.execute("""
    SELECT COUNT(*) FROM songs
    WHERE artist = 'Unknown Artist' OR album = 'Unknown Album'
""")
contaminated = cursor.fetchone()[0]
print(f"🔍 Found {contaminated} songs with Unknown Artist/Album")

# Extract artist from title
cursor.execute("""
    UPDATE songs
    SET artist = TRIM(SUBSTR(title, 1, INSTR(title, ' - ') - 1))
    WHERE artist = 'Unknown Artist'
      AND title LIKE '%-%'
      AND INSTR(title, ' - ') > 0
""")
artist_fixed = cursor.rowcount
print(f"✅ Fixed {artist_fixed} artists (extracted from title)")

# Clean album (set to empty instead of Unknown)
cursor.execute("""
    UPDATE songs
    SET album = ''
    WHERE album = 'Unknown Album'
""")
album_fixed = cursor.rowcount
print(f"✅ Cleaned {album_fixed} albums (set to empty)")

# Commit changes
conn.commit()

# Show final stats
cursor.execute("""
    SELECT
        COUNT(*) as total_songs,
        SUM(CASE WHEN artist = 'Unknown Artist' THEN 1 ELSE 0 END) as still_unknown_artist,
        SUM(CASE WHEN album = 'Unknown Album' THEN 1 ELSE 0 END) as still_unknown_album,
        SUM(CASE WHEN artist != 'Unknown Artist' AND artist != '' THEN 1 ELSE 0 END) as with_artist,
        SUM(CASE WHEN album != 'Unknown Album' AND album != '' THEN 1 ELSE 0 END) as with_album
    FROM songs
""")
stats = cursor.fetchone()

print(f"\n📊 Final Stats:")
print(f"   Total songs: {stats[0]}")
print(f"   With artist: {stats[3]}")
print(f"   With album: {stats[4]}")
print(f"   Still unknown artist: {stats[1]}")
print(f"   Still unknown album: {stats[2]}")

conn.close()
print("\n✅ Database cleaned successfully!")
