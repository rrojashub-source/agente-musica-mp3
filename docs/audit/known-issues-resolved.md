# Known Issues — Resolved
Claude: Do NOT re-report any issue listed here.

## Cross-module fixes (Audit Rounds 1-3, pre-MAPS)

### Round 1 (2026-03-15) — Thread Safety & Singletons
- [FIXED] ThemeManager missing thread-safe singleton → added double-checked locking
- [FIXED] RemoteServer shared state unprotected → added _data_lock RLock
- [FIXED] DownloadQueue._running reads outside lock → all reads now under _lock
- [FIXED] DownloadQueue missing retry() and clear_all() methods → added

### Round 2 (2026-03-15) — Encapsulation & DRY
- [FIXED] PlaybackController calling 5 private methods on LibraryTab/NowPlayingWidget → added public API (play_next, play_previous, notify_stop, notify_song_ended, toggle_play_pause, stop_playback)
- [FIXED] DownloadService accessing queue._items directly → removed all fallback paths, uses queue public API exclusively
- [FIXED] YouTube artifact regex duplicated in 3 files → extracted to utils/text_normalizer.py
- [FIXED] time.sleep() inside RLock in audio_player.py → restructured to sleep outside lock
- [FIXED] Duplicated PlaybackState enum in player_service.py → unified, imports from core.audio_player
- [FIXED] Dead _tab_specs list in ui_composer.py → removed
- [FIXED] Hardcoded version string "2.0" in ui_composer.py → uses APP_VERSION constant
- [FIXED] API validation duplicated in spotify/youtube search → extracted to api/_validation.py
- [FIXED] Content filter thresholds inline → extracted to ContentScore/ContentClassifier constants

### Round 3 (2026-03-16) — Bugs, Encapsulation & DRY
- [FIXED] LibraryController uses search_input but widget is search_box → fixed attribute names
- [FIXED] library_tab calls song_exists_by_file_path but method is song_exists → fixed method name
- [FIXED] Play count incremented in 3 places (main.py, player_service, statistics_service) → consolidated to LibraryService.increment_play_count(), called from main.py only
- [FIXED] library_tab._delete_selected_songs accesses db.conn.cursor() directly → uses execute_query()
- [FIXED] audio_embeddings accesses db.conn directly in 4 places → uses execute_query/fetch_one
- [FIXED] Dead _check_song_ended timer (pass method + QTimer) in library_tab → removed
- [FIXED] Dead _on_prev_clicked/_on_next_clicked wrappers in library_tab → removed
- [FIXED] LibraryService.update_song re-implements field validation → delegates to DatabaseManager.update_song()
- [FIXED] Spotify search_tracks/albums/artists 95% copy-paste → extracted generic _search() method

## src/controllers/ — MAPS Round 4 (2026-03-16)

### Phase 1: Code Quality (Score: 9/10)
- [FIXED] ui_composer._create_tab_widget mixed tab creation with signal wiring → extracted to _connect_data_changed_signals
- [FIXED] ui_composer called library._load_library (private) → added reload_library() public API
- [FIXED] remote_controller.handle_command used 7-branch if/elif → refactored to dispatch table
- [FIXED] remote_controller play/pause/toggle duplicated set_playing logic → extracted _set_playback_state helper
- [FIXED] remote_controller volume handling inline → extracted _handle_volume method

## src/api/ — MAPS Round 5 (2026-03-16)

### Phase 1: Code Quality (Score: 9.5/10)
- [FIXED] musicbrainz_client: `List[Dict]` without type params (3 places) → `List[Dict[str, Any]]`
- [FIXED] musicbrainz_client: unused `_last_request_time` attribute → removed (rate limiting uses RateLimiter)
- [FIXED] musicbrainz_client: `_extract_genre` had dead `if sorted_tags` branch → simplified

## src/main.py — MAPS Round 6 (2026-03-16)

### Phase 1: Code Quality (Score: 9/10)
- [FIXED] `except (ImportError, RuntimeError, Exception)` — Exception superset made others redundant → simplified to `except Exception`
- [FIXED] `str(e)` inside f-string → `{e}` directly

## src/core/ — MAPS Round 38 (2026-03-17)

### Phase 3: Security (Score: 8.5/10)
- [FIXED] duplicate_detector: os.environ["FPCALC"] race condition → use acoustid.fingerprint_file(fpcalc=...) param directly
- [FIXED] cover_art_manager: download_cover no content-type check → validates image/ MIME type + 10MB size cap
- [FIXED] cover_art_manager: download_cover_from_mbid no MBID validation → UUID regex + path confinement to cover_dir
- [FIXED] library_organizer: build_path no base-path confinement → Path.resolve() + startswith check
- [FIXED] audio_embeddings: MD5 for cache key (Bandit B324) → replaced with SHA256

## src/utils/ — MAPS Round 39 (2026-03-17)

### Phase 3: Security (Score: 8.5/10)
- [FIXED] credentials.py: CREDENTIALS_PATH env var accepted without validation → .json extension check + Path.resolve()
- [FIXED] fpcalc_checker: FPCALC env var used with only exists() check → upgraded to is_file() + sanitized log
- [FIXED] fpcalc_checker: get_checker() singleton not thread-safe → double-checked locking with threading.Lock
- [FIXED] rate_limiter: set_limit() no bounds validation → clamp to [0.01, 100.0], reject zero/negative
- [FIXED] credentials.py: _json_cache and _dotenv_loaded globals not thread-safe → double-checked locking with _creds_lock

## src/controllers/ — MAPS Round 40 (2026-03-17)

### Phase 3: Security (Score: 9/10)
- [FIXED] remote_controller: handle_command logs params at INFO → downgraded to DEBUG
- [FIXED] remote_controller: _handle_volume no validation → int() + clamp [0,100]
- [FIXED] remote_controller: seek handler no validation → int() + max(0, ...)

## src/database/ — MAPS Round 36 (2026-03-17)

### Phase 3: Security (Score: 8.5/10)
- [DOCUMENTED] manager.py: executescript() implicit COMMIT breaks migration rollback — documented as acceptable (static bundled scripts)
- [FIXED] manager.py: update_song logs full updates dict (lyrics, cover_art, embeddings) → logs field names only
- [FIXED] manager.py: db_path accepts arbitrary paths → Path.resolve() + extension validation (.db/.sqlite/.sqlite3)
- [FIXED] manager.py: column names interpolated unquoted in SQL → wrapped in double-quotes for safety

## src/plugins/ — MAPS Round 37 (2026-03-17)

### Phase 3: Security (Score: 8.5/10)
- [FIXED] play_counter/scrobbler plugins: sys.path.insert(0, ...) pollutes host process path → removed
- [FIXED] plugin_manager: save_plugin_settings accepts arbitrary-size dicts → max 10KB validation
- [FIXED] plugin_manager: set_whitelist docstring says "None=allow all" but implementation is "None=bundled only" → fixed docstring
- [FIXED] discord_rpc: app_id setting has no format validation → validates 17-19 digit numeric string
- [FIXED] discord_rpc: on_disable() never unregisters hooks → added unregister for all 4 hooks

## src/services/ — MAPS Round 35 (2026-03-17)

### Phase 3: Security (Score: 9/10)
- [FIXED] remote_server: timing-unsafe token comparison (`!=`) → `hmac.compare_digest()` (side-channel prevention)
- [FIXED] statistics_service: SQL column interpolation via f-string → added frozenset allowlist validation
- [FIXED] remote_server: /api/seek no input validation → `max(0, int())` with try/except
- [FIXED] remote_server: uncapped `limit` param in /api/search and /api/recent → `min(limit, 200)`
- [FIXED] cloud_sync_service: temp files (temp_remote.json, temp_upload.json) not deleted → try/finally cleanup
- [FIXED] cloud_sync_service: Drive query injection in `_find_file()` → escape single quotes + backslashes
- [FIXED] remote_server: callback args logged at INFO (leaks search queries) → downgraded to DEBUG
- [FIXED] content_filter/classifier: non-thread-safe `get_classifier()` singleton → double-checked locking with threading.Lock

## src/api/ — MAPS Round 34 (2026-03-16)

### Phase 3: Security (Score: 9/10)
- [FIXED] musicbrainz_client: download_album_art() SSRF — added domain allowlist (coverartarchive.org, archive.org, etc.)
- [FIXED] musicbrainz_client: download_album_art() path traversal — validates extension + uses Path.resolve()
- [FIXED] musicbrainz_client: download_album_art() no content-type check — validates image/ MIME type
- [FIXED] spotify_search/youtube_search/genius_client: API keys stored as public attributes → renamed to _private
- [FIXED] spotify_search: uncapped Retry-After header allows DoS → capped at 60s
- [FIXED] _cache.py: MD5 hash for cache keys (Bandit B324) → replaced with SHA256
- [FIXED] youtube_search: HttpError log may contain API key → sanitized to only log status/reason
- [FIXED] genius_client: raw title/artist in error log allows log injection → sanitized newlines

## src/gui/tabs/ — MAPS Round 41 (2026-03-17)

### Phase 3: Security (Score: 9/10)
- [FIXED] cloud_sync_tab: Google Drive email logged without sanitization → newline/CR stripping
- [FIXED] content_filter_tab: _move_selected/_copy_selected no path confinement on destination → Path.resolve() + startswith check

## src/gui/widgets/ — MAPS Round 42 (2026-03-17)

### Phase 3: Security (Score: 9.5/10)
- [CLEAN] All 10 files — no security issues found. All operations delegated to protected managers.

## src/gui/dialogs/ — MAPS Round 43 (2026-03-17)

### Phase 3: Security (Score: 9.5/10)
- [CLEAN] All 3 files — credentials via OS keyring, input validated with length+character checks.

## src/workers/ — MAPS Round 44 (2026-03-17)

### Phase 3: Security (Score: 9.5/10)
- [CLEAN] All 3 files — path validation via validate_path(), URL validated upstream in download_queue.

## src/main.py — MAPS Round 45 (2026-03-17)

### Phase 3: Security (Score: 9/10)
- [CLEAN] Credentials via secure fallback chain, safe exception handling, subprocess patch.

## src/gui/base/ — MAPS Round 46 (2026-03-17)

### Phase 3: Security (Score: 9.5/10)
- [CLEAN] All 3 files — pure template code with no I/O, network, or credential handling.

## src/gui/visualizers/ — MAPS Round 47 (2026-03-17)

### Phase 3: Security (Score: 9.5/10)
- [CLEAN] All 2 files — static shaders, clamped audio inputs, GUI-thread execution only.

## src/gui/themes/ — MAPS Round 48 (2026-03-17)

### Phase 3: Security (Score: 10/10)
- [CLEAN] All 2 files — pure constants module, no code execution.

## Phase 4: Performance — MAPS Rounds 49-63 (2026-03-17)

### src/core/ — Round 49 (Score: 8.5/10)
- [FIXED] audio_embeddings find_similar(): N+1 query → batch-load all embeddings in single SELECT
- [FIXED] recommendation_engine: exclude_ids list O(n) → set O(1) membership
- [FIXED] waveform_extractor: unbounded cache → bounded to 50 entries with FIFO eviction

### src/gui/tabs/ — Round 50 (Score: 8.5/10)
- [FIXED] library_tab: table population without blockSignals → setRowCount + blockSignals(True/False)
- [DOCUMENTED] remote_tab QR code fetch on GUI thread (LOW, 5s timeout, acceptable)
- [DOCUMENTED] statistics_tab synchronous refresh (MEDIUM, architectural, uses QTimer.singleShot)

### src/gui/widgets/ — Round 51 (Score: 9/10)
- [FIXED] playlist_widget clear_playing_highlight: O(n) loop → O(1) via _highlighted_row tracking

### src/services/ — Round 52 (Score: 8/10)
- [DOCUMENTED] statistics_service get_summary_stats 9 sequential DB queries (architectural, acceptable)
- [DOCUMENTED] download_service count methods iterate full queue (architectural)
- [DOCUMENTED] lyrics_analyzer keyword matching O(n) per song (acceptable for batch <100)

### src/api/ — Round 53 (Score: 8.5/10)
- [FIXED] _cache.py APICache FIFO eviction → true LRU (pop+reinsert on get())
- [FIXED] chords_client _load_from_db: execute_query→fetch_one (was returning None always)
- [FIXED] chords_client: unbounded memory cache → bounded to 200 entries

### src/database/ — Round 54 (Score: 8/10)
- [DOCUMENTED] batch_clean_titles N+1 UPDATE pattern (acceptable for <1000 songs)

### src/plugins/ — Round 55 (Score: 8.5/10)
- [FIXED] scrobbler: unbounded _scrobble_queue → capped at 100 entries with overflow drop

### src/controllers/ — Round 56 (Score: 8/10)
- [DOCUMENTED] ui_composer spectrum worker .wait() on UI thread (architectural)
- [DOCUMENTED] Modal dialogs .exec() blocks app (standard Qt pattern)

### src/utils/ — Round 57 (Score: 9/10)
- [CLEAN] Minor regex recompilation in input_sanitizer, acceptable for non-hot path

### src/gui/dialogs/ — Round 58 (Score: 8/10)
- [DOCUMENTED] API validation calls on UI thread with timeout (acceptable, user-initiated)

### src/workers/ — Round 59 (Score: 9/10)
- [CLEAN] Proper background threading, no UI blocking

### src/gui/visualizers/ — Round 60 (Score: 8.5/10)
- [FIXED] organic_visualizer: 9× glGetUniformLocation per frame → cached in initializeGL

### src/gui/base/ — Round 61 (Score: 9/10)
- [CLEAN] Template code, lazy property pattern appropriate

### src/main.py — Round 62 (Score: 9/10)
- [CLEAN] Sequential service init acceptable for startup

### src/gui/themes/ — Round 63 (Score: 10/10)
- [CLEAN] Pure constants module

## Intentional decisions (do NOT report as issues)
- [INTENTIONAL] 71 `except Exception` blocks justified with inline comments (GUI error boundaries, plugin isolation, etc.)
- [INTENTIONAL] Coverage threshold at 20% — project is in audit phase, will increase incrementally
- [INTENTIONAL] E501 line length warnings — project uses max-line-length=120 (pre-commit handles formatting)
- [INTENTIONAL] E402 import order in main.py — subprocess_patch MUST import before other modules
- [INTENTIONAL] LibraryTab has no search_box widget yet — LibraryController uses hasattr() guard
