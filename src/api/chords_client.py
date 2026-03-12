"""
Chords Client — Chord detection from audio files

Detects chords from MP3 files using librosa chromagram analysis.
No external API dependency — works 100% offline.

Features:
- Chromagram-based chord detection (librosa CQT)
- Major/minor/7th chord recognition
- In-memory + DB caching
- Chord transposition via pychord
- Deduplication of consecutive identical chords

Created: March 2026
"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ChordsClient:
    """
    Offline chord detection from audio files.

    Usage:
        client = ChordsClient(db_manager=db)
        chords = client.get_chords("/path/to/song.mp3", song_id=42)
        # Returns: [{"t": 0.0, "chord": "C"}, {"t": 2.5, "chord": "Am"}, ...]
    """

    # Chromagram note labels (C=0 ... B=11)
    CHROMA_LABELS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Analysis parameters
    HOP_LENGTH = 8192          # ~0.37s per frame at 22050Hz
    BLOCK_SECONDS = 4.0        # Group frames into 4-second blocks (smoother)
    SAMPLE_RATE = 22050        # Standard for analysis
    MIN_ENERGY = 0.01          # Skip silence

    def __init__(self, db_manager=None):
        """
        Initialize ChordsClient.

        Args:
            db_manager: DatabaseManager for caching chords in DB (optional)
        """
        self.db_manager = db_manager
        self._cache = {}  # {song_id: list[dict]}
        self._librosa = None
        self._np = None

        logger.info("ChordsClient initialized")

    def _ensure_libs(self):
        """Lazy-load heavy libraries (librosa, numpy)."""
        if self._librosa is None:
            import librosa
            import numpy as np
            self._librosa = librosa
            self._np = np

    def get_chords(self, file_path: str, song_id: int = None) -> Optional[list]:
        """
        Get chords for a song. Checks cache/DB first, analyzes if needed.

        Args:
            file_path: Path to MP3 file
            song_id: DB song ID for caching (optional)

        Returns:
            List of {"t": float, "chord": str} dicts, or None on failure
        """
        # Check memory cache
        if song_id and song_id in self._cache:
            logger.debug(f"Chords from cache: song_id={song_id}")
            return self._cache[song_id]

        # Check DB cache
        if song_id and self.db_manager:
            cached = self._load_from_db(song_id)
            if cached:
                self._cache[song_id] = cached
                logger.debug(f"Chords from DB: song_id={song_id}")
                return cached

        # Analyze audio
        chords = self.analyze_file(file_path)
        if chords is None:
            return None

        # Cache results
        if song_id:
            self._cache[song_id] = chords
            if self.db_manager:
                self._save_to_db(song_id, chords)

        return chords

    def analyze_file(self, file_path: str) -> Optional[list]:
        """
        Analyze an audio file and detect chords.

        Args:
            file_path: Path to audio file (MP3, WAV, FLAC, etc.)

        Returns:
            List of {"t": float, "chord": str} dicts, or None on failure
        """
        try:
            self._ensure_libs()
            librosa = self._librosa
            np = self._np

            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            logger.info(f"Analyzing chords: {path.name}")

            # Load audio
            y, sr = librosa.load(str(path), sr=self.SAMPLE_RATE)
            duration = len(y) / sr
            logger.debug(f"Loaded {duration:.1f}s audio")

            # Compute CQT chromagram (better for chord detection than STFT)
            chroma = librosa.feature.chroma_cqt(
                y=y, sr=sr, hop_length=self.HOP_LENGTH
            )

            # Segment into blocks
            hop_duration = self.HOP_LENGTH / sr
            n_frames_per_block = max(1, int(self.BLOCK_SECONDS / hop_duration))

            raw_chords = []
            for i in range(0, chroma.shape[1], n_frames_per_block):
                block = chroma[:, i:i + n_frames_per_block]
                if block.shape[1] == 0:
                    break

                # Average chroma energy in block
                avg_chroma = np.mean(block, axis=1)

                # Skip silence
                if np.max(avg_chroma) < self.MIN_ENERGY:
                    continue

                # Detect chord
                chord_name = self._detect_chord(avg_chroma)
                timestamp = round(i * hop_duration, 1)
                raw_chords.append({"t": timestamp, "chord": chord_name})

            # Deduplicate consecutive identical chords
            chords = self._deduplicate(raw_chords)

            logger.info(f"Detected {len(chords)} chord changes in {duration:.0f}s")
            return chords

        except ImportError:
            logger.error("librosa not installed — run: pip install librosa")
            return None
        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Chord analysis failed: {e}")
            return None

    def _detect_chord(self, chroma_vector) -> str:
        """
        Detect chord from a 12-bin chroma vector.

        Uses normalized template matching against major, minor, and 7th chords.
        Cosine similarity ensures fair comparison between templates of different sizes.
        """
        np = self._np
        best_score = -1
        best_chord = "N"  # No chord

        # Normalize input vector
        norm = np.linalg.norm(chroma_vector)
        if norm < 1e-8:
            return "N"
        chroma_norm = chroma_vector / norm

        for root_idx in range(12):
            root_name = self.CHROMA_LABELS[root_idx]

            # Major triad: root, major 3rd (+4), fifth (+7)
            major_t = np.zeros(12)
            major_t[root_idx] = 1.0
            major_t[(root_idx + 4) % 12] = 0.9
            major_t[(root_idx + 7) % 12] = 0.8
            major_t /= np.linalg.norm(major_t)

            score = np.dot(chroma_norm, major_t)
            if score > best_score:
                best_score = score
                best_chord = root_name

            # Minor triad: root, minor 3rd (+3), fifth (+7)
            minor_t = np.zeros(12)
            minor_t[root_idx] = 1.0
            minor_t[(root_idx + 3) % 12] = 0.9
            minor_t[(root_idx + 7) % 12] = 0.8
            minor_t /= np.linalg.norm(minor_t)

            score = np.dot(chroma_norm, minor_t)
            if score > best_score:
                best_score = score
                best_chord = f"{root_name}m"

            # Dominant 7th: root, major 3rd, fifth, minor 7th (+10)
            # Only wins if the 7th note is actually present in the signal
            dom7_t = np.zeros(12)
            dom7_t[root_idx] = 1.0
            dom7_t[(root_idx + 4) % 12] = 0.8
            dom7_t[(root_idx + 7) % 12] = 0.7
            dom7_t[(root_idx + 10) % 12] = 0.6
            dom7_t /= np.linalg.norm(dom7_t)

            score = np.dot(chroma_norm, dom7_t)
            # Require the 7th note to actually be significant
            seventh_energy = chroma_vector[(root_idx + 10) % 12]
            root_energy = chroma_vector[root_idx]
            if score > best_score and seventh_energy > 0.3 * root_energy:
                best_score = score
                best_chord = f"{root_name}7"

        return best_chord

    @staticmethod
    def _deduplicate(chords: list) -> list:
        """Remove consecutive duplicate chords, keeping the first occurrence."""
        if not chords:
            return chords
        result = [chords[0]]
        for c in chords[1:]:
            if c["chord"] != result[-1]["chord"]:
                result.append(c)
        return result

    @staticmethod
    def transpose_chords(chords: list, semitones: int) -> list:
        """
        Transpose all chords by N semitones.

        Args:
            chords: List of {"t": float, "chord": str}
            semitones: Number of semitones (+/-)

        Returns:
            New list with transposed chords
        """
        if semitones == 0:
            return chords

        try:
            from pychord import Chord
        except ImportError:
            logger.error("pychord not installed — run: pip install pychord")
            return chords

        result = []
        for entry in chords:
            try:
                c = Chord(entry["chord"])
                c.transpose(semitones)
                result.append({"t": entry["t"], "chord": str(c)})
            except ValueError:
                # Unknown chord format, keep as-is
                result.append(entry)
        return result

    def _load_from_db(self, song_id: int) -> Optional[list]:
        """Load cached chords from database."""
        try:
            row = self.db_manager.execute_query(
                "SELECT chords FROM songs WHERE id = ?", (song_id,)
            )
            if row and row[0] and row[0][0]:
                return json.loads(row[0][0])
        except (ValueError, KeyError, TypeError) as e:
            logger.debug(f"No cached chords for song {song_id}: {e}")
        return None

    def _save_to_db(self, song_id: int, chords: list):
        """Save chords to database for caching."""
        try:
            self.db_manager.execute_query(
                "UPDATE songs SET chords = ? WHERE id = ?",
                (json.dumps(chords), song_id)
            )
            logger.debug(f"Cached chords to DB: song_id={song_id}")
        except (OSError, ValueError) as e:
            logger.warning(f"Failed to cache chords: {e}")

    def clear_cache(self):
        """Clear in-memory chord cache."""
        size = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared chord cache ({size} entries)")
