#!/usr/bin/env python3
"""
Versión Simplificada del Agente AI para Descarga de MP3
Sin dependencias de OpenAI - Funciona directamente
VERSIÓN CORREGIDA SIN ERRORES DE EMOJIS
"""

import sys
import os
import pandas as pd
import yt_dlp
from pathlib import Path
from typing import Dict, List
import time
import logging
from datetime import datetime

# Configurar logging sin emojis para evitar errores de codificación
class SafeFormatter(logging.Formatter):
    def format(self, record):
        # Remover emojis del mensaje si los hay
        if hasattr(record, 'msg'):
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
        return super().format(record)

# Configurar logging seguro
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler para archivo (soporta UTF-8)
file_handler = logging.FileHandler(
    log_dir / f'download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Handler para consola (ASCII seguro)
console_handler = logging.StreamHandler()
console_handler.setFormatter(SafeFormatter('%(asctime)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

class SimpleMusicDownloader:
    """Descargador de música simplificado sin CrewAI"""
    
    def __init__(self, output_dir="downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuración de yt-dlp
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.output_dir / '%(uploader)s - %(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ignoreerrors': True,
            'no_warnings': False,
            'extractaudio': True,
            'audioformat': 'mp3',
            'socket_timeout': 300,
            'retries': 3,
            'fragment_retries': 3,
        }
        
        # Estadísticas
        self.stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
    
    def read_excel(self, excel_path: str) -> List[Dict]:
        """Leer archivo Excel y adaptarlo a nuestro formato"""
        try:
            logger.info(f"[EXCEL] Leyendo archivo Excel: {excel_path}")
            
            # Leer Excel
            df = pd.read_excel(excel_path)
            
            # Mostrar columnas encontradas
            logger.info(f"[EXCEL] Columnas encontradas: {df.columns.tolist()}")
            
            # Mapear columnas (maneja espacios y variaciones)
            column_mapping = {}
            
            for col in df.columns:
                col_clean = col.strip().lower()
                if 'autor' in col_clean or 'artist' in col_clean:
                    column_mapping['Artist'] = col
                elif 'cancion' in col_clean or 'canción' in col_clean or 'song' in col_clean:
                    column_mapping['Song'] = col
                elif 'link' in col_clean or 'url' in col_clean:
                    column_mapping['URL'] = col
            
            logger.info(f"[EXCEL] Mapeo de columnas: {column_mapping}")
            
            # Validar que tenemos las columnas necesarias
            if 'Artist' not in column_mapping or 'Song' not in column_mapping:
                raise ValueError("No se encontraron las columnas de Artista y Canción")
            
            # Convertir a formato estándar
            songs = []
            for _, row in df.iterrows():
                song_data = {
                    'Artist': str(row[column_mapping['Artist']]).strip(),
                    'Song': str(row[column_mapping['Song']]).strip(),
                    'URL': str(row[column_mapping.get('URL', '')]).strip() if 'URL' in column_mapping else ''
                }
                
                # Limpiar URLs
                if song_data['URL'] and song_data['URL'] != 'nan':
                    # Limpiar URLs de YouTube de parámetros innecesarios
                    url = song_data['URL']
                    if 'youtube.com' in url and 'watch?v=' in url:
                        # Extraer solo la parte esencial de la URL
                        import re
                        match = re.search(r'v=([a-zA-Z0-9_-]{11})', url)
                        if match:
                            video_id = match.group(1)
                            song_data['URL'] = f"https://www.youtube.com/watch?v={video_id}"
                
                # Crear query de búsqueda si no hay URL
                if not song_data['URL'] or song_data['URL'] == 'nan':
                    song_data['Search_Query'] = f"{song_data['Artist']} - {song_data['Song']}"
                else:
                    song_data['Search_Query'] = song_data['URL']
                
                songs.append(song_data)
            
            logger.info(f"[EXCEL] Procesadas {len(songs)} canciones desde Excel")
            return songs
            
        except Exception as e:
            logger.error(f"[ERROR] Error leyendo Excel: {str(e)}")
            raise
    
    def download_song(self, song_data: Dict) -> Dict:
        """Descargar una canción individual"""
        artist = song_data['Artist']
        song = song_data['Song']
        query = song_data['Search_Query']
        
        logger.info(f"[DOWNLOAD] Descargando: {artist} - {song}")
        
        try:
            # Si tenemos URL directa, usar esa; sino buscar
            if query.startswith('http'):
                download_url = query
                logger.info(f"[DOWNLOAD] URL directa: {download_url}")
            else:
                download_url = f"ytsearch1:{query}"
                logger.info(f"[DOWNLOAD] Buscando: {query}")
            
            # Configurar nombre de archivo personalizado
            safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_song = "".join(c for c in song if c.isalnum() or c in (' ', '-', '_')).strip()
            
            custom_opts = self.ydl_opts.copy()
            custom_opts['outtmpl'] = str(self.output_dir / f'{safe_artist} - {safe_song}.%(ext)s')
            
            # Descargar
            with yt_dlp.YoutubeDL(custom_opts) as ydl:
                ydl.download([download_url])
            
            # Buscar archivo descargado
            possible_files = list(self.output_dir.glob(f"{safe_artist} - {safe_song}.*"))
            downloaded_file = possible_files[0] if possible_files else None
            
            result = {
                'status': 'success',
                'artist': artist,
                'song': song,
                'file': str(downloaded_file) if downloaded_file else None,
                'message': f"[SUCCESS] Descarga exitosa: {artist} - {song}"
            }
            
            logger.info(result['message'])
            self.stats['successful'] += 1
            return result
            
        except Exception as e:
            error_msg = f"[ERROR] Error descargando {artist} - {song}: {str(e)}"
            logger.error(error_msg)
            
            result = {
                'status': 'error',
                'artist': artist,
                'song': song,
                'file': None,
                'error': str(e),
                'message': error_msg
            }
            
            self.stats['failed'] += 1
            self.stats['errors'].append(error_msg)
            return result
    
    def download_batch(self, songs: List[Dict]) -> Dict:
        """Descargar todas las canciones"""
        logger.info(f"[BATCH] Iniciando descarga de {len(songs)} canciones")
        
        self.stats['total'] = len(songs)
        results = []
        
        for i, song_data in enumerate(songs, 1):
            logger.info(f"[PROGRESS] Progreso: {i}/{len(songs)}")
            
            result = self.download_song(song_data)
            results.append(result)
            
            # Pausa entre descargas para evitar rate limiting
            if i < len(songs):
                time.sleep(2)
        
        # Generar reporte final
        success_rate = (self.stats['successful'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        
        final_result = {
            'status': 'completed',
            'total_songs': self.stats['total'],
            'successful': self.stats['successful'],
            'failed': self.stats['failed'],
            'success_rate': f"{success_rate:.1f}%",
            'results': results,
            'download_dir': str(self.output_dir),
            'errors': self.stats['errors']
        }
        
        return final_result
    
    def organize_files(self):
        """Organizar archivos por artista"""
        logger.info("[ORGANIZE] Organizando archivos por artista...")
        
        try:
            mp3_files = list(self.output_dir.glob("*.mp3"))
            organized = 0
            
            for mp3_file in mp3_files:
                # Extraer artista del nombre del archivo
                filename = mp3_file.stem
                if ' - ' in filename:
                    artist = filename.split(' - ')[0].strip()
                    
                    # Crear directorio del artista
                    artist_dir = self.output_dir / artist
                    artist_dir.mkdir(exist_ok=True)
                    
                    # Mover archivo
                    new_path = artist_dir / mp3_file.name
                    if not new_path.exists():
                        mp3_file.rename(new_path)
                        organized += 1
                        logger.info(f"[ORGANIZE] Movido: {mp3_file.name} -> {artist}/")
            
            logger.info(f"[ORGANIZE] Organizados {organized} archivos por artista")
            
        except Exception as e:
            logger.error(f"[ERROR] Error organizando archivos: {str(e)}")

def main():
    """Función principal"""
    if len(sys.argv) != 2:
        print("ERROR: Uso: python agente_musica.py archivo.xlsx")
        return False
    
    excel_file = sys.argv[1]
    
    print("=" * 60)
    print("🎵 AGENTE AI - DESCARGA DE MUSICA DESDE YOUTUBE 🎵")
    print("=" * 60)
    print(f"Archivo Excel: {excel_file}")
    print("=" * 60)
    
    try:
        # Crear directorios
        Path("logs").mkdir(exist_ok=True)
        
        # Inicializar descargador
        downloader = SimpleMusicDownloader()
        
        # Leer Excel
        songs = downloader.read_excel(excel_file)
        
        # Confirmar antes de descargar
        print(f"\nSe encontraron {len(songs)} canciones:")
        for i, song in enumerate(songs[:5], 1):  # Mostrar solo las primeras 5
            print(f"  {i}. {song['Artist']} - {song['Song']}")
        
        if len(songs) > 5:
            print(f"  ... y {len(songs) - 5} mas")
        
        print(f"\nDirectorio de descarga: {downloader.output_dir}")
        
        # Preguntar confirmación
        confirm = input(f"\nProceder con la descarga de {len(songs)} canciones? (s/n): ").lower()
        if confirm != 's':
            print("Descarga cancelada por el usuario")
            return False
        
        # Descargar
        result = downloader.download_batch(songs)
        
        # Organizar archivos
        downloader.organize_files()
        
        # Mostrar reporte final
        print("\n" + "=" * 60)
        print("🎯 REPORTE FINAL")
        print("=" * 60)
        print(f"Total de canciones: {result['total_songs']}")
        print(f"Descargas exitosas: {result['successful']}")
        print(f"Descargas fallidas: {result['failed']}")
        print(f"Tasa de exito: {result['success_rate']}")
        print(f"Ubicacion: {result['download_dir']}")
        
        if result['errors']:
            print(f"\nErrores encontrados ({len(result['errors'])}):")
            for error in result['errors'][:3]:  # Mostrar solo los primeros 3
                print(f"  - {error}")
            if len(result['errors']) > 3:
                print(f"  ... y {len(result['errors']) - 3} errores mas (ver logs)")
        
        print("=" * 60)
        
        if result['successful'] > 0:
            print("🎉 Descarga completada! Revisa tu carpeta de descargas.")
        else:
            print("😞 No se pudo descargar ninguna cancion. Revisa los logs.")
        
        return result['successful'] > 0
        
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        print(f"\nError fatal: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nProceso cancelado por el usuario")
        sys.exit(1)
