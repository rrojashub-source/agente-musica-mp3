@echo off
REM ============================================
REM NEXUS Music Manager — Full Installer Build
REM Step 1: PyInstaller (folder mode)
REM Step 2: Inno Setup (installer .exe)
REM ============================================
setlocal enabledelayedexpansion

echo.
echo =============================================
echo   NEXUS Music Manager - Installer Build
echo =============================================
echo.

set PROJECT_ROOT=%~dp0..
set VENV=%PROJECT_ROOT%\venv
set PYTHON=%VENV%\Scripts\python.exe
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
set LOG=%PROJECT_ROOT%\build.log

if not exist "%PYTHON%" (
    echo [ERROR] Python venv not found
    exit /b 1
)
if not exist %ISCC% (
    echo [ERROR] Inno Setup 6 not found at %ISCC%
    exit /b 1
)

echo Build started: %date% %time% > "%LOG%"

REM === Step 1: PyInstaller (folder mode) ===
echo.
echo [1/2] PyInstaller - building application folder...
cd /d "%PROJECT_ROOT%"
"%PYTHON%" -m PyInstaller --clean --noconfirm nexus_music.spec >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller failed! Check build.log
    exit /b 1
)
echo   OK - dist\NEXUS_Music_Manager\ created

REM Verify the folder exists
if not exist "%PROJECT_ROOT%\dist\NEXUS_Music_Manager\NEXUS_Music_Manager.exe" (
    echo [ERROR] PyInstaller output not found
    exit /b 1
)

REM === Step 2: Inno Setup (installer) ===
echo.
echo [2/2] Inno Setup - creating installer...
%ISCC% "%PROJECT_ROOT%\installer\nexus_music_setup.iss" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] Inno Setup failed! Check build.log
    exit /b 1
)

REM === Report ===
echo.
echo =============================================
set INSTALLER=%PROJECT_ROOT%\dist\Setup_NEXUS_Music_v2.1.0.exe
if exist "%INSTALLER%" (
    for %%A in ("%INSTALLER%") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo   BUILD SUCCESSFUL
    echo.
    echo   Installer: dist\Setup_NEXUS_Music_v2.1.0.exe
    echo   Size: !SIZE_MB! MB
    echo.
    echo   App folder: dist\NEXUS_Music_Manager\
) else (
    echo   Installer not found - check build.log
)
echo =============================================

echo Build finished: %date% %time% >> "%LOG%"
endlocal
