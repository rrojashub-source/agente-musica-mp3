"""
Cleanup Workflow - Complete metadata cleanup orchestration

Purpose: Orchestrate the entire metadata cleanup process
- Step 1: Analyze library (find corrupted metadata)
- Step 2: Clean titles/artists/albums (normalize)
- Step 3: Fetch correct metadata (MusicBrainz/Spotify)
- Step 3.5: Fallback to AcoustID fingerprinting (severe corruption)
- Step 4: Preview changes (user confirmation)
- Step 5: Apply changes (update files + database)
- Step 6: Organize library (optional)

Created: November 18, 2025
Updated: November 18, 2025 (Added AcoustID fallback)
"""
import logging
from typing import Dict, List, Optional
from PyQt6.QtCore import QThread, pyqtSignal
import keyring

logger = logging.getLogger(__name__)


class CleanupWorkflowWorker(QThread):
    """
    Background worker for metadata cleanup workflow

    Signals:
        progress(int, str): Progress percentage (0-100) and status message
        step_completed(int, dict): Step number completed with results
        finished(dict): Final results summary
        error(str): Fatal error message
    """

    # Signals
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    step_completed = pyqtSignal(int, dict)  # (step_number, results)
    finished = pyqtSignal(dict)  # Final summary
    error = pyqtSignal(str)  # Error message

    def __init__(self, db_manager, cleaner, fetcher, songs_to_clean: List[Dict],
                 fetch_metadata: bool = True, min_confidence: float = 70.0,
                 download_covers: bool = False):
        """
        Initialize cleanup workflow

        Args:
            db_manager: DatabaseManager instance
            cleaner: MetadataCleaner instance
            fetcher: MetadataFetcher instance
            songs_to_clean: List of songs to process
            fetch_metadata: Whether to fetch from external APIs
            min_confidence: Minimum confidence for metadata matches
            download_covers: Whether to download cover art
        """
        super().__init__()
        self.db_manager = db_manager
        self.cleaner = cleaner
        self.fetcher = fetcher
        self.songs = songs_to_clean
        self.fetch_metadata = fetch_metadata
        self.min_confidence = min_confidence
        self.download_covers = download_covers

        # Results tracking
        self.analysis_report = None
        self.cleaned_songs = []
        self.fetched_songs = []
        self.preview_changes = []

        # Initialize AcoustID client (fallback for severe corruption)
        self.acoustid_client = None
        try:
            acoustid_key = keyring.get_password("nexus_music", "acoustid_api_key")
            if acoustid_key:
                from core.acoustid_client import AcoustIDClient
                self.acoustid_client = AcoustIDClient(acoustid_key)
                if self.acoustid_client.is_available():
                    logger.info("AcoustID fingerprinting enabled (fallback for severe corruption)")
                else:
                    logger.warning("AcoustID API key found but fpcalc not available")
                    self.acoustid_client = None
            else:
                logger.debug("AcoustID API key not configured (fingerprinting unavailable)")
        except Exception as e:
            logger.debug(f"Could not initialize AcoustID: {e}")
            self.acoustid_client = None

        logger.info(f"CleanupWorkflowWorker initialized for {len(songs_to_clean)} songs (covers: {download_covers})")

    def run(self):
        """
        Execute cleanup workflow in background

        Workflow:
        1. Analyze corruption levels
        2. Clean metadata (normalize)
        3. Fetch correct metadata (if enabled)
        4. Generate preview of changes
        5. Return results for user confirmation
        """
        try:
            total_songs = len(self.songs)

            # STEP 1: Analyze library
            self.progress.emit(10, f"Analyzing {total_songs} songs...")
            self._step1_analyze()
            self.progress.emit(20, "Analysis complete")

            # STEP 2: Clean metadata
            self.progress.emit(30, "Cleaning metadata...")
            self._step2_clean()
            self.progress.emit(50, f"Cleaned {len(self.cleaned_songs)} songs")

            # STEP 3: Fetch correct metadata (if enabled)
            if self.fetch_metadata:
                self.progress.emit(60, "Fetching correct metadata...")
                self._step3_fetch()
                self.progress.emit(80, f"Fetched metadata for {len(self.fetched_songs)} songs")

            # STEP 4: Generate preview
            self.progress.emit(90, "Generating preview...")
            self._step4_preview()
            self.progress.emit(95, "Preview ready")

            # STEP 5: Emit final results
            self.progress.emit(100, "Complete")
            self.finished.emit({
                'analysis': self.analysis_report,
                'cleaned': self.cleaned_songs,
                'fetched': self.fetched_songs,
                'preview': self.preview_changes
            })

        except Exception as e:
            logger.error(f"Cleanup workflow error: {e}", exc_info=True)
            self.error.emit(str(e))

    def _step1_analyze(self):
        """Step 1: Analyze corruption levels"""
        self.analysis_report = self.cleaner.analyze_library(self.songs)

        self.step_completed.emit(1, {
            'total': self.analysis_report['total_songs'],
            'clean': self.analysis_report['clean'],
            'minor': self.analysis_report['minor'],
            'moderate': self.analysis_report['moderate'],
            'severe': self.analysis_report['severe']
        })

        logger.info(
            f"Analysis: {self.analysis_report['clean']} clean, "
            f"{self.analysis_report['moderate'] + self.analysis_report['severe']} need cleanup"
        )

    def _step2_clean(self):
        """Step 2: Clean metadata (normalize)"""
        for song in self.songs:
            # Skip clean songs
            corruption = self.cleaner.detect_corruption_level(song)
            if corruption == 'clean':
                continue

            # Clean metadata
            cleaned_metadata, issues = self.cleaner.clean_metadata(song)

            if issues:
                self.cleaned_songs.append({
                    'id': song.get('id'),
                    'original': {
                        'title': song.get('title'),
                        'artist': song.get('artist'),
                        'album': song.get('album')
                    },
                    'cleaned': {
                        'title': cleaned_metadata.get('title'),
                        'artist': cleaned_metadata.get('artist'),
                        'album': cleaned_metadata.get('album')
                    },
                    'issues': issues,
                    'corruption_level': corruption
                })

        self.step_completed.emit(2, {
            'cleaned_count': len(self.cleaned_songs)
        })

    def _step3_fetch(self):
        """Step 3: Fetch correct metadata from external APIs (with AcoustID fallback)"""
        for cleaned_song in self.cleaned_songs:
            try:
                # Use cleaned metadata for search
                title = cleaned_song['cleaned']['title']
                artist = cleaned_song['cleaned']['artist']
                duration = self._get_song_duration(cleaned_song['id'])

                # Fetch from APIs
                best_match = self.fetcher.fetch_metadata(
                    title=title,
                    artist=artist,
                    duration=duration,
                    min_confidence=self.min_confidence
                )

                if best_match:
                    self.fetched_songs.append({
                        'id': cleaned_song['id'],
                        'original': cleaned_song['original'],
                        'cleaned': cleaned_song['cleaned'],
                        'fetched': {
                            'title': best_match.get('title'),
                            'artist': best_match.get('artist'),
                            'album': best_match.get('album'),
                            'year': best_match.get('year')
                        },
                        'confidence': best_match.get('score'),
                        'source': best_match.get('source')
                    })
                elif self.acoustid_client and cleaned_song.get('corruption_level') == 'severe':
                    # Fallback: Try AcoustID fingerprinting for severely corrupted songs
                    logger.info(f"Trying AcoustID fallback for song {cleaned_song['id']}")
                    file_path = self._get_song_file_path(cleaned_song['id'])

                    if file_path:
                        acoustid_match = self.acoustid_client.identify_song(file_path)

                        if acoustid_match:
                            self.fetched_songs.append({
                                'id': cleaned_song['id'],
                                'original': cleaned_song['original'],
                                'cleaned': cleaned_song['cleaned'],
                                'fetched': {
                                    'title': acoustid_match.get('title'),
                                    'artist': acoustid_match.get('artist'),
                                    'album': acoustid_match.get('album', 'Unknown Album'),
                                    'year': acoustid_match.get('year')
                                },
                                'confidence': acoustid_match.get('score', 0) * 100,  # Convert to percentage
                                'source': 'acoustid'
                            })
                            logger.info(f"AcoustID match found for song {cleaned_song['id']}")

            except Exception as e:
                logger.warning(f"Failed to fetch metadata for song {cleaned_song['id']}: {e}")

        self.step_completed.emit(3, {
            'fetched_count': len(self.fetched_songs)
        })

    def _step4_preview(self):
        """Step 4: Generate preview of all changes"""
        for song in self.cleaned_songs:
            song_id = song['id']

            # Check if we have fetched metadata
            fetched = next((f for f in self.fetched_songs if f['id'] == song_id), None)

            if fetched:
                # Use fetched metadata (most accurate)
                self.preview_changes.append({
                    'id': song_id,
                    'original': song['original'],
                    'proposed': fetched['fetched'],
                    'confidence': fetched['confidence'],
                    'source': fetched['source'],
                    'status': 'fetched'
                })
            else:
                # Use cleaned metadata only
                self.preview_changes.append({
                    'id': song_id,
                    'original': song['original'],
                    'proposed': song['cleaned'],
                    'confidence': 50.0,  # Lower confidence (no external validation)
                    'source': 'cleaned',
                    'status': 'cleaned_only'
                })

        self.step_completed.emit(4, {
            'preview_count': len(self.preview_changes)
        })

    def _get_song_duration(self, song_id: int) -> Optional[int]:
        """Get song duration from database"""
        try:
            song = self.db_manager.get_song_by_id(song_id)
            return song.get('duration') if song else None
        except:
            return None

    def _get_song_file_path(self, song_id: int) -> Optional[str]:
        """Get song file path from database"""
        try:
            song = self.db_manager.get_song_by_id(song_id)
            return song.get('file_path') if song else None
        except:
            return None


class CleanupApplier:
    """
    Apply approved metadata changes

    Applies changes from preview to:
    - MP3 file ID3 tags
    - Database records
    - File names (if rename enabled)
    - Cover art (if enabled)
    """

    def __init__(self, db_manager):
        """
        Initialize cleanup applier

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.cover_manager = None  # Initialized when needed
        logger.info("CleanupApplier initialized")

    def apply_changes(self, approved_changes: List[Dict], download_covers: bool = False) -> Dict:
        """
        Apply approved metadata changes

        Args:
            approved_changes: List of changes approved by user
            download_covers: Whether to download album cover art

        Returns:
            Results summary:
            {
                'success': int,
                'failed': int,
                'errors': [str],
                'covers_downloaded': int
            }
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'covers_downloaded': 0
        }

        # Initialize cover manager if needed
        if download_covers and self.cover_manager is None:
            from core.cover_art_manager import CoverArtManager
            self.cover_manager = CoverArtManager()
            logger.info("CoverArtManager initialized for batch download")

        for change in approved_changes:
            try:
                song_id = change['id']
                new_metadata = change['proposed']

                # Update database
                success = self.db_manager.update_song(song_id, {
                    'title': new_metadata.get('title'),
                    'artist': new_metadata.get('artist'),
                    'album': new_metadata.get('album'),
                    'year': new_metadata.get('year')
                })

                if success:
                    results['success'] += 1
                    logger.info(f"Updated song {song_id}: {new_metadata.get('title')}")

                    # Download cover art if enabled
                    if download_covers and self.cover_manager:
                        artist = new_metadata.get('artist')
                        album = new_metadata.get('album')

                        if artist and album:
                            try:
                                # Skip if already exists
                                if not self.cover_manager.has_cover(artist, album):
                                    if self.cover_manager.download_cover(artist, album):
                                        results['covers_downloaded'] += 1
                                        logger.info(f"Downloaded cover: {artist} - {album}")
                                else:
                                    logger.debug(f"Cover already exists: {artist} - {album}")
                            except Exception as e:
                                logger.warning(f"Failed to download cover for {artist} - {album}: {e}")

                    # TODO: Update MP3 file ID3 tags
                    # self._update_id3_tags(song_id, new_metadata)

                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to update song {song_id}")

            except Exception as e:
                results['failed'] += 1
                error_msg = f"Error updating song {change['id']}: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

        logger.info(
            f"Applied changes: {results['success']} success, {results['failed']} failed"
        )

        return results

    def _update_id3_tags(self, song_id: int, metadata: Dict):
        """
        Update ID3 tags in MP3 file

        Args:
            song_id: Song ID
            metadata: New metadata to write
        """
        # TODO: Implement ID3 tag writing with mutagen
        # Get file path from database
        # Open with mutagen
        # Update TIT2, TPE1, TALB, TDRC tags
        # Save file
        pass
