# 🎵 AGENTE_MUSICA_MP3 - Claude Context

**Version:** V1.0 (CLI) → V2.0 (GUI in progress)
**Project:** YouTube Music Downloader & Library Manager
**Philosophy:** "Spotify/iTunes experience for personal MP3 library"

---

## 🎯 Project Mission

Transform basic CLI MP3 downloader into modern GUI application:
- ✅ Download music from YouTube (yt-dlp)
- ✅ MusicBrainz metadata integration
- ⏳ Modern GUI (CustomTkinter/PyQt6)
- ⏳ SQLite database (remove Excel dependency)
- ⏳ Library management (organize, play, edit metadata)

**Current:** CLI app with Excel input
**Target:** Professional GUI app (Spotify-like experience)

---

## 🛠️ Technology Stack

**Core:**
- Python 3.11+
- yt-dlp (YouTube download)
- MusicBrainz API (metadata)
- Excel (.xlsx) - TO BE REMOVED

**Target Stack (V2.0):**
- CustomTkinter or PyQt6 (GUI)
- SQLite (database)
- Mutagen (ID3 tag editing)
- pygame/vlc (audio playback)

---

## 📁 Key Files

```
AGENTE_MUSICA_MP3/
├── PROJECT_DNA.md          # Project specification
├── README.md               # Overview
├── CLAUDE.md               # This file
├── TRACKING.md             # Session logs
├── memory/                 # Dynamic state
│   └── shared/current_phase.md
├── tasks/                  # External plans
├── agente_musica.py        # Main downloader
├── agente_final.py         # Discography search
├── cleanup_assistant_tab.py # Cleanup features
├── library_import_worker.py # Library import
├── downloads/              # Downloaded MP3s
└── Lista_*.xlsx            # Song lists (legacy)
```

---

## 🚀 Development Commands

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

**Cleanup assistant:**
```bash
python cleanup_assistant_tab.py
# Detect duplicates, fix tags, organize files
```

---

## 📐 Current Phase

**PHASE 4:** COMPLETE ✅
- CLI app functional
- Excel integration working
- Download + organize operational

**PHASE 5:** In Progress (GUI Development)
- Modern interface design
- SQLite database migration
- Playback features
- Commercial roadmap (ROADMAP_COMERCIAL.md)

**Status:** Evolution from CLI to modern GUI app

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

**V1.0 (CLI) - DONE:**
- ✅ 100+ songs downloaded successfully
- ✅ Automatic artist organization
- ✅ MusicBrainz metadata accuracy

**V2.0 (GUI) - Target:**
- Modern interface (Spotify-like)
- Zero Excel dependency
- Playlist management
- Audio playback
- Commercial viability

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
- Phase 1-3: CLI prototype
- Phase 4: Production CLI ✅
- Phase 5-6: Modern GUI (in progress)

---

**Last Updated:** November 2, 2025 (NEXUS methodology migration)
**Maintained by:** Ricardo + NEXUS@CLI
