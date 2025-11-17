@echo off
REM ============================================================
REM NEXUS Music Manager Launcher - UTF-8 Support
REM Project: AGENTE_MUSICA_MP3_001
REM ============================================================

echo.
echo ========================================
echo  NEXUS Music Manager
echo  Launching with UTF-8 support...
echo ========================================
echo.

REM Configure Python to use UTF-8
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Launch application
python main_window_complete.py

REM Keep window open if error
if errorlevel 1 (
    echo.
    echo ========================================
    echo  ERROR: Application failed to start
    echo ========================================
    echo.
    pause
)
