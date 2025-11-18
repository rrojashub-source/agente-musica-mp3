#!/usr/bin/env python3
r"""
Convert WSL paths to Windows paths in database

Problem: Database has WSL paths like /mnt/c/Users/ricar/Music/...
Solution: Convert to Windows paths like C:\Users\ricar\Music\...

Created: November 18, 2025
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.manager import DatabaseManager

def convert_wsl_to_windows(wsl_path: str) -> str:
    r"""
    Convert WSL path to Windows path

    /mnt/c/Users/ricar/Music/... -> C:\Users\ricar\Music\...
    /mnt/d/... -> D:\...
    """
    if wsl_path.startswith('/mnt/'):
        # Extract drive letter and rest of path
        parts = wsl_path.split('/')
        drive = parts[2].upper()  # 'c' -> 'C'
        rest = '/'.join(parts[3:])  # 'Users/ricar/Music/...'

        # Convert to Windows format
        windows_path = f"{drive}:\\{rest.replace('/', '\\')}"
        return windows_path

    return wsl_path  # Already Windows format or other


def main():
    print("=" * 60)
    print("🔄 CONVERT WSL PATHS TO WINDOWS PATHS")
    print("=" * 60)
    print()

    db = DatabaseManager('music_library.db')

    # Get all songs
    songs = db.get_all_songs()

    print(f"Total songs: {len(songs)}")
    print()

    # Count paths to convert
    wsl_paths = [s for s in songs if s.get('file_path', '').startswith('/mnt/')]
    windows_paths = [s for s in songs if not s.get('file_path', '').startswith('/mnt/')]

    print(f"WSL paths (need conversion): {len(wsl_paths)}")
    print(f"Windows paths (already correct): {len(windows_paths)}")
    print()

    if len(wsl_paths) == 0:
        print("✅ All paths are already in Windows format!")
        db.close()
        return

    # Show examples
    print("Examples of conversion:")
    for song in wsl_paths[:3]:
        old_path = song.get('file_path', '')
        new_path = convert_wsl_to_windows(old_path)
        print(f"  Before: {old_path[:80]}...")
        print(f"  After:  {new_path[:80]}...")
        print()

    # Confirm
    response = input("Convert all WSL paths to Windows format? (yes/no): ").strip().lower()

    if response != 'yes':
        print("❌ Aborted")
        db.close()
        return

    print()
    print("Converting paths...")

    # Update each song
    updated = 0
    for song in wsl_paths:
        song_id = song.get('id')
        old_path = song.get('file_path', '')
        new_path = convert_wsl_to_windows(old_path)

        # Update in database
        success = db.update_song(song_id, {'file_path': new_path})

        if success:
            updated += 1
            if updated % 50 == 0:
                print(f"  Updated {updated}/{len(wsl_paths)} songs...")

    print()
    print(f"✅ Converted {updated} paths successfully!")
    print()

    # Verify
    print("Verification:")
    songs = db.get_all_songs()
    wsl_remaining = [s for s in songs if s.get('file_path', '').startswith('/mnt/')]

    print(f"  WSL paths remaining: {len(wsl_remaining)}")
    print(f"  Windows paths: {len(songs) - len(wsl_remaining)}")

    if len(wsl_remaining) == 0:
        print()
        print("=" * 60)
        print("✅ ALL PATHS CONVERTED TO WINDOWS FORMAT!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart the application")
        print("2. Try playing songs - no more 'File not found' errors")

    db.close()


if __name__ == '__main__':
    main()
