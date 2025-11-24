# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for NEXUS Music Manager
Build command: pyinstaller nexus_music.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Project paths
project_root = Path(SPECPATH)
src_path = project_root / 'src'

# Collect all source files
a = Analysis(
    [str(src_path / 'main.py')],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=[
        # Include data files
        ('data', 'data'),
        # Include any resource files
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.sip',
        # Database
        'sqlite3',
        # Audio
        'pygame',
        'pygame.mixer',
        # Numpy for visualizer
        'numpy',
        # API clients
        'googleapiclient',
        'googleapiclient.discovery',
        'google.auth',
        'google.oauth2',
        'spotipy',
        'spotipy.oauth2',
        'musicbrainzngs',
        'lyricsgenius',
        # Download
        'yt_dlp',
        # Metadata
        'mutagen',
        'mutagen.mp3',
        'mutagen.id3',
        'mutagen.easyid3',
        # Security
        'keyring',
        'keyring.backends',
        # Utils
        'requests',
        'urllib3',
        'certifi',
        # Our modules
        'database',
        'database.manager',
        'core',
        'core.audio_player',
        'core.playlist_manager',
        'core.download_queue',
        'core.theme_manager',
        'core.keyboard_shortcuts',
        'core.waveform_extractor',
        'core.spectrum_worker',
        'core.duplicate_detector',
        'core.library_organizer',
        'core.batch_renamer',
        'core.metadata_tagger',
        'core.metadata_cleaner',
        'core.metadata_fetcher',
        'core.cover_art_manager',
        'api',
        'api.youtube_search',
        'api.spotify_search',
        'api.musicbrainz_client',
        'api.genius_client',
        'gui',
        'gui.tabs',
        'gui.tabs.library_tab',
        'gui.tabs.search_tab',
        'gui.tabs.lyrics_tab',
        'gui.tabs.import_tab',
        'gui.tabs.duplicates_tab',
        'gui.tabs.organize_tab',
        'gui.tabs.rename_tab',
        'gui.tabs.cleanup_tab',
        'gui.widgets',
        'gui.widgets.now_playing_widget',
        'gui.widgets.playlist_widget',
        'gui.widgets.visualizer_widget',
        'gui.widgets.queue_widget',
        'gui.dialogs',
        'gui.dialogs.api_settings_dialog',
        'gui.dialogs.shortcuts_dialog',
        'utils',
        'utils.input_sanitizer',
        'workers',
        'workers.download_worker',
        'workers.library_import_worker',
        'config_manager',
        'translations',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NEXUS_Music_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path: 'assets/icon.ico'
)

# For creating a directory distribution instead of single file:
# Uncomment below and comment out the EXE section above
#
# exe = EXE(
#     pyz,
#     a.scripts,
#     [],
#     exclude_binaries=True,
#     name='NEXUS_Music_Manager',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     console=False,
# )
#
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='NEXUS_Music_Manager',
# )
