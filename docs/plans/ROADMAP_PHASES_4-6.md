# 🎵 NEXUS Music Manager - Roadmap Phases 4-6

**Proyecto:** AGENTE_MUSICA_MP3_001
**Fecha:** 12 Octubre 2025
**Estado:** Phase 3 completada ✅ - Planning Phases 4-6

---

## ✅ FASES COMPLETADAS

### **Phase 1: PyQt6 Spike (Completada)**
- GUI funcional con 10,000 canciones
- Performance excelente: 0.262s load, 53.1 MB memory
- Sorting, filtering, search básica

### **Phase 2: SQLite Database (Completada)**
- Migración Excel → SQLite
- Schema completo: songs, artists, albums, genres
- FTS5 full-text search
- WAL mode, indexes estratégicos
- 10,016 canciones migradas

### **Phase 3: GUI + Database Integration (Completada ✅)**
- Integración PyQt6 + SQLite
- Performance validada por Ricardo:
  - Load time: ~2s ✅
  - Memory: 42.6 MB ✅
  - Search: milliseconds ✅
  - Sorting: instantaneous ✅
  - Scrolling: smooth ✅
- FTS5 search con géneros
- VIEW songs_complete funcional
- Lazy loading (1,000 songs/página)

---

## 🚀 ROADMAP FUTURO

### **Phase 4: Search & Download System (2 semanas)**

#### **4.1 Search Tab - YouTube + Spotify Integration**

**Descripción:**
Pestaña de búsqueda que permita:
- Buscar por artista, género, álbum, canción
- Resultados de YouTube + Spotify simultáneos
- Seleccionar múltiples canciones
- Agregar a biblioteca con un click

**Implementación Técnica:**

```python
# APIs a usar:
# 1. YouTube Data API v3 (GRATIS)
#    - 10,000 requests/día
#    - Search videos por keyword
#    - Obtener metadata (title, duration, thumbnail)

# 2. Spotify Web API (GRATIS)
#    - 100 requests/segundo
#    - Search tracks, albums, artists
#    - Metadata completa

# Estructura UI:
class SearchTab(QWidget):
    """
    Layout:
    +----------------------------------+
    | [Search Box] [Buscar]           |
    | [x] YouTube  [x] Spotify         |
    +----------------------------------+
    | YouTube Results      | Spotify   |
    | - Song 1 [+]        | - Song 1  |
    | - Song 2 [+]        | - Song 2  |
    +----------------------------------+
    | Selected: 5 songs   [Add to Lib]|
    +----------------------------------+
    """
```

**Librerías:**
- `google-api-python-client` (YouTube API)
- `spotipy` (Spotify API wrapper)
- `yt-dlp` (download)

**Criterio Éxito:**
- Buscar "The Beatles" → resultados en < 2 segundos
- Seleccionar 10 canciones → agregar a biblioteca
- Metadata auto-completada desde API

---

#### **4.2 Download Queue System**

**Descripción:**
Sistema de cola para descargar canciones en background sin bloquear UI.

**Implementación:**

```python
# QThread para downloads asíncronos
class DownloadWorker(QThread):
    progress = pyqtSignal(int)  # 0-100
    finished = pyqtSignal(dict)  # metadata

    def run(self):
        # yt-dlp download con progress callback
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'progress_hooks': [self.hook],
        }

# UI: QueueWidget
class QueueWidget(QWidget):
    """
    Layout:
    +----------------------------------+
    | Queue (5 downloads)             |
    +----------------------------------+
    | ✓ Song 1.mp3                    |
    | ⏳ Song 2.mp3 [====    ] 60%    |
    | ⏸ Song 3.mp3 (paused)           |
    | 🕐 Song 4.mp3 (waiting)         |
    +----------------------------------+
    """
```

**Criterio Éxito:**
- Descargar 50 canciones simultáneas sin frenar UI
- Progress bar en tiempo real
- Cancelar/pausar/resumir downloads

---

#### **4.3 YouTube Playlist Downloader**

**Descripción:**
Descargar playlists completas de YouTube con un comando.

**Implementación:**

```python
# Una línea de código:
ydl.extract_info('https://www.youtube.com/playlist?list=PLxxx', download=True)

# Wrapper con UI:
class PlaylistDownloader:
    def download_playlist(self, url):
        # 1. Extract playlist info
        info = ydl.extract_info(url, download=False)

        # 2. Show preview:
        #    - Playlist name
        #    - Total songs
        #    - Total duration

        # 3. User confirms → download all
        #    - Each song → DownloadWorker
        #    - Auto-complete metadata
        #    - Auto-insert into database
```

**UI:**
```
+------------------------------------------+
| Download YouTube Playlist                |
+------------------------------------------+
| URL: [____________________________] [Go] |
|                                          |
| Found: "90s Rock Hits"                   |
| Songs: 147                               |
| Duration: 9h 23m                         |
|                                          |
| [Cancel] [Download All]                  |
+------------------------------------------+
```

**Criterio Éxito:**
- Pegar URL de playlist → automáticamente descargar todas
- Metadata auto-completada
- Canciones agregadas a biblioteca

---

#### **4.4 Auto-Complete Metadata (MusicBrainz)**

**Descripción:**
Completar metadata faltante usando MusicBrainz API (gratis, sin límite).

**Implementación:**

```python
# MusicBrainz API (sin API key necesaria)
import musicbrainzngs as mb

mb.set_useragent("NexusMusicManager", "1.0")

def autocomplete_metadata(song_title, artist=None):
    # Search recording
    result = mb.search_recordings(
        query=song_title,
        artist=artist,
        limit=5
    )

    # Return:
    # - Album name
    # - Year
    # - Genre tags
    # - Track number
    # - Album art URL
```

**UI Feature:**
```
Right-click en canción con metadata incompleta:
→ "Auto-complete Metadata"
→ Shows 5 matches from MusicBrainz
→ User selects correct one
→ Metadata updated in database
```

**Criterio Éxito:**
- 90% accuracy en auto-complete
- Batch mode: completar 100 canciones a la vez
- Descargar album art automáticamente

---

### **Phase 5: Management Tools (1 semana)**

#### **5.1 Duplicates Detection**

**Descripción:**
Detectar canciones duplicadas usando 3 métodos:

**Método 1: Metadata Comparison**
```python
# Comparar:
# - Title (fuzzy matching)
# - Artist (fuzzy matching)
# - Duration (±3 segundos tolerancia)

from difflib import SequenceMatcher

def are_similar(title1, title2, threshold=0.85):
    ratio = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
    return ratio >= threshold
```

**Método 2: Audio Fingerprinting**
```python
# acoustid + chromaprint
import acoustid

def get_fingerprint(file_path):
    duration, fingerprint = acoustid.fingerprint_file(file_path)
    return fingerprint

# Compare fingerprints → 99% accuracy
```

**Método 3: File Size**
```python
# Misma canción, mismo bitrate → mismo file size
# Rápido pero menos confiable
```

**UI:**
```
+------------------------------------------+
| Duplicate Finder                         |
+------------------------------------------+
| Method: [x] Metadata [x] Fingerprint     |
| Threshold: [====|====] 85%               |
| [Scan Library]                           |
+------------------------------------------+
| Found 23 duplicate groups:               |
|                                          |
| Group 1: "Bohemian Rhapsody"             |
| ├─ 320kbps, 5.9 MB (keep) ✓             |
| └─ 128kbps, 2.1 MB (delete) ☐           |
|                                          |
| [Delete Selected] [Keep All]             |
+------------------------------------------+
```

**Criterio Éxito:**
- Detectar 95%+ duplicados reales
- 0 falsos positivos
- Batch delete con preview

---

#### **5.2 Auto-Organize Folders**

**Descripción:**
Organizar archivos MP3 en estructura de carpetas limpia.

**Estructura Target:**
```
D:\MUSICA_ORGANIZADA\
├── Rock\
│   ├── Queen\
│   │   ├── A Night at the Opera (1975)\
│   │   │   ├── 01 - Bohemian Rhapsody.mp3
│   │   │   ├── 02 - You're My Best Friend.mp3
│   │   │   └── cover.jpg
│   │   └── The Game (1980)\
│   │       └── ...
│   └── The Beatles\
│       └── ...
├── Pop\
│   └── ...
└── Jazz\
    └── ...
```

**Implementación:**
```python
def organize_library(base_path):
    for song in database.get_all_songs():
        # Build path:
        # {base_path}/{genre}/{artist}/{album} ({year})/{track} - {title}.mp3

        target_path = Path(base_path) / \
                      song.genre / \
                      song.artist / \
                      f"{song.album} ({song.year})" / \
                      f"{song.track:02d} - {song.title}.mp3"

        # Move file
        shutil.move(song.file_path, target_path)

        # Update database
        database.update_file_path(song.id, target_path)
```

**UI:**
```
+------------------------------------------+
| Auto-Organize Library                    |
+------------------------------------------+
| Target folder: [Browse]                  |
| D:\MUSICA_ORGANIZADA\                    |
|                                          |
| Structure preview:                       |
| {Genre}\{Artist}\{Album}\{Track}-{Title} |
|                                          |
| [x] Move files                           |
| [ ] Copy files (keep original)           |
| [x] Download album art                   |
|                                          |
| Will organize: 10,016 songs              |
| Estimated time: 3 minutes                |
|                                          |
| [Cancel] [Organize]                      |
+------------------------------------------+
```

**Criterio Éxito:**
- 10,000 canciones organizadas en < 5 minutos
- 0 archivos perdidos
- Database paths actualizados correctamente

---

#### **5.3 Batch Rename Files**

**Descripción:**
Renombrar archivos usando templates.

**Templates:**
```
1. {track} - {title}.mp3
   → 01 - Bohemian Rhapsody.mp3

2. {artist} - {title}.mp3
   → Queen - Bohemian Rhapsody.mp3

3. {artist} - {album} - {track} - {title}.mp3
   → Queen - A Night at the Opera - 01 - Bohemian Rhapsody.mp3

4. Custom: [____________]
```

**Implementación:**
```python
class BatchRenamer:
    def preview_rename(self, template, songs):
        # Show before/after for all files
        for song in songs:
            old_name = song.file_path.name
            new_name = template.format(
                track=f"{song.track:02d}",
                title=self.sanitize(song.title),
                artist=self.sanitize(song.artist),
                album=self.sanitize(song.album)
            )
            yield (old_name, new_name)

    def sanitize(self, text):
        # Remove invalid characters: / \ : * ? " < > |
        return re.sub(r'[/\\:*?"<>|]', '', text)
```

**UI:**
```
+------------------------------------------+
| Batch Rename (150 files selected)       |
+------------------------------------------+
| Template:                                |
| [v] {track} - {title}.mp3               |
|                                          |
| Preview:                                 |
| Before              → After              |
| song1.mp3          → 01 - Bohemian.mp3  |
| track02.mp3        → 02 - You're My.mp3 |
| ...                                      |
|                                          |
| [Cancel] [Rename All]                    |
+------------------------------------------+
```

**Criterio Éxito:**
- Renombrar 1,000 archivos en < 10 segundos
- Preview antes de ejecutar
- Rollback si hay error

---

### **Phase 6: Advanced Features (Futuro)**

#### **6.1 Lyrics Automáticas**

**Qué es:**
Descargar letras de canciones automáticamente y mostrarlas en el player.

**Implementación:**
```python
# Genius API (gratis con API key)
import lyricsgenius

genius = lyricsgenius.Genius(api_key)

def get_lyrics(song_title, artist):
    song = genius.search_song(song_title, artist)
    return song.lyrics if song else None

# Store en database:
# ALTER TABLE songs ADD COLUMN lyrics TEXT;
```

**UI:**
```
+------------------+  +------------------+
| Song Playing     |  | Lyrics           |
|                  |  |                  |
| Bohemian Rhapsody|  | Is this the real |
| Queen            |  | life? Is this    |
| [▶] [⏸] [⏭]     |  | just fantasy?... |
+------------------+  |                  |
                      | [Scroll follows] |
                      +------------------+
```

---

#### **6.2 Spotify Playlist Import**

**Qué es:**
Importar playlists de Spotify (no descarga de Spotify, sino usar Spotify como "lista de compras" y descargar de YouTube).

**Flujo:**
1. User pega URL de Spotify playlist
2. App lee metadata de playlist (canciones, artistas)
3. Para cada canción:
   - Buscar en YouTube: "{artist} - {title} audio"
   - Descargar mejor match
   - Auto-completar metadata desde Spotify
4. Crear playlist local con mismas canciones

**Implementación:**
```python
import spotipy

def import_spotify_playlist(playlist_url):
    # 1. Get playlist tracks from Spotify
    tracks = spotify.playlist_tracks(playlist_url)

    # 2. For each track
    for track in tracks['items']:
        artist = track['track']['artists'][0]['name']
        title = track['track']['name']

        # 3. Search on YouTube
        youtube_url = search_youtube(f"{artist} - {title} audio")

        # 4. Download
        download_song(youtube_url)

        # 5. Add to database with Spotify metadata
        database.insert_song(
            title=title,
            artist=artist,
            album=track['track']['album']['name'],
            year=track['track']['album']['release_date'][:4],
            # ... more metadata
        )
```

**Limitación:**
⚠️ **NO puedes descargar directamente de Spotify** (DRM protegido). Solo usas Spotify como fuente de metadata y buscas la canción en YouTube.

---

#### **6.3 Format Converter**

**Qué es:**
Convertir entre formatos: MP3 ↔ FLAC ↔ WAV ↔ OGG ↔ M4A

**Casos de uso:**
- FLAC → MP3 (reducir tamaño para móvil)
- MP3 → WAV (edición en DAW)
- Batch convert 100 archivos

**Implementación:**
```python
from pydub import AudioSegment

def convert_audio(input_file, output_format):
    audio = AudioSegment.from_file(input_file)

    output_file = input_file.with_suffix(f".{output_format}")

    audio.export(
        output_file,
        format=output_format,
        bitrate="320k" if output_format == "mp3" else None
    )

    return output_file
```

**UI:**
```
+------------------------------------------+
| Format Converter                         |
+------------------------------------------+
| Selected: 25 files                       |
|                                          |
| Convert from: [MP3 v]                    |
| Convert to:   [FLAC v]                   |
|                                          |
| Quality: [====|====] 320kbps             |
|                                          |
| [x] Delete original files                |
| [ ] Keep both versions                   |
|                                          |
| [Cancel] [Convert]                       |
+------------------------------------------+
```

---

## 📊 TIMELINE ESTIMADO

| Phase | Features | Tiempo Estimado | Prioridad |
|-------|----------|----------------|-----------|
| **Phase 4** | Search tab, queue, playlists, MusicBrainz | 2 semanas | 🔥 ALTA |
| **Phase 5** | Duplicates, organize, rename | 1 semana | 🔥 ALTA |
| **Phase 6** | Lyrics, Spotify import, converter | Futuro | 🔷 MEDIA |

---

## ✅ CRITERIOS DE ÉXITO GENERAL

**Phase 4 Completada Cuando:**
- ✅ Buscar canción en YouTube/Spotify → resultados en < 2s
- ✅ Descargar playlist de 100 canciones → automático sin intervención
- ✅ Auto-complete metadata → 90%+ accuracy
- ✅ Download queue → 50 simultáneas sin lag en UI

**Phase 5 Completada Cuando:**
- ✅ Detectar duplicados → 95%+ accuracy, 0 falsos positivos
- ✅ Organizar 10,000 archivos → < 5 minutos
- ✅ Renombrar batch → preview + rollback

**Phase 6 Completada Cuando:**
- ✅ Lyrics automáticas → 80%+ canciones con letras
- ✅ Importar playlist Spotify → descargar de YouTube automáticamente
- ✅ Converter → batch convert 100 archivos < 5 minutos

---

## 🎯 PRIORIZACIÓN FEATURES

### **MUST HAVE (Phase 4):**
1. Search tab (YouTube + Spotify)
2. Download queue system
3. YouTube playlist downloader
4. MusicBrainz auto-complete

### **SHOULD HAVE (Phase 5):**
1. Duplicates detection
2. Auto-organize folders
3. Batch rename

### **NICE TO HAVE (Phase 6):**
1. Lyrics
2. Spotify playlist import
3. Format converter

---

## 📚 RECURSOS TÉCNICOS

### **APIs Gratis:**
- **YouTube Data API v3:** 10,000 requests/día
- **Spotify Web API:** 100 requests/segundo
- **MusicBrainz API:** Sin límite, sin API key
- **Genius API:** Gratis con API key

### **Librerías Python:**
```bash
pip install google-api-python-client  # YouTube
pip install spotipy                    # Spotify
pip install yt-dlp                     # Download
pip install musicbrainzngs             # MusicBrainz
pip install lyricsgenius               # Lyrics
pip install pydub                      # Audio processing
pip install acoustid                   # Fingerprinting
pip install chromaprint                # Fingerprinting
```

### **Documentación:**
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)

---

**🎵 ROADMAP APPROVED BY RICARDO - 12 OCTUBRE 2025** ✨
