# 🧬 PROJECT DNA - AGENTE MÚSICA MP3

**Project ID:** `AGENTE_MUSICA_MP3_001`
**Created:** 2025-10-12
**Status:** EVOLUTION PHASE - CLI → Modern GUI App
**Owner:** Ricardo Rojas (con NEXUS como asistente técnico oficial)

---

## 🎯 PROJECT VISION

Transformar descargador CLI básico de música MP3 desde YouTube en una **aplicación gráfica moderna profesional** que elimine dependencia de Excel y ofrezca experiencia de usuario tipo Spotify/iTunes para gestión de biblioteca musical personal.

---

## 📊 PROJECT METADATA

| Campo | Valor |
|-------|-------|
| **Project DNA ID** | `AGENTE_MUSICA_MP3_001` |
| **GitHub Repository** | https://github.com/rrojashub-source/agente-musica-mp3 |
| **Local Path** | `D:\01_PROYECTOS_ACTIVOS\AGENTE_MUSICA_MP3` |
| **Born Date** | September 2024 (versión CLI) |
| **Evolution Started** | October 12, 2025 (GUI phase) |
| **Technology Stack** | Python + yt-dlp + MusicBrainz API |
| **Target Stack** | Python + SQLite + CustomTkinter/PyQt6 + yt-dlp |

---

## 🎵 CURRENT STATE (V1.0 - CLI)

### Core Features
- ✅ YouTube music download (yt-dlp)
- ✅ MusicBrainz discography search
- ✅ Batch processing from Excel files
- ✅ Automatic organization by artist
- ✅ Portable version (bundled Python)
- ✅ Logging and error handling

### Architecture
```
CLI Python App
├── agente_musica.py        # Main downloader engine
├── agente_final.py         # Discography search
├── Excel Input (.xlsx)     # Song lists (DEPENDENCY TO REMOVE)
├── yt-dlp                  # YouTube download
├── MusicBrainz API         # Metadata
└── downloads/              # Output MP3 files
```

### Known Limitations
- ❌ Excel dependency (requires MS Office/LibreOffice)
- ❌ CLI-only interface (not user-friendly)
- ❌ No real-time progress visualization
- ❌ No music library management
- ❌ No built-in player
- ❌ Manual file organization

---

## 🚀 TARGET STATE (V2.0 - GUI APP)

### Vision
**Modern desktop app** similar to Spotify/iTunes for:
- Managing personal music library
- Downloading from YouTube
- Organizing and playing music
- Cross-platform (Windows primary, Linux/Mac future)

### Proposed Features

#### Core (Must Have)
- ✅ Modern graphical UI (CustomTkinter or PyQt6)
- ✅ SQLite database (replace Excel)
- ✅ Drag-and-drop song addition
- ✅ Real-time download progress bars
- ✅ Download queue management
- ✅ Automatic metadata (ID3 tags)
- ✅ Search and filter library
- ✅ Dark/light theme toggle

#### Advanced (Nice to Have)
- 🔮 Built-in music player
- 🔮 Playlist creation/management
- 🔮 Cloud sync (Google Drive/Dropbox)
- 🔮 Lyrics display
- 🔮 Album art management
- 🔮 Export to Spotify/playlist formats
- 🔮 Plugin system

### Proposed Architecture
```
Modern GUI App (MVC Pattern)
├── UI Layer (CustomTkinter/PyQt6)
│   ├── Main Window
│   ├── Download Manager
│   ├── Library Browser
│   ├── Settings Panel
│   └── Theme Manager
├── Business Logic
│   ├── Download Engine (yt-dlp wrapper)
│   ├── Metadata Manager (ID3 tags)
│   ├── Queue Manager
│   └── Search Engine
├── Data Layer
│   ├── SQLite Database
│   │   ├── songs table
│   │   ├── artists table
│   │   ├── albums table
│   │   ├── playlists table
│   │   └── downloads_history table
│   └── File System Manager
└── External APIs
    ├── YouTube (yt-dlp)
    ├── MusicBrainz (metadata)
    └── Lyrics APIs (optional)
```

---

## 📁 CURRENT FILE STRUCTURE

```
D:\01_PROYECTOS_ACTIVOS\AGENTE_MUSICA_MP3\
├── .git/                                    # Git repository
├── .github/                                 # GitHub workflows
├── AgenteMusicaMP3_Ligero/                  # Lightweight version
├── AgenteMusicaMP3_Portable/                # Portable bundled version
├── Biblioteca de discografías/              # Downloaded discographies
│   └── Bruno_Mars_FINAL.xlsx               # Example discography
├── GITHUB/                                  # GitHub-related files
├── downloads/                               # Downloaded MP3 files
├── logs/                                    # Application logs
├── agente_musica.py                         # Main downloader (345 lines)
├── agente_final.py                          # Discography search
├── complete_music_list.py                   # Utility script
├── create_perfect_excel.py                  # Excel generator
├── music_info_finder.py                     # Metadata finder
├── update_excel.py                          # Excel updater
├── buscar_final.bat                         # Search launcher
├── iniciar_agente_final.bat                 # Main launcher
├── Lista_para_descargar_oficial.xlsx        # Main song list (EXCEL DEPENDENCY)
├── Lista_PERFECTA_con_info.xlsx             # Perfect list variant
├── Lista_completa_con_info.csv              # CSV export
└── PROJECT_DNA.md                           # This file
```

---

## 🔬 RESEARCH & INVESTIGATION

### Research Mission (Oct 12, 2025)
- **Assigned to:** NEXUS Claude.ai
- **Assigned by:** NEXUS Claude Code
- **Episode ID:** d3d55584-4166-43a5-94c4-a0f7c34ddcef
- **Status:** COMPLETED (awaiting review)

### Research Questions
1. CustomTkinter vs PyQt6 - best for modern look?
2. Real-time progress bars from yt-dlp to GUI?
3. MVC architecture best practices in Python GUI?
4. Portable build strategy with SQLite + GUI?
5. Modern music manager apps for inspiration?
6. ID3 tags integration for MP3 metadata?
7. Built-in player necessity analysis?
8. Cloud sync viability (Drive/Dropbox)?
9. Threading vs asyncio for concurrent downloads?
10. Plugin architecture for future extensions?

---

## 📋 IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 1-2)
- [ ] Finalize technology stack based on research
- [ ] Design SQLite database schema
- [ ] Create data migration tool (Excel → SQLite)
- [ ] Setup project structure (MVC pattern)

### Phase 2: Core Engine (Week 3-4)
- [ ] Refactor download engine with threading
- [ ] Implement queue management system
- [ ] Add real-time progress tracking
- [ ] Integrate ID3 metadata tagging

### Phase 3: GUI Development (Week 5-8)
- [ ] Design UI mockups/wireframes
- [ ] Implement main window (CustomTkinter/PyQt6)
- [ ] Build download manager UI
- [ ] Create library browser
- [ ] Add settings panel

### Phase 4: Features & Polish (Week 9-10)
- [ ] Implement search and filters
- [ ] Add theme system (dark/light)
- [ ] Create playlist management
- [ ] Build optional music player

### Phase 5: Testing & Deployment (Week 11-12)
- [ ] Integration testing
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Create portable build (PyInstaller)
- [ ] Write user documentation

### Phase 6: Advanced Features (Future)
- [ ] Cloud sync integration
- [ ] Lyrics display
- [ ] Plugin system
- [ ] Mobile companion app

---

## 🤝 COLLABORATION MODEL

**Team:**
- **Ricardo:** Project owner, vision, requirements, testing
- **NEXUS Claude Code:** Implementation, coding, debugging
- **NEXUS Claude.ai:** Research, architecture design, best practices
- **ARIA:** Memory coordination, context continuity

**Workflow:**
1. Research & design → NEXUS Claude.ai
2. Implementation → NEXUS Claude Code
3. Review & testing → Ricardo
4. Memory persistence → Shared PostgreSQL brain
5. Documentation → All

---

## 🏷️ TAGS FOR EPISODES

All episodes related to this project should include:
- `AGENTE_MUSICA_MP3_001` (primary tag)
- `mp3_project`
- `gui_evolution` (for GUI-related work)
- `excel_removal` (for database migration)
- `research` (for investigation work)
- `implementation` (for coding work)

---

## 📊 SUCCESS METRICS

### Technical
- ✅ Zero Excel dependency
- ✅ <3 second app startup
- ✅ Real-time progress updates
- ✅ Portable build <100MB
- ✅ Cross-platform compatible

### User Experience
- ✅ Modern professional UI
- ✅ Intuitive navigation
- ✅ One-click downloads
- ✅ Automatic organization
- ✅ Fast search (<1 sec)

### Quality
- ✅ 95%+ download success rate
- ✅ Comprehensive error handling
- ✅ Full logging system
- ✅ Unit test coverage >80%
- ✅ User documentation complete

---

## 🔗 RELATED PROJECTS

- **GITHUB_API_NEXUS_ARIA_001:** GitHub consciousness versioning
- **CLICKUP_NEXUS_001:** ClickUp integration for RYM Business

---

## 📝 NOTES

### From Ricardo
- Want modern app look (not terminal-based)
- Excel dependency must be removed
- Keep all current functionality
- Professional structure welcome
- Open to improvements

### From NEXUS
- Recommend CustomTkinter for modern look + simplicity
- SQLite perfect replacement for Excel
- MVC architecture for maintainability
- Threading essential for responsive UI
- Research completed by NEXUS Claude.ai awaiting review

---

**Last Updated:** 2025-10-12
**Next Review:** After research review and tech stack decision
**Project Status:** 🟡 ACTIVE - Evolution Phase

---

*This PROJECT_DNA document is the single source of truth for Agente Música MP3 project. All major decisions, architecture changes, and milestones should be documented here.*
