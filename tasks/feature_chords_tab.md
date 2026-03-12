# Feature: Chords/Tabs Tab — Plan de Implementacion

**Fecha:** 2026-03-12
**Solicitado por:** Ricardo (para su hijo)
**Prioridad:** Feature nueva post-refactoring
**Estimacion:** 3 fases incrementales

---

## Concepto

Nueva tab "Acordes" que muestra los acordes de la cancion que se esta reproduciendo, con diagramas para guitarra y piano, transposicion, y auto-scroll sincronizado con la reproduccion.

**Diferenciador:** Los acordes se detectan **directamente del audio** (MP3) sin depender de APIs externas. Funciona 100% offline.

---

## Arquitectura

```
User plays song
    |
    v
song_metadata_changed signal
    |
    v
ChordsTab.on_song_changed(song_info)
    |
    v
1. Check cache (in-memory + DB column)
    |
    v
2. If not cached: ChordsWorker analyzes MP3
    |
    v
3. Display: chords above lyrics (if available)
   + chord diagrams (guitar/piano)
   + transpose controls
```

### Componentes nuevos

| Archivo | Tipo | Descripcion |
|---------|------|-------------|
| `src/api/chords_client.py` | Servicio | Detecta acordes desde MP3, cache, transposicion |
| `src/gui/tabs/chords_tab.py` | GUI Tab | Display de acordes con diagramas |
| `src/gui/widgets/chord_diagram_widget.py` | Widget | Renderiza diagramas guitarra/piano SVG |
| `data/chords-db/` | Datos | Base de datos JSON de digitaciones (MIT license) |
| `tests/test_chords_tab.py` | Tests | Tests unitarios |
| `tests/test_chords_client.py` | Tests | Tests del servicio |

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/controllers/ui_composer.py` | Agregar tab en `_create_tab_widget()` |
| `src/main.py` | Conectar `song_metadata_changed` -> `chords_tab` |
| `src/translations.py` | Agregar claves ES/EN |
| `requirements.txt` | Agregar dependencias |

---

## Dependencias nuevas

```
chord-extractor>=0.1      # Detecta acordes desde audio (usa Chordino VAMP plugin)
pychord>=1.0               # Parseo y transposicion de acordes
fretboardgtr>=0.2          # Diagramas de guitarra en SVG
```

**Dependencia de sistema:** `libcairo2-dev` (Linux, para fretboardgtr SVG)

**Base de datos de acordes:** `tombatossals/chords-db` (MIT) — JSON con todas las digitaciones de guitarra/ukulele. Se bundlea en `data/chords-db/`.

---

## Fases de Implementacion

### Fase 1: Deteccion de acordes + Display basico
**Scope:** Detectar acordes del MP3 y mostrarlos como texto

1. Instalar `chord-extractor`, `pychord`
2. Crear `src/api/chords_client.py`:
   - `analyze_file(mp3_path) -> list[tuple[float, str]]` (timestamp, chord)
   - Cache en memoria + guardar en DB (columna `chords` en songs)
   - Limpiar nombres de acordes con `pychord`
3. Crear `src/gui/tabs/chords_tab.py`:
   - Extiende QWidget (como LyricsTab)
   - Header con titulo/artista
   - QTextEdit con acordes en formato timeline
   - Worker thread para analisis (no bloquear UI)
4. Integrar en ui_composer + main.py
5. Tests

**Output Fase 1:**
```
[0:00] C
[0:05] Am
[0:10] F
[0:15] G
[0:20] C
...
```

### Fase 2: Diagramas de acordes + Transposicion
**Scope:** Diagramas visuales y cambio de tonalidad

1. Descargar `tombatossals/chords-db` JSON
2. Crear `src/gui/widgets/chord_diagram_widget.py`:
   - Diagrama de guitarra (SVG via `fretboardgtr` o custom QPainter)
   - Diagrama de piano (custom QPainter — teclado con notas resaltadas)
   - Selector de instrumento: guitarra / piano / ukulele
3. Agregar controles de transposicion:
   - Botones +/- semitono
   - Dropdown de tonalidad (C, C#, D, ...)
   - Capo selector (guitarra)
   - Usa `pychord.transpose()` internamente
4. Layout: splitter con acordes a la izquierda, diagrama a la derecha
5. Click en un acorde -> muestra su diagrama

**Output Fase 2:**
```
+------ Layout ------+
| [0:00] C    | [===] |
| [0:05] Am   | Chord |
| [0:10] F    | Diag  |
| [0:15] G    | [SVG] |
|             |       |
| [Transpose: +/-]   |
| [Instrumento: v]    |
+--------------------+
```

### Fase 3: Acordes sobre letras + Auto-scroll
**Scope:** Experiencia premium — acordes alineados con las letras

1. Si la cancion tiene lyrics (Genius), combinar acordes + letras:
   - Alinear por timestamp (acordes detectados tienen timestamp)
   - Formato ChordPro renderizado como HTML en QTextEdit
   - Acordes en color sobre las lineas de letra
2. Auto-scroll sincronizado con la reproduccion:
   - QTimer conectado a `audio_player.get_position()`
   - Scroll proporcional al progreso de la cancion
3. Highlight del acorde actual (resaltar el acorde que suena ahora)

**Output Fase 3:**
```
    C                Am
 Somebody once told me the world is
    F                G
 gonna roll me, I ain't the sharpest
    C
 tool in the shed...
    ^
    [auto-highlighted, auto-scrolling]
```

---

## Alternativa: Si chord-extractor no funciona bien

`chord-extractor` usa el plugin Chordino (VAMP), que requiere compilacion nativa. Si da problemas:

**Plan B:** `autochord` (pip install autochord)
- Usa NNLS-Chroma + Bi-LSTM-CRF
- 25 clases de acordes (mayores, menores, 7mas)
- Mas facil de instalar (pure Python + TensorFlow lite)

**Plan C:** Busqueda online como fallback
- Si el analisis de audio falla, buscar en fuentes web
- Hooktheory API (requiere cuenta, 10 req/10s)
- Solo como complemento, no como fuente principal

---

## Modelo de datos

### Columna nueva en `songs`

```sql
ALTER TABLE songs ADD COLUMN chords TEXT DEFAULT NULL;
-- Almacena JSON: [{"t": 0.0, "chord": "C"}, {"t": 5.2, "chord": "Am"}, ...]
```

### Cache en memoria

```python
# En ChordsClient
self._cache = {}  # {song_id: [{"t": float, "chord": str}, ...]}
```

---

## Prioridad vs Esfuerzo

| Fase | Valor para usuario | Esfuerzo | Dependencias |
|------|-------------------|----------|--------------|
| 1    | Alto (ve los acordes!) | Medio | chord-extractor, pychord |
| 2    | Alto (diagramas visuales) | Medio | fretboardgtr, chords-db |
| 3    | Muy alto (experiencia pro) | Alto | Fase 1 + 2 + lyrics |

---

## Riesgos

| Riesgo | Mitigacion |
|--------|------------|
| chord-extractor requiere VAMP plugin nativo | Plan B: autochord (pure Python) |
| Deteccion de acordes imprecisa | Mostrar confianza %, permitir edicion manual |
| fretboardgtr requiere libcairo en Linux | En Windows (target) funciona sin problema |
| Acordes no alineados bien con letras | Fase 3 es best-effort, Fase 1-2 son independientes |

---

## Verificacion

- [ ] Fase 1: Reproducir cancion -> acordes aparecen automaticamente
- [ ] Fase 1: Acordes se cachean (segunda reproduccion es instantanea)
- [ ] Fase 2: Click en acorde -> diagrama de guitarra aparece
- [ ] Fase 2: Cambiar instrumento -> diagrama cambia
- [ ] Fase 2: Transponer +2 -> todos los acordes suben 2 semitonos
- [ ] Fase 3: Acordes alineados sobre las letras
- [ ] Fase 3: Auto-scroll sigue la reproduccion
- [ ] Fase 3: Acorde actual resaltado
