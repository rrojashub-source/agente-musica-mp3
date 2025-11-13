@echo off
REM ============================================================
REM  NEXUS MUSIC MANAGER - Complete Edition (Phases 1-7)
REM ============================================================
REM  Project: AGENTE_MUSICA_MP3_001
REM  Version: 2.0 Production
REM
REM  Features:
REM  Phase 1-3: Library Management (10,000+ songs, FTS5 search)
REM  Phase 4: Search & Download (YouTube + Spotify dual-source)
REM  Phase 5: Management Tools (duplicates, organize, rename)
REM  Phase 6: Audio Player (pygame.mixer, playback controls)
REM  Phase 7: Playlists (.m3u8) + Audio Visualizer (60 FPS)
REM
REM ============================================================

echo.
echo ============================================================
echo  NEXUS MUSIC MANAGER - Complete Edition
echo  Version 2.0 (Production)
echo ============================================================
echo.
echo Loading all features (Phases 1-7)...
echo.

REM Configure UTF-8 encoding
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Launch application from src/main.py
cd /d "%~dp0"
python src\main.py

REM Handle errors
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  ERROR: Application failed to start
    echo ============================================================
    echo.
    echo Possible causes:
    echo  1. Missing dependencies
    echo     Fix: pip install PyQt6 pygame mutagen
    echo.
    echo  2. Database not initialized
    echo     Fix: Check database migrations in src/database/migrations/
    echo.
    echo  3. Python not in PATH
    echo     Fix: Install Python 3.11+ and add to PATH
    echo.
    echo  4. Module import errors
    echo     Fix: Ensure all src/ modules are present
    echo.
    pause
    exit /b 1
)

exit /b 0
