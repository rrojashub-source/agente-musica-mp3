@echo off
title Agente de Musica MP3 - Descargador de YouTube
color 0A

echo ========================================
echo   🎵 AGENTE DE MUSICA MP3 🎵
echo ========================================
echo.

REM Verificaciones rápidas y silenciosas
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python no está instalado o no está en PATH
    echo 💡 Instala Python desde: https://python.org
    pause
    exit /b 1
)

if not exist "agente_musica.py" (
    echo ❌ Error: agente_musica.py no encontrado
    pause
    exit /b 1
)

if not exist "Lista_para_descargar_oficial.xlsx" (
    echo ❌ Error: Lista_para_descargar_oficial.xlsx no encontrado
    pause
    exit /b 1
)

echo 🔍 Sistema verificado ✅

REM Verificación inteligente de dependencias
echo 📦 Verificando dependencias...

set need_install=false

python -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 set need_install=true

python -c "import yt_dlp" >nul 2>&1  
if %errorlevel% neq 0 set need_install=true

python -c "import openpyxl" >nul 2>&1
if %errorlevel% neq 0 set need_install=true

if "%need_install%"=="true" (
    echo ⏳ Instalando dependencias faltantes...
    pip install pandas yt-dlp openpyxl --quiet --disable-pip-version-check
    echo ✅ Dependencias instaladas
) else (
    echo ✅ Dependencias OK
)

REM Crear carpetas
mkdir downloads 2>nul
mkdir logs 2>nul

REM Mostrar info del archivo
echo.
echo 📊 Archivo a procesar:
for %%A in ("Lista_para_descargar_oficial.xlsx") do (
    echo    📁 %%~nxA (%%~zA bytes)
)

echo    📁 Destino: %cd%\downloads
echo.

REM ¡ELIMINAMOS LA CONFIRMACIÓN REDUNDANTE!
REM El usuario ya decidió ejecutar el .bat, así que procedemos directamente

echo 🚀 Iniciando descarga automáticamente...
echo ⏱️  Esto puede tomar varios minutos dependiendo del número de canciones
echo.
echo =========================================
echo   DESCARGANDO MUSICA...
echo =========================================
echo.

REM Ejecutar directamente
python agente_musica.py Lista_para_descargar_oficial.xlsx

REM Procesar resultado
set exit_code=%errorlevel%

echo.
echo =========================================
if %exit_code% equ 0 (
    echo   ✅ DESCARGA COMPLETADA EXITOSAMENTE
    echo =========================================
    echo.
    
    REM Verificar archivos descargados
    if exist "downloads\*.mp3" (
        echo 🎵 ¡Música descargada exitosamente!
        echo 📁 Ubicación: %cd%\downloads
        echo.
        
        REM Contar archivos MP3
        dir downloads\*.mp3 /s /b 2>nul | find /c ".mp3" >temp_count.txt 2>nul
        if exist temp_count.txt (
            set /p file_count=<temp_count.txt
            echo    🎵 Archivos MP3 descargados: !file_count!
            del temp_count.txt
        )
        
        echo.
        echo 📂 Abriendo carpeta de descargas...
        start "" "downloads"
        
    ) else (
        echo ⚠️  No se encontraron archivos MP3 descargados
        echo 📝 Revisa los logs para más detalles
    )
    
) else (
    echo   ⚠️  COMPLETADO CON ALGUNAS ADVERTENCIAS
    echo =========================================
    echo.
    echo 📝 Algunos archivos pueden no haberse descargado
    echo    Revisa los logs en la carpeta "logs"
    
    if exist "downloads\*.mp3" (
        echo.
        echo 🎵 Pero se descargaron algunos archivos:
        start "" "downloads"
    )
)

echo.
echo ==========================================
echo   Proceso finalizado
echo ==========================================
echo   📁 Descargas: downloads\
echo   📝 Logs: logs\
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
