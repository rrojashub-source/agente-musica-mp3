#!/usr/bin/env python3
"""
Database Cleanup Tool - Remove songs with broken file paths
For NEXUS Music Manager - Production Quality Software

This tool:
1. Scans all songs in database
2. Checks if file path exists on disk
3. Removes broken entries from database
4. Reports statistics
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from database.manager import DatabaseManager


def cleanup_broken_paths(db_manager, dry_run=False):
    """
    Remove songs with non-existent file paths from database

    Args:
        db_manager: DatabaseManager instance
        dry_run: If True, only report what would be deleted (don't actually delete)

    Returns:
        dict: Statistics (total, broken, removed, remaining)
    """
    print("🔍 Scanning database for broken file paths...")
    print()

    # Get all songs
    all_songs = db_manager.get_all_songs()
    total_count = len(all_songs)

    print(f"📊 Total songs in database: {total_count}")
    print()

    # Find broken paths
    broken_songs = []
    for song in all_songs:
        file_path = song.get('file_path', '')
        if not file_path:
            broken_songs.append((song['id'], song.get('title', 'Unknown'), 'No path'))
            continue

        path_obj = Path(file_path)
        if not path_obj.exists():
            broken_songs.append((song['id'], song.get('title', 'Unknown'), file_path))

    broken_count = len(broken_songs)

    if broken_count == 0:
        print("✅ No broken paths found! Database is clean.")
        return {
            'total': total_count,
            'broken': 0,
            'removed': 0,
            'remaining': total_count
        }

    print(f"❌ Found {broken_count} songs with broken paths:")
    print()

    # Show broken songs
    for i, (song_id, title, path) in enumerate(broken_songs, 1):
        print(f"  {i}. [{song_id}] {title}")
        if path != 'No path':
            print(f"     Path: {path}")
        print()

    if dry_run:
        print("🔍 DRY RUN MODE - No changes made")
        print(f"   Would remove {broken_count} songs")
        return {
            'total': total_count,
            'broken': broken_count,
            'removed': 0,
            'remaining': total_count
        }

    # Confirm deletion
    print("⚠️  WARNING: This will permanently delete these entries from the database.")
    print(f"   {broken_count} songs will be removed.")
    print()
    response = input("Continue? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return {
            'total': total_count,
            'broken': broken_count,
            'removed': 0,
            'remaining': total_count
        }

    # Delete broken songs
    print()
    print("🗑️  Removing broken entries...")
    removed_count = 0

    for song_id, title, path in broken_songs:
        try:
            db_manager.delete_song(song_id)
            removed_count += 1
            print(f"  ✓ Removed: {title}")
        except Exception as e:
            print(f"  ✗ Failed to remove [{song_id}]: {e}")

    remaining_count = total_count - removed_count

    print()
    print("=" * 60)
    print("✅ CLEANUP COMPLETE")
    print("=" * 60)
    print(f"Total songs (before):  {total_count}")
    print(f"Broken paths found:    {broken_count}")
    print(f"Successfully removed:  {removed_count}")
    print(f"Remaining songs:       {remaining_count}")
    print("=" * 60)

    return {
        'total': total_count,
        'broken': broken_count,
        'removed': removed_count,
        'remaining': remaining_count
    }


def main():
    """Main entry point"""
    print("=" * 60)
    print("NEXUS Music Manager - Database Cleanup Tool")
    print("Remove songs with broken file paths")
    print("=" * 60)
    print()

    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("🔍 Running in DRY RUN mode (no changes will be made)")
        print()

    # Initialize database
    try:
        db_manager = DatabaseManager()
        print(f"✅ Database connected: {db_manager.db_path}")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

    # Run cleanup
    try:
        stats = cleanup_broken_paths(db_manager, dry_run=dry_run)
    except KeyboardInterrupt:
        print()
        print("❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)
    finally:
        db_manager.close()

    # Exit with appropriate code
    if stats['broken'] > 0 and stats['removed'] == 0:
        sys.exit(1)  # Found broken paths but didn't remove
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()
