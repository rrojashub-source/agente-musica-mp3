#!/usr/bin/env python3
"""
Sistema de Textos de la Aplicación
Project: AGENTE_MUSICA_MP3_001
Idioma: Español Único
"""

# Textos de la aplicación (español único)
TEXTS = {
    # Ventana Principal
    "app_title": "🎵 NEXUS Gestor de Música - Edición Completa",
    "status_ready": "✅ NEXUS Gestor de Música - Todos los Sistemas Operativos",

    # Nombres de Pestañas
    "tab_library": "📚 Biblioteca",
    "tab_search": "🔍 Buscar y Descargar",
    "tab_playlist": "📺 Lista de Reproducción YouTube",
    "tab_queue": "📥 Cola de Descargas",
    "tab_duplicates": "🔍 Encontrar Duplicados",
    "tab_organize": "📁 Auto-Organizar",
    "tab_rename": "📝 Renombrar Lote",
    "tab_player": "▶️ Reproductor",
    "tab_help": "❓ Ayuda",

    # Estadísticas Biblioteca
    "stats_songs": "canciones",
    "stats_artists": "artistas",
    "stats_albums": "álbumes",
    "stats_genres": "géneros",
    "stats_hours": "horas",

    # Tab Buscar
    "search_placeholder": "🔍 Buscar artista, canción, álbum...",
    "search_button": "🔎 Buscar",
    "add_to_queue": "➕ Agregar a Cola de Descargas",
    "clear_selection": "Limpiar Selección",
    "selected": "Seleccionados",
    "btn_search": "🔎 Buscar",
    "btn_add_to_queue": "➕ Agregar a Cola",
    "btn_clear_selection": "Limpiar Selección",
    "status_ready_search": "Listo para buscar",
    "status_searching": "Buscando '{query}'...",
    "status_found_results": "Encontrados {total_results} resultados",
    "status_search_failed": "Búsqueda falló",
    "status_selected": "Seleccionados: {count} canciones",

    # Tab Playlist
    "playlist_url_label": "URL de Playlist de YouTube:",
    "playlist_url_placeholder": "https://www.youtube.com/playlist?list=...",
    "btn_download_playlist": "📥 Descargar Playlist",
    "playlist_status_ready": "Ingresa URL de playlist para comenzar",
    "playlist_status_loading": "Cargando playlist...",
    "playlist_status_found": "Encontrados {count} videos",

    # Tab Cola de Descargas
    "btn_download_all": "⬇️ Descargar Todo",
    "btn_pause_all": "⏸️ Pausar Todo",
    "btn_clear_completed": "🗑️ Limpiar Completados",
    "queue_status_empty": "Cola vacía - Agrega canciones desde Buscar",
    "queue_status_downloading": "Descargando {current}/{total}...",
    "queue_status_complete": "✅ Todas las descargas completadas",

    # Tab Duplicados
    "duplicate_finder": "🔍 Buscador de Duplicados",
    "detection_method": "Método de Detección:",
    "method_metadata": "Metadatos (Título + Artista + Duración)",
    "method_fingerprint": "Huella de Audio (Coincidencia Exacta)",
    "method_filesize": "Tamaño de Archivo (Mismos Bytes)",
    "similarity": "Similitud:",
    "scan_button": "🔎 Escanear Duplicados",
    "auto_select_button": "🎯 Auto-Seleccionar Menor Calidad",
    "delete_button": "🗑️ Eliminar Seleccionados",
    "duplicates_method_label": "Método de Detección:",
    "duplicates_method_metadata": "Metadatos",
    "duplicates_method_fingerprint": "Huella Digital de Audio",
    "duplicates_method_filesize": "Tamaño de Archivo",
    "duplicates_similarity_label": "Umbral de Similitud:",
    "btn_scan_duplicates": "🔎 Escanear Duplicados",
    "btn_auto_select_lower": "🎯 Auto-Seleccionar Menor Calidad",
    "btn_delete_selected": "🗑️ Eliminar Seleccionados",
    "duplicates_status_ready": "Selecciona método y escanea",
    "duplicates_status_scanning": "Escaneando biblioteca...",
    "duplicates_status_found": "Encontrados {count} grupos de duplicados",

    # Tab Organizar
    "organize_title": "📁 Auto-Organizar Biblioteca",
    "target_directory": "Directorio Destino:",
    "folder_structure": "Estructura de Carpetas:",
    "preview_structure": "👁️ Vista Previa Estructura",
    "organize_button": "📁 Organizar Biblioteca",
    "copy_files": "Copiar archivos (mantener original)",
    "organize_target_label": "Directorio Destino:",
    "btn_browse": "📁 Explorar",
    "organize_structure_label": "Estructura de Carpetas:",
    "organize_structure_artist_album": "Artista/Álbum",
    "organize_structure_genre_artist": "Género/Artista/Álbum",
    "organize_structure_flat": "Plano por Artista",
    "btn_preview": "👁️ Vista Previa",
    "btn_organize": "📁 Organizar Biblioteca",
    "organize_status_ready": "Selecciona estructura y previsualiza",
    "organize_status_organizing": "Organizando archivos...",
    "organize_status_complete": "✅ Organización completada",

    # Tab Renombrar
    "rename_title": "📝 Renombrar Archivos en Lote",
    "rename_template": "Plantilla de Renombrado:",
    "custom_template": "Plantilla Personalizada:",
    "load_songs": "🔍 Cargar Canciones",
    "rename_button": "📝 Renombrar Seleccionados",
    "select_all": "Seleccionar Todo",
    "rename_template_label": "Plantilla de Nombres:",
    "rename_template_placeholder": "{track} - {artist} - {title}",
    "rename_variables_label": "Variables disponibles: {title}, {artist}, {album}, {track}, {year}, {genre}",
    "btn_preview_rename": "👁️ Previsualizar",
    "btn_rename": "📝 Renombrar Archivos",
    "rename_status_ready": "Ingresa plantilla y previsualiza",
    "rename_status_renaming": "Renombrando archivos...",
    "rename_status_complete": "✅ Renombrado completado",

    # Tab Reproductor
    "btn_play": "▶️ Reproducir",
    "btn_pause": "⏸️ Pausar",
    "btn_stop": "⏹️ Detener",
    "btn_previous": "⏮️ Anterior",
    "btn_next": "⏭️ Siguiente",
    "btn_add_files": "➕ Agregar Archivos",
    "btn_add_from_library": "📚 Desde Biblioteca",
    "btn_clear_playlist": "🗑️ Limpiar Lista",
    "btn_fetch_lyrics": "🔄 Obtener Letras",
    "player_volume_label": "Volumen:",
    "player_status_ready": "Listo para reproducir",
    "player_status_playing": "Reproduciendo: {title}",
    "player_status_paused": "Pausado",
    "player_status_stopped": "Detenido",
    "player_no_lyrics": "Sin letras disponibles",
    "player_loading_lyrics": "Cargando letras...",

    # Botones Generales
    "browse": "Explorar...",
    "cancel": "Cancelar",
    "confirm": "Confirmar",
    "close": "Cerrar",

    # Mensajes Generales
    "no_selection": "Sin Selección",
    "confirm_deletion": "Confirmar Eliminación",
    "operation_complete": "Operación Completa",
    "error": "Error",
    "success": "Éxito",
}


def t(key: str) -> str:
    """
    Obtener texto de la aplicación

    Args:
        key: Clave del texto

    Returns:
        Texto en español, o la clave si no existe
    """
    return TEXTS.get(key, key)


# Funciones obsoletas mantenidas por compatibilidad
def set_language(language: str):
    """Función obsoleta - aplicación solo en español"""
    pass


def get_language() -> str:
    """Retorna siempre español"""
    return "es"
