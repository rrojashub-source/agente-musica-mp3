"""
Tests for Metadata Autocompleter (Phase 4.3)
TDD: Write tests FIRST, then implement src/core/metadata_autocompleter.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock


class TestMetadataAutocompleter(unittest.TestCase):
    """Test MetadataAutocompleter (auto-complete metadata using MusicBrainz)"""

    def setUp(self):
        """Setup test fixtures"""
        # Import the class we're testing (will fail initially - expected in TDD Red phase)
        try:
            from src.core.metadata_autocompleter import MetadataAutocompleter
            self.autocompleter_class = MetadataAutocompleter
        except ImportError:
            self.autocompleter_class = None  # Expected to fail initially

    def test_autocompleter_class_exists(self):
        """Test MetadataAutocompleter class exists"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found - implement src/core/metadata_autocompleter.py")

        # Should be able to instantiate
        autocompleter = self.autocompleter_class()
        self.assertIsNotNone(autocompleter)

    def test_autocompleter_uses_musicbrainz_client(self):
        """Test autocompleter initializes MusicBrainzClient"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        # Should have MusicBrainzClient instance
        self.assertTrue(hasattr(autocompleter, 'mb_client'))
        self.assertIsNotNone(autocompleter.mb_client)

    def test_autocomplete_single_returns_matches(self):
        """Test autocomplete_single returns list of matches"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        # Mock song data
        song_data = {
            'id': 'song-123',
            'title': 'Bohemian Rhapsody',
            'artist': 'Queen'
        }

        # Mock MusicBrainz search
        with patch.object(autocompleter.mb_client, 'search_recording') as mock_search:
            mock_search.return_value = [
                {'title': 'Bohemian Rhapsody', 'artist': 'Queen', 'album': 'A Night at the Opera',
                 'year': '1975', 'genre': 'rock', 'confidence': 95},
                {'title': 'Bohemian Rhapsody', 'artist': 'Queen', 'album': 'Greatest Hits',
                 'year': '1981', 'genre': 'rock', 'confidence': 85}
            ]

            # Autocomplete
            matches = autocompleter.autocomplete_single(song_data)

            # Verify
            self.assertIsInstance(matches, list)
            self.assertGreater(len(matches), 0)
            self.assertLessEqual(len(matches), 5)

    def test_autocomplete_single_calculates_confidence(self):
        """Test confidence scoring for each match"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        song_data = {'id': '1', 'title': 'Test Song', 'artist': 'Test Artist'}

        with patch.object(autocompleter.mb_client, 'search_recording') as mock_search:
            mock_search.return_value = [
                {'title': 'Test Song', 'artist': 'Test Artist', 'album': 'Album',
                 'year': '2020', 'genre': 'pop'}
            ]

            matches = autocompleter.autocomplete_single(song_data)

            # Each match should have confidence score (0-100)
            for match in matches:
                self.assertIn('confidence', match)
                self.assertGreaterEqual(match['confidence'], 0)
                self.assertLessEqual(match['confidence'], 100)

    def test_autocomplete_single_sorts_by_confidence(self):
        """Test matches sorted by confidence score (highest first)"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        song_data = {'id': '1', 'title': 'Song', 'artist': 'Artist'}

        with patch.object(autocompleter.mb_client, 'search_recording') as mock_search:
            mock_search.return_value = [
                {'title': 'Song', 'artist': 'Artist', 'album': 'Album 1',
                 'year': '2020', 'genre': 'pop'},
                {'title': 'Song (Remix)', 'artist': 'Artist', 'album': 'Album 2',
                 'year': '2021', 'genre': 'pop'},
                {'title': 'Song', 'artist': 'Different Artist', 'album': 'Album 3',
                 'year': '2019', 'genre': 'rock'}
            ]

            matches = autocompleter.autocomplete_single(song_data)

            # Verify sorted by confidence (descending)
            for i in range(len(matches) - 1):
                self.assertGreaterEqual(matches[i]['confidence'], matches[i+1]['confidence'])

    def test_autocomplete_batch_processes_multiple_songs(self):
        """Test batch processing for multiple songs"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        # Mock 5 songs
        songs = [
            {'id': f'song-{i}', 'title': f'Song {i}', 'artist': 'Artist'}
            for i in range(5)
        ]

        with patch.object(autocompleter.mb_client, 'search_recording') as mock_search:
            mock_search.return_value = [
                {'title': 'Song', 'artist': 'Artist', 'album': 'Album',
                 'year': '2020', 'genre': 'pop'}
            ]

            # Batch autocomplete
            results = autocompleter.autocomplete_batch(songs)

            # Verify
            self.assertIsInstance(results, dict)
            self.assertEqual(len(results), 5)

            # Each song should have a result
            for song in songs:
                self.assertIn(song['id'], results)

    def test_autocomplete_batch_auto_selects_high_confidence(self):
        """Test batch mode auto-selects matches with >90% confidence"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        songs = [
            {'id': 'song-1', 'title': 'Exact Match Song', 'artist': 'Exact Artist'},
            {'id': 'song-2', 'title': 'Fuzzy Match Song', 'artist': 'Different Artist'}
        ]

        def mock_search(title, artist=None):
            if 'Exact' in title:
                # High confidence match
                return [{'title': 'Exact Match Song', 'artist': 'Exact Artist',
                        'album': 'Album', 'year': '2020', 'genre': 'pop'}]
            else:
                # Low confidence match
                return [{'title': 'Similar Song', 'artist': 'Similar Artist',
                        'album': 'Album', 'year': '2020', 'genre': 'pop'}]

        with patch.object(autocompleter.mb_client, 'search_recording', side_effect=mock_search):
            results = autocompleter.autocomplete_batch(songs, auto_select_threshold=90)

            # High confidence match should be auto-selected
            self.assertIsNotNone(results['song-1'])
            self.assertEqual(results['song-1']['status'], 'auto_selected')

            # Low confidence match should require manual selection
            if results['song-2'] is not None:
                self.assertEqual(results['song-2']['status'], 'manual_required')

    def test_autocomplete_batch_respects_limit(self):
        """Test batch processing respects item limit (100 songs)"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        # Try to process 150 songs (over limit)
        songs = [{'id': f'song-{i}', 'title': f'Song {i}', 'artist': 'Artist'}
                for i in range(150)]

        # Should either:
        # 1. Process only first 100 OR
        # 2. Raise error/warning about limit
        try:
            with patch.object(autocompleter.mb_client, 'search_recording') as mock_search:
                mock_search.return_value = []
                results = autocompleter.autocomplete_batch(songs)

                # If processed, should be max 100
                self.assertLessEqual(len(results), 100)
        except ValueError as e:
            # Or should raise error about exceeding limit
            self.assertIn('100', str(e).lower() or 'limit' in str(e).lower())

    def test_autocomplete_handles_no_matches(self):
        """Test handling when no MusicBrainz matches found"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        song_data = {'id': '1', 'title': 'NonexistentSong12345', 'artist': 'UnknownArtist'}

        with patch.object(autocompleter.mb_client, 'search_recording') as mock_search:
            mock_search.return_value = []

            matches = autocompleter.autocomplete_single(song_data)

            # Should return empty list (not None, not error)
            self.assertEqual(matches, [])

    def test_fuzzy_matching_improves_confidence(self):
        """Test fuzzy matching for similar but not exact titles"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        # Slightly different title
        song_data = {'id': '1', 'title': 'Song Title (Radio Edit)', 'artist': 'Artist'}

        with patch.object(autocompleter.mb_client, 'search_recording') as mock_search:
            mock_search.return_value = [
                {'title': 'Song Title', 'artist': 'Artist', 'album': 'Album',
                 'year': '2020', 'genre': 'pop'}
            ]

            matches = autocompleter.autocomplete_single(song_data)

            # Should still find match with reasonable confidence
            self.assertGreater(len(matches), 0)
            self.assertGreater(matches[0]['confidence'], 70)

    def test_confidence_score_calculation_exact_match(self):
        """Test confidence calculation for exact match"""
        if self.autocompleter_class is None:
            self.fail("MetadataAutocompleter class not found")

        autocompleter = self.autocompleter_class()

        # Mock calculating confidence
        song_data = {'title': 'Test Song', 'artist': 'Test Artist'}
        mb_result = {'title': 'Test Song', 'artist': 'Test Artist', 'album': 'Album',
                    'year': '2020', 'genre': 'pop'}

        # Should have method to calculate confidence
        if hasattr(autocompleter, '_calculate_confidence'):
            confidence = autocompleter._calculate_confidence(song_data, mb_result)

            # Exact match should be high confidence (90-100%)
            self.assertGreaterEqual(confidence, 90)
            self.assertLessEqual(confidence, 100)


if __name__ == "__main__":
    unittest.main()
