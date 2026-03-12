@echo off
REM Build with full logging to file
setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set SRC=%PROJECT_ROOT%\src
set DIST=%PROJECT_ROOT%\dist
set VENV=%PROJECT_ROOT%\venv
set PYTHON=%VENV%\Scripts\python.exe
set LOG=%PROJECT_ROOT%\build.log

echo Build started: %date% %time% > "%LOG%"
echo. >> "%LOG%"

cd /d "%SRC%"
set PYTHONPATH=%SRC%

"%PYTHON%" -m nuitka ^
    --mode=onefile ^
    --windows-console-mode=disable ^
    --output-dir="%DIST%" ^
    --output-filename=NEXUS_Music_Manager.exe ^
    --enable-plugin=pyside6 ^
    --enable-plugin=upx ^
    --msvc=latest ^
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
    main.py >> "%LOG%" 2>&1

set BUILD_RESULT=%ERRORLEVEL%

echo. >> "%LOG%"
echo Build finished: %date% %time% >> "%LOG%"
echo Exit code: %BUILD_RESULT% >> "%LOG%"

if %BUILD_RESULT% EQU 0 (
    echo BUILD SUCCESS >> "%LOG%"
    if exist "%DIST%\NEXUS_Music_Manager.exe" (
        for %%A in ("%DIST%\NEXUS_Music_Manager.exe") do (
            echo Size: %%~zA bytes >> "%LOG%"
        )
    )
) else (
    echo BUILD FAILED >> "%LOG%"
)

REM Cleanup build artifacts
if exist "%SRC%\main.build" rd /s /q "%SRC%\main.build" >nul 2>&1
if exist "%SRC%\main.onefile-build" rd /s /q "%SRC%\main.onefile-build" >nul 2>&1

exit /b %BUILD_RESULT%
