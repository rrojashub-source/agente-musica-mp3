"""
Tests for Batch Renamer - Phase 5.3 (TDD Red Phase)

Purpose: Batch rename MP3 files based on metadata patterns
- Build filename from templates
- Support find/replace operations
- Case conversion (UPPER, lower, Title Case)
- Number sequences (001, 002, ...)
- Preview changes before applying
- Safe renaming with conflict resolution

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


class TestBatchRenamer(unittest.TestCase):
    """Test batch file renaming engine"""

    def setUp(self):
        """Setup test fixtures"""
        try:
            from src.core.batch_renamer import BatchRenamer
            self.renamer_class = BatchRenamer
        except ImportError:
            self.renamer_class = None

        # Create temp directory for tests
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup temp files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    # ========== STRUCTURAL TESTS ==========

    def test_01_renamer_class_exists(self):
        """Test BatchRenamer exists"""
        if self.renamer_class is None:
            self.fail("BatchRenamer not found - implement src/core/batch_renamer.py")

        self.assertIsNotNone(self.renamer_class)

    def test_02_renamer_builds_filename_from_template(self):
        """Test filename generation from template"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        song = {
            'title': 'Bohemian Rhapsody',
            'artist': 'Queen',
            'album': 'A Night at the Opera',
            'year': 1975,
            'track': 1
        }

        template = "{track:02d} - {artist} - {title}.mp3"

        filename = renamer.build_filename(template, song)

        # Should create proper filename
        expected = "01 - Queen - Bohemian Rhapsody.mp3"
        self.assertEqual(filename, expected)

    def test_03_renamer_sanitizes_filenames(self):
        """Test invalid characters removed from filenames"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        song = {
            'title': 'Song?',
            'artist': 'Artist/Band',
            'album': 'Album:Name',
            'track': 1
        }

        template = "{track:02d} - {artist} - {title}.mp3"

        filename = renamer.build_filename(template, song)

        # Should sanitize invalid chars
        self.assertNotIn('?', filename)
        self.assertNotIn('/', filename)
        self.assertNotIn(':', filename)

    def test_04_renamer_supports_find_replace(self):
        """Test find/replace in filenames"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        song = {
            'title': 'Song Featuring Artist',
            'artist': 'Main Artist',
            'track': 1
        }

        template = "{track:02d} - {title}.mp3"

        # Build base filename
        base_filename = renamer.build_filename(template, song)

        # Apply find/replace: "Featuring" → "feat."
        renamed = renamer.apply_find_replace(base_filename, "Featuring", "feat.")

        self.assertEqual(renamed, "01 - Song feat. Artist.mp3")

    def test_05_renamer_supports_case_conversion(self):
        """Test case conversion (UPPER, lower, Title)"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        song = {
            'title': 'song title',
            'artist': 'ARTIST NAME',
            'track': 1
        }

        template = "{track:02d} - {artist} - {title}.mp3"

        # Build filename
        filename = renamer.build_filename(template, song)

        # Test case conversions
        upper_case = renamer.apply_case_conversion(filename, "upper")
        self.assertEqual(upper_case, "01 - ARTIST NAME - SONG TITLE.MP3")

        lower_case = renamer.apply_case_conversion(filename, "lower")
        self.assertEqual(lower_case, "01 - artist name - song title.mp3")

        title_case = renamer.apply_case_conversion(filename, "title")
        self.assertEqual(title_case, "01 - Artist Name - Song Title.mp3")

    def test_06_renamer_supports_number_sequences(self):
        """Test number sequence insertion (001, 002, ...)"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        songs = [
            {'id': 1, 'title': 'Song A'},
            {'id': 2, 'title': 'Song B'},
            {'id': 3, 'title': 'Song C'}
        ]

        template = "{seq:03d} - {title}.mp3"

        # Build filenames with sequence
        filenames = [renamer.build_filename(template, song, seq=i+1) for i, song in enumerate(songs)]

        self.assertEqual(filenames[0], "001 - Song A.mp3")
        self.assertEqual(filenames[1], "002 - Song B.mp3")
        self.assertEqual(filenames[2], "003 - Song C.mp3")

    def test_07_renamer_preview_mode(self):
        """Test preview without actual renames"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        # Create test file
        source_file = os.path.join(self.temp_dir, "old_name.mp3")
        with open(source_file, 'w') as f:
            f.write("test")

        songs = [{
            'id': 1,
            'title': 'New Title',
            'artist': 'Artist',
            'track': 1,
            'file_path': source_file
        }]

        template = "{track:02d} - {title}.mp3"

        # Preview mode (dry_run=True)
        result = renamer.rename_batch(songs, template, dry_run=True)

        # File should still have old name
        self.assertTrue(os.path.exists(source_file))
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, "01 - New Title.mp3")))

        # Should return preview data
        self.assertIn('preview', result)

    def test_08_renamer_executes_renames(self):
        """Test actual file renaming"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        # Create test file
        old_path = os.path.join(self.temp_dir, "old_name.mp3")
        with open(old_path, 'w') as f:
            f.write("test")

        songs = [{
            'id': 1,
            'title': 'New Title',
            'artist': 'Artist',
            'track': 1,
            'file_path': old_path
        }]

        template = "{track:02d} - {title}.mp3"

        # Execute rename (dry_run=False)
        result = renamer.rename_batch(songs, template, dry_run=False)

        # Old file should not exist
        self.assertFalse(os.path.exists(old_path))

        # New file should exist
        new_path = os.path.join(self.temp_dir, "01 - New Title.mp3")
        self.assertTrue(os.path.exists(new_path))

        self.assertEqual(result['success'], 1)

    def test_09_renamer_handles_name_conflicts(self):
        """Test conflict resolution (file1, file2, ...)"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        # Create existing file
        existing_path = os.path.join(self.temp_dir, "01 - Song.mp3")
        with open(existing_path, 'w') as f:
            f.write("existing")

        # Try to rename another file to same name
        old_path = os.path.join(self.temp_dir, "old.mp3")
        with open(old_path, 'w') as f:
            f.write("new")

        songs = [{
            'id': 2,
            'title': 'Song',
            'artist': 'Artist',
            'track': 1,
            'file_path': old_path
        }]

        template = "{track:02d} - {title}.mp3"

        # Execute rename
        result = renamer.rename_batch(songs, template, dry_run=False)

        # Should create unique name (01 - Song_1.mp3)
        self.assertTrue(os.path.exists(existing_path), "Original file should still exist")
        conflict_path = os.path.join(self.temp_dir, "01 - Song_1.mp3")
        self.assertTrue(os.path.exists(conflict_path), "Conflict file should exist with unique name")

    def test_10_renamer_updates_database_paths(self):
        """Test database updated after rename"""
        if self.renamer_class is None:
            self.skipTest("Renamer not implemented")

        mock_db = Mock()
        renamer = self.renamer_class(mock_db)

        # Create test file
        old_path = os.path.join(self.temp_dir, "old.mp3")
        with open(old_path, 'w') as f:
            f.write("test")

        songs = [{
            'id': 123,
            'title': 'New Title',
            'track': 1,
            'file_path': old_path
        }]

        template = "{track:02d} - {title}.mp3"

        # Execute rename
        result = renamer.rename_batch(songs, template, dry_run=False)

        # Verify database update was called
        new_path = os.path.join(self.temp_dir, "01 - New Title.mp3")
        mock_db.update_song_path.assert_called_once_with(123, new_path)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
