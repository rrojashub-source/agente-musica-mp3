"""
Tests for Content Filter - Phase 8 AI Content Classification

Tests the ContentClassifier, ArtistDatabase, and classification logic.
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.content_filter import (
    ContentClassifier,
    ContentRating,
    ContentScore,
    ClassificationResult,
    get_classifier,
)


class TestContentRating:
    """Test ContentRating enum"""

    def test_rating_values(self):
        """Test all rating values exist"""
        assert ContentRating.EXPLICIT.value == "explicit"
        assert ContentRating.SUGGESTIVE.value == "suggestive"
        assert ContentRating.CLEAN.value == "clean"
        assert ContentRating.CHILDREN.value == "children"
        assert ContentRating.CHRISTIAN.value == "christian"
        assert ContentRating.UNKNOWN.value == "unknown"

    def test_rating_count(self):
        """Test all ratings are defined"""
        assert len(ContentRating) == 6


class TestContentScore:
    """Test ContentScore dataclass"""

    def test_default_score(self):
        """Test default score values"""
        score = ContentScore()
        assert score.explicit_score == 0.0
        assert score.children_score == 0.0
        assert score.clean_score == 0.0
        assert score.confidence == 0.0
        assert score.source == "unknown"
        assert score.reasons == []

    def test_explicit_rating(self):
        """Test explicit score triggers EXPLICIT rating"""
        score = ContentScore(explicit_score=0.8, confidence=0.8)
        assert score.rating == ContentRating.EXPLICIT

    def test_children_rating(self):
        """Test children score triggers CHILDREN rating"""
        score = ContentScore(children_score=0.9, confidence=0.9)
        assert score.rating == ContentRating.CHILDREN

    def test_christian_rating(self):
        """Test christian score triggers CHRISTIAN rating"""
        score = ContentScore(christian_score=0.85, confidence=0.85)
        assert score.rating == ContentRating.CHRISTIAN

    def test_clean_rating(self):
        """Test clean score triggers CLEAN rating"""
        score = ContentScore(clean_score=0.8, confidence=0.7)
        assert score.rating == ContentRating.CLEAN

    def test_suggestive_rating(self):
        """Test medium explicit score triggers SUGGESTIVE rating"""
        score = ContentScore(explicit_score=0.5, confidence=0.5)
        assert score.rating == ContentRating.SUGGESTIVE

    def test_unknown_rating(self):
        """Test low scores give UNKNOWN rating"""
        score = ContentScore(clean_score=0.3, confidence=0.2)
        assert score.rating == ContentRating.UNKNOWN

    def test_to_dict(self):
        """Test serialization to dictionary"""
        score = ContentScore(
            explicit_score=0.5,
            children_score=0.0,
            clean_score=0.5,
            confidence=0.6,
            source="metadata",
            reasons=["test reason"],
        )
        result = score.to_dict()
        assert result["explicit_score"] == 0.5
        assert result["source"] == "metadata"
        assert "test reason" in result["reasons"]


class TestContentClassifier:
    """Test ContentClassifier class"""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance"""
        return ContentClassifier()

    def test_singleton(self):
        """Test get_classifier returns same instance"""
        c1 = get_classifier()
        c2 = get_classifier()
        assert c1 is c2

    def test_artist_database_loaded(self, classifier):
        """Test artist database is loaded"""
        stats = classifier.get_stats()
        assert stats["explicit_artists"] > 0
        assert stats["children_artists"] > 0
        assert stats["christian_artists"] > 0
        assert stats["clean_artists"] > 0

    def test_database_stats(self, classifier):
        """Test database statistics"""
        stats = classifier.get_stats()
        # Based on our database
        assert stats["explicit_artists"] >= 90  # ~99 artists
        assert stats["children_artists"] >= 50  # ~54 artists
        assert stats["christian_artists"] >= 50  # ~54 artists
        assert stats["clean_artists"] >= 70  # ~72 artists

    def test_explicit_artist_detection(self, classifier):
        """Test detection of known explicit artist"""
        score = classifier._analyze_metadata(
            artist="Bad Bunny", title="Titi Me Pregunto", genre="Reggaeton", filename="bad_bunny_song.mp3"
        )
        assert score.explicit_score >= 0.9
        assert score.rating == ContentRating.EXPLICIT
        assert "Bad Bunny" in str(score.reasons)

    def test_children_artist_detection(self, classifier):
        """Test detection of known children's artist"""
        score = classifier._analyze_metadata(
            artist="Plim Plim", title="La Cancion del ABC", genre="Infantil", filename="plim_plim.mp3"
        )
        assert score.children_score >= 0.9
        assert score.rating == ContentRating.CHILDREN
        assert "Plim Plim" in str(score.reasons)

    def test_christian_artist_detection(self, classifier):
        """Test detection of known christian artist"""
        score = classifier._analyze_metadata(
            artist="Hillsong", title="What A Beautiful Name", genre="Worship", filename="hillsong.mp3"
        )
        assert score.christian_score >= 0.9
        assert score.rating == ContentRating.CHRISTIAN

    def test_clean_artist_detection(self, classifier):
        """Test detection of known clean artist"""
        score = classifier._analyze_metadata(
            artist="Coldplay", title="Yellow", genre="Alternative Rock", filename="coldplay.mp3"
        )
        assert score.clean_score >= 0.8
        assert score.rating == ContentRating.CLEAN

    def test_explicit_keyword_detection(self, classifier):
        """Test detection of explicit keywords in title"""
        score = classifier._analyze_metadata(
            artist="Unknown Artist", title="Song With Fuck Word", genre="", filename="explicit_song.mp3"
        )
        assert score.explicit_score >= 0.7
        assert "Explicit keyword" in str(score.reasons)

    def test_children_keyword_detection(self, classifier):
        """Test detection of children keywords in title"""
        score = classifier._analyze_metadata(
            artist="Unknown", title="Nursery Rhyme for Kids", genre="", filename="kids_song.mp3"
        )
        assert score.children_score >= 0.5

    def test_genre_detection(self, classifier):
        """Test genre-based classification hints"""
        # Trap genre typically explicit
        score1 = classifier._analyze_metadata(artist="Unknown", title="Song", genre="Trap", filename="song.mp3")
        assert score1.explicit_score >= 0.3

        # Classical genre typically clean
        score2 = classifier._analyze_metadata(
            artist="Unknown", title="Symphony", genre="Classical", filename="symphony.mp3"
        )
        assert score2.clean_score >= 0.5

    def test_unknown_artist(self, classifier):
        """Test handling of unknown artist"""
        score = classifier._analyze_metadata(
            artist="Unknown Artist XYZ", title="Random Song Title", genre="Pop", filename="random.mp3"
        )
        # Should get low confidence
        assert score.confidence <= 0.5
        assert "No specific indicators" in str(score.reasons)

    def test_case_insensitive(self, classifier):
        """Test artist detection is case insensitive"""
        score1 = classifier._analyze_metadata(artist="BAD BUNNY", title="Song", genre="", filename="song.mp3")
        score2 = classifier._analyze_metadata(artist="bad bunny", title="Song", genre="", filename="song.mp3")
        assert score1.explicit_score == score2.explicit_score


class TestClassificationResult:
    """Test ClassificationResult dataclass"""

    def test_result_creation(self):
        """Test creating classification result"""
        score = ContentScore(explicit_score=0.8, confidence=0.8)
        result = ClassificationResult(
            file_path="/path/to/song.mp3",
            artist="Test Artist",
            title="Test Song",
            rating=ContentRating.EXPLICIT,
            score=score,
        )
        assert result.artist == "Test Artist"
        assert result.title == "Test Song"
        assert result.rating == ContentRating.EXPLICIT

    def test_result_to_dict(self):
        """Test result serialization"""
        score = ContentScore(explicit_score=0.8, confidence=0.8)
        result = ClassificationResult(
            file_path="/path/to/song.mp3",
            artist="Test Artist",
            title="Test Song",
            rating=ContentRating.EXPLICIT,
            score=score,
        )
        data = result.to_dict()
        assert data["artist"] == "Test Artist"
        assert data["rating"] == "explicit"
        assert "score" in data


class TestLyricsAnalyzer:
    """Test LyricsAnalyzer - may skip if dependencies missing"""

    def test_lyrics_analyzer_import(self):
        """Test LyricsAnalyzer can be imported"""
        try:
            from services.content_filter.lyrics_analyzer import LyricsAnalyzer

            assert LyricsAnalyzer is not None
        except ImportError:
            pytest.skip("lyricsgenius not installed")

    def test_profanity_lists(self):
        """Test profanity word lists are defined"""
        from services.content_filter.lyrics_analyzer import PROFANITY_ES, PROFANITY_EN, VIOLENCE_KEYWORDS, DRUG_KEYWORDS

        assert len(PROFANITY_ES) > 0
        assert len(PROFANITY_EN) > 0
        assert len(VIOLENCE_KEYWORDS) > 0
        assert len(DRUG_KEYWORDS) > 0

    def test_analyze_explicit_text(self):
        """Test analysis of text with explicit content"""
        try:
            from services.content_filter.lyrics_analyzer import LyricsAnalyzer

            analyzer = LyricsAnalyzer()
            # Test with sample explicit lyrics
            score = analyzer.analyze_text("Fuck this shit bitch damn")
            assert score.profanity > 0.5
            assert score.explicit_score > 0.3
        except ImportError:
            pytest.skip("lyricsgenius not installed")

    def test_analyze_clean_text(self):
        """Test analysis of clean text"""
        try:
            from services.content_filter.lyrics_analyzer import LyricsAnalyzer

            analyzer = LyricsAnalyzer()
            score = analyzer.analyze_text(
                "I love you, you love me, we are happy family. Peace and joy and happiness forever."
            )
            assert score.profanity == 0
            assert score.positive_messages > 0.3
        except ImportError:
            pytest.skip("lyricsgenius not installed")


class TestAudioAnalyzer:
    """Test AudioAnalyzer - may skip if librosa not installed"""

    def test_audio_analyzer_import(self):
        """Test AudioAnalyzer can be imported"""
        try:
            from services.content_filter.audio_analyzer import AudioAnalyzer, LIBROSA_AVAILABLE

            assert AudioAnalyzer is not None
            # If librosa not available, should still import
        except ImportError:
            pytest.skip("Audio analyzer import failed")

    def test_librosa_flag(self):
        """Test LIBROSA_AVAILABLE flag is set correctly"""
        from services.content_filter.audio_analyzer import LIBROSA_AVAILABLE

        # Flag should be boolean
        assert isinstance(LIBROSA_AVAILABLE, bool)


class TestIntegration:
    """Integration tests for Content Filter"""

    def test_full_classification_workflow(self):
        """Test complete classification workflow with mock data"""
        classifier = get_classifier()

        # Simulate classifying metadata only (no real file)
        score = classifier._analyze_metadata(
            artist="Anuel AA", title="China", genre="Reggaeton", filename="anuel_china.mp3"
        )

        # Create mock result
        result = ClassificationResult(
            file_path="/fake/path/anuel_china.mp3",
            artist="Anuel AA",
            title="China",
            rating=score.rating,
            score=score,
        )

        assert result.rating == ContentRating.EXPLICIT
        assert result.score.explicit_score >= 0.9
        assert result.score.confidence >= 0.8

    def test_batch_classification_mock(self):
        """Test batch classification with mock callback"""
        classifier = get_classifier()
        results = []

        def callback(current, total, result):
            results.append((current, total, result.rating))

        # Would need real files - just test interface exists
        assert hasattr(classifier, "classify_batch")
        assert callable(classifier.classify_batch)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
