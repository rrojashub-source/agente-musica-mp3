# Changelog

All notable changes to NEXUS Music Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Cloud sync básico (planificado)
- Plugin system básico (planificado)

---

## [0.9.3] - 2024-11-24

### Added
- **Rate Limiting:** Sistema centralizado de rate limiting para todas las APIs (YouTube 10/s, Spotify 30/s, MusicBrainz 1/s, Genius 5/s)
- **Gapless Playback:** Transición sin gap entre canciones usando pygame.mixer.queue()
- **Smart Playlists:** Motor de playlists automáticas basadas en reglas
  - Operadores: equals, contains, between, in_last, etc.
  - Modos: ALL (AND) / ANY (OR)
  - Built-in: Recently Added, Most Played, Never Played, By Genre, By Decade, Top Rated
  - Persistencia JSON
- **CHANGELOG.md:** Historial de versiones del proyecto
- **TROUBLESHOOTING.md:** Guía de solución de problemas comunes

### Changed
- Score interno: 92/100 → 95/100

### Refactored
- **Service Layer Architecture:** Nueva capa de servicios para separar lógica de negocio
  - LibraryService: Gestión de biblioteca con signals PyQt6
  - DownloadService: Gestión de descargas con auto-import
  - PlayerService: Control de reproducción con gapless support
  - Domain models: Song, LibraryStats, DownloadItem, NowPlaying (dataclasses)

### Tests
- 15 tests para rate_limiter.py
- 14 tests para gapless_playback.py
- 23 tests para smart_playlist.py
- **29 tests E2E GUI** con pytest-qt:
  - LibraryTab (4 tests)
  - SearchTab (5 tests)
  - QueueWidget (5 tests)
  - Player (5 tests)
  - SmartPlaylist (4 tests)
  - RateLimiter (3 tests)
  - FullIntegration (3 tests)
- **32 tests Service Layer** (LibraryService, DownloadService, PlayerService)

---

## [0.9.2] - 2024-11-24

### Added
- **Skeleton Loading:** Placeholders visuales mientras carga la biblioteca
- **Progress Bars Mejoradas:** Colores por estado (verde=completado, azul=descargando, naranja=pausado, rojo=error)
- **CI/CD Pipeline:** GitHub Actions con tests, security scanning, lint y build
- **Security Scanning:** pip-audit, bandit, safety integrados
- **API Settings Bilingüe:** Diálogo completamente en ES/EN simultáneo

### Changed
- Score interno: 85/100 → 92/100
- Fase 1 MVP marcada como COMPLETADA

---

## [0.9.1] - 2024-11-23

### Added
- **Sistema Multi-idioma:** Soporte completo ES/EN con selector en Settings
- **Drag & Drop:** Importar MP3/M4A/FLAC/WAV arrastrando a la biblioteca
- **Album Grid View:** Vista de álbumes con carátulas en grid responsivo
- **Recomendaciones:** Widget de canciones similares basado en artista/álbum/género
- **Diálogos Bilingües:** About, Shortcuts, API Guide en ES/EN simultáneo

### Changed
- 100+ claves de traducción agregadas
- Preferencia de idioma persistente via QSettings

---

## [0.9.0] - 2024-11-22

### Added
- **Documentación Profesional:** ARCHITECTURE.md, API_REFERENCE.md
- **PyInstaller Config:** nexus_music.spec + BUILD_EXE.bat
- **Security Hardening:** API keys en keyring, input sanitization

### Security
- Validación de paths (prevención path traversal)
- Sanitización de inputs (prevención injection)
- .gitignore comprehensivo (60+ patrones)

---

## [0.8.0] - 2024-11-20

### Added
- **Visualizador Espectro:** Múltiples estilos (Classic Bars, Neon Wave, Circular, Brain AI)
- **Brain AI Style:** Visualización tipo cerebro con partículas reactivas al audio
- **Neon Buttons:** Botones con efecto glow y formas geométricas

### Fixed
- Corrección de bugs en selector de estilos del visualizador
- Fix UnboundLocalError en Brain AI style
- Fix visibilidad de gradientes usando ObjectBoundingMode

### Performance
- Extracción de espectro asíncrona
- Animación suave a 30 FPS

---

## [0.7.0] - 2024-11-18

### Added
- **Now Playing Widget:** Diseño profesional con carátula de álbum
- **Canvas AI Design:** Estilo de botones flat inspirado en Canvas AI

### Fixed
- WSL paths resueltos - base de datos limpia con 312 canciones
- Altura de filas para edición inline visible

---

## [0.6.0] - 2024-11-17

### Added
- **Detector de Duplicados Premium:** UX mejorada con claridad visual
- **Limpieza de Huérfanos:** Previene re-importación de duplicados

### Fixed
- Bug crítico: Auto-import funcionando 100%
- Checkboxes visibles en modo oscuro
- Progress updates incrementales durante fetch de metadata

---

## [0.5.0] - 2024-11-15

### Added
- **AcoustID Integration:** Fingerprinting de audio para identificación
- **Duplicate Detection:** Detección multi-método (hash, fingerprint, metadata)

### Fixed
- Path de fpcalc pasado explícitamente a acoustid
- Skip updates con Unknown Artist/Album

---

## [0.4.0] - 2024-11-12

### Added
- **Search & Download System:** Sistema completo de búsqueda y descarga
- **YouTube + Spotify Search:** Búsqueda dual-source
- **Download Queue:** Cola de descargas con concurrencia
- **Auto-metadata Tagging:** Etiquetado automático via MusicBrainz
- **Auto-import:** Importación automática a biblioteca después de descarga

### Changed
- 127/127 tests pasando
- Phase 4 marcada como COMPLETE

---

## [0.3.0] - 2024-11-01

### Added
- **PyQt6 GUI:** Interfaz gráfica moderna
- **Library Tab:** Visualización de biblioteca con tabla
- **Search Tab:** Búsqueda de canciones
- **Download Tab:** Gestión de descargas
- **Settings Tab:** Configuración de APIs

---

## [0.2.0] - 2024-10-15

### Added
- **SQLite Database:** Base de datos con FTS5 para búsqueda rápida
- **MusicBrainz Integration:** Metadata automática
- **Mutagen Integration:** Edición de tags ID3

---

## [0.1.0] - 2024-09-01

### Added
- **CLI Downloader:** Descargador básico via yt-dlp
- **Excel Import:** Importación de listas desde Excel
- **Basic Metadata:** Extracción básica de metadata

---

## Links

- [Repositorio](https://github.com/user/agente-musica-mp3)
- [Issues](https://github.com/user/agente-musica-mp3/issues)
- [Documentación](./docs/)

---

**Mantenido por:** Ricardo + NEXUS@CLI
