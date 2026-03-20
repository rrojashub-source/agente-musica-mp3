"""
Content Classifier - AI-powered music content classification
Part of NEXUS Music Manager Phase 8

Classifies music into categories:
- EXPLICIT: Adult content, profanity, explicit themes
- CHILDREN: Content specifically for children
- CHRISTIAN: Religious/worship music
- CLEAN: Generally safe for all audiences
- UNKNOWN: Unable to classify with confidence

Multi-tier classification system:
- Tier 1: Metadata analysis (instant, offline)
- Tier 2: Lyrics analysis (online, deep)
- Tier 3: Audio analysis (offline, advanced)

Created: December 8, 2025
"""

import json
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.mutagen_compat import MutagenFile

from utils.resource_path import get_resource_path

logger = logging.getLogger(__name__)


class ContentRating(Enum):
    """Content rating categories"""

    EXPLICIT = "explicit"
    SUGGESTIVE = "suggestive"
    CLEAN = "clean"
    CHILDREN = "children"
    CHRISTIAN = "christian"
    UNKNOWN = "unknown"


@dataclass
class ContentScore:
    """Multi-dimensional content score"""

    # Rating decision thresholds (used by the .rating property)
    THRESHOLD_CHILDREN: float = 0.8
    THRESHOLD_CHRISTIAN: float = 0.8
    THRESHOLD_EXPLICIT: float = 0.7
    THRESHOLD_SUGGESTIVE: float = 0.4
    THRESHOLD_CLEAN: float = 0.7

    # Confidence threshold — below this, deeper analysis tiers activate
    CONFIDENCE_SUFFICIENT: float = 0.85

    # Primary scores (0.0 to 1.0)
    explicit_score: float = 0.0
    children_score: float = 0.0
    christian_score: float = 0.0
    clean_score: float = 0.0

    # Detailed dimensions
    profanity: float = 0.0
    violence: float = 0.0
    sexual_content: float = 0.0
    substance: float = 0.0
    positive_messages: float = 0.0

    # Metadata
    confidence: float = 0.0
    source: str = "unknown"  # 'metadata', 'lyrics', 'audio', 'combined'
    reasons: List[str] = field(default_factory=list)

    @property
    def rating(self) -> ContentRating:
        """Determine final rating based on scores"""
        if self.children_score >= self.THRESHOLD_CHILDREN:
            return ContentRating.CHILDREN
        if self.christian_score >= self.THRESHOLD_CHRISTIAN:
            return ContentRating.CHRISTIAN
        if self.explicit_score >= self.THRESHOLD_EXPLICIT:
            return ContentRating.EXPLICIT
        if self.explicit_score >= self.THRESHOLD_SUGGESTIVE:
            return ContentRating.SUGGESTIVE
        if self.clean_score >= self.THRESHOLD_CLEAN:
            return ContentRating.CLEAN
        return ContentRating.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "rating": self.rating.value,
            "explicit_score": self.explicit_score,
            "children_score": self.children_score,
            "christian_score": self.christian_score,
            "clean_score": self.clean_score,
            "profanity": self.profanity,
            "violence": self.violence,
            "sexual_content": self.sexual_content,
            "substance": self.substance,
            "positive_messages": self.positive_messages,
            "confidence": self.confidence,
            "source": self.source,
            "reasons": self.reasons,
        }


@dataclass
class ClassificationResult:
    """Complete classification result for a song"""

    file_path: str
    artist: str
    title: str
    rating: ContentRating
    score: ContentScore
    metadata_score: Optional[ContentScore] = None
    lyrics_score: Optional[ContentScore] = None
    audio_score: Optional[ContentScore] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": self.file_path,
            "artist": self.artist,
            "title": self.title,
            "rating": self.rating.value,
            "score": self.score.to_dict(),
            "metadata_score": self.metadata_score.to_dict() if self.metadata_score else None,
            "lyrics_score": self.lyrics_score.to_dict() if self.lyrics_score else None,
            "audio_score": self.audio_score.to_dict() if self.audio_score else None,
        }


class ContentClassifier:
    """
    Main content classifier orchestrating all tiers
    """

    # Tier combination weights (sum to 1.0 when all tiers are present)
    WEIGHT_METADATA: float = 0.4
    WEIGHT_LYRICS: float = 0.45
    WEIGHT_AUDIO: float = 0.15

    def __init__(self) -> None:
        self._load_artist_database()
        self._lyrics_analyzer: Any = None  # Lazy load
        self._audio_analyzer: Any = None  # Lazy load
        self._audio_analyzer_checked: bool = False  # Prevent repeated warnings
        self._lyrics_analyzer_checked: bool = False

    def _load_artist_database(self) -> None:
        """Load artist classification database"""
        db_path = get_resource_path("data/artist_database.json")

        try:
            with open(db_path, "r", encoding="utf-8") as f:
                self._db = json.load(f)

            # Build lookup dictionaries
            self._explicit_artists = self._db.get("explicit", {}).get("artists", {})
            self._children_artists = self._db.get("children", {}).get("artists", {})
            self._christian_artists = self._db.get("christian", {}).get("artists", {})
            self._clean_artists = self._db.get("clean", {}).get("artists", {})
            self._keywords = self._db.get("keywords", {})
            self._genres = self._db.get("genres", {})

            logger.info(
                f"Loaded artist database: {len(self._explicit_artists)} explicit, "
                f"{len(self._children_artists)} children, {len(self._christian_artists)} christian, "
                f"{len(self._clean_artists)} clean artists"
            )
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load artist database: {e}")
            self._db = {}
            self._explicit_artists = {}
            self._children_artists = {}
            self._christian_artists = {}
            self._clean_artists = {}
            self._keywords = {}
            self._genres = {}

    def classify_file(self, file_path: str, use_lyrics: bool = False, use_audio: bool = False) -> ClassificationResult:
        """
        Classify a single audio file

        Args:
            file_path: Path to audio file
            use_lyrics: Whether to use Tier 2 (lyrics analysis)
            use_audio: Whether to use Tier 3 (audio analysis)

        Returns:
            ClassificationResult with all scores
        """
        path = Path(file_path)

        # Extract metadata
        artist, title, genre = self._extract_metadata(path)

        # Tier 1: Metadata analysis (always)
        metadata_score = self._analyze_metadata(artist, title, genre, path.name)

        # Tier 2: Lyrics analysis (optional)
        lyrics_score = None
        if use_lyrics and metadata_score.confidence < ContentScore.CONFIDENCE_SUFFICIENT:
            lyrics_score = self._analyze_lyrics(artist, title)

        # Tier 3: Audio analysis (optional)
        audio_score = None
        if use_audio and (
            metadata_score.confidence < ContentScore.CONFIDENCE_SUFFICIENT
            or (lyrics_score and lyrics_score.confidence < ContentScore.CONFIDENCE_SUFFICIENT)
        ):
            audio_score = self._analyze_audio(file_path)

        # Combine scores
        final_score = self._combine_scores(metadata_score, lyrics_score, audio_score)

        return ClassificationResult(
            file_path=str(path),
            artist=artist,
            title=title,
            rating=final_score.rating,
            score=final_score,
            metadata_score=metadata_score,
            lyrics_score=lyrics_score,
            audio_score=audio_score,
        )

    def classify_batch(
        self, file_paths: List[str], use_lyrics: bool = False, use_audio: bool = False, progress_callback: Any = None
    ) -> List[ClassificationResult]:
        """
        Classify multiple files

        Args:
            file_paths: List of paths to audio files
            use_lyrics: Whether to use lyrics analysis
            use_audio: Whether to use audio analysis
            progress_callback: Optional callback(current, total, result)

        Returns:
            List of ClassificationResults
        """
        results = []
        total = len(file_paths)

        for i, path in enumerate(file_paths):
            try:
                result = self.classify_file(path, use_lyrics, use_audio)
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, total, result)

            except (OSError, ValueError, AttributeError) as e:
                logger.error(f"Error classifying {path}: {e}")
                # Create error result
                results.append(
                    ClassificationResult(
                        file_path=path,
                        artist="Unknown",
                        title=Path(path).stem,
                        rating=ContentRating.UNKNOWN,
                        score=ContentScore(confidence=0, source="error", reasons=[f"Error: {e}"]),
                    )
                )

        return results

    def _extract_metadata(self, path: Path) -> tuple:
        """Extract artist, title, genre from audio file"""
        artist = "Unknown"
        title = path.stem
        genre = ""

        try:
            audio = MutagenFile(path, easy=True)
            if audio:
                artist = audio.get("artist", ["Unknown"])[0]
                title = audio.get("title", [path.stem])[0]
                genre = audio.get("genre", [""])[0]
        except (OSError, ValueError, AttributeError) as e:
            logger.debug(f"Could not read metadata from {path}: {e}")
            # Try to parse from filename: "Artist - Title.mp3"
            name = path.stem
            if " - " in name:
                parts = name.split(" - ", 1)
                artist = parts[0].strip()
                title = parts[1].strip()

        return artist, title, genre

    def _analyze_metadata(self, artist: str, title: str, genre: str, filename: str) -> ContentScore:
        """
        Tier 1: Analyze metadata (artist, title, genre, filename)
        Fast, offline, ~70-95% accuracy for known artists
        """
        score = ContentScore(source="metadata")
        artist_lower = artist.lower().strip()
        title_lower = title.lower()
        filename_lower = filename.lower()
        genre_lower = genre.lower()

        # Check known artists
        if artist_lower in self._explicit_artists:
            prob = self._explicit_artists[artist_lower]
            score.explicit_score = max(score.explicit_score, prob)
            score.confidence = max(score.confidence, prob)
            score.reasons.append(f"Known explicit artist: {artist} ({prob:.0%})")

        if artist_lower in self._children_artists:
            prob = self._children_artists[artist_lower]
            score.children_score = max(score.children_score, prob)
            score.confidence = max(score.confidence, prob)
            score.reasons.append(f"Known children's artist: {artist} ({prob:.0%})")

        if artist_lower in self._christian_artists:
            prob = self._christian_artists[artist_lower]
            score.christian_score = max(score.christian_score, prob)
            score.confidence = max(score.confidence, prob)
            score.reasons.append(f"Known christian artist: {artist} ({prob:.0%})")

        if artist_lower in self._clean_artists:
            prob = self._clean_artists[artist_lower]
            score.clean_score = max(score.clean_score, prob)
            score.confidence = max(score.confidence, min(0.7, prob))
            score.reasons.append(f"Known clean artist: {artist} ({prob:.0%})")

        # Check title keywords
        explicit_keywords = self._keywords.get("explicit_title_keywords", [])
        for keyword in explicit_keywords:
            if keyword in title_lower or keyword in filename_lower:
                score.explicit_score = max(score.explicit_score, 0.8)
                score.profanity = max(score.profanity, 0.8)
                score.confidence = max(score.confidence, 0.75)
                score.reasons.append(f"Explicit keyword in title: '{keyword}'")
                break

        children_keywords = self._keywords.get("children_title_keywords", [])
        for keyword in children_keywords:
            if keyword in title_lower or keyword in filename_lower:
                score.children_score = max(score.children_score, 0.7)
                score.confidence = max(score.confidence, 0.65)
                score.reasons.append(f"Children's keyword in title: '{keyword}'")
                break

        christian_keywords = self._keywords.get("christian_title_keywords", [])
        for keyword in christian_keywords:
            if keyword in title_lower or keyword in filename_lower:
                score.christian_score = max(score.christian_score, 0.7)
                score.confidence = max(score.confidence, 0.65)
                score.reasons.append(f"Christian keyword in title: '{keyword}'")
                break

        # Check genre
        explicit_genres = self._genres.get("typically_explicit", [])
        for g in explicit_genres:
            if g in genre_lower:
                score.explicit_score = max(score.explicit_score, 0.4)
                score.confidence = max(score.confidence, 0.35)
                score.reasons.append(f"Genre often explicit: '{genre}'")
                break

        clean_genres = self._genres.get("typically_clean", [])
        for g in clean_genres:
            if g in genre_lower:
                score.clean_score = max(score.clean_score, 0.7)
                score.confidence = max(score.confidence, 0.6)
                score.reasons.append(f"Genre typically clean: '{genre}'")
                break

        christian_genres = self._genres.get("typically_christian", [])
        for g in christian_genres:
            if g in genre_lower:
                score.christian_score = max(score.christian_score, 0.8)
                score.confidence = max(score.confidence, 0.7)
                score.reasons.append(f"Genre is christian: '{genre}'")
                break

        # If no matches, assign base clean score
        if score.confidence == 0:
            score.clean_score = 0.5
            score.confidence = 0.3
            score.reasons.append("No specific indicators found")

        return score

    def _analyze_lyrics(self, artist: str, title: str) -> Optional[ContentScore]:
        """
        Tier 2: Analyze lyrics content
        Requires network, uses Genius/Musixmatch APIs
        """
        # Lazy load lyrics analyzer (only try once)
        if self._lyrics_analyzer is None and not self._lyrics_analyzer_checked:
            self._lyrics_analyzer_checked = True
            try:
                from .lyrics_analyzer import LyricsAnalyzer

                self._lyrics_analyzer = LyricsAnalyzer()
            except ImportError:
                logger.warning("Lyrics analyzer not available")
                return None

        if self._lyrics_analyzer is None:
            return None

        return self._lyrics_analyzer.analyze(artist, title)  # type: ignore[no-any-return]

    def _analyze_audio(self, file_path: str) -> Optional[ContentScore]:
        """
        Tier 3: Analyze audio features
        Requires librosa, offline analysis
        """
        # Lazy load audio analyzer (only try once)
        if self._audio_analyzer is None and not self._audio_analyzer_checked:
            self._audio_analyzer_checked = True
            try:
                from .audio_analyzer import AudioAnalyzer

                self._audio_analyzer = AudioAnalyzer()
            except ImportError:
                logger.warning("Audio analyzer not available (install librosa)")
                return None

        if self._audio_analyzer is None:
            return None

        return self._audio_analyzer.analyze(file_path)  # type: ignore[no-any-return]

    def _combine_scores(
        self, metadata: ContentScore, lyrics: Optional[ContentScore], audio: Optional[ContentScore]
    ) -> ContentScore:
        """Combine scores from all tiers with weighted averaging"""

        # If only metadata, return it
        if not lyrics and not audio:
            return metadata

        # Weights based on typical accuracy
        weights = {
            "metadata": self.WEIGHT_METADATA,
            "lyrics": self.WEIGHT_LYRICS,
            "audio": self.WEIGHT_AUDIO,
        }

        scores = [("metadata", metadata, weights["metadata"])]
        if lyrics:
            scores.append(("lyrics", lyrics, weights["lyrics"]))
        if audio:
            scores.append(("audio", audio, weights["audio"]))

        # Normalize weights
        total_weight = sum(w for _, _, w in scores)

        # Combine
        combined = ContentScore(source="combined")

        for name, score, weight in scores:
            norm_weight = weight / total_weight
            combined.explicit_score += score.explicit_score * norm_weight
            combined.children_score += score.children_score * norm_weight
            combined.christian_score += score.christian_score * norm_weight
            combined.clean_score += score.clean_score * norm_weight
            combined.profanity += score.profanity * norm_weight
            combined.violence += score.violence * norm_weight
            combined.sexual_content += score.sexual_content * norm_weight
            combined.substance += score.substance * norm_weight
            combined.positive_messages += score.positive_messages * norm_weight
            combined.confidence += score.confidence * norm_weight
            combined.reasons.extend([f"[{name}] {r}" for r in score.reasons])

        return combined

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        return {
            "explicit_artists": len(self._explicit_artists),
            "children_artists": len(self._children_artists),
            "christian_artists": len(self._christian_artists),
            "clean_artists": len(self._clean_artists),
            "explicit_keywords": len(self._keywords.get("explicit_title_keywords", [])),
            "children_keywords": len(self._keywords.get("children_title_keywords", [])),
            "christian_keywords": len(self._keywords.get("christian_title_keywords", [])),
        }


# Singleton instance (double-checked locking for thread safety)
_classifier_instance: Optional[ContentClassifier] = None
_classifier_lock: threading.Lock = threading.Lock()


def get_classifier() -> ContentClassifier:
    """Get or create classifier singleton (thread-safe)"""
    global _classifier_instance
    if _classifier_instance is None:
        with _classifier_lock:
            if _classifier_instance is None:
                _classifier_instance = ContentClassifier()
    return _classifier_instance
