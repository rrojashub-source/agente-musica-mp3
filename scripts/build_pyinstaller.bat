@echo off
REM ============================================
REM NEXUS Music Manager — PyInstaller Build
REM Produces: dist/NEXUS_Music_Manager.exe
REM ============================================
setlocal enabledelayedexpansion

echo.
echo =============================================
echo   NEXUS Music Manager - PyInstaller Build
echo =============================================
echo.

set PROJECT_ROOT=%~dp0..
set VENV=%PROJECT_ROOT%\venv
set PYTHON=%VENV%\Scripts\python.exe
set LOG=%PROJECT_ROOT%\build.log

if not exist "%PYTHON%" (
    echo [ERROR] Python venv not found
    exit /b 1
)

echo [OK] Python: & "%PYTHON%" --version
echo [OK] PyInstaller: & "%PYTHON%" -m PyInstaller --version
echo.

echo Build started: %date% %time% > "%LOG%"

cd /d "%PROJECT_ROOT%"

echo Building... (this takes 5-15 minutes)
echo Output: %LOG%

"%PYTHON%" -m PyInstaller ^
    --clean ^
    --noconfirm ^
    nexus_music.spec >> "%LOG%" 2>&1

set BUILD_RESULT=%ERRORLEVEL%

echo. >> "%LOG%"
echo Build finished: %date% %time% >> "%LOG%"
echo Exit code: %BUILD_RESULT% >> "%LOG%"

echo.
if %BUILD_RESULT% EQU 0 (
    if exist "%PROJECT_ROOT%\dist\NEXUS_Music_Manager.exe" (
        for %%A in ("%PROJECT_ROOT%\dist\NEXUS_Music_Manager.exe") do set SIZE=%%~zA
        set /a SIZE_MB=!SIZE! / 1048576
        echo =============================================
        echo   BUILD SUCCESSFUL
        echo   Output: dist\NEXUS_Music_Manager.exe
        echo   Size: !SIZE_MB! MB
        echo =============================================
        echo BUILD SUCCESS - Size: !SIZE! bytes >> "%LOG%"
    ) else (
        echo [ERROR] Build succeeded but exe not found
    )
) else (
    echo =============================================
    echo   BUILD FAILED - check build.log
    echo =============================================
    echo BUILD FAILED >> "%LOG%"
)

endlocal
