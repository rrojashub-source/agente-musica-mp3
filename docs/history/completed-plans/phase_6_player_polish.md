# Phase 6: Audio Player & Production Polish - Implementation Plan

**Created:** November 13, 2025
**Status:** Planning → Execution
**Timeline:** 1-2 days (estimated 8-10 days with full autonomy)
**Priority:** HIGH (complete functional music player)

---

## 🎯 Phase 6 Mission

Transform the app into a **complete, production-ready music player** by adding:
1. **Audio playback** (play/pause/stop/seek)
2. **Now Playing UI** (current song display with controls)
3. **Production polish** (error handling, performance, UX improvements)

**Note:** Playlist management can be Phase 7 (already have download queue as basic playlist). Focus on core playback first.

---

## 📋 Features Breakdown

### **Feature 6.1: Audio Playback Engine (Core)**

**Goal:** Play MP3 files with full controls

**Engine Implementation (src/core/audio_player.py):**
- Library: pygame.mixer (lightweight, cross-platform)
- Methods:
  * `load(file_path)` - Load MP3 file
  * `play()` - Start playback
  * `pause()` - Pause playback
  * `resume()` - Resume from pause
  * `stop()` - Stop and reset
  * `seek(position)` - Jump to position (seconds)
  * `get_position()` - Current position (seconds)
  * `get_duration()` - Total duration (seconds)
  * `set_volume(level)` - Volume 0.0-1.0
  * `is_playing()` - Playback state

**Tests (tests/test_audio_player.py): 12 tests**
1. test_01_audio_player_class_exists
2. test_02_player_loads_mp3_file
3. test_03_player_plays_audio
4. test_04_player_pauses_audio
5. test_05_player_resumes_audio
6. test_06_player_stops_audio
7. test_07_player_seeks_to_position
8. test_08_player_gets_current_position
9. test_09_player_gets_duration
10. test_10_player_sets_volume
11. test_11_player_handles_invalid_file
12. test_12_player_handles_end_of_song

**Acceptance Criteria:**
- Load and play MP3 in < 500ms
- Seek to any position instantly
- Volume control smooth (no clicks)
- Handle end of song gracefully
- Support 44.1kHz and 48kHz sample rates

---

### **Feature 6.2: Now Playing Widget (GUI)**

**Goal:** Display currently playing song with playback controls

**GUI Implementation (src/gui/widgets/now_playing_widget.py):**
- QWidget with horizontal layout
- Components:
  * Album art thumbnail (100x100)
  * Song info (title, artist, album)
  * Playback controls (play/pause, stop, prev, next)
  * Progress slider (seek bar)
  * Time labels (current / total)
  * Volume slider
- QTimer for position updates (100ms)
- Signals for control actions

**Tests (tests/test_now_playing_widget.py): 10 tests**
1. test_01_now_playing_widget_exists
2. test_02_widget_displays_song_info
3. test_03_widget_has_playback_controls
4. test_04_widget_has_progress_slider
5. test_05_widget_has_volume_slider
6. test_06_widget_updates_position
7. test_07_play_button_toggles_state
8. test_08_progress_slider_seeks
9. test_09_volume_slider_adjusts_volume
10. test_10_widget_handles_no_song_loaded

**Acceptance Criteria:**
- Display song metadata correctly
- Progress slider smooth (no jitter)
- Click slider to seek instantly
- Play button toggles to pause icon
- Volume persists between songs

---

### **Feature 6.3: Library Integration (Playback from Library)**

**Goal:** Play songs directly from library view

**Implementation:**
- Add "Play" button/double-click to library table
- Connect library selection to audio player
- Queue next song on end
- Keyboard shortcuts (Space = play/pause, Arrow keys = prev/next)

**Tests (tests/test_playback_integration.py): 8 tests**
1. test_01_double_click_plays_song
2. test_02_play_button_plays_selected_song
3. test_03_end_of_song_plays_next
4. test_04_keyboard_space_toggles_playback
5. test_05_keyboard_arrows_change_song
6. test_06_playing_song_highlights_in_library
7. test_07_play_updates_now_playing_widget
8. test_08_handles_missing_file_gracefully

**Acceptance Criteria:**
- Double-click plays instantly
- Auto-play next song in library order
- Keyboard shortcuts work globally
- Currently playing song highlighted
- Graceful error if file missing

---

## 🧪 TDD Test Plan

**Total Tests Planned:** 30 tests
- Audio Player Engine: 12 tests
- Now Playing Widget: 10 tests
- Playback Integration: 8 tests

**Test Strategy:**
- RED: Write tests first (all fail initially)
- GREEN: Implement minimum code to pass
- REFACTOR: Optimize and clean up

**Mock Strategy:**
- Mock pygame.mixer for engine tests (no actual audio needed)
- Mock audio player for GUI tests (test UI logic only)
- Use temp files for integration tests

---

## 📅 Implementation Timeline

### **Day 1: Audio Playback Engine + Now Playing Widget**

**Morning (4h):**
1. Create audio_player.py tests (RED PHASE)
2. Implement AudioPlayer class (GREEN PHASE)
3. Verify all 12 tests passing
4. Git commit: "feat(phase6): Audio Player Engine - Feature 6.1"

**Afternoon (4h):**
5. Create now_playing_widget.py tests (RED PHASE)
6. Implement NowPlayingWidget GUI (GREEN PHASE)
7. Verify all 10 tests passing
8. Git commit: "feat(phase6): Now Playing Widget - Feature 6.2"

**Evening (2h):**
9. Manual testing with real MP3 files
10. Fix any issues found
11. Update documentation

---

### **Day 2: Integration + Polish (Optional if Day 1 complete)**

**Morning (3h):**
1. Create playback_integration.py tests (RED PHASE)
2. Implement library playback integration (GREEN PHASE)
3. Verify all 8 tests passing
4. Git commit: "feat(phase6): Playback Integration - Feature 6.3"

**Afternoon (3h):**
5. Production polish:
   - Error handling (file not found, corrupt MP3)
   - Performance optimization
   - UX improvements (tooltips, status messages)
   - Keyboard shortcuts
6. Final testing
7. Git commit: "feat(phase6): Production Polish"

**Evening (2h):**
8. Documentation update (README, CLAUDE.md, current_phase.md)
9. Final test suite run (verify 244/264 tests passing)
10. Git commit: "docs(phase6): Phase 6 COMPLETE"

---

## 🔧 Technical Decisions

### **Audio Library Choice: pygame.mixer**

**Why pygame.mixer:**
- ✅ Lightweight (no heavy dependencies)
- ✅ Cross-platform (Windows, Linux, macOS)
- ✅ Simple API (5 methods cover 90% use cases)
- ✅ Already popular in Python community
- ✅ Handles MP3, OGG, WAV out of the box

**Alternatives considered:**
- ❌ VLC (python-vlc): Heavier, requires VLC installation
- ❌ pydub: More for editing/conversion than playback
- ❌ sounddevice: Lower level, more complex

### **UI Updates: QTimer with 100ms interval**

**Why 100ms:**
- Smooth progress bar updates (10 FPS)
- Low CPU usage
- Imperceptible delay for user

### **Playback State Management**

**States:**
- STOPPED (no file loaded)
- PLAYING (audio playing)
- PAUSED (paused, can resume)

**Transitions:**
```
STOPPED → [load + play] → PLAYING
PLAYING → [pause] → PAUSED
PAUSED → [resume] → PLAYING
PLAYING → [stop] → STOPPED
```

---

## 🎨 UI Mockup

**Now Playing Widget:**
```
+------------------------------------------------+
| [Album Art]  Bohemian Rhapsody                |
| [100x100]    Queen - A Night at the Opera     |
|                                                |
| [⏮] [▶/⏸] [⏹] [⏭]    [====|====] Volume     |
|                                                |
| [================|===================]         |
| 2:35 / 5:55                                    |
+------------------------------------------------+
```

**Library View with Playback:**
```
+------------------------------------------------+
| ▶ Bohemian Rhapsody | Queen | 1975 | 5:55    | ← Currently playing (highlighted)
|   You're My Best... | Queen | 1975 | 2:43    |
|   Another One Bit.. | Queen | 1980 | 3:36    |
+------------------------------------------------+
```

---

## ✅ Success Criteria (Phase 6 Complete When)

**Functional:**
- ✅ Play any MP3 file from library
- ✅ Pause/resume works correctly
- ✅ Seek to any position instantly
- ✅ Volume control smooth
- ✅ Auto-play next song when current ends
- ✅ Keyboard shortcuts functional
- ✅ Currently playing song highlighted

**Technical:**
- ✅ 30/30 new tests passing (100%)
- ✅ 244/264 total tests passing (92%+)
- ✅ Zero memory leaks (pygame cleanup)
- ✅ No audio glitches or clicks
- ✅ Works on Windows (primary target)

**UX:**
- ✅ Playback starts in < 500ms
- ✅ Progress bar smooth
- ✅ Error messages user-friendly
- ✅ Controls intuitive (standard music player icons)

---

## 📊 Risk Assessment

**Technical Risks:**
1. **pygame.mixer compatibility** (Mitigation: Test on Windows first, fallback to VLC if needed)
2. **Audio format support** (Mitigation: Stick to MP3 for Phase 6, other formats Phase 7)
3. **Threading issues** (Mitigation: pygame runs in main thread, use QTimer for updates)

**Scope Risks:**
1. **Feature creep** (Mitigation: No playlists in Phase 6, just playback)
2. **Over-engineering** (Mitigation: Simple implementation first, optimize later)

**Timeline Risks:**
1. **pygame learning curve** (Mitigation: API is simple, 1h to learn)
2. **Integration complexity** (Mitigation: Well-defined interfaces)

---

## 🚀 Post-Phase 6 Roadmap

**Phase 7 (Future):**
- Playlist management (create/edit/save)
- Equalizer (bass, treble, presets)
- Visualizer (waveform, spectrum)

**Phase 8 (Advanced Features):**
- Lyrics display (Genius API)
- Spotify playlist import
- Format converter (MP3 ↔ FLAC)
- Cloud sync

**Production Release:**
- Installer (PyInstaller or cx_Freeze)
- Windows executable (.exe)
- User manual
- Website/landing page

---

## 📝 Notes

**Why Skip Playlists in Phase 6:**
- Download queue already functions as basic playlist
- Focus on core playback first (MVP)
- Playlists are Phase 7 (more complex UI)

**Why pygame.mixer over VLC:**
- Simpler integration (5 lines vs 50 lines)
- No external dependencies
- Sufficient for MP3 playback
- Can switch to VLC later if needed

**Why Not Include Equalizer:**
- pygame.mixer has limited EQ support
- Would require VLC or sounddevice
- Better as Phase 7 feature
- Focus on basic playback first

---

**Created by:** NEXUS@CLI (Full Autonomy Mode)
**For:** Ricardo (AGENTE_MUSICA_MP3 Project)
**Methodology:** NEXUS 4-Phase (Explorar → Planificar → Codificar → Confirmar)
**Date:** November 13, 2025
