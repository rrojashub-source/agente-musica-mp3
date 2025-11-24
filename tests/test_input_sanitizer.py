"""
Tests for Input Sanitizer (TDD Red Phase)

Purpose: Prevent injection attacks and filesystem issues
- Remove control characters
- Remove SQL/command injection attempts
- Sanitize filenames for filesystem safety
- Preserve Unicode (Beyoncé, etc.)

Test Strategy: Red → Green → Refactor
Expected Result: All tests FAIL initially (no implementation yet)
"""
import pytest
import unittest


class TestInputSanitizer(unittest.TestCase):
    """Test input sanitization for security"""

    def setUp(self):
        """Setup test fixtures"""
        try:
            from src.utils.input_sanitizer import sanitize_query, sanitize_filename
            self.sanitize_query = sanitize_query
            self.sanitize_filename = sanitize_filename
        except ImportError:
            self.sanitize_query = None
            self.sanitize_filename = None

    # ========== QUERY SANITIZATION TESTS ==========

    def test_01_sanitizer_exists(self):
        """Test sanitizer module exists"""
        if self.sanitize_query is None:
            self.fail("sanitize_query not found - implement src/utils/input_sanitizer.py")

        self.assertIsNotNone(self.sanitize_query)
        self.assertIsNotNone(self.sanitize_filename)

    def test_02_sanitize_query_removes_control_chars(self):
        """Test removal of control characters (0x00-0x1f)"""
        if self.sanitize_query is None:
            self.skipTest("Sanitizer not implemented")

        # Input with control characters
        query = "test\x00\x01\x02song\x0a\x0d"
        result = self.sanitize_query(query)

        # Should remove all control chars
        self.assertEqual(result, "testsong")
        self.assertNotIn("\x00", result)
        self.assertNotIn("\x01", result)

    def test_03_sanitize_query_removes_sql_injection(self):
        """Test removal of SQL injection attempts"""
        if self.sanitize_query is None:
            self.skipTest("Sanitizer not implemented")

        query = "test'; DROP TABLE songs;--"
        result = self.sanitize_query(query)

        # Should remove dangerous SQL characters
        self.assertNotIn("'", result)
        self.assertNotIn(";", result)
        # Note: double dash might remain as single dash

    def test_04_sanitize_query_truncates_long_input(self):
        """Test truncation of long queries to 500 chars"""
        if self.sanitize_query is None:
            self.skipTest("Sanitizer not implemented")

        query = "a" * 1000
        result = self.sanitize_query(query)

        # Should truncate to 500 chars (default)
        self.assertLessEqual(len(result), 500)
        self.assertEqual(len(result), 500)

    def test_05_sanitize_query_preserves_unicode(self):
        """Test preservation of Unicode characters"""
        if self.sanitize_query is None:
            self.skipTest("Sanitizer not implemented")

        query = "Beyoncé - Déjà Vu"
        result = self.sanitize_query(query)

        # Should preserve Unicode accents
        self.assertIn("é", result)
        self.assertIn("Beyoncé", result)

    def test_06_sanitize_query_removes_command_injection(self):
        """Test removal of command injection attempts"""
        if self.sanitize_query is None:
            self.skipTest("Sanitizer not implemented")

        query = "test | ls; rm -rf /"
        result = self.sanitize_query(query)

        # Should remove pipe and command separators
        self.assertNotIn("|", result)
        self.assertNotIn(";", result)

    # ========== FILENAME SANITIZATION TESTS ==========

    def test_07_sanitize_filename_removes_invalid_chars(self):
        """Test filename sanitization removes invalid filesystem chars"""
        if self.sanitize_filename is None:
            self.skipTest("Sanitizer not implemented")

        filename = "song/name:with*invalid|chars?.mp3"
        result = self.sanitize_filename(filename)

        # Should remove/replace invalid filesystem chars
        self.assertNotIn("/", result)
        self.assertNotIn(":", result)
        self.assertNotIn("*", result)
        self.assertNotIn("|", result)
        self.assertNotIn("?", result)

        # Should still be a valid filename
        self.assertTrue(len(result) > 0)
        self.assertIn(".mp3", result)

    def test_08_sanitize_filename_preserves_extension(self):
        """Test filename sanitization preserves file extension"""
        if self.sanitize_filename is None:
            self.skipTest("Sanitizer not implemented")

        filename = "very/long/path/with:invalid*chars.mp3"
        result = self.sanitize_filename(filename)

        # Should preserve .mp3 extension
        self.assertTrue(result.endswith(".mp3"))

    def test_09_sanitize_filename_handles_empty(self):
        """Test filename sanitization handles empty input"""
        if self.sanitize_filename is None:
            self.skipTest("Sanitizer not implemented")

        filename = ""
        result = self.sanitize_filename(filename)

        # Should return a default filename
        self.assertEqual(result, "untitled")

    def test_10_sanitize_filename_truncates_long_names(self):
        """Test filename sanitization truncates to 255 chars (filesystem limit)"""
        if self.sanitize_filename is None:
            self.skipTest("Sanitizer not implemented")

        filename = "a" * 300 + ".mp3"
        result = self.sanitize_filename(filename)

        # Should truncate to 255 chars max
        self.assertLessEqual(len(result), 255)
        # Should still preserve extension
        self.assertTrue(result.endswith(".mp3"))


    # ========== PATH VALIDATION TESTS ==========

    def test_11_validate_path_blocks_traversal(self):
        """Test path validation blocks directory traversal"""
        try:
            from src.utils.input_sanitizer import validate_path
        except ImportError:
            self.skipTest("validate_path not implemented")

        # Attempt to escape base directory
        is_valid, result = validate_path("../../../etc/passwd", "/home/user/music")
        self.assertFalse(is_valid)
        self.assertIn("escapes", result.lower())

    def test_12_validate_path_allows_valid_paths(self):
        """Test path validation allows valid subdirectories"""
        try:
            from src.utils.input_sanitizer import validate_path
        except ImportError:
            self.skipTest("validate_path not implemented")

        import tempfile
        import os

        # Create a temp directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "music")
            os.makedirs(subdir)

            is_valid, result = validate_path("music", tmpdir)
            self.assertTrue(is_valid)

    def test_13_validate_path_empty_input(self):
        """Test path validation handles empty input"""
        try:
            from src.utils.input_sanitizer import validate_path
        except ImportError:
            self.skipTest("validate_path not implemented")

        is_valid, result = validate_path("", "/home/user")
        self.assertFalse(is_valid)

    # ========== URL VALIDATION TESTS ==========

    def test_14_sanitize_url_blocks_file_scheme(self):
        """Test URL validation blocks file:// scheme"""
        try:
            from src.utils.input_sanitizer import sanitize_url
        except ImportError:
            self.skipTest("sanitize_url not implemented")

        is_valid, result = sanitize_url("file:///etc/passwd")
        self.assertFalse(is_valid)
        self.assertIn("scheme", result.lower())

    def test_15_sanitize_url_allows_https(self):
        """Test URL validation allows https://"""
        try:
            from src.utils.input_sanitizer import sanitize_url
        except ImportError:
            self.skipTest("sanitize_url not implemented")

        is_valid, result = sanitize_url("https://youtube.com/watch?v=abc123")
        self.assertTrue(is_valid)

    def test_16_sanitize_url_domain_restriction(self):
        """Test URL validation enforces domain restrictions"""
        try:
            from src.utils.input_sanitizer import sanitize_url
        except ImportError:
            self.skipTest("sanitize_url not implemented")

        # Should allow youtube.com
        is_valid, _ = sanitize_url("https://youtube.com/watch", ["youtube.com"])
        self.assertTrue(is_valid)

        # Should block evil.com
        is_valid, _ = sanitize_url("https://evil.com/malware", ["youtube.com"])
        self.assertFalse(is_valid)

    # ========== METADATA SANITIZATION TESTS ==========

    def test_17_sanitize_metadata_removes_html(self):
        """Test metadata sanitization removes HTML tags"""
        try:
            from src.utils.input_sanitizer import sanitize_metadata
        except ImportError:
            self.skipTest("sanitize_metadata not implemented")

        metadata = {"title": "<script>alert('xss')</script>Test", "artist": "Artist"}
        result = sanitize_metadata(metadata)

        self.assertNotIn("<script>", result["title"])
        self.assertNotIn("</script>", result["title"])
        self.assertIn("Test", result["title"])

    def test_18_sanitize_metadata_handles_nested(self):
        """Test metadata sanitization handles nested structures"""
        try:
            from src.utils.input_sanitizer import sanitize_metadata
        except ImportError:
            self.skipTest("sanitize_metadata not implemented")

        metadata = {
            "title": "Song",
            "album": {"name": "<b>Album</b>", "year": 2024}
        }
        result = sanitize_metadata(metadata)

        self.assertNotIn("<b>", result["album"]["name"])


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
