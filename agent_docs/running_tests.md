# Running Tests

## Quick Commands

```bash
pytest tests/ -v                     # All tests (verbose)
pytest tests/ -x -q --tb=short      # Stop on first failure
pytest tests/test_specific.py        # Single file
pytest tests/ -k "test_name"         # By name pattern
pytest tests/ --cov=src --cov-report=html  # With coverage
```

## Configuration

**pytest.ini**: coverage >= 20% (threshold will increase), markers: network, slow, gui, integration.

## Test Structure (52+ files, 980+ tests)

```
tests/
├── conftest.py                  # Shared fixtures + PySide6 mock management
├── _mock_pyside6.py             # PySide6 mock for headless testing
├── test_*_phase2.py             # Phase-2 GUI tests (mock PySide6 at module level)
├── test_api_*.py                # API client tests (mocked HTTP)
├── test_core_*.py               # Core engine tests
├── test_database_*.py           # SQLite tests (real temp DB)
├── test_e2e_*.py                # End-to-end (skipped without GUI)
└── test_*.py                    # Module-specific tests
```

## Key Fixtures (conftest.py)

- `temp_db` — Temporary SQLite database with WAL/SHM cleanup
- `temp_music_folder` — Temp directory with fake MP3 files
- `mock_db_manager` — Pre-configured Mock of DatabaseManager
- `qapp` — QApplication instance (only if real PySide6 available)
- `restore_pyside6_mocks()` — Restores PySide6 mock modules after phase-2 tests

## PySide6 Mock System

Tests run headless using `_mock_pyside6.py` which replaces PySide6 with MagicMock-based stubs. Phase-2 GUI tests further modify these mocks at module level (replacing QWidget, QVBoxLayout, etc. with custom mocks).

**Critical:** Phase-2 test files contaminate PySide6 mock modules. `conftest.py` has a snapshot/restore mechanism (`_PYSIDE6_SNAPSHOT`, `pytest_collectstart`, `pytest_runtest_setup`) to isolate this contamination.

**Phase-2 files that modify mocks:** test_gui_base_phase2, test_gui_dialogs_phase2, test_gui_tabs_phase2, test_gui_visualizers_phase2, test_gui_widgets_phase2.

## Known Test Behaviors

- **YouTube API tests** — May fail due to quota limits (pre-existing, not a bug)
- **GUI tests** — Skipped without real PySide6 (CI uses xvfb)
- **Integration tests** — Skipped by default (require network + API keys)
- **fpcalc tests** — Skip if Chromaprint not installed
- **Coverage** — Current threshold 20%, actual varies by module (80-100% for audited modules)
