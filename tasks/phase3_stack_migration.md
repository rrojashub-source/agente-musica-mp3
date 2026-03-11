# Phase 3: Stack Migration Plan

**Created:** 2026-03-11
**Status:** In Progress
**Estimated:** 3 sessions (1 per sub-phase)

## Phase 3.1: PyQt6 → PySide6

**Scope:** 61 files (50 src, 11 tests), 162 signal definitions
**Risk:** LOW (mostly mechanical search/replace)

### Steps:
1. Update requirements.txt: `PyQt6>=6.5.0` → `PySide6>=6.5.0`
2. Update requirements-dev.txt: `pytest-qt` stays (supports both)
3. Global replace in all .py files:
   - `from PyQt6.` → `from PySide6.`
   - `import PyQt6` → `import PySide6`
   - `pyqtSignal` → `Signal` (in imports AND definitions)
   - `pyqtSlot` → `Slot` (1 occurrence: queue_widget.py)
   - `pyqtProperty` → `Property` (1 occurrence: skeleton_widget.py)
4. OpenGL special case: `PyQt6.QtOpenGLWidgets` → `PySide6.QtOpenGLWidgets`
5. Fix 2 direct pygame volume calls in playback_controller.py (use AudioPlayer API)
6. Run tests, fix any enum or API differences
7. Verify plugins reference PySide6

### Known Differences:
- `Qt.AlignCenter` works in both (alias)
- `exec()` already used (no `exec_()`)
- No sip, QVariant, .ui files
- `QAction` location: PyQt6.QtGui → same in PySide6

## Phase 3.2: pygame → python-mpv

**Scope:** 2 core files + 2 test files
**Risk:** MEDIUM (different API semantics, requires libmpv binary)
**Dependency:** libmpv.dll (Windows) or libmpv.so (Linux)

### Steps:
1. Install python-mpv: `pip install python-mpv`
2. Obtain libmpv binary for Windows (from mpv.io builds)
3. Rewrite AudioPlayer class internals:
   - `pygame.mixer.init()` → `mpv.MPV()`
   - `.load()/.play()` → `player.play(path)`
   - `.pause()/.unpause()` → `player.pause = True/False`
   - `.seek(pos)` → `player.seek(pos, reference="absolute")`
   - `.get_pos()` → `player.time_pos`
   - `.get_busy()` → Check `player.core_idle`
   - `.set_volume()` → `player.volume` (0-100 scale, not 0.0-1.0)
   - Track end: mpv event system instead of polling
4. Preserve 26-method public API (no consumer changes)
5. Update gapless: use mpv playlist instead of queue()
6. Update tests with mpv mocks
7. Remove pygame from requirements.txt

### Benefits:
- Native gapless playback (no polling hack)
- All audio formats (FLAC, OPUS, AAC, etc.)
- Hardware-accelerated decoding
- Built-in equalizer support

## Phase 3.3: PyInstaller → Nuitka + UPX

**Scope:** Build config + 5 resource path files
**Risk:** MEDIUM (new build toolchain)
**Dependency:** Phases 3.1 + 3.2 complete

### Steps:
1. Install Nuitka: `pip install nuitka`
2. Create build script with Nuitka flags
3. Update 5 files: `sys._MEIPASS` → `__compiled__` detection
4. Configure data file inclusion (themes, shaders, migrations, plugins)
5. Test build, verify all features
6. Apply UPX post-compression
7. Update CI/CD workflow
8. Remove PyInstaller from requirements-dev.txt

### Target:
- 164MB → ~90MB exe size
- Faster startup (compiled C vs bytecode extraction)

## Decision Log:
- PySide6 first: mechanical, enables Nuitka compatibility
- python-mpv second: isolated to AudioPlayer, biggest user-facing improvement
- Nuitka last: depends on both above being stable
