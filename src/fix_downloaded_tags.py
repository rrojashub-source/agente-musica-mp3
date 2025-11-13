#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix tags for already downloaded files from YouTube playlists
Applies proper ID3 tags to MP3 files that have emoji separators
"""

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
from pathlib import Path
import re

def fix_tags_in_folder(folder_path):
    """Fix tags for all MP3 files in folder"""
    folder = Path(folder_path)
    mp3_files = list(folder.glob("*.mp3"))

    print(f"Found {len(mp3_files)} MP3 files")

    fixed_count = 0

    for mp3_file in mp3_files:
        try:
            filename = mp3_file.stem  # Without .mp3

            # Try to split by common emojis
            emoji_pattern = r'[💥💎🌊✨🔥📀🌟❤️🎶💿]'
            parts = re.split(emoji_pattern, filename)

            if len(parts) >= 2:
                artists_part = parts[0].strip()
                title_part = parts[1].strip()

                # Take first artist from comma-separated list
                first_artist = artists_part.split(',')[0].strip()

                print(f"\n  File: {mp3_file.name[:50]}...")
                print(f"  Artist: {first_artist}")
                print(f"  Title: {title_part}")

                # Write tags
                audio = MP3(str(mp3_file), ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()

                audio.tags['TPE1'] = TPE1(encoding=3, text=first_artist)
                audio.tags['TIT2'] = TIT2(encoding=3, text=title_part)

                # Album from title if contains "Billboard"
                if 'Billboard' in title_part:
                    audio.tags['TALB'] = TALB(encoding=3, text='Billboard Hot 100')
                elif 'Pop' in title_part:
                    audio.tags['TALB'] = TALB(encoding=3, text='Pop Songs 2025')

                # Year
                if '2025' in title_part:
                    audio.tags['TDRC'] = TDRC(encoding=3, text='2025')

                audio.save()
                fixed_count += 1
                print("  STATUS: Tags written")

        except Exception as e:
            print(f"  ERROR: {mp3_file.name}: {e}")

    print(f"\nSUMMARY: Fixed {fixed_count}/{len(mp3_files)} files")

if __name__ == "__main__":
    downloads_folder = Path.home() / "Music" / "NEXUS_Downloads"

    print("=" * 60)
    print("FIX DOWNLOADED TAGS")
    print("=" * 60)
    print(f"\nFolder: {downloads_folder}")
    print("")

    if downloads_folder.exists():
        fix_tags_in_folder(downloads_folder)
    else:
        print(f"ERROR: Folder not found: {downloads_folder}")
