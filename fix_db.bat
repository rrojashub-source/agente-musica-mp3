@echo off
echo ========================================
echo Fixing Database - Using Contaminated with Good Durations
echo ========================================

REM Copy contaminated DB (has good durations)
copy /Y music_library_contaminated_20251119.db music_library.db

echo.
echo Running cleanup script...
spike_pyqt6\venv\Scripts\python.exe clean_db.py

echo.
echo ========================================
echo Done! Database fixed with correct durations
echo ========================================
pause
