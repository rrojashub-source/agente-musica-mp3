"""
Tests for Cloud Sync Service
"""
import sys
import os
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Skip all if PyQt6 not available
try:
    from PyQt6.QtCore import QCoreApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False

pytestmark = pytest.mark.skipif(not HAS_QT, reason="PyQt6 not available")


@pytest.fixture(scope='module')
def qapp():
    """Create QCoreApplication for signal testing"""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


# ==========================================
# Data Model Tests
# ==========================================

class TestDataModels:
    """Tests for sync data models"""

    def test_sync_status_enum(self):
        """Test SyncStatus enum values"""
        from services.cloud_sync_service import SyncStatus

        assert SyncStatus.IDLE.value == "idle"
        assert SyncStatus.SYNCING.value == "syncing"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"

    def test_conflict_strategy_enum(self):
        """Test ConflictStrategy enum values"""
        from services.cloud_sync_service import ConflictStrategy

        assert ConflictStrategy.NEWER_WINS.value == "newer_wins"
        assert ConflictStrategy.LOCAL_WINS.value == "local_wins"
        assert ConflictStrategy.REMOTE_WINS.value == "remote_wins"

    def test_sync_state_dataclass(self):
        """Test SyncState dataclass"""
        from services.cloud_sync_service import SyncState

        state = SyncState(
            last_sync_time="2025-11-24T10:00:00",
            last_sync_hash="abc123",
            provider="Local Folder"
        )

        assert state.last_sync_time == "2025-11-24T10:00:00"
        assert state.last_sync_hash == "abc123"

        # Test serialization
        data = state.to_dict()
        restored = SyncState.from_dict(data)
        assert restored.last_sync_time == state.last_sync_time

    def test_library_export_dataclass(self):
        """Test LibraryExport dataclass"""
        from services.cloud_sync_service import LibraryExport

        export = LibraryExport(
            version="1.0",
            exported_at="2025-11-24T10:00:00",
            device_id="test-device",
            songs=[
                {'id': 1, 'title': 'Song 1', 'artist': 'Artist 1'},
                {'id': 2, 'title': 'Song 2', 'artist': 'Artist 2'},
            ],
            playlists=[
                {'id': 1, 'name': 'Playlist 1', 'song_ids': [1, 2]}
            ]
        )

        assert export.version == "1.0"
        assert len(export.songs) == 2
        assert len(export.playlists) == 1

        # Test hash computation
        hash1 = export.compute_hash()
        assert len(hash1) == 16

        # Same content = same hash
        export2 = LibraryExport(
            version="1.0",
            exported_at="different-time",
            device_id="different-device",
            songs=[
                {'id': 1, 'title': 'Song 1', 'artist': 'Artist 1'},
                {'id': 2, 'title': 'Song 2', 'artist': 'Artist 2'},
            ],
            playlists=[
                {'id': 1, 'name': 'Playlist 1', 'song_ids': [1, 2]}
            ]
        )
        assert export.compute_hash() == export2.compute_hash()

    def test_library_export_different_content_different_hash(self):
        """Test that different content produces different hash"""
        from services.cloud_sync_service import LibraryExport

        export1 = LibraryExport(songs=[{'id': 1, 'title': 'Song 1'}])
        export2 = LibraryExport(songs=[{'id': 2, 'title': 'Song 2'}])

        assert export1.compute_hash() != export2.compute_hash()


# ==========================================
# LocalFolderProvider Tests
# ==========================================

class TestLocalFolderProvider:
    """Tests for LocalFolderProvider"""

    @pytest.fixture
    def provider(self, tmp_path):
        """Create provider with temp folder"""
        from services.cloud_sync_service import LocalFolderProvider
        return LocalFolderProvider(str(tmp_path / "sync"))

    def test_connect_creates_folder(self, provider, tmp_path):
        """Test connect creates sync folder"""
        result = provider.connect()

        assert result is True
        assert provider.is_connected
        assert (tmp_path / "sync").exists()

    def test_connect_without_folder_fails(self):
        """Test connect without folder configured fails"""
        from services.cloud_sync_service import LocalFolderProvider

        provider = LocalFolderProvider(None)
        result = provider.connect()

        assert result is False
        assert not provider.is_connected

    def test_upload_and_download(self, provider, tmp_path):
        """Test upload and download file"""
        provider.connect()

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Upload
        result = provider.upload(str(test_file), "remote/test.txt")
        assert result is True
        assert provider.exists("remote/test.txt")

        # Download
        download_path = tmp_path / "downloaded.txt"
        result = provider.download("remote/test.txt", str(download_path))
        assert result is True
        assert download_path.read_text() == "Hello, World!"

    def test_exists(self, provider, tmp_path):
        """Test exists check"""
        provider.connect()

        assert not provider.exists("nonexistent.txt")

        # Create file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        provider.upload(str(test_file), "exists.txt")

        assert provider.exists("exists.txt")

    def test_get_modified_time(self, provider, tmp_path):
        """Test get modified time"""
        provider.connect()

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        provider.upload(str(test_file), "timed.txt")

        mod_time = provider.get_modified_time("timed.txt")
        assert mod_time is not None
        assert isinstance(mod_time, datetime)

    def test_delete(self, provider, tmp_path):
        """Test delete file"""
        provider.connect()

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        provider.upload(str(test_file), "to_delete.txt")

        assert provider.exists("to_delete.txt")

        result = provider.delete("to_delete.txt")
        assert result is True
        assert not provider.exists("to_delete.txt")

    def test_provider_name(self, provider):
        """Test provider name"""
        assert provider.name == "Local Folder"

    def test_disconnect(self, provider):
        """Test disconnect"""
        provider.connect()
        assert provider.is_connected

        provider.disconnect()
        assert not provider.is_connected


# ==========================================
# CloudSyncService Tests
# ==========================================

class TestCloudSyncService:
    """Tests for CloudSyncService"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        from services.cloud_sync_service import CloudSyncService
        CloudSyncService.reset_instance()
        yield
        CloudSyncService.reset_instance()

    @pytest.fixture
    def service(self, tmp_path, qapp):
        """Create service with temp data dir"""
        from services.cloud_sync_service import CloudSyncService
        return CloudSyncService.get_instance(str(tmp_path / "data"))

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider"""
        provider = MagicMock()
        provider.name = "Mock Provider"
        provider.is_connected = True
        provider.connect.return_value = True
        provider.exists.return_value = False
        provider.upload.return_value = True
        provider.download.return_value = True
        return provider

    def test_singleton_pattern(self, tmp_path, qapp):
        """Test CloudSyncService is singleton"""
        from services.cloud_sync_service import CloudSyncService

        service1 = CloudSyncService.get_instance(str(tmp_path / "data1"))
        service2 = CloudSyncService.get_instance(str(tmp_path / "data2"))

        assert service1 is service2

    def test_set_provider(self, service, mock_provider):
        """Test setting cloud provider"""
        result = service.set_provider(mock_provider)

        assert result is True
        assert service.get_provider() is mock_provider

    def test_connect(self, service, mock_provider):
        """Test connecting to provider"""
        service.set_provider(mock_provider)
        result = service.connect()

        assert result is True
        mock_provider.connect.assert_called_once()

    def test_connect_without_provider_fails(self, service):
        """Test connect without provider fails"""
        signal_received = []
        service.sync_failed.connect(lambda x: signal_received.append(x))

        result = service.connect()

        assert result is False

    def test_export_library(self, service, qapp):
        """Test exporting library"""
        # Create mock database
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = [
            {'id': 1, 'title': 'Song 1', 'artist': 'Artist 1', 'file_path': '/path/1.mp3'},
            {'id': 2, 'title': 'Song 2', 'artist': 'Artist 2', 'file_path': '/path/2.mp3'},
        ]

        export = service.export_library(mock_db)

        assert export.version == "1.0"
        assert len(export.songs) == 2
        assert export.device_id is not None

    def test_import_library(self, service, qapp):
        """Test importing library"""
        from services.cloud_sync_service import LibraryExport

        export = LibraryExport(
            songs=[
                {'title': 'Song 1', 'artist': 'Artist 1', 'file_path': '/path/1.mp3'},
                {'title': 'Song 2', 'artist': 'Artist 2', 'file_path': '/path/2.mp3'},
            ]
        )

        mock_db = MagicMock()
        mock_db.fetch_one.return_value = None  # No existing songs
        mock_db.add_song.return_value = 1

        stats = service.import_library(export, mock_db)

        assert stats['added'] == 2
        assert mock_db.add_song.call_count == 2

    def test_sync_new_library(self, service, mock_provider, tmp_path, qapp):
        """Test syncing new library (no remote exists)"""
        service.set_provider(mock_provider)
        service.connect()

        mock_db = MagicMock()
        mock_db.fetch_all.return_value = [
            {'id': 1, 'title': 'Song 1', 'file_path': '/path/1.mp3'}
        ]

        # Track signals
        completed_signals = []
        service.sync_completed.connect(lambda s, m: completed_signals.append((s, m)))

        result = service.sync(mock_db)

        assert result is True
        mock_provider.upload.assert_called_once()
        assert len(completed_signals) == 1
        assert completed_signals[0][0] is True

    def test_sync_not_connected_fails(self, service, qapp):
        """Test sync fails when not connected"""
        failed_signals = []
        service.sync_failed.connect(lambda x: failed_signals.append(x))

        result = service.sync()

        assert result is False
        assert len(failed_signals) == 1

    def test_conflict_strategy(self, service):
        """Test conflict strategy setting"""
        from services.cloud_sync_service import ConflictStrategy

        assert service.conflict_strategy == ConflictStrategy.NEWER_WINS

        service.conflict_strategy = ConflictStrategy.LOCAL_WINS
        assert service.conflict_strategy == ConflictStrategy.LOCAL_WINS

    def test_sync_state_persistence(self, tmp_path, qapp):
        """Test sync state is persisted"""
        from services.cloud_sync_service import CloudSyncService

        # Create service and update state
        service1 = CloudSyncService.get_instance(str(tmp_path / "data"))
        service1._state.last_sync_time = "2025-11-24T10:00:00"
        service1._save_state()

        # Reset singleton
        CloudSyncService.reset_instance()

        # Create new service - should load saved state
        service2 = CloudSyncService.get_instance(str(tmp_path / "data"))

        assert service2._state.last_sync_time == "2025-11-24T10:00:00"

    def test_device_id_persistence(self, tmp_path, qapp):
        """Test device ID is persistent"""
        from services.cloud_sync_service import CloudSyncService

        service1 = CloudSyncService.get_instance(str(tmp_path / "data"))
        device_id1 = service1._device_id

        CloudSyncService.reset_instance()

        service2 = CloudSyncService.get_instance(str(tmp_path / "data"))
        device_id2 = service2._device_id

        assert device_id1 == device_id2


# ==========================================
# Merge Tests
# ==========================================

class TestMerge:
    """Tests for library merge logic"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton"""
        from services.cloud_sync_service import CloudSyncService
        CloudSyncService.reset_instance()
        yield
        CloudSyncService.reset_instance()

    def test_merge_adds_new_songs(self, tmp_path, qapp):
        """Test merge adds songs from both sources"""
        from services.cloud_sync_service import CloudSyncService, LibraryExport

        service = CloudSyncService.get_instance(str(tmp_path))

        local = LibraryExport(songs=[
            {'id': 1, 'title': 'Local Song', 'file_path': '/local.mp3'}
        ])
        remote = LibraryExport(songs=[
            {'id': 2, 'title': 'Remote Song', 'file_path': '/remote.mp3'}
        ])

        merged = service._merge_exports(local, remote)

        assert len(merged.songs) == 2
        paths = [s['file_path'] for s in merged.songs]
        assert '/local.mp3' in paths
        assert '/remote.mp3' in paths

    def test_merge_conflict_newer_wins(self, tmp_path, qapp):
        """Test merge with newer_wins strategy"""
        from services.cloud_sync_service import CloudSyncService, LibraryExport, ConflictStrategy

        service = CloudSyncService.get_instance(str(tmp_path))
        service.conflict_strategy = ConflictStrategy.NEWER_WINS

        local = LibraryExport(songs=[
            {'id': 1, 'title': 'Local Version', 'file_path': '/same.mp3', 'date_modified': '2025-11-24T12:00:00'}
        ])
        remote = LibraryExport(songs=[
            {'id': 1, 'title': 'Remote Version', 'file_path': '/same.mp3', 'date_modified': '2025-11-24T10:00:00'}
        ])

        merged = service._merge_exports(local, remote)

        assert len(merged.songs) == 1
        assert merged.songs[0]['title'] == 'Local Version'  # Newer

    def test_merge_conflict_local_wins(self, tmp_path, qapp):
        """Test merge with local_wins strategy"""
        from services.cloud_sync_service import CloudSyncService, LibraryExport, ConflictStrategy

        service = CloudSyncService.get_instance(str(tmp_path))
        service.conflict_strategy = ConflictStrategy.LOCAL_WINS

        local = LibraryExport(songs=[
            {'id': 1, 'title': 'Local Version', 'file_path': '/same.mp3'}
        ])
        remote = LibraryExport(songs=[
            {'id': 1, 'title': 'Remote Version', 'file_path': '/same.mp3'}
        ])

        merged = service._merge_exports(local, remote)

        assert merged.songs[0]['title'] == 'Local Version'


# ==========================================
# Integration Tests
# ==========================================

class TestCloudSyncIntegration:
    """Integration tests for cloud sync"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton"""
        from services.cloud_sync_service import CloudSyncService
        CloudSyncService.reset_instance()
        yield
        CloudSyncService.reset_instance()

    def test_full_sync_cycle_with_local_provider(self, tmp_path, qapp):
        """Test full sync cycle with LocalFolderProvider"""
        from services.cloud_sync_service import CloudSyncService, LocalFolderProvider

        # Setup
        data_dir = tmp_path / "data"
        sync_dir = tmp_path / "sync"

        service = CloudSyncService.get_instance(str(data_dir))
        provider = LocalFolderProvider(str(sync_dir))
        service.set_provider(provider)
        service.connect()

        # Create mock database
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = [
            {'id': 1, 'title': 'Test Song', 'artist': 'Test Artist', 'file_path': '/test.mp3'}
        ]

        # First sync (upload)
        result = service.sync(mock_db)

        assert result is True
        assert provider.exists(CloudSyncService.SYNC_FILENAME)
        assert service.last_sync_time is not None

        # Verify uploaded content
        sync_file = sync_dir / CloudSyncService.SYNC_FILENAME
        data = json.loads(sync_file.read_text())
        assert len(data['songs']) == 1
        assert data['songs'][0]['title'] == 'Test Song'


# ==========================================
# GUI Tests (require display)
# ==========================================
# Note: These tests require a display (X11/Wayland) and may fail in headless WSL.
# Run with: pytest tests/test_cloud_sync.py::TestCloudSyncTab -v
# Or skip with: pytest tests/test_cloud_sync.py -k "not Tab"

class TestCloudSyncTab:
    """Tests for CloudSyncTab GUI - requires display"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton"""
        from services.cloud_sync_service import CloudSyncService
        CloudSyncService.reset_instance()
        yield
        CloudSyncService.reset_instance()

    @pytest.mark.skipif(
        not os.environ.get('DISPLAY') and not os.environ.get('QT_QPA_PLATFORM'),
        reason="Requires display or QT_QPA_PLATFORM=offscreen"
    )
    def test_tab_creation(self, qapp):
        """Test CloudSyncTab can be created"""
        from gui.tabs.cloud_sync_tab import CloudSyncTab

        tab = CloudSyncTab()
        assert tab is not None
        assert hasattr(tab, 'sync_service')
        assert hasattr(tab, 'provider_combo')
        assert hasattr(tab, 'sync_btn')

    @pytest.mark.skipif(
        not os.environ.get('DISPLAY') and not os.environ.get('QT_QPA_PLATFORM'),
        reason="Requires display or QT_QPA_PLATFORM=offscreen"
    )
    def test_tab_has_required_widgets(self, qapp):
        """Test tab has all required widgets"""
        from gui.tabs.cloud_sync_tab import CloudSyncTab

        tab = CloudSyncTab()

        # Provider selection
        assert tab.provider_combo is not None
        assert tab.provider_combo.count() == 2  # Local + Google Drive

        # Folder selection
        assert tab.folder_input is not None
        assert tab.browse_btn is not None

        # Status displays
        assert tab.connection_status is not None
        assert tab.last_sync_status is not None
        assert tab.device_id_label is not None

        # Action buttons
        assert tab.sync_btn is not None
        assert tab.export_btn is not None
        assert tab.import_btn is not None

        # Progress
        assert tab.progress_bar is not None
        assert tab.log_text is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
