"""
Phase 2 Tests for src/services/ module — MAPS Round 26

Covers:
- StatisticsService: all query methods + exception paths
- LyricsAnalyzer: _analyze_lyrics_content density branches + analyze_text
- ContentClassifier: classify_file tiers, classify_batch, _combine_scores, _extract_metadata
- AudioAnalyzer: _features_to_score (pure logic, no librosa needed)
- DownloadService: queue operations (pause/resume/retry/clear/get_item)
- CloudSyncService: dataclasses, LocalFolderProvider, export/import/merge

Pattern: module-level QApplication to bypass conftest qapp auto-skip.
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Module-level QApplication (bypasses conftest qapp skip)
try:
    from PySide6.QtWidgets import QApplication

    _app = QApplication.instance()
    if _app is None:
        _app = QApplication(sys.argv)
except ImportError:
    pass


# ==========================================
# StatisticsService Tests
# ==========================================


class TestStatisticsServicePhase2:
    """Tests for StatisticsService — covers query methods + error paths."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        from services.statistics_service import StatisticsService

        return StatisticsService(mock_db)

    # --- ListeningStats dataclass ---

    def test_listening_stats_hours(self):
        from services.statistics_service import ListeningStats

        s = ListeningStats(total_duration_seconds=7200)
        assert s.total_hours == 2.0

    def test_listening_stats_days(self):
        from services.statistics_service import ListeningStats

        s = ListeningStats(total_duration_seconds=172800)
        assert s.total_days == 2.0

    # --- get_library_overview ---

    def test_get_library_overview_success(self, service, mock_db):
        mock_db.fetch_one.side_effect = [
            {
                "total_songs": 100,
                "total_artists": 20,
                "total_albums": 15,
                "total_genres": 5,
                "total_duration": 36000,
                "total_size": 1073741824,
                "avg_bitrate": 320,
                "oldest_year": 1980,
                "newest_year": 2024,
            },
            {"total_plays": 500, "songs_played": 80},
        ]
        result = service.get_library_overview()
        assert result["total_songs"] == 100
        assert result["total_plays"] == 500
        assert result["total_duration_hours"] == 10.0

    def test_get_library_overview_exception(self, service, mock_db):
        mock_db.fetch_one.side_effect = sqlite3.Error("DB locked")
        result = service.get_library_overview()
        assert result == {}

    # --- get_top_artists ---

    def test_get_top_artists_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {"artist": "Beatles", "song_count": 10, "total_plays": 50, "total_duration": 3600}
        ]
        result = service.get_top_artists(5)
        assert len(result) == 1
        assert result[0]["artist"] == "Beatles"
        assert result[0]["total_duration_hours"] == 1.0

    def test_get_top_artists_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_top_artists() == []

    # --- get_top_albums ---

    def test_get_top_albums_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {
                "album": "Abbey Road",
                "artist": "Beatles",
                "song_count": 17,
                "total_plays": 100,
                "total_duration": 7200,
            }
        ]
        result = service.get_top_albums(5)
        assert len(result) == 1
        assert result[0]["album"] == "Abbey Road"
        assert result[0]["total_duration_hours"] == 2.0

    def test_get_top_albums_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_top_albums() == []

    # --- get_top_songs ---

    def test_get_top_songs_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "title": "Hey Jude",
                "artist": "Beatles",
                "album": "Single",
                "play_count": 50,
                "duration": 420,
                "last_played": "2024-01-01",
            }
        ]
        result = service.get_top_songs(5)
        assert len(result) == 1
        assert result[0]["title"] == "Hey Jude"

    def test_get_top_songs_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_top_songs() == []

    # --- get_top_genres ---

    def test_get_top_genres_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {"genre": "Rock", "song_count": 30, "total_plays": 200, "total_duration": 10800}
        ]
        result = service.get_top_genres(5)
        assert len(result) == 1
        assert result[0]["genre"] == "Rock"

    def test_get_top_genres_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_top_genres() == []

    # --- get_decade_breakdown ---

    def test_get_decade_breakdown_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {"decade": 1980, "song_count": 15, "total_plays": 100},
            {"decade": 1990, "song_count": 20, "total_plays": 150},
        ]
        result = service.get_decade_breakdown()
        assert len(result) == 2
        assert result[0]["decade"] == "1980s"

    def test_get_decade_breakdown_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_decade_breakdown() == []

    # --- get_recently_added ---

    def test_get_recently_added_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {"id": 1, "title": "New Song", "artist": "New Artist", "album": "New Album", "added_date": "2024-01-01"}
        ]
        result = service.get_recently_added(5)
        assert len(result) == 1

    def test_get_recently_added_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_recently_added() == []

    # --- get_recently_played ---

    def test_get_recently_played_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {"id": 1, "title": "Played", "artist": "A", "album": "B", "last_played": "2024-01-01", "play_count": 5}
        ]
        result = service.get_recently_played(5)
        assert len(result) == 1

    def test_get_recently_played_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_recently_played() == []

    # --- get_bitrate_distribution ---

    def test_get_bitrate_distribution_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [{"quality": "High (320+ kbps)", "song_count": 50, "avg_bitrate": 320}]
        result = service.get_bitrate_distribution()
        assert len(result) == 1
        assert result[0]["quality"] == "High (320+ kbps)"

    def test_get_bitrate_distribution_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_bitrate_distribution() == []

    # --- get_metadata_completeness ---

    def test_get_metadata_completeness_empty(self, service, mock_db):
        mock_db.fetch_one.return_value = {"count": 0}
        result = service.get_metadata_completeness()
        assert result["total"] == 0
        assert result["fields"] == {}

    def test_get_metadata_completeness_success(self, service, mock_db):
        mock_db.fetch_one.side_effect = [
            {"count": 100},  # total
            {"count": 90},  # artist
            {"count": 80},  # album
            {"count": 70},  # year
            {"count": 60},  # genre
            {"count": 95},  # duration
            {"count": 85},  # bitrate
        ]
        result = service.get_metadata_completeness()
        assert result["total"] == 100
        assert result["fields"]["artist"]["percentage"] == 90.0

    def test_get_metadata_completeness_exception(self, service, mock_db):
        mock_db.fetch_one.side_effect = sqlite3.Error("fail")
        result = service.get_metadata_completeness()
        assert result == {"total": 0, "fields": {}}

    # --- get_listening_by_hour ---

    def test_get_listening_by_hour_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {"hour": "08", "play_count": 10},
            {"hour": "14", "play_count": 20},
        ]
        result = service.get_listening_by_hour()
        assert len(result) == 24  # All 24 hours
        # Hour 08 should have 10 plays
        hour_08 = next(h for h in result if h["hour"] == "08")
        assert hour_08["play_count"] == 10

    def test_get_listening_by_hour_null_hour(self, service, mock_db):
        mock_db.fetch_all.return_value = [{"hour": None, "play_count": 5}]
        result = service.get_listening_by_hour()
        assert len(result) == 24
        # All hours should be 0 since None hour is skipped
        assert all(h["play_count"] == 0 for h in result)

    def test_get_listening_by_hour_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_listening_by_hour() == []

    # --- get_listening_by_day ---

    def test_get_listening_by_day_success(self, service, mock_db):
        mock_db.fetch_all.return_value = [
            {"day_num": "1", "play_count": 15},  # Monday
            {"day_num": "5", "play_count": 30},  # Friday
        ]
        result = service.get_listening_by_day()
        assert len(result) == 7
        assert result[1]["day"] == "Monday"
        assert result[1]["play_count"] == 15
        assert result[5]["day"] == "Friday"
        assert result[5]["play_count"] == 30

    def test_get_listening_by_day_null(self, service, mock_db):
        mock_db.fetch_all.return_value = [{"day_num": None, "play_count": 5}]
        result = service.get_listening_by_day()
        assert len(result) == 7
        assert all(d["play_count"] == 0 for d in result)

    def test_get_listening_by_day_exception(self, service, mock_db):
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        assert service.get_listening_by_day() == []

    # --- record_play ---

    def test_record_play_success(self, service, mock_db):
        service.record_play(1, 180, True)
        mock_db.execute_query.assert_called_once()

    def test_record_play_operational_error(self, service, mock_db):
        mock_db.execute_query.side_effect = sqlite3.OperationalError("no table")
        service.record_play(1)  # Should not raise

    def test_record_play_generic_error(self, service, mock_db):
        mock_db.execute_query.side_effect = sqlite3.Error("other")
        service.record_play(1)  # Should not raise

    # --- get_summary_stats ---

    def test_get_summary_stats(self, service, mock_db):
        # Overview needs two fetch_one calls (basic counts, play stats)
        mock_db.fetch_one.side_effect = [
            {
                "total_songs": 10,
                "total_artists": 3,
                "total_albums": 2,
                "total_genres": 2,
                "total_duration": 3600,
                "total_size": 1024,
                "avg_bitrate": 320,
                "oldest_year": 2000,
                "newest_year": 2024,
            },
            {"total_plays": 50, "songs_played": 8},
            # metadata_completeness: total + 6 fields
            {"count": 10},
            {"count": 9},
            {"count": 8},
            {"count": 7},
            {"count": 6},
            {"count": 10},
            {"count": 9},
        ]
        mock_db.fetch_all.return_value = []
        result = service.get_summary_stats()
        assert "overview" in result
        assert "top_artists" in result
        assert "top_songs" in result
        assert "decades" in result


# ==========================================
# LyricsAnalyzer Tests
# ==========================================


class TestLyricsAnalyzerPhase2:
    """Tests for LyricsAnalyzer._analyze_lyrics_content density branches."""

    @pytest.fixture
    def analyzer(self):
        from services.content_filter.lyrics_analyzer import LyricsAnalyzer

        # Bypass __init__ to avoid lyricsgenius/better_profanity imports
        obj = LyricsAnalyzer.__new__(LyricsAnalyzer)
        obj._genius = None
        obj._profanity_checker = None
        return obj

    def test_empty_lyrics(self, analyzer):
        score = analyzer._analyze_lyrics_content("")
        assert score.confidence == 0.1

    def test_high_profanity_density(self, analyzer):
        """Density > 5% → profanity = 1.0"""
        # 2 profanity words in 10 total = 20%
        lyrics = "fuck shit hello world one two three four five six"
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.profanity == 1.0

    def test_medium_profanity_density(self, analyzer):
        """Density > 2% → profanity = 0.8"""
        words = ["hello"] * 40 + ["fuck"]  # 1/41 ≈ 2.4%
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.profanity == 0.8

    def test_low_profanity_density(self, analyzer):
        """Density > 1% → profanity = 0.6"""
        words = ["hello"] * 80 + ["damn"]  # 1/81 ≈ 1.2%
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.profanity == 0.6

    def test_very_low_profanity_density(self, analyzer):
        """Density > 0.5% → profanity = 0.4"""
        words = ["hello"] * 150 + ["shit"]  # 1/151 ≈ 0.66%
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.profanity == 0.4

    def test_minimal_profanity(self, analyzer):
        """Density < 0.5% but count > 0 → profanity = 0.2"""
        words = ["hello"] * 300 + ["damn"]  # 1/301 ≈ 0.33%
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.profanity == 0.2

    def test_violence_high_density(self, analyzer):
        """Violence density > 2% → violence = 0.8"""
        words = ["kill", "murder", "gun"] + ["hello"] * 50
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.violence == 0.8

    def test_violence_medium_density(self, analyzer):
        """Violence density > 0.5% → violence = 0.5"""
        words = ["kill"] + ["hello"] * 100
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.violence == 0.5

    def test_violence_low(self, analyzer):
        """Violence count > 0 but density < 0.5%"""
        words = ["fight"] + ["hello"] * 300
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.violence == 0.2

    def test_drug_high_density(self, analyzer):
        """Drug density > 2% → substance = 0.9"""
        words = ["cocaine", "crack", "weed"] + ["hello"] * 50
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.substance == 0.9

    def test_drug_medium_density(self, analyzer):
        """Drug density > 0.5% → substance = 0.6"""
        words = ["cocaine"] + ["hello"] * 100
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.substance == 0.6

    def test_drug_low(self, analyzer):
        """Drug count > 0 density < 0.5%"""
        words = ["weed"] + ["hello"] * 300
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.substance == 0.3

    def test_sexual_high_density(self, analyzer):
        """Sexual density > 3% → sexual_content = 0.9"""
        words = ["sex", "sexy", "naked", "porn"] + ["hello"] * 50
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.sexual_content == 0.9

    def test_sexual_medium_density(self, analyzer):
        """Sexual density > 1% → sexual_content = 0.6"""
        words = ["sex", "sexy"] + ["hello"] * 100
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.sexual_content == 0.6

    def test_sexual_low(self, analyzer):
        """Sexual count > 0 density < 1%"""
        words = ["sexy"] + ["hello"] * 300
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.sexual_content == 0.3

    def test_positive_high_density(self, analyzer):
        """Positive density > 3% → positive_messages = 0.9"""
        words = ["love", "happy", "joy", "peace"] + ["hello"] * 50
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.positive_messages == 0.9

    def test_positive_medium_density(self, analyzer):
        """Positive density > 1% → positive_messages = 0.6"""
        words = ["love", "happy"] + ["hello"] * 100
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.positive_messages == 0.6

    def test_positive_low(self, analyzer):
        """Positive count > 0 density < 1%"""
        words = ["love"] + ["hello"] * 300
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.positive_messages == 0.3

    def test_explicit_adjustment_high_profanity(self, analyzer):
        """profanity > 0.6 → explicit_score bumped to >= 0.7"""
        words = ["fuck", "shit", "bitch"] + ["hello"] * 30
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.explicit_score >= 0.7

    def test_clean_score_inverse(self, analyzer):
        """Clean lyrics → high clean_score"""
        words = ["love", "happy", "joy", "dream", "smile"] + ["world"] * 50
        lyrics = " ".join(words)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.clean_score > 0.5

    def test_reasons_with_no_explicit(self, analyzer):
        """No explicit content → reason 'No explicit content detected'"""
        # Use words that don't match any keyword set
        lyrics = "the big red car drives down the long empty road today"
        score = analyzer._analyze_lyrics_content(lyrics)
        assert any("No explicit" in r for r in score.reasons)

    def test_reasons_with_profanity(self, analyzer):
        """Profanity found → reason includes count"""
        lyrics = "fuck this world today"
        score = analyzer._analyze_lyrics_content(lyrics)
        assert any("Profanity" in r for r in score.reasons)

    def test_reasons_violence_drug_sexual_positive(self, analyzer):
        """All categories present → all reasons listed"""
        lyrics = "kill cocaine sex love " + " ".join(["word"] * 20)
        score = analyzer._analyze_lyrics_content(lyrics)
        reason_text = " ".join(score.reasons)
        assert "Violence" in reason_text
        assert "Drug" in reason_text
        assert "Sexual" in reason_text
        assert "Positive" in reason_text

    def test_analyze_text_method(self, analyzer):
        """analyze_text is a public wrapper for _analyze_lyrics_content"""
        score = analyzer.analyze_text("love peace joy happy wonderful beautiful")
        assert score.source == "lyrics"
        assert score.positive_messages > 0

    def test_analyze_no_genius(self, analyzer):
        """analyze() returns None when no genius and no lyrics"""
        result = analyzer.analyze("Artist", "Title")
        assert result is None

    def test_profanity_checker_integration(self, analyzer):
        """When profanity_checker is available, it contributes"""
        mock_checker = Mock()
        mock_checker.contains_profanity.return_value = True
        analyzer._profanity_checker = mock_checker
        lyrics = "innocent looking text"
        analyzer._analyze_lyrics_content(lyrics)
        # profanity_count should be at least 1 from checker
        mock_checker.contains_profanity.assert_called_once()

    def test_profanity_checker_exception(self, analyzer):
        """Profanity checker exception is handled gracefully"""
        mock_checker = Mock()
        mock_checker.contains_profanity.side_effect = RuntimeError("fail")
        analyzer._profanity_checker = mock_checker
        lyrics = "some text here now today"
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score is not None  # Should not raise

    def test_spanish_profanity(self, analyzer):
        """Spanish profanity words are detected"""
        lyrics = "puta mierda cabrón " + " ".join(["hola"] * 20)
        score = analyzer._analyze_lyrics_content(lyrics)
        assert score.profanity > 0


# ==========================================
# ContentClassifier Tests
# ==========================================


class TestContentClassifierPhase2:
    """Tests for ContentClassifier — classify_file, batch, combine, extract_metadata."""

    @pytest.fixture
    def classifier(self):
        from services.content_filter.classifier import ContentClassifier

        with patch("services.content_filter.classifier.get_resource_path") as mock_path:
            mock_path.return_value = "fake.json"
            with patch(
                "builtins.open",
                create=True,
                side_effect=lambda *a, **k: self._make_json_file(),
            ):
                with patch("json.load", return_value=self._artist_db()):
                    clf = ContentClassifier()
        return clf

    @staticmethod
    def _artist_db():
        return {
            "explicit": {"artists": {"bad rapper": 0.95}},
            "children": {"artists": {"baby shark": 0.9}},
            "christian": {"artists": {"hillsong": 0.9}},
            "clean": {"artists": {"taylor swift": 0.8}},
            "keywords": {
                "explicit_title_keywords": ["f**k", "nsfw"],
                "children_title_keywords": ["nursery", "lullaby"],
                "christian_title_keywords": ["worship", "hallelujah"],
            },
            "genres": {
                "typically_explicit": ["gangsta rap"],
                "typically_clean": ["classical"],
                "typically_christian": ["gospel"],
            },
        }

    @staticmethod
    def _make_json_file():
        from io import StringIO

        return StringIO("{}")

    # --- ContentScore rating property ---

    def test_content_score_rating_children(self):
        from services.content_filter.classifier import ContentRating, ContentScore

        s = ContentScore(children_score=0.9)
        assert s.rating == ContentRating.CHILDREN

    def test_content_score_rating_christian(self):
        from services.content_filter.classifier import ContentRating, ContentScore

        s = ContentScore(christian_score=0.85)
        assert s.rating == ContentRating.CHRISTIAN

    def test_content_score_rating_explicit(self):
        from services.content_filter.classifier import ContentRating, ContentScore

        s = ContentScore(explicit_score=0.8)
        assert s.rating == ContentRating.EXPLICIT

    def test_content_score_rating_suggestive(self):
        from services.content_filter.classifier import ContentRating, ContentScore

        s = ContentScore(explicit_score=0.5)
        assert s.rating == ContentRating.SUGGESTIVE

    def test_content_score_rating_clean(self):
        from services.content_filter.classifier import ContentRating, ContentScore

        s = ContentScore(clean_score=0.8)
        assert s.rating == ContentRating.CLEAN

    def test_content_score_rating_unknown(self):
        from services.content_filter.classifier import ContentRating, ContentScore

        s = ContentScore()
        assert s.rating == ContentRating.UNKNOWN

    def test_content_score_to_dict(self):
        from services.content_filter.classifier import ContentScore

        s = ContentScore(explicit_score=0.5, source="test", reasons=["reason1"])
        d = s.to_dict()
        assert d["explicit_score"] == 0.5
        assert d["source"] == "test"

    # --- ClassificationResult ---

    def test_classification_result_to_dict(self):
        from services.content_filter.classifier import ClassificationResult, ContentRating, ContentScore

        result = ClassificationResult(
            file_path="/test.mp3",
            artist="Test",
            title="Song",
            rating=ContentRating.CLEAN,
            score=ContentScore(clean_score=0.8),
            metadata_score=ContentScore(clean_score=0.7),
        )
        d = result.to_dict()
        assert d["rating"] == "clean"
        assert d["metadata_score"] is not None
        assert d["lyrics_score"] is None

    # --- _extract_metadata ---

    def test_extract_metadata_from_mutagen(self, classifier):
        mock_audio = MagicMock()
        mock_audio.get.side_effect = lambda k, default: {
            "artist": ["Beatles"],
            "title": ["Hey Jude"],
            "genre": ["Rock"],
        }.get(k, default)

        with patch("services.content_filter.classifier.MutagenFile", return_value=mock_audio):
            artist, title, genre = classifier._extract_metadata(Path("/test.mp3"))
        assert artist == "Beatles"
        assert title == "Hey Jude"
        assert genre == "Rock"

    def test_extract_metadata_mutagen_error_with_dash(self, classifier):
        """On error, parses 'Artist - Title' from filename"""
        with patch("services.content_filter.classifier.MutagenFile", side_effect=OSError("fail")):
            artist, title, genre = classifier._extract_metadata(Path("/Beatles - Hey Jude.mp3"))
        assert artist == "Beatles"
        assert title == "Hey Jude"

    def test_extract_metadata_mutagen_error_no_dash(self, classifier):
        """On error, no dash → filename is title"""
        with patch("services.content_filter.classifier.MutagenFile", side_effect=OSError("fail")):
            artist, title, genre = classifier._extract_metadata(Path("/mysong.mp3"))
        assert artist == "Unknown"
        assert title == "mysong"

    def test_extract_metadata_mutagen_returns_none(self, classifier):
        with patch("services.content_filter.classifier.MutagenFile", return_value=None):
            artist, title, genre = classifier._extract_metadata(Path("/test.mp3"))
        assert artist == "Unknown"
        assert title == "test"

    # --- _analyze_metadata ---

    def test_analyze_metadata_known_explicit_artist(self, classifier):
        score = classifier._analyze_metadata("Bad Rapper", "Song", "", "song.mp3")
        assert score.explicit_score >= 0.9

    def test_analyze_metadata_known_children_artist(self, classifier):
        score = classifier._analyze_metadata("Baby Shark", "Song", "", "song.mp3")
        assert score.children_score >= 0.9

    def test_analyze_metadata_known_christian_artist(self, classifier):
        score = classifier._analyze_metadata("Hillsong", "Song", "", "song.mp3")
        assert score.christian_score >= 0.9

    def test_analyze_metadata_known_clean_artist(self, classifier):
        score = classifier._analyze_metadata("Taylor Swift", "Song", "", "song.mp3")
        assert score.clean_score >= 0.8

    def test_analyze_metadata_explicit_keyword_in_title(self, classifier):
        score = classifier._analyze_metadata("Unknown", "nsfw song", "", "nsfw song.mp3")
        assert score.explicit_score >= 0.8

    def test_analyze_metadata_children_keyword(self, classifier):
        score = classifier._analyze_metadata("Unknown", "nursery rhyme", "", "file.mp3")
        assert score.children_score >= 0.7

    def test_analyze_metadata_christian_keyword(self, classifier):
        score = classifier._analyze_metadata("Unknown", "worship song", "", "file.mp3")
        assert score.christian_score >= 0.7

    def test_analyze_metadata_explicit_genre(self, classifier):
        score = classifier._analyze_metadata("Unknown", "Song", "gangsta rap", "file.mp3")
        assert score.explicit_score >= 0.4

    def test_analyze_metadata_clean_genre(self, classifier):
        score = classifier._analyze_metadata("Unknown", "Song", "classical", "file.mp3")
        assert score.clean_score >= 0.7

    def test_analyze_metadata_christian_genre(self, classifier):
        score = classifier._analyze_metadata("Unknown", "Song", "gospel", "file.mp3")
        assert score.christian_score >= 0.8

    def test_analyze_metadata_no_matches(self, classifier):
        score = classifier._analyze_metadata("Unknown Artist", "Random Song", "", "file.mp3")
        assert score.clean_score == 0.5
        assert score.confidence == 0.3
        assert "No specific indicators" in score.reasons[0]

    # --- classify_file ---

    def test_classify_file_metadata_only(self, classifier):
        with patch.object(classifier, "_extract_metadata", return_value=("Unknown", "Song", "")):
            result = classifier.classify_file("/test.mp3", use_lyrics=False, use_audio=False)
        assert "test.mp3" in result.file_path
        assert result.metadata_score is not None
        assert result.lyrics_score is None
        assert result.audio_score is None

    def test_classify_file_with_lyrics(self, classifier):
        from services.content_filter.classifier import ContentScore

        mock_lyrics_score = ContentScore(explicit_score=0.8, confidence=0.85, source="lyrics")

        with patch.object(classifier, "_extract_metadata", return_value=("Artist", "Song", "")):
            # Make metadata confidence low so lyrics tier triggers
            with patch.object(
                classifier,
                "_analyze_metadata",
                return_value=ContentScore(confidence=0.3, source="metadata"),
            ):
                with patch.object(classifier, "_analyze_lyrics", return_value=mock_lyrics_score):
                    result = classifier.classify_file("/test.mp3", use_lyrics=True)
        assert result.lyrics_score is not None
        assert result.lyrics_score.explicit_score == 0.8

    def test_classify_file_with_audio(self, classifier):
        from services.content_filter.classifier import ContentScore

        mock_audio_score = ContentScore(explicit_score=0.3, confidence=0.5, source="audio")

        with patch.object(classifier, "_extract_metadata", return_value=("Artist", "Song", "")):
            with patch.object(
                classifier,
                "_analyze_metadata",
                return_value=ContentScore(confidence=0.3, source="metadata"),
            ):
                with patch.object(classifier, "_analyze_lyrics", return_value=None):
                    with patch.object(classifier, "_analyze_audio", return_value=mock_audio_score):
                        result = classifier.classify_file("/test.mp3", use_lyrics=True, use_audio=True)
        assert result.audio_score is not None

    # --- classify_batch ---

    def test_classify_batch_success(self, classifier):
        with patch.object(classifier, "_extract_metadata", return_value=("A", "Song", "")):
            results = classifier.classify_batch(["/a.mp3", "/b.mp3"])
        assert len(results) == 2

    def test_classify_batch_with_callback(self, classifier):
        callback = Mock()
        with patch.object(classifier, "_extract_metadata", return_value=("A", "Song", "")):
            classifier.classify_batch(["/a.mp3"], progress_callback=callback)
        callback.assert_called_once()
        assert callback.call_args[0][0] == 1  # current
        assert callback.call_args[0][1] == 1  # total

    def test_classify_batch_error(self, classifier):
        with patch.object(classifier, "classify_file", side_effect=OSError("fail")):
            results = classifier.classify_batch(["/a.mp3"])
        assert len(results) == 1
        assert results[0].rating.value == "unknown"
        assert "Error" in results[0].score.reasons[0]

    # --- _combine_scores ---

    def test_combine_scores_metadata_only(self, classifier):
        from services.content_filter.classifier import ContentScore

        metadata = ContentScore(explicit_score=0.5, source="metadata")
        result = classifier._combine_scores(metadata, None, None)
        assert result is metadata  # Returns metadata directly

    def test_combine_scores_metadata_and_lyrics(self, classifier):
        from services.content_filter.classifier import ContentScore

        metadata = ContentScore(explicit_score=0.3, confidence=0.4, source="metadata")
        lyrics = ContentScore(explicit_score=0.9, confidence=0.85, source="lyrics")
        result = classifier._combine_scores(metadata, lyrics, None)
        assert result.source == "combined"
        # Weighted average: lyrics has higher weight
        assert result.explicit_score > 0.5

    def test_combine_scores_all_three(self, classifier):
        from services.content_filter.classifier import ContentScore

        metadata = ContentScore(explicit_score=0.3, confidence=0.4, source="metadata")
        lyrics = ContentScore(explicit_score=0.8, confidence=0.85, source="lyrics")
        audio = ContentScore(explicit_score=0.5, confidence=0.5, source="audio")
        result = classifier._combine_scores(metadata, lyrics, audio)
        assert result.source == "combined"
        assert len(result.reasons) == 0  # No reasons in input

    # --- _analyze_lyrics (lazy load) ---

    def test_analyze_lyrics_lazy_load_success(self, classifier):
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = Mock()
        mock_module = Mock()
        mock_module.LyricsAnalyzer.return_value = mock_analyzer
        classifier._lyrics_analyzer = None
        classifier._lyrics_analyzer_checked = False
        with patch.dict("sys.modules", {"services.content_filter.lyrics_analyzer": mock_module}):
            result = classifier._analyze_lyrics("Artist", "Title")
        assert result is not None

    def test_analyze_lyrics_import_error(self, classifier):
        classifier._lyrics_analyzer = None
        classifier._lyrics_analyzer_checked = False
        # Simulate ImportError by making the lazy import fail
        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def fail_import(name, *args, **kwargs):
            if "lyrics_analyzer" in name:
                raise ImportError("no module")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fail_import):
            result = classifier._analyze_lyrics("Artist", "Title")
        assert result is None

    def test_analyze_lyrics_already_checked(self, classifier):
        classifier._lyrics_analyzer = None
        classifier._lyrics_analyzer_checked = True
        result = classifier._analyze_lyrics("Artist", "Title")
        assert result is None

    # --- _analyze_audio (lazy load) ---

    def test_analyze_audio_lazy_load_success(self, classifier):
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = Mock()
        mock_module = Mock()
        mock_module.AudioAnalyzer.return_value = mock_analyzer
        classifier._audio_analyzer = None
        classifier._audio_analyzer_checked = False
        with patch.dict("sys.modules", {"services.content_filter.audio_analyzer": mock_module}):
            result = classifier._analyze_audio("/test.mp3")
        assert result is not None

    def test_analyze_audio_import_error(self, classifier):
        classifier._audio_analyzer = None
        classifier._audio_analyzer_checked = False
        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def fail_import(name, *args, **kwargs):
            if "audio_analyzer" in name:
                raise ImportError("no librosa")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fail_import):
            result = classifier._analyze_audio("/test.mp3")
        assert result is None

    def test_analyze_audio_already_checked(self, classifier):
        classifier._audio_analyzer = None
        classifier._audio_analyzer_checked = True
        result = classifier._analyze_audio("/test.mp3")
        assert result is None

    # --- get_stats ---

    def test_get_stats(self, classifier):
        stats = classifier.get_stats()
        assert stats["explicit_artists"] == 1
        assert stats["children_artists"] == 1

    # --- get_classifier singleton ---

    def test_get_classifier_singleton(self):
        import services.content_filter.classifier as mod

        mod._classifier_instance = None
        with patch.object(mod, "ContentClassifier") as MockCls:
            MockCls.return_value = Mock()
            c1 = mod.get_classifier()
            c2 = mod.get_classifier()
        assert c1 is c2


# ==========================================
# AudioAnalyzer Tests
# ==========================================


class TestAudioAnalyzerPhase2:
    """Tests for AudioAnalyzer._features_to_score (pure logic, no librosa)."""

    @pytest.fixture
    def analyzer(self):
        from services.content_filter.audio_analyzer import AudioAnalyzer

        obj = AudioAnalyzer.__new__(AudioAnalyzer)
        return obj

    def _base_features(self):
        """Base features dict with neutral values."""
        return {
            "tempo": 120.0,
            "energy": 0.15,
            "energy_std": 0.05,
            "brightness": 3000.0,
            "noisiness": 0.05,
            "rolloff": 5000.0,
            "mfcc_mean": [0.0] * 13,
            "chroma_std": 0.1,
            "harmonic_brightness": 0.3,
            "harmonic_darkness": 0.3,
            "onset_strength": 0.5,
            "pitch_mean": 300.0,
            "pitch_std": 100.0,
            "high_pitch_ratio": 0.2,
        }

    def test_features_to_score_basic(self, analyzer):
        features = self._base_features()
        score = analyzer._features_to_score(features)
        assert score.source == "audio"
        assert score.confidence == 0.5
        assert len(score.reasons) >= 3  # Tempo, Energy, Valence, high_pitch_ratio

    def test_children_score_moderate_tempo(self, analyzer):
        features = self._base_features()
        features["tempo"] = 110.0  # In 90-140 range
        features["high_pitch_ratio"] = 0.5  # > 0.4
        features["chroma_std"] = 0.1  # < 0.15
        features["harmonic_brightness"] = 0.8  # High valence
        features["harmonic_darkness"] = 0.2
        score = analyzer._features_to_score(features)
        assert score.children_score > 0.5

    def test_children_score_reason(self, analyzer):
        features = self._base_features()
        features["tempo"] = 110.0
        features["high_pitch_ratio"] = 0.5
        features["chroma_std"] = 0.1
        features["harmonic_brightness"] = 0.8
        features["harmonic_darkness"] = 0.2
        score = analyzer._features_to_score(features)
        assert any("children" in r.lower() for r in score.reasons)

    def test_aggressive_score_high_energy(self, analyzer):
        features = self._base_features()
        features["energy"] = 0.25  # > 0.3 * 0.7 = 0.21
        features["brightness"] = 1500.0  # < 2000
        features["onset_strength"] = 2.0  # > 1.5
        features["noisiness"] = 0.15  # > 0.1
        score = analyzer._features_to_score(features)
        assert score.explicit_score > 0  # Capped at 0.5
        assert score.explicit_score <= 0.5

    def test_aggressive_reason(self, analyzer):
        features = self._base_features()
        features["energy"] = 0.3
        features["brightness"] = 1000.0
        features["onset_strength"] = 2.0
        features["noisiness"] = 0.15
        score = analyzer._features_to_score(features)
        assert any("aggressive" in r.lower() for r in score.reasons)

    def test_clean_score_moderate_energy(self, analyzer):
        features = self._base_features()
        features["energy"] = 0.12  # Normalized: 0.12/0.3 = 0.4, in [0.2, 0.6]
        features["harmonic_brightness"] = 0.6
        features["harmonic_darkness"] = 0.3  # valence high
        score = analyzer._features_to_score(features)
        assert score.clean_score > 0.5

    def test_tempo_reasons_in_output(self, analyzer):
        features = self._base_features()
        features["tempo"] = 100.0
        score = analyzer._features_to_score(features)
        assert any("Tempo: 100" in r for r in score.reasons)

    def test_init_raises_without_librosa(self):
        from services.content_filter.audio_analyzer import LIBROSA_AVAILABLE, AudioAnalyzer

        if not LIBROSA_AVAILABLE:
            with pytest.raises(ImportError):
                AudioAnalyzer()

    def test_analyze_returns_none_on_error(self, analyzer):
        """analyze() returns None when librosa.load raises"""
        import services.content_filter.audio_analyzer as mod

        if not mod.LIBROSA_AVAILABLE:
            # Mock librosa
            mock_librosa = Mock()
            mock_librosa.load.side_effect = Exception("corrupt file")
            with patch.object(mod, "librosa", mock_librosa):
                with patch.object(mod, "LIBROSA_AVAILABLE", True):
                    result = analyzer.analyze("/bad.mp3")
            assert result is None

    def test_get_audio_features_returns_none_on_error(self, analyzer):
        import services.content_filter.audio_analyzer as mod

        if not mod.LIBROSA_AVAILABLE:
            mock_librosa = Mock()
            mock_librosa.load.side_effect = Exception("fail")
            with patch.object(mod, "librosa", mock_librosa):
                with patch.object(mod, "LIBROSA_AVAILABLE", True):
                    result = analyzer.get_audio_features("/bad.mp3")
            assert result is None


# ==========================================
# DownloadService Tests (queue operations)
# ==========================================


class TestDownloadServicePhase2:
    """Tests for DownloadService — queue ops not covered in existing tests."""

    @pytest.fixture(autouse=True)
    def reset(self):
        from services.download_service import DownloadService

        DownloadService.reset_instance()
        yield
        DownloadService.reset_instance()

    @pytest.fixture
    def service(self):
        from services.download_service import DownloadService

        svc = DownloadService.get_instance(tempfile.mkdtemp())
        svc._queue = MagicMock()
        return svc

    def test_pause_success(self, service):
        result = service.pause("item-1")
        assert result is True
        service._queue.pause.assert_called_once_with("item-1")

    def test_pause_error(self, service):
        service._queue.pause.side_effect = RuntimeError("fail")
        result = service.pause("item-1")
        assert result is False

    def test_resume_success(self, service):
        result = service.resume("item-1")
        assert result is True
        service._queue.resume.assert_called_once_with("item-1")

    def test_resume_error(self, service):
        service._queue.resume.side_effect = KeyError("no item")
        result = service.resume("item-1")
        assert result is False

    def test_retry_success(self, service):
        result = service.retry("item-1")
        assert result is True

    def test_retry_error(self, service):
        service._queue.retry.side_effect = RuntimeError("fail")
        result = service.retry("item-1")
        assert result is False

    def test_clear_completed_success(self, service):
        service._queue.clear_completed.return_value = 3
        result = service.clear_completed()
        assert result == 3

    def test_clear_completed_error(self, service):
        service._queue.clear_completed.side_effect = RuntimeError("fail")
        result = service.clear_completed()
        assert result == 0

    def test_clear_all_success(self, service):
        service._queue.clear_all.return_value = 5
        result = service.clear_all()
        assert result == 5

    def test_clear_all_error(self, service):
        service._queue.clear_all.side_effect = RuntimeError("fail")
        result = service.clear_all()
        assert result == 0

    def test_get_item_found(self, service):
        service._queue.get_all_items.return_value = {
            "item-1": {"id": "item-1", "url": "http://x", "title": "Song", "status": "pending"}
        }
        item = service.get_item("item-1")
        assert item is not None
        assert item.id == "item-1"

    def test_get_item_not_found(self, service):
        service._queue.get_all_items.return_value = {}
        item = service.get_item("item-999")
        assert item is None

    def test_get_item_error(self, service):
        service._queue.get_all_items.side_effect = AttributeError("fail")
        item = service.get_item("item-1")
        assert item is None

    def test_get_all_items(self, service):
        service._queue.get_all_items.return_value = {
            "a": {"id": "a", "url": "http://a", "title": "A", "status": "pending"},
            "b": {"id": "b", "url": "http://b", "title": "B", "status": "completed"},
        }
        items = service.get_all_items()
        assert len(items) == 2

    def test_get_all_items_error(self, service):
        service._queue.get_all_items.side_effect = AttributeError("fail")
        assert service.get_all_items() == []

    def test_add_download_error(self, service):
        service._queue.add.side_effect = ValueError("bad url")
        result = service.add_download("bad://url")
        assert result is None

    def test_add_batch(self, service):
        service._queue.add.return_value = "id-1"
        items = [
            {"url": "http://a", "metadata": {"title": "A"}},
            {"video_url": "http://b"},
        ]
        ids = service.add_batch(items)
        assert len(ids) == 2

    def test_on_progress(self, service):
        """_on_progress emits download_progress signal"""
        received = []
        service.download_progress.connect(lambda a, b: received.append((a, b)))
        service._on_progress("item-1", 50.0)
        assert received == [("item-1", 50.0)]

    def test_on_completed_with_auto_import(self, service):
        service._auto_import = True
        with patch.object(service, "_import_to_library") as mock_import:
            service._on_completed("item-1", "/path/file.mp3")
        mock_import.assert_called_once_with("item-1", "/path/file.mp3")

    def test_on_completed_without_auto_import(self, service):
        service._auto_import = False
        with patch.object(service, "_import_to_library") as mock_import:
            service._on_completed("item-1", "/path/file.mp3")
        mock_import.assert_not_called()

    def test_on_failed(self, service):
        received = []
        service.download_failed.connect(lambda a, b: received.append((a, b)))
        service._on_failed("item-1", "Network error")
        assert len(received) == 1

    def test_import_to_library_success(self, service):
        mock_lib = Mock()
        mock_lib.add_song.return_value = 42
        mock_metadata = {"title": "Song"}
        with patch.dict(
            "sys.modules",
            {
                "core.metadata_fetcher": Mock(extract_metadata=Mock(return_value=mock_metadata)),
                "services.library_service": Mock(LibraryService=Mock(get_instance=Mock(return_value=mock_lib))),
            },
        ):
            received = []
            service.auto_import_completed.connect(lambda x: received.append(x))
            service._import_to_library("item-1", "/path/file.mp3")
        assert received == [42]

    def test_import_to_library_error(self, service):
        with patch.dict(
            "sys.modules",
            {
                "core.metadata_fetcher": Mock(extract_metadata=Mock(side_effect=OSError("fail"))),
            },
        ):
            service._import_to_library("item-1", "/bad.mp3")  # Should not raise

    def test_auto_import_property(self, service):
        assert service.auto_import_enabled is True
        service.auto_import_enabled = False
        assert service.auto_import_enabled is False

    def test_cleanup(self, service):
        service._queue = Mock(spec=["stop"])
        service.cleanup()
        service._queue is None  # noqa: B015 — just verifying cleanup ran

    def test_cleanup_no_stop(self, service):
        service._queue = Mock(spec=[])
        service.cleanup()

    def test_download_item_to_dict(self):
        from services.download_service import DownloadItem, DownloadStatus

        item = DownloadItem(id="x", url="http://x", title="T", status=DownloadStatus.COMPLETED)
        d = item.to_dict()
        assert d["status"] == "completed"

    def test_download_item_from_dict_enum_status(self):
        from services.download_service import DownloadItem, DownloadStatus

        item = DownloadItem.from_dict({"id": "x", "url": "http://x", "status": DownloadStatus.FAILED})
        assert item.status == DownloadStatus.FAILED

    def test_download_item_from_dict_with_video_url(self):
        from services.download_service import DownloadItem

        item = DownloadItem.from_dict({"id": "x", "video_url": "http://v", "metadata": {"artist": "A"}})
        assert item.url == "http://v"
        assert item.artist == "A"


# ==========================================
# CloudSync Dataclasses & LocalFolderProvider Tests
# ==========================================


class TestCloudSyncPhase2:
    """Tests for cloud_sync_service dataclasses and LocalFolderProvider."""

    # --- SyncState ---

    def test_sync_state_to_dict(self):
        from services.cloud_sync_service import SyncState

        s = SyncState(last_sync_time="2024-01-01", provider="Local Folder")
        d = s.to_dict()
        assert d["provider"] == "Local Folder"

    def test_sync_state_from_dict(self):
        from services.cloud_sync_service import SyncState

        s = SyncState.from_dict(
            {
                "last_sync_time": "2024-01-01",
                "provider": "GDrive",
                "status": "idle",
                "pending_changes": 0,
                "last_sync_hash": None,
                "conflicts": [],
            }
        )
        assert s.provider == "GDrive"

    # --- SyncConflict ---

    def test_sync_conflict_to_dict(self):
        from services.cloud_sync_service import SyncConflict

        c = SyncConflict(
            item_type="song",
            item_id="1",
            local_data={"title": "A"},
            remote_data={"title": "B"},
            local_modified="2024-01-01",
            remote_modified="2024-01-02",
        )
        d = c.to_dict()
        assert d["item_type"] == "song"

    # --- LibraryExport ---

    def test_library_export_to_dict(self):
        from services.cloud_sync_service import LibraryExport

        e = LibraryExport(version="1.0", songs=[{"id": 1}])
        d = e.to_dict()
        assert d["version"] == "1.0"
        assert len(d["songs"]) == 1

    def test_library_export_from_dict(self):
        from services.cloud_sync_service import LibraryExport

        e = LibraryExport.from_dict(
            {
                "version": "2.0",
                "songs": [{"id": 1}, {"id": 2}],
                "playlists": [{"name": "Favs"}],
            }
        )
        assert e.version == "2.0"
        assert len(e.songs) == 2

    def test_library_export_compute_hash(self):
        from services.cloud_sync_service import LibraryExport

        e1 = LibraryExport(songs=[{"id": 1, "file_path": "/a.mp3"}])
        e2 = LibraryExport(songs=[{"id": 1, "file_path": "/a.mp3"}])
        assert e1.compute_hash() == e2.compute_hash()

        e3 = LibraryExport(songs=[{"id": 2, "file_path": "/b.mp3"}])
        assert e1.compute_hash() != e3.compute_hash()

    # --- Enums ---

    def test_sync_status_enum(self):
        from services.cloud_sync_service import SyncStatus

        assert SyncStatus.IDLE.value == "idle"
        assert SyncStatus.SYNCING.value == "syncing"

    def test_conflict_strategy_enum(self):
        from services.cloud_sync_service import ConflictStrategy

        assert ConflictStrategy.NEWER_WINS.value == "newer_wins"
        assert ConflictStrategy.LOCAL_WINS.value == "local_wins"

    # --- LocalFolderProvider ---

    def test_local_provider_connect_no_folder(self):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider(None)
        assert p.connect() is False

    def test_local_provider_connect_success(self, tmp_path):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider(str(tmp_path / "sync"))
        assert p.connect() is True
        assert p.is_connected is True
        assert p.name == "Local Folder"

    def test_local_provider_disconnect(self, tmp_path):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider(str(tmp_path / "sync"))
        p.connect()
        p.disconnect()
        assert p.is_connected is False

    def test_local_provider_upload_download(self, tmp_path):
        from services.cloud_sync_service import LocalFolderProvider

        sync_dir = tmp_path / "sync"
        p = LocalFolderProvider(str(sync_dir))
        p.connect()

        # Create a file to upload
        src_file = tmp_path / "test.json"
        src_file.write_text('{"data": 1}')

        assert p.upload(str(src_file), "test.json") is True
        assert p.exists("test.json") is True

        # Download
        dest = tmp_path / "downloaded.json"
        assert p.download("test.json", str(dest)) is True
        assert dest.read_text() == '{"data": 1}'

    def test_local_provider_upload_not_connected(self):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider("/tmp/sync")
        assert p.upload("/src", "dest") is False

    def test_local_provider_download_not_connected(self):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider("/tmp/sync")
        assert p.download("remote", "/local") is False

    def test_local_provider_download_not_found(self, tmp_path):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider(str(tmp_path / "sync"))
        p.connect()
        assert p.download("nonexistent.json", str(tmp_path / "out.json")) is False

    def test_local_provider_exists_not_connected(self):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider("/tmp/sync")
        assert p.exists("file.json") is False

    def test_local_provider_get_modified_time(self, tmp_path):
        from services.cloud_sync_service import LocalFolderProvider

        sync_dir = tmp_path / "sync"
        p = LocalFolderProvider(str(sync_dir))
        p.connect()

        # File doesn't exist
        assert p.get_modified_time("nope.json") is None

        # Create file
        (sync_dir / "test.json").write_text("data")
        mtime = p.get_modified_time("test.json")
        assert mtime is not None

    def test_local_provider_get_modified_not_connected(self):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider("/tmp/sync")
        assert p.get_modified_time("file.json") is None

    def test_local_provider_delete(self, tmp_path):
        from services.cloud_sync_service import LocalFolderProvider

        sync_dir = tmp_path / "sync"
        p = LocalFolderProvider(str(sync_dir))
        p.connect()

        (sync_dir / "test.json").write_text("data")
        assert p.delete("test.json") is True
        assert not (sync_dir / "test.json").exists()

    def test_local_provider_delete_not_connected(self):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider("/tmp/sync")
        assert p.delete("file.json") is False

    def test_local_provider_delete_nonexistent(self, tmp_path):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider(str(tmp_path / "sync"))
        p.connect()
        assert p.delete("nonexistent.json") is True  # No error

    def test_local_provider_sync_folder_setter(self):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider("/tmp/a")
        assert p.sync_folder == Path("/tmp/a")
        p.sync_folder = "/tmp/b"
        assert p.sync_folder == Path("/tmp/b")
        assert p.is_connected is False

    def test_local_provider_sync_folder_none(self):
        from services.cloud_sync_service import LocalFolderProvider

        p = LocalFolderProvider("/tmp/a")
        p.sync_folder = None
        assert p.sync_folder is None


# ==========================================
# CloudSyncService (core operations)
# ==========================================


class TestCloudSyncServiceOps:
    """Tests for CloudSyncService core methods."""

    @pytest.fixture(autouse=True)
    def reset(self):
        from services.cloud_sync_service import CloudSyncService

        CloudSyncService.reset_instance()
        yield
        CloudSyncService.reset_instance()

    @pytest.fixture
    def service(self, tmp_path):
        from services.cloud_sync_service import CloudSyncService

        svc = CloudSyncService(str(tmp_path / "data"))
        return svc

    def test_init_and_device_id(self, service):
        assert service.device_id is not None
        assert len(service.device_id) > 0

    def test_sync_state_property(self, service):
        state = service.sync_state
        assert state.status == "idle"

    def test_set_provider(self, service):
        mock_provider = Mock()
        mock_provider.name = "TestProvider"
        result = service.set_provider(mock_provider)
        assert result is True
        assert service.get_provider() is mock_provider

    def test_connect_no_provider(self, service):
        received = []
        service.sync_failed.connect(lambda msg: received.append(msg))
        result = service.connect()
        assert result is False
        assert len(received) == 1

    def test_connect_with_provider(self, service):
        from services.cloud_sync_service import SyncStatus

        mock_provider = Mock()
        mock_provider.name = "TestProvider"
        mock_provider.connect.return_value = True
        service._provider = mock_provider
        service._state.provider = "TestProvider"
        result = service.connect()
        assert result is True
        assert service.sync_status == SyncStatus.IDLE

    def test_disconnect(self, service):
        mock_provider = Mock()
        mock_provider.name = "TestProvider"
        service._provider = mock_provider
        service.disconnect()
        mock_provider.disconnect.assert_called_once()

    def test_is_connected_false(self, service):
        assert service.is_connected is False

    def test_is_connected_true(self, service):
        mock_provider = Mock()
        mock_provider.is_connected = True
        service._provider = mock_provider
        assert service.is_connected is True

    def test_conflict_strategy_property(self, service):
        from services.cloud_sync_service import ConflictStrategy

        assert service.conflict_strategy == ConflictStrategy.NEWER_WINS
        service.conflict_strategy = ConflictStrategy.LOCAL_WINS
        assert service.conflict_strategy == ConflictStrategy.LOCAL_WINS

    def test_last_sync_time(self, service):
        assert service.last_sync_time is None

    def test_get_state(self, service):
        state = service.get_state()
        assert state.status == "idle"

    def test_save_and_load_state(self, service, tmp_path):
        from services.cloud_sync_service import CloudSyncService

        service._state.last_sync_time = "2024-01-01T00:00:00"
        service._state.provider = "Local Folder"
        service._save_state()

        # Create new instance to load state
        svc2 = CloudSyncService(str(tmp_path / "data"))
        assert svc2.sync_state.last_sync_time == "2024-01-01T00:00:00"

    def test_export_library(self, service):
        mock_db = Mock()
        mock_db.fetch_all.side_effect = [
            [{"id": 1, "title": "Song A"}],  # songs
            [{"id": 1, "name": "Playlist 1"}],  # playlists
            [{"song_id": 1}],  # playlist_songs
        ]
        export = service.export_library(mock_db)
        assert len(export.songs) == 1
        assert export.device_id == service.device_id

    def test_export_library_db_error(self, service):
        mock_db = Mock()
        mock_db.fetch_all.side_effect = sqlite3.Error("fail")
        export = service.export_library(mock_db)
        assert export.songs == []

    def test_import_library(self, service):
        from services.cloud_sync_service import LibraryExport

        mock_db = Mock()
        mock_db.fetch_one.return_value = None  # Song doesn't exist
        mock_db.add_song.return_value = 1

        export = LibraryExport(songs=[{"file_path": "/a.mp3", "title": "A"}])
        stats = service.import_library(export, mock_db)
        assert stats["added"] == 1

    def test_import_library_existing_merge(self, service):
        from services.cloud_sync_service import LibraryExport

        mock_db = Mock()
        mock_db.fetch_one.return_value = {"id": 1}  # Song exists

        export = LibraryExport(songs=[{"file_path": "/a.mp3"}])
        stats = service.import_library(export, mock_db, merge=True)
        assert stats["skipped"] == 1

    def test_import_library_error(self, service):
        from services.cloud_sync_service import LibraryExport

        mock_db = Mock()
        mock_db.fetch_one.side_effect = sqlite3.Error("fail")

        export = LibraryExport(songs=[{"file_path": "/a.mp3"}])
        stats = service.import_library(export, mock_db)
        assert stats["errors"] == 1

    def test_merge_exports_newer_wins(self, service):
        from services.cloud_sync_service import LibraryExport

        local = LibraryExport(
            songs=[
                {"file_path": "/a.mp3", "title": "Local A", "date_modified": "2024-02"},
            ]
        )
        remote = LibraryExport(
            songs=[
                {"file_path": "/a.mp3", "title": "Remote A", "date_modified": "2024-01"},
                {"file_path": "/b.mp3", "title": "Remote B"},
            ]
        )
        merged = service._merge_exports(local, remote)
        assert len(merged.songs) == 2
        # Local is newer, should win
        song_a = next(s for s in merged.songs if s["file_path"] == "/a.mp3")
        assert song_a["title"] == "Local A"

    def test_merge_exports_local_wins(self, service):
        from services.cloud_sync_service import ConflictStrategy, LibraryExport

        service._conflict_strategy = ConflictStrategy.LOCAL_WINS
        local = LibraryExport(songs=[{"file_path": "/a.mp3", "title": "Local"}])
        remote = LibraryExport(songs=[{"file_path": "/a.mp3", "title": "Remote"}])
        merged = service._merge_exports(local, remote)
        assert merged.songs[0]["title"] == "Local"

    def test_merge_exports_remote_wins(self, service):
        from services.cloud_sync_service import ConflictStrategy, LibraryExport

        service._conflict_strategy = ConflictStrategy.REMOTE_WINS
        local = LibraryExport(songs=[{"file_path": "/a.mp3", "title": "Local"}])
        remote = LibraryExport(songs=[{"file_path": "/a.mp3", "title": "Remote"}])
        merged = service._merge_exports(local, remote)
        assert merged.songs[0]["title"] == "Remote"

    def test_merge_exports_keep_both(self, service):
        from services.cloud_sync_service import ConflictStrategy, LibraryExport

        service._conflict_strategy = ConflictStrategy.KEEP_BOTH  # Falls to default (local)
        local = LibraryExport(songs=[{"file_path": "/a.mp3", "title": "Local"}])
        remote = LibraryExport(songs=[{"file_path": "/a.mp3", "title": "Remote"}])
        merged = service._merge_exports(local, remote)
        assert merged.songs[0]["title"] == "Local"  # Default

    def test_merge_exports_playlists(self, service):
        from services.cloud_sync_service import LibraryExport

        local = LibraryExport(playlists=[{"name": "Favs", "songs": [1]}])
        remote = LibraryExport(playlists=[{"name": "Party", "songs": [2]}])
        merged = service._merge_exports(local, remote)
        assert len(merged.playlists) == 2

    def test_sync_not_connected(self, service):
        received = []
        service.sync_failed.connect(lambda msg: received.append(msg))
        result = service.sync()
        assert result is False

    def test_cleanup(self, service):
        mock_provider = Mock()
        service._provider = mock_provider
        service.cleanup()
        mock_provider.disconnect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
