# Plan: NEXUS Music Manager — De 8.5 a 10/10

**Fecha:** 2026-03-15
**Score actual:** 8.5/10
**Target:** 10/10
**Estimacion total:** ~20-25 horas
**Estrategia:** 5 bloques, ejecutar en orden de impacto

---

## BLOQUE 1: Tests de Cobertura (Score +0.8)
**Prioridad:** MAXIMA | **Esfuerzo:** 6-8 hrs | **Target:** >=80% coverage

### 1.1 Tests para 11 modulos core sin cobertura (~3 hrs)

| Modulo | Archivo test a crear | Tests estimados |
|--------|---------------------|-----------------|
| `core/mood_classifier.py` | `tests/test_mood_classifier.py` | 10-12 |
| `core/bpm_detector.py` | `tests/test_bpm_detector.py` | 8-10 |
| `core/recommendation_engine.py` | `tests/test_recommendation_engine.py` | 10-12 |
| `core/cover_art_manager.py` | `tests/test_cover_art_manager.py` | 8-10 |
| `core/metadata_fetcher.py` | `tests/test_metadata_fetcher.py` | 10-12 |
| `core/waveform_extractor.py` | `tests/test_waveform_extractor.py` | 6-8 |
| `core/spectrum_worker.py` | `tests/test_spectrum_worker.py` | 5-6 |
| `core/cleanup_workflow.py` | `tests/test_cleanup_workflow.py` | 8-10 |
| `core/metadata_cleaner.py` | `tests/test_metadata_cleaner.py` | 6-8 |
| `core/acoustid_client.py` | `tests/test_acoustid_client.py` | 5-6 |
| `core/api_adapters.py` | `tests/test_api_adapters.py` | 4-5 |

**Total:** ~80-100 tests nuevos

### 1.2 Test para API sin cobertura (~20 min)

| Modulo | Archivo test a crear | Tests estimados |
|--------|---------------------|-----------------|
| `api/chords_client.py` | `tests/test_chords_client.py` | 8-10 |

### 1.3 Tests para utils sin cobertura (~30 min)

| Modulo | Archivo test a crear | Tests estimados |
|--------|---------------------|-----------------|
| `utils/constants.py` | `tests/test_constants.py` | 5 |
| `utils/fpcalc_checker.py` | `tests/test_fpcalc_checker.py` | 5 |
| `utils/subprocess_patch.py` | `tests/test_subprocess_patch.py` | 5 |

### 1.4 Completar 23 tests TDD red-phase (~1-2 hrs)

| Archivo | Tests pendientes | Accion |
|---------|-----------------|--------|
| `tests/test_search_tab_ui.py` | 6 con TODO | Implementar |
| `tests/test_playlist_downloader.py` | 8 con TODO | Implementar |
| `tests/test_metadata_autocomplete.py` | 9 con TODO | Implementar |

### 1.5 Configurar coverage report (~10 min)

```bash
# Agregar a pytest.ini
addopts = --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80
```

### 1.6 Centralizar fixtures en conftest.py (~1 hr)

Mover a `tests/conftest.py`:
- `temp_db` — DB temporal con cleanup WAL
- `mock_deps` — dependencias mock comunes
- `qapp` — QApplication singleton
- `temp_music_folder` — directorio con MP3s de test

**Criterio de exito:** `pytest --cov` muestra >=80% en src/

---

## BLOQUE 2: Type Hints + mypy (Score +0.3)
**Prioridad:** ALTA | **Esfuerzo:** 4-6 hrs | **Target:** mypy --strict pasa sin errores

### 2.1 Configurar mypy.ini (~15 min)

```ini
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
check_untyped_defs = True
no_implicit_optional = True
strict_equality = True
warn_redundant_casts = True

# Ignorar terceros sin stubs
[mypy-PySide6.*]
ignore_missing_imports = True
[mypy-mpv.*]
ignore_missing_imports = True
[mypy-mutagen.*]
ignore_missing_imports = True
[mypy-spotipy.*]
ignore_missing_imports = True
```

### 2.2 Type hints por capa (orden de dependencia)

| Orden | Capa | Archivos | Esfuerzo |
|-------|------|----------|----------|
| 1 | `utils/` | 6 archivos | 30 min |
| 2 | `database/` | 2 archivos | 30 min |
| 3 | `core/` | 26 archivos | 2 hrs |
| 4 | `api/` | 6 archivos | 30 min |
| 5 | `services/` | 8 archivos | 45 min |
| 6 | `controllers/` | 4 archivos | 30 min |
| 7 | `gui/` | ~40 archivos (solo firmas publicas) | 1 hr |

### 2.3 Verificar

```bash
mypy src/ --ignore-missing-imports
# Target: 0 errors
```

**Criterio de exito:** `mypy src/` pasa limpio

---

## BLOQUE 3: Seguridad + Infra (Score +0.3)
**Prioridad:** MEDIA-ALTA | **Esfuerzo:** 2-3 hrs

### 3.1 CORS especifico (~10 min)

**Archivo:** `src/services/remote_server.py:151-155`

Cambiar:
```python
# ANTES
"http://192.168.*.*:*"
# DESPUES
f"http://{self._host}:*"  # Solo el IP del servidor
```

### 3.2 Eliminar token en query param (~15 min)

**Archivo:** `src/services/remote_server.py:194`

Eliminar fallback a `request.args.get('token')`. Solo Bearer header.

### 3.3 Token con expiracion (~30 min)

**Archivo:** `src/services/remote_server.py`

- Generar token con timestamp: `token = f"{secrets.token_urlsafe(32)}.{int(time.time())}`
- En `_require_auth()`: verificar edad < 24h
- Endpoint `/api/refresh-token` para renovar

### 3.4 CI/CD con GitHub Actions (~1 hr)

**Crear:** `.github/workflows/ci.yml`

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/ -v --tb=short --cov=src
      - run: mypy src/ --ignore-missing-imports
      - run: bandit -r src/ -ll
      - run: flake8 src/ --max-line-length=120
```

### 3.5 Pre-commit hooks (~30 min)

**Crear:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks: [{id: black}]
  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks: [{id: isort}]
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks: [{id: flake8, args: [--max-line-length=120]}]
```

```bash
pip install pre-commit
pre-commit install
```

**Criterio de exito:** CI verde en GitHub, pre-commit activo

---

## BLOQUE 4: Refactoring Final (Score +0.1)
**Prioridad:** MEDIA | **Esfuerzo:** 3-4 hrs

### 4.1 Migrar 6 workers a BaseWorker (~1.5 hrs)

| Worker | Tab | Complejidad |
|--------|-----|-------------|
| ScanWorker | duplicates_tab.py | Baja (progress int,str) |
| OrganizeWorker | organize_tab.py | Baja |
| RenameWorker | rename_tab.py | Baja |
| ChordsAnalyzeWorker | chords_tab.py | Media (progress str) |
| LyricsSearchWorker | lyrics_tab.py | Baja (no progress) |
| ClassificationWorker | content_filter_tab.py | Media (progress int,int,obj) |

### 4.2 Extraer credential loading utility (~30 min)

**Crear:** `src/utils/credentials.py`

```python
def load_api_credentials(service: str) -> Optional[str]:
    """Load API key from keyring > env > .env > None"""
    ...
```

Usar en: `search_tab.py`, `cloud_sync_tab.py`, `api_config_wizard.py`

### 4.3 Consolidar stylesheets (~1 hr)

**Crear:** `src/gui/themes/style_constants.py`

Mover los 37 `setStyleSheet()` inline a constantes con nombre. Ejemplo:
```python
BUTTON_PRIMARY = "background-color: #4CAF50; color: white; ..."
PROGRESS_BAR = "QProgressBar { ... }"
```

### 4.4 Estandarizar tests a pytest (~1 hr)

Convertir los ~10 archivos que usan `unittest.TestCase` a pytest puro:
- `setUp()` → `@pytest.fixture`
- `self.assertEqual()` → `assert`
- `self.assertRaises()` → `pytest.raises()`

**Criterio de exito:** Cero duplicacion en workers, credential loading centralizado

---

## BLOQUE 5: Documentacion (Score +0.15)
**Prioridad:** BAJA | **Esfuerzo:** 1-1.5 hrs

### 5.1 Actualizar docs/ARCHITECTURE.md (~30 min)

Agregar:
- Diagrama de controllers (PlaybackController, LibraryController, UIComposer, RemoteController)
- BaseTab pattern y herencia
- BaseWorker pattern
- Flujo de signals entre capas

### 5.2 Actualizar docs/API_REFERENCE.md (~20 min)

Agregar:
- JWT auth documentation (Bearer header)
- Token refresh endpoint
- CORS policy

### 5.3 Actualizar CHANGELOG.md (~15 min)

Agregar seccion para audit 2026-03-15 con todos los cambios.

### 5.4 DB migration rollback support (~opcional, 2 hrs)

Agregar metodo `down()` al migration system. Bajo ROI — solo si sobra tiempo.

**Criterio de exito:** Docs reflejan estado actual del codigo

---

## ORDEN DE EJECUCION RECOMENDADO

```
Sesion 1 (~8 hrs): BLOQUE 1 completo (tests)
  → Resultado: Coverage >=80%, ~200 tests nuevos

Sesion 2 (~5 hrs): BLOQUE 2 completo (type hints)
  → Resultado: mypy limpio

Sesion 3 (~3 hrs): BLOQUE 3 completo (seguridad + CI)
  → Resultado: CI verde, security hardened

Sesion 4 (~4 hrs): BLOQUE 4 completo (refactoring)
  → Resultado: BaseWorker usado, credentials centralized

Sesion 5 (~1.5 hrs): BLOQUE 5 completo (docs)
  → Resultado: Documentacion actualizada
```

## SCORE PROGRESSION

| Despues de | Score | Delta |
|------------|-------|-------|
| Estado actual | 8.5 | — |
| Bloque 1 (tests) | 9.3 | +0.8 |
| Bloque 2 (types) | 9.6 | +0.3 |
| Bloque 3 (security+CI) | 9.8 | +0.2 |
| Bloque 4 (refactoring) | 9.9 | +0.1 |
| Bloque 5 (docs) | 10.0 | +0.1 |

---

## VALIDACION FINAL (checklist 10/10)

- [ ] pytest --cov >= 80%
- [ ] mypy src/ — 0 errors
- [ ] bandit -r src/ -ll — 0 issues
- [ ] flake8 src/ — 0 errors
- [ ] CI/CD verde en GitHub
- [ ] Pre-commit hooks activos
- [ ] 0 except Exception sin justificar
- [ ] 0 SQL injection posible
- [ ] 0 archivos huerfanos
- [ ] 14/14 tabs en BaseTab
- [ ] 6/6 workers en BaseWorker
- [ ] Credentials centralizados
- [ ] Stylesheets consolidados
- [ ] Docs actualizados
- [ ] CHANGELOG al dia
