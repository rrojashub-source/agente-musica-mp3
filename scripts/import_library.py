#!/usr/bin/env python3
"""
Quick Library Import Script

Simple script to import MP3s into database.
Usage: python scripts/import_library.py

This is a temporary solution until ImportTab GUI is complete.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from database.manager import DatabaseManager
from workers.library_import_worker import LibraryImportWorker
from PyQt6.QtCore import QCoreApplication


def main():
    """Run import"""
    print("🎵 NEXUS Music Library Import")
    print("=" * 50)

    # Get folder path
    default_path = "C:\\Users\\ricar\\Music"
    folder = input(f"\nFolder to import [{default_path}]: ").strip()

    if not folder:
        folder = default_path

    folder_path = Path(folder)

    if not folder_path.exists():
        print(f"\n❌ Error: Folder not found: {folder}")
        return

    print(f"\n📁 Scanning: {folder_path}")
    print(f"   Recursive: Yes")

    # Create QApplication for QThread
    app = QCoreApplication([])

    # Initialize database
    print("\n🗄️  Initializing database...")
    db = DatabaseManager()

    # Count before
    count_before = db.get_song_count()
    print(f"   Current songs in library: {count_before}")

    # Create worker
    worker = LibraryImportWorker(db, str(folder_path), recursive=True)

    # Connect signals
    def on_progress(pct, msg):
        print(f"   [{pct:3d}%] {msg}")

    def on_song_imported(song):
        print(f"   ✅ {song['title']} - {song['artist']}")

    def on_finished(result):
        print(f"\n{'=' * 50}")
        print(f"✅ Import Complete!")
        print(f"   Imported: {result['success']}")
        print(f"   Skipped: {result['skipped']} (duplicates)")
        print(f"   Failed: {result['failed']}")

        if result['errors']:
            print(f"\n⚠️  Errors:")
            for error in result['errors'][:5]:
                print(f"   - {error}")

        # Count after
        count_after = db.get_song_count()
        print(f"\n📊 Total songs in library: {count_after}")

        app.quit()

    def on_error(error_msg):
        print(f"\n❌ Fatal Error: {error_msg}")
        app.quit()

    worker.progress.connect(on_progress)
    worker.song_imported.connect(on_song_imported)
    worker.finished.connect(on_finished)
    worker.error.connect(on_error)

    # Start import
    print(f"\n🚀 Starting import...")
    worker.start()

    # Run event loop
    app.exec()

    # Cleanup
    db.close()


if __name__ == "__main__":
    main()
