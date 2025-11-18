#!/usr/bin/env python3
"""
Delete songs with WSL paths from database

Problem: Database has duplicates (311 WSL paths + 312 Windows paths)
Solution: Delete WSL paths, keep Windows paths

Created: November 18, 2025
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.manager import DatabaseManager

def main():
    print("=" * 60)
    print("🗑️  DELETE WSL PATHS FROM DATABASE")
    print("=" * 60)
    print()

    db = DatabaseManager('music_library.db')

    # Get all songs
    songs = db.get_all_songs()

    print(f"Total songs: {len(songs)}")
    print()

    # Count paths to delete
    wsl_paths = [s for s in songs if s.get('file_path', '').startswith('/mnt/')]
    windows_paths = [s for s in songs if not s.get('file_path', '').startswith('/mnt/')]

    print(f"WSL paths (will delete): {len(wsl_paths)}")
    print(f"Windows paths (will keep): {len(windows_paths)}")
    print()

    if len(wsl_paths) == 0:
        print("✅ No WSL paths found!")
        db.close()
        return

    # Show examples
    print("Examples of songs to DELETE:")
    for song in wsl_paths[:5]:
        title = song.get('title', 'Unknown')
        artist = song.get('artist', 'Unknown')
        path = song.get('file_path', '')
        print(f"  [{song.get('id')}] {artist} - {title}")
        print(f"      Path: {path[:80]}...")
        print()

    # Confirm
    response = input("Delete all songs with WSL paths? (yes/no): ").strip().lower()

    if response != 'yes':
        print("❌ Aborted")
        db.close()
        return

    print()
    print("Deleting songs with WSL paths...")

    # Delete each song
    deleted = 0
    cursor = db.conn.cursor()

    for song in wsl_paths:
        song_id = song.get('id')
        try:
            cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))
            deleted += 1

            if deleted % 50 == 0:
                print(f"  Deleted {deleted}/{len(wsl_paths)} songs...")
        except Exception as e:
            print(f"Failed to delete song {song_id}: {e}")

    db.conn.commit()

    print()
    print(f"✅ Deleted {deleted} songs with WSL paths!")
    print()

    # Verify
    print("Verification:")
    songs = db.get_all_songs()
    wsl_remaining = [s for s in songs if s.get('file_path', '').startswith('/mnt/')]

    print(f"  Total songs: {len(songs)}")
    print(f"  WSL paths remaining: {len(wsl_remaining)}")
    print(f"  Windows paths: {len(songs) - len(wsl_remaining)}")

    if len(wsl_remaining) == 0:
        print()
        print("=" * 60)
        print("✅ ALL WSL PATHS DELETED!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart the application")
        print("2. Library should work with Windows paths only")

    db.close()


if __name__ == '__main__':
    main()
