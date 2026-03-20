"""
Smart Playlist Engine - Phase 5
Automatically generates playlists based on dynamic rules and criteria

Features:
- Rule-based playlist generation
- Multiple rule types (genre, artist, year, play count, rating, etc.)
- AND/OR logic for combining rules
- Auto-refresh on library changes
- Built-in smart playlist templates
- Custom rule creation

Created: November 24, 2025
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RuleOperator(Enum):
    """Operators for rule conditions"""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    IN_LAST = "in_last"  # For date-based rules (e.g., "in last 30 days")
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class RuleField(Enum):
    """Available fields for rules"""

    TITLE = "title"
    ARTIST = "artist"
    ALBUM = "album"
    GENRE = "genre"
    YEAR = "year"
    RATING = "rating"
    PLAY_COUNT = "play_count"
    DATE_ADDED = "date_added"
    LAST_PLAYED = "last_played"
    DURATION = "duration"
    BPM = "bpm"
    PATH = "path"


class CombineMode(Enum):
    """How to combine multiple rules"""

    ALL = "all"  # AND - all rules must match
    ANY = "any"  # OR - any rule must match


@dataclass
class PlaylistRule:
    """A single rule for smart playlist matching"""

    field: str  # RuleField value
    operator: str  # RuleOperator value
    value: Any  # Value to compare against
    value2: Optional[Any] = None  # Second value for BETWEEN operator

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PlaylistRule:
        """Create from dictionary"""
        return cls(**data)


@dataclass
class SmartPlaylistConfig:
    """Configuration for a smart playlist"""

    name: str
    rules: List[PlaylistRule] = field(default_factory=list)
    combine_mode: str = CombineMode.ALL.value
    limit: int = 0  # 0 = no limit
    sort_by: str = "title"
    sort_ascending: bool = True
    auto_refresh: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "rules": [r.to_dict() for r in self.rules],
            "combine_mode": self.combine_mode,
            "limit": self.limit,
            "sort_by": self.sort_by,
            "sort_ascending": self.sort_ascending,
            "auto_refresh": self.auto_refresh,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SmartPlaylistConfig:
        """Create from dictionary"""
        rules = [PlaylistRule.from_dict(r) for r in data.get("rules", [])]
        return cls(
            name=data["name"],
            rules=rules,
            combine_mode=data.get("combine_mode", CombineMode.ALL.value),
            limit=data.get("limit", 0),
            sort_by=data.get("sort_by", "title"),
            sort_ascending=data.get("sort_ascending", True),
            auto_refresh=data.get("auto_refresh", True),
            description=data.get("description", ""),
        )


class SmartPlaylistEngine:
    """
    Engine for creating and managing smart playlists

    Usage:
        engine = SmartPlaylistEngine(library_db)

        # Create a smart playlist
        config = SmartPlaylistConfig(
            name="Rock Classics",
            rules=[
                PlaylistRule("genre", "contains", "rock"),
                PlaylistRule("year", "between", 1970, 1989)
            ],
            combine_mode="all"
        )

        # Get matching songs
        songs = engine.generate_playlist(config)

        # Use built-in templates
        recently_added = engine.get_recently_added(days=30)
        most_played = engine.get_most_played(limit=50)
    """

    def __init__(self, library_db: Any = None) -> None:
        """
        Initialize smart playlist engine

        Args:
            library_db: Database connection for querying library
        """
        self.library_db: Any = library_db
        self._playlists: Dict[str, SmartPlaylistConfig] = {}
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("SmartPlaylistEngine initialized")

    def set_library_db(self, library_db: Any) -> None:
        """Set or update library database connection"""
        self.library_db = library_db
        self._cache.clear()  # Invalidate cache

    # ==========================================
    # Playlist Management
    # ==========================================

    def create_playlist(self, config: SmartPlaylistConfig) -> bool:
        """
        Create a new smart playlist

        Args:
            config: Playlist configuration

        Returns:
            True if created successfully
        """
        if config.name in self._playlists:
            logger.warning(f"Playlist '{config.name}' already exists")
            return False

        self._playlists[config.name] = config
        logger.info(f"Created smart playlist: {config.name}")
        return True

    def update_playlist(self, name: str, config: SmartPlaylistConfig) -> bool:
        """Update an existing playlist"""
        if name not in self._playlists:
            logger.warning(f"Playlist '{name}' not found")
            return False

        # If name changed, remove old entry
        if config.name != name:
            del self._playlists[name]

        self._playlists[config.name] = config
        self._cache.pop(name, None)
        logger.info(f"Updated smart playlist: {config.name}")
        return True

    def delete_playlist(self, name: str) -> bool:
        """Delete a smart playlist"""
        if name not in self._playlists:
            return False

        del self._playlists[name]
        self._cache.pop(name, None)
        logger.info(f"Deleted smart playlist: {name}")
        return True

    def get_playlist(self, name: str) -> Optional[SmartPlaylistConfig]:
        """Get playlist configuration by name"""
        return self._playlists.get(name)

    def list_playlists(self) -> List[str]:
        """List all smart playlist names"""
        return list(self._playlists.keys())

    # ==========================================
    # Playlist Generation
    # ==========================================

    def generate_playlist(self, config: SmartPlaylistConfig, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Generate playlist by applying rules to library

        Args:
            config: Playlist configuration
            use_cache: Use cached results if available

        Returns:
            List of matching songs (dictionaries with song metadata)
        """
        if not self.library_db:
            logger.error("No library database connected")
            return []

        # Check cache
        if use_cache and config.name in self._cache:
            logger.debug(f"Using cached results for '{config.name}'")
            return self._cache[config.name]

        # Get all songs from library
        all_songs = self._get_all_songs()

        if not all_songs:
            logger.warning("No songs in library")
            return []

        # Apply rules
        matching_songs = self._apply_rules(all_songs, config.rules, config.combine_mode)

        # Sort results
        matching_songs = self._sort_songs(matching_songs, config.sort_by, config.sort_ascending)

        # Apply limit
        if config.limit > 0:
            matching_songs = matching_songs[: config.limit]

        # Cache results
        if config.name:
            self._cache[config.name] = matching_songs

        logger.info(f"Generated '{config.name}': {len(matching_songs)} songs")
        return matching_songs

    def refresh_playlist(self, name: str) -> List[Dict[str, Any]]:
        """Refresh a playlist (regenerate, ignoring cache)"""
        config = self._playlists.get(name)
        if not config:
            return []

        self._cache.pop(name, None)
        return self.generate_playlist(config, use_cache=False)

    def refresh_all(self) -> None:
        """Refresh all playlists"""
        self._cache.clear()
        for name in self._playlists:
            self.generate_playlist(self._playlists[name], use_cache=False)

    # ==========================================
    # Built-in Smart Playlists
    # ==========================================

    def get_recently_added(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recently added songs

        Args:
            days: Number of days to look back
            limit: Maximum songs to return
        """
        config = SmartPlaylistConfig(
            name="_recently_added",
            rules=[PlaylistRule(field=RuleField.DATE_ADDED.value, operator=RuleOperator.IN_LAST.value, value=days)],
            combine_mode=CombineMode.ALL.value,
            limit=limit,
            sort_by="date_added",
            sort_ascending=False,
            description=f"Songs added in the last {days} days",
        )
        return self.generate_playlist(config, use_cache=False)

    def get_recently_played(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently played songs"""
        config = SmartPlaylistConfig(
            name="_recently_played",
            rules=[PlaylistRule(field=RuleField.LAST_PLAYED.value, operator=RuleOperator.IN_LAST.value, value=days)],
            combine_mode=CombineMode.ALL.value,
            limit=limit,
            sort_by="last_played",
            sort_ascending=False,
            description=f"Songs played in the last {days} days",
        )
        return self.generate_playlist(config, use_cache=False)

    def get_most_played(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most played songs"""
        config = SmartPlaylistConfig(
            name="_most_played",
            rules=[PlaylistRule(field=RuleField.PLAY_COUNT.value, operator=RuleOperator.GREATER_THAN.value, value=0)],
            combine_mode=CombineMode.ALL.value,
            limit=limit,
            sort_by="play_count",
            sort_ascending=False,
            description="Most frequently played songs",
        )
        return self.generate_playlist(config, use_cache=False)

    def get_never_played(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get songs that have never been played"""
        config = SmartPlaylistConfig(
            name="_never_played",
            rules=[PlaylistRule(field=RuleField.PLAY_COUNT.value, operator=RuleOperator.EQUALS.value, value=0)],
            combine_mode=CombineMode.ALL.value,
            limit=limit,
            sort_by="date_added",
            sort_ascending=False,
            description="Songs you haven't listened to yet",
        )
        return self.generate_playlist(config, use_cache=False)

    def get_by_genre(self, genre: str, limit: int = 0) -> List[Dict[str, Any]]:
        """Get songs by genre"""
        config = SmartPlaylistConfig(
            name=f"_genre_{genre}",
            rules=[PlaylistRule(field=RuleField.GENRE.value, operator=RuleOperator.CONTAINS.value, value=genre)],
            combine_mode=CombineMode.ALL.value,
            limit=limit,
            sort_by="artist",
            sort_ascending=True,
            description=f"All {genre} songs",
        )
        return self.generate_playlist(config, use_cache=False)

    def get_by_artist(self, artist: str, limit: int = 0) -> List[Dict[str, Any]]:
        """Get songs by artist"""
        config = SmartPlaylistConfig(
            name=f"_artist_{artist}",
            rules=[PlaylistRule(field=RuleField.ARTIST.value, operator=RuleOperator.CONTAINS.value, value=artist)],
            combine_mode=CombineMode.ALL.value,
            limit=limit,
            sort_by="album",
            sort_ascending=True,
            description=f"All songs by {artist}",
        )
        return self.generate_playlist(config, use_cache=False)

    def get_by_decade(self, decade: int, limit: int = 0) -> List[Dict[str, Any]]:
        """Get songs from a specific decade (e.g., 1980 for 80s)"""
        config = SmartPlaylistConfig(
            name=f"_decade_{decade}s",
            rules=[
                PlaylistRule(
                    field=RuleField.YEAR.value, operator=RuleOperator.BETWEEN.value, value=decade, value2=decade + 9
                )
            ],
            combine_mode=CombineMode.ALL.value,
            limit=limit,
            sort_by="year",
            sort_ascending=True,
            description=f"Songs from the {decade}s",
        )
        return self.generate_playlist(config, use_cache=False)

    def get_top_rated(self, min_rating: int = 4, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top rated songs"""
        config = SmartPlaylistConfig(
            name="_top_rated",
            rules=[
                PlaylistRule(
                    field=RuleField.RATING.value, operator=RuleOperator.GREATER_THAN.value, value=min_rating - 1
                )
            ],
            combine_mode=CombineMode.ALL.value,
            limit=limit,
            sort_by="rating",
            sort_ascending=False,
            description=f"Songs rated {min_rating}+ stars",
        )
        return self.generate_playlist(config, use_cache=False)

    # ==========================================
    # Internal Methods
    # ==========================================

    def _get_all_songs(self) -> List[Dict[str, Any]]:
        """Get all songs from library database"""
        if not self.library_db:
            return []

        try:
            # Try different methods depending on library_db type
            if hasattr(self.library_db, "get_all_songs"):
                result: list[dict[str, Any]] = self.library_db.get_all_songs()
                return result  # type: ignore[no-any-return]
            elif hasattr(self.library_db, "search"):
                result2: list[dict[str, Any]] = self.library_db.search("")
                return result2  # type: ignore[no-any-return]
            elif hasattr(self.library_db, "execute"):
                # Direct SQLite connection
                cursor = self.library_db.execute("SELECT * FROM songs")
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                logger.error("Unknown library_db type")
                return []
        except (sqlite3.Error, AttributeError) as e:
            logger.error(f"Failed to get songs from library: {e}")
            return []

    def _apply_rules(
        self, songs: List[Dict[str, Any]], rules: List[PlaylistRule], combine_mode: str
    ) -> List[Dict[str, Any]]:
        """Apply rules to filter songs"""
        if not rules:
            return songs

        matching = []

        for song in songs:
            rule_results = [self._evaluate_rule(song, rule) for rule in rules]

            if combine_mode == CombineMode.ALL.value:
                # All rules must match (AND)
                if all(rule_results):
                    matching.append(song)
            else:
                # Any rule must match (OR)
                if any(rule_results):
                    matching.append(song)

        return matching

    def _evaluate_rule(self, song: Dict[str, Any], rule: PlaylistRule) -> bool:
        """Evaluate a single rule against a song"""
        field_value = song.get(rule.field)
        compare_value = rule.value
        operator = rule.operator

        # Handle None/missing values
        if field_value is None:
            if operator == RuleOperator.IS_EMPTY.value:
                return True
            elif operator == RuleOperator.IS_NOT_EMPTY.value:
                return False
            return False

        # String comparisons (case-insensitive)
        if isinstance(field_value, str):
            field_value = field_value.lower()
            if isinstance(compare_value, str):
                compare_value = compare_value.lower()

        try:
            if operator == RuleOperator.EQUALS.value:
                return bool(field_value == compare_value)  # type: ignore[no-any-return]

            elif operator == RuleOperator.NOT_EQUALS.value:
                return bool(field_value != compare_value)  # type: ignore[no-any-return]

            elif operator == RuleOperator.CONTAINS.value:
                return str(compare_value) in str(field_value)

            elif operator == RuleOperator.NOT_CONTAINS.value:
                return str(compare_value) not in str(field_value)

            elif operator == RuleOperator.STARTS_WITH.value:
                return str(field_value).startswith(str(compare_value))

            elif operator == RuleOperator.ENDS_WITH.value:
                return str(field_value).endswith(str(compare_value))

            elif operator == RuleOperator.GREATER_THAN.value:
                return float(field_value) > float(compare_value)

            elif operator == RuleOperator.LESS_THAN.value:
                return float(field_value) < float(compare_value)

            elif operator == RuleOperator.BETWEEN.value:
                val = float(field_value)
                return float(compare_value) <= val <= float(rule.value2 or 0)  # type: ignore[arg-type]

            elif operator == RuleOperator.IN_LAST.value:
                # Compare dates - value is number of days
                if isinstance(field_value, str):
                    try:
                        field_date = datetime.fromisoformat(field_value)
                    except ValueError:
                        return False
                elif isinstance(field_value, datetime):
                    field_date = field_value
                else:
                    return False

                cutoff = datetime.now() - timedelta(days=int(compare_value))
                return field_date >= cutoff

            elif operator == RuleOperator.IS_EMPTY.value:
                return not field_value

            elif operator == RuleOperator.IS_NOT_EMPTY.value:
                return bool(field_value)

        except (ValueError, TypeError) as e:
            logger.debug(f"Rule evaluation error: {e}")
            return False

        return False

    def _sort_songs(self, songs: List[Dict[str, Any]], sort_by: str, ascending: bool) -> List[Dict[str, Any]]:
        """Sort songs by field"""
        try:
            return sorted(songs, key=lambda s: (s.get(sort_by) is None, s.get(sort_by, "")), reverse=not ascending)
        except (TypeError, ValueError) as e:
            logger.warning(f"Sort failed: {e}")
            return songs

    # ==========================================
    # Persistence
    # ==========================================

    def save_to_json(self, filepath: str) -> bool:
        """Save all playlists to JSON file"""
        try:
            data = {"version": "1.0", "playlists": {name: config.to_dict() for name, config in self._playlists.items()}}

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self._playlists)} playlists to {filepath}")
            return True

        except (OSError, TypeError) as e:
            logger.error(f"Failed to save playlists: {e}")
            return False

    def load_from_json(self, filepath: str) -> bool:
        """Load playlists from JSON file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            playlists_data = data.get("playlists", {})
            self._playlists.clear()

            for name, config_data in playlists_data.items():
                self._playlists[name] = SmartPlaylistConfig.from_dict(config_data)

            logger.info(f"Loaded {len(self._playlists)} playlists from {filepath}")
            return True

        except FileNotFoundError:
            logger.info(f"Playlist file not found: {filepath}")
            return False
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to load playlists: {e}")
            return False


# ==========================================
# Convenience Functions
# ==========================================


def create_genre_playlist(genre: str) -> SmartPlaylistConfig:
    """Create a simple genre-based playlist config"""
    return SmartPlaylistConfig(
        name=f"{genre} Music",
        rules=[PlaylistRule(field=RuleField.GENRE.value, operator=RuleOperator.CONTAINS.value, value=genre)],
        description=f"All {genre} songs",
    )


def create_decade_playlist(decade: int) -> SmartPlaylistConfig:
    """Create a decade-based playlist config"""
    return SmartPlaylistConfig(
        name=f"The {decade}s",
        rules=[
            PlaylistRule(
                field=RuleField.YEAR.value, operator=RuleOperator.BETWEEN.value, value=decade, value2=decade + 9
            )
        ],
        description=f"Songs from {decade}-{decade + 9}",
    )


def create_artist_playlist(artist: str) -> SmartPlaylistConfig:
    """Create an artist-based playlist config"""
    return SmartPlaylistConfig(
        name=f"Best of {artist}",
        rules=[PlaylistRule(field=RuleField.ARTIST.value, operator=RuleOperator.CONTAINS.value, value=artist)],
        sort_by="play_count",
        sort_ascending=False,
        description=f"All songs by {artist}",
    )
