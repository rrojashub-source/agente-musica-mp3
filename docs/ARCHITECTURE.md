# NEXUS Music Manager - Architecture Documentation

**Version:** 2.0 (Production)
**Last Updated:** November 23, 2025

---

## System Overview

```
+-----------------------------------------------------------------------------------+
|                           NEXUS Music Manager                                      |
+-----------------------------------------------------------------------------------+
|                                                                                    |
|  +------------------+    +------------------+    +------------------+              |
|  |   GUI Layer      |    |   Core Layer     |    |   Data Layer     |              |
|  |   (PyQt6)        |<-->|   (Business)     |<-->|   (SQLite)       |              |
|  +------------------+    +------------------+    +------------------+              |
|                                                                                    |
|  +------------------+    +------------------+    +------------------+              |
|  |   API Layer      |    |   Workers        |    |   Utils          |              |
|  |   (External)     |    |   (Threading)    |    |   (Helpers)      |              |
|  +------------------+    +------------------+    +------------------+              |
|                                                                                    |
+-----------------------------------------------------------------------------------+
```

---

## Layer Architecture

### 1. GUI Layer (`src/gui/`)

Responsible for all user interface components using PyQt6.

```
src/gui/
├── tabs/                    # Main application tabs
│   ├── library_tab.py       # Music library browser (10k+ songs)
│   ├── search_tab.py        # YouTube + Spotify search
│   ├── lyrics_tab.py        # Lyrics display (Genius API)
│   ├── import_tab.py        # Library import from folders
│   ├── duplicates_tab.py    # Duplicate detection UI
│   ├── organize_tab.py      # Auto-organize library
│   ├── rename_tab.py        # Batch rename files
│   └── cleanup_tab.py       # Metadata cleanup
│
├── widgets/                 # Reusable UI components
│   ├── now_playing_widget.py    # Current song display + controls
│   ├── playlist_widget.py       # Playlist management sidebar
│   ├── visualizer_widget.py     # Audio visualizer (Bars/Circular/Brain AI)
│   └── queue_widget.py          # Download queue display
│
├── dialogs/                 # Modal dialogs
│   ├── api_settings_dialog.py   # API key configuration
│   └── shortcuts_dialog.py      # Keyboard shortcuts reference
│
└── themes/                  # Visual themes
    └── __init__.py          # Theme definitions
```

### 2. Core Layer (`src/core/`)

Business logic and processing engines.

```
src/core/
├── audio_player.py          # Pygame-based audio playback
├── playlist_manager.py      # Playlist CRUD operations
├── download_queue.py        # Concurrent download manager (3 workers)
├── duplicate_detector.py    # Multi-method duplicate detection
├── library_organizer.py     # Folder structure templates
├── batch_renamer.py         # File renaming with patterns
├── metadata_tagger.py       # ID3 tag writing (Mutagen)
├── metadata_cleaner.py      # Metadata normalization
├── metadata_fetcher.py      # External metadata lookup
├── metadata_autocompleter.py # Auto-complete suggestions
├── cover_art_manager.py     # Album artwork handling
├── waveform_extractor.py    # Audio analysis for visualizer
├── spectrum_worker.py       # FFT processing thread
├── theme_manager.py         # Light/Dark theme switching
├── keyboard_shortcuts.py    # Global hotkeys (Space=Play/Pause)
├── cleanup_workflow.py      # Guided cleanup process
├── acoustid_client.py       # Audio fingerprinting
└── api_adapters.py          # Unified API interface
```

### 3. Data Layer (`src/database/`)

SQLite database with FTS5 full-text search.

```
src/database/
└── manager.py               # Thread-safe DatabaseManager
    ├── Songs table          # Core music metadata
    ├── Playlists table      # User playlists
    ├── PlaylistSongs table  # M:N relationship
    ├── Downloads table      # Download history
    └── FTS5 index           # Full-text search (<100ms)
```

**Thread Safety:** Uses `threading.local()` for per-thread connections.

### 4. API Layer (`src/api/`)

External service integrations.

```
src/api/
├── youtube_search.py        # YouTube Data API v3
├── spotify_search.py        # Spotify Web API (spotipy)
├── musicbrainz_client.py    # MusicBrainz metadata
└── genius_client.py         # Genius lyrics API
```

**Security:** API keys stored in OS keyring (encrypted).

### 5. Workers Layer (`src/workers/`)

Background processing threads.

```
src/workers/
├── download_worker.py       # yt-dlp download thread
└── library_import_worker.py # Folder scanning thread
```

### 6. Utils Layer (`src/utils/`)

Helper utilities.

```
src/utils/
├── input_sanitizer.py       # Security: Input validation
└── fpcalc_checker.py        # AcoustID fingerprint checker
```

---

## Data Flow Diagrams

### Search & Download Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   User      │     │  SearchTab   │     │  YouTube    │
│   Input     │────>│  (GUI)       │────>│  API        │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                    │
                           │ Results            │ Search
                           ▼                    ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  QueueWidget │<────│  Spotify    │
                    │  (GUI)       │     │  API        │
                    └──────────────┘     └─────────────┘
                           │
                           │ Add to Queue
                           ▼
                    ┌──────────────┐     ┌─────────────┐
                    │ DownloadQueue│────>│  yt-dlp     │
                    │  (Core)      │     │  (Download) │
                    └──────────────┘     └─────────────┘
                           │
                           │ Complete
                           ▼
                    ┌──────────────┐     ┌─────────────┐
                    │ MetadataTagger────>│  MusicBrainz│
                    │  (Core)      │     │  (Metadata) │
                    └──────────────┘     └─────────────┘
                           │
                           │ Tagged MP3
                           ▼
                    ┌──────────────┐
                    │ DatabaseManager
                    │  (Auto-import)│
                    └──────────────┘
```

### Playback Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ LibraryTab  │     │ NowPlaying   │     │ AudioPlayer │
│ (Double-click)───>│  Widget      │────>│  (Pygame)   │
└─────────────┘     └──────────────┘     └─────────────┘
      │                    │                    │
      │                    │ Position           │ Audio Data
      │                    ▼                    ▼
      │             ┌──────────────┐     ┌─────────────┐
      │             │ ProgressBar  │     │ Waveform    │
      │             │ (Seek)       │     │ Extractor   │
      │             └──────────────┘     └─────────────┘
      │                                        │
      │                                        │ FFT
      │                                        ▼
      │                                 ┌─────────────┐
      │                                 │ Visualizer  │
      │                                 │ (Bars/AI)   │
      │                                 └─────────────┘
      │
      │ Also plays from:
      ▼
┌─────────────┐
│ PlaylistWidget
│ (Sidebar)   │
└─────────────┘
```

---

## Key Components

### DatabaseManager (`src/database/manager.py`)

Thread-safe SQLite wrapper with connection pooling.

```python
class DatabaseManager:
    def __init__(self, db_path="data/nexus_music.db"):
        self._local = threading.local()  # Per-thread connections
        self._connections = []           # Track all connections
        self._lock = threading.Lock()    # Protect connection list

    @property
    def conn(self) -> sqlite3.Connection:
        """Returns thread-local connection (creates if needed)"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = self._create_connection()
        return self._local.conn
```

### DownloadQueue (`src/core/download_queue.py`)

Concurrent download manager with progress tracking.

```python
class DownloadQueue(QObject):
    progress_updated = pyqtSignal(str, int)  # item_id, progress
    download_complete = pyqtSignal(str, dict) # item_id, result

    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queue = {}  # Active downloads
```

**Fixed Bug:** Lambda closure capture by value for progress callbacks.

### AudioPlayer (`src/core/audio_player.py`)

Pygame-based audio playback with position tracking.

```python
class AudioPlayer(QObject):
    position_changed = pyqtSignal(int)  # Current position in ms
    playback_finished = pyqtSignal()

    def play(self, file_path: str):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
```

### VisualizerWidget (`src/gui/widgets/visualizer_widget.py`)

Real-time audio visualization with 3 styles.

- **Bars:** Classic frequency bars
- **Circular:** Radial visualization
- **Brain AI:** Particle-based neural network effect (250 particles)

---

## Security Measures

### Input Validation (`src/utils/input_sanitizer.py`)

```python
class InputSanitizer:
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Remove dangerous characters from filenames"""

    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Prevent injection in search queries"""

    @staticmethod
    def validate_path(path: str, base_dir: str) -> bool:
        """Prevent path traversal attacks"""
```

### API Key Storage

- Keys stored in OS keyring (Windows Credential Manager / macOS Keychain)
- Never logged or displayed in full
- Service names: `nexus_youtube_api`, `nexus_spotify_*`, `nexus_genius_api`

### SQL Injection Prevention

- All queries use parameterized statements
- No string concatenation for user input

---

## Performance Optimizations

| Component | Optimization | Impact |
|-----------|-------------|--------|
| Database | FTS5 full-text search | <100ms search on 10k+ songs |
| Database | WAL journal mode | Concurrent reads/writes |
| Database | Connection pooling | Thread-safe, no locks |
| Library | Lazy loading | Only visible rows loaded |
| Visualizer | 30 FPS cap | CPU ~10% (was ~20%) |
| Brain AI | 250 particles | CPU reduced 50% |
| Downloads | 3 concurrent workers | Optimal throughput |

---

## File Structure

```
AGENTE_MUSICA_MP3/
├── src/                     # Source code
│   ├── main.py              # Application entry point
│   ├── api/                 # External API clients
│   ├── core/                # Business logic
│   ├── database/            # Data access layer
│   ├── gui/                 # User interface
│   ├── utils/               # Utilities
│   └── workers/             # Background threads
│
├── data/                    # Runtime data
│   └── nexus_music.db       # SQLite database
│
├── downloads/               # Downloaded MP3s
│
├── tests/                   # Test suite (148 tests)
│   ├── test_*.py            # Unit tests
│   └── conftest.py          # Pytest fixtures
│
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # This file
│   ├── plans/               # Roadmaps and plans
│   └── architecture/        # Technical reviews
│
├── requirements.txt         # Python dependencies
├── setup.py                 # Package configuration
├── LICENSE                  # MIT License
└── README.md                # Project overview
```

---

## Dependencies

### Core
- **PyQt6** >= 6.5.0 - GUI framework
- **pygame** >= 2.5.0 - Audio playback
- **yt-dlp** >= 2023.10.13 - YouTube downloads
- **mutagen** >= 1.47.0 - ID3 tag editing
- **numpy** >= 1.24.0 - Audio processing

### APIs
- **google-api-python-client** - YouTube Data API
- **spotipy** >= 2.23.0 - Spotify Web API
- **lyricsgenius** >= 3.0.1 - Genius lyrics API
- **musicbrainzngs** >= 0.7.1 - MusicBrainz API

### Security
- **keyring** >= 24.0.0 - Secure credential storage
- **python-dotenv** >= 1.0.0 - Environment configuration

---

## Entry Points

### Main Application
```bash
python src/main.py
```

### Windows Launcher
```bash
LAUNCH_NEXUS_MUSIC.bat
```

### Tests
```bash
pytest tests/ -v
```

---

## Future Architecture (Planned)

### Service Layer (Phase 8)
```
src/services/
├── library_service.py       # Library operations
├── download_service.py      # Download management
├── playback_service.py      # Audio control
└── playlist_service.py      # Playlist operations
```

This will decouple GUI from business logic, enabling:
- Easier testing (no PyQt dependency)
- Future CLI interface
- Potential REST API

---

**Document Version:** 1.0
**Created by:** NEXUS@CLI
