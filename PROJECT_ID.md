# PROJECT_ID.md
**AGENTE_MUSICA_MP3 - YouTube Music Downloader & Library Manager**

## 🆔 IDENTITY

- **Project ID:** AGENTE_MUSICA_MP3_001
- **Version:** Pre-Commercial (Score: 85/100)
- **Status:** ACTIVE - All Critical Fixes Done, Ready for Packaging
- **License:** MIT
- **Created:** September 2024
- **Last Updated:** November 23, 2025 (Critical Fixes + Thread-Safety)
- **GitHub:** Private (pending setup)

---

## 🎯 OBJECTIVE

Modern music library manager with professional search, download, and management features. Provides Spotify/iTunes-like experience for personal MP3 collections.

**Achieved:** PyQt6 GUI + Search & Download System + Security Hardening
**Next:** Management tools (duplicates, organize, rename) + Music Player

---

## 📊 CURRENT STATE

**Phase:** Pre-Commercial (Score: 85/100) ✅

**Critical Fixes Completed (Nov 23, 2025):**
- ✅ LICENSE (MIT) added
- ✅ Lambda closure bug fixed (download_queue.py)
- ✅ clear() method added (now_playing_widget.py)
- ✅ Brain AI optimized (500→250 particles)
- ✅ Playlist highlight sync implemented
- ✅ Database thread-safety (threading.local)

**Compliance Score:** 7/7 (100%)
- ✅ PROJECT_ID.md (this file)
- ✅ PROJECT_DNA.md (detailed specification)
- ✅ CLAUDE.md (context for Claude instances)
- ✅ README.md (public overview)
- ✅ TRACKING.md (session logs)
- ✅ LICENSE (MIT)
- ✅ memory/ + tasks/

**Commercial Readiness Score:** 85/100
- ✅ API keys encrypted (OS keyring)
- ✅ Input validation (injection prevention)
- ✅ Thread-safe database
- ✅ All critical bugs fixed
- ⏳ Packaging (setup.py + PyInstaller) - pending

**Operational Features:**
- ✅ PyQt6 modern GUI with visualizer
- ✅ SQLite database (thread-safe, FTS5 search)
- ✅ YouTube + Spotify search & download
- ✅ Download queue (concurrent, fixed)
- ✅ MusicBrainz auto-metadata
- ✅ Playlist management with highlight
- ✅ Music player with controls

**Pending for Commercial:**
- ⏳ Packaging (.exe without Python)
- ⏳ i18n (Spanish version)
- ⏳ Recommendations feature
- ⏳ AI integration (TBD)

---

## 🛠️ TECH STACK

**Current (V1.0):**
- Python 3.11+
- yt-dlp (YouTube download)
- MusicBrainz API (metadata)
- Excel (.xlsx) - TO BE REMOVED

**Target (V2.0):**
- CustomTkinter or PyQt6 (GUI)
- SQLite (database)
- Mutagen (ID3 tag editing)
- pygame/vlc (audio playback)

---

## 📁 KEY FILES

- `PROJECT_DNA.md` - Detailed specification (~300 lines)
- `CLAUDE.md` - Context for Claude instances
- `agente_musica.py` - Main downloader engine
- `agente_final.py` - Discography search
- `downloads/` - Downloaded MP3 library

**Documentation:**
- `README.md` - Public overview
- `TRACKING.md` - Session-by-session progress
- `ROADMAP_PHASES_4-6.md` - Evolution roadmap
- `ROADMAP_COMERCIAL.md` - Commercial potential

---

## 🚀 QUICK START

**Download songs:**
```bash
python agente_musica.py
# Input: Excel file with song list
# Output: MP3s in downloads/
```

**Search discography:**
```bash
python agente_final.py
# Input: Artist name
# Output: Full discography from MusicBrainz
```

---

## 📝 NOTES

**Philosophy:** "Spotify/iTunes experience for personal MP3 library"

**Evolution Path:**
- Phase 1-3: CLI prototype ✅
- Phase 4: Production CLI ✅ (100+ songs downloaded)
- Phase 5-6: Modern GUI ⏳ (in progress)

**Commercial Potential:**
- Personal music library manager
- Premium features: Cloud sync, advanced metadata
- Target: Users who own music locally (no streaming)

---

**For detailed specification, see:** `PROJECT_DNA.md`
**For Claude context, see:** `CLAUDE.md`
**For session history, see:** `TRACKING.md`

---

**Last Updated:** November 23, 2025 (Critical Fixes + Thread-Safety)
**Maintained by:** Ricardo + NEXUS@CLI
