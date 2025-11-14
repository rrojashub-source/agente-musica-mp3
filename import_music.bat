@echo off
REM Quick Import Script for Windows
REM Imports MP3s from C:\Users\ricar\Music\ into database

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d "%~dp0"

echo.
echo ========================================
echo   NEXUS Music Library Import
echo ========================================
echo.

python scripts/import_library.py

echo.
echo Press any key to close...
pause >nul
