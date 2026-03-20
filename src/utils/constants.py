"""
Application Constants — NEXUS Music Manager

Centralized constants to eliminate magic numbers across the codebase.
Organized by domain. Import specific sections as needed.

Created: March 11, 2026
"""

# ==========================================
# Application Identity
# ==========================================
APP_VERSION = "2.1.0"

# ==========================================
# Audio Engine (python-mpv)
# ==========================================
# Note: mpv handles sample rate/channels/buffer internally
# These are kept for reference and any custom audio processing
AUDIO_SAMPLE_RATE = 44100  # Hz - standard sample rate
AUDIO_CHANNELS = 2  # Stereo

FILE_HASH_CHUNK_SIZE = 4096  # Bytes - for file hash computation

# ==========================================
# API / Network
# ==========================================
API_CACHE_SIZE = 128  # LRU cache max entries (YouTube, Spotify)
API_DEFAULT_RESULTS = 20  # Default search results per query
API_MAX_RESULTS = 50  # Maximum results per API request
API_QUERY_MAX_LENGTH = 500  # Max characters for sanitized queries
API_DEFAULT_TIMEOUT = 10  # Seconds - HTTP request timeout
API_MAX_RETRIES = 3  # Default retry attempts for rate-limited requests

# ==========================================
# Database
# ==========================================
DB_CONNECTION_TIMEOUT = 30.0  # Seconds - SQLite connection timeout
MAX_CONCURRENT_DOWNLOADS = 50  # Download queue max parallel downloads
MAX_DOWNLOAD_RETRIES = 3  # Failed download retry attempts

# ==========================================
# Timers / Intervals
# ==========================================
POSITION_UPDATE_INTERVAL_MS = 250  # Player position poll (4 updates/sec)
REMOTE_UPDATE_INTERVAL_MS = 500  # Remote control sync (2 updates/sec)
TRACK_END_CHECK_INTERVAL_MS = 1000  # End-of-song detection
VISUALIZER_FRAME_INTERVAL_MS = 33  # ~30 FPS for visualizer
ANIMATION_FRAME_INTERVAL_MS = 16  # ~60 FPS for animations

# ==========================================
# UI Defaults
# ==========================================
MAIN_WINDOW_WIDTH = 1400
MAIN_WINDOW_HEIGHT = 900
DEFAULT_REMOTE_PORT = 8080
PORT_RANGE_MIN = 1024
PORT_RANGE_MAX = 65535
ALBUM_ART_THUMBNAIL_SIZE = 100
CONFIDENCE_THRESHOLD_DEFAULT = 70

# ==========================================
# Default Metadata Values
# ==========================================
DEFAULT_ARTIST = "Unknown Artist"
DEFAULT_ALBUM = "Unknown Album"
DEFAULT_TITLE = "Unknown Title"
DEFAULT_GENRE = "Unknown"
