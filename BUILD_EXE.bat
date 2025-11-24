@echo off
REM ============================================
REM NEXUS Music Manager - Build Windows Executable
REM ============================================

echo.
echo ====================================
echo   NEXUS Music Manager - Build Tool
echo ====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo.
echo [1/3] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Building executable...
pyinstaller nexus_music.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo ====================================
echo   Executable location:
echo   dist\NEXUS_Music_Manager.exe
echo ====================================
echo.

REM Check if exe was created
if exist "dist\NEXUS_Music_Manager.exe" (
    echo SUCCESS: Executable created successfully!
    echo Size:
    for %%A in ("dist\NEXUS_Music_Manager.exe") do echo   %%~zA bytes
    echo.
    echo To run: dist\NEXUS_Music_Manager.exe
) else (
    echo WARNING: Executable not found. Check build output.
)

echo.
pause
