# NEXUS Music Manager

**Version:** 1.0.0 RELEASE | **Status:** Completado (maintenance mode) | **Score:** 99/100

---

## Resumen

Gestor de biblioteca musical profesional con GUI PyQt6. Descarga desde YouTube, búsqueda dual YouTube+Spotify, metadata automática via MusicBrainz, reproductor con 4 visualizadores, IA para similitud de canciones, filtro de contenido, plugins, control remoto móvil, sync cloud, multi-idioma ES/EN.

## Stack

- **Python 3.11+** — Core
- **PyQt6** — GUI (13 tabs, 8 widgets custom)
- **SQLite + FTS5 + WAL** — Base de datos con búsqueda full-text
- **pygame + numpy FFT** — Reproducción de audio y análisis espectral
- **OpenGL 3.3 + GLSL** — Visualizador orgánico SDF
- **yt-dlp** — Descargas de YouTube
- **Flask** — API REST para control remoto
- **PyInstaller** — Empaquetado .exe Windows

## Estructura

```
src/
├── main.py                 # Entry point (NexusMainWindow)
├── api/                    # YouTube, Spotify, MusicBrainz, Genius clients
├── core/                   # Player, downloads, embeddings, duplicates, metadata
├── gui/
│   ├── tabs/               # 13 tabs funcionales
│   ├── widgets/            # 8 widgets custom (NowPlaying, Visualizer, Playlist...)
│   ├── visualizers/        # Organic SDF visualizer (OpenGL)
│   ├── dialogs/            # API settings, shortcuts
│   └── themes/             # dark.qss, light.qss
├── services/               # Cloud sync, remote server, content filter, stats
├── plugins/                # Plugin system (17 hooks) + 3 plugins
├── database/               # SQLite manager + 5 migraciones SQL
├── workers/                # Background workers (download, import)
├── utils/                  # Sanitizer, rate limiter, subprocess patch
└── translations.py         # ES/EN (200+ claves)
tests/                      # 49 archivos, 416+ tests
docs/                       # Arquitectura, API reference, troubleshooting
scripts/                    # 12 scripts utilitarios
tasks/                      # 11 planes de fase (históricos)
memory/                     # Estado por componente
```

## Ejecutar

```bash
# Producción (Windows)
dist/NEXUS_Music_Manager.exe

# Desarrollo
pip install -r requirements.txt
python src/main.py

# Tests
pytest tests/ -v
```

## Reglas

- **Proyecto completado** — solo mantenimiento y bug fixes
- NO agregar features nuevas sin decisión explícita de Ricardo
- DB principal: `music_library.db` (68 canciones, FTS5)
- API keys en OS keyring (no en código)
- Los paths en la DB pueden necesitar actualización si cambia la ubicación de los MP3s
- **NOTA:** CLAUDE.md anterior decía "librosa" pero el proyecto usa numpy FFT directamente

## Dependencias clave

Ver `requirements.txt` (20 deps producción) y `requirements-dev.txt` (14 deps dev).
**Inconsistencia conocida:** `setup.py` omite algunas deps (pypresence, flask, flask-cors, qrcode, PyOpenGL, pyacoustid).

## Git

- Remote: `origin → github.com/rrojashub-source/agente-musica-mp3.git`
- Branch principal: `main` (212 commits)
- Branch sin limpiar: `practical-solomon`
