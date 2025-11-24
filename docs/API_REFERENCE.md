# NEXUS Music Manager - API Reference

**Version:** 2.0
**Last Updated:** November 23, 2025

---

## Table of Contents

1. [Database Layer](#database-layer)
2. [Core Engines](#core-engines)
3. [API Clients](#api-clients)
4. [GUI Components](#gui-components)
5. [Utilities](#utilities)
6. [Workers](#workers)

---

## Database Layer

### DatabaseManager (`src/database/manager.py`)

Thread-safe SQLite database manager with FTS5 full-text search.

#### Constructor

```python
DatabaseManager(db_path: str = "data/nexus_music.db")
```

**Parameters:**
- `db_path` - Path to SQLite database file (auto-created if not exists)

#### Methods

##### `get_all_songs(limit: int = None, offset: int = 0) -> List[dict]`
Retrieve songs from the library.

```python
songs = db.get_all_songs(limit=100, offset=0)
# Returns: [{"id": 1, "title": "Song", "artist": "Artist", ...}, ...]
```

##### `search_songs(query: str) -> List[dict]`
Full-text search using FTS5 index.

```python
results = db.search_songs("Bohemian Rhapsody")
# Searches: title, artist, album fields
# Returns: Matching songs sorted by relevance
```

##### `add_song(song_data: dict) -> int`
Add a new song to the library.

```python
song_id = db.add_song({
    "title": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "file_path": "/path/to/song.mp3",
    "duration": 240,  # seconds
    "bitrate": 320,   # kbps
})
```

##### `delete_song(song_id: int) -> bool`
Delete a song by ID.

##### `get_song_by_id(song_id: int) -> dict`
Get a single song by ID.

##### `update_song(song_id: int, data: dict) -> bool`
Update song metadata.

##### `close()`
Close all database connections (thread-safe).

---

## Core Engines

### AudioPlayer (`src/core/audio_player.py`)

Pygame-based audio playback engine.

#### Signals (PyQt6)

| Signal | Parameters | Description |
|--------|------------|-------------|
| `position_changed` | `int` (ms) | Emitted every 100ms with current position |
| `playback_finished` | - | Emitted when song ends |
| `error_occurred` | `str` | Emitted on playback error |

#### Methods

##### `play(file_path: str)`
Start playing an audio file.

```python
player.play("/path/to/song.mp3")
```

##### `pause()`
Pause playback (can be resumed).

##### `resume()`
Resume paused playback.

##### `stop()`
Stop playback completely.

##### `set_position(position_ms: int)`
Seek to position in milliseconds.

##### `set_volume(volume: int)`
Set volume (0-100).

##### `get_position() -> int`
Get current position in milliseconds.

##### `get_duration() -> int`
Get total duration in milliseconds.

##### `is_playing() -> bool`
Check if currently playing.

---

### DownloadQueue (`src/core/download_queue.py`)

Concurrent download manager with progress tracking.

#### Signals (PyQt6)

| Signal | Parameters | Description |
|--------|------------|-------------|
| `progress_updated` | `str, int` (item_id, progress%) | Download progress update |
| `download_complete` | `str, dict` (item_id, result) | Download finished successfully |
| `download_failed` | `str, str` (item_id, error) | Download failed |
| `queue_empty` | - | All downloads completed |

#### Methods

##### `add_to_queue(item: dict) -> str`
Add item to download queue.

```python
item_id = queue.add_to_queue({
    "title": "Song Title",
    "artist": "Artist",
    "url": "https://youtube.com/watch?v=...",
    "output_dir": "/downloads"
})
```

##### `start_downloads()`
Begin processing the queue.

##### `pause_downloads()`
Pause all active downloads.

##### `cancel_download(item_id: str)`
Cancel a specific download.

##### `clear_completed()`
Remove completed items from queue.

##### `get_queue_status() -> dict`
Get current queue state.

```python
status = queue.get_queue_status()
# Returns: {"pending": 5, "active": 3, "completed": 10, "failed": 1}
```

---

### PlaylistManager (`src/core/playlist_manager.py`)

Playlist CRUD operations.

#### Methods

##### `create_playlist(name: str) -> int`
Create a new playlist.

##### `delete_playlist(playlist_id: int) -> bool`
Delete a playlist.

##### `rename_playlist(playlist_id: int, new_name: str) -> bool`
Rename a playlist.

##### `get_all_playlists() -> List[dict]`
Get all playlists with song counts.

##### `get_playlist_songs(playlist_id: int) -> List[dict]`
Get all songs in a playlist.

##### `add_song_to_playlist(playlist_id: int, song_id: int) -> bool`
Add a song to a playlist.

##### `remove_song_from_playlist(playlist_id: int, song_id: int) -> bool`
Remove a song from a playlist.

##### `reorder_playlist(playlist_id: int, song_ids: List[int]) -> bool`
Set new order for playlist songs.

---

### DuplicateDetector (`src/core/duplicate_detector.py`)

Multi-method duplicate detection.

#### Methods

##### `find_duplicates(method: str = "metadata") -> List[tuple]`
Find duplicate songs.

**Methods:**
- `"metadata"` - Match by title + artist
- `"fingerprint"` - Audio fingerprint (AcoustID)
- `"filesize"` - Match by file size + duration

```python
detector = DuplicateDetector(db_manager)
duplicates = detector.find_duplicates(method="metadata")
# Returns: [(song1_id, song2_id, similarity_score), ...]
```

---

## API Clients

### YouTubeSearch (`src/api/youtube_search.py`)

YouTube Data API v3 wrapper.

#### Methods

##### `search(query: str, max_results: int = 10) -> List[dict]`
Search YouTube for videos.

```python
results = youtube.search("Queen Bohemian Rhapsody", max_results=5)
# Returns: [{"video_id": "abc", "title": "...", "channel": "...", "duration": "5:55"}, ...]
```

##### `get_video_info(video_id: str) -> dict`
Get detailed video information.

---

### SpotifySearch (`src/api/spotify_search.py`)

Spotify Web API wrapper.

#### Methods

##### `search(query: str, search_type: str = "track", limit: int = 10) -> List[dict]`
Search Spotify catalog.

```python
results = spotify.search("Bohemian Rhapsody", search_type="track")
# Returns: [{"spotify_id": "...", "title": "...", "artist": "...", "album": "..."}, ...]
```

---

### GeniusClient (`src/api/genius_client.py`)

Genius lyrics API wrapper.

#### Methods

##### `search_song(title: str, artist: str) -> dict`
Search for a song on Genius.

##### `get_lyrics(song_url: str) -> str`
Fetch lyrics from a Genius URL.

```python
lyrics = genius.get_lyrics("https://genius.com/Queen-bohemian-rhapsody-lyrics")
# Returns: Full lyrics text
```

---

### MusicBrainzClient (`src/api/musicbrainz_client.py`)

MusicBrainz metadata API.

#### Methods

##### `search_recording(title: str, artist: str) -> List[dict]`
Search for recordings.

##### `get_release_info(mbid: str) -> dict`
Get album/release information.

---

## GUI Components

### LibraryTab (`src/gui/tabs/library_tab.py`)

Main library browser with table view.

#### Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `song_selected` | `int` (song_id) | Single-click selection |
| `play_song_requested` | `int` (song_id) | Double-click to play |
| `add_to_playlist_requested` | `int, int` | Add song to playlist |

---

### NowPlayingWidget (`src/gui/widgets/now_playing_widget.py`)

Current song display with playback controls.

#### Methods

##### `set_song(song_data: dict)`
Display a song's information.

##### `clear()`
Reset widget to initial state.

##### `set_playing(is_playing: bool)`
Update play/pause button state.

---

### VisualizerWidget (`src/gui/widgets/visualizer_widget.py`)

Real-time audio visualization.

#### Methods

##### `set_style(style: str)`
Set visualization style.

**Styles:**
- `"bars"` - Classic frequency bars
- `"circular"` - Radial visualization
- `"brain_ai"` - Neural network particles

##### `update_data(audio_data: np.ndarray)`
Feed audio data for visualization.

##### `start()` / `stop()`
Control visualization timer.

---

## Utilities

### InputSanitizer (`src/utils/input_sanitizer.py`)

Security utilities for input validation.

#### Functions

##### `sanitize_query(query: str, max_length: int = 500) -> str`
Sanitize user input for API queries.

```python
safe_query = sanitize_query("test'; DROP TABLE;--")
# Returns: "test DROP TABLE--"
```

##### `sanitize_filename(filename: str, max_length: int = 255) -> str`
Sanitize filename for filesystem safety.

```python
safe_name = sanitize_filename("song:with*bad|chars.mp3")
# Returns: "song_with_bad_chars.mp3"
```

##### `validate_path(path: str, base_dir: str) -> tuple[bool, str]`
Validate path to prevent directory traversal.

```python
is_valid, result = validate_path("../../../etc/passwd", "/home/user/music")
# Returns: (False, "Path escapes base directory")
```

##### `sanitize_url(url: str, allowed_domains: list = None) -> tuple[bool, str]`
Validate and sanitize URLs.

```python
is_valid, url = sanitize_url("https://youtube.com/watch?v=abc", ["youtube.com"])
# Returns: (True, "https://youtube.com/watch?v=abc")
```

##### `sanitize_metadata(metadata: dict) -> dict`
Sanitize metadata from external sources.

---

## Workers

### DownloadWorker (`src/workers/download_worker.py`)

Background thread for yt-dlp downloads.

#### Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `progress` | `int` | Download progress 0-100 |
| `finished` | `dict` | Download result |
| `error` | `str` | Error message |

---

### LibraryImportWorker (`src/workers/library_import_worker.py`)

Background thread for folder scanning.

#### Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `progress` | `int, int` | (current, total) files processed |
| `file_found` | `dict` | New song discovered |
| `finished` | `int` | Total songs imported |

---

## Configuration

### ConfigManager (`src/config_manager.py`)

Application settings management.

#### Methods

##### `get(key: str, default: Any = None) -> Any`
Get a configuration value.

##### `set(key: str, value: Any)`
Set a configuration value.

##### `save()`
Persist configuration to disk.

**Common Keys:**
- `downloads_dir` - Download output directory
- `theme` - "dark" or "light"
- `language` - "es" or "en"
- `max_concurrent_downloads` - 1-5
- `default_audio_quality` - "320" or "192"

---

## Error Handling

All methods that can fail return appropriate values or raise exceptions:

```python
try:
    result = db.add_song(song_data)
except DatabaseError as e:
    logger.error(f"Database error: {e}")
except ValidationError as e:
    logger.error(f"Invalid data: {e}")
```

---

## Thread Safety

- `DatabaseManager` - Thread-safe via `threading.local()`
- `DownloadQueue` - Thread-safe via `ThreadPoolExecutor`
- GUI widgets - Must be accessed from main thread only
- Use signals to communicate between threads and GUI

---

**Document Version:** 1.0
**Created by:** NEXUS@CLI
