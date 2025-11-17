# 🎵 Agente de Música MP3 - Descargador Automático de YouTube

Un agente inteligente que automatiza la descarga de música desde YouTube, con capacidades de búsqueda automática de discografías completas.

## ✨ Características

- 🤖 **Búsqueda automática** de discografías completas por artista
- 🎥 **Encuentra URLs de YouTube** automáticamente
- 📊 **Procesamiento de Excel** con listas de canciones
- 🎵 **Descarga en MP3** de alta calidad (192 kbps)
- 📁 **Organización automática** por artista
- 🚀 **Versión portable** que funciona desde USB
- 📝 **Logging completo** para debugging

## 🚀 Inicio Rápido

### Opción 1: Uso Simple (Excel manual)
1. Edita `Lista_para_descargar_oficial.xlsx` con tus canciones
2. Ejecuta `iniciar_agente_final.bat`
3. ¡Disfruta tu música en la carpeta `downloads/`!

### Opción 2: Búsqueda Automática
1. Ejecuta `buscar_final.bat`
2. Ingresa el nombre del artista (ej: "Metallica")
3. El agente buscará toda la discografía automáticamente
4. Usa el Excel generado con el agente de descarga

## 📋 Requisitos

- Python 3.7+
- Conexión a Internet
- Windows 7+ (para archivos .bat)

**Dependencias** (se instalan automáticamente):
- `pandas` - Procesamiento de Excel
- `yt-dlp` - Descarga de YouTube
- `openpyxl` - Lectura de archivos Excel

## 🛠️ Instalación

### Instalación Normal
```bash
git clone https://github.com/TU_USUARIO/agente-musica-mp3
cd agente-musica-mp3
```

### Versión Portable (Sin Python)
1. Descarga la carpeta `AgenteMusicaMP3_Portable`
2. Copia a USB
3. Ejecuta `Iniciar.bat` en cualquier PC

## 🎯 Uso Detallado

### Formato del Excel
| Artist | Song | Album | Year | URL |
|--------|------|-------|------|-----|
| Metallica | Enter Sandman | Metallica | 1991 | https://youtube.com/... |
| Queen | Bohemian Rhapsody | A Night at the Opera | 1975 | |

- **Artist**: Nombre del artista
- **Song**: Título de la canción
- **Album**: Álbum (opcional)
- **Year**: Año (opcional)
- **URL**: URL de YouTube (opcional - se busca automáticamente si está vacía)

### Archivos Principales

- `agente_musica.py` - Motor principal de descarga
- `iniciar_agente_final.bat` - Lanzador principal
- `buscar_final.bat` - Búsqueda automática de discografías
- `agente_final.py` - Agente de búsqueda inteligente

## 📁 Estructura del Proyecto

```
agente-musica-mp3/
├── 🐍 agente_musica.py              # Motor principal
├── 🤖 agente_final.py               # Búsqueda automática  
├── 🚀 iniciar_agente_final.bat      # Lanzador principal
├── 🔍 buscar_final.bat              # Búsqueda de discografías
├── 📊 Lista_para_descargar_oficial.xlsx  # Ejemplo de Excel
├── 📁 downloads/                    # Música descargada
├── 📁 logs/                        # Registros de actividad
├── 📁 AgenteMusicaMP3_Portable/     # Versión portable
└── 📁 AgenteMusicaMP3_Ligero/       # Versión ligera
```

## 🎨 Capturas de Pantalla

### Interfaz Principal
```
========================================
  🎵 AGENTE DE MUSICA MP3 🎵
========================================
🔍 Sistema verificado ✅
📦 Dependencias OK ✅
📊 Archivo a procesar: Lista_para_descargar_oficial.xlsx
🚀 Iniciando descarga automáticamente...
```

### Búsqueda Automática
```
🤖 AGENTE AI COMPLETO - BÚSQUEDA + URLS
=============================================
🎵 Ingresa el artista: Metallica
🚀 Proceso completo para: Metallica
   1️⃣ Buscar discografía
   2️⃣ Buscar URLs de YouTube  
   3️⃣ Generar Excel completo
```

## 🔧 Características Avanzadas

### Versión Portable
- ✅ No requiere Python instalado
- ✅ Funciona desde USB en cualquier PC
- ✅ Incluye todas las dependencias
- ✅ Compatible con Windows 7+

### Búsqueda Inteligente
- 🔍 Utiliza MusicBrainz API para discografías
- 🎥 Búsqueda automática en YouTube
- 🧠 Filtrado inteligente de duplicados
- ⚡ Rate limiting para evitar bloqueos

### Organización Automática
- 📁 Crea carpetas por artista
- 🎵 Archivos MP3 de alta calidad
- 📝 Logging detallado de cada descarga
- 🔄 Reintentos automáticos en caso de error

## ⚠️ Consideraciones Legales

Este proyecto es para **uso educativo y personal únicamente**. 

- ✅ **Legal**: Descargar música de dominio público o Creative Commons
- ✅ **Legal**: Crear copias de seguridad de música que ya posees
- ❌ **Ilegal**: Descargar música con copyright sin permiso

**Alternativas legales recomendadas:**
- YouTube Premium (descargas oficiales)
- Spotify Premium
- Apple Music
- Amazon Music

## 🐛 Solución de Problemas

### Error: "Python no encontrado"
```bash
# Instalar Python desde python.org
# Asegurarse de marcar "Add Python to PATH"
```

### Error: "No se encuentran canciones"
- Verificar conexión a Internet
- Comprobar que las URLs de YouTube sean válidas
- Revisar logs en la carpeta `logs/`

### Descargas lentas
- El agente incluye rate limiting para evitar bloqueos
- Para listas grandes (50+ canciones), considera dividir en lotes

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📜 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Excelente herramienta de descarga
- [MusicBrainz](https://musicbrainz.org/) - Base de datos musical abierta
- [pandas](https://pandas.pydata.org/) - Procesamiento de datos en Python

## 🔗 Enlaces

- [Documentación de yt-dlp](https://github.com/yt-dlp/yt-dlp#readme)
- [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API)
- [Guía de Python para principiantes](https://www.python.org/about/gettingstarted/)

## 📊 Estadísticas

- 🎵 Funciona con cualquier artista en MusicBrainz
- ⚡ Velocidad: ~2 segundos por canción (con URL directa)
- 📦 Versión portable: 4GB (incluye todo)
- 🪶 Versión ligera: <1MB (requiere Python)

---

**¿Encontraste útil este proyecto? ¡Dale una ⭐ en GitHub!**

Desarrollado con ❤️ para los amantes de la música
