# NEXUS Music Manager

**Professional Music Library Management System**

Version 2.1.0 | Python 3.13 | PySide6 | Windows | MIT License

---

## The Problem

Music lovers managing MP3 libraries (100-10,000 songs) juggle multiple tools: yt-dlp for downloads, MusicBrainz Picard for tags, foobar2000 for playback, and manual scripts for organization. NEXUS Music Manager unifies everything into one desktop application.

## Solution

A professional music library manager with a PySide6 GUI that integrates downloading, metadata enrichment, organization, playback, and AI-powered analysis.

**User journey:** Import your MP3s -> Enrich metadata automatically -> Organize your library -> Enjoy with visualizers and smart recommendations.

---

## Install

### Windows Installer (recommended)

Download `Setup_NEXUS_Music_v2.1.0.exe` (154 MB) from [Releases](https://github.com/rrojashub-source/agente-musica-mp3/releases).

### Development Setup

```bash
git clone https://github.com/rrojashub-source/agente-musica-mp3.git
cd agente-musica-mp3
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for testing/linting
python src/main.py
```

**Prerequisite:** [libmpv](https://sourceforge.net/projects/mpv-player-windows/) — place `libmpv-2.dll` in `src/` or system PATH.

---

## Features

### Download & Search
- **YouTube Download** — MP3 320kbps via yt-dlp with concurrent queue (3 simultaneous)
- **Spotify Search** — Find songs, auto-convert to YouTube download
- **Playlist Download** — Full playlist import with progress tracking

### Library Management
- **SQLite + FTS5 + WAL** — Full-text search across title, artist, album
- **Duplicate Detection** — Audio fingerprinting (AcoustID) + metadata + file hash
- **Auto-Organizer** — Artist/Album folder structure templates
- **Batch Rename** — Template-based mass renaming
- **Import Scanner** — Drag-and-drop folder import with metadata extraction

### Music Player
- **python-mpv** — Gapless playback, all audio formats
- **10-Band Equalizer** — Rock, Pop, Jazz, Classical presets
- **4 Visualizers** — Bars, Waveform, Brain AI, Organic SDF (OpenGL 3.3 + GLSL)
- **Synced Lyrics** — LRC format + Genius API fallback
- **Chord Detection** — Real-time chord analysis with guitar diagrams
- **Keyboard Shortcuts** — Fully customizable (Space, arrows, F11 fullscreen)

### AI & Analysis
- **Audio Embeddings** — 128D feature vectors from scipy FFT
- **Find Similar Songs** — Cosine similarity search across your library
- **BPM Detection** — Automatic tempo analysis
- **Mood Classification** — Happy, Sad, Energetic, Calm

### Extras
- **Cloud Sync** — Local folder + Google Drive providers
- **Plugin System** — 17 hooks, 3 included plugins (PlayCounter, Scrobbler, Discord RPC)
- **Multi-language** — Spanish/English (274 translation keys)
- **Dark/Light Themes** — QSS-based with style constants
- **Statistics** — Play history, top artists, listening trends

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| GUI | PySide6 6.10 |
| Database | SQLite + FTS5 + WAL |
| Audio | python-mpv (libmpv) + scipy.fft |
| Visualizers | OpenGL 3.3 + GLSL shaders |
| Downloads | yt-dlp |
| Metadata | mutagen-rs (Rust, 57x faster) with mutagen fallback |
| APIs | YouTube Data v3, Spotify, MusicBrainz, Genius, AcoustID |
| Packaging | PyInstaller 6.19 + Inno Setup 6 (154 MB installer) |
| Quality | mypy strict, pytest 980+, ruff, bandit |
| CI/CD | GitHub Actions (test, type-check, security, build) |

---

## Project Structure

```
agente-musica-mp3/
├── src/                        # Application source (116 files, 37K LOC)
│   ├── main.py                 # Entry point (Facade pattern, 338 LOC)
│   ├── api/                    # YouTube, Spotify, MusicBrainz, Genius, Chords
│   ├── core/                   # Audio player, downloads, embeddings, metadata, playlists
│   ├── controllers/            # Playback, Library, UIComposer, Remote
│   ├── database/               # SQLite manager + 6 SQL migrations
│   ├── gui/
│   │   ├── base/               # BaseTab shared template
│   │   ├── tabs/               # 12 tabs (library, search, lyrics, chords, import, ...)
│   │   ├── widgets/            # 9 widgets (player, visualizer, equalizer, ...)
│   │   ├── visualizers/        # Organic SDF visualizer (OpenGL + GLSL)
│   │   ├── dialogs/            # API settings, shortcuts
│   │   └── themes/             # dark.qss, light.qss, style_constants.py
│   ├── services/               # Cloud sync, statistics, download service
│   ├── plugins/                # Plugin system (17 hooks) + 3 built-in plugins
│   ├── workers/                # Background workers (download, import, scan)
│   └── utils/                  # Sanitizer, rate limiter, credentials, constants
├── tests/                      # 86 test files
├── docs/                       # PRD, architecture, API reference, audit reports
│   ├── history/                # Archived docs from previous phases
│   └── plans/                  # Active roadmaps
├── scripts/                    # Build scripts, DB utilities
├── installer/                  # Inno Setup configuration
├── agent_docs/                 # Build, test, and architecture guides
└── tasks/                      # Active development notes
```

---

## Quality Metrics

| Metric | Status |
|--------|--------|
| mypy | 0 errors (116 files, strict mode) |
| ruff | Clean (lint + format, line-length=120) |
| bandit | Clean (-ll) |
| pytest | 980+ tests passing |
| pre-commit | ruff (replaces black + isort + flake8) |
| Audit | MAPS 4-phase audit: 15/15 modules approved (63 rounds) |
| UAT | 7 rounds, 2576 log lines, 0 errors |

---

## API Keys (Optional)

Configure via **Tools > Configure API Keys** in the app. Keys are stored in your OS keyring (never in code).

| API | Purpose | Required? |
|-----|---------|-----------|
| YouTube Data v3 | Search | Optional (scraping fallback) |
| Spotify Web API | Alternative search | Optional |
| Genius | Lyrics | Optional |
| AcoustID | Audio fingerprinting | Optional |

---

## System Requirements

- **OS:** Windows 10/11 (64-bit)
- **RAM:** 4 GB minimum, 8 GB recommended
- **Storage:** 200 MB for application
- **GPU:** OpenGL 3.3 compatible (for visualizers)
- **Audio:** libmpv-2.dll (bundled in installer)

---

## Security

- JWT Bearer authentication on remote API (24h expiration)
- CORS restricted to specific server IP (not wildcard)
- Path traversal protection with symlink checks
- FTS5 query sanitization (SQL injection prevention)
- Plugin whitelist (default-deny)
- Input sanitization on all external data
- Credentials in OS keyring (4-tier fallback)

---

## Development

```bash
# Run application
python src/main.py

# Run tests
pytest tests/ -v

# Type checking
mypy src/ --ignore-missing-imports

# Lint + format
ruff check src/ tests/
ruff format src/ tests/

# Security scan
bandit -r src/ -ll

# Build installer (requires PyInstaller + Inno Setup 6)
scripts\build_installer.bat
```

Pre-commit hooks (ruff lint + format) run automatically on every commit.

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | Product requirements, scope, and non-goals |
| [Architecture](docs/ARCHITECTURE.md) | System design and patterns |
| [API Reference](docs/API_REFERENCE.md) | Internal API and REST endpoints |
| [Progress](docs/PROGRESS.md) | Current status and next steps |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and fixes |
| [Changelog](CHANGELOG.md) | Version history |
| [Commercial Roadmap](docs/plans/ROADMAP_COMERCIAL_V2.md) | Future plans |

---

## Implementation Phases

| Phase | Name | Period |
|-------|------|--------|
| 1 | Core Library + Database | Sep 2025 |
| 2 | Search + Download | Oct 2025 |
| 3 | Stack Migration (PyQt6 -> PySide6) | Oct 2025 |
| 4 | API Integration (Spotify, MusicBrainz, Genius) | Nov 2025 |
| 5 | Management Tools (duplicates, organize, rename) | Nov 2025 |
| 6 | Player Polish (gapless, visualizer) | Nov 2025 |
| 7 | Advanced Features (plugins, remote, cloud, i18n) | Nov-Dec 2025 |
| 8 | AI Features (embeddings, content filter, chords) | Dec 2025 |
| 9 | Packaging + Build | Dec 2025 |
| 10 | Refactoring + Audit | Mar 2026 |

All 10 phases completed.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Follow code style: `ruff` (120 chars), type hints required
4. Run tests: `pytest tests/ -v`
5. Run checks: `mypy src/ --ignore-missing-imports && ruff check src/`
6. Submit a PR to `main`

---

## Credits

Built by **Ricardo Rojas** with **Claude (NEXUS@CLI)** as AI pair-programmer.

This was my first software project. It started in September 2025 as a simple idea — "what if I could manage my music library with one tool?" — and grew into 304 commits, 116 source files, and 37,000 lines of code over 7 months. There were moments I thought I wouldn't finish it. I did.

10 development phases. 63 audit rounds. 7 UAT rounds. From a script that barely played MP3s to a full desktop application with AI recommendations, OpenGL visualizers, and a Windows installer.

**Period:** September 2025 - March 2026
**License:** MIT — Copyright (c) 2025-2026 Ricardo Rojas
