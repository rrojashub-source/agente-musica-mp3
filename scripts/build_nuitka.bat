@echo off
REM ============================================
REM NEXUS Music Manager — Nuitka Build Script
REM Produces: dist/NEXUS_Music_Manager.exe
REM Nuitka 4.x / Python 3.13 / MSVC 2022
REM ============================================
setlocal enabledelayedexpansion

echo.
echo =============================================
echo   NEXUS Music Manager - Nuitka Build
echo =============================================
echo.

REM === CONFIG ===
set PROJECT_ROOT=%~dp0..
set SRC=%PROJECT_ROOT%\src
set DIST=%PROJECT_ROOT%\dist
set VENV=%PROJECT_ROOT%\venv
set PYTHON=%VENV%\Scripts\python.exe
set OUTPUT_NAME=NEXUS_Music_Manager

REM === Verify venv exists ===
if not exist "%PYTHON%" (
    echo [ERROR] Python venv not found at %PYTHON%
    echo Run: python -m venv venv && venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

REM === Verify Nuitka ===
"%PYTHON%" -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Nuitka not installed. Run: venv\Scripts\pip install nuitka ordered-set
    exit /b 1
)

echo [OK] Python: %PYTHON%
"%PYTHON%" --version
echo.

REM === Verify libmpv ===
if not exist "%SRC%\libmpv-2.dll" (
    echo [ERROR] libmpv-2.dll not found in %SRC%
    echo Download from: https://sourceforge.net/projects/mpv-player-windows/
    exit /b 1
)
echo [OK] libmpv-2.dll found

REM === Clean previous build artifacts ===
echo.
echo [1/3] Cleaning previous build...
if exist "%DIST%\%OUTPUT_NAME%.exe" (
    echo   Backing up existing exe...
    move "%DIST%\%OUTPUT_NAME%.exe" "%DIST%\%OUTPUT_NAME%.exe.old" >nul 2>&1
)
if exist "%SRC%\main.build" rd /s /q "%SRC%\main.build" >nul 2>&1
if exist "%SRC%\main.dist" rd /s /q "%SRC%\main.dist" >nul 2>&1
if exist "%SRC%\main.onefile-build" rd /s /q "%SRC%\main.onefile-build" >nul 2>&1

REM === Build ===
echo.
echo [2/3] Building with Nuitka (this takes 10-30 minutes)...
echo   Mode: onefile (single .exe)
echo   Plugins: pyside6, upx
echo   Compiler: MSVC 2022 (auto-detected)
echo.

cd /d "%SRC%"
set PYTHONPATH=%SRC%

"%PYTHON%" -m nuitka ^
    --mode=onefile ^
    --windows-console-mode=disable ^
    --output-dir="%DIST%" ^
    --output-filename=%OUTPUT_NAME%.exe ^
    --enable-plugin=pyside6 ^
    --enable-plugin=upx ^
    --msvc=latest ^
    --jobs=8 ^
    --lto=yes ^
    --include-data-dir="%SRC%\data"=data ^
    --include-data-dir="%SRC%\gui\visualizers\organic_shaders"=gui/visualizers/organic_shaders ^
    --include-data-dir="%SRC%\gui\themes"=gui/themes ^
    --include-data-dir="%SRC%\database\migrations"=database/migrations ^
    --include-data-dir="%SRC%\plugins\available"=plugins/available ^
    --include-data-files="%SRC%\libmpv-2.dll"=libmpv-2.dll ^
    --include-module=sqlite3 ^
    --include-module=mpv ^
    --include-module=numpy ^
    --include-module=numpy.fft ^
    --include-module=numpy.linalg ^
    --include-module=OpenGL ^
    --include-module=OpenGL.GL ^
    --include-module=OpenGL.GL.shaders ^
    --include-module=OpenGL.arrays ^
    --include-module=OpenGL.arrays.ctypesarrays ^
    --include-module=OpenGL.platform ^
    --include-module=OpenGL.platform.win32 ^
    --include-module=googleapiclient ^
    --include-module=googleapiclient.discovery ^
    --include-module=google.auth ^
    --include-module=google.oauth2 ^
    --include-module=spotipy ^
    --include-module=spotipy.oauth2 ^
    --include-module=musicbrainzngs ^
    --include-module=lyricsgenius ^
    --include-module=yt_dlp ^
    --include-module=mutagen ^
    --include-module=mutagen.mp3 ^
    --include-module=mutagen.id3 ^
    --include-module=mutagen.easyid3 ^
    --include-module=keyring ^
    --include-module=keyring.backends ^
    --include-module=requests ^
    --include-module=urllib3 ^
    --include-module=certifi ^
    --include-module=pydub ^
    --include-module=librosa ^
    --include-module=pychord ^
    --include-module=bs4 ^
    --include-module=flask ^
    --include-module=flask_cors ^
    --include-module=qrcode ^
    --include-module=pypresence ^
    --include-module=acoustid ^
    --include-module=dotenv ^
    --include-module=shiboken6 ^
    --include-package=database ^
    --include-package=core ^
    --include-package=api ^
    --include-package=gui ^
    --include-package=gui.tabs ^
    --include-package=gui.widgets ^
    --include-package=gui.visualizers ^
    --include-package=gui.dialogs ^
    --include-package=gui.base ^
    --include-package=gui.themes ^
    --include-package=controllers ^
    --include-package=services ^
    --include-package=plugins ^
    --include-package=workers ^
    --include-package=utils ^
    --include-module=config_manager ^
    --include-module=translations ^
    --include-module=api_config_wizard ^
    --include-module=correction_engine ^
    --include-module=folder_manager ^
    --include-module=help_tab ^
    --nofollow-import-to=tkinter ^
    --nofollow-import-to=matplotlib ^
    --nofollow-import-to=scipy ^
    --nofollow-import-to=pandas ^
    --nofollow-import-to=PIL ^
    --nofollow-import-to=cv2 ^
    --nofollow-import-to=tensorflow ^
    --nofollow-import-to=torch ^
    --assume-yes-for-downloads ^
    --show-progress ^
    --show-memory ^
    --company-name="NEXUS" ^
    --product-name="NEXUS Music Manager" ^
    --product-version="2.1.0" ^
    --file-description="Professional Music Library Manager" ^
    --copyright="2025-2026 NEXUS / Ricardo" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed! Check output above.
    exit /b 1
)

REM === Post-build ===
echo.
echo [3/3] Post-build cleanup...
if exist "%SRC%\main.build" rd /s /q "%SRC%\main.build" >nul 2>&1
if exist "%SRC%\main.onefile-build" rd /s /q "%SRC%\main.onefile-build" >nul 2>&1

REM === Report ===
echo.
echo =============================================
if exist "%DIST%\%OUTPUT_NAME%.exe" (
    for %%A in ("%DIST%\%OUTPUT_NAME%.exe") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo   BUILD SUCCESSFUL
    echo   Output: %DIST%\%OUTPUT_NAME%.exe
    echo   Size: !SIZE_MB! MB
    if exist "%DIST%\%OUTPUT_NAME%.exe.old" (
        for %%B in ("%DIST%\%OUTPUT_NAME%.exe.old") do set OLD_SIZE=%%~zB
        set /a OLD_MB=!OLD_SIZE! / 1048576
        echo   Previous: !OLD_MB! MB
    )
) else (
    echo   BUILD FAILED - no exe produced
)
echo =============================================
echo.

endlocal
