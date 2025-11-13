"""
Metadata Autocompleter - Phase 4.3
Auto-complete music metadata using MusicBrainz with confidence scoring

Features:
- Single song autocomplete (manual selection)
- Batch autocomplete (auto-select high confidence)
- Fuzzy string matching for confidence scoring
- User override support

Security (Pre-Phase 5 Hardening):
- Input sanitization to prevent injection attacks
"""
import logging
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from src.api.musicbrainz_client import MusicBrainzClient
from src.utils.input_sanitizer import sanitize_query

# Setup logger
logger = logging.getLogger(__name__)


class MetadataAutocompleter:
    """
    Auto-complete metadata using MusicBrainz with confidence scoring

    Usage:
        autocompleter = MetadataAutocompleter()

        # Single song (returns matches for manual selection)
        song = {'id': '1', 'title': 'Bohemian Rhapsody', 'artist': 'Queen'}
        matches = autocompleter.autocomplete_single(song)

        # Batch processing (auto-selects high confidence)
        songs = [{'id': '1', 'title': 'Song 1', 'artist': 'Artist 1'}, ...]
        results = autocompleter.autocomplete_batch(songs, auto_select_threshold=90)
    """

    def __init__(self):
        """
        Initialize metadata autocompleter
        """
        self.mb_client = MusicBrainzClient()
        logger.info("MetadataAutocompleter initialized")

    def autocomplete_single(self, song_data: Dict) -> List[Dict]:
        """
        Autocomplete single song (returns matches for user selection)

        Args:
            song_data (dict): Song data with 'title' and optional 'artist'
                             Format: {'id', 'title', 'artist'}

        Returns:
            list: List of matches sorted by confidence (highest first)
                  Format: [{'title', 'artist', 'album', 'year', 'genre', 'confidence'}]

        Examples:
            >>> song = {'id': '1', 'title': 'Bohemian Rhapsody', 'artist': 'Queen'}
            >>> matches = autocompleter.autocomplete_single(song)
            >>> print(matches[0]['confidence'])  # e.g., 95
        """
        # Extract query params
        title = song_data.get('title', '')
        artist = song_data.get('artist', None)

        # Sanitize inputs (remove injection attempts, control chars)
        title = sanitize_query(title, max_length=500)
        if artist:
            artist = sanitize_query(artist, max_length=500)

        if not title:
            logger.warning("No title provided for autocomplete")
            return []

        # Search MusicBrainz
        mb_results = self.mb_client.search_recording(title, artist=artist)

        if not mb_results:
            logger.info(f"No MusicBrainz matches for: {title}")
            return []

        # Calculate confidence for each match
        matches = []
        for mb_result in mb_results:
            confidence = self._calculate_confidence(song_data, mb_result)
            match = {**mb_result, 'confidence': confidence}
            matches.append(match)

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x['confidence'], reverse=True)

        logger.info(f"Autocomplete single: {len(matches)} matches for '{title}'")
        return matches

    def autocomplete_batch(self, songs: List[Dict], auto_select_threshold: int = 90) -> Dict[str, Optional[Dict]]:
        """
        Batch autocomplete for multiple songs

        Args:
            songs (list): List of song dicts [{'id', 'title', 'artist'}, ...]
            auto_select_threshold (int): Auto-select if confidence >= this (default: 90)

        Returns:
            dict: Results by song ID
                  {
                      'song-id': {
                          'metadata': {...},
                          'confidence': 95,
                          'status': 'auto_selected'  # or 'manual_required'
                      }
                  }

        Examples:
            >>> songs = [{'id': '1', 'title': 'Song', 'artist': 'Artist'}]
            >>> results = autocompleter.autocomplete_batch(songs)
            >>> print(results['1']['status'])  # 'auto_selected' or 'manual_required'
        """
        # Limit to 100 songs
        if len(songs) > 100:
            logger.warning(f"Batch processing limited to 100 songs (received {len(songs)})")
            songs = songs[:100]

        results = {}

        for song in songs:
            song_id = song.get('id')
            if not song_id:
                logger.warning("Song without ID, skipping")
                continue

            # Get matches
            matches = self.autocomplete_single(song)

            if not matches:
                # No matches found
                results[song_id] = None
                continue

            # Get best match
            best_match = matches[0]

            # Auto-select if confidence high enough
            if best_match['confidence'] >= auto_select_threshold:
                results[song_id] = {
                    'metadata': best_match,
                    'confidence': best_match['confidence'],
                    'status': 'auto_selected'
                }
                logger.info(f"Auto-selected: {song.get('title')} (confidence: {best_match['confidence']})")
            else:
                # Requires manual selection
                results[song_id] = {
                    'metadata': best_match,
                    'confidence': best_match['confidence'],
                    'status': 'manual_required',
                    'all_matches': matches  # Provide all matches for manual selection
                }
                logger.info(f"Manual required: {song.get('title')} (confidence: {best_match['confidence']})")

        logger.info(f"Batch complete: {len(results)} songs processed")
        return results

    def _calculate_confidence(self, song_data: Dict, mb_result: Dict) -> int:
        """
        Calculate confidence score (0-100) for match

        Args:
            song_data (dict): Original song data
            mb_result (dict): MusicBrainz result

        Returns:
            int: Confidence score (0-100)
        """
        confidence = 0

        # Title similarity (40% weight)
        title_sim = self._fuzzy_match(
            song_data.get('title', '').lower(),
            mb_result.get('title', '').lower()
        )
        confidence += int(title_sim * 40)

        # Artist similarity (40% weight)
        if song_data.get('artist'):
            artist_sim = self._fuzzy_match(
                song_data.get('artist', '').lower(),
                mb_result.get('artist', '').lower()
            )
            confidence += int(artist_sim * 40)
        else:
            # No artist to compare, give partial credit
            confidence += 20

        # Album name presence (10% weight)
        if mb_result.get('album') and mb_result['album'] != 'Unknown':
            confidence += 10

        # Year presence (5% weight)
        if mb_result.get('year') and mb_result['year'] != 'Unknown':
            confidence += 5

        # Genre presence (5% weight)
        if mb_result.get('genre') and mb_result['genre'] != 'Unknown':
            confidence += 5

        # Ensure 0-100 range
        confidence = max(0, min(100, confidence))

        return confidence

    def _fuzzy_match(self, str1: str, str2: str) -> float:
        """
        Calculate fuzzy string similarity (0.0 - 1.0)

        Args:
            str1 (str): First string
            str2 (str): Second string

        Returns:
            float: Similarity ratio (0.0 = no match, 1.0 = exact match)
        """
        if not str1 or not str2:
            return 0.0

        # Use SequenceMatcher for fuzzy matching
        ratio = SequenceMatcher(None, str1, str2).ratio()

        return ratio
