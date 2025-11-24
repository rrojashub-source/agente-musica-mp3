"""
Remote Control Server
REST API for controlling NEXUS Music Manager from mobile devices

Features:
- Playback control (play, pause, skip, previous, volume)
- Queue management
- Library search
- Now playing info
- Mobile-friendly web interface

Usage:
    server = RemoteServer.get_instance()
    server.start(port=8080)
"""
import os
import json
import socket
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, asdict
from functools import wraps

try:
    from flask import Flask, jsonify, request, send_from_directory, render_template_string
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

try:
    import qrcode
    from io import BytesIO
    import base64
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    from PyQt6.QtCore import QObject, pyqtSignal
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QObject = object

logger = logging.getLogger(__name__)


@dataclass
class NowPlayingInfo:
    """Current playback state"""
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: int = 0
    position: int = 0
    is_playing: bool = False
    volume: int = 100
    cover_url: str = ""


@dataclass
class QueueItem:
    """Queue item info"""
    id: int
    title: str
    artist: str
    duration: int


class RemoteServer(QObject if HAS_QT else object):
    """
    REST API server for remote control.

    Provides endpoints for:
    - GET /api/status - Current playback status
    - POST /api/play - Play/resume
    - POST /api/pause - Pause
    - POST /api/next - Next track
    - POST /api/previous - Previous track
    - POST /api/volume - Set volume
    - GET /api/queue - Get queue
    - POST /api/queue/add - Add to queue
    - POST /api/queue/clear - Clear queue
    - GET /api/search - Search library
    - GET / - Mobile web interface
    - GET /qr - QR code for connection
    """

    _instance: Optional['RemoteServer'] = None

    # Signals
    if HAS_QT:
        server_started = pyqtSignal(str, int)  # host, port
        server_stopped = pyqtSignal()
        command_received = pyqtSignal(str, dict)  # command, params
        client_connected = pyqtSignal(str)  # client_ip

    def __init__(self):
        if HAS_QT:
            super().__init__()

        self._app: Optional[Flask] = None
        self._server_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._host = "0.0.0.0"
        self._port = 8080

        # Callbacks for player control
        self._callbacks: Dict[str, Callable] = {}

        # Current state (updated by player service)
        self._now_playing = NowPlayingInfo()
        self._queue: list = []

        if HAS_FLASK:
            self._setup_app()

    @classmethod
    def get_instance(cls) -> 'RemoteServer':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)"""
        if cls._instance and cls._instance._is_running:
            cls._instance.stop()
        cls._instance = None

    def _setup_app(self):
        """Setup Flask application"""
        self._app = Flask(__name__)
        CORS(self._app)  # Allow cross-origin requests

        # Disable Flask logging in production
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)

        self._register_routes()

    def _register_routes(self):
        """Register API routes"""
        app = self._app

        # ==========================================
        # Web Interface
        # ==========================================

        @app.route('/')
        def index():
            """Mobile web interface"""
            return render_template_string(MOBILE_HTML)

        @app.route('/qr')
        def qr_code():
            """Generate QR code for connection"""
            if not HAS_QRCODE:
                return jsonify({'error': 'QR code not available'}), 500

            url = f"http://{self.get_local_ip()}:{self._port}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return jsonify({
                'url': url,
                'qr_image': f"data:image/png;base64,{img_str}"
            })

        # ==========================================
        # Playback Control API
        # ==========================================

        @app.route('/api/status')
        def get_status():
            """Get current playback status"""
            return jsonify({
                'now_playing': asdict(self._now_playing),
                'queue_length': len(self._queue)
            })

        @app.route('/api/play', methods=['POST'])
        def play():
            """Play/resume playback"""
            self._execute_callback('play')
            if HAS_QT:
                self.command_received.emit('play', {})
            return jsonify({'success': True, 'action': 'play'})

        @app.route('/api/pause', methods=['POST'])
        def pause():
            """Pause playback"""
            self._execute_callback('pause')
            if HAS_QT:
                self.command_received.emit('pause', {})
            return jsonify({'success': True, 'action': 'pause'})

        @app.route('/api/toggle', methods=['POST'])
        def toggle():
            """Toggle play/pause"""
            self._execute_callback('toggle')
            if HAS_QT:
                self.command_received.emit('toggle', {})
            return jsonify({'success': True, 'action': 'toggle'})

        @app.route('/api/next', methods=['POST'])
        def next_track():
            """Skip to next track"""
            self._execute_callback('next')
            if HAS_QT:
                self.command_received.emit('next', {})
            return jsonify({'success': True, 'action': 'next'})

        @app.route('/api/previous', methods=['POST'])
        def previous_track():
            """Go to previous track"""
            self._execute_callback('previous')
            if HAS_QT:
                self.command_received.emit('previous', {})
            return jsonify({'success': True, 'action': 'previous'})

        @app.route('/api/volume', methods=['POST'])
        def set_volume():
            """Set volume (0-100)"""
            data = request.get_json() or {}
            volume = data.get('volume', 100)
            volume = max(0, min(100, int(volume)))

            self._execute_callback('volume', volume)
            self._now_playing.volume = volume

            if HAS_QT:
                self.command_received.emit('volume', {'volume': volume})
            return jsonify({'success': True, 'volume': volume})

        @app.route('/api/seek', methods=['POST'])
        def seek():
            """Seek to position (seconds)"""
            data = request.get_json() or {}
            position = data.get('position', 0)

            self._execute_callback('seek', position)
            if HAS_QT:
                self.command_received.emit('seek', {'position': position})
            return jsonify({'success': True, 'position': position})

        # ==========================================
        # Queue API
        # ==========================================

        @app.route('/api/queue')
        def get_queue():
            """Get current queue"""
            return jsonify({
                'queue': [asdict(item) if hasattr(item, '__dataclass_fields__') else item
                         for item in self._queue]
            })

        @app.route('/api/queue/add', methods=['POST'])
        def add_to_queue():
            """Add song to queue"""
            data = request.get_json() or {}
            song_id = data.get('song_id')

            if song_id:
                self._execute_callback('queue_add', song_id)
                if HAS_QT:
                    self.command_received.emit('queue_add', {'song_id': song_id})
                return jsonify({'success': True, 'song_id': song_id})
            return jsonify({'success': False, 'error': 'No song_id provided'}), 400

        @app.route('/api/queue/clear', methods=['POST'])
        def clear_queue():
            """Clear queue"""
            self._execute_callback('queue_clear')
            if HAS_QT:
                self.command_received.emit('queue_clear', {})
            return jsonify({'success': True, 'action': 'queue_clear'})

        # ==========================================
        # Library API
        # ==========================================

        @app.route('/api/search')
        def search():
            """Search library"""
            query = request.args.get('q', '')
            limit = request.args.get('limit', 20, type=int)

            results = self._execute_callback('search', query, limit) or []
            return jsonify({'results': results, 'query': query})

        @app.route('/api/library/recent')
        def recent():
            """Get recently played"""
            limit = request.args.get('limit', 10, type=int)
            results = self._execute_callback('recent', limit) or []
            return jsonify({'results': results})

    def _execute_callback(self, name: str, *args):
        """Execute registered callback"""
        if name in self._callbacks:
            try:
                return self._callbacks[name](*args)
            except Exception as e:
                logger.error(f"Callback error [{name}]: {e}")
        return None

    # ==========================================
    # Public API
    # ==========================================

    def register_callback(self, name: str, callback: Callable) -> None:
        """Register a callback for remote commands"""
        self._callbacks[name] = callback

    def update_now_playing(self, info: NowPlayingInfo) -> None:
        """Update current playback info"""
        self._now_playing = info

    def update_queue(self, queue: list) -> None:
        """Update queue"""
        self._queue = queue

    def start(self, port: int = 8080, host: str = "0.0.0.0") -> bool:
        """Start the server"""
        if not HAS_FLASK:
            logger.error("Flask not installed. Install with: pip install flask flask-cors")
            return False

        if self._is_running:
            logger.warning("Server already running")
            return True

        self._port = port
        self._host = host

        def run_server():
            try:
                self._app.run(host=host, port=port, threaded=True, use_reloader=False)
            except Exception as e:
                logger.error(f"Server error: {e}")

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        self._is_running = True

        local_ip = self.get_local_ip()
        logger.info(f"Remote server started at http://{local_ip}:{port}")

        if HAS_QT:
            self.server_started.emit(local_ip, port)

        return True

    def stop(self) -> None:
        """Stop the server"""
        self._is_running = False
        # Flask doesn't have a clean shutdown, but daemon thread will end with app
        if HAS_QT:
            self.server_stopped.emit()
        logger.info("Remote server stopped")

    @property
    def is_running(self) -> bool:
        """Check if server is running"""
        return self._is_running

    @property
    def url(self) -> str:
        """Get server URL"""
        return f"http://{self.get_local_ip()}:{self._port}"

    @staticmethod
    def get_local_ip() -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


# ==========================================
# Mobile Web Interface HTML
# ==========================================

MOBILE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>NEXUS Remote</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            padding: 20px;
            text-align: center;
            background: rgba(0,0,0,0.3);
        }

        .header h1 {
            font-size: 1.5rem;
            color: #4CAF50;
        }

        .now-playing {
            padding: 30px 20px;
            text-align: center;
            flex: 1;
        }

        .album-art {
            width: 200px;
            height: 200px;
            background: #333;
            border-radius: 10px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 4rem;
        }

        .track-info h2 {
            font-size: 1.3rem;
            margin-bottom: 5px;
        }

        .track-info p {
            color: #aaa;
            font-size: 1rem;
        }

        .progress-bar {
            margin: 20px 0;
            height: 4px;
            background: #333;
            border-radius: 2px;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: #4CAF50;
            border-radius: 2px;
            width: 0%;
            transition: width 0.3s;
        }

        .time-display {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #aaa;
        }

        .controls {
            padding: 20px;
            background: rgba(0,0,0,0.3);
        }

        .main-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            margin-bottom: 20px;
        }

        .control-btn {
            background: none;
            border: none;
            color: #fff;
            font-size: 2rem;
            cursor: pointer;
            padding: 15px;
            border-radius: 50%;
            transition: all 0.2s;
        }

        .control-btn:hover {
            background: rgba(255,255,255,0.1);
        }

        .control-btn:active {
            transform: scale(0.95);
        }

        .play-btn {
            background: #4CAF50;
            font-size: 2.5rem;
            padding: 20px;
        }

        .play-btn:hover {
            background: #45a049;
        }

        .volume-control {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0 20px;
        }

        .volume-slider {
            flex: 1;
            -webkit-appearance: none;
            height: 4px;
            background: #333;
            border-radius: 2px;
        }

        .volume-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            background: #4CAF50;
            border-radius: 50%;
            cursor: pointer;
        }

        .status {
            text-align: center;
            padding: 10px;
            font-size: 0.8rem;
            color: #666;
        }

        .status.connected { color: #4CAF50; }
        .status.disconnected { color: #f44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎵 NEXUS Remote</h1>
    </div>

    <div class="now-playing">
        <div class="album-art" id="albumArt">🎵</div>
        <div class="track-info">
            <h2 id="trackTitle">Not Playing</h2>
            <p id="trackArtist">-</p>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        <div class="time-display">
            <span id="currentTime">0:00</span>
            <span id="totalTime">0:00</span>
        </div>
    </div>

    <div class="controls">
        <div class="main-controls">
            <button class="control-btn" onclick="previous()">⏮️</button>
            <button class="control-btn play-btn" id="playBtn" onclick="togglePlay()">▶️</button>
            <button class="control-btn" onclick="next()">⏭️</button>
        </div>
        <div class="volume-control">
            <span>🔈</span>
            <input type="range" class="volume-slider" id="volumeSlider"
                   min="0" max="100" value="100" onchange="setVolume(this.value)">
            <span>🔊</span>
        </div>
    </div>

    <div class="status" id="status">Connecting...</div>

    <script>
        let isPlaying = false;

        function formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }

        function updateUI(data) {
            const np = data.now_playing;
            document.getElementById('trackTitle').textContent = np.title || 'Not Playing';
            document.getElementById('trackArtist').textContent = np.artist || '-';
            document.getElementById('currentTime').textContent = formatTime(np.position);
            document.getElementById('totalTime').textContent = formatTime(np.duration);

            const progress = np.duration > 0 ? (np.position / np.duration) * 100 : 0;
            document.getElementById('progressFill').style.width = progress + '%';

            document.getElementById('volumeSlider').value = np.volume;

            isPlaying = np.is_playing;
            document.getElementById('playBtn').textContent = isPlaying ? '⏸️' : '▶️';
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                updateUI(data);
                document.getElementById('status').textContent = 'Connected';
                document.getElementById('status').className = 'status connected';
            } catch (e) {
                document.getElementById('status').textContent = 'Disconnected';
                document.getElementById('status').className = 'status disconnected';
            }
        }

        async function togglePlay() {
            await fetch('/api/toggle', { method: 'POST' });
            fetchStatus();
        }

        async function next() {
            await fetch('/api/next', { method: 'POST' });
            fetchStatus();
        }

        async function previous() {
            await fetch('/api/previous', { method: 'POST' });
            fetchStatus();
        }

        async function setVolume(value) {
            await fetch('/api/volume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ volume: parseInt(value) })
            });
        }

        // Poll for updates
        setInterval(fetchStatus, 1000);
        fetchStatus();
    </script>
</body>
</html>
'''
