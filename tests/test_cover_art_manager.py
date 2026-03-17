"""
Tests for CoverArtManager - Automatic cover art downloading

Tests cover:
- Initialization and directory creation
- Cover URL resolution via MusicBrainz
- Cover download with HTTP mocking
- Download by MusicBrainz Release ID
- Cover path generation and existence checks
- Filename sanitization
- Statistics gathering
- Error handling (network errors, missing releases, filesystem errors)
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

# ─── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def cover_manager(tmp_path):
    """CoverArtManager with a temporary cover directory"""
    with patch("core.cover_art_manager.musicbrainzngs"):
        from core.cover_art_manager import CoverArtManager

        return CoverArtManager(cover_art_dir=str(tmp_path / "covers"))


@pytest.fixture
def cover_manager_cls():
    """Return the CoverArtManager class with musicbrainzngs patched"""
    with patch("core.cover_art_manager.musicbrainzngs"):
        from core.cover_art_manager import CoverArtManager

        yield CoverArtManager


# ─── Tests: Initialization ─────────────────────────────────────────────


class TestCoverArtInit:
    def test_init_creates_directory(self, tmp_path):
        """Cover directory is created on init"""
        cover_dir = tmp_path / "my_covers"
        with patch("core.cover_art_manager.musicbrainzngs"):
            from core.cover_art_manager import CoverArtManager

            CoverArtManager(cover_art_dir=str(cover_dir))
        assert cover_dir.exists()

    def test_init_default_directory(self):
        """Default cover directory is downloads/covers"""
        with patch("core.cover_art_manager.musicbrainzngs"):
            with patch.object(Path, "mkdir"):
                from core.cover_art_manager import CoverArtManager

                manager = CoverArtManager()
                assert "covers" in str(manager.cover_dir)


# ─── Tests: get_cover_url ──────────────────────────────────────────────


class TestGetCoverUrl:
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_get_cover_url_success(self, mock_mbngs, tmp_path):
        """Successful cover URL lookup returns a URL string"""
        mock_mbngs.search_releases.return_value = {"release-list": [{"id": "abc-123"}]}
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        url = manager.get_cover_url("Queen", "A Night at the Opera")

        assert url is not None
        assert "abc-123" in url
        assert "coverartarchive.org" in url

    @patch("core.cover_art_manager.musicbrainzngs")
    def test_get_cover_url_no_releases(self, mock_mbngs, tmp_path):
        """Returns None when no releases found"""
        mock_mbngs.search_releases.return_value = {"release-list": []}
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        url = manager.get_cover_url("Nobody", "No Album")
        assert url is None

    @patch("core.cover_art_manager.musicbrainzngs")
    def test_get_cover_url_api_error(self, mock_mbngs, tmp_path):
        """Returns None on API error"""
        mock_mbngs.search_releases.side_effect = requests.RequestException("timeout")
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        url = manager.get_cover_url("Artist", "Album")
        assert url is None


# ─── Tests: download_cover ─────────────────────────────────────────────


class TestDownloadCover:
    @patch("core.cover_art_manager.requests.get")
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_download_cover_success(self, mock_mbngs, mock_get, tmp_path):
        """Cover is downloaded and saved to expected path"""
        mock_mbngs.search_releases.return_value = {"release-list": [{"id": "release-id-1"}]}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"\xff\xd8\xff\xe0FAKE_JPEG_DATA"
        mock_get.return_value = mock_response

        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        result = manager.download_cover("Queen", "A Night at the Opera")

        assert result is True
        # Verify file was written
        expected_dir = tmp_path / "Queen" / "A Night at the Opera"
        cover_file = expected_dir / "cover.jpg"
        assert cover_file.exists()
        assert cover_file.read_bytes() == b"\xff\xd8\xff\xe0FAKE_JPEG_DATA"

    @patch("core.cover_art_manager.musicbrainzngs")
    def test_download_cover_no_url(self, mock_mbngs, tmp_path):
        """Returns False when no cover URL is found"""
        mock_mbngs.search_releases.return_value = {"release-list": []}
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        result = manager.download_cover("Nobody", "No Album")
        assert result is False

    @patch("core.cover_art_manager.requests.get")
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_download_cover_http_error(self, mock_mbngs, mock_get, tmp_path):
        """Returns False on HTTP error (e.g. 404)"""
        mock_mbngs.search_releases.return_value = {"release-list": [{"id": "id-1"}]}
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        result = manager.download_cover("Artist", "Album")
        assert result is False

    @patch("core.cover_art_manager.requests.get")
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_download_cover_custom_save_path(self, mock_mbngs, mock_get, tmp_path):
        """Cover is saved to custom path when provided"""
        mock_mbngs.search_releases.return_value = {"release-list": [{"id": "id-1"}]}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"JPEG_DATA"
        mock_get.return_value = mock_response

        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        custom_path = str(tmp_path / "custom_cover.jpg")
        result = manager.download_cover("Artist", "Album", save_path=custom_path)

        assert result is True
        assert Path(custom_path).exists()


# ─── Tests: download_cover_from_mbid ───────────────────────────────────


class TestDownloadFromMBID:
    @patch("core.cover_art_manager.requests.get")
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_download_from_mbid_success(self, mock_mbngs, mock_get, tmp_path):
        """Cover downloaded by MBID is saved correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"IMAGE_DATA"
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_get.return_value = mock_response

        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        valid_mbid = "12345678-1234-1234-1234-123456789abc"
        save_path = str(tmp_path / "mbid_cover.jpg")
        result = manager.download_cover_from_mbid(valid_mbid, save_path)

        assert result is True
        assert Path(save_path).read_bytes() == b"IMAGE_DATA"
        mock_get.assert_called_once_with(
            f"https://coverartarchive.org/release/{valid_mbid}/front", timeout=10, stream=True
        )

    @patch("core.cover_art_manager.requests.get")
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_download_from_mbid_not_found(self, mock_mbngs, mock_get, tmp_path):
        """Returns False when MBID has no cover art"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        result = manager.download_cover_from_mbid("bad-id", str(tmp_path / "x.jpg"))
        assert result is False


# ─── Tests: Path and existence checks ──────────────────────────────────


class TestPathAndExistence:
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_get_cover_path(self, mock_mbngs, tmp_path):
        """get_cover_path returns expected artist/album/cover.jpg structure"""
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        path = manager.get_cover_path("Queen", "Greatest Hits")
        assert path == tmp_path / "Queen" / "Greatest Hits" / "cover.jpg"

    @patch("core.cover_art_manager.musicbrainzngs")
    def test_has_cover_true(self, mock_mbngs, tmp_path):
        """has_cover returns True when cover file exists"""
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        cover_dir = tmp_path / "Queen" / "Greatest Hits"
        cover_dir.mkdir(parents=True)
        (cover_dir / "cover.jpg").write_bytes(b"data")

        assert manager.has_cover("Queen", "Greatest Hits") is True

    @patch("core.cover_art_manager.musicbrainzngs")
    def test_has_cover_false(self, mock_mbngs, tmp_path):
        """has_cover returns False when cover file does not exist"""
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        assert manager.has_cover("Nobody", "No Album") is False


# ─── Tests: Filename sanitization ──────────────────────────────────────


class TestSanitizeFilename:
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_sanitize_removes_invalid_chars(self, mock_mbngs, tmp_path):
        """Invalid filesystem characters are replaced with underscores"""
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        sanitized = manager._sanitize_filename('AC/DC: "Best Of" <Hits>')
        assert "/" not in sanitized
        assert ":" not in sanitized
        assert '"' not in sanitized
        assert "<" not in sanitized
        assert ">" not in sanitized

    @patch("core.cover_art_manager.musicbrainzngs")
    def test_sanitize_truncates_long_names(self, mock_mbngs, tmp_path):
        """Names longer than 100 chars are truncated"""
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        long_name = "A" * 200
        sanitized = manager._sanitize_filename(long_name)
        assert len(sanitized) <= 100


# ─── Tests: Statistics ─────────────────────────────────────────────────


class TestStats:
    @patch("core.cover_art_manager.musicbrainzngs")
    def test_get_stats_with_covers(self, mock_mbngs, tmp_path):
        """Stats correctly count artists and covers"""
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        # Create artist/album/cover structure
        for artist in ["Queen", "Pink Floyd"]:
            album_dir = tmp_path / artist / "Album"
            album_dir.mkdir(parents=True)
            (album_dir / "cover.jpg").write_bytes(b"data")

        stats = manager.get_stats()
        assert stats["total_artists"] == 2
        assert stats["total_covers"] == 2

    @patch("core.cover_art_manager.musicbrainzngs")
    def test_get_stats_empty_dir(self, mock_mbngs, tmp_path):
        """Stats return zeros for empty cover directory"""
        from core.cover_art_manager import CoverArtManager

        manager = CoverArtManager(cover_art_dir=str(tmp_path))

        stats = manager.get_stats()
        assert stats["total_artists"] == 0
        assert stats["total_covers"] == 0
