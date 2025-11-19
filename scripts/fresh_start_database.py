#!/usr/bin/env python3
"""
Fresh Start Database Script - Wipe & Re-import with Path Normalization

Purpose: Clean slate for music library database
- Backup existing database
- Wipe all songs
- Re-import from music folder with normalized paths
- Verify results (no duplicates, correct paths)

Created: November 18, 2025
Author: NEXUS + Ricardo
"""
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.manager import DatabaseManager
from workers.library_import_worker import LibraryImportWorker
from PyQt6.QtCore import QCoreApplication

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_database(db_path: Path) -> Path:
    """
    Create timestamped backup of database

    Args:
        db_path: Path to database file

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = db_path.parent / f"music_library_backup_{timestamp}.db"

    logger.info(f"Creating backup: {backup_path}")

    # Copy main database file
    if db_path.exists():
        shutil.copy2(db_path, backup_path)

        # Copy WAL and SHM files if they exist
        for ext in ['-wal', '-shm']:
            src = Path(str(db_path) + ext)
            if src.exists():
                dst = Path(str(backup_path) + ext)
                shutil.copy2(src, dst)

        logger.info(f"✅ Backup created: {backup_path}")
        return backup_path
    else:
        logger.warning("Database file does not exist, no backup created")
        return None


def wipe_database(db_manager: DatabaseManager):
    """
    Wipe all songs from database

    Args:
        db_manager: DatabaseManager instance
    """
    logger.info("Wiping all songs from database...")

    try:
        # Get count before wipe
        count_before = db_manager.get_song_count()
        logger.info(f"Songs before wipe: {count_before}")

        # Delete all songs
        cursor = db_manager.conn.cursor()
        cursor.execute("DELETE FROM songs")
        db_manager.conn.commit()

        # Reset autoincrement counter
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='songs'")
        db_manager.conn.commit()

        # Verify wipe
        count_after = db_manager.get_song_count()
        logger.info(f"Songs after wipe: {count_after}")

        if count_after == 0:
            logger.info("✅ Database wiped successfully")
        else:
            logger.error(f"❌ Wipe failed: {count_after} songs remain")
            return False

        return True

    except Exception as e:
        logger.error(f"Failed to wipe database: {e}")
        return False


def reimport_library(db_manager: DatabaseManager, music_folder: str, app: QCoreApplication):
    """
    Re-import music library with normalized paths

    Args:
        db_manager: DatabaseManager instance
        music_folder: Path to music folder to import
        app: QCoreApplication instance for QThread
    """
    logger.info(f"Starting fresh import from: {music_folder}")
    logger.info("Path normalization: ENABLED ✅")
    logger.info("Duration filter: Skip files > 15 minutes ✅")

    # Create import worker with duration filter
    # max_duration=900 seconds (15 minutes) - skips playlists and mixes
    worker = LibraryImportWorker(db_manager, music_folder, recursive=True, max_duration=900)

    # Track progress
    def on_progress(percentage, message):
        if percentage % 10 == 0 or percentage == 100:  # Log every 10%
            logger.info(f"Progress: {percentage}% - {message}")

    def on_song_imported(song_data):
        # Log every 50 songs
        if db_manager.get_song_count() % 50 == 0:
            logger.info(f"Imported {db_manager.get_song_count()} songs so far...")

    def on_finished(result):
        success = result['success']
        failed = result['failed']
        skipped = result['skipped']

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ FRESH IMPORT COMPLETE!")
        logger.info(f"   Imported: {success} songs")
        logger.info(f"   Skipped: {skipped} duplicates")
        logger.info(f"   Failed: {failed} errors")

        if result.get('errors'):
            logger.info("")
            logger.info("⚠️  Errors encountered:")
            for error in result['errors'][:10]:
                logger.info(f"   - {error}")

        # Final stats
        total = db_manager.get_song_count()
        logger.info("")
        logger.info(f"📊 Total songs in library: {total}")
        logger.info("=" * 60)

        app.quit()

    def on_error(error_message):
        logger.error(f"❌ Fatal error during import: {error_message}")
        app.quit()

    # Connect signals
    worker.progress.connect(on_progress)
    worker.song_imported.connect(on_song_imported)
    worker.finished.connect(on_finished)
    worker.error.connect(on_error)

    # Start import
    worker.start()

    # Wait for completion
    app.exec()


def verify_results(db_manager: DatabaseManager):
    """
    Verify fresh import results

    Args:
        db_manager: DatabaseManager instance
    """
    logger.info("")
    logger.info("🔍 Verifying results...")

    total = db_manager.get_song_count()
    logger.info(f"Total songs: {total}")

    # Check for potential duplicates (same title + artist)
    cursor = db_manager.conn.cursor()
    cursor.execute("""
        SELECT title, artist, COUNT(*) as count
        FROM songs
        GROUP BY title, artist
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 10
    """)

    duplicates = cursor.fetchall()

    if duplicates:
        logger.warning(f"⚠️  Found {len(duplicates)} potential duplicate groups:")
        for dup in duplicates:
            logger.warning(f"   - {dup[0]} - {dup[1]} ({dup[2]} copies)")
    else:
        logger.info("✅ No duplicate title+artist combinations found")

    # Sample paths (verify they're normalized)
    cursor.execute("SELECT file_path FROM songs LIMIT 5")
    sample_paths = cursor.fetchall()

    logger.info("")
    logger.info("📁 Sample paths (should be normalized):")
    for path in sample_paths:
        logger.info(f"   {path[0]}")


def main():
    """Main execution"""
    print("")
    print("=" * 60)
    print("🔄 FRESH START DATABASE SCRIPT")
    print("=" * 60)
    print("")
    print("This script will:")
    print("  1. Backup current database")
    print("  2. Wipe all songs (DELETE)")
    print("  3. Re-import from music folder with normalized paths")
    print("  4. Verify results (no duplicates, correct paths)")
    print("")
    print("⚠️  WARNING: This will DELETE all songs from database!")
    print("   (Backup will be created first)")
    print("")

    # Get user confirmation
    response = input("Continue? (yes/no): ").strip().lower()

    if response != 'yes':
        print("❌ Aborted by user")
        return

    print("")

    # Configuration
    db_path = Path('music_library.db')
    music_folder = input("Enter music folder path [C:\\Users\\ricar\\Music]: ").strip()

    if not music_folder:
        music_folder = r"C:\Users\ricar\Music"

    # Convert to absolute path if needed
    music_folder = str(Path(music_folder).resolve())

    if not Path(music_folder).exists():
        print(f"❌ Folder not found: {music_folder}")
        return

    print(f"Music folder: {music_folder}")
    print("")

    # Create QApplication for QThread
    app = QCoreApplication(sys.argv)

    try:
        # Step 1: Backup
        print("Step 1: Backing up database...")
        backup_path = backup_database(db_path)

        if backup_path:
            print(f"✅ Backup created: {backup_path}")

        print("")

        # Step 2: Wipe
        print("Step 2: Wiping database...")
        db_manager = DatabaseManager(str(db_path))

        success = wipe_database(db_manager)

        if not success:
            print("❌ Wipe failed, aborting")
            return

        print("")

        # Step 3: Re-import
        print("Step 3: Re-importing library (this may take several minutes)...")
        print("")

        reimport_library(db_manager, music_folder, app)

        # Step 4: Verify
        verify_results(db_manager)

        print("")
        print("=" * 60)
        print("✅ FRESH START COMPLETE!")
        print("=" * 60)
        print("")
        print(f"Backup saved at: {backup_path}")
        print("You can now launch the GUI and use the clean library.")
        print("")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"❌ Error: {e}")
    finally:
        if 'db_manager' in locals():
            db_manager.close()


if __name__ == '__main__':
    main()
