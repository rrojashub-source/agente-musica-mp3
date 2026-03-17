# Scoring History

| Date | Module | Phase | Score Before | Score After | Issues Fixed |
|------|--------|-------|-------------|------------|--------------|
| 2026-03-15 | cross-module | Quality | 6.8/10 | 7.6/10 | Round 1: 7 fixes (singletons, thread safety, DRY) |
| 2026-03-15 | cross-module | Quality | 7.6/10 | ~7.5/10 | Round 2: 9 fixes (encapsulation, DRY, dead code) |
| 2026-03-16 | cross-module | Quality | ~7.0/10 | ~7.5/10 | Round 3: 9 fixes (bugs, encapsulation, DRY) |

| 2026-03-16 | src/controllers/ | Code Quality | 8/10 | 9/10 | MAPS Round 4: dispatch table, signal extraction, public API |
| 2026-03-16 | src/api/ | Code Quality | 8/10 | 9.5/10 | MAPS Round 5: type annotations, dead code, simplification |
| 2026-03-16 | src/main.py | Code Quality | 8/10 | 9/10 | MAPS Round 6: redundant except, str(e) cleanup |
| 2026-03-16 | src/gui/themes/ | Code Quality | — | 9.5/10 | MAPS Round 7: no fixes needed, clean constants |
| 2026-03-16 | src/gui/base/ | Code Quality | — | 9.5/10 | MAPS Round 8: no fixes needed, clean templates |
| 2026-03-16 | src/workers/ | Code Quality | — | 9/10 | MAPS Round 9: no fixes needed, BaseWorker pattern |
| 2026-03-16 | src/gui/visualizers/ | Code Quality | — | 9/10 | MAPS Round 10: unused param noted, OpenGL DRY acceptable |
| 2026-03-16 | src/database/ | Code Quality | — | 9/10 | MAPS Round 11: dead SQL in LIKE fallback removed |
| 2026-03-16 | src/plugins/ | Code Quality | — | 9/10 | MAPS Round 12: no fixes needed, clean security model |
| 2026-03-16 | src/gui/dialogs/ | Code Quality | — | 9/10 | MAPS Round 13: 3x redundant str(e) in f-strings |
| 2026-03-16 | src/utils/ | Code Quality | — | 9/10 | MAPS Round 14: redundant except, unnecessary Path conversion |
| 2026-03-16 | src/services/ | Code Quality | — | 9/10 | MAPS Round 15: 4 fixes (redundant comprehension, str(e), duplicate import, dead var) |
| 2026-03-16 | src/gui/widgets/ | Code Quality | — | 9/10 | MAPS Round 16: 6 fixes (120 LOC dead code, redundant imports, double assignment, str(e)) |
| 2026-03-16 | src/gui/tabs/ | Code Quality | — | 9/10 | MAPS Round 17: 8 fixes (13× redundant local imports → module-level, dead variable, 2× str(e)) |
| 2026-03-16 | src/core/ | Code Quality | ~7/10 | 9/10 | MAPS Round 18: 7 fixes (2× local import re, 3× str(e), 3× dead variables, 1× redundant import) |

| 2026-03-16 | src/gui/themes/ | Tests | — | 100% | MAPS Round 19: auto-approved, constants-only module fully covered |
| 2026-03-16 | src/utils/ | Tests | — | 83% | MAPS Round 20: auto-approved, 9 files already at 83% aggregate coverage |
| 2026-03-16 | src/api/ | Tests | ~76% | 88% | MAPS Round 21: +36 unit tests (_cache 100%, spotify 98%, youtube 80%, chords 83%) |
| 2026-03-16 | src/plugins/ | Tests | ~70% | 84% | MAPS Round 22: +34 tests (manager 90%, play_counter 88%, discord 61%, base 96%) |
| 2026-03-16 | src/database/ | Tests | ~53% | 81% | MAPS Round 23: +26 tests (CRUD, cleanup_orphans, LIKE fallback, context manager) |
| 2026-03-16 | src/workers/ | Tests | ~35% | 98% | MAPS Round 24: +30 tests (extract_metadata, _scan_folder, _process_file all branches, DownloadWorker path validation + progress) |
| 2026-03-16 | src/controllers/ | Tests | ~36% | 83% | MAPS Round 25: +68 tests (library 100%, playback 100%, remote 100%, ui_composer 58%) |
| 2026-03-16 | src/services/ | Tests | ~66% | 82% | MAPS Round 26: +187 tests (statistics 100%, classifier 97%, download 92%, library 88%, lyrics 86%, player 84%, remote 82%, spotify 82%, cloud 69%, audio 50%) |
| 2026-03-16 | src/core/ | Tests | ~73% | 80% | MAPS Round 27: +148 tests (playlist_manager 99%, smart_playlist 96%, audio_feature 95%, metadata_tagger 95%, equalizer 94%, metadata_cleaner 94%, lrc_parser 93%, recommendation 93%, cover_art 92%, library_organizer 91%, bpm 88%, metadata_fetcher 88%, autocompleter 96%, duplicate 81%, cleanup 80%) |
| 2026-03-16 | src/main.py | Tests | 0% | 87% | MAPS Round 28: +17 tests (closeEvent, _on_song_play_started, _init_services, _init_controllers, _connect_signals, main entry point). Pattern: QMainWindow real-class patch for Shiboken bypass |
| 2026-03-16 | src/gui/base/ | Tests | 39% | 100% | MAPS Round 29: +32 tests (BaseTab init/layout/progress/worker/dialogs, BaseWorker cancel). Pattern: QWidget real-class replacement for mock PySide6 |
| 2026-03-16 | src/gui/dialogs/ | Tests | ~12% | 96% | MAPS Round 30: +42 tests (APITabWidget init/load/validate 4 APIs, SpotifyTabWidget init/load/validate/clear, APISettingsDialog init/save/help, ShortcutsDialog). Pattern: QFrame.Shape enum + local QMessageBox import via sys.modules |
| 2026-03-16 | src/gui/visualizers/ | Tests | 0% | 87% | MAPS Round 31: +51 tests (fallback init, update_audio 7 beat branches, update_from_fft, _average_bins edge cases, set_style 4 presets, _on_timer attack/decay, GL early returns, mocked OpenGL paths: initializeGL/paintGL/_setup_quad/cleanup). Pattern: OPENGL_AVAILABLE patch + GL function mocks |
| 2026-03-16 | src/gui/widgets/ | Tests | 0% | 88% | MAPS Round 32: +394 tests (9 widget files). chord_diagram 93%, equalizer 99%, now_playing 97%, playlist 92%, queue 80%, recommendations 88%, skeleton 88%, visualizer 85%, album_grid 59%. Pattern: __dict__ method extraction + __getattr__ base class for constructor coverage + module-level QMessageBox/QInputDialog/QFileDialog patches |
| 2026-03-16 | src/gui/tabs/ | Tests | 0% | 81% | MAPS Round 33: +284 tests (15 tab files). statistics 99%, chords 94%, lyrics 94%, remote 86%, cloud_sync 85%, cleanup 84%, organize 84%, search 83%, rename 82%, import 81%, plugins 76%, library 75%, duplicates 75%, content_filter 66%. Pattern: _base type with __getattr__ + 25 Qt type replacements + BaseTab/BaseWorker property delattr + __dict__ method extraction |

| 2026-03-16 | src/api/ | Security | 7/10 | 9/10 | MAPS Round 34: 6 fixes (SSRF+path traversal in download_album_art, credentials as public attrs→private, uncapped Retry-After→60s max, MD5→SHA256 cache key, HttpError log sanitized, log injection prevention). Bandit: 0 issues |
| 2026-03-17 | src/services/ | Security | 7/10 | 9/10 | MAPS Round 35: 8 fixes (timing-safe token compare via hmac, SQL column allowlist, seek input validation, limit cap 200, temp file cleanup, Drive query injection escape, callback args→DEBUG, classifier thread-safe singleton) |
| 2026-03-17 | src/database/ | Security | 7.5/10 | 8.5/10 | MAPS Round 36: 4 fixes (executescript rollback documented, update_song log→field names only, db_path resolve+extension validation, quoted column identifiers in SQL) |
| 2026-03-17 | src/plugins/ | Security | 6.5/10 | 8.5/10 | MAPS Round 37: 5 fixes (sys.path.insert removed from 2 plugins, settings size validation 10KB max, set_whitelist docstring fixed, Discord app_id format validation, on_disable hook unregister) |
| 2026-03-17 | src/core/ | Security | 7.5/10 | 8.5/10 | MAPS Round 38: 4 fixes (FPCALC env race→fpcalc param, cover_art MBID validation+content-type+size cap+path confinement, library_organizer path traversal prevention, MD5→SHA256 in audio_embeddings) |
| 2026-03-17 | src/utils/ | Security | 6.5/10 | 8.5/10 | MAPS Round 39: 5 fixes (CREDENTIALS_PATH .json validation, FPCALC env is_file check, get_checker thread-safe singleton, rate_limiter set_limit bounds validation, credentials.py thread-safe json cache+dotenv) |
| 2026-03-17 | src/controllers/ | Security | 8.5/10 | 9/10 | MAPS Round 40: 3 fixes (handle_command log→DEBUG, _handle_volume defensive clamp, seek position int+clamp) |
| 2026-03-17 | src/gui/tabs/ | Security | 8.5/10 | 9/10 | MAPS Round 41: 2 fixes (cloud_sync_tab log injection email sanitized, content_filter_tab path confinement on move/copy destinations) |
| 2026-03-17 | src/gui/widgets/ | Security | — | 9.5/10 | MAPS Round 42: 0 fixes needed, all ops delegated to protected managers |
| 2026-03-17 | src/gui/dialogs/ | Security | — | 9.5/10 | MAPS Round 43: 0 fixes needed, credentials via OS keyring, input validated |
| 2026-03-17 | src/workers/ | Security | — | 9.5/10 | MAPS Round 44: 0 fixes needed, path validation via validate_path(), URL validated upstream |
| 2026-03-17 | src/main.py | Security | — | 9/10 | MAPS Round 45: 0 fixes needed, credentials via secure fallback, safe exception handling |
| 2026-03-17 | src/gui/base/ | Security | — | 9.5/10 | MAPS Round 46: 0 fixes needed, pure template code with no I/O |
| 2026-03-17 | src/gui/visualizers/ | Security | — | 9.5/10 | MAPS Round 47: 0 fixes needed, static shaders, clamped inputs, GUI-thread only |
| 2026-03-17 | src/gui/themes/ | Security | — | 10/10 | MAPS Round 48: 0 fixes needed, pure constants module |

| 2026-03-17 | src/core/ | Performance | 7/10 | 8.5/10 | MAPS Round 49: 3 fixes (batch embeddings query in find_similar, exclude_ids list→set O(1), waveform cache bounded to 50 entries) |
| 2026-03-17 | src/gui/tabs/ | Performance | 7/10 | 8.5/10 | MAPS Round 50: 1 fix (library_tab setRowCount+blockSignals for batch table population) |
| 2026-03-17 | src/gui/widgets/ | Performance | 8.5/10 | 9/10 | MAPS Round 51: 1 fix (clear_playing_highlight O(n)→O(1) via _highlighted_row tracking) |
| 2026-03-17 | src/services/ | Performance | 6/10 | 8/10 | MAPS Round 52: architectural findings documented (stats sequential queries, download count scans, lyrics keyword matching). Most require refactoring beyond scope |
| 2026-03-17 | src/api/ | Performance | 7/10 | 8.5/10 | MAPS Round 53: 3 fixes (APICache FIFO→true LRU via pop+reinsert, chords_client execute_query→fetch_one, chords cache bounded to 200 entries) |
| 2026-03-17 | src/database/ | Performance | 7.5/10 | 8/10 | MAPS Round 54: architectural finding documented (batch_clean_titles N+1 UPDATE pattern) |
| 2026-03-17 | src/plugins/ | Performance | 6.5/10 | 8.5/10 | MAPS Round 55: 1 fix (scrobbler queue bounded to 100 entries with overflow drop) |
| 2026-03-17 | src/controllers/ | Performance | — | 8/10 | MAPS Round 56: architectural findings documented (spectrum worker .wait(), modal dialogs). Acceptable for current use |
| 2026-03-17 | src/utils/ | Performance | — | 9/10 | MAPS Round 57: 0 fixes needed, minor regex recompilation acceptable |
| 2026-03-17 | src/gui/dialogs/ | Performance | — | 8/10 | MAPS Round 58: architectural finding documented (API validation on UI thread). Acceptable with timeout |
| 2026-03-17 | src/workers/ | Performance | — | 9/10 | MAPS Round 59: 0 fixes needed, proper background threading |
| 2026-03-17 | src/gui/visualizers/ | Performance | 8/10 | 8.5/10 | MAPS Round 60: 1 fix (cached glGetUniformLocation in initializeGL, 9 lookups saved per frame) |
| 2026-03-17 | src/gui/base/ | Performance | — | 9/10 | MAPS Round 61: 0 fixes needed, clean template code |
| 2026-03-17 | src/main.py | Performance | — | 9/10 | MAPS Round 62: 0 fixes needed, sequential init acceptable for startup |
| 2026-03-17 | src/gui/themes/ | Performance | — | 10/10 | MAPS Round 63: 0 fixes needed, pure constants module |

## Notes
- Rounds 1-3 were cross-module (pre-MAPS methodology)
- Starting from Round 4, audits are per-module with scope-locking (MAPS)
- Scores with ~ are estimates; formal per-module scores start with MAPS
