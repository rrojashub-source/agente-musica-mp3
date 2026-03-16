# NEXUS Music Manager - Architecture Documentation

**Version:** 2.1.0 (Refactored)
**Last Updated:** March 15, 2026

---

## System Overview

```
+-----------------------------------------------------------------------------------+
|                           NEXUS Music Manager                                      |
+-----------------------------------------------------------------------------------+
|                                                                                    |
|  +------------------+    +------------------+    +------------------+              |
|  |   GUI Layer      |    |  Controllers     |    |   Services       |              |
|  |   (PySide6)      |<-->|  (Orchestration) |<-->|  (Business)      |              |
|  +------------------+    +------------------+    +------------------+              |
|         |                                              |                           |
|  +------------------+    +------------------+    +------------------+              |
|  |   Core Layer     |    |   API Layer      |    |   Data Layer     |              |
|  |   (Engines)      |    |   (External)     |    |   (SQLite+FTS5)  |              |
|  +------------------+    +------------------+    +------------------+              |
|                                                                                    |
|  +------------------+    +------------------+    +------------------+              |
|  |   Workers        |    |   Plugins        |    |   Utils          |              |
|  |   (Threading)    |    |   (Extensions)   |    |   (Helpers)      |              |
|  +------------------+    +------------------+    +------------------+              |
+-----------------------------------------------------------------------------------+
```

---

## Layer Architecture

### 1. GUI Layer (`src/gui/`)

User interface components using **PySide6** (migrated from PyQt6 in Fase 3).

```
src/gui/
├── base/                    # Base classes
│   ├── base_tab.py          # BaseTab template (shared by all tabs)
│   └── base_worker.py       # BaseWorker (shared by all background workers)
│
├── tabs/                    # 14 application tabs
│   ├── library_tab.py       # Music library browser
│   ├── search_tab.py        # YouTube + Spotify search
│   ├── lyrics_tab.py        # Lyrics display (Genius API)
│   ├── chords_tab.py        # Chord detection + diagram display
│   ├── import_tab.py        # Library import from folders
│   ├── duplicates_tab.py    # Duplicate detection UI
│   ├── organize_tab.py      # Auto-organize library
│   ├── rename_tab.py        # Batch rename files
│   ├── cleanup_tab.py       # Metadata cleanup workflow
│   ├── statistics_tab.py    # Library analytics
│   ├── content_filter_tab.py # Content classification
│   ├── plugins_tab.py       # Plugin management
│   ├── remote_tab.py        # Mobile remote control
│   └── cloud_sync_tab.py    # Cloud synchronization
│
├── widgets/                 # Reusable UI components
│   ├── now_playing_widget.py    # Current song + controls
│   ├── playlist_widget.py       # Playlist sidebar
│   ├── visualizer_widget.py     # Audio visualizer (4 modes)
│   ├── queue_widget.py          # Download queue
│   ├── album_grid_widget.py     # Album cover grid
│   ├── equalizer_widget.py      # EQ sliders
│   ├── recommendations_widget.py # Similar songs
│   ├── skeleton_widget.py       # Loading skeleton placeholder
│   └── chord_diagram_widget.py  # Guitar chord diagrams
│
├── visualizers/             # OpenGL visualizers
│   └── organic_visualizer.py    # Organic SDF visualizer (GLSL)
│
├── dialogs/                 # Modal dialogs
│   ├── api_settings_dialog.py   # API key configuration
│   └── shortcuts_dialog.py      # Keyboard shortcuts
│
└── themes/                  # Visual themes
    ├── dark.qss             # Dark theme stylesheet
    ├── light.qss            # Light theme stylesheet
    └── style_constants.py   # Centralized style constants
```

#### BaseTab Pattern

All tabs inherit from `BaseTab`, which provides:
- Standard layout structure (header, content, status bar)
- Progress reporting via `_update_progress()`
- Worker connection via `connect_worker()`
- Translation support via `tr()`

#### BaseWorker Pattern

All background workers inherit from `BaseWorker`, which provides:
- Standard signals: `progress(int, str)`, `finished(object)`, `error(str)`
- Abstract `do_work()` method with automatic error handling
- Cancellation support via `cancel()` / `is_cancelled`
- Subclasses can override signal signatures (e.g. ChordsAnalyzeWorker uses `progress(str)`)

Workers using BaseWorker (13 total):
- DownloadWorker, LibraryImportWorker, LibraryScanWorker
- ScanWorker (duplicates), OrganizeWorker, RenameWorker
- ChordsAnalyzeWorker, LyricsSearchWorker, ClassificationWorker
- CleanupWorkflowWorker, SpectrumWorker, _SimilarityWorker

### 2. Controllers Layer (`src/controllers/`)

Orchestration layer between GUI and services (Fase 2 refactoring).

```
src/controllers/
├── playback_controller.py   # Audio playback orchestration
├── library_controller.py    # Library operations + signals
├── ui_composer.py           # Main window composition + tab wiring
└── remote_controller.py     # Remote server <-> GUI bridge
```

### 3. Services Layer (`src/services/`)

Business logic decoupled from GUI.

```
src/services/
├── library_service.py       # Library CRUD + signals
├── download_service.py      # Download management + auto-import
├── player_service.py        # Audio control with gapless support
├── cloud_sync_service.py    # Google Drive sync
├── remote_server.py         # Flask REST API + JWT auth
└── content_filter/          # Content classification engine
    ├── classifier.py        # Main classifier
    └── lyrics_analyzer.py   # Lyrics-based analysis
```

### 4. Core Layer (`src/core/`)

Processing engines and business logic.

```
src/core/
├── audio_player.py          # python-mpv audio playback (gapless)
├── audio_embeddings.py      # 128D embeddings for similarity
├── playlist_manager.py      # Playlist CRUD
├── download_queue.py        # Concurrent download manager
├── duplicate_detector.py    # Multi-method duplicate detection
├── library_organizer.py     # Folder structure templates
├── batch_renamer.py         # File renaming with patterns
├── metadata_tagger.py       # ID3 tag writing (Mutagen)
├── metadata_cleaner.py      # Metadata normalization
├── metadata_fetcher.py      # External metadata lookup
├── metadata_autocompleter.py # Auto-complete suggestions
├── cover_art_manager.py     # Album artwork handling
├── mood_classifier.py       # Mood detection (audio features)
├── bpm_detector.py          # BPM detection
├── recommendation_engine.py # Similar song recommendations
├── waveform_extractor.py    # Audio analysis for visualizer
├── spectrum_worker.py       # FFT processing thread
├── theme_manager.py         # Light/Dark theme switching
├── keyboard_shortcuts.py    # Global hotkeys
├── cleanup_workflow.py      # Guided cleanup process
├── acoustid_client.py       # Audio fingerprinting
└── api_adapters.py          # Unified API interface
```

### 5. API Layer (`src/api/`)

External service integrations.

```
src/api/
├── youtube_search.py        # YouTube Data API v3
├── spotify_search.py        # Spotify Web API (spotipy)
├── musicbrainz_client.py    # MusicBrainz metadata
├── genius_client.py         # Genius lyrics API
└── chords_client.py         # Chord detection (librosa + chords-db)
```

**Security:** API keys loaded via centralized `utils/credentials.py` (keyring > env > .env > credentials.json).

### 6. Data Layer (`src/database/`)

SQLite database with FTS5 full-text search and migration system.

```
src/database/
├── manager.py               # Thread-safe DatabaseManager
└── migrations/              # 6 SQL migration files
    ├── 001_initial.sql
    └── ...
```

**Thread Safety:** Uses `threading.local()` for per-thread connections.

### 7. Plugins Layer (`src/plugins/`)

Extensibility system with 17 hook points.

```
src/plugins/
├── plugin_base.py           # Abstract plugin interface
├── plugin_manager.py        # Singleton manager (whitelist default-deny)
└── available/               # 3 plugins
    ├── play_counter.py      # Play count tracking
    ├── scrobbler.py         # Last.fm/ListenBrainz
    └── discord_rpc.py       # Discord Rich Presence
```

### 8. Utils Layer (`src/utils/`)

```
src/utils/
├── input_sanitizer.py       # Security: input validation
├── credentials.py           # Centralized credential loading (4-tier)
├── fpcalc_checker.py        # AcoustID fingerprint checker
├── rate_limiter.py          # API rate limiting
├── constants.py             # Application constants
└── subprocess_patch.py      # PyInstaller subprocess fix
```

---

## Signal Flow Between Layers

```
GUI (tabs/widgets)
    │ user action
    ▼
Controllers (playback, library, ui_composer)
    │ orchestrate
    ▼
Services (library, download, player)
    │ business logic
    ▼
Core (engines) ←→ API (external) ←→ Database (SQLite)
```

Signals flow upward via PySide6 Signal/Slot:
- Core emits → Service relays → Controller handles → GUI updates

---

## Remote Control Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Mobile       │     │ Flask REST   │     │ Remote          │
│ Browser      │────>│ API Server   │────>│ Controller      │
│ (HTML/JS)    │     │ (JWT auth)   │     │ (Signal bridge) │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │                      │
                    Bearer token            PySide6 signals
                    CORS restricted         ▼
                    24h expiration     PlaybackController
```

---

## Security Measures

| Measure | Implementation |
|---------|---------------|
| API keys | OS keyring via `utils/credentials.py` |
| SQL injection | Parameterized queries + column allowlist |
| Path traversal | `validate_path()` with symlink checks |
| Input sanitization | `InputSanitizer` for all user input |
| Remote auth | JWT Bearer tokens (24h expiration) |
| CORS | Restricted to server IP only |
| Plugins | Whitelist default-deny sandbox |
| Thread safety | RLock in AudioPlayer, DownloadQueue |

---

## Quality Assurance

| Tool | Config | Target |
|------|--------|--------|
| pytest | `pytest.ini` (coverage >= 20%) | 1,289 tests |
| mypy | `mypy.ini` (strict mode) | 0 errors, 111 files |
| flake8 | CI + pre-commit | max-line-length=120 |
| bandit | CI security scan | 0 high/critical |
| black | pre-commit hook | Auto-format |
| isort | pre-commit hook | Import sorting |

---

## Dependencies

### Core
- **PySide6** >= 6.6.0 - GUI framework
- **python-mpv** - Audio playback (gapless, all formats)
- **yt-dlp** - YouTube downloads
- **mutagen** - ID3 tag editing
- **numpy** - Audio processing (FFT)

### APIs
- **google-api-python-client** - YouTube Data API
- **spotipy** - Spotify Web API
- **lyricsgenius** - Genius lyrics API
- **musicbrainzngs** - MusicBrainz API

### Security
- **keyring** - Secure credential storage
- **python-dotenv** - Environment configuration

### Build
- **PyInstaller** 6.19 + UPX (151MB bundle)
- **Inno Setup** - Windows installer

---

**Document Version:** 2.1
**Last Updated:** 2026-03-15
