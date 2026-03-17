"""
Remote Control Server
REST API for controlling NEXUS Music Manager from mobile devices

Features:
- Playback control (play, pause, skip, previous, volume)
- Queue management
- Library search
- Now playing info
- Mobile-friendly web interface

Security:
- Bearer token authentication (24h expiry + refresh)
- Rate limiting (60 req/min per IP)
- CORS restricted to local network
- Token removed from browser history via replaceState

Known limitation: HTTP only (no TLS). Auth token is visible in plaintext
on the local network. Acceptable for LAN-only music remote control;
do not expose this server to the public internet.

Usage:
    server = RemoteServer.get_instance()
    server.start(port=8080)
"""

import hmac
import logging
import secrets
import socket
import threading
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

try:
    from flask import Flask, jsonify, render_template_string, request
    from flask_cors import CORS

    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

try:
    import base64
    from io import BytesIO

    import qrcode

    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    from PySide6.QtCore import QObject, Signal

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


class RemoteServer(QObject if HAS_QT else object):  # type: ignore[misc]
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

    _instance: Optional["RemoteServer"] = None
    _lock: threading.Lock = threading.Lock()

    # Signals
    if HAS_QT:
        server_started = Signal(str, int)  # host, port
        server_stopped = Signal()
        command_received = Signal(str, dict)  # command, params
        client_connected = Signal(str)  # client_ip

    def __init__(self) -> None:
        if HAS_QT:
            super().__init__()

        self._app: Optional[Any] = None
        self._server_thread: Optional[threading.Thread] = None
        self._is_running: bool = False
        self._host: str = "127.0.0.1"
        self._port: int = 8080

        # Auth token with expiration (24h)
        self._token_max_age: int = 86400  # 24 hours in seconds
        self._auth_token: str = self._generate_token()

        # Rate limiting per IP: {ip: [timestamps]}
        self._rate_limit_requests: Dict[str, List[float]] = defaultdict(list)
        self._rate_limit_max: int = 60  # requests per minute
        self._rate_limit_window: int = 60  # seconds

        # Lock for shared state accessed by Flask request threads
        self._data_lock: threading.RLock = threading.RLock()

        # Callbacks for player control
        self._callbacks: Dict[str, Callable[..., Any]] = {}

        # Current state (updated by player service)
        self._now_playing: NowPlayingInfo = NowPlayingInfo()
        self._queue: List[Any] = []

        if HAS_FLASK:
            self._setup_app()

    @classmethod
    def get_instance(cls) -> "RemoteServer":
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)"""
        if cls._instance and cls._instance._is_running:
            cls._instance.stop()
        cls._instance = None

    def _setup_app(self) -> None:
        """Setup Flask application with security hardening"""
        self._app = Flask(__name__)

        # CORS: only allow localhost and this server's IP
        CORS(
            self._app,
            origins=[
                "http://127.0.0.1:*",
                "http://localhost:*",
                f"http://{self.get_local_ip()}:*",
            ],
        )

        # Disable Flask logging in production
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.WARNING)

        # Rate limiting middleware
        @self._app.before_request
        def _rate_limit() -> Any:
            client_ip = request.remote_addr or "unknown"
            now = time.time()
            window_start = now - self._rate_limit_window

            with self._data_lock:
                # Clean old entries
                self._rate_limit_requests[client_ip] = [
                    t for t in self._rate_limit_requests[client_ip] if t > window_start
                ]

                if len(self._rate_limit_requests[client_ip]) >= self._rate_limit_max:
                    logger.warning(f"Rate limit exceeded for {client_ip}")
                    return jsonify({"error": "Rate limit exceeded"}), 429

                self._rate_limit_requests[client_ip].append(now)

        self._register_routes()

    def _require_auth(self, f: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator: require valid auth token in Authorization Bearer header only"""

        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            auth_header = request.headers.get("Authorization", "")
            token = None
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

            if not token or not self._validate_token(token):
                logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
                return jsonify({"error": "Unauthorized"}), 401

            return f(*args, **kwargs)

        return decorated

    def _generate_token(self) -> str:
        """Generate a token with embedded timestamp for expiration"""
        return f"{secrets.token_urlsafe(32)}.{int(time.time())}"

    def _validate_token(self, token: str) -> bool:
        """Validate token matches and has not expired"""
        if not hmac.compare_digest(token, self._auth_token):
            return False
        try:
            timestamp = int(token.rsplit(".", 1)[1])
            return (time.time() - timestamp) < self._token_max_age
        except (IndexError, ValueError):
            return False

    def _register_routes(self) -> None:
        """Register API routes"""
        app = self._app

        # ==========================================
        # Web Interface
        # ==========================================

        @app.route("/")  # type: ignore[union-attr]
        def index() -> Any:
            """Mobile web interface — requires token in query param (initial load via QR)"""
            token = request.args.get("token", "")
            if not self._validate_token(token):
                return jsonify({"error": "Unauthorized. Scan QR code to connect."}), 401
            return render_template_string(MOBILE_HTML, auth_token=self._auth_token)

        @app.route("/qr")  # type: ignore[union-attr]
        @self._require_auth
        def qr_code() -> Any:
            """Generate QR code for connection (includes auth token)"""
            if not HAS_QRCODE:
                return jsonify({"error": "QR code not available"}), 500

            url = f"http://{self.get_local_ip()}:{self._port}?token={self._auth_token}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return jsonify({"url": url, "qr_image": f"data:image/png;base64,{img_str}"})

        # ==========================================
        # Playback Control API
        # ==========================================

        @app.route("/api/status")  # type: ignore[union-attr]
        @self._require_auth
        def get_status() -> Any:
            """Get current playback status"""
            with self._data_lock:
                return jsonify({"now_playing": asdict(self._now_playing), "queue_length": len(self._queue)})

        @app.route("/api/play", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def play() -> Any:
            """Play/resume playback"""
            self._execute_callback("play")
            if HAS_QT:
                self.command_received.emit("play", {})
            return jsonify({"success": True, "action": "play"})

        @app.route("/api/pause", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def pause() -> Any:
            """Pause playback"""
            self._execute_callback("pause")
            if HAS_QT:
                self.command_received.emit("pause", {})
            return jsonify({"success": True, "action": "pause"})

        @app.route("/api/toggle", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def toggle() -> Any:
            """Toggle play/pause"""
            self._execute_callback("toggle")
            if HAS_QT:
                self.command_received.emit("toggle", {})
            return jsonify({"success": True, "action": "toggle"})

        @app.route("/api/next", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def next_track() -> Any:
            """Skip to next track"""
            self._execute_callback("next")
            if HAS_QT:
                self.command_received.emit("next", {})
            return jsonify({"success": True, "action": "next"})

        @app.route("/api/previous", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def previous_track() -> Any:
            """Go to previous track"""
            self._execute_callback("previous")
            if HAS_QT:
                self.command_received.emit("previous", {})
            return jsonify({"success": True, "action": "previous"})

        @app.route("/api/volume", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def set_volume() -> Any:
            """Set volume (0-100)"""
            data = request.get_json() or {}
            volume = data.get("volume", 100)
            volume = max(0, min(100, int(volume)))

            self._execute_callback("volume", volume)
            with self._data_lock:
                self._now_playing.volume = volume

            if HAS_QT:
                self.command_received.emit("volume", {"volume": volume})
            return jsonify({"success": True, "volume": volume})

        @app.route("/api/seek", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def seek() -> Any:
            """Seek to position (seconds)"""
            data = request.get_json() or {}
            try:
                position = max(0, int(data.get("position", 0)))
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid position value"}), 400

            self._execute_callback("seek", position)
            if HAS_QT:
                self.command_received.emit("seek", {"position": position})
            return jsonify({"success": True, "position": position})

        # ==========================================
        # Queue API
        # ==========================================

        @app.route("/api/queue")  # type: ignore[union-attr]
        @self._require_auth
        def get_queue() -> Any:
            """Get current queue"""
            with self._data_lock:
                queue_copy = list(self._queue)
            return jsonify(
                {"queue": [asdict(item) if hasattr(item, "__dataclass_fields__") else item for item in queue_copy]}
            )

        @app.route("/api/queue/add", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def add_to_queue() -> Any:
            """Add song to queue"""
            data = request.get_json() or {}
            song_id = data.get("song_id")

            if song_id:
                self._execute_callback("queue_add", song_id)
                if HAS_QT:
                    self.command_received.emit("queue_add", {"song_id": song_id})
                return jsonify({"success": True, "song_id": song_id})
            return jsonify({"success": False, "error": "No song_id provided"}), 400

        @app.route("/api/queue/clear", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def clear_queue() -> Any:
            """Clear queue"""
            self._execute_callback("queue_clear")
            if HAS_QT:
                self.command_received.emit("queue_clear", {})
            return jsonify({"success": True, "action": "queue_clear"})

        # ==========================================
        # Library API
        # ==========================================

        @app.route("/api/search")  # type: ignore[union-attr]
        @self._require_auth
        def search() -> Any:
            """Search library"""
            query = request.args.get("q", "")
            limit = min(request.args.get("limit", 20, type=int), 200)

            results = self._execute_callback("search", query, limit) or []
            return jsonify({"results": results, "query": query})

        @app.route("/api/library/recent")  # type: ignore[union-attr]
        @self._require_auth
        def recent() -> Any:
            """Get recently played"""
            limit = min(request.args.get("limit", 10, type=int), 200)
            results = self._execute_callback("recent", limit) or []
            return jsonify({"results": results})

        @app.route("/api/refresh-token", methods=["POST"])  # type: ignore[union-attr]
        @self._require_auth
        def refresh_token() -> Any:
            """Refresh auth token (extends expiration)"""
            self._auth_token = self._generate_token()
            return jsonify({"token": self._auth_token})

    def _execute_callback(self, name: str, *args: Any) -> Any:
        """Execute registered callback"""
        logger.debug(
            f"Executing callback '{name}', registered: {name in self._callbacks}, all callbacks: {list(self._callbacks.keys())}"
        )
        if name in self._callbacks:
            try:
                logger.debug(f"Calling callback '{name}' with args: {args}")
                result = self._callbacks[name](*args)
                logger.info(f"Callback '{name}' executed successfully")
                return result
            except Exception as e:  # callback isolation - user-registered code may raise anything
                # Broad catch intentional: callbacks are user-registered and can raise
                # any exception; the server must not crash on a bad callback.
                logger.error(f"Callback error [{name}]: {e}")
        else:
            logger.warning(f"No callback registered for '{name}'")
        return None

    # ==========================================
    # Public API
    # ==========================================

    def register_callback(self, name: str, callback: Callable[..., Any]) -> None:
        """Register a callback for remote commands"""
        self._callbacks[name] = callback
        logger.info(f"Registered callback '{name}', total callbacks: {list(self._callbacks.keys())}")

    def update_now_playing(self, info: NowPlayingInfo) -> None:
        """Update current playback info (thread-safe)"""
        with self._data_lock:
            self._now_playing = info

    def update_queue(self, queue: List[Any]) -> None:
        """Update queue (thread-safe)"""
        with self._data_lock:
            self._queue = list(queue)

    @property
    def auth_token(self) -> str:
        """Get current session auth token"""
        return self._auth_token

    def start(self, port: int = 8080, host: str = "127.0.0.1") -> bool:
        """Start the server"""
        if not HAS_FLASK:
            logger.error("Flask not installed. Install with: pip install flask flask-cors")
            return False

        if self._is_running:
            logger.warning("Server already running")
            return True

        self._port = port
        self._host = host

        def run_server() -> None:
            try:
                self._app.run(host=host, port=port, threaded=True, use_reloader=False)  # type: ignore[union-attr]
            except (OSError, RuntimeError) as e:
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
        """Get server URL (with auth token for QR code)"""
        return f"http://{self.get_local_ip()}:{self._port}?token={self._auth_token}"

    @staticmethod
    def get_local_ip() -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip  # type: ignore[no-any-return]
        except OSError:
            return "127.0.0.1"


# ==========================================
# Mobile Web Interface HTML
# ==========================================

MOBILE_HTML = """
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
        // Auth token injected by server
        const AUTH_TOKEN = '{{ auth_token }}';
        // Remove token from URL to prevent exposure in browser history
        if (window.history && window.history.replaceState) {
            window.history.replaceState({}, document.title, window.location.pathname);
        }
        const AUTH_HEADERS = {
            'Authorization': 'Bearer ' + AUTH_TOKEN,
            'Content-Type': 'application/json'
        };
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
                const res = await fetch('/api/status', { headers: AUTH_HEADERS });
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
            await fetch('/api/toggle', { method: 'POST', headers: AUTH_HEADERS });
            fetchStatus();
        }

        async function next() {
            await fetch('/api/next', { method: 'POST', headers: AUTH_HEADERS });
            fetchStatus();
        }

        async function previous() {
            await fetch('/api/previous', { method: 'POST', headers: AUTH_HEADERS });
            fetchStatus();
        }

        async function setVolume(value) {
            await fetch('/api/volume', {
                method: 'POST',
                headers: AUTH_HEADERS,
                body: JSON.stringify({ volume: parseInt(value) })
            });
        }

        // Poll for updates
        setInterval(fetchStatus, 1000);
        fetchStatus();
    </script>
</body>
</html>
"""
