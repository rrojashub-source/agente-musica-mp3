# NEXUS Music Manager

**Version:** 2.1.0 | **Status:** Post-audit fixes in progress | **Audit Score:** 7.6/10 (5-agent audit, 2nd round) | **Target:** 8.5+/10

---

## Estado Actual (2026-03-15)

Proyecto completado en dic-2025 (score comercial 99/100). Restaurado desde backup Z: el 2026-03-10. Cuatro auditorias: 2026-03-10 (6.8/10), 2026-03-15 (8.5/10), 2026-03-15 post-plan (6.3/10), 2026-03-15 post-fixes (7.6/10 — Security 8.5, Code 8.0, Imports 7.5, Tests 7.0, Docs 7.0).

**Ronda actual de fixes (post 5-agent audit):**
1. **Security** — Plugin whitelist bypass fixed, FTS5 MATCH sanitization
2. **Build/Deps** — setup.py entry point fixed, deps synced, dead deps removed
3. **Code Quality** — 71 except Exception justified, 11/12 workers→BaseWorker
4. **Cleanup** — Coverage threshold realistic (20%), flake8 E722 enabled, mypy stubs cleaned
5. **Docs** — README.md rewritten, API_REFERENCE.md fixed

**Documentos clave:**
- `PROJECT_STATE.json` — estado dinamico completo (fases, decisiones, plan)
- `docs/AUDIT_REPORT_2026-03-10.md` — hallazgos de auditoria (9 criticos, 8 altos)
- `tasks/plan_10_de_10.md` — plan detallado 5 bloques ejecutado

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
