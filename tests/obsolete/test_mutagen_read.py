#!/usr/bin/env python3
"""Test rápido: qué lee mutagen de nuestros MP3 de prueba"""

from mutagen import File as MutagenFile
from pathlib import Path

test_file = Path("test_files_robustez/01 - The Beatles - Hey Jude.mp3")

print(f"Analizando: {test_file}")
print("=" * 60)

audio = MutagenFile(str(test_file), easy=True)

print(f"audio object: {audio}")
print(f"audio is None: {audio is None}")

if audio:
    print(f"\nhasattr tags: {hasattr(audio, 'tags')}")
    print(f"audio.tags: {audio.tags if hasattr(audio, 'tags') else 'N/A'}")

    if hasattr(audio, 'tags') and audio.tags:
        print("\n'title' in audio:", 'title' in audio)
        print("'artist' in audio:", 'artist' in audio)

        if 'title' in audio:
            print(f"  audio['title']: {audio['title']}")
        if 'artist' in audio:
            print(f"  audio['artist']: {audio['artist']}")
    else:
        print("\n❌ audio.tags está vacío o None")

print("\n" + "=" * 60)
print("CONCLUSIÓN:")

title_tag = None
artist_tag = None

if hasattr(audio, 'tags') and audio.tags:
    if 'title' in audio:
        title_tag = str(audio['title'][0]) if audio['title'] else None
    if 'artist' in audio:
        artist_tag = str(audio['artist'][0]) if audio['artist'] else None

print(f"title_tag = {repr(title_tag)}")
print(f"artist_tag = {repr(artist_tag)}")
print(f"\nCondición 'not title_tag and not artist_tag': {not title_tag and not artist_tag}")
print("^ Esto debería ser True para detectar el problema")
