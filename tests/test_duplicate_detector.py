"""
Tests for Duplicate Detector - Phase 5.1 (TDD Red Phase)

Purpose: Detect duplicate songs using multiple methods
- Metadata comparison (fuzzy matching)
- Audio fingerprinting (acoustid/chromaprint)
- File size comparison (quick pre-filter)

Test Strategy: Red → Green → Refactor
Expected Result: All tests FAIL initially (no implementation yet)
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path


class TestDuplicateDetector(unittest.TestCase):
    """Test duplicate detection engine"""

    def setUp(self):
        """Setup test fixtures"""
        try:
            from src.core.duplicate_detector import DuplicateDetector
            self.detector_class = DuplicateDetector
        except ImportError:
            self.detector_class = None

    # ========== STRUCTURAL TESTS ==========

    def test_01_duplicate_detector_class_exists(self):
        """Test DuplicateDetector class exists"""
        if self.detector_class is None:
            self.fail("DuplicateDetector not found - implement src/core/duplicate_detector.py")

        self.assertIsNotNone(self.detector_class)

    def test_02_detector_has_detection_methods(self):
        """Test detector has 3 detection methods"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        # Mock database
        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Verify methods exist
        self.assertTrue(hasattr(detector, 'detect_by_metadata'), "Missing detect_by_metadata method")
        self.assertTrue(hasattr(detector, 'detect_by_fingerprint'), "Missing detect_by_fingerprint method")
        self.assertTrue(hasattr(detector, 'detect_by_filesize'), "Missing detect_by_filesize method")
        self.assertTrue(hasattr(detector, 'scan_library'), "Missing scan_library method")

    # ========== METHOD 1: METADATA COMPARISON ==========

    def test_03_detect_by_metadata_finds_exact_match(self):
        """Test metadata detection finds exact duplicates"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Two songs with identical metadata
        songs = [
            {'id': 1, 'title': 'Bohemian Rhapsody', 'artist': 'Queen', 'duration': 354, 'file_path': '/path/1.mp3'},
            {'id': 2, 'title': 'Bohemian Rhapsody', 'artist': 'Queen', 'duration': 354, 'file_path': '/path/2.mp3'},
        ]

        mock_db.get_all_songs.return_value = songs

        # Detect duplicates
        duplicates = detector.detect_by_metadata()

        # Should find 1 duplicate group with 2 songs
        self.assertGreater(len(duplicates), 0, "No duplicate groups found")
        self.assertEqual(len(duplicates[0]['songs']), 2, "Duplicate group should have 2 songs")

    def test_04_detect_by_metadata_finds_fuzzy_match(self):
        """Test metadata detection finds similar titles (fuzzy matching)"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Similar but not identical titles
        songs = [
            {'id': 1, 'title': 'Bohemian Rhapsody', 'artist': 'Queen', 'duration': 354, 'file_path': '/path/1.mp3'},
            {'id': 2, 'title': 'Bohemian Rhapsody (Remaster)', 'artist': 'Queen', 'duration': 356, 'file_path': '/path/2.mp3'},
        ]

        mock_db.get_all_songs.return_value = songs

        # Detect duplicates (should match due to fuzzy matching)
        duplicates = detector.detect_by_metadata()

        # Should find match despite slight title difference
        self.assertGreater(len(duplicates), 0, "Fuzzy matching failed - no duplicates found")

    def test_05_detect_by_metadata_respects_threshold(self):
        """Test threshold controls similarity matching"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Songs with low similarity
        songs = [
            {'id': 1, 'title': 'Bohemian Rhapsody', 'artist': 'Queen', 'duration': 354, 'file_path': '/path/1.mp3'},
            {'id': 2, 'title': 'Different Song', 'artist': 'Queen', 'duration': 200, 'file_path': '/path/2.mp3'},
        ]

        mock_db.get_all_songs.return_value = songs

        # High threshold (0.9) - should NOT match
        detector.similarity_threshold = 0.9
        duplicates_high = detector.detect_by_metadata()

        # Low threshold (0.3) - might match on artist
        detector.similarity_threshold = 0.3
        duplicates_low = detector.detect_by_metadata()

        # High threshold should find fewer/no matches
        self.assertLessEqual(len(duplicates_high), len(duplicates_low), "Threshold not respected")

    def test_06_detect_by_metadata_compares_duration(self):
        """Test duration comparison (±3 seconds tolerance)"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Same title/artist, slightly different duration (within tolerance)
        songs = [
            {'id': 1, 'title': 'Test Song', 'artist': 'Test Artist', 'duration': 200, 'file_path': '/path/1.mp3'},
            {'id': 2, 'title': 'Test Song', 'artist': 'Test Artist', 'duration': 202, 'file_path': '/path/2.mp3'},  # +2s
        ]

        mock_db.get_all_songs.return_value = songs

        # Should match (within ±3s tolerance)
        duplicates = detector.detect_by_metadata()
        self.assertGreater(len(duplicates), 0, "Duration tolerance not working")

    # ========== METHOD 2: AUDIO FINGERPRINTING ==========

    def test_07_detect_by_fingerprint_generates_signature(self):
        """Test audio fingerprint generation"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Mock acoustid fingerprint generation
        with patch('acoustid.fingerprint_file') as mock_fp:
            mock_fp.return_value = (354, 'AQAB1234fingerprint')

            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Generate fingerprint
                fingerprint = detector._generate_fingerprint(tmp_path)

                # Should return fingerprint string
                self.assertIsNotNone(fingerprint, "Fingerprint generation returned None")
                self.assertIsInstance(fingerprint, str, "Fingerprint should be string")
            finally:
                os.unlink(tmp_path)

    def test_08_detect_by_fingerprint_compares_signatures(self):
        """Test fingerprint comparison accuracy"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Mock songs with same fingerprint (duplicates)
        songs = [
            {'id': 1, 'title': 'Song A', 'artist': 'Artist', 'duration': 200, 'file_path': '/path/1.mp3'},
            {'id': 2, 'title': 'Song B', 'artist': 'Artist', 'duration': 200, 'file_path': '/path/2.mp3'},
        ]

        mock_db.get_all_songs.return_value = songs

        # Mock fingerprint generation (same fingerprint for both)
        with patch.object(detector, '_generate_fingerprint') as mock_fp:
            mock_fp.return_value = 'AQAB1234same_fingerprint'

            duplicates = detector.detect_by_fingerprint()

            # Should detect as duplicates
            self.assertGreater(len(duplicates), 0, "Fingerprint comparison failed")

    def test_09_detect_by_fingerprint_handles_missing_file(self):
        """Test graceful handling of missing files"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        songs = [
            {'id': 1, 'title': 'Missing', 'artist': 'Artist', 'duration': 200, 'file_path': '/nonexistent/file.mp3'},
        ]

        mock_db.get_all_songs.return_value = songs

        # Should not crash
        try:
            duplicates = detector.detect_by_fingerprint()
            # Should return empty list or skip missing files
            self.assertIsInstance(duplicates, list, "Should return list even with missing files")
        except Exception as e:
            self.fail(f"Fingerprint detection crashed on missing file: {e}")

    # ========== METHOD 3: FILE SIZE ==========

    def test_10_detect_by_filesize_groups_same_size(self):
        """Test grouping by file size"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Create temp files with same size
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp1:
            tmp1.write(b'x' * 1000)  # 1000 bytes
            tmp1_path = tmp1.name

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp2:
            tmp2.write(b'y' * 1000)  # 1000 bytes (same size)
            tmp2_path = tmp2.name

        try:
            songs = [
                {'id': 1, 'title': 'Song 1', 'artist': 'Artist', 'duration': 200, 'file_path': tmp1_path},
                {'id': 2, 'title': 'Song 2', 'artist': 'Artist', 'duration': 200, 'file_path': tmp2_path},
            ]

            mock_db.get_all_songs.return_value = songs

            # Detect by file size
            duplicates = detector.detect_by_filesize()

            # Should group files of same size
            self.assertGreater(len(duplicates), 0, "File size grouping failed")
        finally:
            os.unlink(tmp1_path)
            os.unlink(tmp2_path)

    def test_11_detect_by_filesize_is_fast(self):
        """Test filesize detection completes quickly"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Create 100 mock songs
        songs = []
        for i in range(100):
            songs.append({
                'id': i,
                'title': f'Song {i}',
                'artist': 'Artist',
                'duration': 200,
                'file_path': f'/path/{i}.mp3'
            })

        mock_db.get_all_songs.return_value = songs

        # Mock os.path.getsize to avoid actual file access
        with patch('os.path.getsize') as mock_size:
            mock_size.return_value = 5000000  # 5 MB

            import time
            start = time.time()
            duplicates = detector.detect_by_filesize()
            elapsed = time.time() - start

            # Should complete in < 1 second
            self.assertLess(elapsed, 1.0, f"File size detection too slow: {elapsed:.2f}s")

    # ========== INTEGRATION TESTS ==========

    def test_12_scan_library_returns_duplicate_groups(self):
        """Test full library scan returns groups"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Mock songs with duplicates
        songs = [
            {'id': 1, 'title': 'Song A', 'artist': 'Artist 1', 'duration': 200, 'file_path': '/path/1.mp3', 'bitrate': 320},
            {'id': 2, 'title': 'Song A', 'artist': 'Artist 1', 'duration': 201, 'file_path': '/path/2.mp3', 'bitrate': 128},
        ]

        mock_db.get_all_songs.return_value = songs

        # Scan library using metadata method
        result = detector.scan_library(method='metadata')

        # Should return list of duplicate groups
        self.assertIsInstance(result, list, "scan_library should return list")
        if len(result) > 0:
            # Each group should have keys: 'representative', 'duplicates', 'confidence'
            group = result[0]
            self.assertIn('songs', group, "Duplicate group missing 'songs' key")
            self.assertIsInstance(group['songs'], list, "Group songs should be list")

    def test_13_duplicate_groups_sorted_by_quality(self):
        """Test groups sorted (highest bitrate first)"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Songs with different bitrates
        songs = [
            {'id': 1, 'title': 'Song A', 'artist': 'Artist', 'duration': 200, 'file_path': '/path/1.mp3', 'bitrate': 128},
            {'id': 2, 'title': 'Song A', 'artist': 'Artist', 'duration': 200, 'file_path': '/path/2.mp3', 'bitrate': 320},
        ]

        mock_db.get_all_songs.return_value = songs

        result = detector.scan_library(method='metadata')

        if len(result) > 0:
            group = result[0]
            songs_in_group = group['songs']

            # First song should have highest bitrate
            if len(songs_in_group) >= 2:
                first_bitrate = songs_in_group[0].get('bitrate', 0)
                second_bitrate = songs_in_group[1].get('bitrate', 0)
                self.assertGreaterEqual(first_bitrate, second_bitrate, "Songs not sorted by quality")

    # ========== EDGE CASES ==========

    def test_14_empty_library_returns_no_duplicates(self):
        """Test empty library handling"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Empty library
        mock_db.get_all_songs.return_value = []

        result = detector.scan_library(method='metadata')

        # Should return empty list
        self.assertEqual(len(result), 0, "Empty library should return no duplicates")

    def test_15_single_song_returns_no_duplicates(self):
        """Test single song handling"""
        if self.detector_class is None:
            self.skipTest("Detector not implemented")

        mock_db = Mock()
        detector = self.detector_class(mock_db)

        # Single song
        songs = [
            {'id': 1, 'title': 'Only Song', 'artist': 'Artist', 'duration': 200, 'file_path': '/path/1.mp3'},
        ]

        mock_db.get_all_songs.return_value = songs

        result = detector.scan_library(method='metadata')

        # Should return no duplicates
        self.assertEqual(len(result), 0, "Single song should return no duplicates")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
