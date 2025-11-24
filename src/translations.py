#!/usr/bin/env python3
"""
Multi-language Translation System
Project: AGENTE_MUSICA_MP3_001
Languages: Español (es), English (en)

Usage:
    from translations import tr, set_language, get_language, LANGUAGES

    # Get translated text
    title = tr("app_title")

    # Change language
    set_language("es")  # Spanish
    set_language("en")  # English

    # Get current language
    current = get_language()  # "es" or "en"
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Available languages
LANGUAGES = {
    "es": "Español",
    "en": "English"
}

# Current language (default: Spanish for Latin America market)
_current_language = "es"

# Translation dictionaries
TRANSLATIONS = {
    "es": {
        # === Main Window ===
        "app_title": "🎵 NEXUS Gestor de Música - Edición Completa",
        "status_ready": "✅ NEXUS Gestor de Música - Listo",

        # === Tab Names ===
        "tab_import": "📥 Importar",
        "tab_library": "🎵 Biblioteca",
        "tab_albums": "📀 Álbumes",
        "tab_lyrics": "📝 Letras",
        "tab_search": "🔍 Buscar",
        "tab_queue": "📥 Cola",
        "tab_duplicates": "🔍 Duplicados",
        "tab_rename": "✏️ Renombrar",
        "tab_organize": "📁 Organizar",
        "tab_cleanup": "✨ Limpieza",
        "tab_playlist": "🎵 Playlist",

        # === Library Tab ===
        "library_title": "📚 Biblioteca de Música",
        "library_songs": "canciones",
        "library_artists": "artistas",
        "library_albums": "álbumes",
        "library_empty": "Biblioteca vacía - Importa música para comenzar",
        "library_search_placeholder": "🔍 Buscar en biblioteca...",

        # === Search Tab ===
        "search_title": "🔍 Buscar y Descargar",
        "search_placeholder": "🔍 Buscar artista, canción, álbum...",
        "btn_search": "🔎 Buscar",
        "btn_add_to_queue": "➕ Agregar a Cola",
        "btn_clear_selection": "Limpiar Selección",
        "search_youtube": "YouTube",
        "search_spotify": "Spotify",
        "search_results": "resultados",
        "search_selected": "Seleccionados: {count}",
        "search_no_results": "No se encontraron resultados",
        "search_error": "Error en búsqueda",

        # === Queue Tab ===
        "queue_title": "📥 Cola de Descargas",
        "btn_download_all": "⬇️ Descargar Todo",
        "btn_pause_all": "⏸️ Pausar Todo",
        "btn_clear_completed": "🗑️ Limpiar Completados",
        "queue_empty": "Cola vacía - Agrega canciones desde Buscar",
        "queue_downloading": "Descargando {current}/{total}...",
        "queue_complete": "✅ Todas las descargas completadas",
        "queue_status_pending": "Pendiente",
        "queue_status_downloading": "Descargando",
        "queue_status_complete": "Completado",
        "queue_status_failed": "Falló",

        # === Duplicates Tab ===
        "duplicates_title": "🔍 Detector de Duplicados",
        "duplicates_method": "Método de Detección:",
        "duplicates_method_metadata": "Metadatos (Título + Artista)",
        "duplicates_method_fingerprint": "Huella de Audio",
        "duplicates_method_filesize": "Tamaño de Archivo",
        "duplicates_similarity": "Similitud mínima:",
        "btn_scan_duplicates": "🔎 Escanear",
        "btn_auto_select": "🎯 Auto-Seleccionar Menor Calidad",
        "btn_delete_selected": "🗑️ Eliminar Seleccionados",
        "duplicates_found": "Encontrados {count} grupos de duplicados",
        "duplicates_none": "No se encontraron duplicados",

        # === Organize Tab ===
        "organize_title": "📁 Auto-Organizar Biblioteca",
        "organize_target": "Directorio Destino:",
        "organize_structure": "Estructura de Carpetas:",
        "organize_artist_album": "Artista/Álbum",
        "organize_genre_artist": "Género/Artista/Álbum",
        "organize_flat": "Plano (todo junto)",
        "btn_browse": "📁 Explorar",
        "btn_preview": "👁️ Vista Previa",
        "btn_organize": "📁 Organizar",
        "organize_copy": "Copiar archivos (mantener original)",
        "organize_move": "Mover archivos",

        # === Rename Tab ===
        "rename_title": "✏️ Renombrar en Lote",
        "rename_template": "Plantilla:",
        "rename_template_help": "Variables: {title}, {artist}, {album}, {track}, {year}",
        "btn_preview_rename": "👁️ Previsualizar",
        "btn_rename": "✏️ Renombrar",
        "rename_success": "Renombrados {count} archivos",

        # === Player / Now Playing ===
        "player_title": "▶️ Reproduciendo",
        "player_no_song": "Sin canción",
        "player_unknown_artist": "Artista Desconocido",
        "player_unknown_album": "Álbum Desconocido",
        "btn_play": "▶️",
        "btn_pause": "⏸️",
        "btn_stop": "⏹️",
        "btn_previous": "⏮️",
        "btn_next": "⏭️",
        "player_volume": "Volumen",
        "player_shuffle": "Aleatorio",
        "player_repeat": "Repetir",

        # === Playlist Widget ===
        "playlist_title": "🎵 Lista de Reproducción",
        "playlist_new": "Nueva Playlist",
        "playlist_delete": "Eliminar Playlist",
        "playlist_rename": "Renombrar",
        "playlist_add_songs": "Agregar Canciones",
        "playlist_remove_song": "Quitar de Playlist",
        "playlist_empty": "Playlist vacía",
        "playlist_songs_count": "{count} canciones",

        # === Lyrics Tab ===
        "lyrics_title": "📝 Letras",
        "lyrics_no_song": "Reproduce una canción para ver sus letras",
        "lyrics_loading": "Buscando letras...",
        "lyrics_not_found": "Letras no encontradas",
        "btn_fetch_lyrics": "🔄 Buscar Letras",

        # === Import Tab ===
        "import_title": "📥 Importar Biblioteca",
        "import_select_folder": "Seleccionar Carpeta",
        "import_scanning": "Escaneando archivos...",
        "import_found": "Encontrados {count} archivos de música",
        "import_complete": "Importación completada",
        "btn_import": "📥 Importar",
        "btn_select_folder": "📁 Seleccionar Carpeta",

        # === Cleanup Tab ===
        "cleanup_title": "✨ Asistente de Limpieza de Metadatos",
        "cleanup_scan": "Escanear Problemas",
        "cleanup_fix_all": "Corregir Todo",
        "cleanup_issues_found": "Encontrados {count} problemas",

        # === Dialogs ===
        "dialog_confirm": "Confirmar",
        "dialog_cancel": "Cancelar",
        "dialog_close": "Cerrar",
        "dialog_save": "Guardar",
        "dialog_delete_confirm": "¿Estás seguro de que deseas eliminar?",
        "dialog_error": "Error",
        "dialog_success": "Éxito",
        "dialog_warning": "Advertencia",

        # === Settings ===
        "settings_title": "⚙️ Configuración",
        "settings_language": "Idioma:",
        "settings_theme": "Tema:",
        "settings_theme_dark": "Oscuro",
        "settings_theme_light": "Claro",
        "settings_downloads": "Carpeta de Descargas:",
        "settings_api_keys": "Claves de API",
        "settings_save": "Guardar Configuración",

        # === API Settings ===
        "api_title": "🔑 Configuración de API",
        "api_youtube": "YouTube API Key",
        "api_spotify_id": "Spotify Client ID",
        "api_spotify_secret": "Spotify Client Secret",
        "api_genius": "Genius API Token",
        "api_test": "Probar Conexión",
        "api_save": "Guardar",

        # === Errors ===
        "error_file_not_found": "Archivo no encontrado",
        "error_connection": "Error de conexión",
        "error_api_key": "Clave de API inválida",
        "error_download": "Error en descarga",
        "error_database": "Error de base de datos",

        # === Status Messages ===
        "status_loading": "Cargando...",
        "status_saving": "Guardando...",
        "status_processing": "Procesando...",
        "status_complete": "Completado",
        "status_failed": "Falló",
        "status_cancelled": "Cancelado",
        "status_theme_switched": "Cambiado a tema {theme}",

        # === Menu Items ===
        "menu_file": "&Archivo",
        "menu_exit": "&Salir",
        "menu_settings": "&Configuración",
        "menu_api_config": "&Configuración de API...",
        "menu_language": "&Idioma",
        "menu_view": "&Ver",
        "menu_toggle_theme": "Alternar &Tema Claro/Oscuro",
        "menu_help": "&Ayuda",
        "menu_shortcuts": "&Atajos de Teclado",
        "menu_api_guide": "&Guía de Configuración API",
        "menu_about": "&Acerca de",

        # === Language Change ===
        "language_changed_title": "Idioma Cambiado",
        "language_changed_message": "El idioma se ha cambiado. Por favor reinicia la aplicación para ver los cambios.",
    },

    "en": {
        # === Main Window ===
        "app_title": "🎵 NEXUS Music Manager - Complete Edition",
        "status_ready": "✅ NEXUS Music Manager - Ready",

        # === Tab Names ===
        "tab_import": "📥 Import",
        "tab_library": "🎵 Library",
        "tab_albums": "📀 Albums",
        "tab_lyrics": "📝 Lyrics",
        "tab_search": "🔍 Search",
        "tab_queue": "📥 Queue",
        "tab_duplicates": "🔍 Duplicates",
        "tab_rename": "✏️ Rename",
        "tab_organize": "📁 Organize",
        "tab_cleanup": "✨ Cleanup",
        "tab_playlist": "🎵 Playlist",

        # === Library Tab ===
        "library_title": "📚 Music Library",
        "library_songs": "songs",
        "library_artists": "artists",
        "library_albums": "albums",
        "library_empty": "Library empty - Import music to get started",
        "library_search_placeholder": "🔍 Search library...",

        # === Search Tab ===
        "search_title": "🔍 Search & Download",
        "search_placeholder": "🔍 Search artist, song, album...",
        "btn_search": "🔎 Search",
        "btn_add_to_queue": "➕ Add to Queue",
        "btn_clear_selection": "Clear Selection",
        "search_youtube": "YouTube",
        "search_spotify": "Spotify",
        "search_results": "results",
        "search_selected": "Selected: {count}",
        "search_no_results": "No results found",
        "search_error": "Search error",

        # === Queue Tab ===
        "queue_title": "📥 Download Queue",
        "btn_download_all": "⬇️ Download All",
        "btn_pause_all": "⏸️ Pause All",
        "btn_clear_completed": "🗑️ Clear Completed",
        "queue_empty": "Queue empty - Add songs from Search",
        "queue_downloading": "Downloading {current}/{total}...",
        "queue_complete": "✅ All downloads completed",
        "queue_status_pending": "Pending",
        "queue_status_downloading": "Downloading",
        "queue_status_complete": "Complete",
        "queue_status_failed": "Failed",

        # === Duplicates Tab ===
        "duplicates_title": "🔍 Duplicate Detector",
        "duplicates_method": "Detection Method:",
        "duplicates_method_metadata": "Metadata (Title + Artist)",
        "duplicates_method_fingerprint": "Audio Fingerprint",
        "duplicates_method_filesize": "File Size",
        "duplicates_similarity": "Minimum similarity:",
        "btn_scan_duplicates": "🔎 Scan",
        "btn_auto_select": "🎯 Auto-Select Lower Quality",
        "btn_delete_selected": "🗑️ Delete Selected",
        "duplicates_found": "Found {count} duplicate groups",
        "duplicates_none": "No duplicates found",

        # === Organize Tab ===
        "organize_title": "📁 Auto-Organize Library",
        "organize_target": "Target Directory:",
        "organize_structure": "Folder Structure:",
        "organize_artist_album": "Artist/Album",
        "organize_genre_artist": "Genre/Artist/Album",
        "organize_flat": "Flat (all together)",
        "btn_browse": "📁 Browse",
        "btn_preview": "👁️ Preview",
        "btn_organize": "📁 Organize",
        "organize_copy": "Copy files (keep original)",
        "organize_move": "Move files",

        # === Rename Tab ===
        "rename_title": "✏️ Batch Rename",
        "rename_template": "Template:",
        "rename_template_help": "Variables: {title}, {artist}, {album}, {track}, {year}",
        "btn_preview_rename": "👁️ Preview",
        "btn_rename": "✏️ Rename",
        "rename_success": "Renamed {count} files",

        # === Player / Now Playing ===
        "player_title": "▶️ Now Playing",
        "player_no_song": "No song playing",
        "player_unknown_artist": "Unknown Artist",
        "player_unknown_album": "Unknown Album",
        "btn_play": "▶️",
        "btn_pause": "⏸️",
        "btn_stop": "⏹️",
        "btn_previous": "⏮️",
        "btn_next": "⏭️",
        "player_volume": "Volume",
        "player_shuffle": "Shuffle",
        "player_repeat": "Repeat",

        # === Playlist Widget ===
        "playlist_title": "🎵 Playlist",
        "playlist_new": "New Playlist",
        "playlist_delete": "Delete Playlist",
        "playlist_rename": "Rename",
        "playlist_add_songs": "Add Songs",
        "playlist_remove_song": "Remove from Playlist",
        "playlist_empty": "Playlist empty",
        "playlist_songs_count": "{count} songs",

        # === Lyrics Tab ===
        "lyrics_title": "📝 Lyrics",
        "lyrics_no_song": "Play a song to see its lyrics",
        "lyrics_loading": "Searching lyrics...",
        "lyrics_not_found": "Lyrics not found",
        "btn_fetch_lyrics": "🔄 Fetch Lyrics",

        # === Import Tab ===
        "import_title": "📥 Import Library",
        "import_select_folder": "Select Folder",
        "import_scanning": "Scanning files...",
        "import_found": "Found {count} music files",
        "import_complete": "Import complete",
        "btn_import": "📥 Import",
        "btn_select_folder": "📁 Select Folder",

        # === Cleanup Tab ===
        "cleanup_title": "✨ Metadata Cleanup Wizard",
        "cleanup_scan": "Scan for Issues",
        "cleanup_fix_all": "Fix All",
        "cleanup_issues_found": "Found {count} issues",

        # === Dialogs ===
        "dialog_confirm": "Confirm",
        "dialog_cancel": "Cancel",
        "dialog_close": "Close",
        "dialog_save": "Save",
        "dialog_delete_confirm": "Are you sure you want to delete?",
        "dialog_error": "Error",
        "dialog_success": "Success",
        "dialog_warning": "Warning",

        # === Settings ===
        "settings_title": "⚙️ Settings",
        "settings_language": "Language:",
        "settings_theme": "Theme:",
        "settings_theme_dark": "Dark",
        "settings_theme_light": "Light",
        "settings_downloads": "Downloads Folder:",
        "settings_api_keys": "API Keys",
        "settings_save": "Save Settings",

        # === API Settings ===
        "api_title": "🔑 API Configuration",
        "api_youtube": "YouTube API Key",
        "api_spotify_id": "Spotify Client ID",
        "api_spotify_secret": "Spotify Client Secret",
        "api_genius": "Genius API Token",
        "api_test": "Test Connection",
        "api_save": "Save",

        # === Errors ===
        "error_file_not_found": "File not found",
        "error_connection": "Connection error",
        "error_api_key": "Invalid API key",
        "error_download": "Download error",
        "error_database": "Database error",

        # === Status Messages ===
        "status_loading": "Loading...",
        "status_saving": "Saving...",
        "status_processing": "Processing...",
        "status_complete": "Complete",
        "status_failed": "Failed",
        "status_cancelled": "Cancelled",
        "status_theme_switched": "Switched to {theme} theme",

        # === Menu Items ===
        "menu_file": "&File",
        "menu_exit": "E&xit",
        "menu_settings": "&Settings",
        "menu_api_config": "&API Configuration...",
        "menu_language": "&Language",
        "menu_view": "&View",
        "menu_toggle_theme": "Toggle &Dark/Light Theme",
        "menu_help": "&Help",
        "menu_shortcuts": "&Keyboard Shortcuts",
        "menu_api_guide": "&API Setup Guide",
        "menu_about": "&About",

        # === Language Change ===
        "language_changed_title": "Language Changed",
        "language_changed_message": "Language has been changed. Please restart the application to see the changes.",
    }
}


def set_language(lang_code: str) -> bool:
    """
    Set the current language

    Args:
        lang_code: Language code ("es" or "en")

    Returns:
        True if language was set, False if invalid code
    """
    global _current_language

    if lang_code in LANGUAGES:
        _current_language = lang_code
        logger.info(f"Language set to: {LANGUAGES[lang_code]} ({lang_code})")
        return True

    logger.warning(f"Invalid language code: {lang_code}")
    return False


def get_language() -> str:
    """Get current language code"""
    return _current_language


def get_language_name() -> str:
    """Get current language display name"""
    return LANGUAGES.get(_current_language, "Unknown")


def tr(key: str, **kwargs) -> str:
    """
    Get translated text (main translation function)

    Args:
        key: Translation key
        **kwargs: Format parameters (e.g., count=5)

    Returns:
        Translated text, or key if not found

    Example:
        tr("app_title")  # "NEXUS Music Manager"
        tr("search_selected", count=5)  # "Selected: 5"
    """
    text = TRANSLATIONS.get(_current_language, {}).get(key)

    if text is None:
        # Fallback to English
        text = TRANSLATIONS.get("en", {}).get(key, key)
        if text == key:
            logger.debug(f"Missing translation for key: {key}")

    # Apply format parameters
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing format parameter in translation '{key}': {e}")

    return text


# Alias for backward compatibility
def t(key: str, **kwargs) -> str:
    """Alias for tr() - backward compatibility"""
    return tr(key, **kwargs)


# Legacy TEXTS dict for backward compatibility
TEXTS = TRANSLATIONS["es"]
