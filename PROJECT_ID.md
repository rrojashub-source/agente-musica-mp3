# PROJECT_ID.md
**AGENTE_MUSICA_MP3 - YouTube Music Downloader & Library Manager**

## 🆔 IDENTITY

- **Project ID:** AGENTE_MUSICA_MP3_001
- **Version:** V1.0 (CLI) → V2.0 (GUI in progress)
- **Status:** ACTIVE - Evolution Phase
- **Created:** September 2024
- **Last Updated:** November 2, 2025
- **GitHub:** https://github.com/rrojashub-source/agente-musica-mp3

---

## 🎯 OBJECTIVE

Transform basic CLI MP3 downloader into modern GUI application that eliminates Excel dependency and provides Spotify/iTunes-like experience for personal music library management.

**Current:** CLI app with Excel input
**Target:** Professional GUI app (CustomTkinter/PyQt6)

---

## 📊 CURRENT STATE

**Phase:** V1.0 CLI COMPLETE ✅ → V2.0 GUI In Progress ⏳

**Compliance Score:** 6/6 (100%)
- ✅ PROJECT_ID.md (this file)
- ✅ PROJECT_DNA.md (detailed specification)
- ✅ CLAUDE.md (context for Claude instances)
- ✅ README.md (public overview)
- ✅ TRACKING.md (session logs)
- ✅ memory/ (dynamic state)
- ✅ tasks/ (external plans)

**Working Features:**
- ✅ YouTube download (yt-dlp)
- ✅ MusicBrainz metadata
- ✅ Excel batch processing
- ✅ Auto-organization by artist
- ✅ 100+ songs downloaded successfully

**To Be Implemented:**
- ⏳ Modern GUI (CustomTkinter/PyQt6)
- ⏳ SQLite database (remove Excel)
- ⏳ Library management
- ⏳ Built-in player

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
