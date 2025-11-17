@echo off
REM ============================================
REM  NEXUS MUSIC MANAGER - COMPLETE EDITION
REM ============================================
REM  Project: AGENTE_MUSICA_MP3_001
REM  Version: Complete (Phases 3+4+5+6)
REM
REM  Features Available:
REM  - Library Management (10,000+ songs)
REM  - Search and Download (YouTube + Spotify)
REM  - Duplicate Detection
REM  - Auto-Organize Folders
REM  - Batch Rename
REM  - Music Player with Lyrics
REM  - Multi-language (Spanish/English)
REM
REM ============================================

echo.
echo ============================================
echo  NEXUS MUSIC MANAGER - COMPLETE EDITION
echo ============================================
echo.

REM Check if virtual environment exists
if not exist "spike_pyqt6\venv\Scripts\python.exe" (
    echo [!] Virtual environment not found!
    echo [*] Creating virtual environment...
    python -m venv spike_pyqt6\venv

    echo [*] Installing dependencies...
    spike_pyqt6\venv\Scripts\pip install -r requirements.txt

    if errorlevel 1 (
        echo.
        echo [X] Failed to install dependencies
        echo [*] Please run manually:
        echo     spike_pyqt6\venv\Scripts\pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo [*] Activating virtual environment...
echo [*] Launching NEXUS Music Manager...
echo.

REM Activate virtual environment and run
spike_pyqt6\venv\Scripts\python.exe main_window_complete.py

if errorlevel 1 (
    echo.
    echo ============================================
    echo  ERROR: Application failed to start
    echo ============================================
    echo.
    echo Possible causes:
    echo  1. Missing dependencies - Run: pip install -r requirements.txt
    echo  2. PyQt6 not installed - Run: pip install PyQt6
    echo  3. Database issues - Check phase2_database folder
    echo.
    pause
    exit /b 1
)

exit /b 0
