# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for NEXUS Music Manager v2.1.0
Build command: pyinstaller nexus_music.spec
Stack: PySide6 + python-mpv + OpenGL
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
    binaries=[
        # libmpv for audio playback
        ('src/libmpv-2.dll', '.'),
    ],
    datas=[
        # Include data files (artist database, etc.)
        ('src/data', 'data'),
        # Include shader files for Organic Visualizer
        ('src/gui/visualizers/organic_shaders', 'gui/visualizers/organic_shaders'),
        # Include theme files (QSS stylesheets)
        ('src/gui/themes', 'gui/themes'),
        # Include database migrations
        ('src/database/migrations', 'database/migrations'),
        # Include plugins
        ('src/plugins/available', 'plugins/available'),
    ],
    hiddenimports=[
        # === PySide6 ===
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtOpenGLWidgets',
        'shiboken6',

        # === OpenGL for Organic Visualizer ===
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.GL.shaders',
        'OpenGL.arrays',
        'OpenGL.arrays.ctypesarrays',
        'OpenGL.platform',
        'OpenGL.platform.win32',

        # === Audio ===
        'mpv',
        'pydub',
        'numpy',
        'numpy.fft',
        'librosa',
        'pychord',

        # === Database ===
        'sqlite3',

        # === API clients ===
        'googleapiclient',
        'googleapiclient.discovery',
        'google.auth',
        'google.oauth2',
        'spotipy',
        'spotipy.oauth2',
        'musicbrainzngs',
        'lyricsgenius',
        'yt_dlp',

        # === Metadata ===
        'mutagen',
        'mutagen.mp3',
        'mutagen.id3',
        'mutagen.easyid3',
        'mutagen.flac',
        'mutagen.m4a',
        'mutagen.oggvorbis',

        # === Security ===
        'keyring',
        'keyring.backends',

        # === Web/HTTP ===
        'requests',
        'urllib3',
        'certifi',
        'bs4',
        'flask',
        'flask_cors',

        # === Plugins ===
        'pypresence',
        'qrcode',
        'acoustid',

        # === Config ===
        'dotenv',

        # === Our modules: controllers ===
        'controllers',
        'controllers.playback_controller',
        'controllers.ui_composer',
        'controllers.library_controller',
        'controllers.remote_controller',

        # === Our modules: database ===
        'database',
        'database.manager',

        # === Our modules: core ===
        'core',
        'core.audio_player',
        'core.audio_equalizer',
        'core.audio_embeddings',
        'core.audio_feature_extractor',
        'core.bpm_detector',
        'core.mood_classifier',
        'core.playlist_manager',
        'core.smart_playlist',
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
        'core.metadata_autocompleter',
        'core.cover_art_manager',
        'core.recommendation_engine',
        'core.lrc_parser',
        'core.api_adapters',
        'core.acoustid_client',
        'core.cleanup_workflow',

        # === Our modules: API ===
        'api',
        'api.youtube_search',
        'api.spotify_search',
        'api.musicbrainz_client',
        'api.genius_client',
        'api.chords_client',

        # === Our modules: GUI tabs ===
        'gui',
        'gui.base',
        'gui.base.base_tab',
        'gui.tabs',
        'gui.tabs.library_tab',
        'gui.tabs.search_tab',
        'gui.tabs.lyrics_tab',
        'gui.tabs.chords_tab',
        'gui.tabs.import_tab',
        'gui.tabs.duplicates_tab',
        'gui.tabs.organize_tab',
        'gui.tabs.rename_tab',
        'gui.tabs.cleanup_tab',
        'gui.tabs.cloud_sync_tab',
        'gui.tabs.statistics_tab',

        # === Our modules: GUI widgets ===
        'gui.widgets',
        'gui.widgets.now_playing_widget',
        'gui.widgets.playlist_widget',
        'gui.widgets.visualizer_widget',
        'gui.widgets.queue_widget',
        'gui.widgets.album_grid_widget',
        'gui.widgets.chord_diagram_widget',
        'gui.widgets.equalizer_widget',
        'gui.widgets.recommendations_widget',
        'gui.widgets.skeleton_widget',

        # === Our modules: GUI other ===
        'gui.visualizers',
        'gui.visualizers.organic_visualizer',
        'gui.dialogs',
        'gui.dialogs.api_settings_dialog',
        'gui.dialogs.shortcuts_dialog',
        'gui.themes',

        # === Our modules: services ===
        'services',
        'services.cloud_sync_service',
        'services.remote_server',
        'services.statistics_service',
        'services.download_service',
        'services.library_service',
        'services.player_service',
        'services.spotify_playlist_importer',

        # === Our modules: utils ===
        'utils',
        'utils.input_sanitizer',
        'utils.subprocess_patch',
        'utils.constants',
        'utils.rate_limiter',
        'utils.fpcalc_checker',

        # === Our modules: workers ===
        'workers',
        'workers.download_worker',
        'workers.library_import_worker',

        # === Our modules: plugins ===
        'plugins',
        'plugins.plugin_base',
        'plugins.plugin_manager',

        # === Our modules: top-level ===
        'config_manager',
        'translations',
        'api_config_wizard',
        'correction_engine',
        'folder_manager',
        'help_tab',
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
        'IPython',
        'jupyter',
        'notebook',
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
