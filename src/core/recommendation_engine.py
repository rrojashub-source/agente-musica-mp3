"""
Recommendation Engine - Similar Songs Suggestions

Provides song recommendations based on:
- Same artist (highest priority)
- Same album
- Same genre
- Similar decade/year

Created: November 23, 2025
"""

import logging
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Engine for recommending similar songs based on metadata.

    Uses a simple scoring system:
    - Same artist: +10 points
    - Same album: +5 points
    - Same genre: +3 points
    - Similar year (±5 years): +2 points
    """

    def __init__(self, db_manager: Any) -> None:
        """
        Initialize recommendation engine

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager: Any = db_manager
        logger.info("RecommendationEngine initialized")

    def get_recommendations(
        self, current_song: Dict[str, Any], limit: int = 10, exclude_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recommended songs similar to current song

        Args:
            current_song: Dict with song data (artist, album, genre, year)
            limit: Maximum number of recommendations
            exclude_ids: List of song IDs to exclude (e.g., already played)

        Returns:
            List of recommended song dicts sorted by relevance
        """
        if not current_song:
            return []

        exclude_ids = exclude_ids or []
        current_id = current_song.get("id")
        if current_id:
            exclude_ids.append(current_id)

        # Get all songs from database
        all_songs = self.db_manager.get_all_songs()

        if not all_songs:
            return []

        # Calculate scores for each song
        scored_songs = []

        current_artist = (current_song.get("artist") or "").lower().strip()
        current_album = (current_song.get("album") or "").lower().strip()
        current_genre = (current_song.get("genre") or "").lower().strip()
        current_year = current_song.get("year")

        for song in all_songs:
            song_id = song.get("id")

            # Skip excluded songs
            if song_id in exclude_ids:
                continue

            score = 0

            # Same artist (highest weight)
            song_artist = (song.get("artist") or "").lower().strip()
            if song_artist and song_artist == current_artist:
                score += 10

            # Same album
            song_album = (song.get("album") or "").lower().strip()
            if song_album and song_album == current_album:
                score += 5

            # Same genre
            song_genre = (song.get("genre") or "").lower().strip()
            if song_genre and song_genre == current_genre:
                score += 3

            # Similar year (within 5 years)
            song_year = song.get("year")
            if current_year and song_year:
                try:
                    year_diff = abs(int(current_year) - int(song_year))
                    if year_diff <= 5:
                        score += 2
                    elif year_diff <= 10:
                        score += 1
                except (ValueError, TypeError):
                    pass

            # Only include songs with some relevance
            if score > 0:
                scored_songs.append((score, song))

        # Sort by score (descending)
        scored_songs.sort(key=lambda x: x[0], reverse=True)

        # Get top recommendations
        recommendations = [song for score, song in scored_songs[:limit]]

        # Add some randomization to avoid always showing same songs
        if len(recommendations) > 3:
            # Keep top 3, shuffle the rest
            top_3 = recommendations[:3]
            rest = recommendations[3:]
            random.shuffle(rest)
            recommendations = top_3 + rest

        logger.info(
            f"Generated {len(recommendations)} recommendations for "
            f"'{current_song.get('title')}' by {current_artist}"
        )

        return recommendations

    def get_random_from_genre(self, genre: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get random songs from a specific genre

        Args:
            genre: Genre to search for
            limit: Maximum number of songs

        Returns:
            List of song dicts
        """
        if not genre:
            return []

        all_songs = self.db_manager.get_all_songs()
        genre_lower = genre.lower().strip()

        matching = [song for song in all_songs if (song.get("genre") or "").lower().strip() == genre_lower]

        random.shuffle(matching)
        return matching[:limit]

    def get_random_from_artist(self, artist: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get random songs from a specific artist

        Args:
            artist: Artist name
            limit: Maximum number of songs

        Returns:
            List of song dicts
        """
        if not artist:
            return []

        all_songs = self.db_manager.get_all_songs()
        artist_lower = artist.lower().strip()

        matching = [song for song in all_songs if (song.get("artist") or "").lower().strip() == artist_lower]

        random.shuffle(matching)
        return matching[:limit]

    def get_discover_playlist(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Generate a "Discover" playlist with varied songs

        Tries to include songs from different artists and genres
        for variety.

        Args:
            limit: Maximum number of songs

        Returns:
            List of varied song dicts
        """
        all_songs = self.db_manager.get_all_songs()

        if not all_songs:
            return []

        # Group by genre
        by_genre: dict[str, list[dict[str, Any]]] = {}
        for song in all_songs:
            genre = (song.get("genre") or "Unknown").lower().strip()
            if genre not in by_genre:
                by_genre[genre] = []
            by_genre[genre].append(song)

        # Pick songs from each genre proportionally
        discover = []
        genres = list(by_genre.keys())
        random.shuffle(genres)

        per_genre = max(1, limit // len(genres)) if genres else 0

        for genre in genres:
            genre_songs = by_genre[genre]
            random.shuffle(genre_songs)
            discover.extend(genre_songs[:per_genre])

            if len(discover) >= limit:
                break

        # Shuffle final list
        random.shuffle(discover)
        return discover[:limit]
