#!/usr/bin/env python3
"""
🤖 AGENTE AI FINAL - BÚSQUEDA COMPLETA CORREGIDA
"""

import requests
import pandas as pd
import yt_dlp
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteFinal:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def buscar_discografia_completa(self, artista):
        logger.info(f"🔍 Buscando discografía de: {artista}")
        canciones = []
        
        try:
            canciones.extend(self._buscar_musicbrainz(artista))
        except Exception as e:
            logger.warning(f"Error MusicBrainz: {e}")
        
        canciones_unicas = self._eliminar_duplicados(canciones)
        logger.info(f"✅ Encontradas {len(canciones_unicas)} canciones únicas")
        return canciones_unicas
    
    def _buscar_musicbrainz(self, artista):
        canciones = []
        url = "https://musicbrainz.org/ws/2/artist"
        params = {'query': artista, 'fmt': 'json', 'limit': 1}
        
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            return canciones
        
        artistas = response.json().get('artists', [])
        if not artistas:
            return canciones
        
        artist_id = artistas[0]['id']
        
        releases_url = "https://musicbrainz.org/ws/2/release"
        releases_params = {
            'artist': artist_id,
            'fmt': 'json',
            'limit': 100,
            'type': 'album|single'
        }
        
        releases_response = self.session.get(releases_url, params=releases_params)
        if releases_response.status_code == 200:
            releases = releases_response.json().get('releases', [])
            
            for release in releases[:20]:
                tracks = self._obtener_tracks(release['id'])
                
                for track in tracks:
                    canciones.append({
                        'Artist': artista,
                        'Song': track['title'],
                        'Album': release.get('title', ''),
                        'Year': release.get('date', '')[:4] if release.get('date') else '',
                        'URL': ''
                    })
                
                time.sleep(1)
        
        return canciones
    
    def _obtener_tracks(self, release_id):
        url = f"https://musicbrainz.org/ws/2/release/{release_id}"
        params = {'inc': 'recordings', 'fmt': 'json'}
        
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            return []
        
        data = response.json()
        tracks = []
        
        for medium in data.get('media', []):
            for track in medium.get('tracks', []):
                tracks.append({'title': track['title']})
        
        time.sleep(1)
        return tracks
    
    def buscar_urls_youtube(self, canciones):
        logger.info(f"🎥 Buscando URLs de YouTube para {len(canciones)} canciones...")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True
        }
        
        urls_encontradas = 0
        
        for i, cancion in enumerate(canciones):
            print(f"🔍 {i+1}/{len(canciones)}: {cancion['Artist']} - {cancion['Song']}")
            
            try:
                # SOLUCIÓN CORREGIDA: ytsearch1: prefix
                query = f"ytsearch1:{cancion['Artist']} {cancion['Song']}"
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    resultado = ydl.extract_info(query, download=False)
                    
                    if resultado and 'entries' in resultado and resultado['entries']:
                        entry = resultado['entries'][0]
                        if 'id' in entry:
                            video_id = entry['id']
                            url = f"https://www.youtube.com/watch?v={video_id}"
                            cancion['URL'] = url
                            urls_encontradas += 1
                            print(f"   ✅ URL encontrada")
                        else:
                            print(f"   ❌ Sin ID")
                    else:
                        print(f"   ❌ Sin resultados")
            
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            time.sleep(1.5)
        
        print(f"\n📊 URLs encontradas: {urls_encontradas}/{len(canciones)}")
        return canciones
    
    def _eliminar_duplicados(self, canciones):
        vistas = set()
        unicas = []
        
        for cancion in canciones:
            clave = (cancion['Artist'].lower(), cancion['Song'].lower())
            if clave not in vistas:
                vistas.add(clave)
                unicas.append(cancion)
        
        return unicas
    
    def guardar_excel(self, canciones, filename):
        df = pd.DataFrame(canciones)
        df.to_excel(filename, index=False)
        logger.info(f"✅ Guardado: {filename}")
        return filename

def main():
    print("🤖 AGENTE AI FINAL - TODO CORREGIDO")
    print("=" * 40)
    
    agente = AgenteFinal()
    
    artista = input("🎵 Artista: ").strip()
    if not artista:
        return
    
    # Buscar discografía
    canciones = agente.buscar_discografia_completa(artista)
    if not canciones:
        print("❌ Sin canciones")
        return
    
    print(f"✅ {len(canciones)} canciones encontradas")
    
    # Limitar para evitar bloqueos
    max_canciones = min(len(canciones), 50)
    if len(canciones) > 50:
        print(f"⚠️ Limitando a {max_canciones} para evitar bloqueos")
        canciones = canciones[:max_canciones]
    
    # Buscar URLs
    print(f"\n🎥 Buscando URLs...")
    canciones_con_urls = agente.buscar_urls_youtube(canciones)
    
    # Guardar
    filename = f"{artista.replace(' ', '_')}_FINAL.xlsx"
    agente.guardar_excel(canciones_con_urls, filename)
    
    urls_encontradas = sum(1 for c in canciones_con_urls if c['URL'])
    
    print(f"\n🎉 ¡COMPLETADO!")
    print(f"📊 Total: {len(canciones_con_urls)}")
    print(f"🎥 URLs: {urls_encontradas}")
    print(f"💾 Excel: {filename}")
    print(f"🚀 ¡Listo para descargar!")

if __name__ == "__main__":
    try:
        main()
        input("\nEnter para salir...")
    except KeyboardInterrupt:
        print("\n👋 Cancelado")
