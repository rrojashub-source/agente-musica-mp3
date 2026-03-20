"""
Tests for Search Tab UI (Phase 4.1)
TDD: Write tests FIRST, then implement src/gui/tabs/search_tab.py
"""

import time
from unittest.mock import Mock, patch

import pytest

# Guard: skip entire module if PySide6 is not available (CI headless, etc.)
PySide6 = pytest.importorskip("PySide6")


# ------------------------------------------------------------------ fixtures


@pytest.fixture
def search_tab(qapp):
    """
    Create a SearchTab with mocked credentials / searchers so no real
    API calls are made and no credential-missing dialog appears.
    """
    with (
        patch("gui.tabs.search_tab.SearchTab._load_credentials"),
        patch("gui.tabs.search_tab.SearchTab._show_missing_credentials_prompt"),
    ):
        from gui.tabs.search_tab import SearchTab

        tab = SearchTab(download_queue=Mock())
        # Inject mock searchers
        tab.youtube_searcher = Mock()
        tab.spotify_searcher = Mock()
        tab._credentials_missing = False
        yield tab


# ----------------------------------------------------------- test functions


class TestSearchTabUI:
    """Test Search Tab user interface"""

    def test_search_box_functionality(self, search_tab):
        """Test search box accepts input and triggers search"""
        # Configure mock YouTube results
        search_tab.youtube_searcher.search.return_value = [{"title": "Bohemian Rhapsody", "video_id": "abc123"}]
        search_tab.spotify_searcher.search_tracks.return_value = []

        # Type a query
        search_tab.search_box.setText("Bohemian Rhapsody")

        # Trigger search (simulates pressing Enter / clicking Buscar)
        result = search_tab.on_search_clicked()

        assert result is True
        search_tab.youtube_searcher.search.assert_called_once_with("Bohemian Rhapsody", max_results=10)

    def test_results_display(self, search_tab):
        """Test search results display correctly"""
        yt_results = [
            {"title": "Song A", "video_id": "v1"},
            {"title": "Song B", "video_id": "v2"},
        ]
        sp_results = [
            {"title": "Song C", "artist": "Artist C"},
        ]
        search_tab.youtube_searcher.search.return_value = yt_results
        search_tab.spotify_searcher.search_tracks.return_value = sp_results

        search_tab.search_box.setText("test")
        search_tab.on_search_clicked()

        # YouTube list should have 2 items, Spotify list 1
        assert search_tab.youtube_results.count() == 2
        assert search_tab.spotify_results.count() == 1

        # Verify first YouTube item contains title text
        first_yt_text = search_tab.youtube_results.item(0).text()
        assert "Song A" in first_yt_text

    def test_multiple_selection(self, search_tab):
        """Test selecting multiple songs from results"""
        # Manually add 5 songs via the internal selection helper
        for i in range(5):
            song_data = {"title": f"Song {i}", "video_id": f"v{i}", "source": "youtube"}
            search_tab._add_to_selection(song_data)

        assert len(search_tab.selected_songs) == 5
        assert "5 songs" in search_tab.selected_count_label.text()

    def test_add_to_library_button(self, search_tab):
        """Test 'Add to Library' button adds selected songs to download queue"""
        # Pre-select songs
        songs = [
            {"title": "Song 1", "video_id": "v1", "source": "youtube"},
            {"title": "Song 2", "video_id": "v2", "source": "youtube"},
        ]
        for s in songs:
            search_tab._add_to_selection(s)

        # Click "Download Selected" (suppress QMessageBox)
        with patch("gui.tabs.search_tab.QMessageBox"):
            search_tab.on_add_to_library_clicked()

        # download_queue.add should have been called for each song
        assert search_tab.download_queue.add.call_count == 2

        # Selection cleared after adding
        assert len(search_tab.selected_songs) == 0

    def test_concurrent_api_calls(self, search_tab):
        """Test YouTube + Spotify search calls run concurrently (both called)"""
        search_tab.youtube_searcher.search.return_value = []
        search_tab.spotify_searcher.search_tracks.return_value = []

        # Both checkboxes enabled
        search_tab.youtube_checkbox.setChecked(True)
        search_tab.spotify_checkbox.setChecked(True)

        search_tab.search_box.setText("test query")
        search_tab.on_search_clicked()

        # Both APIs should have been called
        search_tab.youtube_searcher.search.assert_called_once()
        search_tab.spotify_searcher.search_tracks.assert_called_once()

    def test_search_response_time(self, search_tab):
        """Test search completes in < 2 seconds (with mocked APIs)"""
        search_tab.youtube_searcher.search.return_value = [
            {"title": f"Song {i}", "video_id": f"v{i}"} for i in range(10)
        ]
        search_tab.spotify_searcher.search_tracks.return_value = [
            {"title": f"Track {i}", "artist": f"Artist {i}"} for i in range(10)
        ]

        search_tab.search_box.setText("performance test")

        start = time.monotonic()
        search_tab.on_search_clicked()
        elapsed = time.monotonic() - start

        assert elapsed < 2.0, f"Search took {elapsed:.2f}s, expected < 2s"

    def test_empty_query_rejected(self, search_tab):
        """Test that an empty query does not trigger a search"""
        search_tab.search_box.setText("")
        result = search_tab.on_search_clicked()
        assert result is False
        search_tab.youtube_searcher.search.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
