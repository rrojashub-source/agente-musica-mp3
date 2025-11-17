# 🎵 AGENTE_MUSICA_MP3 - Claude Context

**Version:** Phase 4 Complete + Critical Bug Fixes (Nov 17, 2025)
**Project:** YouTube Music Downloader & Library Manager
**Philosophy:** "Spotify/iTunes experience for personal MP3 library"

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

**PHASE 4: COMPLETE** ✅ (November 12, 2025)
- Search & Download System fully operational
- YouTube + Spotify dual-source search
- Download queue with concurrent downloads
- Auto-metadata tagging with MusicBrainz
- 127/127 tests passing

**PRE-PHASE 5 HARDENING: COMPLETE** ✅ (November 13, 2025)
- API keys encrypted in OS keyring
- Input validation (prevents injection attacks)
- Comprehensive .gitignore (60+ patterns)
- Test suite extended to 148/148 tests
- Security score: 40/100 → 85/100

**PHASE 5: READY TO START** ⏳
- Duplicates detection
- Auto-organize library
- Batch rename files
- Tag editor GUI
- Import existing library

**Status:** All blockers resolved, ready for Phase 5 development

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
- Pre-Phase 5: Security Hardening ✅
- **Nov 17, 2025: Critical Bug Fix (Auto-Import) ✅**
- Phase 5-6: Management & Player (ready to start)

---

**Last Updated:** November 17, 2025 (Critical Bug Fix: Auto-Import COMPLETE - Downloads now auto-import to library)
**Maintained by:** Ricardo + NEXUS@CLI
