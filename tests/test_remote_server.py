"""
Tests for Remote Control Server
"""
import sys
import os
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Check for Flask and flask-cors
try:
    import flask
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from services.remote_server import RemoteServer, NowPlayingInfo, QueueItem


# ==========================================
# Data Model Tests
# ==========================================

class TestDataModels:
    """Tests for data models"""

    def test_now_playing_info_defaults(self):
        """Test NowPlayingInfo default values"""
        info = NowPlayingInfo()

        assert info.title == ""
        assert info.artist == ""
        assert info.album == ""
        assert info.duration == 0
        assert info.position == 0
        assert info.is_playing is False
        assert info.volume == 100

    def test_now_playing_info_custom(self):
        """Test NowPlayingInfo with custom values"""
        info = NowPlayingInfo(
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            duration=180,
            position=45,
            is_playing=True,
            volume=75
        )

        assert info.title == "Test Song"
        assert info.artist == "Test Artist"
        assert info.is_playing is True
        assert info.volume == 75

    def test_queue_item(self):
        """Test QueueItem"""
        item = QueueItem(
            id=1,
            title="Song",
            artist="Artist",
            duration=200
        )

        assert item.id == 1
        assert item.title == "Song"


# ==========================================
# Remote Server Tests
# ==========================================

class TestRemoteServer:
    """Tests for RemoteServer"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        RemoteServer.reset_instance()
        yield
        RemoteServer.reset_instance()

    def test_singleton_pattern(self):
        """Test singleton pattern"""
        server1 = RemoteServer.get_instance()
        server2 = RemoteServer.get_instance()

        assert server1 is server2

    def test_initial_state(self):
        """Test initial server state"""
        server = RemoteServer.get_instance()

        assert not server.is_running
        assert server._now_playing.title == ""
        assert server._queue == []

    def test_update_now_playing(self):
        """Test updating now playing info"""
        server = RemoteServer.get_instance()

        info = NowPlayingInfo(
            title="Test Song",
            artist="Test Artist",
            is_playing=True
        )
        server.update_now_playing(info)

        assert server._now_playing.title == "Test Song"
        assert server._now_playing.is_playing is True

    def test_update_queue(self):
        """Test updating queue"""
        server = RemoteServer.get_instance()

        queue = [
            {'id': 1, 'title': 'Song 1'},
            {'id': 2, 'title': 'Song 2'}
        ]
        server.update_queue(queue)

        assert len(server._queue) == 2
        assert server._queue[0]['title'] == 'Song 1'

    def test_register_callback(self):
        """Test registering callbacks"""
        server = RemoteServer.get_instance()

        callback = Mock()
        server.register_callback('play', callback)

        # Verify callback is registered
        assert 'play' in server._callbacks
        assert server._callbacks['play'] is callback

    def test_execute_callback(self):
        """Test executing callbacks"""
        server = RemoteServer.get_instance()

        callback = Mock(return_value="result")
        server.register_callback('test', callback)

        result = server._execute_callback('test', 'arg1', 'arg2')

        callback.assert_called_once_with('arg1', 'arg2')
        assert result == "result"

    def test_execute_callback_not_registered(self):
        """Test executing non-existent callback"""
        server = RemoteServer.get_instance()

        result = server._execute_callback('nonexistent')
        assert result is None

    def test_get_local_ip(self):
        """Test getting local IP"""
        ip = RemoteServer.get_local_ip()

        # Should be a valid IP or localhost
        assert ip is not None
        parts = ip.split('.')
        assert len(parts) == 4 or ip == "127.0.0.1"


# ==========================================
# API Endpoint Tests (with Flask test client)
# ==========================================

@pytest.mark.skipif(not HAS_FLASK, reason="Flask/flask-cors not installed")
class TestRemoteServerAPI:
    """Tests for REST API endpoints"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        RemoteServer.reset_instance()
        yield
        RemoteServer.reset_instance()

    @pytest.fixture
    def client(self):
        """Create test client"""
        server = RemoteServer.get_instance()
        if server._app is None:
            pytest.skip("Flask app not initialized")
        server._app.config['TESTING'] = True
        return server._app.test_client()

    def test_status_endpoint(self, client):
        """Test GET /api/status"""
        response = client.get('/api/status')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'now_playing' in data
        assert 'queue_length' in data

    def test_play_endpoint(self, client):
        """Test POST /api/play"""
        response = client.post('/api/play')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['action'] == 'play'

    def test_pause_endpoint(self, client):
        """Test POST /api/pause"""
        response = client.post('/api/pause')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['action'] == 'pause'

    def test_toggle_endpoint(self, client):
        """Test POST /api/toggle"""
        response = client.post('/api/toggle')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['action'] == 'toggle'

    def test_next_endpoint(self, client):
        """Test POST /api/next"""
        response = client.post('/api/next')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['action'] == 'next'

    def test_previous_endpoint(self, client):
        """Test POST /api/previous"""
        response = client.post('/api/previous')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['action'] == 'previous'

    def test_volume_endpoint(self, client):
        """Test POST /api/volume"""
        response = client.post(
            '/api/volume',
            data=json.dumps({'volume': 75}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['volume'] == 75

    def test_volume_endpoint_clamps_value(self, client):
        """Test volume is clamped to 0-100"""
        # Test over 100
        response = client.post(
            '/api/volume',
            data=json.dumps({'volume': 150}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert data['volume'] == 100

        # Test under 0
        response = client.post(
            '/api/volume',
            data=json.dumps({'volume': -50}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert data['volume'] == 0

    def test_seek_endpoint(self, client):
        """Test POST /api/seek"""
        response = client.post(
            '/api/seek',
            data=json.dumps({'position': 60}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['position'] == 60

    def test_queue_endpoint(self, client):
        """Test GET /api/queue"""
        server = RemoteServer.get_instance()
        server.update_queue([{'id': 1, 'title': 'Test'}])

        response = client.get('/api/queue')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'queue' in data
        assert len(data['queue']) == 1

    def test_queue_add_endpoint(self, client):
        """Test POST /api/queue/add"""
        response = client.post(
            '/api/queue/add',
            data=json.dumps({'song_id': 123}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['song_id'] == 123

    def test_queue_add_no_id(self, client):
        """Test queue/add without song_id"""
        response = client.post(
            '/api/queue/add',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_queue_clear_endpoint(self, client):
        """Test POST /api/queue/clear"""
        response = client.post('/api/queue/clear')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_search_endpoint(self, client):
        """Test GET /api/search"""
        server = RemoteServer.get_instance()
        server.register_callback('search', lambda q, l: [{'title': 'Result'}])

        response = client.get('/api/search?q=test&limit=10')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert data['query'] == 'test'

    def test_index_returns_html(self, client):
        """Test GET / returns HTML"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'NEXUS Remote' in response.data
        assert b'html' in response.data


# ==========================================
# Callback Integration Tests
# ==========================================

@pytest.mark.skipif(not HAS_FLASK, reason="Flask/flask-cors not installed")
class TestRemoteServerCallbacks:
    """Tests for callback integration"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test"""
        RemoteServer.reset_instance()
        yield
        RemoteServer.reset_instance()

    @pytest.fixture
    def client(self):
        """Create test client"""
        server = RemoteServer.get_instance()
        if server._app is None:
            pytest.skip("Flask app not initialized")
        server._app.config['TESTING'] = True
        return server._app.test_client()

    def test_play_triggers_callback(self, client):
        """Test play endpoint triggers callback"""
        server = RemoteServer.get_instance()
        callback = Mock()
        server.register_callback('play', callback)

        client.post('/api/play')

        callback.assert_called_once()

    def test_volume_triggers_callback_with_value(self, client):
        """Test volume endpoint passes value to callback"""
        server = RemoteServer.get_instance()
        callback = Mock()
        server.register_callback('volume', callback)

        client.post(
            '/api/volume',
            data=json.dumps({'volume': 50}),
            content_type='application/json'
        )

        callback.assert_called_once_with(50)

    def test_search_uses_callback_result(self, client):
        """Test search endpoint uses callback result"""
        server = RemoteServer.get_instance()
        server.register_callback('search', lambda q, l: [
            {'id': 1, 'title': f'Result for {q}'}
        ])

        response = client.get('/api/search?q=hello')
        data = json.loads(response.data)

        assert len(data['results']) == 1
        assert data['results'][0]['title'] == 'Result for hello'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
