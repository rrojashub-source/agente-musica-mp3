#!/usr/bin/env python3
"""
Script para crear archivos MP3 de prueba con 23 formatos de nombre diferentes
Para testear robustez del PatternDetector
"""

import os
from pathlib import Path

# Directorio de salida
test_dir = Path("test_files_robustez")
test_dir.mkdir(exist_ok=True)

# Lista de nombres de archivo de prueba (23 patrones)
test_files = [
    # === TRACK NUMBERS (4 patrones) ===
    "01 - The Beatles - Hey Jude.mp3",  # track_artist_title_dash
    "Track 02 - Pink Floyd - Comfortably Numb.mp3",  # track_word_artist_title
    "03. Led Zeppelin - Stairway to Heaven.mp3",  # track_dot_artist_title
    "Queen - 04 - Bohemian Rhapsody.mp3",  # artist_track_title

    # === AÑOS (2 patrones) ===
    "Nirvana - Smells Like Teen Spirit (1991).mp3",  # artist_title_year
    "Radiohead - Creep [1992].mp3",  # artist_title_year_bracket

    # === FEATURING (2 patrones) ===
    "Jay-Z feat. Alicia Keys - Empire State of Mind.mp3",  # artist_feat_title
    "Eminem & Rihanna - Love The Way You Lie.mp3",  # artist_and_title

    # === REMIX/VERSIONES (3 patrones) ===
    "Daft Punk - Get Lucky (Remix).mp3",  # artist_title_remix
    "Calvin Harris - Summer [Radio Edit].mp3",  # artist_title_edit
    "Coldplay - Fix You (Live).mp3",  # artist_title_live

    # === BÁSICOS (7 patrones) ===
    "The Rolling Stones - Paint It Black.mp3",  # artist_title_dash (COMÚN)
    "David_Bowie_Space_Oddity.mp3",  # artist_title_underscore
    "ACDC-Highway to Hell.mp3",  # artist_title_slash simulado (/ causa problemas filesystem)
    "Wonderwall (Oasis).mp3",  # title_artist_parenthesis (INVERTIDO)
    "Bob Dylan ~ Blowin' in the Wind.mp3",  # artist_title_tilde
    "The Doors | Riders on the Storm.mp3",  # artist_title_pipe

    # === OLDSCHOOL (2 patrones) ===
    "Metallica-EnterSandman.mp3",  # artist_title_dash_nospace
    "GreenDayBasketCase.mp3",  # artist_title_camelcase

    # === EDGE CASES ADICIONALES ===
    "01-Guns N' Roses-Sweet Child O' Mine.mp3",  # Sin espacios después separadores
    "The Who - Won't Get Fooled Again.mp3",  # Apóstrofes
    "Björk - Hyperballad.mp3",  # Caracteres especiales
    "R.E.M. - Losing My Religion.mp3",  # Puntos en nombre artista
    "2Pac - California Love.mp3",  # Número al inicio del artista
]

print(f"Creando {len(test_files)} archivos de prueba en {test_dir}...\n")

# Crear archivos MP3 mínimos (header MP3 válido de 144 bytes)
# ID3v2 header mínimo + frame MPEG vacío
mp3_minimal_header = bytes([
    # ID3v2 header (10 bytes)
    0x49, 0x44, 0x33,  # "ID3"
    0x03, 0x00,        # Version 2.3.0
    0x00,              # Flags
    0x00, 0x00, 0x00, 0x00,  # Size (0)
]) + bytes(134)  # Padding para 144 bytes totales

for filename in test_files:
    filepath = test_dir / filename

    # Escribir archivo MP3 mínimo
    with open(filepath, 'wb') as f:
        f.write(mp3_minimal_header)

    print(f"✅ {filename}")

print(f"\n🎯 Total: {len(test_files)} archivos creados")
print(f"📁 Directorio: {test_dir.absolute()}")
print("\n🧪 Ahora puedes escanear esta carpeta en el Cleanup Assistant para validar los 23 patrones")
