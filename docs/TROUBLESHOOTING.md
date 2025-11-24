# Troubleshooting Guide / Guía de Solución de Problemas

Este documento cubre los problemas más comunes y sus soluciones.
This document covers the most common issues and their solutions.

---

## Tabla de Contenidos / Table of Contents

1. [Problemas de Descarga / Download Issues](#1-problemas-de-descarga--download-issues)
2. [Problemas de API / API Issues](#2-problemas-de-api--api-issues)
3. [Problemas de Base de Datos / Database Issues](#3-problemas-de-base-de-datos--database-issues)
4. [Problemas de Reproducción / Playback Issues](#4-problemas-de-reproducción--playback-issues)
5. [Problemas de Interfaz / UI Issues](#5-problemas-de-interfaz--ui-issues)
6. [Problemas de Instalación / Installation Issues](#6-problemas-de-instalación--installation-issues)

---

## 1. Problemas de Descarga / Download Issues

### 1.1 "yt-dlp download fails" / "Falla la descarga de yt-dlp"

**Síntomas:**
- Error: "ERROR: Unable to download webpage"
- Error: "ERROR: Video unavailable"
- Descarga se queda en 0%

**Soluciones:**

```bash
# 1. Actualizar yt-dlp (más común)
pip install -U yt-dlp

# 2. Verificar conexión a internet
ping youtube.com

# 3. Limpiar cache de yt-dlp
yt-dlp --rm-cache-dir

# 4. Probar descarga manual
yt-dlp "https://www.youtube.com/watch?v=VIDEO_ID" -v
```

**Si persiste:**
- Algunos videos están geo-bloqueados
- El video puede haber sido eliminado
- YouTube puede estar limitando tu IP (esperar 1 hora)

---

### 1.2 "Download stuck at 99%" / "Descarga atascada en 99%"

**Causa:** FFmpeg está convirtiendo el archivo.

**Solución:**
- Esperar 1-2 minutos (conversión normal)
- Verificar que FFmpeg está instalado:
```bash
ffmpeg -version
```

**Si FFmpeg no está instalado:**
```bash
# Windows (con chocolatey)
choco install ffmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

---

### 1.3 "No audio in downloaded file" / "Sin audio en archivo descargado"

**Causa:** Formato de audio incorrecto.

**Solución:**
1. Ir a Settings → Download
2. Cambiar formato a "mp3" o "m4a"
3. Verificar que FFmpeg está instalado

---

## 2. Problemas de API / API Issues

### 2.1 "YouTube API quota exceeded" / "Cuota de API YouTube excedida"

**Síntomas:**
- Error 403: "quotaExceeded"
- Búsquedas dejan de funcionar

**Soluciones:**

1. **Esperar 24 horas** - La cuota se resetea a medianoche PT
2. **Usar Spotify como alternativa** - Configurar API de Spotify en Settings
3. **Crear nueva API key:**
   - Ir a [Google Cloud Console](https://console.cloud.google.com/)
   - Crear nuevo proyecto
   - Habilitar YouTube Data API v3
   - Crear nueva API key

---

### 2.2 "Spotify API 401 Unauthorized" / "Spotify API 401 No autorizado"

**Causa:** Credenciales inválidas o expiradas.

**Solución:**
1. Ir a Settings → API → Spotify
2. Verificar Client ID y Client Secret
3. Si no tienes credenciales:
   - Ir a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Crear nueva aplicación
   - Copiar Client ID y Client Secret

---

### 2.3 "MusicBrainz rate limit" / "Límite de tasa de MusicBrainz"

**Síntomas:**
- Error 503: "Rate limit exceeded"
- Metadata no se obtiene

**Solución:**
- MusicBrainz permite 1 request/segundo
- La app ya tiene rate limiting implementado
- Si persiste, esperar 5 minutos

---

### 2.4 "API key not saved" / "API key no se guarda"

**Causa:** Problema con keyring del sistema.

**Solución Windows:**
```bash
# Verificar que Credential Manager está funcionando
cmdkey /list
```

**Solución Linux:**
```bash
# Instalar keyring backend
pip install keyrings.alt
# O usar secretservice
sudo apt install gnome-keyring
```

---

## 3. Problemas de Base de Datos / Database Issues

### 3.1 "Database locked" / "Base de datos bloqueada"

**Síntomas:**
- Error: "database is locked"
- Operaciones fallan intermitentemente

**Soluciones:**

1. **Cerrar otras instancias** de la aplicación
2. **Verificar procesos:**
```bash
# Windows
tasklist | findstr python

# Linux/macOS
ps aux | grep python
```

3. **Reiniciar la aplicación**

4. **Si persiste, reparar DB:**
```bash
sqlite3 music_library.db "PRAGMA integrity_check;"
```

---

### 3.2 "Songs not appearing in library" / "Canciones no aparecen en biblioteca"

**Causas posibles:**
1. Filtro activo en búsqueda
2. Archivos en ubicación incorrecta
3. Base de datos desincronizada

**Soluciones:**

1. **Limpiar filtro de búsqueda** - Borrar texto en barra de búsqueda
2. **Refrescar biblioteca** - Clic en botón "Refresh"
3. **Re-escanear carpeta:**
   - Settings → Library → Scan Folder
   - Seleccionar carpeta de música

---

### 3.3 "Duplicate songs after re-import" / "Canciones duplicadas después de re-importar"

**Solución:**
1. Ir a Tools → Find Duplicates
2. Seleccionar método de detección (Hash recomendado)
3. Revisar y eliminar duplicados

---

## 4. Problemas de Reproducción / Playback Issues

### 4.1 "No sound" / "Sin sonido"

**Soluciones:**

1. **Verificar volumen** del sistema y de la app
2. **Verificar dispositivo de audio:**
   - Windows: Click derecho en speaker → Open Sound Settings
   - Verificar que el dispositivo correcto está seleccionado

3. **Verificar archivo:**
```bash
# Probar con otro reproductor
ffplay "ruta/al/archivo.mp3"
```

4. **Reinstalar PyQt6 multimedia:**
```bash
pip uninstall PyQt6 PyQt6-Qt6
pip install PyQt6
```

---

### 4.2 "Audio stuttering / crackling" / "Audio entrecortado"

**Causas:**
- CPU sobrecargado
- Buffer de audio muy pequeño
- Conflicto con otros programas

**Soluciones:**

1. **Cerrar programas innecesarios**
2. **Deshabilitar visualizador** temporalmente
3. **Verificar uso de CPU** (Task Manager)

---

### 4.3 "Visualizer not moving" / "Visualizador no se mueve"

**Soluciones:**

1. **Verificar que hay audio reproduciéndose**
2. **Cambiar estilo de visualizador** (menú desplegable)
3. **Reiniciar reproducción** (pausar y reproducir)

---

## 5. Problemas de Interfaz / UI Issues

### 5.1 "UI elements too small/large" / "Elementos UI muy pequeños/grandes"

**Solución Windows:**
1. Click derecho en escritorio → Display settings
2. Ajustar "Scale and layout"
3. Reiniciar la aplicación

**Solución con variable de entorno:**
```bash
# Escalar 150%
set QT_SCALE_FACTOR=1.5
python main.py
```

---

### 5.2 "Dark theme not applying" / "Tema oscuro no se aplica"

**Solución:**
1. Settings → Appearance → Theme
2. Seleccionar "Dark"
3. Reiniciar la aplicación

---

### 5.3 "Drag and drop not working" / "Arrastrar y soltar no funciona"

**Causas:**
- Permisos de administrador
- Tipo de archivo no soportado

**Soluciones:**

1. **Verificar tipo de archivo** - Solo MP3, M4A, FLAC, WAV
2. **No ejecutar como administrador** en Windows
3. **Arrastrar directamente a la tabla** de biblioteca

---

## 6. Problemas de Instalación / Installation Issues

### 6.1 "ModuleNotFoundError: No module named 'PyQt6'"

**Solución:**
```bash
pip install PyQt6 PyQt6-Qt6
```

**Si falla en Linux:**
```bash
sudo apt install python3-pyqt6
# O
pip install --user PyQt6
```

---

### 6.2 "DLL load failed" (Windows)

**Causa:** Faltan Visual C++ Redistributables.

**Solución:**
1. Descargar [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Instalar y reiniciar

---

### 6.3 "xcb plugin not found" (Linux)

**Solución:**
```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0
sudo apt install libxkbcommon-x11-0
```

---

## Logs y Diagnóstico / Logs and Diagnostics

### Ubicación de logs / Log location:

```
Windows: %APPDATA%\NEXUS_Music\logs\
Linux:   ~/.local/share/NEXUS_Music/logs/
macOS:   ~/Library/Application Support/NEXUS_Music/logs/
```

### Habilitar modo debug / Enable debug mode:

```bash
# Ejecutar con logging verbose
python main.py --debug

# O establecer variable de entorno
set NEXUS_DEBUG=1
python main.py
```

### Reportar un bug / Report a bug:

1. Recolectar información:
   - Versión de la app
   - Sistema operativo
   - Pasos para reproducir
   - Mensaje de error completo
   - Archivo de log relevante

2. Crear issue en GitHub con esta información

---

## Contacto / Contact

- **GitHub Issues:** [Reportar problema](https://github.com/user/agente-musica-mp3/issues)
- **Documentación:** [docs/](./docs/)

---

**Última actualización / Last updated:** 24 Noviembre 2025
**Mantenido por / Maintained by:** Ricardo + NEXUS@CLI
