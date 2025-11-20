"""
Duplicate Detector - Phase 5.1

Detect duplicate songs using multiple methods:
- Method 1: Metadata comparison (fuzzy string matching)
- Method 2: Audio fingerprinting (acoustid/chromaprint)
- Method 3: File size comparison (quick pre-filter)

Created: November 13, 2025
Updated: November 19, 2025 (Fixed fpcalc path passing)
"""
import logging
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from collections import defaultdict
import os

from utils.fpcalc_checker import FpcalcChecker

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Detect duplicate songs using multiple detection methods

    Usage:
        detector = DuplicateDetector(db_manager)
        duplicates = detector.scan_library(method='metadata')

        # Result format:
        [
            {
                'songs': [song1_dict, song2_dict],  # Sorted by quality (highest first)
                'confidence': 0.95,  # Similarity score (0.0-1.0)
                'method': 'metadata'
            },
            ...
        ]
    """

    def __init__(self, db_manager, similarity_threshold=0.85):
        """
        Initialize duplicate detector

        Args:
            db_manager: Database manager instance
            similarity_threshold: Minimum similarity for fuzzy matching (0.0-1.0)
        """
        self.db = db_manager
        self.similarity_threshold = similarity_threshold

        # Initialize fpcalc checker for audio fingerprinting
        self.fpcalc_checker = FpcalcChecker()
        if self.fpcalc_checker.is_available():
            logger.info(f"DuplicateDetector initialized (threshold: {similarity_threshold}, fpcalc: {self.fpcalc_checker.fpcalc_path})")
        else:
            logger.info(f"DuplicateDetector initialized (threshold: {similarity_threshold}, fpcalc: NOT AVAILABLE)")

    def scan_library(self, method='metadata') -> List[Dict]:
        """
        Scan entire library for duplicates

        Args:
            method: Detection method ('metadata', 'fingerprint', or 'filesize')

        Returns:
            List of duplicate groups, each containing:
            - songs: List of duplicate songs (sorted by quality)
            - confidence: Similarity score
            - method: Detection method used
        """
        if method == 'metadata':
            return self.detect_by_metadata()
        elif method == 'fingerprint':
            return self.detect_by_fingerprint()
        elif method == 'filesize':
            return self.detect_by_filesize()
        else:
            logger.error(f"Unknown detection method: {method}")
            return []

    def detect_by_metadata(self) -> List[Dict]:
        """
        Detect duplicates by comparing metadata (title, artist, duration)

        Uses fuzzy string matching for title/artist comparison.
        Duration tolerance: ±3 seconds

        Returns:
            List of duplicate groups
        """
        songs = self.db.get_all_songs()

        if len(songs) == 0:
            logger.info("Empty library - no duplicates")
            return []

        if len(songs) == 1:
            logger.info("Single song - no duplicates")
            return []

        duplicate_groups = []
        processed = set()

        # Compare each song with every other song
        for i, song1 in enumerate(songs):
            if song1['id'] in processed:
                continue

            duplicates = [song1]

            for j, song2 in enumerate(songs[i + 1:], start=i + 1):
                if song2['id'] in processed:
                    continue

                # Calculate similarity
                similarity = self._calculate_metadata_similarity(song1, song2)

                if similarity >= self.similarity_threshold:
                    duplicates.append(song2)
                    processed.add(song2['id'])

            # If found duplicates (more than original song)
            if len(duplicates) > 1:
                processed.add(song1['id'])

                # Sort by quality (bitrate)
                sorted_duplicates = self._sort_by_quality(duplicates)

                duplicate_groups.append({
                    'songs': sorted_duplicates,
                    'confidence': similarity,
                    'method': 'metadata'
                })

        logger.info(f"Metadata detection: Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups

    def detect_by_fingerprint(self) -> List[Dict]:
        """
        Detect duplicates using audio fingerprinting

        Uses acoustid/chromaprint for audio signature comparison.
        High accuracy (99%) but slower than metadata.

        Returns:
            List of duplicate groups
        """
        songs = self.db.get_all_songs()

        if len(songs) == 0:
            return []

        # Generate fingerprints for all songs
        fingerprints = {}
        for song in songs:
            try:
                fp = self._generate_fingerprint(song['file_path'])
                if fp:
                    fingerprints[song['id']] = fp
            except Exception as e:
                logger.warning(f"Failed to generate fingerprint for {song['file_path']}: {e}")
                continue

        # Group songs by fingerprint
        fp_groups = defaultdict(list)
        for song in songs:
            if song['id'] in fingerprints:
                fp = fingerprints[song['id']]
                fp_groups[fp].append(song)

        # Build duplicate groups
        duplicate_groups = []
        for fp, songs_list in fp_groups.items():
            if len(songs_list) > 1:
                sorted_songs = self._sort_by_quality(songs_list)
                duplicate_groups.append({
                    'songs': sorted_songs,
                    'confidence': 0.99,  # Fingerprint is highly accurate
                    'method': 'fingerprint'
                })

        logger.info(f"Fingerprint detection: Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups

    def detect_by_filesize(self) -> List[Dict]:
        """
        Detect duplicates by comparing file sizes

        Quick pre-filter method. Same song + bitrate = same file size.
        Less accurate (70%) but very fast.

        Returns:
            List of duplicate groups
        """
        songs = self.db.get_all_songs()

        if len(songs) == 0:
            return []

        # Group songs by file size
        size_groups = defaultdict(list)

        for song in songs:
            try:
                file_path = song['file_path']
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    size_groups[size].append(song)
            except Exception as e:
                logger.warning(f"Failed to get file size for {song['file_path']}: {e}")
                continue

        # Build duplicate groups
        duplicate_groups = []
        for size, songs_list in size_groups.items():
            if len(songs_list) > 1:
                sorted_songs = self._sort_by_quality(songs_list)
                duplicate_groups.append({
                    'songs': sorted_songs,
                    'confidence': 0.70,  # File size is less reliable
                    'method': 'filesize'
                })

        logger.info(f"File size detection: Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups

    def _calculate_metadata_similarity(self, song1: Dict, song2: Dict) -> float:
        """
        Calculate similarity score between two songs based on metadata

        Args:
            song1, song2: Song dictionaries

        Returns:
            Similarity score (0.0 - 1.0)
        """
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

        return similarity

    def _generate_fingerprint(self, file_path: str) -> Optional[str]:
        """
        Generate audio fingerprint for a file

        Args:
            file_path: Path to audio file

        Returns:
            Fingerprint string or None if failed

        Note: Requires acoustid library and fpcalc binary
        """
        if not os.path.exists(file_path):
            return None

        # Check if fpcalc is available
        if not self.fpcalc_checker.is_available():
            logger.warning("fpcalc not found - fingerprint detection unavailable")
            return None

        try:
            import acoustid

            # CRITICAL: acoustid.fingerprint_file() doesn't accept fpcalc parameter
            # Instead, it reads from FPCALC environment variable
            # Set it temporarily for this call
            old_fpcalc = os.environ.get('FPCALC')
            os.environ['FPCALC'] = self.fpcalc_checker.fpcalc_path

            try:
                duration, fingerprint = acoustid.fingerprint_file(file_path)
                return fingerprint
            finally:
                # Restore original environment variable
                if old_fpcalc is not None:
                    os.environ['FPCALC'] = old_fpcalc
                else:
                    os.environ.pop('FPCALC', None)

        except ImportError:
            logger.warning("acoustid not installed - fingerprint detection unavailable")
            return None
        except Exception as e:
            logger.warning(f"Failed to generate fingerprint: {e}")
            return None

    def _sort_by_quality(self, songs: List[Dict]) -> List[Dict]:
        """
        Sort songs by quality (highest bitrate first)

        Args:
            songs: List of song dictionaries

        Returns:
            Sorted list (highest quality first)
        """
        return sorted(songs, key=lambda s: s.get('bitrate', 0), reverse=True)
