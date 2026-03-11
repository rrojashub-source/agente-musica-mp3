# NEXUS Music Manager

**Version:** 1.0.0 | **Status:** Refactoring planificado | **Audit Score:** 6.8/10 | **Target:** 8.5/10

---

## Estado Actual (2026-03-10)

Proyecto completado en dic-2025 (score comercial 99/100). Restaurado desde backup Z: el 2026-03-10 tras perdida del working tree. Auditoria integral completada con 4 agentes. Plan de refactoring v2 aprobado.

**Documentos clave:**
- `PROJECT_STATE.json` — estado dinamico completo (fases, decisiones, plan)
- `docs/AUDIT_REPORT_2026-03-10.md` — hallazgos de auditoria (9 criticos, 8 altos)
- `tasks/refactoring_plan_v2.md` — plan detallado 4 fases, 6 semanas

**IMPORTANTE:** NO agregar features nuevas hasta completar Fase 1 (seguridad) y Fase 2 (refactoring).

---

## Resumen

Gestor de biblioteca musical profesional con GUI PyQt6. Descarga YouTube, busqueda Spotify, metadata automatica MusicBrainz, reproductor con 4 visualizadores, IA para similitud (embeddings 128D), filtro de contenido, plugins, control remoto movil, sync cloud, multi-idioma ES/EN.

## Stack Actual → Target

| Componente | Actual | Target (Fase 3) |
|------------|--------|------------------|
| GUI | PyQt6 | **PySide6** (LGPL, soporte Nuitka) |
| Audio | pygame | **python-mpv** (gapless real, todos formatos) |
| Empaquetado | PyInstaller (164MB) | **Nuitka + UPX** (~90MB) |
| DB | SQLite + FTS5 + WAL | Sin cambio |
| Visualizer | OpenGL 3.3 + GLSL | Sin cambio |
| APIs | YouTube, Spotify, MusicBrainz, Genius | Sin cambio |
| Remote | Flask REST API | Flask + **JWT auth** (Fase 1) |

## Estructura

```
src/
├── main.py                 # Entry point — GOD CLASS, split en Fase 2
├── api/                    # YouTube, Spotify, MusicBrainz, Genius
├── core/                   # Player, downloads, embeddings, duplicates, metadata
├── gui/
│   ├── tabs/               # 13 tabs (necesitan BaseTab en Fase 2)
│   ├── widgets/            # 8 widgets custom
│   ├── visualizers/        # Organic SDF visualizer (OpenGL)
│   ├── dialogs/            # API settings, shortcuts
│   └── themes/             # dark.qss, light.qss
├── services/               # Cloud sync, remote server, content filter
├── plugins/                # Plugin system (17 hooks) + 3 plugins
├── database/               # SQLite manager + 5 migraciones SQL
├── workers/                # Download, import workers
├── utils/                  # Sanitizer, rate limiter, subprocess patch
└── translations.py         # ES/EN (200+ claves)
tests/                      # 49 archivos, 416+ tests
docs/                       # Arquitectura, API ref, auditoria
scripts/                    # 16 scripts utilitarios
tasks/                      # Planes de fase + plan refactoring v2
```

## Vulnerabilidades Criticas (Fase 1)

1. **Flask sin auth** → `src/services/remote_server.py` — agregar JWT + CORS restrictivo
2. **Path traversal** → `src/workers/download_worker.py:49` — validar output_path
3. **Plugins sin sandbox** → `src/plugins/plugin_manager.py:157` — whitelist
4. **Thread-safety** → `audio_player.py`, `download_queue.py` — agregar RLock
5. **348 except Exception** → especificar excepciones en todo el proyecto
6. **Metodos truncados** → main.py, audio_player, cloud_sync — completar

## Ejecutar

```bash
# Produccion (Windows)
dist/NEXUS_Music_Manager.exe

# Desarrollo
pip install -r requirements.txt
python src/main.py

# Tests
pytest tests/ -v
```

## Reglas

- **Fase 1 (seguridad) es BLOQUEANTE** — no avanzar sin completarla
- Commits atomicos: un cambio logico por commit
- Tests deben pasar despues de cada fase
- El exe en dist/ es la version funcional pre-refactoring
- DB principal: `music_library.db` (68 canciones, FTS5)
- API keys en OS keyring (no en codigo)
- Paths en DB pueden necesitar update si cambia ubicacion de MP3s
- El proyecto usa **numpy FFT** (no librosa) para audio analysis

## Dependencias

Ver `requirements.txt` (20 deps) y `requirements-dev.txt` (14 deps).
**Inconsistencia:** `setup.py` omite: pypresence, flask, flask-cors, qrcode, PyOpenGL, pyacoustid.

## Git

- Remote: `origin` → `github.com/rrojashub-source/agente-musica-mp3.git`
- Branch: `main` (213 commits)
- Branch sin limpiar: `practical-solomon` (considerar eliminar)
