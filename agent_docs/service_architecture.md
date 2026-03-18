# Service Architecture

## Layer Diagram

```
GUI Layer (PySide6)  <-->  Controllers (Orchestration)  <-->  Services (Business)
       |                                                          |
Core Layer (Engines)       API Layer (External)            Data Layer (SQLite+FTS5)
       |                                                          |
Workers (Threading)        Plugins (Extensions)            Utils (Helpers)
```

## Source Structure

```
src/
├── main.py                 # Entry point — Facade (340 LOC, delegates to controllers)
├── api/                    # External API clients
│   ├── youtube_search.py   # YouTube Data API v3
│   ├── spotify_search.py   # Spotify Web API (spotipy)
│   ├── musicbrainz_client.py  # MusicBrainz + cover art
│   ├── genius_client.py    # Genius lyrics API
│   ├── chords_client.py    # Chord detection (librosa)
│   ├── _cache.py           # LRU API response cache (SHA256 keys)
│   └── _validation.py      # Shared API input validation
├── core/                   # Business logic engines
│   ├── audio_player.py     # python-mpv wrapper (gapless, RLock)
│   ├── download_queue.py   # Thread-safe download queue
│   ├── audio_embeddings.py # 128D embeddings + similarity (sklearn)
│   ├── duplicate_detector.py  # Hash, fingerprint, metadata detection
│   ├── library_organizer.py   # File organization by template
│   ├── cover_art_manager.py   # Album art download + cache
│   ├── metadata_manager.py    # Mutagen tag read/write
│   ├── player_service.py      # Playback state machine
│   ├── library_service.py     # Library CRUD operations
│   ├── recommendation_engine.py  # IA recommendations
│   └── waveform_extractor.py    # numpy FFT analysis
├── controllers/            # Orchestration layer
│   ├── playback_controller.py  # Play/pause/next/prev coordination
│   ├── library_controller.py   # Library operations coordination
│   ├── ui_composer.py          # Tab creation + signal wiring
│   └── remote_controller.py    # Remote API command dispatch
├── gui/
│   ├── base/               # Templates
│   │   ├── base_tab.py     # BaseTab (layout, progress, workers)
│   │   └── base_worker.py  # BaseWorker (signals, do_work, cancellation)
│   ├── tabs/               # 14 tabs (all extend BaseTab)
│   ├── widgets/            # 9 custom widgets (playlist, now_playing, etc.)
│   ├── visualizers/        # Organic SDF visualizer (OpenGL 3.3 + GLSL)
│   ├── dialogs/            # API settings, keyboard shortcuts
│   └── themes/             # dark.qss, light.qss, style_constants.py
├── services/               # Business services
│   ├── cloud_sync_service.py   # Google Drive sync
│   ├── remote_server.py        # Flask REST API + JWT
│   ├── content_filter.py       # Content classification
│   ├── statistics_service.py   # Playback stats
│   └── download_service.py     # Download orchestration
├── plugins/                # Plugin system
│   ├── plugin_manager.py   # 17 hooks, whitelist default-deny
│   ├── play_counter.py     # Play count tracking plugin
│   ├── scrobbler.py        # Last.fm scrobbling plugin
│   └── discord_rpc.py      # Discord Rich Presence plugin
├── database/
│   ├── manager.py          # SQLite + FTS5 + WAL + migrations
│   └── migrations/         # 6 SQL migration files
├── workers/
│   ├── download_worker.py     # Background download thread
│   └── library_import_worker.py  # Library scan thread
├── utils/
│   ├── credentials.py      # 4-tier fallback (keyring > env > .env > JSON)
│   ├── input_sanitizer.py  # Path validation, symlink checks
│   ├── rate_limiter.py     # Token bucket rate limiter
│   ├── constants.py        # App-wide constants
│   └── subprocess_patch.py # Windows subprocess CREATE_NO_WINDOW
└── translations.py         # ES/EN (274 keys)
```

## Design Patterns

- **Facade** — main.py (340 LOC) delegates to 4 controllers
- **BaseTab** — Template for all 14 tabs (layout, progress bar, worker management)
- **BaseWorker** — Template for 12/13 workers (signals, do_work(), cancellation)
- **Controllers** — PlaybackController, LibraryController, UIComposer, RemoteController
- **Style Constants** — gui/themes/style_constants.py replaces inline styles
- **Credential Utility** — utils/credentials.py with 4-level fallback

## Security Model

1. **Auth** — JWT Bearer tokens (24h expiration + refresh endpoint)
2. **CORS** — Restricted to specific server IP (not wildcard)
3. **Path traversal** — validate_path() with symlink checks
4. **Plugins** — Whitelist default-deny (including load_plugin_class)
5. **Thread-safety** — RLock in audio_player, download_queue; Lock for singletons
6. **SQL injection** — Column allowlist in manager.py and library_service.py
7. **FTS5 injection** — Query sanitization in search_songs()
8. **Credentials** — Centralized in utils/credentials.py (never hardcoded)
9. **SSRF** — Domain allowlist for cover art downloads
10. **Timing attacks** — hmac.compare_digest() for token comparison

## Database

- **Engine:** SQLite 3 with FTS5 (full-text search) + WAL mode
- **File:** music_library.db (68 songs in test DB)
- **Migrations:** 6 SQL files in database/migrations/
- **Thread safety:** threading.local() for per-thread connections
