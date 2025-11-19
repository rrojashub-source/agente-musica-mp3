#!/usr/bin/env python3
"""
Diagnose Path Issues

Check if file_path entries in database actually exist on disk

Created: November 18, 2025
"""
import sys
import sqlite3
import os
from pathlib import Path


def main():
    print("=" * 80)
    print("🔍 PATH DIAGNOSIS")
    print("=" * 80)
    print()

    # Connect to database
    conn = sqlite3.connect('music_library.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all songs
    cursor.execute("SELECT id, title, artist, file_path FROM songs")
    rows = cursor.fetchall()
    songs = [dict(row) for row in rows]

    print(f"Total songs in database: {len(songs)}")
    print()

    # Check path validity
    valid_paths = []
    invalid_paths = []
    wsl_paths = []
    windows_paths = []

    for song in songs:
        file_path = song['file_path']

        # Categorize by path type
        if file_path.startswith('/mnt/'):
            wsl_paths.append(song)
        elif ':' in file_path:  # Windows path (C:, D:, etc.)
            windows_paths.append(song)

        # Check if file exists
        if os.path.exists(file_path):
            valid_paths.append(song)
        else:
            invalid_paths.append(song)

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ Valid paths (file exists):   {len(valid_paths)}")
    print(f"❌ Invalid paths (file missing): {len(invalid_paths)}")
    print()
    print(f"🐧 WSL paths (/mnt/...):        {len(wsl_paths)}")
    print(f"🪟 Windows paths (C:\\...):      {len(windows_paths)}")
    print()

    # Show examples of invalid paths
    if invalid_paths:
        print("=" * 80)
        print("EXAMPLES OF INVALID PATHS (First 10)")
        print("=" * 80)
        print()

        for song in invalid_paths[:10]:
            print(f"ID: {song['id']}")
            print(f"Title: {song['title']}")
            print(f"Artist: {song['artist']}")
            print(f"Path: {song['file_path']}")
            print(f"Exists: {os.path.exists(song['file_path'])}")
            print()

    # Show examples of valid paths
    if valid_paths:
        print("=" * 80)
        print("EXAMPLES OF VALID PATHS (First 5)")
        print("=" * 80)
        print()

        for song in valid_paths[:5]:
            print(f"ID: {song['id']}")
            print(f"Title: {song['title']}")
            print(f"Path: {song['file_path']}")
            print(f"Exists: ✅")
            print()

    # Check if all paths are in same directory
    if valid_paths:
        directories = set()
        for song in valid_paths:
            directory = os.path.dirname(song['file_path'])
            directories.add(directory)

        print("=" * 80)
        print("DIRECTORIES FOUND")
        print("=" * 80)
        print()
        print(f"Number of unique directories: {len(directories)}")
        print()
        for directory in sorted(directories):
            count = sum(1 for s in valid_paths if os.path.dirname(s['file_path']) == directory)
            print(f"  {directory} ({count} songs)")
        print()

    conn.close()


if __name__ == '__main__':
    main()
