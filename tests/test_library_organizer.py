"""
Tests for Library Organizer - Phase 5.2 (TDD Red Phase)

Purpose: Organize music library into structured folders
- Build paths from templates
- Move/copy files safely
- Update database paths
- Handle conflicts and errors

Test Strategy: Red → Green → Refactor
Expected Result: All tests FAIL initially (no implementation yet)
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import shutil


class TestLibraryOrganizer(unittest.TestCase):
    """Test library organization engine"""

    def setUp(self):
        """Setup test fixtures"""
        try:
            from src.core.library_organizer import LibraryOrganizer
            self.organizer_class = LibraryOrganizer
        except ImportError:
            self.organizer_class = None

        # Create temp directory for tests
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup temp files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    # ========== STRUCTURAL TESTS ==========

    def test_01_organizer_class_exists(self):
        """Test LibraryOrganizer exists"""
        if self.organizer_class is None:
            self.fail("LibraryOrganizer not found - implement src/core/library_organizer.py")

        self.assertIsNotNone(self.organizer_class)

    def test_02_organizer_builds_path_from_template(self):
        """Test path generation from template"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        song = {
            'title': 'Bohemian Rhapsody',
            'artist': 'Queen',
            'album': 'A Night at the Opera',
            'year': 1975,
            'track': 1
        }

        template = "{artist}/{album} ({year})/{track:02d} - {title}.mp3"

        path = organizer.build_path(self.temp_dir, template, song)

        # Should create proper path
        expected = os.path.join(
            self.temp_dir,
            "Queen",
            "A Night at the Opera (1975)",
            "01 - Bohemian Rhapsody.mp3"
        )

        self.assertEqual(str(path), expected)

    def test_03_organizer_sanitizes_folder_names(self):
        """Test invalid characters removed from paths"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        song = {
            'title': 'Song?',
            'artist': 'Artist/Band',
            'album': 'Album:Name',
            'year': 2020,
            'track': 1
        }

        template = "{artist}/{album}/{title}.mp3"

        path = organizer.build_path(self.temp_dir, template, song)

        # Should sanitize invalid chars in FILENAMES (not directory separators)
        path_str = str(path)
        # Get just the filename parts (artist, album, title)
        relative_path = path_str[len(self.temp_dir):].strip('/\\')

        # Verify problematic chars were replaced with _
        self.assertIn('Artist_Band', relative_path)  # '/' was replaced
        self.assertIn('Album_Name', relative_path)   # ':' was replaced
        self.assertIn('Song_', relative_path)        # '?' was replaced

        # Verify directory separators still exist (not sanitized)
        self.assertIn('/', relative_path)  # Path should have directory separators

    def test_04_organizer_handles_missing_metadata(self):
        """Test fallback when metadata missing"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        song = {
            'title': 'Song',
            # Missing artist, album, year
        }

        template = "{artist}/{album}/{title}.mp3"

        path = organizer.build_path(self.temp_dir, template, song)

        # Should use fallbacks (e.g., "Unknown Artist")
        path_lower = str(path).lower()
        self.assertIn("unknown", path_lower)

    def test_05_organizer_creates_directories(self):
        """Test directory creation"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        target_dir = os.path.join(self.temp_dir, "Artist", "Album")

        # Directory should not exist yet
        self.assertFalse(os.path.exists(target_dir))

        # Create directories
        organizer._create_directories(target_dir)

        # Directory should now exist
        self.assertTrue(os.path.exists(target_dir))

    def test_06_organizer_moves_files(self):
        """Test file moving works"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        # Create source file
        source_file = os.path.join(self.temp_dir, "source.mp3")
        with open(source_file, 'w') as f:
            f.write("test content")

        # Target path
        target_file = os.path.join(self.temp_dir, "subdir", "target.mp3")

        # Move file
        result = organizer._move_file(source_file, target_file)

        # Source should not exist
        self.assertFalse(os.path.exists(source_file))

        # Target should exist
        self.assertTrue(os.path.exists(target_file))

        self.assertTrue(result)

    def test_07_organizer_updates_database_paths(self):
        """Test database updated after move"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        song_id = 123
        new_path = "/new/path/song.mp3"

        organizer._update_database_path(song_id, new_path)

        # Verify database update was called
        mock_db.update_song_path.assert_called_once_with(song_id, new_path)

    def test_08_organizer_handles_duplicate_names(self):
        """Test conflict resolution (file1.mp3, file2.mp3)"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        # Create existing file
        existing_file = os.path.join(self.temp_dir, "song.mp3")
        with open(existing_file, 'w') as f:
            f.write("existing")

        # Try to create another file with same name
        new_path = organizer._handle_name_conflict(existing_file)

        # Should generate unique name
        self.assertNotEqual(new_path, existing_file)
        self.assertTrue("song" in os.path.basename(new_path))

    def test_09_organizer_preview_mode(self):
        """Test preview without actual moves"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        # Create test file
        source_file = os.path.join(self.temp_dir, "test.mp3")
        with open(source_file, 'w') as f:
            f.write("test")

        songs = [{
            'id': 1,
            'title': 'Test',
            'artist': 'Artist',
            'album': 'Album',
            'year': 2020,
            'track': 1,
            'file_path': source_file
        }]

        mock_db.get_all_songs.return_value = songs

        template = "{artist}/{album}/{title}.mp3"

        # Preview mode (dry_run=True)
        result = organizer.organize(self.temp_dir, template, songs, move=True, dry_run=True)

        # File should still exist in original location
        self.assertTrue(os.path.exists(source_file))

        # Should return preview data
        self.assertIn('preview', result)

    def test_10_organizer_rollback_on_error(self):
        """Test rollback if error during organization"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        # This test verifies that if an error occurs mid-organization,
        # changes can be rolled back (if implemented)

        # For now, just verify organizer has rollback capability
        self.assertTrue(
            hasattr(organizer, 'rollback') or hasattr(organizer, '_rollback'),
            "Organizer missing rollback capability"
        )

    # ========== PERFORMANCE TEST ==========

    def test_11_organizer_processes_1000_files_fast(self):
        """Test 1,000 files organized in < 30 seconds"""
        if self.organizer_class is None:
            self.skipTest("Organizer not implemented")

        mock_db = Mock()
        organizer = self.organizer_class(mock_db)

        # Create 1000 mock songs (no actual files for speed)
        songs = []
        for i in range(1000):
            songs.append({
                'id': i,
                'title': f'Song {i}',
                'artist': f'Artist {i % 10}',
                'album': f'Album {i % 50}',
                'year': 2020,
                'track': i % 15 + 1,
                'file_path': f'/mock/path/song{i}.mp3'
            })

        mock_db.get_all_songs.return_value = songs

        template = "{artist}/{album}/{title}.mp3"

        import time
        start = time.time()

        # Dry run to test path building performance
        result = organizer.organize(self.temp_dir, template, songs, dry_run=True)

        elapsed = time.time() - start

        # Should complete in < 30 seconds
        self.assertLess(elapsed, 30.0, f"Organization too slow: {elapsed:.2f}s")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
