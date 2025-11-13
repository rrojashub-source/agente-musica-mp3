#!/usr/bin/env python3
"""
Library Import Worker - Escanea e importa archivos de música
Extrae metadatos con mutagen y los guarda en la base de datos
Project: AGENTE_MUSICA_MP3_001
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from PyQt6.QtCore import QThread, pyqtSignal
except ImportError:
    print("❌ PyQt6 not installed")
    exit(1)

try:
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
except ImportError:
    print("❌ mutagen not installed")
    print("   Install with: pip install mutagen")
    exit(1)

# Import database manager
sys.path.insert(0, str(Path(__file__).parent / "phase2_database"))
from database_manager import MusicDatabaseManager


class LibraryImportWorker(QThread):
    """
    Worker que escanea carpeta de música y extrae metadatos
    Actualiza progreso en tiempo real e importa a base de datos
    """

    # Señales
    progress_update = pyqtSignal(int, str)  # (progress %, message)
    file_processed = pyqtSignal(str, bool)  # (file_path, success)
    import_complete = pyqtSignal(int, int)  # (total_imported, total_errors)
    error_occurred = pyqtSignal(str)

    def __init__(self, library_path: str, db_path: str):
        super().__init__()
        self.library_path = Path(library_path)
        self.db_path = db_path
        self.audio_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.wav', '.wma', '.aac'}
        self._is_cancelled = False

    def cancel(self):
        """Cancelar importación"""
        self._is_cancelled = True

    def extract_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extrae metadatos de un archivo de audio usando mutagen
        Retorna diccionario con metadatos o None si falla
        """
        try:
            audio = MutagenFile(str(file_path), easy=True)

            if audio is None:
                return None

            # Extraer metadatos comunes
            metadata = {
                'file_path': str(file_path),
                'title': None,
                'artists': None,
                'album': None,
                'genres': None,
                'year': None,
                'track_number': None,
                'duration_ms': None,
                'bitrate': None,
                'codec': None,
                'file_size': file_path.stat().st_size
            }

            # Title y Artist
            if hasattr(audio, 'tags') and audio.tags:
                # Usar easy tags si están disponibles
                if 'title' in audio:
                    title_raw = str(audio['title'][0]) if audio['title'] else None
                    metadata['title'] = title_raw
                if 'artist' in audio:
                    metadata['artists'] = str(audio['artist'][0]) if audio['artist'] else None

                if 'album' in audio:
                    metadata['album'] = str(audio['album'][0]) if audio['album'] else None
                if 'genre' in audio:
                    metadata['genres'] = str(audio['genres'][0]) if audio['genre'] else None
                if 'date' in audio:
                    try:
                        year_str = str(audio['date'][0])
                        metadata['year'] = int(year_str[:4]) if year_str else None
                    except (ValueError, IndexError):
                        pass
                if 'tracknumber' in audio:
                    try:
                        track_str = str(audio['tracknumber'][0])
                        # Manejar formato "1/10"
                        if '/' in track_str:
                            track_str = track_str.split('/')[0]
                        metadata['track_number'] = int(track_str)
                    except (ValueError, IndexError):
                        pass

            # Si no hay título, usar nombre del archivo
            if not metadata['title']:
                metadata['title'] = file_path.stem

            # SMART PARSING: Si no hay artista pero el título tiene formato "Artista - Canción", separarlos
            # Esto funciona tanto para tags ID3 como para nombres de archivo
            if metadata['title'] and not metadata['artists']:
                if ' - ' in metadata['title']:
                    parts = metadata['title'].split(' - ', 1)
                    if len(parts) == 2:
                        metadata['artists'] = parts[0].strip()
                        metadata['title'] = parts[1].strip()

            # Duration (en milisegundos)
            if hasattr(audio.info, 'length'):
                metadata['duration_ms'] = int(audio.info.length * 1000)

            # Bitrate
            if hasattr(audio.info, 'bitrate'):
                metadata['bitrate'] = audio.info.bitrate

            # Codec (determinar por extensión y tipo)
            ext = file_path.suffix.lower()
            if ext == '.mp3':
                metadata['codec'] = 'MP3'
            elif ext == '.flac':
                metadata['codec'] = 'FLAC'
            elif ext in ['.m4a', '.mp4']:
                metadata['codec'] = 'AAC'
            elif ext == '.ogg':
                metadata['codec'] = 'Vorbis'
            elif ext == '.wav':
                metadata['codec'] = 'WAV'
            else:
                metadata['codec'] = ext[1:].upper()

            return metadata

        except Exception as e:
            # Error al leer archivo - retornar metadatos mínimos
            return {
                'file_path': str(file_path),
                'title': file_path.stem,
                'file_size': file_path.stat().st_size,
                'error': str(e)
            }

    def run(self):
        """Escanear carpeta e importar archivos"""
        try:
            self.progress_update.emit(0, "Iniciando escaneo...")

            # Conectar a base de datos
            db = MusicDatabaseManager(self.db_path)

            # Encontrar todos los archivos de audio
            self.progress_update.emit(5, "Buscando archivos de audio...")
            audio_files = []

            for ext in self.audio_extensions:
                audio_files.extend(self.library_path.rglob(f'*{ext}'))

            total_files = len(audio_files)

            if total_files == 0:
                self.import_complete.emit(0, 0)
                return

            self.progress_update.emit(10, f"Encontrados {total_files:,} archivos")

            # Importar archivos
            imported_count = 0
            error_count = 0

            for i, file_path in enumerate(audio_files):
                if self._is_cancelled:
                    self.progress_update.emit(100, "Importación cancelada")
                    return

                # Calcular progreso (10-95%)
                progress = 10 + int((i / total_files) * 85)

                # Extraer metadatos
                metadata = self.extract_metadata(file_path)

                if metadata and 'error' not in metadata:
                    try:
                        # Importar a base de datos
                        db.add_song(
                            file_path=metadata['file_path'],
                            title=metadata['title'],
                            artists=metadata.get('artists'),
                            album=metadata.get('album'),
                            genres=metadata.get('genres'),
                            year=metadata.get('year'),
                            track_number=metadata.get('track_number'),
                            duration_ms=metadata.get('duration_ms'),
                            bitrate=metadata.get('bitrate'),
                            codec=metadata.get('codec'),
                            file_size=metadata.get('file_size'),
                            commit=False  # Commit en lote cada 100
                        )

                        imported_count += 1
                        self.file_processed.emit(str(file_path), True)

                        # Commit cada 100 archivos para mejor performance
                        if imported_count % 100 == 0:
                            db.conn.commit()
                            self.progress_update.emit(
                                progress,
                                f"Importados: {imported_count:,}/{total_files:,}"
                            )

                    except Exception as e:
                        error_count += 1
                        self.file_processed.emit(str(file_path), False)
                else:
                    error_count += 1
                    self.file_processed.emit(str(file_path), False)

            # Commit final
            db.conn.commit()

            # Completado
            self.progress_update.emit(100, f"Importación completa: {imported_count:,} archivos")
            self.import_complete.emit(imported_count, error_count)

            db.close()

        except Exception as e:
            self.error_occurred.emit(f"Error durante importación: {str(e)}")
