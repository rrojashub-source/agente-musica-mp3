# 🚀 Quick Start - NEXUS Music Manager

## ✅ Cómo Usar la Aplicación (Simple - 1 Paso)

La aplicación te guía automáticamente en el primer uso.

### **PASO ÚNICO: Ejecutar el Reproductor**

**Opción 1: Doble clic en Windows** ⭐ RECOMENDADO

1. Doble clic en:
   ```
   run_music_player.bat
   ```

2. **Si es la primera vez:**
   - Verás mensaje: "Your music library is empty"
   - Click "OK"
   - La app te llevará automáticamente a la pestaña "📥 Import Library"
   - Click "Browse" y selecciona tu carpeta de música (o usa `C:\Users\ricar\Music\`)
   - Click "🚀 Import Library"
   - Espera a que termine (verás progreso en tiempo real)
   - ¡Listo! Ya puedes usar el reproductor

3. **Si ya importaste música antes:**
   - La app abre directamente en la pestaña "🎵 Library"
   - Doble-click en cualquier canción para reproducir

---

**Opción 2: Desde terminal**

```bash
python src/main.py
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

## 🎵 Features Disponibles

### **Tabs Principales:**

1. **🎵 Library** - Tu biblioteca completa
   - Doble clic para reproducir
   - Búsqueda rápida (FTS5)
   - Keyboard shortcuts

2. **🔍 Search** - Buscar en YouTube + Spotify
   - Download y auto-metadata

3. **📥 Import Library** ⭐ NUEVO
   - Importa tu colección de MP3s
   - Progress bar en tiempo real
   - Skips duplicados automáticamente

4. **🔍 Duplicates** - Encuentra duplicados
   - 3 métodos de detección

5. **📁 Organize** - Organiza por carpetas
   - Templates personalizables
   - Preview + Rollback

6. **✏️ Rename** - Renombra archivos
   - Find/replace masivo
   - Preview antes de aplicar

### **Otros:**
- **Now Playing** - Controles de reproducción
- **Visualizer** - Waveform en tiempo real
- **Playlist Manager** - Gestión de playlists

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
