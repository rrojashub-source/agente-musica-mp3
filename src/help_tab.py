#!/usr/bin/env python3
"""
Help Tab - Integrated Documentation
Project: AGENTE_MUSICA_MP3_001
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QTextBrowser, QComboBox,
        QHBoxLayout, QLabel, QPushButton
    )
    from PyQt6.QtGui import QFont
    from PyQt6.QtCore import Qt
except ImportError:
    print("❌ PyQt6 not installed")
    exit(1)


class HelpTab(QWidget):
    """
    Help and Documentation Tab
    Comprehensive guide for all features
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📖 Ayuda y Documentación")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Topic selector
        topic_layout = QHBoxLayout()

        topic_label = QLabel("Tema:")
        topic_layout.addWidget(topic_label)

        self.topic_combo = QComboBox()
        self.topic_combo.addItems([
            "📚 Introducción General",
            "📚 Biblioteca - Explorar Música",
            "🔍 Buscar y Descargar",
            "📺 Descargar Listas de Reproducción",
            "🔍 Encontrar Duplicados",
            "📁 Organizar Biblioteca",
            "📝 Renombrar Archivos",
            "⚙️ Configuración API Keys",
            "🎯 Consejos y Trucos",
            "❓ Preguntas Frecuentes",
            "📋 Ver Logs del Sistema"
        ])
        self.topic_combo.currentIndexChanged.connect(self.change_topic)
        topic_layout.addWidget(self.topic_combo)

        layout.addLayout(topic_layout)

        # Content browser
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        layout.addWidget(self.content_browser)

        # Load initial content
        self.load_content()


    def change_topic(self, index: int):
        """Change help topic"""
        self.load_content()

    def load_content(self):
        """Load help content for current topic"""
        topic_index = self.topic_combo.currentIndex()
        content = self.get_content_es(topic_index)
        self.content_browser.setHtml(content)

    def get_content_es(self, topic_index: int) -> str:
        """Get Spanish content"""
        contents = [
            self.intro_es(),
            self.library_es(),
            self.search_es(),
            self.playlist_es(),
            self.duplicates_es(),
            self.organize_es(),
            self.rename_es(),
            self.api_keys_es(),
            self.tips_es(),
            self.faq_es(),
            self.logs_es()
        ]

        return contents[topic_index] if topic_index < len(contents) else contents[0]

    # ========================================
    # SPANISH CONTENT
    # ========================================

    def intro_es(self) -> str:
        return """
        <h1>🎵 NEXUS Gestor de Música</h1>
        <h2>Bienvenido a tu Gestor de Música Completo</h2>

        <h3>✨ Características Principales:</h3>
        <ul>
            <li><b>📚 Biblioteca</b> - Explora más de 10,000 canciones con búsqueda instantánea</li>
            <li><b>🔍 Buscar y Descargar</b> - Encuentra música en YouTube y Spotify</li>
            <li><b>📺 Listas de Reproducción</b> - Descarga playlists completas de YouTube</li>
            <li><b>📥 Cola de Descargas</b> - Gestiona descargas simultáneas</li>
            <li><b>🔍 Duplicados</b> - Encuentra y elimina canciones duplicadas</li>
            <li><b>📁 Organizar</b> - Ordena tu biblioteca automáticamente</li>
            <li><b>📝 Renombrar</b> - Cambia nombres de archivos en lote</li>
        </ul>

        <h3>🚀 Inicio Rápido:</h3>
        <ol>
            <li>Explora la pestaña <b>📚 Biblioteca</b> para ver tus canciones</li>
            <li>Usa <b>🔍 Buscar y Descargar</b> para encontrar nueva música</li>
            <li>Organiza tu colección con <b>📁 Organizar</b></li>
            <li>Limpia duplicados con <b>🔍 Encontrar Duplicados</b></li>
        </ol>

        <h3>📖 Navegación:</h3>
        <p>Usa el selector de temas arriba para ver ayuda específica de cada función.</p>

        <h3>💡 Nota:</h3>
        <p>Algunas funciones requieren API keys gratuitos (YouTube, Spotify).
        Ver la sección <b>⚙️ Configuración API Keys</b> para más información.</p>
        """

    def library_es(self) -> str:
        return """
        <h1>📚 Biblioteca - Explorar Música</h1>

        <h3>🎯 Función:</h3>
        <p>Explora tu colección completa de música con búsqueda instantánea y ordenamiento.</p>

        <h3>✨ Características:</h3>
        <ul>
            <li><b>Búsqueda FTS5</b> - Encuentra canciones por título, artista, álbum o género</li>
            <li><b>Ordenamiento</b> - Click en columnas para ordenar</li>
            <li><b>Selección múltiple</b> - Selecciona varias canciones a la vez</li>
            <li><b>Estadísticas</b> - Ve totales de canciones, artistas, álbumes</li>
        </ul>

        <h3>📊 Columnas Disponibles:</h3>
        <ul>
            <li><b>ID</b> - Identificador único</li>
            <li><b>Título</b> - Nombre de la canción</li>
            <li><b>Artistas</b> - Intérpretes</li>
            <li><b>Álbum</b> - Álbum de origen</li>
            <li><b>Género</b> - Estilo musical</li>
            <li><b>Año</b> - Fecha de lanzamiento</li>
            <li><b>Bitrate</b> - Calidad de audio</li>
            <li><b>Rating</b> - Calificación (estrellas)</li>
        </ul>

        <h3>🔍 Cómo Buscar:</h3>
        <ol>
            <li>Usa el cuadro de búsqueda en la parte superior</li>
            <li>Escribe: título, artista, álbum o género</li>
            <li>Los resultados aparecen instantáneamente</li>
            <li>Click en columnas para ordenar</li>
        </ol>

        <h3>⚡ Rendimiento:</h3>
        <p>La biblioteca carga ~2 segundos con 10,000+ canciones y usa solo 43MB de memoria.</p>
        """

    def search_es(self) -> str:
        return """
        <h1>🔍 Buscar y Descargar</h1>

        <h3>🎯 Función:</h3>
        <p>Busca música en YouTube y Spotify y descárgala directamente.</p>

        <h3>✨ Características:</h3>
        <ul>
            <li><b>Búsqueda dual</b> - YouTube + Spotify simultáneamente</li>
            <li><b>Resultados organizados</b> - Dos tablas separadas</li>
            <li><b>Selección múltiple</b> - Marca varias canciones</li>
            <li><b>Vista previa</b> - Ve detalles antes de descargar</li>
        </ul>

        <h3>📝 Cómo Usar:</h3>
        <ol>
            <li>Escribe tu búsqueda: "Queen - Bohemian Rhapsody"</li>
            <li>Marca YouTube y/o Spotify</li>
            <li>Click en <b>🔎 Buscar</b></li>
            <li>Revisa resultados en ambas tablas</li>
            <li>Marca las canciones que quieras</li>
            <li>Click en <b>➕ Agregar a Cola</b></li>
            <li>Ve a pestaña <b>📥 Cola de Descargas</b> para ver progreso</li>
        </ol>

        <h3>⚙️ Requisito:</h3>
        <p><b>API Keys requeridos</b> - YouTube Data API v3 y Spotify Web API.</p>
        <p>Ver sección <b>⚙️ Configuración API Keys</b> para obtenerlos gratis.</p>

        <h3>🎵 Calidad de Descarga:</h3>
        <ul>
            <li>Formato: MP3 320kbps</li>
            <li>Conversión: FFmpeg automática</li>
            <li>Metadata: Extraída automáticamente</li>
        </ul>
        """

    def playlist_es(self) -> str:
        return """
        <h1>📺 Descargar Listas de Reproducción</h1>

        <h3>🎯 Función:</h3>
        <p>Descarga playlists completas de YouTube con un solo click.</p>

        <h3>✨ Ventajas:</h3>
        <ul>
            <li><b>Un click</b> - Pega URL y descarga todo</li>
            <li><b>Vista previa</b> - Ve canciones antes de descargar</li>
            <li><b>Sin límites</b> - Playlists de 100+ canciones</li>
            <li><b>Sin API key</b> - No consume cuota de YouTube</li>
        </ul>

        <h3>📝 Cómo Usar:</h3>
        <ol>
            <li>Copia URL de playlist de YouTube</li>
            <li>Ejemplo: https://www.youtube.com/playlist?list=PLxxx...</li>
            <li>Pega en el campo de URL</li>
            <li>Click en <b>🔍 Cargar Playlist</b></li>
            <li>Revisa información (título, canciones, duración)</li>
            <li>Click en <b>⬇️ Descargar Todas</b></li>
            <li>Todas las canciones se agregan a la cola automáticamente</li>
        </ol>

        <h3>📊 Vista Previa Muestra:</h3>
        <ul>
            <li>Título de la playlist</li>
            <li>Creador</li>
            <li>Total de canciones</li>
            <li>Duración total</li>
            <li>Primeras 10 canciones</li>
        </ul>

        <h3>⏱️ Tiempo Estimado:</h3>
        <p>Playlist de 100 canciones ≈ 30-40 minutos de descarga (3 simultáneas).</p>
        """

    def duplicates_es(self) -> str:
        return """
        <h1>🔍 Encontrar Duplicados</h1>

        <h3>🎯 Función:</h3>
        <p>Detecta canciones duplicadas usando 3 métodos diferentes.</p>

        <h3>🔬 Métodos de Detección:</h3>

        <h4>1️⃣ Metadatos (Recomendado):</h4>
        <ul>
            <li>Compara: Título + Artista + Duración</li>
            <li>Similitud ajustable (70-100%)</li>
            <li>Rápido: ~2 minutos para 10,000 canciones</li>
            <li>Detecta remixes y versiones similares</li>
        </ul>

        <h4>2️⃣ Huella de Audio:</h4>
        <ul>
            <li>Análisis acústico con chromaprint</li>
            <li>99% precisión para duplicados exactos</li>
            <li>Más lento: ~10 canciones/segundo</li>
            <li>Requiere: libchromaprint-tools</li>
        </ul>

        <h4>3️⃣ Tamaño de Archivo:</h4>
        <ul>
            <li>Compara bytes exactos</li>
            <li>Súper rápido: ~200 canciones/segundo</li>
            <li>Menos preciso (falsos positivos)</li>
            <li>Útil para copias exactas</li>
        </ul>

        <h3>📝 Cómo Usar:</h3>
        <ol>
            <li>Selecciona método (Metadatos recomendado)</li>
            <li>Ajusta similitud (85% default)</li>
            <li>Click en <b>🔎 Escanear Duplicados</b></li>
            <li>Revisa grupos de duplicados</li>
            <li>Click en <b>🎯 Auto-Seleccionar Menor Calidad</b></li>
            <li>Verifica selección</li>
            <li>Click en <b>🗑️ Eliminar Seleccionados</b></li>
        </ol>

        <h3>💡 Tip:</h3>
        <p>La app mantiene automáticamente la versión de mayor bitrate (mejor calidad).</p>
        """

    def organize_es(self) -> str:
        return """
        <h1>📁 Organizar Biblioteca</h1>

        <h3>🎯 Función:</h3>
        <p>Organiza tu biblioteca automáticamente en carpetas estructuradas.</p>

        <h3>📂 Estructuras Disponibles:</h3>

        <h4>1️⃣ Género/Artista/Álbum/Canción:</h4>
        <pre>
Rock/
  └── Queen/
      └── A Night at the Opera (1975)/
          └── 01 - Bohemian Rhapsody.mp3
        </pre>

        <h4>2️⃣ Artista/Álbum/Canción:</h4>
        <pre>
Queen/
  └── A Night at the Opera/
      └── 01 - Bohemian Rhapsody.mp3
        </pre>

        <h4>3️⃣ Género/Artista/Canción:</h4>
        <pre>
Rock/
  └── Queen/
      └── Bohemian Rhapsody.mp3
        </pre>

        <h4>4️⃣ Plano (Artista - Título):</h4>
        <pre>
Queen - Bohemian Rhapsody.mp3
The Beatles - Hey Jude.mp3
        </pre>

        <h3>📝 Cómo Usar:</h3>
        <ol>
            <li>Selecciona carpeta destino</li>
            <li>Elige estructura deseada</li>
            <li>Click en <b>👁️ Vista Previa</b> (ver primeras 10)</li>
            <li>Marca si quieres copiar o mover</li>
            <li>Click en <b>📁 Organizar Biblioteca</b></li>
            <li>Confirma operación</li>
        </ol>

        <h3>⚠️ Mover vs Copiar:</h3>
        <ul>
            <li><b>Mover</b> - Archivos originales se eliminan</li>
            <li><b>Copiar</b> - Archivos originales permanecen</li>
        </ul>

        <h3>⏱️ Rendimiento:</h3>
        <p>10,000 archivos organizados en ~3 minutos.</p>
        """

    def rename_es(self) -> str:
        return """
        <h1>📝 Renombrar Archivos</h1>

        <h3>🎯 Función:</h3>
        <p>Renombra archivos en lote usando plantillas personalizables.</p>

        <h3>🔤 Variables Disponibles:</h3>
        <ul>
            <li><b>{track}</b> - Número de pista (01, 02...)</li>
            <li><b>{title}</b> - Título de canción</li>
            <li><b>{artist}</b> - Artista</li>
            <li><b>{album}</b> - Álbum</li>
            <li><b>{year}</b> - Año</li>
            <li><b>{genre}</b> - Género</li>
        </ul>

        <h3>📋 Plantillas Predefinidas:</h3>
        <ol>
            <li><code>{track} - {title}.mp3</code> → 01 - Bohemian Rhapsody.mp3</li>
            <li><code>{artist} - {title}.mp3</code> → Queen - Bohemian Rhapsody.mp3</li>
            <li><code>{artist} - {album} - {track} - {title}.mp3</code></li>
            <li><code>{track}. {artist} - {title}.mp3</code></li>
            <li><code>{year} - {artist} - {title}.mp3</code></li>
            <li><b>Personalizada</b> - Crea tu propia plantilla</li>
        </ol>

        <h3>📝 Cómo Usar:</h3>
        <ol>
            <li>Filtra canciones (opcional): "Queen"</li>
            <li>Click en <b>🔍 Cargar Canciones</b></li>
            <li>Selecciona plantilla o crea personalizada</li>
            <li>Revisa vista previa (Antes → Después)</li>
            <li>Click en <b>📝 Renombrar Seleccionados</b></li>
            <li>Confirma operación</li>
        </ol>

        <h3>✨ Vista Previa:</h3>
        <p>La tabla muestra cómo quedaría cada archivo ANTES de renombrar.</p>
        <p>Archivos que cambien aparecen en <b style="color: green;">verde</b>.</p>

        <h3>⏱️ Rendimiento:</h3>
        <p>1,000 archivos renombrados en ~2 segundos.</p>
        """

    def api_keys_es(self) -> str:
        return """
        <h1>⚙️ Configuración API Keys</h1>

        <h3>🔑 APIs Necesarios:</h3>

        <h2>1️⃣ YouTube Data API v3 (Para Búsqueda)</h2>

        <h4>🆓 Totalmente Gratis:</h4>
        <ul>
            <li>10,000 búsquedas por día</li>
            <li>Sin tarjeta de crédito</li>
            <li>Sin límites de tiempo</li>
        </ul>

        <h4>📝 Cómo Obtenerlo:</h4>
        <ol>
            <li>Ve a: <a href="https://console.developers.google.com/">Google Developers Console</a></li>
            <li>Crea un proyecto (o selecciona existente)</li>
            <li>Habilita "YouTube Data API v3"</li>
            <li>Ve a Credenciales → Crear Credenciales → API Key</li>
            <li>Copia la API key</li>
        </ol>

        <h4>⚙️ Dónde Configurar:</h4>
        <p>Edita archivo: <code>phase4_search_download/search_tab.py</code></p>
        <p>Línea 42: <code>API_KEY = "TU_CLAVE_AQUI"</code></p>

        <h2>2️⃣ Spotify Web API (Para Búsqueda)</h2>

        <h4>🆓 Totalmente Gratis:</h4>
        <ul>
            <li>100 búsquedas por segundo</li>
            <li>Sin límite diario</li>
            <li>Sin tarjeta de crédito</li>
        </ul>

        <h4>📝 Cómo Obtenerlo:</h4>
        <ol>
            <li>Ve a: <a href="https://developer.spotify.com/dashboard/">Spotify for Developers</a></li>
            <li>Inicia sesión (o crea cuenta gratis)</li>
            <li>Click en "Create an App"</li>
            <li>Completa nombre y descripción</li>
            <li>Click en "Show Client Secret"</li>
            <li>Copia Client ID y Client Secret</li>
        </ol>

        <h4>⚙️ Dónde Configurar:</h4>
        <p>Edita archivo: <code>phase4_search_download/search_tab.py</code></p>
        <p>Líneas 87-88:</p>
        <pre>
CLIENT_ID = "TU_CLIENT_ID"
CLIENT_SECRET = "TU_CLIENT_SECRET"
        </pre>

        <h3>✅ Sin API Keys Funciona:</h3>
        <ul>
            <li>✅ Biblioteca completa</li>
            <li>✅ Descargar playlists YouTube</li>
            <li>✅ Todas las herramientas de gestión</li>
            <li>❌ Solo búsqueda YouTube/Spotify necesita keys</li>
        </ul>

        <h3>💰 Costo Total:</h3>
        <p style="font-size: 20px; color: green;"><b>$0.00 por mes 🎉</b></p>
        """

    def tips_es(self) -> str:
        return """
        <h1>🎯 Consejos y Trucos</h1>

        <h3>⚡ Optimización de Rendimiento:</h3>
        <ul>
            <li><b>Búsqueda rápida</b> - La búsqueda FTS5 es instantánea, úsala libremente</li>
            <li><b>Ordenamiento</b> - Click en columnas usa SQL, no carga memoria</li>
            <li><b>Descargas</b> - 3 simultáneas es óptimo, más no acelera</li>
        </ul>

        <h3>🔍 Búsqueda Efectiva:</h3>
        <ul>
            <li><b>Términos simples</b> - "Queen Bohemian" mejor que frase completa</li>
            <li><b>Género + Artista</b> - "Rock Queen" para búsqueda específica</li>
            <li><b>Año</b> - "1975 Queen" para canciones de ese año</li>
        </ul>

        <h3>🧹 Mantenimiento de Biblioteca:</h3>
        <ol>
            <li><b>Primero:</b> Encuentra y elimina duplicados</li>
            <li><b>Segundo:</b> Organiza en carpetas estructuradas</li>
            <li><b>Tercero:</b> Renombra archivos con plantilla consistente</li>
            <li><b>Cuarto:</b> Revisa metadata con MusicBrainz</li>
        </ol>

        <h3>💾 Gestión de Espacio:</h3>
        <ul>
            <li><b>Duplicados</b> - Pueden liberar 10-20% de espacio</li>
            <li><b>Bitrate</b> - 320kbps es óptimo (192kbps suficiente para móvil)</li>
            <li><b>Organizar</b> - Usa "Copiar" primero para probar, luego "Mover"</li>
        </ul>

        <h3>🎵 Calidad de Audio:</h3>
        <ul>
            <li><b>YouTube</b> - Máximo 320kbps (después de conversión)</li>
            <li><b>Spotify</b> - Solo metadata (no descarga directa)</li>
            <li><b>Playlists</b> - Descargan en máxima calidad disponible</li>
        </ul>

        <h3>⚠️ Antes de Eliminar:</h3>
        <ol>
            <li>Revisa SIEMPRE la vista previa</li>
            <li>Usa "Auto-Seleccionar" para mantener mejor calidad</li>
            <li>Haz backup de archivos importantes primero</li>
            <li>Prueba en pequeña cantidad primero</li>
        </ol>

        <h3>🚀 Workflow Recomendado:</h3>
        <ol>
            <li>Descarga nueva música (Búsqueda o Playlists)</li>
            <li>Auto-completa metadata con MusicBrainz</li>
            <li>Busca duplicados y elimina</li>
            <li>Organiza en carpetas</li>
            <li>Renombra con plantilla consistente</li>
            <li>Disfruta tu biblioteca perfecta! 🎵</li>
        </ol>
        """

    def faq_es(self) -> str:
        return """
        <h1>❓ Preguntas Frecuentes</h1>

        <h3>🔧 Problemas Técnicos:</h3>

        <h4>Q: La app no inicia</h4>
        <p><b>A:</b> Verifica que tengas PyQt6 instalado:<br>
        <code>pip install PyQt6</code></p>

        <h4>Q: Búsqueda YouTube/Spotify no funciona</h4>
        <p><b>A:</b> Configura API keys (ver sección Configuración API Keys).<br>
        Sin keys, solo puedes usar descargas de playlists.</p>

        <h4>Q: Error al descargar</h4>
        <p><b>A:</b> Instala yt-dlp actualizado:<br>
        <code>pip install --upgrade yt-dlp</code></p>

        <h4>Q: No convierte a MP3</h4>
        <p><b>A:</b> Instala FFmpeg:<br>
        Linux: <code>sudo apt install ffmpeg</code><br>
        Mac: <code>brew install ffmpeg</code></p>

        <h3>💡 Uso:</h3>

        <h4>Q: ¿Puedo descargar de Spotify?</h4>
        <p><b>A:</b> No directamente (DRM). Busca en Spotify y descarga de YouTube.</p>

        <h4>Q: ¿Cuánto espacio ocupa la base de datos?</h4>
        <p><b>A:</b> 10,000 canciones ≈ 50MB de base de datos SQLite.</p>

        <h4>Q: ¿Puedo importar desde iTunes/Spotify?</h4>
        <p><b>A:</b> Actualmente no. Futuro: importación de playlists.</p>

        <h4>Q: ¿La organización mueve los archivos?</h4>
        <p><b>A:</b> Depende de la opción. "Copiar" mantiene originales, "Mover" elimina.</p>

        <h3>🔐 Privacidad:</h3>

        <h4>Q: ¿Mis datos se envían a algún servidor?</h4>
        <p><b>A:</b> No. Todo es local excepto búsquedas API (YouTube/Spotify).</p>

        <h4>Q: ¿Se guardan mis API keys?</h4>
        <p><b>A:</b> Sí, en archivos locales. No se comparten.</p>

        <h3>📊 Rendimiento:</h3>

        <h4>Q: ¿Cuántas canciones soporta?</h4>
        <p><b>A:</b> Probado con 10,000+. Teóricamente ilimitado (SQLite soporta TB).</p>

        <h4>Q: ¿Por qué solo 3 descargas simultáneas?</h4>
        <p><b>A:</b> Óptimo para no saturar conexión. Configurable en código.</p>

        <h3>🆘 Soporte:</h3>

        <h4>Q: ¿Dónde reporto bugs?</h4>
        <p><b>A:</b> Contacta al desarrollador: ricardo@nexusmusic.com</p>

        <h4>Q: ¿Hay actualizaciones?</h4>
        <p><b>A:</b> Sí, proyecto activo. Check GitHub para últimas versiones.</p>

        <h4>Q: ¿Es código abierto?</h4>
        <p><b>A:</b> Sí, licencia MIT. Contribuciones bienvenidas.</p>
        """

    def logs_es(self) -> str:
        """Display system logs in Spanish"""
        from logger_system import get_recent_logs, get_log_file_path

        try:
            logs = get_recent_logs(100)  # Get last 100 lines
            log_file = get_log_file_path()

            return f"""
            <h1>📋 Logs del Sistema</h1>

            <h3>📂 Ubicación del Archivo de Log:</h3>
            <p><code>{log_file}</code></p>

            <h3>🔍 ¿Para qué sirven los logs?</h3>
            <ul>
                <li>Rastrear errores y excepciones</li>
                <li>Diagnosticar problemas de la aplicación</li>
                <li>Ver qué operaciones se ejecutaron</li>
                <li>Depurar funcionalidades que fallan</li>
            </ul>

            <h3>📝 Últimas 100 Líneas del Log:</h3>
            <div style='background: #2b2b2b; color: #f8f8f2; padding: 15px;
                        border-radius: 5px; font-family: "Courier New", monospace;
                        font-size: 11px; overflow-x: auto; max-height: 400px; overflow-y: auto;'>
<pre>{logs}</pre>
            </div>

            <h3>⚙️ Información Adicional:</h3>
            <ul>
                <li><b>Rotación:</b> Los logs se rotan diariamente</li>
                <li><b>Formato:</b> <code>nexus_music_YYYYMMDD.log</code></li>
                <li><b>Retención:</b> Se mantienen 7 días</li>
                <li><b>Niveles:</b> DEBUG, INFO, WARNING, ERROR, CRITICAL</li>
            </ul>

            <h3>🔧 Niveles de Log:</h3>
            <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%;">
                <tr style="background: #f0f0f0;">
                    <th>Nivel</th>
                    <th>Descripción</th>
                </tr>
                <tr>
                    <td><b>DEBUG</b></td>
                    <td>Información detallada para diagnóstico</td>
                </tr>
                <tr>
                    <td><b>INFO</b></td>
                    <td>Eventos generales de la aplicación</td>
                </tr>
                <tr>
                    <td><b>WARNING</b></td>
                    <td>Situaciones inesperadas pero no críticas</td>
                </tr>
                <tr>
                    <td><b>ERROR</b></td>
                    <td>Errores que impiden operaciones específicas</td>
                </tr>
                <tr>
                    <td><b>CRITICAL</b></td>
                    <td>Errores graves que pueden detener la app</td>
                </tr>
            </table>

            <p><i>💡 Tip: Si reportas un problema, copia las líneas relevantes del log para ayudar en el diagnóstico.</i></p>
            """
        except Exception as e:
            return f"""
            <h1>📋 Logs del Sistema</h1>
            <p style='color: red;'><b>Error al cargar logs:</b> {str(e)}</p>
            <p>El sistema de logs puede no estar inicializado correctamente.</p>
            """

    # ========================================
