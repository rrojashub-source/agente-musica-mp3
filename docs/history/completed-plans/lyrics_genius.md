# Feature #2: Lyrics Integration with Genius API

**Status:** In Progress
**Estimated Time:** 2-3 hours
**Priority:** High (Feature sequence #2/5)
**Created:** November 17, 2025

---

## 🎯 Objective

Implement automatic lyrics fetching and display using Genius API when a song is playing.

**User Experience:**
1. User plays a song
2. App automatically searches for lyrics on Genius
3. Lyrics tab shows synchronized lyrics
4. User can manually search if auto-search fails
5. Lyrics persist during playback

---

## 📋 Requirements

### Functional Requirements

**FR-1: Genius API Integration**
- ✅ Use `lyricsgenius` Python library (official client)
- ✅ Secure API token storage (OS keyring, like existing APIs)
- ✅ Error handling for rate limits, network errors
- ✅ Fallback when lyrics not found

**FR-2: Auto-Search on Song Change**
- ✅ Listen to song metadata changes (title + artist)
- ✅ Automatic search when new song plays
- ✅ Show loading state during search
- ✅ Cache lyrics to avoid repeated API calls

**FR-3: Lyrics Display Tab**
- ✅ Dedicated "Lyrics" tab in main window
- ✅ Scrollable text area with formatted lyrics
- ✅ Song metadata header (title, artist, album)
- ✅ Manual search button (if auto-search fails)
- ✅ "No lyrics found" placeholder

**FR-4: API Settings**
- ✅ Add Genius API token field to API Settings Dialog
- ✅ Inline instructions for getting Genius token
- ✅ Validation of token before saving

### Non-Functional Requirements

**NFR-1: Performance**
- Search completes in <3 seconds (typical)
- No UI blocking during search (background worker)
- Cache lyrics in memory (session-level)

**NFR-2: Security**
- API token encrypted in OS keyring (consistent with YouTube/Spotify)
- No hardcoded secrets

**NFR-3: User Experience**
- Professional UI matching existing tabs
- Clear error messages
- Graceful degradation (works without token)

---

## 🏗️ Architecture

### Component Structure

```
Feature: Lyrics Display
├─ src/api/genius_client.py          (NEW - Genius API client)
├─ src/gui/tabs/lyrics_tab.py        (NEW - Lyrics display tab)
├─ src/gui/widgets/now_playing_widget.py  (MODIFY - Add metadata signal)
├─ src/gui/dialogs/api_settings_dialog.py (MODIFY - Add Genius token field)
├─ src/main.py                       (MODIFY - Integrate lyrics tab)
└─ tests/test_genius_client.py       (NEW - TDD tests)
```

### Signal Flow

```
User plays song
    ↓
LibraryTab.play_song(song_info)
    ↓
NowPlayingWidget.load_song(song_info)
    ↓
NowPlayingWidget.song_metadata_changed.emit(song_info)  ← NEW SIGNAL
    ↓
LyricsTab._on_song_changed(song_info)
    ↓
LyricsTab._search_lyrics(title, artist)
    ↓
GeniusClient.search_lyrics(title, artist)
    ↓
Genius API → Return lyrics
    ↓
LyricsTab.display_lyrics(lyrics_text)
```

### Data Flow

**Input:**
- `song_info` dict with keys: `title`, `artist`, `album`, `file_path`

**Processing:**
1. Extract `title` and `artist` from `song_info`
2. Query Genius API: `/search?q={artist} {title}`
3. Get first result's lyrics URL
4. Fetch lyrics from Genius page (lyricsgenius handles this)
5. Cache in memory: `{(title, artist): lyrics_text}`

**Output:**
- Formatted lyrics text displayed in scrollable QTextEdit

---

## 🔧 Implementation Plan (TDD)

### Phase 1: Genius API Client (30 min)

**File:** `src/api/genius_client.py`

**TDD Steps:**

**RED - Write Tests First:**
```python
# tests/test_genius_client.py

def test_01_client_initialization():
    """GeniusClient should initialize with token"""

def test_02_search_lyrics_success():
    """Should return lyrics for valid song"""

def test_03_search_lyrics_not_found():
    """Should return None when lyrics not found"""

def test_04_search_lyrics_no_token():
    """Should raise error when no token provided"""

def test_05_cache_lyrics():
    """Should cache lyrics to avoid repeated API calls"""
```

**GREEN - Implement:**
```python
# src/api/genius_client.py

import lyricsgenius
import logging
from typing import Optional, Tuple

class GeniusClient:
    """Client for Genius API lyrics fetching"""

    def __init__(self, access_token: str):
        """Initialize with Genius API token"""
        self.genius = lyricsgenius.Genius(access_token)
        self.genius.verbose = False  # Disable console output
        self.genius.remove_section_headers = True  # Clean lyrics
        self._cache = {}  # {(title, artist): lyrics}

    def search_lyrics(self, title: str, artist: str) -> Optional[str]:
        """
        Search for lyrics on Genius

        Args:
            title: Song title
            artist: Artist name

        Returns:
            Lyrics text or None if not found
        """
        # Check cache first
        cache_key = (title.lower(), artist.lower())
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Search Genius
            song = self.genius.search_song(title, artist)

            if song and song.lyrics:
                lyrics = song.lyrics
                self._cache[cache_key] = lyrics
                return lyrics

            return None

        except Exception as e:
            logger.error(f"Genius API error: {e}")
            return None
```

**REFACTOR:**
- Add timeout for API calls
- Add retry logic for transient errors
- Add error types (NotFoundError, RateLimitError, NetworkError)

---

### Phase 2: Lyrics Display Tab (45 min)

**File:** `src/gui/tabs/lyrics_tab.py`

**TDD Steps:**

**RED - Write Tests:**
```python
# tests/test_lyrics_tab.py

def test_01_tab_initialization():
    """LyricsTab should initialize with empty state"""

def test_02_display_lyrics():
    """Should display lyrics text in text area"""

def test_03_show_loading_state():
    """Should show loading message during search"""

def test_04_show_not_found_message():
    """Should show 'not found' when lyrics unavailable"""

def test_05_manual_search():
    """Manual search button should trigger search"""
```

**GREEN - Implement:**
```python
# src/gui/tabs/lyrics_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

class LyricsSearchWorker(QThread):
    """Background worker for lyrics search"""
    finished = pyqtSignal(str)  # lyrics_text
    error = pyqtSignal(str)  # error_message

    def __init__(self, genius_client, title, artist):
        super().__init__()
        self.genius_client = genius_client
        self.title = title
        self.artist = artist

    def run(self):
        try:
            lyrics = self.genius_client.search_lyrics(self.title, self.artist)
            if lyrics:
                self.finished.emit(lyrics)
            else:
                self.error.emit("Lyrics not found")
        except Exception as e:
            self.error.emit(str(e))


class LyricsTab(QWidget):
    """Tab for displaying song lyrics"""

    def __init__(self, genius_client=None):
        super().__init__()
        self.genius_client = genius_client
        self.current_song = None
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Header with song info
        self.header_label = QLabel("No song playing")
        self.header_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.header_label)

        # Lyrics text area
        self.lyrics_text = QTextEdit()
        self.lyrics_text.setReadOnly(True)
        self.lyrics_text.setPlaceholderText("Play a song to see lyrics...")
        font = QFont("Courier New", 11)
        self.lyrics_text.setFont(font)
        layout.addWidget(self.lyrics_text)

        # Bottom controls
        controls_layout = QHBoxLayout()

        self.search_button = QPushButton("🔍 Manual Search")
        self.search_button.clicked.connect(self._on_manual_search)
        controls_layout.addWidget(self.search_button)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        self.setLayout(layout)

    def on_song_changed(self, song_info: dict):
        """Called when a new song starts playing"""
        self.current_song = song_info

        # Update header
        title = song_info.get('title', 'Unknown')
        artist = song_info.get('artist', 'Unknown Artist')
        self.header_label.setText(f"{title} - {artist}")

        # Auto-search lyrics
        self._search_lyrics(title, artist)

    def _search_lyrics(self, title: str, artist: str):
        """Search for lyrics (background thread)"""
        if not self.genius_client:
            self.lyrics_text.setPlainText("Genius API not configured.\n\nGo to Settings → API Setup to add your Genius token.")
            return

        # Show loading state
        self.lyrics_text.setPlainText("⏳ Searching for lyrics...")
        self.search_button.setEnabled(False)

        # Start background search
        self._worker = LyricsSearchWorker(self.genius_client, title, artist)
        self._worker.finished.connect(self._on_lyrics_found)
        self._worker.error.connect(self._on_lyrics_error)
        self._worker.start()

    def _on_lyrics_found(self, lyrics: str):
        """Display found lyrics"""
        self.lyrics_text.setPlainText(lyrics)
        self.search_button.setEnabled(True)

    def _on_lyrics_error(self, error: str):
        """Show error message"""
        self.lyrics_text.setPlainText(f"❌ {error}\n\nTry manual search or check API settings.")
        self.search_button.setEnabled(True)

    def _on_manual_search(self):
        """Manual search triggered by button"""
        if self.current_song:
            title = self.current_song.get('title', '')
            artist = self.current_song.get('artist', '')
            self._search_lyrics(title, artist)
```

**REFACTOR:**
- Add scroll position preservation
- Add font size controls
- Add "Copy to clipboard" button

---

### Phase 3: Integration (45 min)

**3.1 Modify NowPlayingWidget (10 min)**

**File:** `src/gui/widgets/now_playing_widget.py`

Add new signal:
```python
# Line 59 (after song_loaded signal)
song_metadata_changed = pyqtSignal(dict)  # Emits full song_info
```

Emit in `load_song()`:
```python
# Line 256 (after song_loaded.emit)
self.song_metadata_changed.emit(song_info)
```

**3.2 Modify API Settings Dialog (20 min)**

**File:** `src/gui/dialogs/api_settings_dialog.py`

Add Genius tab:
```python
# In __init__ after Spotify tab
genius_tab = self._create_genius_tab()
tabs.addTab(genius_tab, "Genius API")
```

Add `_create_genius_tab()` method:
```python
def _create_genius_tab(self):
    """Create Genius API settings tab"""
    widget = QWidget()
    layout = QVBoxLayout()

    # Instructions
    info_text = QLabel(
        "<b>Get your Genius API token:</b><br>"
        "1. Go to <a href='https://genius.com/api-clients'>genius.com/api-clients</a><br>"
        "2. Sign up (free account)<br>"
        "3. Create 'New API Client'<br>"
        "4. Generate 'Client Access Token'<br>"
        "5. Paste token below"
    )
    info_text.setOpenExternalLinks(True)
    info_text.setWordWrap(True)
    layout.addWidget(info_text)

    # Token field
    form_layout = QFormLayout()
    self.genius_token_input = QLineEdit()
    self.genius_token_input.setEchoMode(QLineEdit.EchoMode.Password)
    self.genius_token_input.setPlaceholderText("Paste your Genius Client Access Token")
    form_layout.addRow("Access Token:", self.genius_token_input)

    layout.addLayout(form_layout)
    layout.addStretch()

    widget.setLayout(layout)
    return widget
```

Add keyring save/load in `_save_credentials()` and `_load_credentials()`:
```python
# Save
if self.genius_token_input.text().strip():
    keyring.set_password("nexus_music", "genius_token", self.genius_token_input.text().strip())

# Load
genius_token = keyring.get_password("nexus_music", "genius_token")
if genius_token:
    self.genius_token_input.setText(genius_token)
```

**3.3 Modify main.py (15 min)**

**File:** `src/main.py`

Import GeniusClient and LyricsTab:
```python
from api.genius_client import GeniusClient
from gui.tabs.lyrics_tab import LyricsTab
```

Initialize GeniusClient in `__init__`:
```python
# After SearchTab initialization
try:
    genius_token = keyring.get_password("nexus_music", "genius_token")
    if genius_token:
        self.genius_client = GeniusClient(genius_token)
        logger.info("Genius client initialized")
    else:
        self.genius_client = None
        logger.warning("Genius API token not found")
except Exception as e:
    logger.error(f"Failed to initialize Genius client: {e}")
    self.genius_client = None
```

Create LyricsTab:
```python
# After search_tab
self.lyrics_tab = LyricsTab(self.genius_client)
logger.info("Lyrics tab loaded")
```

Add to tabs:
```python
self.tabs.addTab(self.lyrics_tab, "📝 Lyrics")
```

Connect signal:
```python
# After now_playing connections
self.now_playing.song_metadata_changed.connect(self.lyrics_tab.on_song_changed)
```

---

### Phase 4: Testing & Validation (30 min)

**Manual Testing Checklist:**

1. ✅ **API Setup:**
   - Open Settings → API Setup → Genius tab
   - Instructions visible and clear
   - Paste token, save, reopen app → token persists

2. ✅ **Auto-Search:**
   - Play a popular song (e.g., "Bohemian Rhapsody - Queen")
   - Switch to Lyrics tab
   - Verify lyrics appear within 3 seconds
   - Verify header shows correct song info

3. ✅ **Not Found:**
   - Play obscure/instrumental song
   - Verify "not found" message appears
   - Verify manual search button enabled

4. ✅ **Manual Search:**
   - Click "Manual Search" button
   - Verify re-search happens
   - Verify loading state shown

5. ✅ **No Token:**
   - Remove Genius token from settings
   - Restart app
   - Play song
   - Verify friendly message about missing token

6. ✅ **Performance:**
   - Play 5 songs in sequence
   - Verify no UI blocking
   - Verify cached songs load instantly

**Automated Tests:**

Run full test suite:
```bash
pytest tests/test_genius_client.py -v
pytest tests/test_lyrics_tab.py -v
```

Expected: All tests pass (10+ tests)

---

## 📦 Dependencies

**New Dependency:**
```bash
pip install lyricsgenius
```

Add to `requirements.txt`:
```
lyricsgenius>=3.0.1
```

**Genius API:**
- Free tier (no credit card required)
- Rate limit: Unknown (research needed)
- Documentation: https://docs.genius.com/

---

## 🎨 UI Design

**Lyrics Tab Layout:**
```
┌─────────────────────────────────────┐
│ 🎵 Bohemian Rhapsody - Queen        │  ← Header (bold, 14pt)
├─────────────────────────────────────┤
│                                     │
│ Is this the real life?              │
│ Is this just fantasy?               │
│ Caught in a landslide               │  ← Lyrics (Courier New, 11pt)
│ No escape from reality              │     Scrollable, read-only
│                                     │
│ ...                                 │
│                                     │
├─────────────────────────────────────┤
│ [🔍 Manual Search]        [Copy]   │  ← Controls
└─────────────────────────────────────┘
```

**Theme Integration:**
- Inherit from current theme (dark/light)
- Use theme colors for text area background
- Professional monospace font for lyrics

---

## 🚨 Error Handling

**Scenarios:**

1. **No Token:** Show message "Configure Genius API in Settings"
2. **Network Error:** Show "Connection failed, try again"
3. **Not Found:** Show "Lyrics not found for this song"
4. **Rate Limit:** Show "Too many requests, wait a moment"
5. **Invalid Token:** Show "Invalid API token, check Settings"

**Logging:**
```python
logger.info(f"Searching lyrics: {title} - {artist}")
logger.info(f"Lyrics found ({len(lyrics)} chars)")
logger.warning(f"Lyrics not found: {title} - {artist}")
logger.error(f"Genius API error: {e}")
```

---

## 📊 Success Metrics

**Feature Complete When:**
- ✅ Genius API integration working (lyricsgenius installed, token stored)
- ✅ Auto-search triggers on song change
- ✅ Lyrics display correctly in dedicated tab
- ✅ Manual search works as fallback
- ✅ API Settings includes Genius token field
- ✅ Error handling covers all scenarios
- ✅ No UI blocking (background worker)
- ✅ Tests pass (10+ tests, 100% coverage)
- ✅ User can play 5 songs and see lyrics for each

**Performance:**
- Search completes <3s for 90% of songs
- Cached songs load <100ms
- No memory leaks after 20+ song changes

---

## 🔮 Future Enhancements (Phase 7+)

**Nice to Have (Later):**
- Synced lyrics (line-by-line with playback position)
- Translation button (show lyrics in different languages)
- Lyrics editing (crowdsourced corrections)
- Export lyrics to .lrc file
- Search history (recently searched songs)
- Favorite lyrics bookmarks

---

## 📝 Notes

**Design Decisions:**

1. **Why lyricsgenius?**
   - Official Python client for Genius API
   - Well-maintained (updated 2024)
   - Handles authentication, pagination, rate limiting
   - Cleaner than manual API calls

2. **Why separate signal for metadata?**
   - Existing `song_loaded` emits file_path (str)
   - Lyrics needs full metadata (dict)
   - Avoids breaking existing waveform integration
   - More semantic clarity

3. **Why background worker?**
   - API calls can take 1-3 seconds
   - Prevents UI freezing
   - Allows "loading" state
   - Professional UX

4. **Why in-memory cache?**
   - Avoid repeated API calls for same song
   - Fast lookup (<1ms)
   - Session-scoped (cleared on app restart)
   - Simple implementation

**Risks:**

1. **Genius rate limiting:** Unknown limits, might hit during heavy testing
   - Mitigation: Implement exponential backoff

2. **Lyrics accuracy:** Genius relies on crowdsourced data
   - Mitigation: Manual search fallback

3. **API changes:** Genius API might change endpoints
   - Mitigation: Use official lyricsgenius library (abstracts API)

---

**Estimated Total Time:** 2-3 hours
**Priority:** High (commercial feature, user-requested)
**Complexity:** Medium (API integration + UI)

**Last Updated:** November 17, 2025
