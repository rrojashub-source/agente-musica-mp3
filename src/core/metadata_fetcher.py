"""
Metadata Fetcher - Intelligent metadata search and matching

Purpose: Search correct metadata from multiple sources
- MusicBrainz API (primary)
- Spotify API (secondary)
- AcoustID fingerprinting (if available)
- Smart matching with confidence scoring

Created: November 18, 2025
"""
import logging
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class MetadataFetcher:
    """
    Fetch correct metadata from multiple sources with intelligent matching

    Search strategy:
    1. Try MusicBrainz first (most accurate metadata)
    2. Try Spotify as fallback (broader coverage)
    3. Score results by similarity to query
    4. Return best match with confidence level
    """

    def __init__(self, musicbrainz_client=None, spotify_client=None):
        """
        Initialize metadata fetcher

        Args:
            musicbrainz_client: MusicBrainzClient instance (optional)
            spotify_client: SpotifyClient instance (optional)
        """
        self.musicbrainz_client = musicbrainz_client
        self.spotify_client = spotify_client

        logger.info("MetadataFetcher initialized")

    def search_by_title_artist(self, title: str, artist: str,
                                duration: Optional[int] = None) -> List[Dict]:
        """
        Search metadata by title + artist

        Args:
            title: Song title (cleaned)
            artist: Artist name (cleaned)
            duration: Duration in seconds (optional, for better matching)

        Returns:
            List of match results with scores:
            [
                {
                    'title': str,
                    'artist': str,
                    'album': str,
                    'year': int,
                    'duration': int,
                    'score': float (0-100),
                    'source': 'musicbrainz' or 'spotify'
                },
                ...
            ]
        """
        results = []

        # Try MusicBrainz first
        if self.musicbrainz_client:
            try:
                mb_results = self._search_musicbrainz(title, artist, duration)
                results.extend(mb_results)
            except Exception as e:
                logger.warning(f"MusicBrainz search failed: {e}")

        # Try Spotify as fallback
        if self.spotify_client:
            try:
                spotify_results = self._search_spotify(title, artist, duration)
                results.extend(spotify_results)
            except Exception as e:
                logger.warning(f"Spotify search failed: {e}")

        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)

        return results

    def _search_musicbrainz(self, title: str, artist: str,
                           duration: Optional[int] = None) -> List[Dict]:
        """
        Search MusicBrainz API

        Args:
            title: Song title
            artist: Artist name
            duration: Duration in seconds (optional)

        Returns:
            List of results with scores
        """
        if not self.musicbrainz_client:
            return []

        results = []

        try:
            # Build MusicBrainz query
            query = f'recording:"{title}" AND artist:"{artist}"'

            # Search (using adapter or direct client)
            mb_results = self.musicbrainz_client.search_recordings(query, limit=5)

            if not mb_results:
                logger.debug(f"No MusicBrainz results for: {title} - {artist}")
                return []

            # Process results
            for mb_recording in mb_results:
                # Extract metadata (handle both adapter and raw formats)
                mb_title = mb_recording.get('title', '')
                mb_artist = self._extract_artist_name(mb_recording)
                mb_album = self._extract_album_name(mb_recording)
                mb_year = self._extract_year(mb_recording)

                # Handle duration (may be missing or in different formats)
                mb_duration = 0
                if 'length' in mb_recording:
                    # Raw format: milliseconds
                    mb_duration = mb_recording.get('length', 0) // 1000
                elif 'duration' in mb_recording:
                    # Adapter format: seconds
                    mb_duration = mb_recording.get('duration', 0)

                # Calculate match score
                score = self._calculate_match_score(
                    query_title=title,
                    query_artist=artist,
                    query_duration=duration,
                    result_title=mb_title,
                    result_artist=mb_artist,
                    result_duration=mb_duration
                )

                results.append({
                    'title': mb_title,
                    'artist': mb_artist,
                    'album': mb_album,
                    'year': mb_year,
                    'duration': mb_duration,
                    'score': score,
                    'source': 'musicbrainz',
                    'raw': mb_recording
                })

        except Exception as e:
            logger.error(f"MusicBrainz search error: {e}")

        return results

    def _search_spotify(self, title: str, artist: str,
                       duration: Optional[int] = None) -> List[Dict]:
        """
        Search Spotify API

        Args:
            title: Song title
            artist: Artist name
            duration: Duration in seconds (optional)

        Returns:
            List of results with scores
        """
        if not self.spotify_client:
            return []

        results = []

        try:
            # Build Spotify query
            query = f"track:{title} artist:{artist}"

            # Search (using adapter or direct client)
            spotify_results = self.spotify_client.search_tracks(query, limit=5)

            if not spotify_results:
                logger.debug(f"No Spotify results for: {title} - {artist}")
                return []

            # Process results
            for track in spotify_results:
                # Extract metadata (handle both adapter and raw formats)
                sp_title = track.get('name', '') or track.get('title', '')

                # Handle artists (different formats)
                sp_artist = ''
                if 'artists' in track and track['artists']:
                    sp_artist = track['artists'][0].get('name', '')
                elif 'artist' in track:
                    sp_artist = track.get('artist', '')

                # Handle album (different formats)
                sp_album = ''
                if 'album' in track:
                    if isinstance(track['album'], dict):
                        sp_album = track['album'].get('name', '')
                    else:
                        sp_album = track['album']

                # Handle year
                sp_year = self._extract_spotify_year(track)

                # Handle duration (may be in different formats)
                sp_duration = 0
                if 'duration_ms' in track:
                    # Raw format: milliseconds
                    sp_duration = track.get('duration_ms', 0) // 1000
                elif 'duration' in track:
                    # Adapter format: seconds
                    sp_duration = track.get('duration', 0)

                # Calculate match score
                score = self._calculate_match_score(
                    query_title=title,
                    query_artist=artist,
                    query_duration=duration,
                    result_title=sp_title,
                    result_artist=sp_artist,
                    result_duration=sp_duration
                )

                results.append({
                    'title': sp_title,
                    'artist': sp_artist,
                    'album': sp_album,
                    'year': sp_year,
                    'duration': sp_duration,
                    'score': score,
                    'source': 'spotify',
                    'raw': track
                })

        except Exception as e:
            logger.error(f"Spotify search error: {e}")

        return results

    def _calculate_match_score(self, query_title: str, query_artist: str,
                               query_duration: Optional[int],
                               result_title: str, result_artist: str,
                               result_duration: int) -> float:
        """
        Calculate match confidence score (0-100)

        Scoring weights:
        - Title similarity: 50%
        - Artist similarity: 30%
        - Duration match: 20%

        Args:
            query_*: Original query parameters
            result_*: Result from API

        Returns:
            Score from 0 to 100
        """
        # Title similarity (50% weight)
        title_sim = self._string_similarity(query_title, result_title)
        title_score = title_sim * 50

        # Artist similarity (30% weight)
        artist_sim = self._string_similarity(query_artist, result_artist)
        artist_score = artist_sim * 30

        # Duration similarity (20% weight)
        duration_score = 0
        if query_duration and result_duration:
            duration_diff = abs(query_duration - result_duration)
            if duration_diff <= 3:
                duration_score = 20  # Perfect match
            elif duration_diff <= 10:
                duration_score = 15  # Close match
            elif duration_diff <= 30:
                duration_score = 10  # Acceptable match
            # else: 0 (poor match)

        total_score = title_score + artist_score + duration_score

        return round(total_score, 2)

    def _string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using SequenceMatcher

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        if not str1 or not str2:
            return 0.0

        # Normalize for comparison
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()

        return SequenceMatcher(None, str1, str2).ratio()

    def _extract_artist_name(self, mb_recording: Dict) -> str:
        """Extract artist name from MusicBrainz recording"""
        try:
            artist_credit = mb_recording.get('artist-credit', [])
            if artist_credit:
                return artist_credit[0].get('name', 'Unknown Artist')
        except:
            pass
        return 'Unknown Artist'

    def _extract_album_name(self, mb_recording: Dict) -> str:
        """Extract album name from MusicBrainz recording"""
        try:
            releases = mb_recording.get('releases', [])
            if releases:
                return releases[0].get('title', 'Unknown Album')
        except:
            pass
        return 'Unknown Album'

    def _extract_year(self, mb_recording: Dict) -> Optional[int]:
        """Extract release year from MusicBrainz recording"""
        try:
            releases = mb_recording.get('releases', [])
            if releases:
                date_str = releases[0].get('date', '')
                if date_str:
                    return int(date_str[:4])
        except:
            pass
        return None

    def _extract_spotify_year(self, track: Dict) -> Optional[int]:
        """Extract release year from Spotify track"""
        try:
            album = track.get('album', {})
            release_date = album.get('release_date', '')
            if release_date:
                return int(release_date[:4])
        except:
            pass
        return None

    def get_best_match(self, results: List[Dict], min_confidence: float = 70.0) -> Optional[Dict]:
        """
        Get best match from results

        Args:
            results: List of search results with scores
            min_confidence: Minimum confidence score to accept (0-100)

        Returns:
            Best match if score >= min_confidence, None otherwise
        """
        if not results:
            return None

        best = results[0]  # Already sorted by score

        if best['score'] >= min_confidence:
            logger.info(
                f"Best match: {best['title']} - {best['artist']} "
                f"(score: {best['score']}%, source: {best['source']})"
            )
            return best
        else:
            logger.warning(
                f"Best match score too low: {best['score']}% < {min_confidence}% threshold"
            )
            return None

    def fetch_metadata(self, title: str, artist: str,
                      duration: Optional[int] = None,
                      min_confidence: float = 70.0) -> Optional[Dict]:
        """
        One-shot fetch: Search and return best match

        Args:
            title: Song title
            artist: Artist name
            duration: Duration in seconds (optional)
            min_confidence: Minimum confidence to accept

        Returns:
            Best match metadata or None
        """
        results = self.search_by_title_artist(title, artist, duration)
        return self.get_best_match(results, min_confidence)
