# 🚀 Quick Start - NEXUS Music Manager

## ✅ Cómo Ejecutar la Aplicación Completa (Phases 1-7)

### **Opción 1: Doble clic en Windows** ⭐ RECOMENDADO

1. **Navega al directorio del proyecto:**
   ```
   D:\01_PROYECTOS_ACTIVOS\AGENTE_MUSICA_MP3\
   ```

2. **Doble clic en:**
   ```
   run_music_player.bat
   ```

3. **¡Listo!** La aplicación se abrirá con todos los features.

---

### **Opción 2: Desde terminal**

```bash
cd /mnt/d/01_PROYECTOS_ACTIVOS/AGENTE_MUSICA_MP3

# Ejecutar directamente
python src/main.py

# O usar el .bat
./run_music_player.bat
```

---

## 📋 Verificar Dependencias

Si la app falla al iniciar, instala dependencias:

```bash
pip install PyQt6 pygame mutagen
```

**Dependencias completas (si necesitas todas):**
```bash
pip install PyQt6 pygame mutagen requests spotipy yt-dlp
```

---

## 🎵 Features Disponibles en la Aplicación

Cuando ejecutes `run_music_player.bat`, verás:

### **Top Panel:**
- **Now Playing Widget** - Controles de reproducción (play/pause/stop/volume)
- **Audio Visualizer** - Waveform en tiempo real (60 FPS)

### **Tabs (Pestañas):**
1. **🎵 Library** - Tu biblioteca completa (10,000+ canciones)
   - Doble clic para reproducir
   - Búsqueda FTS5 (rápida)
   - Keyboard shortcuts (Space, Up/Down)

2. **🔍 Search & Download** - Buscar en YouTube + Spotify
   - Dual-source search
   - Download queue
   - Auto-metadata (MusicBrainz)

3. **📥 Queue** - Download queue (placeholder por ahora)

4. **🔍 Duplicates** - Detector de duplicados
   - 3 métodos: metadata, fingerprint, filesize
   - Preview antes de borrar

5. **📁 Organize** - Auto-organizar carpetas
   - Templates personalizables
   - Preview mode
   - Rollback support

6. **✏️ Rename** - Renombrar archivos en lote
   - Find/replace
   - Case conversion
   - Preview antes de aplicar

### **Right Panel:**
- **Playlist Manager** - Gestión de playlists
  - Create/delete/rename
  - Import/export .m3u8
  - Drag & drop (próximamente)

---

## 🔧 Troubleshooting

### **Error: "PyQt6 not installed"**
```bash
pip install PyQt6
```

### **Error: "Database not initialized"**
La base de datos se crea automáticamente en la primera ejecución.
Si hay problemas, verifica que existan las migraciones en:
```
src/database/migrations/
```

### **Error: "pygame not found"**
```bash
pip install pygame
```

### **Error: "Module import errors"**
Asegúrate de estar en el directorio del proyecto:
```bash
cd /mnt/d/01_PROYECTOS_ACTIVOS/AGENTE_MUSICA_MP3
python src/main.py
```

---

## 🎯 Cosas a Probar

1. **Reproducción de audio:**
   - Tab "Library" → Doble clic en una canción
   - Debería empezar a reproducir
   - Prueba play/pause/stop/volume

2. **Visualizer:**
   - Mientras se reproduce, el visualizer debería mostrar la waveform
   - La línea roja es la posición actual

3. **Playlists:**
   - Panel derecho → "Create Playlist"
   - Agrega canciones desde Library
   - Export a .m3u8 (compatible con VLC)

4. **Search & Download:**
   - Tab "Search" → Busca un artista
   - Verás resultados de YouTube + Spotify
   - Selecciona y descarga

5. **Management Tools:**
   - Tab "Duplicates" → Buscar duplicados
   - Tab "Organize" → Auto-organizar por carpetas
   - Tab "Rename" → Renombrar archivos

---

## 📊 Estado del Proyecto

**Version:** 2.0 Production
**Phases Complete:** 1-7 (100%)
**Test Coverage:** 286/306 tests (93.5%)
**Features Operational:** 20+ features

**Ready for:**
- ✅ Manual testing
- ✅ Real-world usage
- ✅ Phase 8 planning (equalizer, lyrics, etc.)

---

## 💬 Reportar Issues

Si encuentras bugs o problemas:

1. **Anota el error exacto** (captura de pantalla si es posible)
2. **Qué estabas haciendo** cuando ocurrió
3. **Logs:** Check terminal output para mensajes de error

**La app tiene logging habilitado**, así que verás mensajes informativos en la terminal.

---

**¡Disfruta probando tu reproductor de música completo! 🎵**
