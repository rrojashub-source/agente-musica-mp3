# PRD: NEXUS Music Manager

**Version:** 2.1.0 | **Date:** 2026-03-17 | **Author:** Ricardo Rojas

---

## 1. PROBLEMA

**Quien:** Usuarios de Windows que gestionan bibliotecas de musica MP3 (100-10,000 canciones).

**Dolor:** Los reproductores existentes (Winamp, foobar2000, MusicBee) no integran descarga de YouTube, busqueda Spotify, metadata automatica, deteccion de duplicados por audio fingerprint, ni IA para similitud musical en una sola herramienta.

**Solucion actual:** Multiples herramientas separadas (yt-dlp CLI, MusicBrainz Picard, foobar2000, scripts manuales). Flujo fragmentado, metadata incompleta, duplicados no detectados.

---

## 2. SOLUCION

Gestor de biblioteca musical profesional con GUI PySide6 que unifica descarga, organizacion, metadata, reproduccion y analisis en una sola aplicacion de escritorio.

**Viaje del usuario:**
1. **Importar** — Escanea carpeta de MP3s, detecta duplicados, extrae metadata existente
2. **Enriquecer** — Busca metadata automatica (MusicBrainz, Genius lyrics, Spotify art), descarga nuevas canciones (YouTube)
3. **Organizar** — Renombra archivos, organiza por carpetas, filtra contenido, gestiona playlists
4. **Disfrutar** — Reproduce con gapless playback, visualizador OpenGL, control remoto movil, recomendaciones IA

---

## 3. ALCANCE MVP

### Features implementadas (v2.1.0)
- [x] Biblioteca musical con busqueda FTS5 (14 tabs)
- [x] Descarga YouTube + busqueda Spotify
- [x] Metadata automatica MusicBrainz + Genius lyrics + album art
- [x] Reproductor python-mpv con gapless playback
- [x] 4 visualizadores OpenGL (Organic SDF shaders)
- [x] Deteccion de duplicados (hash, fingerprint, metadata)
- [x] IA: embeddings 128D para similitud musical + recomendaciones
- [x] Filtro de contenido (clasificacion automatica)
- [x] Sistema de plugins (17 hooks, 3 plugins incluidos)
- [x] Control remoto movil (Flask REST + JWT + QR)
- [x] Cloud sync (Google Drive)
- [x] Multi-idioma ES/EN (274 claves)
- [x] Acordes (deteccion + diagramas)
- [x] Estadisticas de reproduccion
- [x] Keyboard shortcuts personalizables
- [x] Temas dark/light

### Non-goals (NO implementar sin aprobacion explicita)
- Streaming desde servicios (Spotify, Apple Music, Tidal)
- Soporte para formatos de video
- Aplicacion movil nativa (el control remoto web es suficiente)
- Base de datos centralizada (servidor) — se usa SQLite local
- Soporte Linux/macOS (solo Windows por ahora)
- Ecualizador de audio (complejidad vs beneficio)
- Edicion de tags ID3 manual masiva (usar MusicBrainz Picard para eso)
- Rip de CDs

---

## 4. RESTRICCIONES TECNICAS

| Componente | Decision | Razon |
|------------|----------|-------|
| GUI | PySide6 | Migrado desde PyQt6 (licencia LGPL, mejor soporte Qt6) |
| Audio | python-mpv (libmpv) | Gapless real, todos los formatos, bajo overhead |
| DB | SQLite + FTS5 + WAL | Sin servidor, portable, busqueda full-text integrada |
| Empaquetado | PyInstaller 6.19 + UPX | Nuitka bloqueado por yt_dlp #2879 |
| FFT | numpy | No librosa (demasiado pesado para analisis basico) |
| Auth | JWT Bearer 24h | Control remoto movil, CORS restringido a IP servidor |
| Credentials | OS keyring > env > .env > JSON | 4-tier fallback via utils/credentials.py |
| CI/CD | GitHub Actions | test, mypy, bandit, flake8, build |

---

## 5. CRITERIOS DE EXITO

### Lanzamiento (CUMPLIDO dic-2025)
- Score comercial: 99/100
- Ejecutable standalone: 151MB (PyInstaller + UPX)
- 68 canciones en DB de prueba

### Calidad (CUMPLIDO mar-2026)
- mypy: 0 errores (111 archivos, strict mode)
- pytest: 980+ tests pass
- flake8: limpio (max-line-length=120)
- bandit: limpio (-ll)
- Auditoria MAPS: 15/15 modulos aprobados en 4 fases

---

## 6. FASES DE IMPLEMENTACION

| Fase | Nombre | Status | Periodo |
|------|--------|--------|---------|
| 1 | Core Library + DB | COMPLETADA | Sep 2025 |
| 2 | Search + Download | COMPLETADA | Oct 2025 |
| 3 | Stack Migration (PyQt6 -> PySide6) | COMPLETADA | Oct 2025 |
| 4 | API Integration (Spotify, MusicBrainz, Genius) | COMPLETADA | Nov 2025 |
| 5 | Management Tools (duplicates, organize, rename) | COMPLETADA | Nov 2025 |
| 6 | Player Polish (gapless, visualizer) | COMPLETADA | Nov 2025 |
| 7 | Advanced Features (plugins, remote, cloud, i18n) | COMPLETADA | Nov-Dic 2025 |
| 8 | AI Features (embeddings, content filter, chords) | COMPLETADA | Dic 2025 |
| 9 | Packaging + Build | COMPLETADA | Dic 2025 |
| 10 | Refactoring + Audit | COMPLETADA | Mar 2026 |
