"""
Tests for MusicBrainz Client (Phase 4.3)
TDD: Write tests FIRST, then implement src/api/musicbrainz_client.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil


class TestMusicBrainzClient(unittest.TestCase):
    """Test MusicBrainzClient (metadata search via MusicBrainz API)"""

    def setUp(self):
        """Setup test fixtures"""
        # Create temporary directory for downloads
        self.test_dir = tempfile.mkdtemp()
        self.test_output = Path(self.test_dir) / "cover.jpg"

        # Import the class we're testing (will fail initially - expected in TDD Red phase)
        try:
            from src.api.musicbrainz_client import MusicBrainzClient
            self.client_class = MusicBrainzClient
        except ImportError:
            self.client_class = None  # Expected to fail initially

    def tearDown(self):
        """Cleanup test files"""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_client_class_exists(self):
        """Test MusicBrainzClient class exists"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found - implement src/api/musicbrainz_client.py")

        # Should be able to instantiate
        client = self.client_class()
        self.assertIsNotNone(client)

    def test_client_initialization_sets_user_agent(self):
        """Test client initializes with custom user agent"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        # Create client
        client = self.client_class(app_name="NexusMusicManager", app_version="1.0")

        # Verify user agent is set (should have app name)
        self.assertTrue(hasattr(client, 'app_name'))
        self.assertEqual(client.app_name, "NexusMusicManager")
        self.assertEqual(client.app_version, "1.0")

    def test_search_recording_returns_results(self):
        """Test search_recording returns list of matches"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        # Mock MusicBrainz API response
        with patch('musicbrainzngs.search_recordings') as mock_search:
            mock_search.return_value = {
                'recording-list': [
                    {
                        'id': 'test-id-1',
                        'title': 'Bohemian Rhapsody',
                        'artist-credit': [{'artist': {'name': 'Queen'}}],
                        'release-list': [{
                            'title': 'A Night at the Opera',
                            'date': '1975',
                            'release-group': {'type': 'Album'}
                        }],
                        'tag-list': [{'name': 'rock', 'count': 10}]
                    }
                ]
            }

            # Search
            results = client.search_recording("Bohemian Rhapsody", artist="Queen")

            # Verify results
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            self.assertLessEqual(len(results), 5, "Should return max 5 results")

    def test_search_recording_result_format(self):
        """Test search results have correct format"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        # Mock API response
        with patch('musicbrainzngs.search_recordings') as mock_search:
            mock_search.return_value = {
                'recording-list': [
                    {
                        'id': 'test-id-1',
                        'title': 'Test Song',
                        'artist-credit': [{'artist': {'name': 'Test Artist'}}],
                        'release-list': [{
                            'title': 'Test Album',
                            'date': '2020',
                            'release-group': {'type': 'Album'}
                        }],
                        'tag-list': [{'name': 'pop', 'count': 5}]
                    }
                ]
            }

            results = client.search_recording("Test Song")

            # Verify format
            self.assertEqual(len(results), 1)
            result = results[0]

            # Required fields
            self.assertIn('title', result)
            self.assertIn('artist', result)
            self.assertIn('album', result)
            self.assertIn('year', result)
            self.assertIn('genre', result)

            # Verify values
            self.assertEqual(result['title'], 'Test Song')
            self.assertEqual(result['artist'], 'Test Artist')
            self.assertEqual(result['album'], 'Test Album')
            self.assertEqual(result['year'], '2020')

    def test_search_recording_with_artist_filter(self):
        """Test searching with artist parameter"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        with patch('musicbrainzngs.search_recordings') as mock_search:
            mock_search.return_value = {'recording-list': []}

            # Search with artist
            client.search_recording("Song Title", artist="Artist Name")

            # Verify API called with artist parameter
            mock_search.assert_called_once()
            call_args = mock_search.call_args[1]
            self.assertIn('artist', call_args['query'].lower())

    def test_search_recording_handles_no_results(self):
        """Test handling when no results found"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        with patch('musicbrainzngs.search_recordings') as mock_search:
            mock_search.return_value = {'recording-list': []}

            # Search
            results = client.search_recording("NonexistentSong12345")

            # Should return empty list (not None, not error)
            self.assertEqual(results, [])

    def test_search_recording_limits_to_5_results(self):
        """Test search returns maximum 5 results"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        with patch('musicbrainzngs.search_recordings') as mock_search:
            # Mock 10 results
            mock_results = []
            for i in range(10):
                mock_results.append({
                    'id': f'id-{i}',
                    'title': f'Song {i}',
                    'artist-credit': [{'artist': {'name': 'Artist'}}],
                    'release-list': [{'title': 'Album', 'date': '2020'}],
                    'tag-list': []
                })

            mock_search.return_value = {'recording-list': mock_results}

            # Search
            results = client.search_recording("Test")

            # Should limit to 5
            self.assertLessEqual(len(results), 5)

    def test_search_recording_handles_api_error(self):
        """Test handling MusicBrainz API errors"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        with patch('musicbrainzngs.search_recordings') as mock_search:
            mock_search.side_effect = Exception("API Error")

            # Should handle error gracefully (return empty, not crash)
            results = client.search_recording("Test")
            self.assertEqual(results, [])

    def test_download_album_art_downloads_image(self):
        """Test downloading album art from URL"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        # Mock HTTP request
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'fake_image_data'
            mock_get.return_value = mock_response

            # Download
            success = client.download_album_art("https://example.com/cover.jpg", str(self.test_output))

            # Verify
            self.assertTrue(success, "Should return True on success")
            self.assertTrue(self.test_output.exists(), "Image file should be created")

    def test_download_album_art_handles_invalid_url(self):
        """Test handling invalid URL for album art"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        # Should handle gracefully
        success = client.download_album_art("invalid-url", str(self.test_output))
        self.assertFalse(success, "Should return False on failure")

    def test_rate_limiting_respected(self):
        """Test respects MusicBrainz rate limit (1 request/second)"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        # Client should have rate limiting mechanism
        self.assertTrue(hasattr(client, '_rate_limiter') or hasattr(client, '_last_request_time'),
                       "Client should have rate limiting mechanism")

    def test_search_recording_extracts_genre_from_tags(self):
        """Test genre extraction from MusicBrainz tags"""
        if self.client_class is None:
            self.fail("MusicBrainzClient class not found")

        client = self.client_class()

        with patch('musicbrainzngs.search_recordings') as mock_search:
            mock_search.return_value = {
                'recording-list': [{
                    'id': 'test-id',
                    'title': 'Song',
                    'artist-credit': [{'artist': {'name': 'Artist'}}],
                    'release-list': [{'title': 'Album', 'date': '2020'}],
                    'tag-list': [
                        {'name': 'rock', 'count': 10},
                        {'name': 'progressive rock', 'count': 5}
                    ]
                }]
            }

            results = client.search_recording("Song")

            # Should extract most popular genre
            self.assertEqual(results[0]['genre'], 'rock')


if __name__ == "__main__":
    unittest.main()
