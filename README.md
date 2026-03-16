# NEXUS Music Manager

**Professional Music Library Management System**

Version: 2.1.0 | Python 3.13 | PySide6 | License: MIT

---

## Overview

Desktop music library manager with YouTube downloading, Spotify search, automatic metadata tagging (MusicBrainz), real-time audio visualization (OpenGL), AI-powered song similarity, chord detection, lyrics, plugin system, mobile remote control, and cloud sync. Supports Spanish and English.

**Metrics:** 111 source files, 38K LOC, 560+ tests, audit score 7.6/10.

---

## Quick Start

```bash
# Pre-built Windows executable
dist/NEXUS_Music_Manager.exe

# Development
pip install -r requirements.txt
python src/main.py

# Tests
pytest tests/ -v
```

---

## Features

### Download & Search
- **YouTube Download** -- High quality MP3 320kbps via yt-dlp
- **Spotify Search** -- Find songs with auto-conversion to YouTube
- **Playlist Download** -- One-click full playlist downloads
- **Concurrent Queue** -- 3 simultaneous downloads with progress tracking

### Library Management
- **SQLite + FTS5 + WAL** -- Full-text search across title, artist, album
- **Duplicate Detector** -- Audio fingerprinting (AcoustID), metadata, filesize
- **Auto-Organizer** -- Artist/Album folder structure templates
- **Batch Rename** -- Template-based mass renaming
- **Content Filter** -- Kids/Family/Clean modes with AI classification

### Music Player
- **python-mpv** -- Gapless playback, all audio formats
- **10-Band Equalizer** -- Rock, Pop, Jazz, Classical presets
- **4 Visualizers** -- Bars, Waveform, Brain AI, Organic SDF (OpenGL 3.3 + GLSL)
- **Lyrics Display** -- LRC synchronized + Genius API
- **Chord Detection** -- Real-time chord analysis via librosa
- **Keyboard Shortcuts** -- Space=play, arrows=seek, etc.

### AI Features
- **Audio Embeddings** -- 128D feature vectors from numpy FFT analysis
- **Find Similar Songs** -- Cosine similarity search
- **BPM Detection** -- Automatic tempo analysis
- **Mood Classification** -- Happy, Sad, Energetic, Calm

### Cloud & Remote
- **Mobile Remote** -- Flask REST API + JWT auth + QR code pairing
- **Cloud Sync** -- Local folder + Google Drive providers
- **Plugin System** -- 17 hooks, 3 included plugins (PlayCounter, Scrobbler, Discord RPC)
- **Multi-language** -- Spanish/English (274 translation keys)

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| GUI | PySide6 |
| Database | SQLite + FTS5 + WAL |
| Audio | python-mpv (libmpv) + numpy FFT |
| Visualizers | OpenGL 3.3 + GLSL shaders |
| Downloads | yt-dlp |
| Metadata | Mutagen (ID3 tags) |
| APIs | YouTube, Spotify, MusicBrainz, Genius, AcoustID |
| Remote | Flask REST + JWT Bearer auth |
| Packaging | PyInstaller 6.19 + UPX (151 MB) |
| CI/CD | GitHub Actions (test, mypy, bandit, flake8, build) |

## Project Structure

```
src/
├── main.py                 # Entry point (Facade pattern)
├── api/                    # YouTube, Spotify, MusicBrainz, Genius, Chords
├── core/                   # Player, downloads, embeddings, duplicates, metadata
├── controllers/            # Playback, Library, UIComposer, Remote
├── gui/
│   ├── base/               # BaseTab template for tabs
│   ├── tabs/               # 14 tabs
│   ├── widgets/            # 9 custom widgets
│   ├── visualizers/        # Organic SDF visualizer (OpenGL)
│   ├── dialogs/            # API settings, shortcuts
│   └── themes/             # dark.qss, light.qss, style constants
├── services/               # Cloud sync, remote server, content filter
├── plugins/                # Plugin system (17 hooks) + 3 plugins
├── database/               # SQLite manager + 6 SQL migrations
├── workers/                # Download, import, scan workers (BaseWorker)
├── utils/                  # Sanitizer, rate limiter, credentials, constants
└── translations.py         # ES/EN (274 keys)
tests/                      # 52 files, 560+ tests
docs/                       # Architecture, API reference, audit report
```

## API Keys (Optional)

Configure via Tools > Configure API Keys in the app.

| API | Purpose |
|-----|---------|
| YouTube Data v3 | Search |
| Spotify Web API | Alternative search |
| Genius | Lyrics |
| AcoustID | Audio fingerprinting |

Keys are stored in OS keyring (never in code).

## System Requirements

- Windows 10/11 (64-bit)
- 4 GB RAM minimum (8 GB recommended)
- 200 MB storage

## Security

- JWT Bearer authentication on remote API (24h expiration)
- CORS restricted to localhost + server IP
- Path traversal protection with symlink checks
- FTS5 query sanitization (injection prevention)
- Plugin whitelist (default-deny)
- SQL column name allowlists
- Input sanitization on all external data

## Documentation

- `docs/ARCHITECTURE.md` -- System architecture and design patterns
- `docs/API_REFERENCE.md` -- Internal API and REST endpoint reference
- `CHANGELOG.md` -- Version history

## Credits

- **Development:** Ricardo Rojas + NEXUS@CLI
- **Period:** September--December 2025, refactoring + audit March 2026
- **License:** MIT -- Copyright (c) 2025 Ricardo Rojas
