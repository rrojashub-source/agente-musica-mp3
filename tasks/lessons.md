# Lessons Learned — Anti-patterns encontrados en auditoria

**Source:** 63 rounds de auditoria MAPS (Mar 2026)
**Objetivo:** Evitar estos patrones en codigo futuro. Revisar al inicio de cada sesion.

---

## Thread Safety

1. **Singleton sin lock** — ThemeManager, FpcalcChecker, ContentClassifier usaban patron singleton sin proteccion. Fix: double-checked locking con threading.Lock.
2. **Sleep dentro de RLock** — audio_player.py hacia time.sleep() dentro de un RLock, bloqueando otros threads. Fix: reestructurar para sleep fuera del lock.
3. **Globals sin proteccion** — credentials.py tenia _json_cache y _dotenv_loaded como globals mutables sin lock. Fix: _creds_lock con double-checked locking.
4. **Lecturas fuera de lock** — DownloadQueue._running se leia sin adquirir _lock. Fix: todas las lecturas bajo lock.

## Encapsulacion

5. **Atributos publicos para credenciales** — API keys en spotify_search.client_id, youtube_search.api_key, genius_client.access_token. Fix: renombrar a _private con prefijo underscore.
6. **Acceso a metodos privados entre clases** — PlaybackController llamaba 5 metodos privados de LibraryTab/NowPlayingWidget. Fix: API publica (play_next, play_previous, etc).
7. **Acceso directo a db.conn** — audio_embeddings y library_tab accedian a db.conn.cursor() directamente. Fix: usar execute_query/fetch_one.

## DRY (Don't Repeat Yourself)

8. **Logica duplicada en 3+ archivos** — YouTube artifact regex en 3 archivos, PlaybackState enum en 2 archivos, play count increment en 3 lugares. Fix: extraer a modulo unico.
9. **Copy-paste en API search** — Spotify search_tracks/albums/artists eran 95% identicas. Fix: metodo generico _search().
10. **Volume sync duplicada** — _sync_volume_ui() duplicada en multiples tabs. Fix: extraer metodo comun.

## Seguridad

11. **SSRF sin allowlist** — musicbrainz_client.download_album_art() aceptaba cualquier URL. Fix: domain allowlist (coverartarchive.org, archive.org).
12. **Path traversal** — library_organizer.build_path y content_filter_tab no validaban destino. Fix: Path.resolve() + startswith check.
13. **Timing-unsafe comparison** — remote_server comparaba tokens con != (vulnerable a timing attack). Fix: hmac.compare_digest().
14. **Log injection** — genius_client logueaba titulo/artista sin sanitizar (newlines). Fix: strip newlines/CR.
15. **MD5 para cache** — _cache.py y audio_embeddings usaban MD5 (Bandit B324). Fix: SHA256.
16. **SQL column interpolation** — statistics_service interpolaba nombres de columna via f-string. Fix: frozenset allowlist.
17. **Input sin validar en endpoints** — /api/seek, /api/search sin validacion. Fix: int() + clamp + min(limit, 200).

## Performance

18. **N+1 queries** — audio_embeddings.find_similar() hacia query por cada cancion. Fix: batch-load con single SELECT.
19. **Caches sin bound** — waveform_extractor, chords_client, scrobbler sin limite. Fix: bounded cache (50, 200, 100 entries).
20. **O(n) donde O(1) es posible** — playlist_widget.clear_playing_highlight iteraba todas las filas. Fix: _highlighted_row tracking.
21. **LRU falso** — APICache usaba FIFO eviction. Fix: true LRU (pop+reinsert on get()).
22. **glGetUniformLocation por frame** — organic_visualizer llamaba 9x por frame. Fix: cache en initializeGL.

## Testing

23. **Mock contamination** — Phase-2 GUI tests modifican PySide6 mock modules a nivel de modulo, contaminando tests subsecuentes. Fix: snapshot/restore en conftest.py.
24. **Tests usando atributos renombrados** — Despues de renombrar atributos a _private, tests seguian accediendo al nombre viejo. Fix: actualizar tests junto con el rename.

## Compatibilidad de Librerías

25. **mutagen-rs vs mutagen API differences** — mutagen-rs es drop-in EXCEPTO: `mutagen.id3.error` no existe en mutagen_rs (usar `mutagen_rs.id3.ID3Error`). `MutagenError` se llama `MutagenPyError` internamente pero se re-exporta como `MutagenError`. Siempre usar shim `utils/mutagen_compat.py`.
26. **PyPI name collision** — `dippy` en PyPI v0.1.0 es un paquete DIFERENTE al Dippy de ldayton (auto-approve hook). Instalar siempre desde `git+https://github.com/ldayton/Dippy.git`.

## QThread / Workers

27. **NUNCA usar QThread.terminate()** — Mata threads de C extensions (numpy/scipy/librosa) causando corrupción de memoria → segfault en la siguiente operación. Usar `worker.cancel()` + `requestInterruption()` + `wait(timeout)` + disconnect signals como fallback.
28. **BaseWorker.is_cancelled es property read-only** — No se puede hacer `worker.is_cancelled = True`. Usar `worker.cancel()` que setea `_cancelled = True` internamente.

## PyInstaller Build

29. **PyInstaller --distpath alterno pierde data files** — Con `--distpath dist_new`, los `datas` del spec no se copian a `_internal/`. Solución: copiar manualmente themes, shaders, migrations, chord DB, certifi/cacert.pem, o usar siempre el distpath default.
30. **Siempre limpiar __pycache__ antes de rebuild** — .pyc stale causa que el exe use código viejo. El script `scripts/clean_build.bat` automatiza esto.
