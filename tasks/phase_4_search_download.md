# Phase 4: Search & Download System - Implementation Plan

**Created:** November 12, 2025
**Status:** PLANNING (not started)
**Duration:** Estimated 2 weeks
**Priority:** 🔥 HIGH

---

## 🎯 Phase Goal

Implement complete search and download system with:
- YouTube + Spotify search integration
- Background download queue (non-blocking UI)
- YouTube playlist downloader
- MusicBrainz metadata auto-complete

---

## 📋 SOURCE OF TRUTH

**This file is the authoritative plan for Phase 4.**

If there's any conflict between this plan and other documentation, THIS FILE WINS.
Any changes to scope/implementation MUST be documented here first.

---

## 🧪 TESTS TO WRITE FIRST (TDD)

### 4.1 Search Tab Tests

**File:** `tests/test_youtube_search.py`
```python
# Tests BEFORE implementation:
- test_youtube_api_connection()
- test_search_by_artist()
- test_search_by_song()
- test_search_results_format()
- test_search_timeout_handling()
- test_search_rate_limit_handling()
- test_invalid_query_handling()
```

**File:** `tests/test_spotify_search.py`
```python
# Tests BEFORE implementation:
- test_spotify_api_connection()
- test_search_tracks()
- test_search_albums()
- test_search_artists()
- test_metadata_extraction()
- test_rate_limit_handling()
- test_oauth_token_refresh()
```

**File:** `tests/test_search_tab_ui.py`
```python
# Tests BEFORE implementation:
- test_search_box_functionality()
- test_results_display()
- test_multiple_selection()
- test_add_to_library_button()
- test_concurrent_api_calls()
- test_search_response_time()  # < 2 seconds
```

---

### 4.2 Download Queue Tests

**File:** `tests/test_download_queue.py`
```python
# Tests BEFORE implementation:
- test_queue_add_song()
- test_queue_remove_song()
- test_concurrent_downloads()  # 50 simultaneous
- test_progress_callback()
- test_pause_resume_download()
- test_cancel_download()
- test_download_completion_event()
- test_queue_persistence()  # Survives app restart
```

**File:** `tests/test_download_worker.py`
```python
# Tests BEFORE implementation:
- test_yt_dlp_download()
- test_mp3_conversion()
- test_metadata_embedding()
- test_file_naming()
- test_error_handling()  # Network fail, disk full
- test_progress_reporting()
```

---

### 4.3 Playlist Downloader Tests

**File:** `tests/test_playlist_downloader.py`
```python
# Tests BEFORE implementation:
- test_extract_playlist_info()
- test_playlist_preview()
- test_download_all_songs()
- test_metadata_autocomplete()
- test_database_insertion()
- test_invalid_playlist_url()
- test_large_playlist_handling()  # 100+ songs
```

---

### 4.4 MusicBrainz Tests

**File:** `tests/test_metadata_autocomplete.py`
```python
# Tests BEFORE implementation:
- test_musicbrainz_search()
- test_metadata_extraction()
- test_album_art_download()
- test_batch_autocomplete()  # 100 songs
- test_accuracy_threshold()  # 90%+
- test_user_selection_workflow()
- test_database_update()
```

---

## 🔨 IMPLEMENTATION STEPS (TDD Red → Green → Refactor)

### Step 1: Setup API Credentials (Day 1)

**Tasks:**
1. Register YouTube Data API v3
   - Get API key from Google Cloud Console
   - 10,000 requests/day limit
   - Add to `~/.claude/secrets/credentials.json`

2. Register Spotify Web API
   - Create app in Spotify Developer Dashboard
   - Get Client ID + Client Secret
   - Add to `~/.claude/secrets/credentials.json`

3. MusicBrainz setup
   - No API key needed
   - Set user agent: `NexusMusicManager/1.0`

**Acceptance:**
- ✅ All API credentials stored securely
- ✅ Test connection to each API successful

---

### Step 2: YouTube Search Integration (Days 2-3)

**Red Phase:**
1. Write all tests in `tests/test_youtube_search.py` ✅
2. Run tests → VERIFY they FAIL ✅

**Green Phase:**
3. Create `src/api/youtube_search.py`:
   ```python
   class YouTubeSearcher:
       def __init__(self, api_key):
           # Initialize YouTube Data API v3

       def search(self, query, max_results=20):
           # Return: list of video results
           # Format: [{'video_id', 'title', 'duration', 'thumbnail_url'}]

       def get_video_metadata(self, video_id):
           # Detailed metadata for single video
   ```

4. Run tests → VERIFY they PASS ✅

**Refactor Phase:**
5. Add error handling (rate limits, timeouts)
6. Optimize API calls (batch requests)
7. Add caching (avoid duplicate searches)

**Integration:**
- Connect to `src/gui/tabs/search_tab.py` (created in Step 6)

---

### Step 3: Spotify Search Integration (Days 2-3)

**Red Phase:**
1. Write all tests in `tests/test_spotify_search.py` ✅
2. Run tests → VERIFY they FAIL ✅

**Green Phase:**
3. Create `src/api/spotify_search.py`:
   ```python
   class SpotifySearcher:
       def __init__(self, client_id, client_secret):
           # Initialize Spotipy with OAuth

       def search_tracks(self, query, limit=20):
           # Return: list of track results
           # Format: [{'title', 'artist', 'album', 'year', 'duration'}]

       def get_track_metadata(self, track_id):
           # Detailed metadata for single track
   ```

4. Run tests → VERIFY they PASS ✅

**Refactor Phase:**
5. Add OAuth token refresh logic
6. Handle rate limits (100 requests/second)
7. Add metadata normalization (Spotify → DB format)

**Integration:**
- Connect to `src/gui/tabs/search_tab.py` (created in Step 6)

---

### Step 4: Download Queue System (Days 4-5)

**Red Phase:**
1. Write all tests in `tests/test_download_queue.py` ✅
2. Write all tests in `tests/test_download_worker.py` ✅
3. Run tests → VERIFY they FAIL ✅

**Green Phase:**
4. Create `src/workers/download_worker.py`:
   ```python
   class DownloadWorker(QThread):
       progress = pyqtSignal(int)  # 0-100
       finished = pyqtSignal(dict)  # metadata
       error = pyqtSignal(str)

       def __init__(self, video_url, output_path):
           # Initialize yt-dlp options

       def run(self):
           # Execute download with progress callback
   ```

5. Create `src/core/download_queue.py`:
   ```python
   class DownloadQueue:
       def __init__(self, max_concurrent=50):
           # Manage concurrent downloads

       def add(self, video_url, metadata):
           # Add to queue

       def start(self):
           # Start processing queue

       def pause(self, download_id):
       def resume(self, download_id):
       def cancel(self, download_id):
   ```

6. Run tests → VERIFY they PASS ✅

**Refactor Phase:**
7. Optimize concurrent downloads (thread pool)
8. Add queue persistence (survive app restart)
9. Implement retry logic (failed downloads)

**Integration:**
- Connect to `src/gui/widgets/queue_widget.py` (created in Step 7)

---

### Step 5: MusicBrainz Auto-Complete (Days 6-7)

**Red Phase:**
1. Write all tests in `tests/test_metadata_autocomplete.py` ✅
2. Run tests → VERIFY they FAIL ✅

**Green Phase:**
3. Create `src/api/musicbrainz_client.py`:
   ```python
   class MusicBrainzClient:
       def __init__(self):
           # Set user agent

       def search_recording(self, title, artist=None):
           # Return: list of matches (up to 5)
           # Format: [{'title', 'artist', 'album', 'year', 'genre', 'album_art_url'}]

       def download_album_art(self, url, output_path):
           # Download cover art
   ```

4. Create `src/core/metadata_autocompleter.py`:
   ```python
   class MetadataAutocompleter:
       def autocomplete_single(self, song_id):
           # Search MusicBrainz, show 5 matches, user selects

       def autocomplete_batch(self, song_ids):
           # Batch mode: 100 songs at once
           # Use best match automatically (90%+ confidence)
   ```

5. Run tests → VERIFY they PASS ✅

**Refactor Phase:**
6. Add fuzzy matching for better accuracy
7. Implement confidence scoring (0-100%)
8. Add user override (manual selection)

**Integration:**
- Add context menu to library table: "Auto-complete Metadata"
- Connect to search tab (auto-complete new downloads)

---

### Step 6: Search Tab UI (Days 8-9)

**Red Phase:**
1. Write all tests in `tests/test_search_tab_ui.py` ✅
2. Run tests → VERIFY they FAIL ✅

**Green Phase:**
3. Create `src/gui/tabs/search_tab.py`:
   ```python
   class SearchTab(QWidget):
       """
       Layout:
       +----------------------------------+
       | [Search Box] [Buscar]           |
       | [x] YouTube  [x] Spotify         |
       +----------------------------------+
       | YouTube Results      | Spotify   |
       | - Song 1 [+]        | - Song 1  |
       | - Song 2 [+]        | - Song 2  |
       +----------------------------------+
       | Selected: 5 songs   [Add to Lib]|
       +----------------------------------+
       """

       def on_search_clicked(self):
           # Call YouTube + Spotify APIs concurrently

       def on_add_to_library_clicked(self):
           # Add selected songs to download queue
   ```

4. Run tests → VERIFY they PASS ✅

**Refactor Phase:**
5. Add loading indicators (API calls in progress)
6. Add result thumbnails/album art
7. Optimize UI performance (lazy loading results)

**Integration:**
- Add to main window as new tab
- Connect to download queue system

---

### Step 7: Queue Widget UI (Days 8-9)

**Tasks:**
1. Create `src/gui/widgets/queue_widget.py`:
   ```python
   class QueueWidget(QWidget):
       """
       Layout:
       +----------------------------------+
       | Queue (5 downloads)             |
       +----------------------------------+
       | ✓ Song 1.mp3                    |
       | ⏳ Song 2.mp3 [====    ] 60%    |
       | ⏸ Song 3.mp3 (paused)           |
       | 🕐 Song 4.mp3 (waiting)         |
       +----------------------------------+
       """

       def update_progress(self, download_id, percent):
           # Update progress bar in real-time
   ```

2. Integrate with main window (bottom panel or side panel)

**Acceptance:**
- ✅ Real-time progress updates
- ✅ Pause/resume/cancel buttons functional
- ✅ Queue persists between sessions

---

### Step 8: Playlist Downloader (Days 10-11)

**Red Phase:**
1. Write all tests in `tests/test_playlist_downloader.py` ✅
2. Run tests → VERIFY they FAIL ✅

**Green Phase:**
3. Create `src/core/playlist_downloader.py`:
   ```python
   class PlaylistDownloader:
       def extract_playlist_info(self, playlist_url):
           # Return: {'name', 'song_count', 'total_duration', 'songs': [...]}

       def download_playlist(self, playlist_url):
           # Add all songs to download queue
           # Auto-complete metadata for each
           # Insert into database
   ```

4. Add UI dialog: `src/gui/dialogs/playlist_dialog.py`
   - Input: URL field
   - Preview: Playlist info
   - Action: "Download All" button

5. Run tests → VERIFY they PASS ✅

**Refactor Phase:**
6. Add progress tracking (X of N songs downloaded)
7. Handle invalid URLs gracefully
8. Add option to create new playlist in DB

**Integration:**
- Add "Download Playlist" button to search tab
- Connect to download queue

---

### Step 9: Integration Testing (Day 12)

**End-to-End Tests:**
1. Search "The Beatles" → verify results < 2s
2. Select 10 songs → add to library
3. Download 50 songs concurrently → verify no UI lag
4. Paste playlist URL → download all automatically
5. Auto-complete metadata → verify 90%+ accuracy

**Performance Tests:**
- Load test: 100 simultaneous downloads
- Stress test: 1000+ song library with search active
- Network test: Handle disconnections gracefully

**Acceptance:**
- ✅ All tests PASS
- ✅ No crashes or freezes
- ✅ Performance meets criteria

---

### Step 10: Documentation & Cleanup (Day 13-14)

**Tasks:**
1. Update README.md with new features
2. Create user guide: `docs/guides/phase_4_user_guide.md`
3. Add API setup tutorial: `docs/guides/api_setup.md`
4. Update TRACKING.md
5. Update memory/shared/current_phase.md
6. Git commit (Phase 4 complete)

**Code cleanup:**
- Remove debug prints
- Add docstrings to all functions
- Run linter (black, flake8)
- Optimize imports

---

## 🔗 INTEGRATION POINTS

### External APIs:
- **YouTube Data API v3** → `src/api/youtube_search.py`
- **Spotify Web API** → `src/api/spotify_search.py`
- **MusicBrainz API** → `src/api/musicbrainz_client.py`

### Existing Systems:
- **SQLite Database** → Insert new songs after download
- **yt-dlp** → Download engine (already using in CLI)
- **Main Window** → Add search tab
- **Library Tab** → Add context menu "Auto-complete Metadata"

### New Components:
- `src/api/` → API clients
- `src/workers/download_worker.py` → Background downloads
- `src/core/download_queue.py` → Queue management
- `src/gui/tabs/search_tab.py` → Search UI
- `src/gui/widgets/queue_widget.py` → Queue UI
- `src/gui/dialogs/playlist_dialog.py` → Playlist downloader

---

## ✅ SUCCESS CRITERIA

### Phase 4 is COMPLETE when:

1. **Search Functionality:**
   - ✅ Search "The Beatles" → results from YouTube + Spotify in < 2 seconds
   - ✅ Select multiple songs → add to library with one click
   - ✅ Metadata auto-completed from API

2. **Download Queue:**
   - ✅ Download 50 songs simultaneously without UI lag
   - ✅ Progress bar updates in real-time
   - ✅ Can cancel/pause/resume downloads
   - ✅ Queue persists between app restarts

3. **Playlist Downloader:**
   - ✅ Paste YouTube playlist URL → auto-download all songs
   - ✅ Metadata auto-completed
   - ✅ Songs added to library automatically

4. **Metadata Auto-Complete:**
   - ✅ Right-click song → "Auto-complete Metadata"
   - ✅ Shows 5 matches from MusicBrainz
   - ✅ User selects correct one → metadata updated
   - ✅ Batch mode: 100 songs at once
   - ✅ 90%+ accuracy

5. **Code Quality:**
   - ✅ All tests passing (coverage > 80%)
   - ✅ No linter errors
   - ✅ Documentation complete

---

## 🚨 BLOCKERS & RISKS

### Potential Blockers:
- **API Rate Limits:**
  - YouTube: 10,000 requests/day (mitigate: cache results)
  - Spotify: 100 requests/second (mitigate: batch requests)
  - MusicBrainz: No limit (no mitigation needed)

- **Network Issues:**
  - Mitigate: Retry logic, timeout handling, offline mode

- **yt-dlp Updates:**
  - YouTube changes API → yt-dlp breaks
  - Mitigate: Keep yt-dlp updated, monitor repo

### Known Risks:
- **Copyright concerns:** App downloads from YouTube (user responsibility)
- **Metadata accuracy:** MusicBrainz not 100% accurate (user can override)
- **Disk space:** Large downloads (add disk space check)

---

## 📦 DEPENDENCIES

### Python Packages (add to requirements.txt):
```
google-api-python-client==2.100.0  # YouTube
spotipy==2.23.0                     # Spotify
musicbrainzngs==0.7.1               # MusicBrainz
yt-dlp==2023.10.13                  # Already installed (update if needed)
```

### API Credentials (store in ~/.claude/secrets/credentials.json):
```json
{
  "apis": {
    "youtube": {
      "api_key": "YOUR_YOUTUBE_API_KEY"
    },
    "spotify": {
      "client_id": "YOUR_SPOTIFY_CLIENT_ID",
      "client_secret": "YOUR_SPOTIFY_CLIENT_SECRET"
    }
  }
}
```

---

## 📝 SESSION NOTES

### November 12, 2025 - Plan Created
- Created this plan during methodology compliance audit
- All implementation steps follow TDD (Red → Green → Refactor)
- Estimated 2 weeks (14 days)
- Ready for Ricardo approval

**Next Action:** Get Ricardo approval → Begin Step 1 (API Setup)

---

## 🎯 APPROVAL STATUS

**Status:** ⏳ PENDING APPROVAL

**Ricardo:** Please review this plan and approve before I start coding.

**Changes requested:** (none yet)

---

**Created by:** NEXUS@CLI
**Maintained by:** Ricardo + NEXUS
**Last Updated:** November 12, 2025
**Format:** Markdown (optimized for Claude Code reading)
