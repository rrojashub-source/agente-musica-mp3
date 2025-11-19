"""
API Adapters - Bridge between existing API clients and MetadataFetcher

Purpose: Adapt MusicBrainzClient and SpotifySearcher to work with MetadataFetcher
Created: November 18, 2025
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class MusicBrainzAdapter:
    """
    Adapter for MusicBrainzClient to work with MetadataFetcher

    Converts MusicBrainzClient format to MetadataFetcher expected format
    """

    def __init__(self, musicbrainz_client):
        """
        Initialize adapter

        Args:
            musicbrainz_client: Instance of api.musicbrainz_client.MusicBrainzClient
        """
        self.client = musicbrainz_client
        logger.info("MusicBrainzAdapter initialized")

    def search_recordings(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search recordings and return in MetadataFetcher format

        Args:
            query: Search query (ignored, uses title+artist from client)
            limit: Maximum results

        Returns:
            List of dicts with MusicBrainz raw format expected by MetadataFetcher
        """
        # Extract title and artist from query
        # Query format: 'recording:"title" AND artist:"artist"'
        import re
        title_match = re.search(r'recording:"([^"]+)"', query)
        artist_match = re.search(r'artist:"([^"]+)"', query)

        if not title_match:
            logger.warning("Could not extract title from query")
            return []

        title = title_match.group(1)
        artist = artist_match.group(1) if artist_match else None

        # Use existing MusicBrainzClient
        results = self.client.search_recording(title, artist=artist, limit=limit)

        if not results:
            return []

        # Convert to MetadataFetcher expected format
        adapted_results = []
        for result in results:
            # Build structure expected by MetadataFetcher
            adapted = {
                'title': result.get('title', ''),
                'artist-credit': [
                    {
                        'name': result.get('artist', 'Unknown Artist'),
                        'artist': {
                            'name': result.get('artist', 'Unknown Artist')
                        }
                    }
                ],
                'releases': [
                    {
                        'title': result.get('album', 'Unknown Album'),
                        'date': f"{result.get('year', '')}-01-01" if result.get('year') else ''
                    }
                ],
                'length': 0  # Duration not available from current client
            }

            adapted_results.append(adapted)

        logger.info(f"Adapted {len(adapted_results)} MusicBrainz results")
        return adapted_results


class SpotifyAdapter:
    """
    Adapter for SpotifySearcher to work with MetadataFetcher

    Converts SpotifySearcher format to MetadataFetcher expected format
    """

    def __init__(self, spotify_searcher):
        """
        Initialize adapter

        Args:
            spotify_searcher: Instance of api.spotify_search.SpotifySearcher
        """
        self.searcher = spotify_searcher
        logger.info("SpotifyAdapter initialized")

    def search_tracks(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search tracks and return in MetadataFetcher format

        Args:
            query: Search query (format: "track:title artist:artist")
            limit: Maximum results

        Returns:
            List of dicts with Spotify format expected by MetadataFetcher
        """
        # Extract title and artist from query
        # Query format: "track:title artist:artist"
        import re
        track_match = re.search(r'track:([^\s]+(?:\s+[^\s]+)*?)(?:\s+artist:|$)', query)
        artist_match = re.search(r'artist:(.+)', query)

        if not track_match:
            logger.warning("Could not extract track from query")
            return []

        title = track_match.group(1).strip()
        artist = artist_match.group(1).strip() if artist_match else ""

        # Build Spotify query
        spotify_query = f"{title} {artist}".strip()

        # Use existing SpotifySearcher
        try:
            results = self.searcher.search_tracks(spotify_query, limit=limit)

            if not results:
                return []

            # Results from SpotifySearcher are already in correct format
            # Just ensure they have the expected structure
            adapted_results = []
            for track in results:
                adapted = {
                    'name': track.get('title', ''),
                    'artists': [
                        {'name': track.get('artist', 'Unknown Artist')}
                    ],
                    'album': {
                        'name': track.get('album', 'Unknown Album'),
                        'release_date': track.get('year', '')
                    },
                    'duration_ms': track.get('duration', 0) * 1000  # Convert seconds to ms
                }

                adapted_results.append(adapted)

            logger.info(f"Adapted {len(adapted_results)} Spotify results")
            return adapted_results

        except Exception as e:
            logger.error(f"Spotify search error: {e}")
            return []
