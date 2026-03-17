# NEXUS Music Manager

**Version:** 2.1.0 | **Status:** MAPS audit in progress | **Methodology:** Per-module, phase-locked

---

## Audit Rules — READ BEFORE ANY AUDIT SESSION

**Methodology: MAPS** (Memory, Alcance, Progresion, Scoring)

Before ANY audit or fix session:
1. Read `docs/audit/progress-tracker.md` → understand current state
2. Read `docs/audit/known-issues-resolved.md` → NEVER re-report these
3. Read `docs/audit/approved-modules.md` → SKIP approved modules unless explicitly asked

Rules:
- ONE module per session, ONE phase per session
- Max 8 findings per session — prioritize by severity
- Score each module 1-10 for the current phase
- Phase progression: Code Quality → Tests → Security → Performance
- A module must score >= 8/10 in Phase N before starting Phase N+1
- Linter-catchable issues are NOT audit findings (run linters first)
- After fixing, update tracking files with new scores
- Score NEVER goes down — if it does, methodology is wrong

## Estado Actual (2026-03-16)

Proyecto completado en dic-2025 (score comercial 99/100). Restaurado desde backup Z: el 2026-03-10.
3 rounds de auditorias cross-module completados. Migrando a metodologia MAPS (per-module).

**Documentos clave:**
- `docs/audit/progress-tracker.md` — estado de auditoria por modulo
- `docs/audit/known-issues-resolved.md` — issues ya corregidos (NO re-reportar)
- `docs/audit/approved-modules.md` — modulos aprobados por fase
- `docs/audit/scoring-history.md` — historial de puntajes

---

## Resumen

Gestor de biblioteca musical profesional con GUI PySide6. Descarga YouTube, busqueda Spotify, metadata automatica MusicBrainz, reproductor con 4 visualizadores, IA para similitud (embeddings 128D), filtro de contenido, plugins, control remoto movil, sync cloud, multi-idioma ES/EN.

## Stack Actual

| Componente | Estado | Notas |
|------------|--------|-------|
| GUI | PySide6 | COMPLETADO (migrado desde PyQt6 en Fase 3) |
| Audio | python-mpv | COMPLETADO (gapless real, todos formatos) |
| Empaquetado | PyInstaller 6.19 + UPX (151MB) | Nuitka bloqueado por yt_dlp #2879 |
| DB | SQLite + FTS5 + WAL | Sin cambio |
| Visualizer | OpenGL 3.3 + GLSL | Sin cambio |
| APIs | YouTube, Spotify, MusicBrainz, Genius, Chords | Sin cambio |
| Remote | Flask REST API + JWT Bearer + CORS | Token 24h + refresh endpoint |
| CI/CD | GitHub Actions | test, mypy, bandit, flake8, build |
| Pre-commit | black + isort + flake8 | Instalado |

## Estructura

```
src/
├── main.py                 # Entry point — Facade (340 LOC, refactored Fase 2)
├── api/                    # YouTube, Spotify, MusicBrainz, Genius, Chords
├── core/                   # Player, downloads, embeddings, duplicates, metadata
├── controllers/            # PlaybackController, LibraryController, UIComposer, RemoteController
├── gui/
│   ├── base/               # BaseTab + BaseWorker (templates para tabs y workers)
│   ├── tabs/               # 14 tabs (todos usan BaseTab)
│   ├── widgets/            # 9 widgets custom
│   ├── visualizers/        # Organic SDF visualizer (OpenGL)
│   ├── dialogs/            # API settings, shortcuts
│   └── themes/             # dark.qss, light.qss, style_constants.py
├── services/               # Cloud sync, remote server, content filter
├── plugins/                # Plugin system (17 hooks) + 3 plugins
├── database/               # SQLite manager + 6 migraciones SQL
├── workers/                # Download, import workers
├── utils/                  # Sanitizer, rate limiter, constants, credentials, subprocess patch
└── translations.py         # ES/EN (274 claves)
tests/                      # 52+ archivos, 560+ tests
docs/                       # Arquitectura, API ref, auditoria
scripts/                    # 16 scripts utilitarios
tasks/                      # Planes de fase + plan 10/10
```

## Calidad de Codigo

| Herramienta | Estado | Configuracion |
|-------------|--------|---------------|
| mypy | **0 errores** (111 archivos) | `mypy.ini` strict mode |
| pytest | **980+ tests pass** (1,289 collected) | `pytest.ini` con coverage >= 20% |
| flake8 | Limpio | max-line-length=120 |
| bandit | Limpio | -ll (low+medium) |
| pre-commit | Activo | black, isort, flake8 |

## Seguridad

1. **Flask auth** → JWT Bearer tokens, 24h expiration, refresh endpoint
2. **CORS** → Restringido a IP especifica del servidor (no wildcard)
3. **Path traversal** → `validate_path()` con symlink checks
4. **Plugins** → Whitelist default-deny (incluyendo load_plugin_class)
5. **Thread-safety** → RLock en audio_player y download_queue
6. **SQL injection** → Column allowlist en manager.py y library_service.py
7. **FTS5 injection** → Query sanitization en search_songs()
8. **Credentials** → Centralizadas en `utils/credentials.py` (keyring > env > .env > JSON)

## Patrones de Diseno

- **BaseTab** — Template para todas las 14 tabs (layout, progress, workers)
- **BaseWorker** — Template para 12/13 workers (signals, do_work(), cancellation)
- **Style Constants** — `gui/themes/style_constants.py` reemplaza estilos inline
- **Credential Utility** — `utils/credentials.py` con fallback de 4 niveles
- **Controllers** — PlaybackController, LibraryController, UIComposer, RemoteController
- **Facade** — main.py (340 LOC) delega a controllers

## Ejecutar

```bash
# Produccion (Windows)
dist/NEXUS_Music_Manager.exe

# Desarrollo
pip install -r requirements.txt
python src/main.py

# Tests
pytest tests/ -v

# Type checking
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/ -ll
```

## Reglas

- Commits atomicos: un cambio logico por commit
- Tests deben pasar despues de cada fase
- El exe en dist/ es la version funcional pre-refactoring
- DB principal: `music_library.db` (68 canciones, FTS5)
- API keys en OS keyring (no en codigo), cargadas via `utils/credentials.py`
- Paths en DB pueden necesitar update si cambia ubicacion de MP3s
- El proyecto usa **numpy FFT** (no librosa) para audio analysis
- Type hints requeridos en todos los archivos (mypy strict)

## Dependencias

Ver `requirements.txt` (26 deps) y `requirements-dev.txt` (14 deps).
`setup.py` sincronizado con extras_require: fingerprint, chords, audio-analysis, remote, visualizer, discord, dotenv, all.

## Git

- Remote: `origin` → `github.com/rrojashub-source/agente-musica-mp3.git`
- Branch: `main` (252 commits)
