"""
Check which database files are valid (not corrupted)
"""
import sqlite3
import os
from pathlib import Path

db_files = [
    "music_library.db",
    "music_library_contaminated_20251119.db",
    "music_library_backup_20251118_204041.db",
    "music_library_backup_20251118_200302.db",
    "music_library_backup_20251118_064442.db",
]

print("🔍 Checking database integrity...\n")

for db_file in db_files:
    if not os.path.exists(db_file):
        print(f"❌ {db_file}: NOT FOUND")
        continue

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]

        if result == "ok":
            # Get stats
            cursor.execute("SELECT COUNT(*) FROM songs")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM songs WHERE artist = 'Unknown Artist'")
            unknown = cursor.fetchone()[0]

            cursor.execute("SELECT MAX(duration) FROM songs")
            max_duration = cursor.fetchone()[0]

            print(f"✅ {db_file}:")
            print(f"   Songs: {total}")
            print(f"   Unknown Artist: {unknown}")
            print(f"   Max Duration: {max_duration}s ({max_duration/3600:.1f}h)")

            # Check if durations are reasonable
            if max_duration > 36000:  # 10 hours
                print(f"   ⚠️  HAS DURATION BUG")
            else:
                print(f"   ✅ Durations OK")
            print()
        else:
            print(f"❌ {db_file}: CORRUPTED - {result}\n")

        conn.close()

    except Exception as e:
        print(f"❌ {db_file}: ERROR - {e}\n")

print("\n📊 Recommendation: Use the DB with most songs, no Unknown, and good durations")
