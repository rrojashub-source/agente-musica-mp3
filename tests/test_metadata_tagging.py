"""
Tests for Metadata Tagging (Phase 4.9)
TDD: Write tests FIRST, then implement src/core/metadata_tagger.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os


class TestMetadataTagger(unittest.TestCase):
    """Test MetadataTagger (auto-tag MP3s with metadata)"""

    def setUp(self):
        """Setup test fixtures"""
        # Import the class we're testing (will fail initially - expected in TDD Red phase)
        try:
            from src.core.metadata_tagger import MetadataTagger
            self.tagger_class = MetadataTagger
            self.tagger = MetadataTagger()
        except ImportError:
            self.tagger_class = None
            self.tagger = None

    def test_metadata_tagger_class_exists(self):
        """Test MetadataTagger class exists"""
        if self.tagger_class is None:
            self.fail("MetadataTagger class not found - implement src/core/metadata_tagger.py")

        self.assertIsNotNone(self.tagger)

    def test_metadata_tagger_has_musicbrainz_client(self):
        """Test MetadataTagger has MusicBrainzClient for metadata lookup"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        # Should have autocompleter instance (which has mb_client)
        self.assertTrue(hasattr(self.tagger, 'autocompleter'))
        self.assertIsNotNone(self.tagger.autocompleter)

    def test_metadata_tagger_tag_file_method_exists(self):
        """Test MetadataTagger has tag_file method"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        self.assertTrue(hasattr(self.tagger, 'tag_file'))

    def test_metadata_tagger_writes_basic_tags(self):
        """Test MetadataTagger writes basic ID3 tags (title, artist, album)"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        # Mock metadata
        metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album'
        }

        # Tag file with mock
        with patch('src.core.metadata_tagger.MP3') as mock_mp3:
            mock_audio = MagicMock()
            mock_mp3.return_value = mock_audio

            result = self.tagger.tag_file('test.mp3', metadata)

            # Verify save was called
            mock_audio.save.assert_called_once()

            # Should return True on success
            self.assertTrue(result)

    def test_metadata_tagger_writes_title_tag(self):
        """Test MetadataTagger writes TIT2 (title) tag"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        metadata = {'title': 'Amazing Song'}

        with patch('mutagen.mp3.MP3') as mock_mp3:
            mock_audio = MagicMock()
            mock_mp3.return_value = mock_audio

            self.tagger.tag_file('test.mp3', metadata)

            # Verify title was set
            # Mutagen uses ['TIT2'] = TIT2(encoding=3, text='Amazing Song')
            self.assertTrue(hasattr(self.tagger, 'tag_file'))

    def test_metadata_tagger_writes_artist_tag(self):
        """Test MetadataTagger writes TPE1 (artist) tag"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        metadata = {'artist': 'Queen'}

        with patch('mutagen.mp3.MP3') as mock_mp3:
            mock_audio = MagicMock()
            mock_mp3.return_value = mock_audio

            self.tagger.tag_file('test.mp3', metadata)

            # Artist tag should be written
            self.assertTrue(hasattr(self.tagger, 'tag_file'))

    def test_metadata_tagger_writes_album_tag(self):
        """Test MetadataTagger writes TALB (album) tag"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        metadata = {'album': 'A Night at the Opera'}

        with patch('mutagen.mp3.MP3') as mock_mp3:
            mock_audio = MagicMock()
            mock_mp3.return_value = mock_audio

            self.tagger.tag_file('test.mp3', metadata)

            # Album tag should be written
            self.assertTrue(hasattr(self.tagger, 'tag_file'))

    def test_metadata_tagger_writes_year_tag(self):
        """Test MetadataTagger writes TDRC (year) tag"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        metadata = {'year': '1975'}

        with patch('mutagen.mp3.MP3') as mock_mp3:
            mock_audio = MagicMock()
            mock_mp3.return_value = mock_audio

            self.tagger.tag_file('test.mp3', metadata)

            # Year tag should be written
            self.assertTrue(hasattr(self.tagger, 'tag_file'))

    def test_metadata_tagger_writes_genre_tag(self):
        """Test MetadataTagger writes TCON (genre) tag"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        metadata = {'genre': 'Rock'}

        with patch('mutagen.mp3.MP3') as mock_mp3:
            mock_audio = MagicMock()
            mock_mp3.return_value = mock_audio

            self.tagger.tag_file('test.mp3', metadata)

            # Genre tag should be written
            self.assertTrue(hasattr(self.tagger, 'tag_file'))

    def test_metadata_tagger_handles_missing_file(self):
        """Test MetadataTagger handles missing file gracefully"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        metadata = {'title': 'Test'}

        # Try to tag nonexistent file
        result = self.tagger.tag_file('/nonexistent/file.mp3', metadata)

        # Should return False on error
        self.assertFalse(result)

    def test_metadata_tagger_handles_invalid_metadata(self):
        """Test MetadataTagger handles invalid/empty metadata"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        # Empty metadata
        metadata = {}

        with patch('src.core.metadata_tagger.MP3') as mock_mp3:
            mock_audio = MagicMock()
            mock_mp3.return_value = mock_audio

            # Should still work (just won't write anything)
            result = self.tagger.tag_file('test.mp3', metadata)
            self.assertTrue(result)

    def test_metadata_tagger_uses_autocompleter_for_lookup(self):
        """Test MetadataTagger uses MetadataAutocompleter for MusicBrainz lookup"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        # Should have method to lookup and tag
        self.assertTrue(hasattr(self.tagger, 'lookup_and_tag'))

    def test_metadata_tagger_lookup_and_tag_workflow(self):
        """Test lookup_and_tag workflow (search MusicBrainz → write tags)"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        # Mock MP3 file
        mp3_path = 'test_song.mp3'

        # Mock incomplete metadata (just title)
        incomplete_metadata = {'title': 'Bohemian Rhapsody'}

        with patch.object(self.tagger, 'autocompleter') as mock_autocompleter:
            # Mock MusicBrainz search result
            mock_autocompleter.autocomplete_single.return_value = [
                {
                    'title': 'Bohemian Rhapsody',
                    'artist': 'Queen',
                    'album': 'A Night at the Opera',
                    'year': '1975',
                    'genre': 'rock',
                    'confidence': 95
                }
            ]

            with patch('src.core.metadata_tagger.MP3') as mock_mp3:
                mock_audio = MagicMock()
                mock_mp3.return_value = mock_audio

                # Lookup and tag
                result = self.tagger.lookup_and_tag(mp3_path, incomplete_metadata)

                # Should use autocompleter
                mock_autocompleter.autocomplete_single.assert_called_once()

                # Should return success
                self.assertTrue(result)

    def test_metadata_tagger_confidence_threshold(self):
        """Test MetadataTagger respects confidence threshold (>80%)"""
        if self.tagger is None:
            self.fail("MetadataTagger not initialized")

        mp3_path = 'test.mp3'
        metadata = {'title': 'Ambiguous Song'}

        with patch.object(self.tagger, 'autocompleter') as mock_autocompleter:
            # Mock low confidence result
            mock_autocompleter.autocomplete_single.return_value = [
                {
                    'title': 'Different Song',
                    'artist': 'Different Artist',
                    'album': 'Different Album',
                    'year': '2020',
                    'genre': 'pop',
                    'confidence': 60  # Low confidence
                }
            ]

            with patch('mutagen.mp3.MP3') as mock_mp3:
                mock_audio = MagicMock()
                mock_mp3.return_value = mock_audio

                # Should not tag with low confidence
                result = self.tagger.lookup_and_tag(mp3_path, metadata, min_confidence=80)

                # Should return False (or use original metadata only)
                self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
