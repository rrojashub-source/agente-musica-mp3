# Phase 8: AI Content Filter & Smart Classification

**Version:** 1.0
**Created:** December 8, 2025
**Status:** PROPOSED
**Estimated Effort:** 3-5 days (MVP) / 2 weeks (Full)
**Priority:** HIGH (Unique differentiator feature)

---

## Executive Summary

Implementar un sistema inteligente de clasificación de contenido musical que permita:
- Detectar contenido explícito automáticamente
- Identificar música infantil
- Clasificar por mood/energía
- Crear "Safe Zones" para diferentes contextos (niños, trabajo, eventos)

**Diferenciador clave:** Ningún reproductor de música local ofrece esto. Spotify Kids existe pero requiere suscripción y streaming. NEXUS Music lo hace OFFLINE con tu propia biblioteca.

---

## Problem Statement

### El Problema Real (Validado hoy)
- Usuario recibió 2 USBs con música mezclada
- Necesitaba separar: explícito vs limpio vs infantil
- Proceso manual: 2+ horas
- Con NEXUS AI: ~5 minutos

### Gap en el Mercado
| Solución | Problema |
|----------|----------|
| Spotify Kids | Requiere streaming + suscripción |
| iTunes | No tiene filtro de contenido |
| VLC/Winamp | Zero clasificación |
| Playlists manuales | Tedioso, error-prone |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI CONTENT FILTER SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │   TIER 1     │   │   TIER 2     │   │   TIER 3     │        │
│  │  Metadata    │──▶│   Lyrics     │──▶│   Audio      │        │
│  │  Analysis    │   │   Analysis   │   │   Analysis   │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│        │                   │                   │                 │
│        ▼                   ▼                   ▼                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              CLASSIFICATION ENGINE                   │       │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │       │
│  │  │EXPLICIT │ │CHILDREN │ │ CLEAN   │ │ MOOD    │   │       │
│  │  │ 0-100   │ │ 0-100   │ │ 0-100   │ │Vector   │   │       │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │       │
│  └─────────────────────────────────────────────────────┘       │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                 ACTION ENGINE                        │       │
│  │  [Tag ID3] [Move] [Copy] [Smart Playlist] [Export]  │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Multi-Tier Classification System

### TIER 1: Metadata Analysis (Offline, Instant)
**Confianza: 70-95%** | **Costo: $0** | **Velocidad: <1ms/song**

```python
class MetadataAnalyzer:
    """
    Analiza ID3 tags + nombre archivo + artista conocido
    """

    # Base de datos de artistas categorizados
    EXPLICIT_ARTISTS = {
        "bad_bunny": 0.95,      # 95% probabilidad explícito
        "anuel_aa": 0.98,
        "daddy_yankee": 0.60,   # Depende del álbum
        "cardi_b": 0.95,
        "megan_thee_stallion": 0.98,
        # ... 500+ artistas
    }

    CHILDREN_ARTISTS = {
        "plim_plim": 1.0,
        "pinkfong": 1.0,
        "cocomelon": 1.0,
        "cantajuego": 1.0,
        "gallina_pintadita": 1.0,
        # ... 200+ artistas
    }

    CLEAN_ARTISTS = {
        "coldplay": 0.95,
        "ed_sheeran": 0.85,
        "taylor_swift": 0.70,  # Varía por álbum
        # ... 1000+ artistas
    }

    # Keywords en títulos
    EXPLICIT_KEYWORDS = [
        "explicit", "dirty", "uncensored", "xxx",
        # Palabras en español
        "perra", "puta", "culo", "mierda", "cabron",
        # Contextuales
        "twerk", "perreo", "sexo",
    ]

    CHILDREN_KEYWORDS = [
        "infantil", "kids", "niños", "nursery",
        "lullaby", "cancion de cuna", "baby",
    ]
```

**Fuentes de datos:**
- ID3 Genre tag
- ID3 Comment tag (a veces tiene "explicit")
- Nombre de archivo
- Carpeta contenedora (artista)
- MusicBrainz metadata (ya integrado)

### TIER 2: Lyrics Analysis (Online, Deep)
**Confianza: 88-94%** | **Costo: Free tier** | **Velocidad: 1-3s/song**

```python
class LyricsAnalyzer:
    """
    Obtiene letras y analiza contenido con NLP
    Basado en research: BERT alcanza 94% accuracy
    """

    def __init__(self):
        # APIs de letras (fallback chain)
        self.genius = GeniusAPI()      # Gratis con límites
        self.musixmatch = MusixmatchAPI()  # 2000 req/día gratis

        # Modelo de clasificación
        self.classifier = self._load_classifier()

    def analyze(self, artist: str, title: str) -> ContentScore:
        lyrics = self._fetch_lyrics(artist, title)
        if not lyrics:
            return ContentScore(confidence=0)

        # Multi-dimensional analysis (basado en research 2024)
        return ContentScore(
            explicit=self._detect_explicit(lyrics),
            violence=self._detect_violence(lyrics),
            substance=self._detect_drugs_alcohol(lyrics),
            sexual=self._detect_sexual_content(lyrics),
            positive=self._detect_positive_messages(lyrics),
        )

    def _detect_explicit(self, lyrics: str) -> float:
        """
        Combina:
        1. Profanity dictionary (baseline)
        2. Contextual analysis (ML)
        3. Sentiment analysis
        """
        # Approach 1: Dictionary-based (fast, 80% accuracy)
        profanity_score = self._profanity_check(lyrics)

        # Approach 2: ML classification (slower, 94% accuracy)
        ml_score = self._ml_classify(lyrics)

        # Weighted combination
        return (profanity_score * 0.3) + (ml_score * 0.7)
```

**APIs disponibles (research):**
| API | Free Tier | Python Package | Accuracy |
|-----|-----------|----------------|----------|
| [Genius](https://lyricsgenius.readthedocs.io/) | Unlimited* | `lyricsgenius` | N/A (just lyrics) |
| [Musixmatch](https://publicapis.io/musixmatch-api) | 2000/día | `pymusixmatch` | N/A (just lyrics) |

**Modelos de clasificación (research 2024):**
| Model | Accuracy | Speed | Size |
|-------|----------|-------|------|
| LSTM | 88% | Fast | 50MB |
| BERT | 94% | Medium | 400MB |
| DistilBERT | 91% | Fast | 250MB |

### TIER 3: Audio Analysis (Offline, Advanced)
**Confianza: 75-85%** | **Costo: $0** | **Velocidad: 2-5s/song**

```python
class AudioAnalyzer:
    """
    Analiza características del audio sin letras
    Útil para música instrumental o idiomas desconocidos
    """

    def __init__(self):
        self.librosa = librosa  # Audio processing
        self.yamnet = self._load_yamnet()  # Google's audio classifier

    def analyze(self, audio_path: str) -> AudioFeatures:
        # Cargar audio
        y, sr = librosa.load(audio_path, duration=30)

        # Extraer features (basado en Spotify API)
        return AudioFeatures(
            # Energy: 0.0 (calm) to 1.0 (intense)
            energy=self._compute_energy(y, sr),

            # Valence: 0.0 (sad) to 1.0 (happy)
            valence=self._compute_valence(y, sr),

            # Danceability
            danceability=self._compute_danceability(y, sr),

            # Speechiness: detecta contenido hablado/rap
            speechiness=self._compute_speechiness(y, sr),

            # Tempo (BPM)
            tempo=librosa.beat.tempo(y=y, sr=sr)[0],

            # Instrumentalness: 1.0 = no vocals
            instrumentalness=self._compute_instrumentalness(y, sr),

            # Children detection (pitch, tempo patterns)
            children_score=self._detect_children_music(y, sr),
        )

    def _detect_children_music(self, y, sr) -> float:
        """
        Patrones típicos de música infantil:
        - Tempo moderado (100-130 BPM)
        - Melodías simples (poca variación tonal)
        - Voces agudas frecuentes
        - Repetición alta
        """
        tempo = librosa.beat.tempo(y=y, sr=sr)[0]

        # Children's music usually 100-130 BPM
        tempo_score = 1.0 if 100 <= tempo <= 130 else 0.5

        # High pitch detection
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        high_pitch_ratio = self._compute_high_pitch_ratio(pitches)

        # Repetition detection
        repetition = self._compute_repetition(y, sr)

        return (tempo_score * 0.3 + high_pitch_ratio * 0.4 + repetition * 0.3)
```

**Librerías (open source):**
| Library | Use Case | Source |
|---------|----------|--------|
| [librosa](https://librosa.org/) | Audio feature extraction | PyPI |
| [openSMILE](https://www.audeering.com/research/open-source/) | Speech/music analysis | audEERING |
| [YAMNet](https://ai.google.dev/edge/mediapipe/solutions/audio/audio_classifier) | Audio event classification | Google MediaPipe |

---

## Classification Categories

### 1. Content Rating (Principal)
```python
class ContentRating(Enum):
    EXPLICIT = "explicit"      # Contenido adulto
    SUGGESTIVE = "suggestive"  # Insinuaciones
    CLEAN = "clean"            # Apto para todos
    CHILDREN = "children"      # Específico para niños
    UNKNOWN = "unknown"        # No clasificado
```

### 2. Multi-dimensional Analysis (Avanzado)
Basado en [research 2024](https://aclanthology.org/2024.lrec-main.1129.pdf):

```python
@dataclass
class ContentDimensions:
    # 0.0 to 1.0 scale
    positive_messages: float   # Mensajes positivos
    violence: float            # Referencias a violencia
    substance: float           # Drogas/alcohol
    sexual_content: float      # Contenido sexual
    profanity: float           # Lenguaje fuerte
    consumerism: float         # Materialismo/lujo
```

### 3. Mood/Context Classification
```python
class MoodCategory(Enum):
    PARTY = "party"            # Fiesta, alta energía
    RELAXATION = "relaxation"  # Relajación, baja energía
    WORKOUT = "workout"        # Ejercicio, motivación
    FOCUS = "focus"            # Concentración, instrumental
    ROMANCE = "romance"        # Romántico
    SAD = "sad"                # Melancólico
    CHILDREN = "children"      # Música infantil
```

---

## Smart Features (Thinking Outside the Box)

### Feature 1: "Safe Zone" Profiles
```python
class SafeZoneProfile:
    """
    Perfiles predefinidos para diferentes contextos
    """
    PROFILES = {
        "toddler": SafeZone(
            max_age=3,
            allowed_ratings=[ContentRating.CHILDREN],
            max_tempo=130,
            require_high_valence=True,
            block_keywords=["muerte", "miedo", "oscuro"],
        ),

        "kid_5_10": SafeZone(
            max_age=10,
            allowed_ratings=[ContentRating.CHILDREN, ContentRating.CLEAN],
            allow_instrumental=True,
        ),

        "family_event": SafeZone(
            allowed_ratings=[ContentRating.CLEAN],
            block_explicit_artists=True,
            prefer_high_valence=True,
        ),

        "work_safe": SafeZone(
            allowed_ratings=[ContentRating.CLEAN],
            prefer_instrumental=True,
            max_energy=0.7,
        ),
    }
```

### Feature 2: USB Export Wizard
```
┌─────────────────────────────────────────┐
│       USB EXPORT WIZARD                 │
├─────────────────────────────────────────┤
│ Select destination: [F:\]              │
│                                         │
│ Export Profile:                         │
│ ○ All music                            │
│ ● Kids party (clean + children)        │
│ ○ Work safe (clean + instrumental)     │
│ ○ Custom filter...                     │
│                                         │
│ Options:                                │
│ ☑ Organize by artist folders           │
│ ☑ Include album art                    │
│ ☐ Convert to MP3 (320kbps)             │
│                                         │
│ Preview: 156 songs (2.3 GB)            │
│                                         │
│ [Cancel]              [Export]          │
└─────────────────────────────────────────┘
```

### Feature 3: Real-time Classification on Import
```python
class ImportClassifier:
    """
    Clasifica automáticamente al importar nueva música
    """

    async def on_new_song_added(self, song: Song):
        # Tier 1: Instant metadata check
        score = self.metadata_analyzer.analyze(song)

        if score.confidence < 0.8:
            # Tier 2: Background lyrics fetch
            self.queue_lyrics_analysis(song)

        # Tag immediately with current confidence
        song.content_rating = score.rating
        song.content_confidence = score.confidence
```

### Feature 4: Community Classification Database
```python
class CommunityClassifications:
    """
    Base de datos compartida de clasificaciones
    - Users can submit corrections
    - Crowdsourced artist database
    - Syncs with NEXUS servers (optional)
    """

    API_ENDPOINT = "https://nexus-music-api.com/classifications"

    def submit_correction(self, song_id: str, correct_rating: ContentRating):
        """User corrige una clasificación incorrecta"""
        pass

    def sync_artist_database(self):
        """Descarga clasificaciones de artistas actualizadas"""
        pass
```

### Feature 5: AI Learning from User Behavior
```python
class UserBehaviorLearning:
    """
    Aprende de las correcciones del usuario
    - Si usuario mueve canción a "Kids", aprende patrón
    - Si usuario elimina canción del playlist "Clean", aprende
    """

    def on_user_action(self, action: UserAction):
        if action.type == "move_to_playlist":
            playlist_type = self.get_playlist_type(action.playlist)
            self.learn_association(action.song, playlist_type)
```

### Feature 6: Parental Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│                 PARENTAL DASHBOARD                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Library Overview:                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ████████████████████░░░░ 78% Clean                   │  │
│  │ ████░░░░░░░░░░░░░░░░░░░░ 15% Explicit                │  │
│  │ ██░░░░░░░░░░░░░░░░░░░░░░  7% Children                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Quick Actions:                                             │
│  [Create Kids Playlist]  [Remove All Explicit]             │
│  [Export Safe USB]       [Review Uncertain]                │
│                                                             │
│  Recent Additions Needing Review: 12 songs                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Bad Bunny - Monaco     │ EXPLICIT (95%) │ [Keep][Del]│   │
│  │ Unknown - Party Song   │ UNCERTAIN(60%) │ [Review]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 8.1: MVP Core (2-3 días)
```
□ src/services/content_classifier.py
  ├── MetadataAnalyzer (artist DB + keywords)
  ├── ContentRating enum
  └── ClassificationResult dataclass

□ src/data/artist_database.json
  ├── 100 explicit artists
  ├── 50 children artists
  └── 200 clean artists

□ src/gui/tabs/content_filter_tab.py
  ├── Scan folder/library button
  ├── Results table with ratings
  ├── Bulk actions (move, tag, delete)
  └── Export filtered selection
```

### Phase 8.2: Lyrics Integration (2 días)
```
□ src/services/lyrics_analyzer.py
  ├── GeniusAPI integration
  ├── MusixmatchAPI fallback
  ├── Profanity detection
  └── Basic ML classification

□ src/services/content_cache.py
  ├── SQLite cache for lyrics
  ├── Classification cache
  └── Background fetch queue
```

### Phase 8.3: Audio Analysis (2-3 días)
```
□ src/services/audio_analyzer.py
  ├── librosa integration
  ├── Energy/valence computation
  ├── Children music detection
  └── Mood classification

□ Dependencies
  ├── librosa
  ├── numpy
  └── scipy
```

### Phase 8.4: Smart Features (3-4 días)
```
□ Safe Zone Profiles
□ USB Export Wizard
□ Real-time import classification
□ Parental Dashboard
□ User behavior learning
```

### Phase 8.5: Polish & Testing (2 días)
```
□ Unit tests (target: 90% coverage)
□ Integration tests
□ Performance optimization
□ Documentation
```

---

## Database Schema Updates

```sql
-- Add to existing songs table
ALTER TABLE songs ADD COLUMN content_rating TEXT DEFAULT 'unknown';
ALTER TABLE songs ADD COLUMN content_confidence REAL DEFAULT 0.0;
ALTER TABLE songs ADD COLUMN explicit_score REAL DEFAULT 0.0;
ALTER TABLE songs ADD COLUMN children_score REAL DEFAULT 0.0;
ALTER TABLE songs ADD COLUMN violence_score REAL DEFAULT 0.0;
ALTER TABLE songs ADD COLUMN sexual_score REAL DEFAULT 0.0;
ALTER TABLE songs ADD COLUMN substance_score REAL DEFAULT 0.0;
ALTER TABLE songs ADD COLUMN valence REAL;
ALTER TABLE songs ADD COLUMN energy REAL;
ALTER TABLE songs ADD COLUMN classification_source TEXT;  -- 'metadata', 'lyrics', 'audio', 'user'
ALTER TABLE songs ADD COLUMN classified_at TIMESTAMP;

-- New table for artist classifications
CREATE TABLE artist_classifications (
    artist_name TEXT PRIMARY KEY,
    default_rating TEXT,
    confidence REAL,
    source TEXT,  -- 'database', 'community', 'user'
    updated_at TIMESTAMP
);

-- Cache for lyrics
CREATE TABLE lyrics_cache (
    song_id TEXT PRIMARY KEY,
    lyrics TEXT,
    source TEXT,
    fetched_at TIMESTAMP
);
```

---

## Dependencies

### Required (MVP)
```
# Already have
mutagen          # ID3 tag reading

# New
lyricsgenius     # Genius API
pymusixmatch     # Musixmatch API (backup)
better-profanity # Profanity detection
```

### Optional (Advanced)
```
librosa          # Audio analysis
transformers     # BERT models (if using ML)
torch            # PyTorch backend
```

### Size Impact
| Feature | Dependencies | Size |
|---------|--------------|------|
| MVP | lyricsgenius, better-profanity | +5MB |
| Audio | librosa, numpy, scipy | +150MB |
| ML | transformers, torch | +500MB |

**Recommendation:** Start with MVP, audio optional, ML as future enhancement.

---

## API Rate Limits & Costs

| Service | Free Tier | Paid |
|---------|-----------|------|
| Genius API | Unlimited (slow) | N/A |
| Musixmatch | 2000 req/day | $0.001/req |
| Spotify Audio Features | 0 (need track on Spotify) | N/A |

**Strategy:** Cache aggressively, classify in background, prioritize metadata tier.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Classification accuracy (explicit) | >90% |
| Classification accuracy (children) | >95% |
| Songs classified per second | >10 (metadata only) |
| User corrections needed | <5% |
| False positive rate (explicit) | <3% |

---

## Competitive Analysis

| Feature | NEXUS | Spotify Kids | iTunes | VLC |
|---------|-------|--------------|--------|-----|
| Offline classification | ✅ | ❌ | ❌ | ❌ |
| Custom safe zones | ✅ | ❌ | ❌ | ❌ |
| USB export filtered | ✅ | ❌ | ❌ | ❌ |
| Multi-dimensional analysis | ✅ | ❌ | ❌ | ❌ |
| Local library support | ✅ | ❌ | ✅ | ✅ |
| Free | ✅ | ❌ | ✅ | ✅ |

**NEXUS = Único reproductor local con AI Content Filter**

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives (clean marked explicit) | Medium | User correction + learning |
| False negatives (explicit missed) | High | Conservative defaults + Tier 2/3 |
| API rate limits | Medium | Aggressive caching |
| Large ML models | High | Make ML optional, MVP uses rules |
| Non-English lyrics | Medium | Support Spanish priority, expand later |

---

## Future Enhancements

1. **Voice Command:** "Hey NEXUS, play kids music"
2. **Time-based Profiles:** "Work mode" during business hours
3. **Location-based:** Safe mode when connected to "Kids Room" speakers
4. **Sync with Parental Controls:** Integration with Windows Family Safety
5. **Community Database:** Share classifications with other NEXUS users

---

## References

### Research Papers
- [Explicit Content Detection in Music Lyrics Using Machine Learning (IEEE)](https://ieeexplore.ieee.org/document/8367165/)
- [Deep Learning for Explicit Content Classification (IEEE 2024)](https://ieeexplore.ieee.org/document/10903884/)
- [Multi-dimensional Content Analysis (LREC-COLING 2024)](https://aclanthology.org/2024.lrec-main.1129.pdf)
- [NLP Detecting Explicit Content (Medium)](https://medium.com/@tanyufei0514/nlp-detecting-explicit-content-in-music-lyrics-7cd0450779e5)

### APIs & Tools
- [Spotify Audio Features API](https://developer.spotify.com/documentation/web-api/reference/get-audio-features)
- [lyricsgenius Documentation](https://lyricsgenius.readthedocs.io/en/master/)
- [Google MediaPipe Audio Classifier](https://ai.google.dev/edge/mediapipe/solutions/audio/audio_classifier)
- [openSMILE - Open Source Audio Analysis](https://www.audeering.com/research/open-source/)
- [Music Genre Classification (GitHub)](https://github.com/topics/music-genre-classification)

### Industry Standards
- [RIAA Parental Advisory Label](https://www.riaa.com/resources-learning/parental-advisory-label/)
- [Spotify Safety Center](https://www.spotify.com/uk/safetyandprivacy/parental-guide)

---

## Approval

**Prepared by:** NEXUS AI
**Date:** December 8, 2025
**Status:** Awaiting Ricardo's approval

### Decision Required:
1. **Approve MVP** - Start with metadata + lyrics (3-4 days)
2. **Approve Full** - Include audio analysis (7-10 days)
3. **Defer** - Complete packaging (.exe) first
4. **Modify** - Request changes to plan

---

*"The only music player that knows when to protect little ears."*
