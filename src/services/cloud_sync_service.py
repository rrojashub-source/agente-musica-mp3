"""
NEXUS Music Manager - Cloud Sync Service
Synchronizes library metadata across devices via cloud storage

Features:
- Export/import library to JSON
- Multiple cloud provider support (Local, Google Drive, Dropbox)
- Conflict resolution strategies
- Delta sync (only changes)
- Offline-first with eventual consistency
"""

import hashlib
import json
import logging
import shutil
import sqlite3
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Sync status enum"""

    IDLE = "idle"
    SYNCING = "syncing"
    UPLOADING = "uploading"
    DOWNLOADING = "downloading"
    RESOLVING_CONFLICTS = "resolving_conflicts"
    COMPLETED = "completed"
    FAILED = "failed"


class ConflictStrategy(Enum):
    """Conflict resolution strategy"""

    NEWER_WINS = "newer_wins"  # Most recent change wins
    LOCAL_WINS = "local_wins"  # Local changes always win
    REMOTE_WINS = "remote_wins"  # Remote changes always win
    KEEP_BOTH = "keep_both"  # Keep both versions
    MANUAL = "manual"  # Ask user


@dataclass
class SyncState:
    """Tracks sync state"""

    last_sync_time: Optional[str] = None
    last_sync_hash: Optional[str] = None
    provider: Optional[str] = None
    status: str = "idle"
    pending_changes: int = 0
    conflicts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncState":
        return cls(**data)


@dataclass
class SyncConflict:
    """Represents a sync conflict"""

    item_type: str  # "song", "playlist", "setting"
    item_id: str
    local_data: Dict[str, Any]
    remote_data: Dict[str, Any]
    local_modified: str
    remote_modified: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LibraryExport:
    """Exported library data structure"""

    version: str = "1.0"
    exported_at: str = ""
    device_id: str = ""
    songs: List[Dict[str, Any]] = field(default_factory=list)
    playlists: List[Dict[str, Any]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    sync_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LibraryExport":
        return cls(
            version=data.get("version", "1.0"),
            exported_at=data.get("exported_at", ""),
            device_id=data.get("device_id", ""),
            songs=data.get("songs", []),
            playlists=data.get("playlists", []),
            settings=data.get("settings", {}),
            sync_metadata=data.get("sync_metadata", {}),
        )

    def compute_hash(self) -> str:
        """Compute hash of library content for change detection"""
        content = json.dumps(
            {
                "songs": sorted(self.songs, key=lambda x: x.get("id", 0)),
                "playlists": sorted(self.playlists, key=lambda x: x.get("id", 0)),
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ==========================================
# Cloud Provider Abstraction
# ==========================================


class CloudProvider(ABC):
    """Abstract base class for cloud storage providers"""

    @abstractmethod
    def connect(self) -> bool:
        """Connect/authenticate with the provider"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from provider"""
        pass

    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> bool:
        """Upload file to cloud"""
        pass

    @abstractmethod
    def download(self, remote_path: str, local_path: str) -> bool:
        """Download file from cloud"""
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """Check if remote file exists"""
        pass

    @abstractmethod
    def get_modified_time(self, remote_path: str) -> Optional[datetime]:
        """Get last modified time of remote file"""
        pass

    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        """Delete remote file"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class LocalFolderProvider(CloudProvider):
    """
    Local folder sync provider (for testing, NAS, or shared folders)
    Syncs to a local folder that can be synced via other tools
    """

    def __init__(self, sync_folder: Optional[str] = None) -> None:
        self._sync_folder: Optional[Path] = Path(sync_folder) if sync_folder else None
        self._connected: bool = False

    def connect(self) -> bool:
        """Connect (verify folder exists)"""
        if self._sync_folder is None:
            logger.error("No sync folder configured")
            return False

        try:
            self._sync_folder.mkdir(parents=True, exist_ok=True)
            self._connected = True
            logger.info(f"Connected to local folder: {self._sync_folder}")
            return True
        except OSError as e:
            logger.error(f"Failed to connect to local folder: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect"""
        self._connected = False

    def upload(self, local_path: str, remote_path: str) -> bool:
        """Copy file to sync folder"""
        if not self._connected or self._sync_folder is None:
            return False

        try:
            dest = self._sync_folder / remote_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, dest)
            logger.info(f"Uploaded to local folder: {remote_path}")
            return True
        except OSError as e:
            logger.error(f"Failed to upload {remote_path}: {e}")
            return False

    def download(self, remote_path: str, local_path: str) -> bool:
        """Copy file from sync folder"""
        if not self._connected or self._sync_folder is None:
            return False

        try:
            src = self._sync_folder / remote_path
            if not src.exists():
                logger.error(f"Remote file not found: {remote_path}")
                return False

            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, local_path)
            logger.info(f"Downloaded from local folder: {remote_path}")
            return True
        except OSError as e:
            logger.error(f"Failed to download {remote_path}: {e}")
            return False

    def exists(self, remote_path: str) -> bool:
        """Check if file exists in sync folder"""
        if not self._connected or self._sync_folder is None:
            return False
        return (self._sync_folder / remote_path).exists()

    def get_modified_time(self, remote_path: str) -> Optional[datetime]:
        """Get file modification time"""
        if not self._connected or self._sync_folder is None:
            return None

        path = self._sync_folder / remote_path
        if path.exists():
            return datetime.fromtimestamp(path.stat().st_mtime)
        return None

    def delete(self, remote_path: str) -> bool:
        """Delete file from sync folder"""
        if not self._connected or self._sync_folder is None:
            return False

        try:
            path = self._sync_folder / remote_path
            if path.exists():
                path.unlink()
            return True
        except OSError as e:
            logger.error(f"Failed to delete {remote_path}: {e}")
            return False

    @property
    def name(self) -> str:
        return "Local Folder"

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def sync_folder(self) -> Optional[Path]:
        return self._sync_folder

    @sync_folder.setter
    def sync_folder(self, path: Optional[str]) -> None:
        self._sync_folder = Path(path) if path else None
        self._connected = False


class GoogleDriveProvider(CloudProvider):
    """
    Google Drive sync provider with OAuth credentials.
    User-friendly flow: just click "Connect" and authorize in browser.

    Requires: pip install google-api-python-client google-auth-oauthlib

    Credentials loaded from ~/.nexus_music/cloud/gdrive_credentials.json
    """

    _SCOPES: List[str] = ["https://www.googleapis.com/auth/drive.file"]

    @classmethod
    def _load_client_config(cls) -> Dict[str, Any]:
        """Load OAuth credentials from config file"""
        config_path = Path.home() / ".nexus_music" / "cloud" / "gdrive_credentials.json"

        if config_path.exists():
            try:
                with open(config_path) as f:
                    return json.load(f)  # type: ignore[no-any-return]
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load credentials: {e}")

        # Return empty config - will fail gracefully
        return {}

    def __init__(self, credentials_file: Optional[str] = None) -> None:
        """
        Initialize Google Drive provider.

        Args:
            credentials_file: Deprecated, kept for backwards compatibility.
                             Now uses embedded credentials.
        """
        self._service: Any = None
        self._connected: bool = False
        self._folder_id: Optional[str] = None
        self._user_email: Optional[str] = None

        # Token stored in user's home directory
        self._token_dir: Path = Path.home() / ".nexus_music" / "cloud"
        self._token_dir.mkdir(parents=True, exist_ok=True)
        self._token_path: Path = self._token_dir / "google_drive_token.json"

    @property
    def is_authenticated(self) -> bool:
        """Check if user has already authorized the app"""
        return self._token_path.exists()

    @property
    def user_email(self) -> Optional[str]:
        """Get connected user's email"""
        return self._user_email

    def connect(self) -> bool:
        """
        Connect to Google Drive.
        Opens browser for authorization if needed.
        """
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None

            # Try to load existing token
            if self._token_path.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(self._token_path), self._SCOPES)
                except (OSError, ValueError, KeyError) as e:
                    logger.warning(f"Invalid token file, will re-authenticate: {e}")
                    creds = None

            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        from google.auth.transport.requests import Request

                        creds.refresh(Request())
                        logger.info("Google Drive token refreshed")
                    except (ConnectionError, OSError, ValueError) as e:
                        logger.warning(f"Token refresh failed, re-authenticating: {e}")
                        creds = None

                if not creds:
                    # Load credentials from config file
                    client_config = self._load_client_config()
                    if not client_config:
                        logger.error("No Google Drive credentials found. Please configure gdrive_credentials.json")
                        return False

                    # Start OAuth flow - opens browser automatically
                    flow = InstalledAppFlow.from_client_config(client_config, self._SCOPES)
                    creds = flow.run_local_server(
                        port=0,
                        prompt="consent",
                        success_message="¡Conexión exitosa! Puedes cerrar esta ventana y volver a NEXUS Music Manager.",
                    )
                    logger.info("Google Drive authorization completed")

                # Save token for future use
                with open(self._token_path, "w") as token:
                    token.write(creds.to_json())

            # Build service
            self._service = build("drive", "v3", credentials=creds)
            self._connected = True

            # Get user info
            self._get_user_info()

            # Create or find NEXUS_Music_Sync folder
            self._ensure_sync_folder()

            logger.info(f"Connected to Google Drive as {self._user_email}")
            return True

        except ImportError:
            logger.error(
                "Google Drive dependencies not installed. Run: pip install google-api-python-client google-auth-oauthlib"
            )
            return False
        except Exception as e:  # OAuth raises heterogeneous exceptions (HttpError, TransportError, etc.)
            # Broad catch intentional: OAuth flow can raise many heterogeneous exceptions
            # (HttpError, TransportError, browser errors, OS errors) depending on environment.
            logger.error(f"Failed to connect to Google Drive: {e}")
            return False

    def _get_user_info(self) -> None:
        """Get authenticated user's email"""
        try:
            about = self._service.about().get(fields="user").execute()
            self._user_email = about.get("user", {}).get("emailAddress", "Unknown")
        except (KeyError, AttributeError, ConnectionError, OSError) as e:
            logger.debug(f"Could not get user info: {e}")
            self._user_email = "Connected"

    def logout(self) -> None:
        """Logout and remove saved token"""
        self.disconnect()
        if self._token_path.exists():
            self._token_path.unlink()
            logger.info("Google Drive token removed")
        self._user_email = None

    def _ensure_sync_folder(self) -> None:
        """Create or find sync folder in Drive"""
        if not self._service:
            return

        # Search for existing folder
        results = (
            self._service.files()
            .list(
                q="name='NEXUS_Music_Sync' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )

        files = results.get("files", [])
        if files:
            self._folder_id = files[0]["id"]
        else:
            # Create folder
            file_metadata = {"name": "NEXUS_Music_Sync", "mimeType": "application/vnd.google-apps.folder"}
            folder = self._service.files().create(body=file_metadata, fields="id").execute()
            self._folder_id = folder.get("id")

    def disconnect(self) -> None:
        """Disconnect from Google Drive"""
        self._service = None
        self._connected = False
        self._folder_id = None

    def upload(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Google Drive"""
        if not self._connected or not self._folder_id:
            return False

        try:
            from googleapiclient.http import MediaFileUpload

            # Check if file exists
            existing = self._find_file(remote_path)

            file_metadata: dict[str, Any] = {"name": remote_path}
            media = MediaFileUpload(local_path, resumable=True)

            if existing:
                # Update existing file
                self._service.files().update(fileId=existing["id"], media_body=media).execute()
            else:
                # Create new file
                file_metadata["parents"] = [self._folder_id]  # type: ignore[assignment]
                self._service.files().create(body=file_metadata, media_body=media, fields="id").execute()

            logger.info(f"Uploaded to Google Drive: {remote_path}")
            return True
        except (OSError, ConnectionError, KeyError) as e:
            logger.error(f"Failed to upload to Drive: {e}")
            return False

    def download(self, remote_path: str, local_path: str) -> bool:
        """Download file from Google Drive"""
        if not self._connected:
            return False

        try:
            import io

            from googleapiclient.http import MediaIoBaseDownload

            file_info = self._find_file(remote_path)
            if not file_info:
                return False

            request = self._service.files().get_media(fileId=file_info["id"])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(fh.getvalue())

            logger.info(f"Downloaded from Google Drive: {remote_path}")
            return True
        except (OSError, ConnectionError, KeyError) as e:
            logger.error(f"Failed to download from Drive: {e}")
            return False

    def _find_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Find file in sync folder"""
        if not self._service or not self._folder_id:
            return None

        # Escape single quotes to prevent Drive query injection
        safe_filename = filename.replace("\\", "\\\\").replace("'", "\\'")
        results = (
            self._service.files()
            .list(
                q=f"name='{safe_filename}' and '{self._folder_id}' in parents and trashed=false",
                spaces="drive",
                fields="files(id, name, modifiedTime)",
            )
            .execute()
        )

        files = results.get("files", [])
        return files[0] if files else None

    def exists(self, remote_path: str) -> bool:
        """Check if file exists"""
        return self._find_file(remote_path) is not None

    def get_modified_time(self, remote_path: str) -> Optional[datetime]:
        """Get file modified time"""
        file_info = self._find_file(remote_path)
        if file_info and "modifiedTime" in file_info:
            return datetime.fromisoformat(file_info["modifiedTime"].replace("Z", "+00:00"))
        return None

    def delete(self, remote_path: str) -> bool:
        """Delete file from Drive"""
        if not self._connected:
            return False

        try:
            file_info = self._find_file(remote_path)
            if file_info:
                self._service.files().delete(fileId=file_info["id"]).execute()
            return True
        except (ConnectionError, OSError, KeyError) as e:
            logger.error(f"Failed to delete from Drive: {e}")
            return False

    @property
    def name(self) -> str:
        return "Google Drive"

    @property
    def is_connected(self) -> bool:
        return self._connected


# ==========================================
# Cloud Sync Service
# ==========================================


class CloudSyncService(QObject):
    """
    Cloud Sync Service - Orchestrates library synchronization

    Signals:
        sync_started: Emitted when sync begins
        sync_progress: Emitted during sync (status, message, percent)
        sync_completed: Emitted when sync finishes (success, message)
        sync_failed: Emitted on error (error_message)
        conflict_detected: Emitted when conflicts found (conflicts_list)
        status_changed: Emitted when status changes (SyncStatus)
    """

    # Signals
    sync_started = Signal()
    sync_progress = Signal(str, str, int)  # status, message, percent
    sync_completed = Signal(bool, str)  # success, message
    sync_failed = Signal(str)  # error_message
    conflict_detected = Signal(list)  # conflicts
    status_changed = Signal(object)  # SyncStatus

    # Singleton
    _instance: Optional["CloudSyncService"] = None
    _lock: threading.Lock = threading.Lock()

    # Remote filename
    SYNC_FILENAME: str = "nexus_library_sync.json"
    STATE_FILENAME: str = "sync_state.json"

    def __init__(self, data_dir: Optional[str] = None) -> None:
        """Initialize CloudSyncService"""
        super().__init__()

        self._data_dir: Path = Path(data_dir) if data_dir else Path.home() / ".nexus_music"
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._provider: Optional[CloudProvider] = None
        self._state: SyncState = SyncState()
        self._conflict_strategy: ConflictStrategy = ConflictStrategy.NEWER_WINS
        self._device_id: str = self._get_device_id()
        self._db_manager: Any = None

        # Load saved state
        self._load_state()

        logger.info(f"CloudSyncService initialized (device: {self._device_id})")

    @classmethod
    def get_instance(cls, data_dir: Optional[str] = None) -> "CloudSyncService":
        """Get singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(data_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)"""
        with cls._lock:
            cls._instance = None

    def _get_device_id(self) -> str:
        """Generate unique device ID"""
        import platform
        import uuid

        device_file = self._data_dir / "device_id"
        if device_file.exists():
            return device_file.read_text().strip()

        # Generate new ID
        device_id = f"{platform.node()}_{uuid.uuid4().hex[:8]}"
        device_file.write_text(device_id)
        return device_id

    @property
    def device_id(self) -> str:
        """Public property to access device ID"""
        return self._device_id

    @property
    def sync_state(self) -> "SyncState":
        """Public property to access sync state"""
        return self._state

    def _load_state(self) -> None:
        """Load sync state from disk"""
        state_file = self._data_dir / self.STATE_FILENAME
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                self._state = SyncState.from_dict(data)
            except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
                logger.error(f"Failed to load sync state: {e}")

    def _save_state(self) -> None:
        """Save sync state to disk"""
        state_file = self._data_dir / self.STATE_FILENAME
        try:
            state_file.write_text(json.dumps(self._state.to_dict(), indent=2))
        except OSError as e:
            logger.error(f"Failed to save sync state: {e}")

    # ==========================================
    # Provider Management
    # ==========================================

    def set_provider(self, provider: CloudProvider) -> bool:
        """Set cloud provider"""
        self._provider = provider
        self._state.provider = provider.name
        self._save_state()
        return True

    def get_provider(self) -> Optional[CloudProvider]:
        """Get current provider"""
        return self._provider

    def connect(self) -> bool:
        """Connect to cloud provider"""
        if not self._provider:
            self.sync_failed.emit("No cloud provider configured")
            return False

        result = self._provider.connect()
        if result:
            self._state.status = SyncStatus.IDLE.value
        return result

    def disconnect(self) -> None:
        """Disconnect from cloud provider"""
        if self._provider:
            self._provider.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return bool(self._provider and self._provider.is_connected)  # type: ignore[return-value]

    # ==========================================
    # Export/Import
    # ==========================================

    def export_library(self, db_manager: Any = None) -> LibraryExport:
        """
        Export library to LibraryExport object

        Args:
            db_manager: Database manager (optional, uses internal if not provided)
        """
        db = db_manager or self._db_manager
        if not db:
            from database.manager import DatabaseManager

            # Use default path - this should be configured
            db = DatabaseManager()

        export = LibraryExport(
            version="1.0",
            exported_at=datetime.now().isoformat(),
            device_id=self._device_id,
            songs=[],
            playlists=[],
            settings={},
            sync_metadata={"last_sync": self._state.last_sync_time, "source_device": self._device_id},
        )

        # Export songs
        try:
            songs = db.fetch_all("SELECT * FROM songs")
            export.songs = songs
        except sqlite3.Error as e:
            logger.error(f"Failed to export songs: {e}")

        # Export playlists
        try:
            playlists = db.fetch_all("SELECT * FROM playlists")
            export.playlists = playlists

            # Include playlist songs
            for playlist in export.playlists:
                playlist_songs = db.fetch_all(
                    "SELECT song_id FROM playlist_songs WHERE playlist_id = ?", (playlist["id"],)
                )
                playlist["song_ids"] = [s["song_id"] for s in playlist_songs]
        except sqlite3.Error as e:
            logger.debug(f"No playlists to export: {e}")

        logger.info(f"Exported {len(export.songs)} songs, {len(export.playlists)} playlists")
        return export

    def import_library(self, export: LibraryExport, db_manager: Any = None, merge: bool = True) -> Dict[str, int]:
        """
        Import library from LibraryExport object

        Args:
            export: Library export data
            db_manager: Database manager
            merge: If True, merge with existing; if False, replace

        Returns:
            Statistics dict (added, updated, skipped)
        """
        db = db_manager or self._db_manager
        if not db:
            from database.manager import DatabaseManager

            db = DatabaseManager()

        stats = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}

        for song in export.songs:
            try:
                # Check if song exists (by file_path or title+artist)
                existing = db.fetch_one("SELECT id FROM songs WHERE file_path = ?", (song.get("file_path", ""),))

                if existing:
                    if merge:
                        # Update existing
                        # (simplified - in production, compare modified times)
                        stats["skipped"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    # Add new song
                    db.add_song(song)
                    stats["added"] += 1

            except sqlite3.Error as e:
                logger.error(f"Failed to import song: {e}")
                stats["errors"] += 1

        logger.info(f"Import complete: {stats}")
        return stats

    # ==========================================
    # Sync Operations
    # ==========================================

    def sync(self, db_manager: Any = None) -> bool:
        """
        Perform full sync with cloud

        1. Export local library
        2. Download remote library (if exists)
        3. Merge changes
        4. Upload merged library
        """
        if not self.is_connected:
            self.sync_failed.emit("Not connected to cloud provider")
            return False

        self.sync_started.emit()
        self._state.status = SyncStatus.SYNCING.value
        self.status_changed.emit(SyncStatus.SYNCING)

        try:
            # Step 1: Export local library
            self.sync_progress.emit("exporting", "Exporting local library...", 10)
            local_export = self.export_library(db_manager)
            local_hash = local_export.compute_hash()

            # Step 2: Check for remote library
            self.sync_progress.emit("checking", "Checking remote library...", 30)

            temp_remote = self._data_dir / "temp_remote.json"
            temp_upload = self._data_dir / "temp_upload.json"

            try:
                if self._provider.exists(self.SYNC_FILENAME):  # type: ignore[union-attr]
                    # Download remote
                    self.sync_progress.emit("downloading", "Downloading remote library...", 40)
                    self._state.status = SyncStatus.DOWNLOADING.value

                    if self._provider.download(self.SYNC_FILENAME, str(temp_remote)):  # type: ignore[union-attr]
                        remote_data = json.loads(temp_remote.read_text())
                        remote_export = LibraryExport.from_dict(remote_data)
                        remote_hash = remote_export.compute_hash()

                        # Check for changes
                        if local_hash == remote_hash:
                            self.sync_progress.emit("complete", "Already in sync", 100)
                            self._update_sync_state(local_hash)
                            self.sync_completed.emit(True, "Library already in sync")
                            return True

                        # Merge libraries
                        self.sync_progress.emit("merging", "Merging changes...", 60)
                        merged = self._merge_exports(local_export, remote_export)
                    else:
                        merged = local_export
                else:
                    # No remote - use local
                    merged = local_export

                # Step 3: Upload merged library
                self.sync_progress.emit("uploading", "Uploading to cloud...", 80)
                self._state.status = SyncStatus.UPLOADING.value

                temp_upload.write_text(json.dumps(merged.to_dict(), indent=2))

                if self._provider.upload(str(temp_upload), self.SYNC_FILENAME):  # type: ignore[union-attr]
                    self._update_sync_state(merged.compute_hash())
                    self.sync_progress.emit("complete", "Sync completed", 100)
                    self._state.status = SyncStatus.COMPLETED.value
                    self.status_changed.emit(SyncStatus.COMPLETED)
                    self.sync_completed.emit(True, f"Synced {len(merged.songs)} songs")
                    return True
                else:
                    raise Exception("Failed to upload to cloud")
            finally:
                # Clean up temp files to prevent data leakage
                for tf in (temp_remote, temp_upload):
                    try:
                        tf.unlink(missing_ok=True)
                    except OSError:
                        pass

        except Exception as e:  # sync orchestrates network/disk/DB - all failures must reach UI
            # Broad catch intentional: sync() orchestrates network, disk, JSON and DB
            # operations; any of them can fail and must be reported to the UI via signals.
            logger.error(f"Sync failed: {e}")
            self._state.status = SyncStatus.FAILED.value
            self.status_changed.emit(SyncStatus.FAILED)
            self.sync_failed.emit(str(e))
            return False

    def _merge_exports(self, local: LibraryExport, remote: LibraryExport) -> LibraryExport:
        """Merge two library exports"""
        merged = LibraryExport(
            version="1.0",
            exported_at=datetime.now().isoformat(),
            device_id=self._device_id,
            songs=[],
            playlists=[],
            settings={**remote.settings, **local.settings},
        )

        # Create lookup by file_path
        local_songs = {s.get("file_path"): s for s in local.songs if s.get("file_path")}
        remote_songs = {s.get("file_path"): s for s in remote.songs if s.get("file_path")}

        all_paths = set(local_songs.keys()) | set(remote_songs.keys())

        for path in all_paths:
            local_song = local_songs.get(path)
            remote_song = remote_songs.get(path)

            if local_song and remote_song:
                # Both have it - resolve conflict
                if self._conflict_strategy == ConflictStrategy.NEWER_WINS:
                    local_mod = local_song.get("date_modified", "")
                    remote_mod = remote_song.get("date_modified", "")
                    merged.songs.append(local_song if local_mod >= remote_mod else remote_song)
                elif self._conflict_strategy == ConflictStrategy.LOCAL_WINS:
                    merged.songs.append(local_song)
                elif self._conflict_strategy == ConflictStrategy.REMOTE_WINS:
                    merged.songs.append(remote_song)
                else:
                    merged.songs.append(local_song)  # Default to local
            elif local_song:
                merged.songs.append(local_song)
            elif remote_song:
                merged.songs.append(remote_song)

        # Merge playlists (similar logic)
        local_playlists = {p.get("name"): p for p in local.playlists}
        remote_playlists = {p.get("name"): p for p in remote.playlists}
        all_names = set(local_playlists.keys()) | set(remote_playlists.keys())

        for name in all_names:
            local_pl = local_playlists.get(name)
            remote_pl = remote_playlists.get(name)
            merged.playlists.append(local_pl or remote_pl)  # type: ignore[arg-type]

        return merged

    def _update_sync_state(self, content_hash: str) -> None:
        """Update sync state after successful sync"""
        self._state.last_sync_time = datetime.now().isoformat()
        self._state.last_sync_hash = content_hash
        self._state.status = SyncStatus.IDLE.value
        self._state.conflicts = []
        self._save_state()

    # ==========================================
    # Settings
    # ==========================================

    @property
    def conflict_strategy(self) -> ConflictStrategy:
        """Get conflict resolution strategy"""
        return self._conflict_strategy

    @conflict_strategy.setter
    def conflict_strategy(self, strategy: ConflictStrategy) -> None:
        """Set conflict resolution strategy"""
        self._conflict_strategy = strategy

    @property
    def last_sync_time(self) -> Optional[str]:
        """Get last sync time"""
        return self._state.last_sync_time

    @property
    def sync_status(self) -> SyncStatus:
        """Get current sync status"""
        return SyncStatus(self._state.status)

    def get_state(self) -> SyncState:
        """Get full sync state"""
        return self._state

    # ==========================================
    # Cleanup
    # ==========================================

    def cleanup(self) -> None:
        """Cleanup resources"""
        self._save_state()
        if self._provider:
            self._provider.disconnect()
        logger.info("CloudSyncService cleaned up")
