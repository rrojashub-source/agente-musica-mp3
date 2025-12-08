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

        # === Cloud Sync Tab ===
        "tab_cloud_sync": "☁️ Sincronización",
        "cloud_sync_title": "☁️ Sincronización en la Nube",
        "cloud_sync_info": "Sincroniza los metadatos de tu biblioteca entre dispositivos usando almacenamiento en la nube.\nNota: Solo se sincronizan metadatos, no los archivos MP3.",
        "cloud_sync_provider_config": "Configuración del Proveedor",
        "cloud_sync_provider": "Proveedor:",
        "cloud_sync_local_folder": "Carpeta Local (NAS/USB)",
        "cloud_sync_folder": "Carpeta:",
        "cloud_sync_folder_placeholder": "D:\\Sync\\NexusMusic o /mnt/nas/music",
        "cloud_sync_browse": "📁 Examinar",
        "cloud_sync_gdrive_info": "🔐 Google Drive requiere autenticación OAuth 2.0.\nNecesitas un archivo credentials.json de Google Cloud Console.",
        "cloud_sync_credentials_file": "Archivo de Credenciales:",
        "cloud_sync_credentials_placeholder": "Ruta al credentials.json de Google Cloud Console",
        "cloud_sync_how_to_credentials": "📖 Cómo Obtener Credenciales",
        "cloud_sync_status_not_auth": "Estado: No autenticado",
        "cloud_sync_connect": "🔗 Conectar Proveedor",
        "cloud_sync_status": "Estado de Sincronización",
        "cloud_sync_connection": "Conexión:",
        "cloud_sync_not_connected": "⚪ No conectado",
        "cloud_sync_connected": "🟢 Conectado",
        "cloud_sync_last_sync": "Última Sincronización:",
        "cloud_sync_never": "Nunca",
        "cloud_sync_device_id": "ID de Dispositivo:",
        "cloud_sync_options": "Opciones de Sincronización",
        "cloud_sync_conflict": "Resolución de Conflictos:",
        "cloud_sync_conflict_newer": "El más reciente gana (recomendado)",
        "cloud_sync_conflict_local": "Local gana (preferir este dispositivo)",
        "cloud_sync_conflict_remote": "Remoto gana (preferir nube)",
        "cloud_sync_conflict_both": "Mantener ambos (sin pérdida de datos)",
        "cloud_sync_conflict_manual": "Manual (preguntar cada vez)",
        "cloud_sync_auto_sync": "Sincronizar automáticamente al iniciar",
        "cloud_sync_progress": "Progreso",
        "cloud_sync_ready": "Listo",
        "cloud_sync_actions": "Acciones",
        "cloud_sync_sync_now": "🔄 Sincronizar Ahora",
        "cloud_sync_export": "📤 Exportar Biblioteca",
        "cloud_sync_import": "📥 Importar Biblioteca",
        "cloud_sync_activity_log": "Registro de Actividad",
        "cloud_sync_clear_log": "Limpiar Registro",

        # === Cloud Sync - Google Drive OAuth ===
        "cloud_sync_gdrive_simple_info": "Conecta tu cuenta de Google para sincronizar tu biblioteca en la nube.\nSolo se sincronizan los metadatos, no los archivos MP3.",
        "cloud_sync_connect_google": "Conectar con Google",
        "cloud_sync_logout": "Cerrar Sesión",
        "cloud_sync_checking_auth": "Verificando autenticación...",
        "cloud_sync_opening_browser": "Abriendo navegador...",
        "cloud_sync_connected_as": "Conectado como",
        "cloud_sync_success": "Conexión Exitosa",
        "cloud_sync_gdrive_success_msg": "¡Conectado a Google Drive!\n\nTu biblioteca se sincronizará en la carpeta 'NEXUS_Music_Sync'.",
        "cloud_sync_connection_failed": "Conexión fallida",
        "cloud_sync_missing_deps": "Dependencias faltantes",
        "cloud_sync_logout_confirm_title": "Cerrar Sesión",
        "cloud_sync_logout_confirm_msg": "¿Deseas cerrar sesión de Google Drive?\n\nTus datos sincronizados permanecerán en la nube.",

        # === Plugins Tab ===
        "tab_plugins": "🔌 Plugins",
        "plugins_title": "🔌 Administrador de Plugins",
        "plugins_info": "Extiende la funcionalidad de NEXUS con plugins.\nHabilita o deshabilita plugins según tus necesidades.",
        "plugins_installed": "Plugins Instalados",
        "plugins_name": "Nombre",
        "plugins_version": "Versión",
        "plugins_description": "Descripción",
        "plugins_status": "Estado",
        "plugins_enable": "Habilitar",
        "plugins_disable": "Deshabilitar",
        "plugins_enabled": "Habilitado",
        "plugins_disabled": "Deshabilitado",
        "plugins_settings": "Configuración del Plugin",
        "plugins_no_settings": "Este plugin no tiene configuración.",
        "plugins_statistics": "📊 ESTADÍSTICAS",
        "plugins_total_plays": "Total de reproducciones",
        "plugins_unique_songs": "Canciones únicas",
        "plugins_avg_plays": "Promedio por canción",
        "plugins_most_played": "🏆 Más reproducidas",

        # === Remote Tab ===
        "tab_remote": "📱 Remoto",
        "remote_title": "📱 Control Remoto",
        "remote_instructions": "1. Haz clic en 'Iniciar' para habilitar el control remoto\n2. Asegúrate de que tu teléfono esté en la misma red WiFi\n3. Escanea el código QR o ingresa la URL en el navegador de tu móvil",
        "remote_server": "Servidor",
        "remote_port": "Puerto:",
        "remote_start": "▶ Iniciar",
        "remote_stop": "⏹ Detener",
        "remote_connection": "Conexión",
        "remote_url_not_running": "URL: No ejecutando",
        "remote_open_browser": "🌐 Abrir en Navegador",
        "remote_status_stopped": "⚪ Servidor detenido",
        "remote_status_running": "🟢 Servidor ejecutando",
        "remote_activity_log": "Registro de Actividad",

        # === Content Filter Tab ===
        "tab_content_filter": "🛡️ Filtro",
        "content_filter_title": "🛡️ Filtro de Contenido",
        "content_filter_description": "Clasifica tu música por tipo de contenido (explícito, infantil, limpio). Usa base de datos de artistas, análisis de palabras clave, y opcionalmente letras/audio.",
        "content_filter_scan": "Escanear",
        "content_filter_source": "Fuente:",
        "content_filter_source_folder": "Carpeta",
        "content_filter_source_library": "Biblioteca",
        "content_filter_use_lyrics": "Analizar letras (online)",
        "content_filter_lyrics_tooltip": "Busca letras en Genius/Musixmatch para análisis profundo",
        "content_filter_use_audio": "Analizar audio",
        "content_filter_audio_tooltip": "Analiza características de audio (requiere librosa)",
        "content_filter_scan_btn": "🔍 Escanear",
        "content_filter_cancel": "Cancelar",
        "content_filter_results": "Resultados",
        "content_filter_show": "Mostrar:",
        "content_filter_all": "Todos",
        "content_filter_explicit_only": "Solo Explícitos",
        "content_filter_clean_only": "Solo Limpios",
        "content_filter_children_only": "Solo Infantil",
        "content_filter_unknown_only": "Solo Desconocidos",
        "content_filter_col_artist": "Artista",
        "content_filter_col_title": "Título",
        "content_filter_col_rating": "Clasificación",
        "content_filter_col_confidence": "Confianza",
        "content_filter_col_reasons": "Razones",
        "content_filter_col_path": "Ruta",
        "content_filter_actions": "Acciones",
        "content_filter_move_to": "📁 Mover a...",
        "content_filter_copy_to": "📋 Copiar a...",
        "content_filter_delete": "🗑️ Eliminar",
        "content_filter_export_safe": "✅ Exportar Solo Seguros",
        "content_filter_select_folder": "Seleccionar carpeta a escanear",
        "content_filter_library_coming_soon": "Escaneo de biblioteca - Próximamente",
        "content_filter_no_files_title": "Sin archivos",
        "content_filter_no_files_msg": "No se encontraron archivos de audio en la carpeta seleccionada",
        "content_filter_select_dest": "Seleccionar carpeta destino",
        "content_filter_move_complete": "Movimiento completado",
        "content_filter_moved_count": "Se movieron {count} archivos",
        "content_filter_copy_complete": "Copia completada",
        "content_filter_copied_count": "Se copiaron {count} archivos",
        "content_filter_confirm_delete": "Confirmar eliminación",
        "content_filter_delete_confirm_msg": "¿Eliminar {count} archivos permanentemente?",
        "content_filter_delete_complete": "Eliminación completada",
        "content_filter_deleted_count": "Se eliminaron {count} archivos",
        "content_filter_scan_first": "Primero escanea una carpeta",
        "content_filter_select_export_dest": "Seleccionar carpeta para exportar",
        "content_filter_no_safe_content": "No hay contenido seguro para exportar",
        "content_filter_export_complete": "Exportación completada",
        "content_filter_exported_count": "Se exportaron {count}/{total} archivos seguros",
        # Safe Zones
        "content_filter_safe_zones": "Zonas Seguras",
        "content_filter_kids_mode": "👶 Modo Niños",
        "content_filter_kids_mode_tooltip": "Solo música infantil",
        "content_filter_family_mode": "👨‍👩‍👧‍👦 Modo Familia",
        "content_filter_family_mode_tooltip": "Música familiar (sin contenido explícito)",
        "content_filter_clean_mode": "✨ Modo Limpio",
        "content_filter_clean_mode_tooltip": "Música limpia para adultos",
        "content_filter_export_usb": "📱 Exportar a USB",
        "content_filter_export_usb_tooltip": "Exportar música organizada a USB",
        "content_filter_select_usb": "Seleccionar USB o destino",
        "content_filter_no_zone_match": "No hay canciones que coincidan con {zone}.\nPermitidos: {allowed}",
        "content_filter_zone_export_complete": "{icon} Exportación {zone} Completada",
        "content_filter_zone_export_msg": "Se exportaron {count} canciones a:\n{path}",
        "content_filter_usb_export_complete": "Exportación USB Completada",
        "content_filter_usb_export_msg": "Se exportaron {count} canciones al USB.\n\nEstructura de carpetas:\n  {base}/Infantil - Música infantil\n  {base}/Clean - Música limpia\n  {base}/Christian - Música cristiana\n  {base}/Explicit - Contenido explícito\n\nResumen guardado en: {summary}",
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

        # === Cloud Sync Tab ===
        "tab_cloud_sync": "☁️ Cloud Sync",
        "cloud_sync_title": "☁️ Cloud Sync",
        "cloud_sync_info": "Sync your library metadata across devices using cloud storage.\nNote: Only metadata is synced, not the actual MP3 files.",
        "cloud_sync_provider_config": "Provider Configuration",
        "cloud_sync_provider": "Provider:",
        "cloud_sync_local_folder": "Local Folder (NAS/USB)",
        "cloud_sync_folder": "Folder:",
        "cloud_sync_folder_placeholder": "D:\\Sync\\NexusMusic or /mnt/nas/music",
        "cloud_sync_browse": "📁 Browse",
        "cloud_sync_gdrive_info": "🔐 Google Drive requires OAuth 2.0 authentication.\nYou need a credentials.json file from Google Cloud Console.",
        "cloud_sync_credentials_file": "Credentials File:",
        "cloud_sync_credentials_placeholder": "Path to credentials.json from Google Cloud Console",
        "cloud_sync_how_to_credentials": "📖 How to Get Credentials",
        "cloud_sync_status_not_auth": "Status: Not authenticated",
        "cloud_sync_connect": "🔗 Connect Provider",
        "cloud_sync_status": "Sync Status",
        "cloud_sync_connection": "Connection:",
        "cloud_sync_not_connected": "⚪ Not connected",
        "cloud_sync_connected": "🟢 Connected",
        "cloud_sync_last_sync": "Last Sync:",
        "cloud_sync_never": "Never",
        "cloud_sync_device_id": "Device ID:",
        "cloud_sync_options": "Sync Options",
        "cloud_sync_conflict": "Conflict Resolution:",
        "cloud_sync_conflict_newer": "Newer Wins (recommended)",
        "cloud_sync_conflict_local": "Local Wins (prefer this device)",
        "cloud_sync_conflict_remote": "Remote Wins (prefer cloud)",
        "cloud_sync_conflict_both": "Keep Both (no data loss)",
        "cloud_sync_conflict_manual": "Manual (ask each time)",
        "cloud_sync_auto_sync": "Auto-sync on startup",
        "cloud_sync_progress": "Progress",
        "cloud_sync_ready": "Ready",
        "cloud_sync_actions": "Actions",
        "cloud_sync_sync_now": "🔄 Sync Now",
        "cloud_sync_export": "📤 Export Library",
        "cloud_sync_import": "📥 Import Library",
        "cloud_sync_activity_log": "Activity Log",
        "cloud_sync_clear_log": "Clear Log",

        # === Cloud Sync - Google Drive OAuth ===
        "cloud_sync_gdrive_simple_info": "Connect your Google account to sync your library to the cloud.\nOnly metadata is synced, not the actual MP3 files.",
        "cloud_sync_connect_google": "Connect with Google",
        "cloud_sync_logout": "Logout",
        "cloud_sync_checking_auth": "Checking authentication...",
        "cloud_sync_opening_browser": "Opening browser...",
        "cloud_sync_connected_as": "Connected as",
        "cloud_sync_success": "Connection Successful",
        "cloud_sync_gdrive_success_msg": "Connected to Google Drive!\n\nYour library will sync to the 'NEXUS_Music_Sync' folder.",
        "cloud_sync_connection_failed": "Connection failed",
        "cloud_sync_missing_deps": "Missing dependencies",
        "cloud_sync_logout_confirm_title": "Logout",
        "cloud_sync_logout_confirm_msg": "Do you want to logout from Google Drive?\n\nYour synced data will remain in the cloud.",

        # === Plugins Tab ===
        "tab_plugins": "🔌 Plugins",
        "plugins_title": "🔌 Plugin Manager",
        "plugins_info": "Extend NEXUS functionality with plugins.\nEnable or disable plugins based on your needs.",
        "plugins_installed": "Installed Plugins",
        "plugins_name": "Name",
        "plugins_version": "Version",
        "plugins_description": "Description",
        "plugins_status": "Status",
        "plugins_enable": "Enable",
        "plugins_disable": "Disable",
        "plugins_enabled": "Enabled",
        "plugins_disabled": "Disabled",
        "plugins_settings": "Plugin Settings",
        "plugins_no_settings": "This plugin has no settings.",
        "plugins_statistics": "📊 STATISTICS",
        "plugins_total_plays": "Total plays",
        "plugins_unique_songs": "Unique songs",
        "plugins_avg_plays": "Average per song",
        "plugins_most_played": "🏆 Most played",

        # === Remote Tab ===
        "tab_remote": "📱 Remote",
        "remote_title": "📱 Remote Control",
        "remote_instructions": "1. Click 'Start' to enable remote control\n2. Make sure your phone is on the same WiFi network\n3. Scan the QR code or enter the URL in your mobile browser",
        "remote_server": "Server",
        "remote_port": "Port:",
        "remote_start": "▶ Start",
        "remote_stop": "⏹ Stop",
        "remote_connection": "Connection",
        "remote_url_not_running": "URL: Not running",
        "remote_open_browser": "🌐 Open in Browser",
        "remote_status_stopped": "⚪ Server stopped",
        "remote_status_running": "🟢 Server running",
        "remote_activity_log": "Activity Log",

        # === Content Filter Tab ===
        "tab_content_filter": "🛡️ Filter",
        "content_filter_title": "🛡️ Content Filter",
        "content_filter_description": "Classify your music by content type (explicit, children, clean). Uses artist database, keyword analysis, and optionally lyrics/audio.",
        "content_filter_scan": "Scan",
        "content_filter_source": "Source:",
        "content_filter_source_folder": "Folder",
        "content_filter_source_library": "Library",
        "content_filter_use_lyrics": "Analyze lyrics (online)",
        "content_filter_lyrics_tooltip": "Fetch lyrics from Genius/Musixmatch for deep analysis",
        "content_filter_use_audio": "Analyze audio",
        "content_filter_audio_tooltip": "Analyze audio features (requires librosa)",
        "content_filter_scan_btn": "🔍 Scan",
        "content_filter_cancel": "Cancel",
        "content_filter_results": "Results",
        "content_filter_show": "Show:",
        "content_filter_all": "All",
        "content_filter_explicit_only": "Explicit Only",
        "content_filter_clean_only": "Clean Only",
        "content_filter_children_only": "Children Only",
        "content_filter_unknown_only": "Unknown Only",
        "content_filter_col_artist": "Artist",
        "content_filter_col_title": "Title",
        "content_filter_col_rating": "Rating",
        "content_filter_col_confidence": "Confidence",
        "content_filter_col_reasons": "Reasons",
        "content_filter_col_path": "Path",
        "content_filter_actions": "Actions",
        "content_filter_move_to": "📁 Move to...",
        "content_filter_copy_to": "📋 Copy to...",
        "content_filter_delete": "🗑️ Delete",
        "content_filter_export_safe": "✅ Export Safe Only",
        "content_filter_select_folder": "Select folder to scan",
        "content_filter_library_coming_soon": "Library scanning - Coming soon",
        "content_filter_no_files_title": "No files",
        "content_filter_no_files_msg": "No audio files found in selected folder",
        "content_filter_select_dest": "Select destination folder",
        "content_filter_move_complete": "Move complete",
        "content_filter_moved_count": "Moved {count} files",
        "content_filter_copy_complete": "Copy complete",
        "content_filter_copied_count": "Copied {count} files",
        "content_filter_confirm_delete": "Confirm delete",
        "content_filter_delete_confirm_msg": "Delete {count} files permanently?",
        "content_filter_delete_complete": "Delete complete",
        "content_filter_deleted_count": "Deleted {count} files",
        "content_filter_scan_first": "Scan a folder first",
        "content_filter_select_export_dest": "Select folder for export",
        "content_filter_no_safe_content": "No safe content to export",
        "content_filter_export_complete": "Export complete",
        "content_filter_exported_count": "Exported {count}/{total} safe files",
        # Safe Zones
        "content_filter_safe_zones": "Safe Zones",
        "content_filter_kids_mode": "👶 Kids Mode",
        "content_filter_kids_mode_tooltip": "Children's music only",
        "content_filter_family_mode": "👨‍👩‍👧‍👦 Family Mode",
        "content_filter_family_mode_tooltip": "Family music (no explicit content)",
        "content_filter_clean_mode": "✨ Clean Mode",
        "content_filter_clean_mode_tooltip": "Clean music for adults",
        "content_filter_export_usb": "📱 Export to USB",
        "content_filter_export_usb_tooltip": "Export organized music to USB",
        "content_filter_select_usb": "Select USB Drive or Destination",
        "content_filter_no_zone_match": "No songs match {zone} criteria.\nAllowed: {allowed}",
        "content_filter_zone_export_complete": "{icon} {zone} Export Complete",
        "content_filter_zone_export_msg": "Exported {count} songs to:\n{path}",
        "content_filter_usb_export_complete": "USB Export Complete",
        "content_filter_usb_export_msg": "Exported {count} songs to USB.\n\nFolder structure:\n  {base}/Infantil - Children's music\n  {base}/Clean - Clean music\n  {base}/Christian - Christian music\n  {base}/Explicit - Explicit content\n\nSummary saved to: {summary}",
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
