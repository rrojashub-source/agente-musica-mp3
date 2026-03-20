"""
Tests for AcoustIDClient - Audio Fingerprinting
Mocks subprocess (fpcalc), HTTP calls, and the acoustid library.
"""

from unittest.mock import patch


from src.core.acoustid_client import AcoustIDClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(api_key="test-api-key", fpcalc_available=True):
    """Create an AcoustIDClient with mocked FpcalcChecker."""
    with patch("src.core.acoustid_client.FpcalcChecker") as MockChecker:
        checker = MockChecker.return_value
        checker.is_available.return_value = fpcalc_available
        checker.fpcalc_path = "C:/tools/fpcalc.exe" if fpcalc_available else None
        checker.get_install_instructions.return_value = "Install fpcalc..."
        client = AcoustIDClient(api_key=api_key)
    return client


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    def test_available_when_key_and_fpcalc(self):
        client = _make_client(api_key="key", fpcalc_available=True)
        assert client.is_available() is True

    def test_unavailable_without_api_key(self):
        client = _make_client(api_key=None, fpcalc_available=True)
        assert client.is_available() is False

    def test_unavailable_without_fpcalc(self):
        client = _make_client(api_key="key", fpcalc_available=False)
        assert client.is_available() is False


# ---------------------------------------------------------------------------
# identify_song
# ---------------------------------------------------------------------------


class TestIdentifySong:
    def test_returns_none_when_not_available(self):
        client = _make_client(api_key=None, fpcalc_available=False)
        assert client.identify_song("some_file.mp3") is None

    def test_returns_none_for_missing_file(self, tmp_path):
        client = _make_client()
        result = client.identify_song(str(tmp_path / "nonexistent.mp3"))
        assert result is None

    @patch("src.core.acoustid_client.acoustid.lookup")
    @patch("src.core.acoustid_client.acoustid.match")
    def test_successful_identification(self, mock_match, mock_lookup, tmp_path):
        """Successful match returns dict with title, artist, score."""
        client = _make_client()

        # Create a dummy audio file
        audio_file = tmp_path / "song.mp3"
        audio_file.write_bytes(b"\x00" * 100)

        # Mock acoustid.match to yield results
        mock_match.return_value = iter(
            [
                (0.95, "rec-id-1", "Bohemian Rhapsody", "Queen"),
                (0.80, "rec-id-2", "Bohemian Rhapsody", "Gregorian"),
            ]
        )
        # Prevent _enrich_metadata from making real calls
        mock_lookup.return_value = {}

        result = client.identify_song(str(audio_file))

        assert result is not None
        assert result["title"] == "Bohemian Rhapsody"
        assert result["artist"] == "Queen"
        assert result["score"] == 0.95
        assert result["recording_id"] == "rec-id-1"

    @patch("src.core.acoustid_client.acoustid.match")
    def test_no_match_returns_none(self, mock_match, tmp_path):
        client = _make_client()
        audio_file = tmp_path / "noise.mp3"
        audio_file.write_bytes(b"\x00" * 100)

        mock_match.return_value = iter([])
        result = client.identify_song(str(audio_file))
        assert result is None

    @patch("src.core.acoustid_client.acoustid.match")
    def test_network_error_returns_none(self, mock_match, tmp_path):
        """WebServiceError should be caught and return None."""
        import acoustid as real_acoustid

        client = _make_client()
        audio_file = tmp_path / "song.mp3"
        audio_file.write_bytes(b"\x00" * 100)

        mock_match.side_effect = real_acoustid.WebServiceError("timeout")

        result = client.identify_song(str(audio_file))
        assert result is None


# ---------------------------------------------------------------------------
# batch_identify
# ---------------------------------------------------------------------------


class TestBatchIdentify:
    @patch.object(AcoustIDClient, "identify_song")
    def test_batch_filters_by_min_score(self, mock_identify):
        client = _make_client()

        mock_identify.side_effect = [
            {"title": "A", "artist": "X", "score": 0.95},
            {"title": "B", "artist": "Y", "score": 0.50},
            None,
        ]

        results = client.batch_identify(["f1.mp3", "f2.mp3", "f3.mp3"], min_score=0.7)

        assert results["f1.mp3"] is not None
        assert results["f1.mp3"]["score"] == 0.95
        assert results["f2.mp3"] is None  # below threshold
        assert results["f3.mp3"] is None  # no match


# ---------------------------------------------------------------------------
# get_fingerprint
# ---------------------------------------------------------------------------


class TestGetFingerprint:
    @patch("src.core.acoustid_client.acoustid.fingerprint_file")
    def test_get_fingerprint_success(self, mock_fp_file):
        client = _make_client()
        mock_fp_file.return_value = (210, "AQAA...base64...")

        fp = client.get_fingerprint("song.mp3")
        assert fp == "AQAA...base64..."

    def test_get_fingerprint_no_fpcalc(self):
        client = _make_client(fpcalc_available=False)
        assert client.get_fingerprint("song.mp3") is None
