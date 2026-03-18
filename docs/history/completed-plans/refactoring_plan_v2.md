# Plan de Refactoring — NEXUS Music Manager v2.0

**Creado:** 2026-03-10
**Basado en:** Auditoria integral (4 agentes: code review, security, refactoring, stack research)
**Objetivo:** Llevar el proyecto de 6.8/10 a 8.5/10+
**Tiempo estimado total:** 6 semanas

---

## Fase 1: Seguridad + Blockers (Semana 1-2)

**Objetivo:** Eliminar vulnerabilidades criticas y codigo roto.

### 1.1 Auth JWT en Flask Remote Server
- **Archivo:** `src/services/remote_server.py`
- **Que hacer:**
  - Agregar autenticacion JWT en todos los endpoints
  - CORS restrictivo: solo `127.0.0.1` y `localhost`
  - Default host: `127.0.0.1` (no `0.0.0.0`)
  - Rate limiting por IP
  - Generar token unico por sesion, mostrarlo en QR
- **Tests:** `tests/test_remote_server.py` — agregar tests de auth

### 1.2 Validar output_path en Download Worker
- **Archivo:** `src/workers/download_worker.py:49`
- **Que hacer:**
  - Usar `validate_path(output_path, base_dir)` de `input_sanitizer.py`
  - Asegurar que output_path esta dentro del directorio de descargas permitido
  - Rechazar paths con `..`, symlinks fuera de base
- **Tests:** Agregar test de path traversal

### 1.3 Seguridad de Plugins
- **Archivo:** `src/plugins/plugin_manager.py:157-180`
- **Que hacer:**
  - Whitelist de plugins permitidos (lista en config)
  - NO cargar plugins que no esten en whitelist
  - No modificar sys.path globalmente (usar spec_from_file_location con rutas explicitas)
  - Log de warning cuando se intenta cargar plugin no autorizado
- **Tests:** Test de plugin no autorizado rechazado

### 1.4 Validar URLs en Download Queue
- **Archivo:** `src/core/download_queue.py:71`
- **Que hacer:**
  - Validar que URL empiece con `https://youtube.com/`, `https://youtu.be/`, `https://www.youtube.com/`
  - Sanitizar metadata con `sanitize_metadata()`
  - Rechazar URLs malformadas
- **Tests:** Test de URL invalida rechazada

### 1.5 Completar Metodos Truncados
- **Archivos:**
  - `src/main.py` — `_toggle_theme()`
  - `src/core/audio_player.py` — `queue_next()`
  - `src/core/download_queue.py` — `_import_to_database()`
  - `src/services/cloud_sync_service.py` — `GoogleDriveProvider.connect()`
- **Que hacer:** Revisar cada metodo, completar implementacion o marcar como NotImplementedError explicito

### 1.6 Threading Safety
- **Archivos:** `src/core/audio_player.py`, `src/core/download_queue.py`
- **Que hacer:**
  - Agregar `threading.RLock()` para `_state`, `_duration` en audio_player
  - Proteger `_items` dict en download_queue con lock
  - Usar `with self._lock:` en todas las operaciones sobre estado compartido
- **Tests:** Test de acceso concurrente (stress test basico)

### 1.7 Especificar Excepciones
- **Archivos:** Global (348 ocurrencias de `except Exception`)
- **Que hacer:**
  - Reemplazar con excepciones especificas: `FileNotFoundError`, `sqlite3.OperationalError`, `requests.Timeout`, `ID3Error`, etc.
  - En casos donde realmente se necesite catch-all, agregar logging.critical y re-raise
  - Priorizar: remote_server, download_worker, plugin_manager, audio_player
- **Herramienta:** `grep -rn "except Exception" src/` para listar todas

---

## Fase 2: Refactoring Estructural (Semana 3-4)

**Objetivo:** Romper God Classes, eliminar duplicacion, habilitar testing.

### 2.1 Split main.py en Controllers
- **Archivo:** `src/main.py` (1373 lineas -> ~200 lineas)
- **Crear:**
  - `src/controllers/playback_controller.py` — logica de reproduccion
  - `src/controllers/library_controller.py` — DB + busqueda
  - `src/controllers/ui_composer.py` — crear tabs/widgets
  - `src/controllers/remote_controller.py` — comandos remotos
  - `src/controllers/stats_controller.py` — estadisticas + plugins
- **main.py queda como Facade** que instancia controllers y conecta signals
- **Tests:** Cada controller testeable independientemente

### 2.2 Extract BaseTab Class
- **Crear:** `src/gui/base/base_tab.py`
- **Template Methods:**
  - `_init_ui()` — setup comun (layout, tabla)
  - `get_table_columns()` — abstracto, cada tab define columnas
  - `_load_data()` — abstracto, cada tab carga datos
  - `_connect_signals()` — template con hooks
- **Refactorizar:** 15 tabs para heredar de BaseTab
- **Resultado:** Cada tab reduce ~30% de codigo

### 2.3 Split audio_embeddings.py
- **Archivo:** `src/core/audio_embeddings.py` (1074 lineas -> 3 archivos)
- **Crear:**
  - `src/core/audio_feature_extractor.py` — FFT + spectrum + MFCC
  - `src/core/bpm_detector.py` — deteccion de tempo (puro calculo, sin DB)
  - `src/core/mood_classifier.py` — clasificacion de mood (puro calculo)
- **audio_embeddings.py queda como orquestador** que usa las 3 clases
- **Beneficio:** BPMDetector y MoodClassifier testables sin DB

### 2.4 Split cleanup_assistant_tab.py
- **Archivo:** `src/cleanup_assistant_tab.py` (1210 lineas -> 3 archivos)
- **Crear:**
  - `src/core/metadata_issue_detector.py` — detectar problemas
  - `src/core/musicbrainz_enricher.py` — buscar metadata online
  - `src/core/cleanup_orchestrator.py` — coordinar y aplicar cambios
- **Tab queda como UI** que llama al orchestrator

### 2.5 Dependency Injection
- **Crear:** `src/services/service_factory.py`
- **AppContext dataclass** con todas las dependencias
- **main.py** recibe AppContext en lugar de instanciar 26 cosas
- **Beneficio:** Tests con mocks, startup configurable

### 2.6 Eliminar Dead Code
- **Eliminar:** `src/main_window_complete.py` (804 lineas — duplicado de main.py)
- **Limpiar:** Codigo comentado en library_tab.py y otros
- **Ejecutar:** `autoflake --remove-all-unused-imports src/`

---

## Fase 3: Migracion de Stack (Semana 5-6)

**Objetivo:** Modernizar stack sin reescribir.

### 3.1 PyQt6 -> PySide6
- **Por que:** Licencia LGPL (libre para comercial), soporte Nuitka oficial
- **Como:** Cambiar imports (`from PyQt6` -> `from PySide6`), ajustar flags menores
- **Herramienta:** Script de migracion automatica (sed/regex)
- **Tests:** Ejecutar suite completa despues de migracion

### 3.2 PyInstaller -> Nuitka
- **Por que:** EXE 35-40% mas pequeno, 2-4x mas rapido
- **Como:**
  - Instalar: `pip install nuitka`
  - Comando: `python -m nuitka --standalone --enable-plugin=pyside6 --windows-disable-console src/main.py`
  - Configurar exclusiones (tkinter, matplotlib, scipy, etc.)
- **Resultado esperado:** 164MB -> ~100MB

### 3.3 pygame -> python-mpv
- **Por que:** Gapless playback real, todos los formatos, ecualizador nativo
- **Como:**
  - Instalar: `pip install python-mpv` + bundlear `libmpv-2.dll`
  - Refactorizar `src/core/audio_player.py` para usar mpv API
  - Mantener misma interfaz publica (play, pause, stop, seek, volume)
- **Tests:** Todos los test_audio_player deben pasar

### 3.4 UPX Compression
- **Como:** Nuitka con `--enable-plugin=upx`
- **Resultado:** ~80-95MB final (reduccion 45% vs original)

---

## Fase 4: Polish (Continuo / Post-refactoring)

### 4.1 Type Hints Completos
- Ejecutar `mypy src/ --ignore-missing-imports`
- Priorizar: database/manager.py, core/*.py, services/*.py
- Objetivo: 0 errores mypy en modulos criticos

### 4.2 Constantes para Magic Numbers
- Crear `src/constants.py` con todas las constantes UI/audio/config
- Reemplazar ~329 magic numbers

### 4.3 Variables Globales -> Singletons
- `translations.py`: `_current_language` -> `LanguageManager.get_instance()`
- Otros modulos con estado global

### 4.4 Documentacion
- Docstrings completos en database/manager.py (Args, Returns, Raises)
- Docstrings en todos los metodos publicos de controllers nuevos

### 4.5 Patrones Avanzados (Opcional)
- Event Bus para signals (reemplazar 42+ conexiones manuales)
- Repository Pattern para DB access
- Command Pattern para undo/redo en rename/delete
- Strategy Pattern para content filter

---

## Criterios de Exito

| Metrica | Antes | Despues | Meta |
|---------|-------|---------|------|
| Puntuacion general | 6.8/10 | 8.5/10 | 8.5+ |
| Vulnerabilidades criticas | 3 | 0 | 0 |
| Archivo mas grande | 1373 LOC | <500 LOC | <500 |
| except Exception genericos | 348 | <20 | <20 |
| Type hints coverage | ~1.5% | >50% | >50% |
| Tamano EXE | 164MB | ~90MB | <100MB |
| Deps max por clase | 26 | <8 | <8 |
| Test coverage estimado | ~30% | ~70% | >65% |

---

## Notas Importantes

- **NO agregar features nuevas** hasta completar Fase 1 y 2
- **Cada fase termina con tests pasando** — no avanzar si hay regresiones
- **Commits atomicos** — un commit por cambio logico, no megacommits
- **El proyecto ya funciona (v1.0.0)** — el refactoring es mejora, no reconstruccion
- **El exe en dist/ sigue siendo la version funcional** hasta que se recompile

---

*Plan creado por NEXUS@CLI basado en auditoria de 4 agentes (2026-03-10)*
