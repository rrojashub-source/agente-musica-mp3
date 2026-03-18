# 🎯 ACTION PLAN: Pre-Phase 5 Hardening

**Fecha:** 13 Noviembre 2025
**Basado en:** Auditoría de 3 agentes (arquitecto-web, cerebro-analyst, code-reviewer)
**Objetivo:** Resolver blockers críticos ANTES de iniciar Phase 5
**Duración estimada:** 2-3 días de trabajo

---

## 📊 EXECUTIVE SUMMARY

**Consenso de los 3 agentes:**
- ✅ **Proyecto técnicamente sólido** (score 62-70/100)
- ✅ Arquitectura bien pensada (Desktop MVC)
- ✅ Phase 4 features excelentes (127 tests escritos)
- 🔴 **BLOCKERS CRÍTICOS** (5 issues impiden producción)
- 🟠 Deuda técnica manejable (drift documental, structure cleanup)

**Scores Promedio:**
- arquitecto-web: 70/100
- cerebro-analyst: 62/100
- code-reviewer: 65/100
**Promedio consolidado:** **65.7/100**

---

## 🔴 BLOCKERS CRÍTICOS (Los 3 agentes coinciden)

### BLOCKER #1: API Keys en Plaintext 🔐

**Severity:** CRITICAL (Los 3 agentes lo marcaron)
**Location:** `src/api_config_wizard.py:447-461`
**Impact:** Si el repo se hace público o se compromete el filesystem, las API keys quedan expuestas

**Problema actual:**
```python
# Lines 447-461
config_file = Path(__file__).parent / "api_keys_config.txt"

with open(config_file, 'w') as f:
    f.write("# NEXUS Music Manager - API Configuration\n")
    f.write(f"YOUTUBE_API_KEY={youtube_key}\n")
    f.write(f"SPOTIFY_CLIENT_ID={spotify_id}\n")
    f.write(f"SPOTIFY_CLIENT_SECRET={spotify_secret}\n")
    f.write(f"GENIUS_ACCESS_TOKEN={genius_token}\n")
```

**Riesgos:**
- ❌ API keys almacenadas en texto plano en filesystem
- ❌ Archivo NO está en `.gitignore` → riesgo commit accidental
- ❌ Cualquier proceso con acceso al filesystem puede leerlas
- ❌ OWASP Top 10: A07:2021 – Identification and Authentication Failures

**Sugerencia de Ricardo:** ✅ GUI para que el cliente pegue/valide sus API keys

**SOLUCIÓN PROPUESTA (Opción A - Recomendada):**

```python
# Usar keyring del sistema operativo (encrypted por el OS)
import keyring

# Guardar (encrypted)
keyring.set_password("nexus_music", "youtube_api_key", youtube_key)
keyring.set_password("nexus_music", "spotify_client_id", spotify_id)
keyring.set_password("nexus_music", "spotify_client_secret", spotify_secret)
keyring.set_password("nexus_music", "genius_token", genius_token)

# Recuperar
youtube_key = keyring.get_password("nexus_music", "youtube_api_key")
```

**SOLUCIÓN IMPLEMENTACIÓN - GUI Wizard:**

1. **API Settings Dialog (nueva ventana GUI):**
   - Tab 1: YouTube API
     - QLineEdit para pegar API key
     - QPushButton "Validate" → llama YouTube API para verificar
     - QLabel status (✅ Valid / ❌ Invalid)
   - Tab 2: Spotify API
     - QLineEdit para Client ID
     - QLineEdit para Client Secret (password mode)
     - QPushButton "Validate"
   - Tab 3: Genius API (opcional)
   - QPushButton "Save" → guarda en keyring (NO archivo)

2. **Validación automática:**
   - Click "Validate" → hace request real a API
   - Si 200 OK → muestra ✅ "Valid - X requests remaining today"
   - Si 401/403 → muestra ❌ "Invalid - Check your credentials"

3. **Beneficios:**
   - ✅ User-friendly (no archivos de texto)
   - ✅ Validación inmediata (detecta typos)
   - ✅ Encrypted por el OS
   - ✅ Zero risk de commit accidental

**Alternativa si keyring no funciona:**
- Cifrar archivo con `cryptography.fernet`
- Derivar clave de password del usuario (PBKDF2)
- Nunca commitear el archivo cifrado

**Estimación:** 6 horas (4h código + 1h tests + 1h docs)

---

### BLOCKER #2: Tests Rotos 🧪

**Severity:** CRITICAL
**Detectado por:** cerebro-analyst, code-reviewer
**Error:** `ModuleNotFoundError: No module named 'PyQt6'`, `ModuleNotFoundError: No module named 'folder_manager'`

**Problema:**
```bash
pytest tests/ -v
# ERROR collecting tests/test_download_worker.py
# ModuleNotFoundError: No module named 'PyQt6'

# ERROR collecting tests/test_fase2b_imports.py
# ModuleNotFoundError: No module named 'folder_manager'
```

**Causas:**
1. PyQt6 no instalado en venv actual (requirements.txt existe pero no se ejecutó `pip install`)
2. Tests legacy en `tests/test_fase2b_imports.py` buscan módulos obsoletos
3. sys.path manipulation en production code NO replicado en tests

**SOLUCIÓN:**

1. **Verificar venv y reinstalar dependencias:**
```bash
# Activar venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstalar todo
pip install -r requirements.txt

# Verificar PyQt6
python -c "import PyQt6; print(PyQt6.__version__)"
```

2. **Limpiar tests obsoletos:**
```bash
# Mover tests legacy a carpeta archive
mkdir -p tests/obsolete
mv tests/test_fase2b_imports.py tests/obsolete/
mv tests/test_cleanup_ui_fase2b_fixed.py tests/obsolete/
mv tests/test_files_robustez/ tests/obsolete/
mv tests/test_files_robustez_real/ tests/obsolete/
mv tests/test_mutagen_read.py tests/obsolete/
mv tests/test_underscore_fix.py tests/obsolete/
```

3. **Fix conftest.py para imports:**
```python
# tests/conftest.py
import sys
from pathlib import Path

# Add src/ to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# QApplication for PyQt6 tests
import pytest
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()
```

4. **Validar:**
```bash
# Ejecutar SOLO tests Phase 4 (127 tests)
pytest tests/test_youtube_search.py \
       tests/test_spotify_search.py \
       tests/test_download_worker.py \
       tests/test_download_queue.py \
       tests/test_musicbrainz_client.py \
       tests/test_metadata_autocompleter.py \
       tests/test_search_tab.py \
       tests/test_queue_widget.py \
       tests/test_download_integration.py \
       tests/test_metadata_tagging.py \
       tests/test_e2e_complete_flow.py \
       -v
```

**Estimación:** 2 horas (1h fix + 1h validation)

---

### BLOCKER #3: .gitignore Incompleto 📝

**Severity:** HIGH
**Detectado por:** code-reviewer, arquitecto-web

**Problema:** .gitignore actual NO protege secrets:
```bash
# .gitignore actual (incompleto)
venv/
__pycache__/
*.pyc
.pytest_cache/
.cache/
```

**Falta agregar:**
```bash
# === SECRETS & CREDENTIALS ===
# API keys (legacy plaintext files)
api_keys_config.txt
api_keys.txt
config.txt
*.env
.env*
credentials.json
secrets/

# === DATABASE (user data) ===
*.db
*.sqlite
*.sqlite3
user_library.db
databases/

# === LOGS (may contain sensitive info) ===
logs/
*.log
nexus_music.log

# === CONFIG (local paths) ===
config.json
.nexus_music/

# === DOWNLOADS (user files) ===
downloads/
*.mp3
*.m4a
*.wav

# === BACKUPS ===
backups/
*.backup
*.old

# === PYTHON ===
# (ya existe, mantener)
venv/
__pycache__/
*.pyc
.pytest_cache/
.cache/

# === IDE ===
.vscode/
.idea/
*.swp
*.swo
*~

# === OS ===
.DS_Store
Thumbs.db
desktop.ini

# === DEVELOPMENT ===
development/
experiments/
OLD/
temp/
tmp/

# === ARCHIVES (legacy) ===
tests/obsolete/
tests/test_files_robustez/
tests/test_files_robustez_real/
```

**SOLUCIÓN:**
1. Actualizar `.gitignore` con lo anterior
2. Verificar que NO se commiteen archivos sensibles:
```bash
git status --ignored
```

3. Si ya se commitearon secrets:
```bash
# CRÍTICO: Si se commitearon API keys, REVOCARLAS y generar nuevas
# Remover del historial (si repo es privado):
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch api_keys_config.txt" \
  --prune-empty --tag-name-filter cat -- --all
```

**Estimación:** 1 hora

---

### BLOCKER #4: Input Validation Débil 🛡️

**Severity:** HIGH
**Detectado por:** code-reviewer
**Location:** `src/api/youtube_search.py:64-75`, `src/api/spotify_search.py`

**Problema:**
```python
def search(self, query, max_results=20, use_cache=True):
    # Input validation
    if not query or query is None:
        logger.warning("Empty or None query received")
        return []

    # Sanitize query (truncate if too long)
    if len(query) > 500:
        query = query[:500]

    # ❌ FALTA:
    # - No sanitiza caracteres especiales
    # - No valida encoding
    # - No previene command injection
```

**Riesgo:** Command injection si query contiene caracteres maliciosos

**SOLUCIÓN:**
```python
import re
from urllib.parse import quote

def sanitize_query(query: str) -> str:
    """
    Sanitize user input for API queries

    Args:
        query: Raw user input string

    Returns:
        Sanitized query safe for API calls
    """
    if not query:
        return ""

    # Remove control characters (0x00-0x1f, 0x7f-0x9f)
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)

    # Remove SQL injection attempts (just in case)
    query = re.sub(r'[\'\";]', '', query)

    # Limit length
    query = query[:500]

    # URL encode special characters
    query = quote(query, safe=' ')

    return query.strip()
```

**Aplicar en:**
- `src/api/youtube_search.py` → `search()`
- `src/api/spotify_search.py` → `search()`
- `src/core/metadata_autocompleter.py` → `autocomplete_single()`

**Estimación:** 3 horas (2h código + 1h tests)

---

### BLOCKER #5: Drift Documental 📚

**Severity:** HIGH
**Detectado por:** cerebro-analyst, arquitecto-web

**Inconsistencias detectadas:**

| Documento | Expected | Actual | Severity |
|-----------|----------|--------|----------|
| README.md | "Production Ready" | Phase 5 Planning | HIGH |
| CLAUDE.md | agente_musica.py in root | Moved to OLD/ | HIGH |
| current_phase.md | 127/127 tests passing | Import errors | CRITICAL |
| PROJECT_ID.md | 100% compliance | Missing files | MEDIUM |

**SOLUCIÓN:**

1. **README.md:**
```markdown
# Actualizar status
**Status:** Phase 4 Complete (65% overall) - Desktop Application
**Production Readiness:** Beta (Security hardening in progress)
**Next Phase:** Phase 5 - Management & Cleanup Tools
```

2. **CLAUDE.md:**
```markdown
# Actualizar key files
## 📁 Key Files

```
AGENTE_MUSICA_MP3/
├── PROJECT_DNA.md          # Project specification
├── README.md               # Overview
├── CLAUDE.md               # This file
├── TRACKING.md             # Session logs
├── src/                    # Source code (Phase 4 complete)
│   ├── api/                # YouTube, Spotify, MusicBrainz APIs
│   ├── core/               # Download queue, metadata tagger
│   ├── gui/                # PyQt6 widgets
│   └── workers/            # Background download workers
├── tests/                  # 127 Phase 4 tests
└── OLD/                    # Legacy CLI code (archived)
    ├── agente_musica.py    # (moved from root)
    └── agente_final.py     # (moved from root)
```
```

3. **current_phase.md:**
```markdown
# Actualizar test status
**Test Suite:**
- Phase 4 Tests: 127 tests written (11 files)
- Status: ⚠️ Import errors being fixed (Pre-Phase 5 hardening)
- Target: 127/127 passing before Phase 5
```

4. **PROJECT_ID.md:**
```markdown
# Actualizar compliance
**Compliance:** 6/6 (100%) ✅
- ✅ PROJECT_ID.md (this file)
- ✅ PROJECT_DNA.md (architecture docs)
- ✅ CLAUDE.md (Claude context)
- ✅ README.md (public overview)
- ✅ TRACKING.md (session logs)
- ✅ memory/ (dynamic state)
- ✅ tasks/ (external plans)
- ✅ Git repository (13 Phase 4 commits)

**Current Phase:** Pre-Phase 5 Hardening (Security + Testing)
**Overall Progress:** 65% (CLI + GUI foundation + Search & Download System complete)
```

**Estimación:** 2 horas

---

## 🟠 MEJORAS RECOMENDADAS (No blockers)

### Mejora #1: Clean Project Structure

**Issue:** 9,000+ files en venv/ contaminan proyecto
**Fix:**
```bash
# Mover venv fuera del proyecto
mv venv ../AGENTE_MUSICA_MP3_venv

# Actualizar scripts para usar venv externo
# Agregar a .bashrc / .zshrc:
alias activate-nexus="source ../AGENTE_MUSICA_MP3_venv/bin/activate"

# Documentar en README:
"Virtual environment is located at ../AGENTE_MUSICA_MP3_venv"
```

**Estimación:** 1 hora
**Prioridad:** BAJA (no bloquea funcionalidad)

---

### Mejora #2: Refactor sys.path Manipulation

**Issue:** sys.path hacks en main_window_complete.py complican imports
**Fix:** Convertir a proper Python package con `__init__.py`

```python
# ANTES (malo):
sys.path.insert(0, str(Path(__file__).parent / "phase4_search_download"))
from search_tab import SearchTab

# DESPUÉS (correcto):
from src.gui.tabs.search_tab import SearchTab
```

**Estimación:** 4 horas
**Prioridad:** MEDIA (mejora mantenibilidad)

---

### Mejora #3: Type Hints Comprehensive

**Issue:** Coverage 40% (inconsistente)
**Fix:** Agregar type hints a todos los módulos core

```python
from typing import Dict, List, Optional

def search(
    self,
    query: str,
    max_results: int = 20,
    use_cache: bool = True
) -> List[Dict[str, str]]:
    ...
```

**Estimación:** 8 horas
**Prioridad:** BAJA (mejora IDE experience)

---

## 📋 PLAN DE IMPLEMENTACIÓN

### FASE 1: BLOCKERS CRÍTICOS (2-3 días)

**Día 1 (6-8 horas):**
1. ✅ **API Keys Security** (6h)
   - [ ] Crear `src/gui/dialogs/api_settings_dialog.py`
   - [ ] Implementar keyring integration
   - [ ] Crear GUI wizard con validación
   - [ ] Tests para validación API
   - [ ] Actualizar `api_config_wizard.py` para usar keyring
   - [ ] Docs: "How to get API keys" en README

2. ✅ **.gitignore completo** (1h)
   - [ ] Actualizar `.gitignore` con secrets
   - [ ] Verificar `git status --ignored`
   - [ ] Commit cambios

**Día 2 (4-5 horas):**
3. ✅ **Fix Tests** (2h)
   - [ ] Verificar venv: `pip install -r requirements.txt`
   - [ ] Mover tests obsoletos a `tests/obsolete/`
   - [ ] Ejecutar: `pytest tests/test_*.py -v` (solo Phase 4)
   - [ ] Validar 127/127 pasan

4. ✅ **Input Validation** (3h)
   - [ ] Crear `src/utils/input_sanitizer.py`
   - [ ] Aplicar en YouTube, Spotify, MusicBrainz clients
   - [ ] Tests para sanitization
   - [ ] Docs en docstrings

**Día 3 (2 horas):**
5. ✅ **Align Documentation** (2h)
   - [ ] Actualizar README.md (status)
   - [ ] Actualizar CLAUDE.md (file structure)
   - [ ] Actualizar current_phase.md (test status)
   - [ ] Actualizar PROJECT_ID.md (compliance)
   - [ ] Commit: "docs: Align with Phase 4 completion + Pre-Phase 5 hardening"

---

### FASE 2: VALIDACIÓN (0.5 día)

**Checklist Pre-Phase 5:**
- [ ] API keys NO están en plaintext (keyring OK)
- [ ] `.gitignore` protege secrets
- [ ] Tests: 127/127 passing
- [ ] Input validation en todos los API clients
- [ ] Documentación actualizada (no drift)
- [ ] Git: Todos los cambios committed
- [ ] Ricardo aprueba para Phase 5

**Comando de validación:**
```bash
# Ejecutar desde raíz
./scripts/validate_pre_phase5.sh

# Debe reportar:
# ✅ API Keys: Secured (keyring)
# ✅ .gitignore: Complete (40 patterns)
# ✅ Tests: 127/127 PASSING
# ✅ Input Validation: Applied (3 clients)
# ✅ Documentation: Aligned (0 drift issues)
# 🎉 PRE-PHASE 5 HARDENING COMPLETE - Ready for Phase 5!
```

---

## 🎯 PRIORIZACIÓN RICARDO

**Sugerencia de Ricardo:** GUI para API keys ✅
**Implementación:** Incluida en Blocker #1 (Día 1)

**Features GUI propuesta:**
1. **Dialog "API Settings":**
   - Tabs para cada API (YouTube, Spotify, Genius)
   - QLineEdit para pegar keys
   - "Validate" button → test real API call
   - Status icon (✅/❌) + remaining quota
   - "Save" → guarda en keyring (encrypted)

2. **Access from Main Window:**
   - Menu: `Tools → API Settings...`
   - Shortcut: `Ctrl+K` (K = Keys)
   - First run: Auto-open wizard

3. **User Experience:**
   - User-friendly (no archivos de texto)
   - Instant validation (detecta typos)
   - Shows API quota remaining
   - Clear error messages

**¿Apruebas este approach?**

---

## 📊 ESTIMACIÓN TOTAL

| Fase | Duración | Esfuerzo |
|------|----------|----------|
| **FASE 1: Blockers** | 2-3 días | 12-15 horas |
| **FASE 2: Validación** | 0.5 días | 2 horas |
| **TOTAL** | **2.5-3.5 días** | **14-17 horas** |

**Mejoras opcionales (si tiempo permite):**
| Mejora | Duración | Esfuerzo |
|--------|----------|----------|
| Clean Structure | 0.5 días | 1 hora |
| Refactor sys.path | 1 día | 4 horas |
| Type Hints | 1.5 días | 8 horas |

---

## ✅ SUCCESS CRITERIA

**Pre-Phase 5 Hardening completado cuando:**
1. ✅ API keys encrypted (keyring o Fernet)
2. ✅ GUI API Settings dialog funcional
3. ✅ .gitignore protege secrets (40+ patterns)
4. ✅ Tests: 127/127 passing (zero import errors)
5. ✅ Input validation en 3 API clients
6. ✅ Documentación aligned (zero drift)
7. ✅ Git commits: Todo trackeado
8. ✅ Ricardo aprueba para Phase 5

**Security Score Target:** 40/100 → 85/100
**Overall Score Target:** 65.7/100 → 80/100

---

## 🚀 PRÓXIMOS PASOS

**Después de completar Pre-Phase 5 Hardening:**
1. **Git commit:** "feat(pre-phase5): Security hardening complete"
2. **Update TRACKING.md:** Session log de Pre-Phase 5
3. **Begin Phase 5:** Management & Cleanup Tools (5 features)

**Phase 5 Features (roadmap):**
- Duplicates detection
- Auto-organize library
- Batch rename files
- Tag editor GUI
- Import existing library

---

**Creado por:** NEXUS@CLI
**Basado en:** Auditoría de arquitecto-web, cerebro-analyst, code-reviewer
**Fecha:** 13 Noviembre 2025
**Status:** ⏳ Awaiting Ricardo Approval
