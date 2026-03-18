# NEXUS Music Manager

**Version:** 2.1.0 | **Status:** Maintenance (audit complete) | **Protocol:** NEXUS Dev Protocol v1.0

---

## Resumen

Gestor de biblioteca musical profesional con GUI PySide6. Descarga YouTube, busqueda Spotify, metadata automatica MusicBrainz, reproductor con visualizadores OpenGL, IA para similitud (embeddings 128D), plugins, control remoto movil, sync cloud, multi-idioma ES/EN.

## Documentos Clave

- `docs/PRD.md` — Requisitos, alcance, non-goals
- `docs/PROGRESS.md` — Estado actual y proximos pasos
- `tasks/lessons.md` — Anti-patrones a evitar (LEER antes de codificar)
- `PROJECT_STATE.json` — Estado dinamico, scores, decisiones
- `agent_docs/` — Detalles de build, tests, arquitectura (Progressive Disclosure)

## Scope Control

- Nunca implementar features no listadas en docs/PRD.md sin preguntar primero.
- Si una tarea cruza mas de una fase, parar y pedir guia.
- Antes de agregar dependencias externas, explicar por que y esperar aprobacion.

## Auditoria MAPS

Antes de cualquier sesion de auditoria:
1. Leer `docs/audit/progress-tracker.md` — estado por modulo
2. Leer `docs/audit/known-issues-resolved.md` — NUNCA re-reportar estos
3. Leer `docs/audit/approved-modules.md` — NO re-auditar sin pedirlo

**Status:** 15/15 modulos aprobados, 4/4 fases completadas (63 rounds).

## Calidad

| Herramienta | Estado | Config |
|-------------|--------|--------|
| mypy | 0 errores (111 archivos) | mypy.ini strict |
| pytest | 980+ tests pass | pytest.ini, coverage >= 20% |
| flake8 | Limpio | max-line-length=120 |
| bandit | Limpio | -ll |
| pre-commit | Activo | black, isort, flake8 |

## Reglas

- Commits atomicos: un cambio logico por commit
- Type hints requeridos en todos los archivos (mypy strict)
- API keys en OS keyring (no en codigo), via `utils/credentials.py`
- numpy FFT (no librosa) para audio analysis
- DB principal: `music_library.db` (SQLite + FTS5 + WAL)
- Paths en DB pueden necesitar update si cambia ubicacion de MP3s

## Ejecutar

```bash
python src/main.py                          # Dev
pytest tests/ -v                            # Tests
mypy src/ --ignore-missing-imports          # Types
bandit -r src/ -ll                          # Security
```

Ver `agent_docs/building_the_project.md` para build, deps, empaquetado.
Ver `agent_docs/running_tests.md` para fixtures, mocks PySide6, coverage.
Ver `agent_docs/service_architecture.md` para estructura, seguridad, patrones.

## Git

- Remote: `origin` -> github.com/rrojashub-source/agente-musica-mp3.git
- Branch: `main`

## Al compactar, preservar

Lista de archivos modificados, comandos de test, decisiones tomadas, estado de tareas pendientes.
