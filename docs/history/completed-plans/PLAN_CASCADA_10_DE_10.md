# Plan Cascada 10/10 — Corrección Secuencial con TDD

**Fecha:** 2026-03-16
**Score actual:** 7.86/10 (promedio R4)
**Objetivo:** 10/10 real en cada capa
**Método:** Cascada secuencial + TDD. Cada capa se congela antes de pasar a la siguiente.

---

## Principios

1. **Cascada estricta**: CODE → TESTS → SECURITY → IMPORTS → DOCS
2. **TDD**: Escribir test que falle → fix → test pasa → commit
3. **Congelamiento**: No tocar capas anteriores al trabajar en la siguiente
4. **Commits atómicos**: Un fix = un commit
5. **Sin paralelismo**: Un agente a la vez, un fix a la vez
6. **Auditoría por capa**: Al terminar cada capa, auditar SOLO esa capa

---

## CAPA 1: CODE (actual 8.3/10 → objetivo 10/10)

Todos los cambios de código se hacen aquí. Después de esta capa, el código NO se toca.

### CODE-01: Extraer `_sync_volume_ui()` en PlaybackController
- **Archivo:** `src/controllers/playback_controller.py:286-340`
- **Problema:** Volume slider update (blockSignals/setValue/setText) repetido 4x
- **TDD:** Test que valide que `_sync_volume_ui(50)` actualiza slider y label
- **Fix:** Extraer método, reemplazar 4 repeticiones
- **Verificar:** También eliminar duplicado en `remote_controller.py:104-109`

### CODE-02: Extraer `_play_song()` en PlaybackController
- **Archivo:** `src/controllers/playback_controller.py:140-183,233-260`
- **Problema:** `play_song_from_playlist()` y `play_recommended_song()` comparten ~80% lógica
- **TDD:** Test que valide `_play_song(song_data, source)` con file existente y no existente
- **Fix:** Extraer método privado, ambos lo llaman

### CODE-03: Eliminar imports no usados en library_tab.py
- **Archivo:** `src/gui/tabs/library_tab.py:28,31`
- **Problema:** `QThread`, `QUrl`, `Slot`, `QApplication` importados pero no usados
- **Fix:** Eliminar las 4 líneas de import
- **Sin TDD** (cambio trivial, flake8 valida)

### CODE-04: Eliminar import no usado en playback_controller.py
- **Archivo:** `src/controllers/playback_controller.py:11`
- **Problema:** `import sqlite3` no se usa
- **Fix:** Eliminar la línea
- **Sin TDD** (cambio trivial)

### CODE-05: Eliminar `_play_next/_play_prev` duplicación
- **Archivo:** `src/controllers/playback_controller.py:185-231`
- **Problema:** `_play_next_from_playlist()` y `_play_prev_from_playlist()` idénticos salvo +1/-1
- **TDD:** Test que valide `_play_adjacent_in_playlist(direction=1)` y `direction=-1`
- **Fix:** Extraer método con parámetro direction

### CODE-06: Verificar import keyring en main.py
- **Archivo:** `src/main.py:42`
- **Problema:** `import keyring` posiblemente no usado directamente
- **Fix:** Si no se usa, eliminar
- **Sin TDD** (cambio trivial)

### CODE-07: Eliminar TODOs obsoletos en cleanup_workflow.py
- **Archivo:** `src/core/cleanup_workflow.py:418,443`
- **Problema:** TODOs para escritura de ID3 tags no implementados
- **Fix:** Eliminar o implementar
- **Sin TDD** (limpieza)

**Validación de capa:** `pytest tests/ -v` → 0 nuevos fallos. `flake8 src/` → limpio. `mypy src/` → 0 errores.

---

## CAPA 2: TESTS (actual 7.5/10 → objetivo 10/10)

Se corrigen los 5 tests rotos y se añade cobertura crítica. El código de src/ NO cambia aquí
(excepto bugs reales descubiertos por tests — documentarlos).

### TEST-01: Fix test_song_exists_by_file_path_true
- **Archivo:** `tests/test_database_manager.py`
- **Problema:** Path relativo vs Path.resolve() produce mismatch en Windows
- **Fix:** Usar path absoluto real (`tmp_path / "music" / "song.mp3"`) en el test
- **Verificar:** ¿Es bug en producción? Si sí, fix va en CAPA 1 (volver atrás)

### TEST-02: Fix test_add_download_none_metadata_bug
- **Archivo:** `tests/test_download_service.py:190-202`
- **Problema:** Test stale — asserts `result is None` pero producción retorna `"item_003"`
- **Fix:** Actualizar assertion al comportamiento actual O documentar que el bug fue arreglado

### TEST-03: Fix test_detect_by_fingerprint (skipif fpcalc)
- **Archivo:** `tests/test_duplicate_detector.py`
- **Problema:** Requiere binario `fpcalc` no disponible
- **Fix:** `@pytest.mark.skipif(not shutil.which("fpcalc"), reason="fpcalc not found")`

### TEST-04: Fix test_organizer_sanitizes_folder_names (cross-platform)
- **Archivo:** `tests/test_library_organizer.py`
- **Problema:** Hardcodea `/` pero Windows usa `\`
- **Fix:** Usar `os.sep` o `pathlib.PurePosixPath` en assertion

### TEST-05: Fix test_search_by_artist (mock YouTube API)
- **Archivo:** `tests/test_youtube_search.py`
- **Problema:** Llama API real de YouTube, resultado no determinístico
- **Fix:** Mock de `googleapiclient` con respuesta predefinida

### TEST-06: Aumentar cobertura de database/manager.py (50% → 80%+)
- **Tests nuevos para:** `search_songs()` FTS5, `add_song()` path normalization,
  `get_all_songs()` sorting, WAL mode setup, migration execution
- **Archivos afectados:** `tests/test_database_manager.py`

### TEST-07: Test para JWT token refresh/expiration
- **Archivo:** `tests/test_remote_server.py` (nuevo o existente)
- **Tests:** Token válido, token expirado, refresh endpoint, token inválido

### TEST-08: Aumentar cobertura módulos críticos
- `download_queue.py` 62% → 80%+ (concurrent limits, cancellation)
- `cloud_sync_service.py` 46% → 70%+ (conflict resolution, error recovery)
- `playback_controller.py` 33% → 70%+ (play, volume, navigation)

### TEST-09: Test plugin whitelist deny
- **Archivo:** `tests/test_plugins.py`
- **Test:** Intentar cargar plugin NO whitelisted sin `_skip_whitelist=True` → debe fallar

### TEST-10: Test FTS5 injection at DB layer
- **Archivo:** `tests/test_database_manager.py`
- **Test:** `search_songs('"; DROP TABLE songs; --')` → no error, 0 resultados

### TEST-11: Marcar tests de red con @pytest.mark.network
- **Archivos:** `test_youtube_search.py`, `test_spotify_search.py`
- **Fix:** Decorator `@pytest.mark.network` + `pytest.ini` marker registration

**Validación de capa:** `pytest tests/ -v` → 0 FAILED. Coverage ≥ 60% overall.

---

## CAPA 3: SECURITY (actual 8.5/10 → objetivo 10/10)

Fixes de seguridad puntuales. Tests ya existen de CAPA 2.

### SEC-01: Download worker reject arbitrary paths
- **Archivo:** `src/workers/download_worker.py:87-91`
- **Problema:** Fallback permite dirs arbitrarios con solo warning
- **TDD:** Test ya debe existir de TEST-08 (download_queue coverage)
- **Fix:** Cambiar fallback a `raise ValueError("Path outside allowed directories")`

### SEC-02: Documentar HTTP-only como limitación conocida
- **Archivo:** `src/services/remote_server.py` (docstring)
- **Fix:** Añadir nota en docstring del módulo sobre HTTP-only y riesgos en LAN compartida
- **Sin TDD** (documentación de código)

### SEC-03: Plugin whitelist file integrity
- **Archivo:** `src/plugins/plugin_manager.py:137-147`
- **Problema:** Whitelist file puede ser sobreescrito por otro proceso
- **TDD:** Test ya existe de TEST-09
- **Fix:** Validar contenido del whitelist contra `_bundled_plugins` al cargar

### SEC-04: Escapar wildcards en LIKE queries
- **Archivo:** `src/database/manager.py:284`, `src/services/library_service.py:349`
- **Problema:** `%` y `_` no escapados en LIKE patterns
- **TDD:** Test en test_database_manager que busque literal `%` y `_`
- **Fix:** `query.replace('%', '\\%').replace('_', '\\_')` + `ESCAPE '\\'`

**Validación de capa:** `pytest tests/ -v` → 0 FAILED. `bandit -r src/ -ll` → limpio.

---

## CAPA 4: IMPORTS/DEPS (actual 7.5/10 → objetivo 10/10)

Limpieza de dependencias y CI. Código ya congelado.

### IMP-01: Reducir flake8 ignore list en CI
- **Archivo:** `.github/workflows/ci.yml:102`
- **Problema:** Ignora F401, F403, F405, F811, F841 (detectores útiles deshabilitados)
- **Fix:** Quitar F-codes del ignore. Agregar `# noqa: F403` inline donde sea intencional
- **Pre-requisito:** CODE-03 y CODE-04 ya eliminaron imports no usados
- **Verificar:** `flake8 src/ --max-line-length=120` con nueva config → 0 errores
- **Sincronizar:** `.pre-commit-config.yaml` debe tener mismos ignores

### IMP-02: Añadir better-profanity a requirements.txt
- **Archivo:** `requirements.txt`
- **Fix:** Añadir `better-profanity>=0.7.0` en sección Phase 5 o crear sección content-filter

### IMP-03: Documentar que requirements.txt = install "all"
- **Archivo:** `requirements.txt` (header)
- **Fix:** Añadir comentario: `# Installs ALL features (equivalent to pip install nexus-music-manager[all])`

### IMP-04: Resolver star import OpenGL
- **Archivo:** `src/gui/visualizers/organic_visualizer.py:58`
- **Fix:** Añadir `# noqa: F403` (es idiomático en OpenGL Python)

### IMP-05: Añadir Python 3.10 a CI matrix
- **Archivo:** `.github/workflows/ci.yml:18`
- **Fix:** `python-version: ['3.10', '3.11', '3.12', '3.13']`

**Validación de capa:** `flake8 src/` → 0 errores. `pip install -r requirements.txt` → OK.

---

## CAPA 5: DOCS (actual 7.5/10 → objetivo 10/10)

Última capa. Documenta el estado FINAL del código ya congelado.

### DOC-01: Reescribir AudioPlayer en API_REFERENCE.md
- **Archivo:** `docs/API_REFERENCE.md:106-135`
- **Fix:** Documentar API real: `load(file_path)`, `play()`, `seek(float)`,
  `set_volume(float 0.0-1.0)`, `get_position() -> float (seconds)`,
  callbacks `on_track_end`, `remove_track_end_callback`

### DOC-02: Actualizar VisualizerWidget styles
- **Archivo:** `docs/API_REFERENCE.md:358-361`
- **Fix:** Añadir "organic" y "waveform" a lista de estilos

### DOC-03: Añadir ChordsClient a API_REFERENCE.md
- **Archivo:** `docs/API_REFERENCE.md`
- **Fix:** Nueva sección documentando `ChordsClient` API

### DOC-04: Fix coverage threshold en docs
- **Archivos:** `CLAUDE.md:74`, `docs/ARCHITECTURE.md:274`
- **Fix:** Cambiar "80%" a valor real del `pytest.ini`

### DOC-05: Fix conteo de tests en ARCHITECTURE.md
- **Archivo:** `docs/ARCHITECTURE.md:274`
- **Fix:** "325+" → conteo real post-CAPA 2

### DOC-06: Fix numeración duplicada en CLAUDE.md
- **Archivo:** `CLAUDE.md:89`
- **Fix:** Renumerar item 8 (Credentials)

### DOC-07: Actualizar conteo de deps en CLAUDE.md
- **Archivo:** `CLAUDE.md:133`
- **Fix:** "20 deps" → conteo real post-CAPA 4

### DOC-08: Añadir prerequisito libmpv
- **Archivos:** `README.md`, `CLAUDE.md`
- **Fix:** Sección Prerequisites mencionando libmpv-2.dll (Windows) / libmpv.so (Linux)

### DOC-09: Añadir sección Contributing
- **Archivo:** `README.md`
- **Fix:** Breve sección con code style, PR process, testing requirements

### DOC-10: Añadir sección Screenshots
- **Archivo:** `README.md`
- **Fix:** Placeholder con 2-3 screenshots o nota "screenshots coming soon"

### DOC-11: Fix fechas en CHANGELOG.md
- **Archivo:** `CHANGELOG.md:182`
- **Fix:** Cambiar "2024" a "2025" en todas las fechas

### DOC-12: Fix widgets faltantes en ARCHITECTURE.md
- **Archivo:** `docs/ARCHITECTURE.md:67`
- **Fix:** Añadir `skeleton_widget.py` y `chord_diagram_widget.py`

### DOC-13: Actualizar lista BaseWorker en ARCHITECTURE.md
- **Archivo:** `docs/ARCHITECTURE.md:101-102`
- **Fix:** Listar los 13 workers que usan BaseWorker

**Validación de capa:** Lectura manual. Cross-check con código congelado.

---

## Protocolo de Ejecución

```
Para cada CAPA:
  1. Leer este plan (la sección de la capa actual)
  2. Para cada fix en orden:
     a. Si requiere TDD: escribir test → verificar que falla → fix → verificar que pasa
     b. Si no requiere TDD: hacer fix directo
     c. Commit atómico con ID del fix (ej: "fix(code): CODE-01 extract _sync_volume_ui")
  3. Validación de capa completa (pytest + herramientas específicas)
  4. Auditoría de capa (1 agente solo para esa capa)
  5. Si score < 9.5: iterar fixes dentro de la capa
  6. Si score ≥ 9.5: CONGELAR capa, pasar a siguiente

Para evitar autocompactación:
  - Máximo 3-4 fixes por sesión de conversación
  - Commit después de cada fix
  - Si el contexto se acerca al límite, nueva conversación leyendo este plan
  - El plan es la fuente de verdad, no el historial de conversación
```

---

## Tracking de Progreso

| Capa | Fix | Status | Commit | Score |
|------|-----|--------|--------|-------|
| CODE | CODE-01..07 | DONE | b9b7119 | - |
| CODE | Validación | DONE | - | 8.3 → 10 |
| TESTS | TEST-01..11 | DONE | 615afbc | - |
| TESTS | Validación | DONE | - | 7.5 → 10 |
| SECURITY | SEC-01..04 | DONE | 46636e2 | - |
| SECURITY | Validación | DONE | - | 8.5 → 10 |
| IMPORTS | IMP-01..05 | DONE | 5204e4a | - |
| IMPORTS | Validación | DONE | - | 7.5 → 10 |
| DOCS | DOC-01..13 | DONE | 61eda1a | - |
| DOCS | Validación | DONE | - | 7.5 → 10 |
