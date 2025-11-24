# 🎵 AGENTE_MUSICA_MP3 - Claude Context

**Version:** Pre-Commercial (Score: 85/100) ✅
**Project:** YouTube Music Downloader & Library Manager
**Philosophy:** "Spotify/iTunes experience for personal MP3 library"
**Commercial Score:** 85/100 ✅ (target achieved)
**License:** MIT

---

## 🎯 Project Mission

Modern GUI music manager with professional features:
- ✅ Download music from YouTube (yt-dlp)
- ✅ MusicBrainz metadata integration
- ✅ Modern GUI (PyQt6)
- ✅ SQLite database (10,000+ songs)
- ✅ Dual-source search (YouTube + Spotify)
- ✅ Spotify → YouTube auto-conversion (seamless)
- ✅ Download queue with concurrent downloads
- ✅ Auto-metadata tagging
- ✅ **Auto-import to Library Database (after download)**
- ✅ Security hardening (encrypted API keys, input validation)
- ⏳ Library management tools (duplicates, organize, rename)

**Current:** Phase 4 Complete + Critical Bug Fix (Auto-Import Working 100%)
**Target:** Extended testing → Phase 5 (Management & Cleanup Tools)

---

## 🛠️ Technology Stack

**Production Stack (Phase 4 Complete):**
- Python 3.11+
- PyQt6 (modern GUI framework)
- yt-dlp (YouTube download engine)
- SQLite (database with FTS5 search)
- Mutagen (ID3 tag editing)
- MusicBrainz API (metadata)
- YouTube Data API v3 (search)
- Spotify Web API (alternative search)
- Keyring (encrypted API key storage)

**Security (Pre-Phase 5 Hardening):**
- OS keyring integration (encrypted secrets)
- Input sanitization (injection prevention)
- Comprehensive .gitignore (secret protection)

---

## 📁 Key Files

```
AGENTE_MUSICA_MP3/
├── PROJECT_DNA.md              # Project specification
├── PROJECT_ID.md               # NEXUS standard spec
├── README.md                   # Overview
├── CLAUDE.md                   # This file
├── TRACKING.md                 # Session logs
├── memory/                     # Dynamic state
│   └── shared/current_phase.md # Global phase tracking
├── tasks/                      # External plans
├── src/                        # Source code
│   ├── api/                    # API clients (YouTube, Spotify, MusicBrainz)
│   ├── core/                   # Core logic (download queue, metadata)
│   ├── gui/                    # GUI components (tabs, widgets, dialogs)
│   └── utils/                  # Utilities (input_sanitizer)
├── tests/                      # Test suite (148 tests)
├── downloads/                  # Downloaded MP3s
└── OLD/                        # Legacy CLI code (archived)
```

---

## 🚀 Running the Application

**Launch GUI (Recommended):**
```bash
# Windows:
LAUNCH_NEXUS_MUSIC.bat

# Linux/Mac:
source spike_pyqt6/venv/bin/activate
python main_window_complete.py
```

**Run Tests:**
```bash
# Full test suite (148 tests):
pytest tests/ -v

# Specific tests:
pytest tests/test_input_sanitizer.py -v
pytest tests/test_api_settings_dialog.py -v
```

---

## 📐 Current Phase

**ALL PHASES COMPLETE** ✅ (Phases 1-7)
- Phase 4: Search & Download System ✅
- Phase 5: Management & Cleanup Tools ✅
- Phase 6: Audio Player & Production Polish ✅
- Phase 7: Playlists, Visualizer, Keyboard Shortcuts ✅

**CRITICAL FIXES COMPLETED** ✅ (November 23, 2025)
- ✅ LICENSE (MIT) added
- ✅ Lambda closure bug fixed (download_queue.py:529-531)
- ✅ clear() method added (now_playing_widget.py)
- ✅ Brain AI optimized (500→250 particles)
- ✅ Database thread-safety (threading.local)
- ✅ Playlist highlight sync implemented

**COMMERCIAL SCORE: 85/100** ✅ (target achieved)
- Functionality: 90/100 ✅
- Infrastructure: 75/100 ✅ (improved)
- Pending: Packaging (.exe)

**NEXT FEATURES (Optional):**
1. ⏳ Packaging (setup.py + PyInstaller) - for .exe distribution
2. 🌍 Versión en Español (i18n) - mercado objetivo
3. 🎵 Recomendaciones de canciones similares (idea del hijo)
4. 🤖 AI Integration (TBD)

**Status:** Ready for GitHub + Packaging
**Roadmap:** See `docs/plans/ROADMAP_COMERCIAL_V2.md`

---

## 🛡️ DO NOT TOUCH

**User Data:**
- downloads/ folder (user's MP3 library)
- Lista_*.xlsx files (user's song lists)
- Organized music folders in C:\Users\ricar\Music\

**Production Files:**
- agente_musica.py (working downloader)
- config files

---

## 🔄 Workflow

**1. EXPLORAR:**
```
Read: PROJECT_DNA.md, ROADMAP_PHASES_4-6.md
Understand: Current phase, pending features
```

**2. PLANIFICAR:**
```
Create plan in tasks/[feature].md
Get Ricardo approval
```

**3. CODIFICAR:**
```
Implement feature
Test with real downloads
```

**4. CONFIRMAR:**
```
Git commit
Update TRACKING.md
```

---

## 📊 Success Metrics

**Phase 1-4 (CLI + Search & Download) - COMPLETE:**
- ✅ 100+ songs downloaded successfully
- ✅ PyQt6 modern GUI operational
- ✅ Dual-source search (YouTube + Spotify)
- ✅ Download queue with concurrent downloads
- ✅ Auto-metadata tagging (MusicBrainz)
- ✅ 148/148 tests passing
- ✅ Security hardening complete

**Phase 5-6 (Management & Player) - Target:**
- Duplicates detection and removal
- Auto-organize library by artist/album
- Batch rename with templates
- Full-featured music player
- Playlist management

---

## 🆘 Common Issues

**Issue: "yt-dlp download fails"**
- Solution: Update yt-dlp: `pip install -U yt-dlp`

**Issue: "Excel file not found"**
- Solution: Check file path in Lista_*.xlsx

**Issue: "MusicBrainz rate limit"**
- Solution: Add delays between requests

**Issue: "Context loss between sessions"**
- Solution: Read memory/shared/current_phase.md

---

## 📝 Notes

**Commercial Potential:**
- Roadmap in ROADMAP_COMERCIAL.md
- Target: Personal music library manager
- Monetization: Premium features, cloud sync

**Architecture Evolution:**
- Phase 1-3: CLI prototype ✅
- Phase 4: Search & Download System ✅
- Phase 5: Management & Cleanup Tools ✅
- Phase 6: Audio Player & Production Polish ✅
- Phase 7: Playlists, Visualizer, Keyboard Shortcuts ✅
- **Nov 21, 2025: Brain AI Visualizer Enhanced ✅**
- **Nov 23, 2025: Playlist Redesign (Grid + Tab) ✅**
- **Nov 23, 2025: Pre-Commercial Audit (Score 72/100)**

---

**Last Updated:** November 23, 2025 (All Critical Fixes Done - Score 85/100)
**Maintained by:** Ricardo + NEXUS@CLI
