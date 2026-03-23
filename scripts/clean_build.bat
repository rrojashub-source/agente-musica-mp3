@echo off
REM ============================================
REM Clean Build — Delete ALL caches + rebuild
REM Use during testing to avoid stale .pyc
REM ============================================
setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set VENV=%PROJECT_ROOT%\venv
set PYTHON=%VENV%\Scripts\python.exe

echo.
echo =============================================
echo   CLEAN BUILD - Removing all caches
echo =============================================
echo.

cd /d "%PROJECT_ROOT%"

REM 1. Delete build artifacts
if exist build (
    echo [CLEAN] Removing build/
    rmdir /s /q build
)
if exist dist (
    echo [CLEAN] Removing dist/
    rmdir /s /q dist
)

REM 2. Delete ALL __pycache__ in src/
echo [CLEAN] Removing __pycache__ from src/
for /d /r src %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d"
    )
)

REM 3. Delete .pyc files directly
echo [CLEAN] Removing stale .pyc files
del /s /q src\*.pyc 2>nul

echo.
echo [BUILD] Starting PyInstaller...
echo.

"%PYTHON%" -m PyInstaller --clean --noconfirm nexus_music.spec

set BUILD_RESULT=%ERRORLEVEL%

echo.
if %BUILD_RESULT% EQU 0 (
    for %%A in ("%PROJECT_ROOT%\dist\NEXUS_Music_Manager\NEXUS_Music_Manager.exe") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo =============================================
    echo   BUILD OK - !SIZE_MB! MB
    echo   dist\NEXUS_Music_Manager\NEXUS_Music_Manager.exe
    echo =============================================
) else (
    echo =============================================
    echo   BUILD FAILED - check output above
    echo =============================================
)

endlocal
