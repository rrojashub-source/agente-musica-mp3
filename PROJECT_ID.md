# PROJECT_ID.md
**AGENTE_MUSICA_MP3 - YouTube Music Downloader & Library Manager**

## 🆔 IDENTITY

- **Project ID:** AGENTE_MUSICA_MP3_001
- **Version:** Phase 4 Complete + Pre-Phase 5 Hardening Done
- **Status:** ACTIVE - Ready for Phase 5 (Management Tools)
- **Created:** September 2024
- **Last Updated:** November 13, 2025 (Pre-Phase 5 Hardening COMPLETE)
- **GitHub:** https://github.com/rrojashub-source/agente-musica-mp3

---

## 🎯 OBJECTIVE

Modern music library manager with professional search, download, and management features. Provides Spotify/iTunes-like experience for personal MP3 collections.

**Achieved:** PyQt6 GUI + Search & Download System + Security Hardening
**Next:** Management tools (duplicates, organize, rename) + Music Player

---

## 📊 CURRENT STATE

**Phase:** Phase 4 COMPLETE ✅ + Pre-Phase 5 Hardening DONE ✅ → Ready for Phase 5 ⏳

**Compliance Score:** 6/6 (100%)
- ✅ PROJECT_ID.md (this file)
- ✅ PROJECT_DNA.md (detailed specification)
- ✅ CLAUDE.md (context for Claude instances)
- ✅ README.md (public overview)
- ✅ TRACKING.md (session logs)
- ✅ memory/ (dynamic state)
- ✅ tasks/ (external plans)

**Security Score:** 85/100 (Production-ready)
- ✅ API keys encrypted (OS keyring)
- ✅ Input validation (injection prevention)
- ✅ Comprehensive .gitignore (60+ patterns)
- ✅ Test suite complete (148/148 passing)

**Operational Features (Phase 1-4):**
- ✅ PyQt6 modern GUI
- ✅ SQLite database (10,000+ songs, FTS5 search)
- ✅ YouTube search & download
- ✅ Spotify search (alternative source)
- ✅ Download queue (concurrent downloads)
- ✅ MusicBrainz auto-metadata
- ✅ ID3 tag auto-tagging

**To Be Implemented (Phase 5-6):**
- ⏳ Duplicates detection
- ⏳ Auto-organize library (artist/album folders)
- ⏳ Batch rename with templates
- ⏳ Tag editor GUI
- ⏳ Music player with playlists

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

**Last Updated:** November 2, 2025 (NEXUS methodology migration)
**Maintained by:** Ricardo + NEXUS@CLI
