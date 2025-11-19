#!/usr/bin/env python3
r"""
Scan Music Folder

Find all MP3 files in C:\Users\ricar\Music and compare with database

Created: November 18, 2025
"""
import os
from pathlib import Path


def main():
    print("=" * 80)
    print("🎵 SCANNING MUSIC FOLDER")
    print("=" * 80)
    print()

    # Music folder location
    music_folder = Path("C:/Users/ricar/Music")

    if not music_folder.exists():
        # Try WSL path
        music_folder = Path("/mnt/c/Users/ricar/Music")

    if not music_folder.exists():
        print(f"❌ Music folder not found: {music_folder}")
        return

    print(f"📁 Scanning: {music_folder}")
    print()

    # Find all MP3 files
    mp3_files = list(music_folder.rglob("*.mp3"))

    print(f"✅ Found {len(mp3_files)} MP3 files")
    print()

    # Group by subdirectory
    directories = {}
    for mp3_file in mp3_files:
        parent = mp3_file.parent
        if parent not in directories:
            directories[parent] = []
        directories[parent].append(mp3_file)

    # Show directory structure
    print("=" * 80)
    print("DIRECTORY STRUCTURE")
    print("=" * 80)
    print()

    for directory in sorted(directories.keys()):
        count = len(directories[directory])
        relative_path = directory.relative_to(music_folder) if directory != music_folder else Path(".")
        print(f"📂 {relative_path} ({count} files)")

    print()

    # Show first 20 files
    print("=" * 80)
    print("SAMPLE FILES (First 20)")
    print("=" * 80)
    print()

    for i, mp3_file in enumerate(sorted(mp3_files)[:20], 1):
        relative_path = mp3_file.relative_to(music_folder)
        size_mb = mp3_file.stat().st_size / (1024 * 1024)
        print(f"{i:3}. {relative_path} ({size_mb:.2f} MB)")

    if len(mp3_files) > 20:
        print(f"\n... and {len(mp3_files) - 20} more files")

    print()


if __name__ == '__main__':
    main()
