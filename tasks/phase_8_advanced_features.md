# Phase 8: Advanced Features & Premium Experience

**Version:** 1.0
**Created:** November 13, 2025
**Status:** PLANNING (awaiting Ricardo approval)
**Estimated Duration:** 25-30 days (can be split into sub-phases)

---

## 🎯 Mission

Transform AGENTE_MUSICA_MP3 into a premium-tier music player with advanced features comparable to foobar2000, MusicBee, and Poweramp.

**Target Users:**
- Audiophiles (advanced audio controls)
- Power users (analytics, automation)
- Casual users (polish, themes)
- Multi-device users (cloud sync)

---

## 📊 Features Overview (14 Features Proposed)

### **Priority Tiers**

| Priority | Features | Impact | Complexity | Days |
|----------|----------|--------|------------|------|
| **HIGH** | Equalizer, Crossfade, Lyrics, ReplayGain | 🔥 High | Medium | 12-15 |
| **MEDIUM** | Scrobbling, Album Art, Smart Shuffle, Sleep Timer | ⭐ Medium | Low-Medium | 8-10 |
| **LOW** | Format Converter, Cloud Sync, Themes, Stats | ✨ Nice-to-have | High | 10-15 |

**Recommendation:** Implement HIGH priority first (Phase 8A), then MEDIUM (Phase 8B), then LOW (Phase 8C)

---

## 🔥 HIGH PRIORITY FEATURES (Phase 8A: 12-15 days)

### **Feature 8.1: 10-Band Graphic Equalizer (3-4 days)**

**Description:** Professional audio equalizer with presets and custom curves

**User Value:**
- Audiophiles can fine-tune audio output
- Presets for different genres (Rock, Jazz, Classical, etc.)
- Compensate for headphone/speaker characteristics

**Technical Approach:**
- **Tech Stack:**
  - `pedalboard` (Spotify's audio effects library)
  - OR `scipy.signal` (IIR/FIR filters)
  - PyQt6 for GUI (sliders + frequency visualization)
- **Architecture:**
  - `src/core/equalizer.py` - DSP engine (10 bands: 32Hz-16kHz)
  - `src/gui/widgets/equalizer_widget.py` - GUI with sliders
  - Integration with `audio_player.py` (real-time processing)
- **Features:**
  - 10 frequency bands: 32Hz, 64Hz, 125Hz, 250Hz, 500Hz, 1kHz, 2kHz, 4kHz, 8kHz, 16kHz
  - ±12 dB gain per band
  - 10+ presets (Rock, Pop, Jazz, Classical, Vocal, Bass Boost, etc.)
  - Custom presets (save/load)
  - Bypass button
  - Real-time preview

**Implementation Steps:**
1. Research: Test pedalboard vs scipy performance
2. Red Phase: Create `tests/test_equalizer.py` (15 tests)
3. Green Phase: Implement DSP engine
4. Red Phase: Create `tests/test_equalizer_widget.py` (12 tests)
5. Green Phase: Implement GUI
6. Integration: Connect to AudioPlayer
7. Testing: Verify audio quality (no clipping, no distortion)

**Success Criteria:**
- ✅ 10 bands operational (-12 to +12 dB)
- ✅ 10+ presets available
- ✅ Real-time processing (<10ms latency)
- ✅ No audio artifacts (clipping, distortion)
- ✅ 27 tests passing

---

### **Feature 8.2: Crossfade & Gapless Playback (2-3 days)**

**Description:** Smooth transitions between songs

**User Value:**
- DJ-style crossfade for party mode
- Gapless playback for live albums, classical music
- Professional listening experience

**Technical Approach:**
- **Tech Stack:**
  - pygame.mixer enhancements (dual channel mixing)
  - OR switch to `python-vlc` (native crossfade support)
- **Architecture:**
  - Enhance `src/core/audio_player.py` with dual buffer
  - `src/core/crossfade_engine.py` - mixing algorithm
  - Settings in `NowPlayingWidget` (crossfade duration slider)
- **Features:**
  - Crossfade: 0-10 seconds (configurable)
  - Gapless: Zero-gap between tracks
  - Fade types: Linear, logarithmic, S-curve
  - Per-playlist setting (crossfade ON/OFF)

**Implementation Steps:**
1. Research: pygame.mixer vs python-vlc for crossfade
2. Red Phase: Create `tests/test_crossfade.py` (10 tests)
3. Green Phase: Implement dual-buffer audio engine
4. Integration: Update AudioPlayer + LibraryTab
5. GUI: Add crossfade slider in NowPlayingWidget
6. Testing: Verify smooth transitions

**Success Criteria:**
- ✅ Crossfade 0-10s operational
- ✅ Gapless playback working
- ✅ No audio pops/clicks
- ✅ 10 tests passing

---

### **Feature 8.3: Synchronized Lyrics Display (3-4 days)**

**Description:** Real-time lyrics synchronized with playback

**User Value:**
- Karaoke experience
- Language learning
- Enhanced engagement

**Technical Approach:**
- **Tech Stack:**
  - LRC file parser (plain text format)
  - Lyrics APIs: Genius, Musixmatch, LRCLIB
  - PyQt6 QTextEdit with scrolling
- **Architecture:**
  - `src/core/lyrics_fetcher.py` - API client
  - `src/core/lrc_parser.py` - LRC file parser
  - `src/gui/widgets/lyrics_widget.py` - Scrolling display
  - Integration with `NowPlayingWidget` (position tracking)
- **Features:**
  - Auto-fetch lyrics (Genius/Musixmatch/LRCLIB)
  - LRC file support (manual import)
  - Synchronized scrolling (highlight current line)
  - Edit lyrics manually
  - Save to LRC file

**Implementation Steps:**
1. Research: Compare lyrics APIs (free tier limits)
2. Red Phase: Create `tests/test_lyrics_fetcher.py` (8 tests)
3. Green Phase: Implement API client
4. Red Phase: Create `tests/test_lrc_parser.py` (6 tests)
5. Green Phase: Implement LRC parser
6. Red Phase: Create `tests/test_lyrics_widget.py` (10 tests)
7. Green Phase: Implement GUI with sync
8. Integration: Connect to AudioPlayer position updates

**Success Criteria:**
- ✅ Auto-fetch from 1+ API
- ✅ LRC parsing working
- ✅ Real-time sync (<100ms accuracy)
- ✅ 24 tests passing

---

### **Feature 8.4: ReplayGain Normalization (2-3 days)**

**Description:** Automatic loudness normalization (EBU R128 standard)

**User Value:**
- Consistent volume across tracks/albums
- No manual volume adjustments
- Professional loudness standard (LUFS)

**Technical Approach:**
- **Tech Stack:**
  - `r128gain` (ReplayGain 2.0 scanner)
  - `pyloudnorm` (ITU BS.1770-4 loudness meter)
  - `mutagen` (write REPLAYGAIN_* tags)
- **Architecture:**
  - `src/core/replaygain_scanner.py` - Loudness analysis
  - `src/gui/tabs/replaygain_tab.py` - Batch scanner GUI
  - Integration with `AudioPlayer` (apply gain on playback)
- **Features:**
  - Scan tracks/albums for loudness (LUFS)
  - Write ReplayGain tags (TRACK_GAIN, ALBUM_GAIN)
  - Apply gain on playback (prevent clipping)
  - Batch processing (QThread worker)
  - Album vs Track mode

**Implementation Steps:**
1. Research: r128gain vs pyloudnorm (performance)
2. Red Phase: Create `tests/test_replaygain_scanner.py` (10 tests)
3. Green Phase: Implement scanner engine
4. Red Phase: Create `tests/test_replaygain_tab.py` (8 tests)
5. Green Phase: Implement batch GUI
6. Integration: Update AudioPlayer to read/apply gain
7. Testing: Verify no clipping, consistent loudness

**Success Criteria:**
- ✅ Scan 100 songs in <5 minutes
- ✅ Write ReplayGain tags correctly
- ✅ Playback applies gain (±18 dB range)
- ✅ 18 tests passing

---

## ⭐ MEDIUM PRIORITY FEATURES (Phase 8B: 8-10 days)

### **Feature 8.5: Last.fm Scrobbling (2 days)**

**Description:** Track listening history to Last.fm

**User Value:**
- Build listening statistics
- Discover similar artists
- Social sharing

**Technical Approach:**
- **Tech Stack:** `pylast` (Last.fm Python API)
- **Architecture:**
  - `src/api/lastfm_client.py` - API wrapper
  - Integration with `AudioPlayer` (scrobble on 50% played)
  - Settings dialog for credentials
- **Features:**
  - Auto-scrobble (50% or 4 minutes)
  - Now playing update
  - Love/unlove tracks
  - View recent scrobbles

**Implementation Steps:**
1. Red Phase: Create `tests/test_lastfm_client.py` (10 tests)
2. Green Phase: Implement API client
3. Integration: Hook into AudioPlayer position tracking
4. GUI: Add Last.fm settings dialog
5. Testing: Mock API calls

**Success Criteria:**
- ✅ Scrobble on 50% played
- ✅ Now playing updates
- ✅ 10 tests passing

---

### **Feature 8.6: Album Art Downloader (2 days)**

**Description:** Auto-download missing album art

**User Value:**
- Complete library visually
- Professional appearance
- No manual searching

**Technical Approach:**
- **Tech Stack:**
  - MusicBrainz CoverArtArchive API
  - Last.fm API (fallback)
  - `Pillow` (image processing)
- **Architecture:**
  - `src/core/album_art_fetcher.py` - API client
  - `src/gui/tabs/album_art_tab.py` - Batch downloader
  - Integration with database (store art path)
- **Features:**
  - Auto-download from MusicBrainz/Last.fm
  - Batch processing (missing art only)
  - Multiple sizes (thumbnail 100x100, full 500x500)
  - Embed in MP3 (ID3 APIC frame)

**Implementation Steps:**
1. Red Phase: Create `tests/test_album_art_fetcher.py` (8 tests)
2. Green Phase: Implement API client
3. Red Phase: Create `tests/test_album_art_tab.py` (6 tests)
4. Green Phase: Implement batch GUI
5. Integration: Update database schema (album_art_path)
6. Testing: Verify image quality

**Success Criteria:**
- ✅ Download from 2+ sources
- ✅ Batch 100 albums in <5 minutes
- ✅ Embed in MP3 correctly
- ✅ 14 tests passing

---

### **Feature 8.7: Smart Shuffle / Auto-DJ (2-3 days)**

**Description:** Intelligent shuffle avoiding artist/album repetition

**User Value:**
- Better randomization
- Avoid hearing same artist twice in a row
- Balanced library rotation

**Technical Approach:**
- **Tech Stack:**
  - Custom algorithm (weighted randomization)
  - pandas (library analysis)
- **Architecture:**
  - `src/core/smart_shuffle.py` - Shuffle algorithm
  - Integration with PlaylistManager
  - Settings: artist separation (min 5 songs)
- **Features:**
  - Avoid same artist for N songs (configurable)
  - Balance album/genre distribution
  - Favor highly rated songs (if ratings exist)
  - History tracking (last 50 songs)

**Implementation Steps:**
1. Red Phase: Create `tests/test_smart_shuffle.py` (12 tests)
2. Green Phase: Implement algorithm
3. Integration: Update PlaylistManager
4. GUI: Add shuffle mode selector (Random vs Smart)
5. Testing: Verify distribution quality

**Success Criteria:**
- ✅ No artist repeats in 5 songs
- ✅ Genre distribution balanced
- ✅ 12 tests passing

---

### **Feature 8.8: Sleep Timer (1 day)**

**Description:** Auto-stop playback after duration

**User Value:**
- Fall asleep to music
- Auto-shutdown after duration
- Fade-out option

**Technical Approach:**
- **Tech Stack:** PyQt6 QTimer
- **Architecture:**
  - `src/core/sleep_timer.py` - Timer logic
  - GUI in `NowPlayingWidget` (timer button)
- **Features:**
  - Preset durations: 15m, 30m, 1h, 2h
  - Custom duration
  - Fade-out last 10 seconds
  - Visual countdown

**Implementation Steps:**
1. Red Phase: Create `tests/test_sleep_timer.py` (8 tests)
2. Green Phase: Implement timer logic
3. GUI: Add timer button + dialog
4. Integration: Connect to AudioPlayer
5. Testing: Verify timer accuracy

**Success Criteria:**
- ✅ Timer accuracy ±1 second
- ✅ Fade-out smooth
- ✅ 8 tests passing

---

## ✨ LOW PRIORITY FEATURES (Phase 8C: 10-15 days)

### **Feature 8.9: Format Converter (3-4 days)**

**Description:** Convert between MP3/FLAC/WAV/OGG

**User Value:**
- Prepare files for different devices
- Convert lossy ↔ lossless
- Batch conversion

**Technical Approach:**
- **Tech Stack:**
  - `ffmpeg` (via subprocess)
  - `pydub` (Python wrapper)
- **Architecture:**
  - `src/core/format_converter.py` - Converter engine
  - `src/gui/tabs/converter_tab.py` - Batch GUI
- **Features:**
  - Formats: MP3, FLAC, WAV, OGG, M4A
  - Bitrate selection (128-320 kbps)
  - Sample rate (44.1kHz, 48kHz)
  - Batch processing
  - Progress tracking

**Implementation Steps:**
1. Red Phase: Create `tests/test_format_converter.py` (10 tests)
2. Green Phase: Implement converter
3. Red Phase: Create `tests/test_converter_tab.py` (8 tests)
4. Green Phase: Implement GUI
5. Testing: Verify audio quality

**Success Criteria:**
- ✅ 5+ formats supported
- ✅ Convert 100 files in <10 minutes
- ✅ 18 tests passing

---

### **Feature 8.10: Cloud Sync (4-5 days)**

**Description:** Backup/sync library to cloud (Google Drive, Dropbox)

**User Value:**
- Multi-device access
- Automatic backup
- Disaster recovery

**Technical Approach:**
- **Tech Stack:**
  - `google-api-python-client` (Google Drive)
  - `dropbox` (Dropbox SDK)
- **Architecture:**
  - `src/cloud/sync_engine.py` - Sync logic
  - `src/gui/dialogs/cloud_settings_dialog.py` - OAuth setup
- **Features:**
  - One-way backup (local → cloud)
  - Two-way sync (bidirectional)
  - Conflict resolution
  - Selective sync (playlists only)

**Implementation Steps:**
1. Research: Google Drive vs Dropbox API
2. Red Phase: Create `tests/test_sync_engine.py` (12 tests)
3. Green Phase: Implement sync logic
4. OAuth: Setup Google/Dropbox authentication
5. GUI: Settings dialog
6. Testing: Mock cloud API calls

**Success Criteria:**
- ✅ Backup 1,000 songs to cloud
- ✅ Sync database + metadata
- ✅ 12 tests passing

---

### **Feature 8.11: Themes & Skins (2-3 days)**

**Description:** Customizable UI themes (dark, light, custom colors)

**User Value:**
- Personalization
- Reduce eye strain (dark mode)
- Match OS theme

**Technical Approach:**
- **Tech Stack:** PyQt6 QSS (Qt Stylesheets)
- **Architecture:**
  - `src/themes/` - QSS files
  - `src/gui/theme_manager.py` - Theme loader
- **Features:**
  - 5+ built-in themes (Dark, Light, Nord, Dracula, Monokai)
  - Custom themes (user-created QSS)
  - Real-time preview
  - Save theme preference

**Implementation Steps:**
1. Research: PyQt6 QSS best practices
2. Create 5 QSS themes
3. Red Phase: Create `tests/test_theme_manager.py` (6 tests)
4. Green Phase: Implement theme loader
5. GUI: Theme selector in settings
6. Testing: Verify all widgets themed

**Success Criteria:**
- ✅ 5+ themes available
- ✅ Real-time switching
- ✅ 6 tests passing

---

### **Feature 8.12: Listening Statistics (2-3 days)**

**Description:** Track play counts, listening time, top artists

**User Value:**
- Discover listening habits
- Year-in-review stats
- Top songs/artists/albums

**Technical Approach:**
- **Tech Stack:**
  - SQLite (new `listening_history` table)
  - pandas (data analysis)
  - matplotlib/pyqtgraph (charts)
- **Architecture:**
  - `src/database/migrations/008_listening_history.sql`
  - `src/core/stats_analyzer.py` - Analytics engine
  - `src/gui/tabs/stats_tab.py` - Charts/graphs
- **Features:**
  - Play count per song
  - Total listening time
  - Top 10 artists/albums/songs
  - Listening trends (per week/month)
  - Export to CSV

**Implementation Steps:**
1. Red Phase: Create migration + tests (8 tests)
2. Green Phase: Implement history tracking
3. Red Phase: Create `tests/test_stats_tab.py` (10 tests)
4. Green Phase: Implement charts
5. Integration: Hook into AudioPlayer
6. Testing: Verify data accuracy

**Success Criteria:**
- ✅ History tracking operational
- ✅ Charts render correctly
- ✅ 18 tests passing

---

### **Feature 8.13: Spotify Playlist Import (2 days)**

**Description:** Import playlists from Spotify account

**User Value:**
- Migrate from Spotify
- Discover new music
- Match songs in library

**Technical Approach:**
- **Tech Stack:** `spotipy` (Spotify API)
- **Architecture:**
  - `src/api/spotify_importer.py` - Import logic
  - `src/gui/dialogs/spotify_import_dialog.py` - OAuth + selection
- **Features:**
  - OAuth login
  - List user playlists
  - Select playlists to import
  - Match songs in library (or download)
  - Import as .m3u8

**Implementation Steps:**
1. Red Phase: Create `tests/test_spotify_importer.py` (10 tests)
2. Green Phase: Implement OAuth + import
3. GUI: Import dialog
4. Integration: Create playlists in database
5. Testing: Mock Spotify API

**Success Criteria:**
- ✅ Import 10+ playlists
- ✅ Match 80%+ songs
- ✅ 10 tests passing

---

### **Feature 8.14: Advanced Tag Editor (1-2 days)**

**Description:** Bulk edit metadata (tags, album art, lyrics)

**User Value:**
- Fix incorrect metadata
- Bulk edit artist/album
- Add missing info

**Technical Approach:**
- **Tech Stack:** `mutagen` (extended usage)
- **Architecture:**
  - `src/gui/dialogs/tag_editor_dialog.py` - Edit UI
  - Integration with LibraryTab (multi-select)
- **Features:**
  - Edit all ID3 tags (title, artist, album, year, genre, etc.)
  - Bulk edit (apply to multiple songs)
  - Embed album art
  - Embed lyrics
  - Auto-fill from MusicBrainz

**Implementation Steps:**
1. Red Phase: Create `tests/test_tag_editor.py` (8 tests)
2. Green Phase: Implement tag editor
3. GUI: Edit dialog
4. Integration: Multi-select in LibraryTab
5. Testing: Verify tag write correctness

**Success Criteria:**
- ✅ Edit all ID3v2.3 tags
- ✅ Bulk edit 100+ songs
- ✅ 8 tests passing

---

## 📋 Implementation Roadmap

### **Phase 8A: HIGH Priority (12-15 days) - RECOMMEND STARTING HERE**

| Week | Features | Tests | Days |
|------|----------|-------|------|
| Week 1 | Equalizer (8.1) | 27 | 3-4 |
| Week 1-2 | Crossfade (8.2) | 10 | 2-3 |
| Week 2 | Lyrics (8.3) | 24 | 3-4 |
| Week 2-3 | ReplayGain (8.4) | 18 | 2-3 |
| **Total** | **4 features** | **79 tests** | **12-15 days** |

### **Phase 8B: MEDIUM Priority (8-10 days) - AFTER 8A APPROVAL**

| Week | Features | Tests | Days |
|------|----------|-------|------|
| Week 3 | Scrobbling (8.5) | 10 | 2 |
| Week 3-4 | Album Art (8.6) | 14 | 2 |
| Week 4 | Smart Shuffle (8.7) | 12 | 2-3 |
| Week 4 | Sleep Timer (8.8) | 8 | 1 |
| **Total** | **4 features** | **44 tests** | **8-10 days** |

### **Phase 8C: LOW Priority (10-15 days) - OPTIONAL**

| Week | Features | Tests | Days |
|------|----------|-------|------|
| Week 5 | Format Converter (8.9) | 18 | 3-4 |
| Week 5-6 | Cloud Sync (8.10) | 12 | 4-5 |
| Week 6 | Themes (8.11) | 6 | 2-3 |
| Week 6-7 | Statistics (8.12) | 18 | 2-3 |
| Week 7 | Spotify Import (8.13) | 10 | 2 |
| Week 7 | Tag Editor (8.14) | 8 | 1-2 |
| **Total** | **6 features** | **72 tests** | **10-15 days** |

---

## 🎯 Success Metrics

### **Test Coverage Goals**

| Phase | Features | New Tests | Cumulative Tests |
|-------|----------|-----------|------------------|
| Current (Phase 7) | 7 phases | 286 | 286/306 (93.5%) |
| Phase 8A | +4 features | +79 | 365/385 (95%) |
| Phase 8B | +4 features | +44 | 409/429 (95%) |
| Phase 8C | +6 features | +72 | 481/501 (96%) |
| **Total Phase 8** | **+14 features** | **+195 tests** | **481/501 (96%)** |

### **Performance Targets**

- ✅ Equalizer: <10ms latency
- ✅ Crossfade: No audio pops/clicks
- ✅ Lyrics: <100ms sync accuracy
- ✅ ReplayGain: 100 songs scanned in <5 minutes
- ✅ Cloud sync: 1,000 songs uploaded in <30 minutes

---

## 🛠️ Technical Stack Summary

**New Dependencies:**

```python
# Phase 8A (HIGH)
pedalboard>=0.9.0          # Equalizer DSP
# OR scipy>=1.11.0         # Alternative DSP
python-vlc>=3.0.0          # Crossfade (if switching from pygame)
pylast>=5.2.0              # Lyrics APIs
r128gain>=1.0.0            # ReplayGain scanner
pyloudnorm>=0.1.0          # Loudness analysis

# Phase 8B (MEDIUM)
pylast>=5.2.0              # Last.fm scrobbling
Pillow>=10.0.0             # Album art processing

# Phase 8C (LOW)
pydub>=0.25.0              # Format converter
google-api-python-client   # Google Drive
dropbox>=11.0.0            # Dropbox
matplotlib>=3.8.0          # Statistics charts
spotipy>=2.23.0            # Spotify import
```

---

## 🔍 Research Notes

**From Web Search:**

1. **Equalizer:** Poweramp, BlackPlayer, and Evermusic all use 10-band equalizers as standard. Pedalboard (Spotify's library) is production-ready.

2. **Crossfade:** Standard feature in premium players (Poweramp, Pulsar). Duration 0-10s is common.

3. **Lyrics:** LRC format is industry standard. APIs: Genius, Musixmatch, LRCLIB (free tier).

4. **ReplayGain:** r128gain implements ReplayGain 2.0 spec (EBU R128/ITU BS.1770). Industry standard for loudness normalization.

5. **Smart Shuffle:** MusicBee and foobar2000 both implement artist separation algorithms. Typical separation: 5-10 songs.

---

## 💡 Recommendations

### **For Ricardo:**

1. **Start with Phase 8A (HIGH priority)**
   - Biggest user impact
   - 12-15 days
   - Equalizer + Crossfade + Lyrics + ReplayGain = Professional tier

2. **Skip Phase 8C initially (LOW priority)**
   - Cloud sync is complex (4-5 days alone)
   - Format converter duplicates existing tools
   - Save for commercial version

3. **Consider Phase 8B as "nice-to-have"**
   - Scrobbling + Album Art + Smart Shuffle = 6-7 days
   - Good bang-for-buck ratio

### **Alternative: Minimal Phase 8 (8-10 days)**

If time is limited, implement only:
- ✅ Equalizer (8.1) - 3-4 days
- ✅ Crossfade (8.2) - 2-3 days
- ✅ Lyrics (8.3) - 3-4 days

**Result:** Premium audio experience in 8-10 days

---

## 📝 Next Steps

**Awaiting Ricardo Decision:**

1. **Option A:** Full Phase 8 (all 14 features, 25-30 days)
2. **Option B:** Phase 8A only (4 features, 12-15 days) - RECOMMENDED
3. **Option C:** Minimal Phase 8 (3 features, 8-10 days)
4. **Option D:** Custom selection (pick favorites)

**Once approved:**
- Create detailed TDD plan for selected features
- Research tech stack (pedalboard vs scipy for EQ)
- Begin Feature 8.1 (Equalizer) implementation

---

**Created by:** NEXUS@CLI
**Research Sources:** Poweramp, MusicBee, foobar2000, Pulsar, web search results
**Status:** PLANNING - awaiting Ricardo approval
**Next Review:** After manual testing of Phase 7 complete
