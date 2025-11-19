#!/usr/bin/env python3
"""
Test Metadata Cleaner

Purpose: Test metadata cleaning on current library
Shows before/after comparison

Created: November 18, 2025
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.manager import DatabaseManager
from core.metadata_cleaner import MetadataCleaner


def main():
    print("=" * 80)
    print("🧹 METADATA CLEANER TEST")
    print("=" * 80)
    print()

    # Connect to database
    db = DatabaseManager('music_library.db')

    # Get all songs
    songs = db.get_all_songs()
    print(f"Total songs in library: {len(songs)}")
    print()

    # Initialize cleaner
    cleaner = MetadataCleaner()

    # Analyze library
    print("=" * 80)
    print("LIBRARY ANALYSIS")
    print("=" * 80)
    print()

    report = cleaner.analyze_library(songs)

    print(f"📊 Corruption Levels:")
    print(f"  ✅ Clean:    {report['clean']} songs")
    print(f"  ⚠️  Minor:    {report['minor']} songs")
    print(f"  ⚠️  Moderate: {report['moderate']} songs")
    print(f"  ❌ Severe:   {report['severe']} songs")
    print()

    # Show examples of cleaning
    print("=" * 80)
    print("CLEANING EXAMPLES (First 10 problematic songs)")
    print("=" * 80)
    print()

    problematic = report['problematic_songs'][:10]

    for i, song_info in enumerate(problematic, 1):
        # Get full song data
        song = next((s for s in songs if s['id'] == song_info['id']), None)
        if not song:
            continue

        print(f"Song {i}: [{song_info['corruption_level'].upper()}]")
        print(f"  ID: {song['id']}")
        print()

        # Clean metadata
        cleaned, issues = cleaner.clean_metadata(song)

        # Show title changes
        if song['title'] != cleaned['title']:
            print(f"  Title:")
            print(f"    BEFORE: {song['title']}")
            print(f"    AFTER:  {cleaned['title']}")
            if 'title' in issues:
                print(f"    Issues: {', '.join(issues['title'])}")
        else:
            print(f"  Title: {song['title']} (no changes)")

        # Show artist changes
        if song['artist'] != cleaned['artist']:
            print(f"  Artist:")
            print(f"    BEFORE: {song['artist']}")
            print(f"    AFTER:  {cleaned['artist']}")
            if 'artist' in issues:
                print(f"    Issues: {', '.join(issues['artist'])}")
        else:
            print(f"  Artist: {song['artist']} (no changes)")

        # Show album changes
        if song['album'] != cleaned['album']:
            print(f"  Album:")
            print(f"    BEFORE: {song['album']}")
            print(f"    AFTER:  {cleaned['album']}")
            if 'album' in issues:
                print(f"    Issues: {', '.join(issues['album'])}")
        else:
            print(f"  Album: {song['album']} (no changes)")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    total_problematic = report['moderate'] + report['severe']
    print(f"Total songs needing cleanup: {total_problematic}")
    print()
    print("Next steps:")
    print("  1. Review cleaning results above")
    print("  2. Implement Metadata Fetcher (MusicBrainz/Spotify)")
    print("  3. Create GUI wizard for batch cleanup")
    print()

    db.close()


if __name__ == '__main__':
    main()
