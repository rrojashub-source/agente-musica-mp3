#!/usr/bin/env python3
"""
Debug duplicates detection

Analyze database to find potential duplicates and show similarity scores

Created: November 18, 2025
"""
import sys
import sqlite3
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher


def calculate_similarity(song1, song2):
    """Calculate similarity score between two songs"""
    # Title similarity (50% weight)
    title1 = song1.get('title', '').lower()
    title2 = song2.get('title', '').lower()
    title_sim = SequenceMatcher(None, title1, title2).ratio()

    # Artist similarity (30% weight)
    artist1 = song1.get('artist', '').lower()
    artist2 = song2.get('artist', '').lower()
    artist_sim = SequenceMatcher(None, artist1, artist2).ratio()

    # Duration similarity (20% weight) - ±3 seconds tolerance
    duration1 = song1.get('duration', 0)
    duration2 = song2.get('duration', 0)
    duration_diff = abs(duration1 - duration2)

    if duration_diff <= 3:
        duration_sim = 1.0
    elif duration_diff <= 10:
        duration_sim = 0.5
    else:
        duration_sim = 0.0

    # Weighted average
    similarity = (title_sim * 0.5) + (artist_sim * 0.3) + (duration_sim * 0.2)

    return similarity, title_sim, artist_sim, duration_sim


def find_exact_title_matches(songs):
    """Find songs with exact same title (case-insensitive)"""
    title_groups = defaultdict(list)

    for song in songs:
        title_lower = song.get('title', '').lower().strip()
        if title_lower:
            title_groups[title_lower].append(song)

    # Filter groups with duplicates
    duplicates = {title: songs_list for title, songs_list in title_groups.items() if len(songs_list) > 1}

    return duplicates


def find_exact_title_artist_matches(songs):
    """Find songs with exact same title + artist"""
    key_groups = defaultdict(list)

    for song in songs:
        title = song.get('title', '').lower().strip()
        artist = song.get('artist', '').lower().strip()
        key = f"{title}||{artist}"
        if title and artist:
            key_groups[key].append(song)

    # Filter groups with duplicates
    duplicates = {key: songs_list for key, songs_list in key_groups.items() if len(songs_list) > 1}

    return duplicates


def main():
    print("=" * 80)
    print("🔍 DEBUG DUPLICATES DETECTION")
    print("=" * 80)
    print()

    # Connect to database directly (avoid WAL mode issues in WSL)
    conn = sqlite3.connect('music_library.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all songs
    cursor.execute("SELECT * FROM songs")
    rows = cursor.fetchall()
    songs = [dict(row) for row in rows]

    print(f"Total songs in library: {len(songs)}")
    print()

    # === METHOD 1: Exact Title Matches ===
    print("=" * 80)
    print("METHOD 1: EXACT TITLE MATCHES (case-insensitive)")
    print("=" * 80)
    print()

    title_duplicates = find_exact_title_matches(songs)

    if title_duplicates:
        print(f"Found {len(title_duplicates)} groups with duplicate titles:\n")

        for i, (title, songs_list) in enumerate(title_duplicates.items(), 1):
            print(f"Group {i}: \"{title}\" ({len(songs_list)} songs)")
            for song in songs_list:
                artist = song.get('artist', 'Unknown')
                duration = song.get('duration', 0)
                file_path = song.get('file_path', '')
                print(f"  [{song['id']}] {artist} - {duration}s")
                print(f"      Path: {file_path}")
            print()
    else:
        print("✅ No duplicate titles found")
        print()

    # === METHOD 2: Exact Title + Artist Matches ===
    print("=" * 80)
    print("METHOD 2: EXACT TITLE + ARTIST MATCHES")
    print("=" * 80)
    print()

    title_artist_duplicates = find_exact_title_artist_matches(songs)

    if title_artist_duplicates:
        print(f"Found {len(title_artist_duplicates)} groups with duplicate title+artist:\n")

        for i, (key, songs_list) in enumerate(title_artist_duplicates.items(), 1):
            title, artist = key.split('||')
            print(f"Group {i}: \"{title}\" by {artist} ({len(songs_list)} songs)")
            for song in songs_list:
                duration = song.get('duration', 0)
                bitrate = song.get('bitrate', 0)
                file_path = song.get('file_path', '')
                print(f"  [{song['id']}] {duration}s @ {bitrate} kbps")
                print(f"      Path: {file_path}")
            print()
    else:
        print("✅ No duplicate title+artist combinations found")
        print()

    # === METHOD 3: Fuzzy Matching Analysis ===
    print("=" * 80)
    print("METHOD 3: FUZZY MATCHING ANALYSIS (threshold: 0.85)")
    print("=" * 80)
    print()

    high_similarity_pairs = []

    for i, song1 in enumerate(songs):
        for song2 in songs[i + 1:]:
            similarity, title_sim, artist_sim, duration_sim = calculate_similarity(song1, song2)

            # Show pairs with high similarity (>= 0.70)
            if similarity >= 0.70:
                high_similarity_pairs.append({
                    'song1': song1,
                    'song2': song2,
                    'similarity': similarity,
                    'title_sim': title_sim,
                    'artist_sim': artist_sim,
                    'duration_sim': duration_sim
                })

    if high_similarity_pairs:
        # Sort by similarity (highest first)
        high_similarity_pairs.sort(key=lambda x: x['similarity'], reverse=True)

        print(f"Found {len(high_similarity_pairs)} high similarity pairs (>= 0.70):\n")

        for i, pair in enumerate(high_similarity_pairs[:20], 1):  # Show top 20
            song1 = pair['song1']
            song2 = pair['song2']
            sim = pair['similarity']
            t_sim = pair['title_sim']
            a_sim = pair['artist_sim']
            d_sim = pair['duration_sim']

            threshold_status = "✅ DETECTED" if sim >= 0.85 else "❌ NOT DETECTED"

            print(f"Pair {i}: Similarity = {sim:.2%} {threshold_status}")
            print(f"  Song 1 [{song1['id']}]: {song1.get('title', '')} - {song1.get('artist', '')}")
            print(f"  Song 2 [{song2['id']}]: {song2.get('title', '')} - {song2.get('artist', '')}")
            print(f"  Breakdown: Title={t_sim:.2%}, Artist={a_sim:.2%}, Duration={d_sim:.2%}")
            print()

        if len(high_similarity_pairs) > 20:
            print(f"... and {len(high_similarity_pairs) - 20} more pairs")
            print()

    else:
        print("✅ No high similarity pairs found")
        print()

    # === SUMMARY ===
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Exact title duplicates: {len(title_duplicates)} groups")
    print(f"Exact title+artist duplicates: {len(title_artist_duplicates)} groups")
    print(f"High similarity pairs (>= 0.70): {len(high_similarity_pairs)} pairs")
    print(f"  - Above threshold (>= 0.85): {sum(1 for p in high_similarity_pairs if p['similarity'] >= 0.85)}")
    print(f"  - Below threshold (0.70-0.84): {sum(1 for p in high_similarity_pairs if p['similarity'] < 0.85)}")
    print()

    conn.close()


if __name__ == '__main__':
    main()
