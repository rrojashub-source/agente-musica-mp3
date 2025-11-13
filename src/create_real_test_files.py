#!/usr/bin/env python3
"""
Copiar archivos MP3 REALES de Bruno Mars y renombrarlos con 23 patrones
Para testear robustez con archivos válidos
"""

import shutil
from pathlib import Path

# Directorio origen (Bruno Mars)
source_dir = Path("/mnt/c/Users/ricar/Music/Bruno Mars")

# Directorio destino
test_dir = Path("test_files_robustez_real")
test_dir.mkdir(exist_ok=True)

# Buscar archivos MP3 en carpeta Bruno Mars
source_files = list(source_dir.glob("*.mp3"))

if len(source_files) == 0:
    print(f"❌ No se encontraron archivos MP3 en {source_dir}")
    exit(1)

print(f"✅ Encontrados {len(source_files)} archivos MP3 en carpeta Bruno Mars")
print(f"Vamos a usar los primeros 24 para crear tests con 23 patrones\n")

# Nombres de archivo de prueba (23 patrones + edge cases)
test_patterns = [
    # === TRACK NUMBERS (4 patrones) ===
    "01 - The Beatles - Hey Jude.mp3",
    "Track 02 - Pink Floyd - Comfortably Numb.mp3",
    "03. Led Zeppelin - Stairway to Heaven.mp3",
    "Queen - 04 - Bohemian Rhapsody.mp3",

    # === AÑOS (2 patrones) ===
    "Nirvana - Smells Like Teen Spirit (1991).mp3",
    "Radiohead - Creep [1992].mp3",

    # === FEATURING (2 patrones) ===
    "Jay-Z feat. Alicia Keys - Empire State of Mind.mp3",
    "Eminem & Rihanna - Love The Way You Lie.mp3",

    # === REMIX/VERSIONES (3 patrones) ===
    "Daft Punk - Get Lucky (Remix).mp3",
    "Calvin Harris - Summer [Radio Edit].mp3",
    "Coldplay - Fix You (Live).mp3",

    # === BÁSICOS (6 patrones - sin slash) ===
    "The Rolling Stones - Paint It Black.mp3",
    "David_Bowie_Space_Oddity.mp3",
    "Wonderwall (Oasis).mp3",
    "Bob Dylan ~ Blowin' in the Wind.mp3",
    "The Doors | Riders on the Storm.mp3",

    # === OLDSCHOOL (2 patrones) ===
    "Metallica-EnterSandman.mp3",
    "GreenDayBasketCase.mp3",

    # === EDGE CASES (5 adicionales) ===
    "01-Guns N' Roses-Sweet Child O' Mine.mp3",
    "The Who - Won't Get Fooled Again.mp3",
    "Björk - Hyperballad.mp3",
    "R.E.M. - Losing My Religion.mp3",
    "2Pac - California Love.mp3",
]

# Copiar y renombrar
copied = 0
for i, pattern_name in enumerate(test_patterns):
    if i >= len(source_files):
        print(f"⚠️  Solo había {len(source_files)} archivos, copiados todos")
        break

    source_file = source_files[i]
    dest_file = test_dir / pattern_name

    # Copiar archivo
    shutil.copy2(source_file, dest_file)
    print(f"✅ {pattern_name}")
    copied += 1

print(f"\n🎯 Total: {copied} archivos MP3 REALES copiados y renombrados")
print(f"📁 Directorio: {test_dir.absolute()}")
print("\n🧪 Ahora escanea esta carpeta en Cleanup Assistant")
print("   Debería detectar ~23-24 problemas (tags vacíos pero filename con patrón)")
