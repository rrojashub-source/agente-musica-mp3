@echo off
REM ============================================
REM  NEXUS MUSIC MANAGER - LAUNCH SCRIPT
REM ============================================
REM  Project: AGENTE_MUSICA_MP3_001
REM  Version: 2.0 (Production)
REM  All Phases Complete (1-7)
REM ============================================

echo.
echo ============================================
echo  NEXUS MUSIC MANAGER v2.0
echo ============================================
echo  All Phases Complete (1-7)
echo ============================================
echo.

REM Check if virtual environment exists
if not exist "spike_pyqt6\venv\Scripts\python.exe" (
    echo [!] Virtual environment not found!
    echo [*] Creating virtual environment...
    python -m venv spike_pyqt6\venv

    if errorlevel 1 (
        echo.
        echo [X] Failed to create virtual environment
        echo [*] Make sure Python 3.11+ is installed
        pause
        exit /b 1
    )

    echo [*] Installing dependencies...
    spike_pyqt6\venv\Scripts\pip install -r requirements.txt

    if errorlevel 1 (
        echo.
        echo [X] Failed to install dependencies
        echo [*] Please check requirements.txt
        pause
        exit /b 1
    )

    echo.
    echo [*] Dependencies installed successfully!
    echo.
)

echo [*] Launching NEXUS Music Manager...
echo.

REM Launch the app (src/main.py is the entry point)
spike_pyqt6\venv\Scripts\python.exe src\main.py

if errorlevel 1 (
    echo.
    echo ============================================
    echo  ERROR: Application failed to start
    echo ============================================
    echo.
    echo Possible causes:
    echo  1. Missing dependencies - Delete spike_pyqt6\venv and run again
    echo  2. PyQt6 not installed - Check requirements.txt
    echo  3. Database issues - Check database\music_library.db
    echo  4. Python version - Need Python 3.11 or higher
    echo.
    echo Check the error message above for details.
    echo.
    pause
    exit /b 1
)

exit /b 0
