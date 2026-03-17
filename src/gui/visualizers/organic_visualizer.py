"""
Organic Visualizer Widget - SDF Ray Marching Audio Visualizer

Phase 10 Feature: Fluid organic visualization that "dances" with music.
Ported from NEXUS Avatar desktop pet shader technology.

Features:
- SDF (Signed Distance Functions) for smooth shapes
- Ray Marching for 3D rendering without polygons
- Smooth-min blending for organic transitions
- Simplex noise for natural deformation
- Audio-reactive: bass -> nucleus, mids -> extensions, highs -> sparkles
- Beat detection triggers fluid <-> crystal metamorphosis

Technical:
- Uses QOpenGLWidget for native GLSL shader support
- Renders at 60 FPS with minimal CPU usage
- All rendering done on GPU via fragment shader

Created: December 17, 2025
Origin: NEXUS Avatar project (nexus-avatar/src/shaders/nexusCore.ts)
"""

# mypy: disable-error-code="name-defined, misc"

from __future__ import annotations

import ctypes
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from gui.themes.style_constants import Styles
from utils.constants import ANIMATION_FRAME_INTERVAL_MS
from utils.resource_path import get_resource_path

# Try to import OpenGL - graceful fallback if not available
try:
    from OpenGL.GL import *  # noqa: F403
    from OpenGL.GL import shaders
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    QOpenGLWidget = QWidget  # Fallback

logger = logging.getLogger(__name__)


class OrganicVisualizerWidget(QOpenGLWidget if OPENGL_AVAILABLE else QWidget):
    """
    SDF Ray Marching Visualizer driven by audio FFT data.

    This visualizer creates organic, fluid shapes that react to music:
    - Bass frequencies pulse the central nucleus
    - Mid frequencies move the extensions
    - High frequencies create sparkle particles
    - Beat detection triggers metamorphosis (fluid <-> crystal)

    Usage:
        visualizer = OrganicVisualizerWidget()
        visualizer.update_audio(bass=0.8, mids=0.5, highs=0.3, amplitude=0.6)

        # Or from FFT data:
        visualizer.update_from_fft(fft_bins)
    """

    # Brain AI color palette (matches other visualizers)
    DEFAULT_BASE_COLOR: Tuple[float, float, float] = (0.0, 0.78, 1.0)  # Cyan (0, 200, 255)
    DEFAULT_ACCENT_COLOR: Tuple[float, float, float] = (0.39, 0.0, 1.0)  # Purple (100, 0, 255)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the Organic Visualizer Widget."""
        if not OPENGL_AVAILABLE:
            super().__init__(parent)
            self._init_fallback_ui()
            return

        # Set OpenGL format for better quality
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setSamples(4)  # Anti-aliasing
        QSurfaceFormat.setDefaultFormat(fmt)

        super().__init__(parent)

        # Shader program
        self.shader_program: Optional[int] = None
        self.vao: Optional[int] = None
        self.vbo: Optional[int] = None

        # Audio uniforms (0.0 to 1.0)
        self.bass: float = 0.0
        self.mids: float = 0.0
        self.highs: float = 0.0
        self.amplitude: float = 0.0
        self.beat: float = 0.0  # 0 = fluid, 1 = crystal

        # Smoothing targets (for responsive but smooth animation)
        self._target_bass: float = 0.0
        self._target_mids: float = 0.0
        self._target_highs: float = 0.0
        self._target_amplitude: float = 0.0

        # Time tracking
        self.start_time: float = time.time()

        # Colors
        self.base_color: Tuple[float, float, float] = self.DEFAULT_BASE_COLOR
        self.accent_color: Tuple[float, float, float] = self.DEFAULT_ACCENT_COLOR

        # Beat detection state
        self._last_amplitude: float = 0.0
        self._beat_decay: float = 0.0

        # Animation timer (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start(ANIMATION_FRAME_INTERVAL_MS)  # ~60 FPS

        # Widget settings
        self.setMinimumSize(200, 200)

        logger.info("OrganicVisualizerWidget initialized (OpenGL)")

    def _init_fallback_ui(self) -> None:
        """Initialize fallback UI when OpenGL is not available."""
        # Initialize audio state (needed even in fallback mode)
        self.bass = 0.0
        self.mids = 0.0
        self.highs = 0.0
        self.amplitude = 0.0
        self.beat = 0.0
        self._last_amplitude = 0.0
        self._beat_decay = 0.0
        self._target_bass = 0.0
        self._target_mids = 0.0
        self._target_highs = 0.0
        self._target_amplitude = 0.0

        layout = QVBoxLayout(self)
        label = QLabel("OpenGL not available\nInstall PyOpenGL for organic visualizer")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.FALLBACK_LABEL)
        layout.addWidget(label)
        logger.warning("OrganicVisualizerWidget: OpenGL not available, using fallback")

    def initializeGL(self) -> None:
        """Initialize OpenGL resources."""
        if not OPENGL_AVAILABLE:
            return

        try:
            # Load shaders
            shader_dir = get_resource_path("gui/visualizers/organic_shaders")
            vertex_path = shader_dir / "vertex.glsl"
            fragment_path = shader_dir / "fragment_music.glsl"

            with open(vertex_path, "r") as f:
                vertex_src = f.read()
            with open(fragment_path, "r") as f:
                fragment_src = f.read()

            # Compile shaders
            vertex_shader = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)

            # Create fullscreen quad VAO/VBO
            self._setup_quad()

            # Set clear color (dark background)
            glClearColor(0.02, 0.02, 0.05, 1.0)

            logger.info("OpenGL initialized successfully")

        except Exception as e:  # OpenGL init can fail with diverse driver/GPU errors
            logger.error(f"Failed to initialize OpenGL: {e}")
            self.shader_program = None

    def _setup_quad(self) -> None:
        """Setup fullscreen quad geometry."""
        # Fullscreen quad vertices (position + texcoord)
        # Format: x, y, u, v
        vertices = np.array(
            [
                -1.0,
                -1.0,
                0.0,
                0.0,  # Bottom-left
                1.0,
                -1.0,
                1.0,
                0.0,  # Bottom-right
                1.0,
                1.0,
                1.0,
                1.0,  # Top-right
                -1.0,
                -1.0,
                0.0,
                0.0,  # Bottom-left
                1.0,
                1.0,
                1.0,
                1.0,  # Top-right
                -1.0,
                1.0,
                0.0,
                1.0,  # Top-left
            ],
            dtype=np.float32,
        )

        # Create VAO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Create VBO
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Setup vertex attributes
        stride = 4 * 4  # 4 floats * 4 bytes

        # Position attribute (location 0)
        pos_loc = glGetAttribLocation(self.shader_program, "position")
        if pos_loc >= 0:
            glEnableVertexAttribArray(pos_loc)
            glVertexAttribPointer(pos_loc, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        # TexCoord attribute (location 1)
        tex_loc = glGetAttribLocation(self.shader_program, "texCoord")
        if tex_loc >= 0:
            glEnableVertexAttribArray(tex_loc)
            glVertexAttribPointer(tex_loc, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))

        glBindVertexArray(0)

        # Cache uniform locations to avoid per-frame lookups
        self._uniform_locs: Dict[str, int] = {}
        for name in [
            "u_time",
            "u_resolution",
            "u_bass",
            "u_mids",
            "u_highs",
            "u_amplitude",
            "u_beat",
            "u_baseColor",
            "u_accentColor",
        ]:
            self._uniform_locs[name] = glGetUniformLocation(self.shader_program, name)

    def resizeGL(self, width: int, height: int) -> None:
        """Handle widget resize."""
        if not OPENGL_AVAILABLE:
            return
        glViewport(0, 0, width, height)

    def paintGL(self) -> None:
        """Render the visualizer."""
        if not OPENGL_AVAILABLE or not self.shader_program:
            return

        glClear(GL_COLOR_BUFFER_BIT)

        glUseProgram(self.shader_program)

        # Set uniforms using cached locations
        current_time = time.time() - self.start_time
        locs = self._uniform_locs

        loc = locs.get("u_time", -1)
        if loc >= 0:
            glUniform1f(loc, current_time)

        loc = locs.get("u_resolution", -1)
        if loc >= 0:
            glUniform2f(loc, float(self.width()), float(self.height()))

        loc = locs.get("u_bass", -1)
        if loc >= 0:
            glUniform1f(loc, self.bass)

        loc = locs.get("u_mids", -1)
        if loc >= 0:
            glUniform1f(loc, self.mids)

        loc = locs.get("u_highs", -1)
        if loc >= 0:
            glUniform1f(loc, self.highs)

        loc = locs.get("u_amplitude", -1)
        if loc >= 0:
            glUniform1f(loc, self.amplitude)

        loc = locs.get("u_beat", -1)
        if loc >= 0:
            glUniform1f(loc, self.beat)

        loc = locs.get("u_baseColor", -1)
        if loc >= 0:
            glUniform3f(loc, *self.base_color)

        loc = locs.get("u_accentColor", -1)
        if loc >= 0:
            glUniform3f(loc, *self.accent_color)

        # Draw fullscreen quad
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        glUseProgram(0)

    def _on_timer(self) -> None:
        """Timer callback for animation."""
        # FAST smoothing toward targets (responsive but not jerky)
        # Attack: 0.5 = very fast response to increases
        # Decay: 0.15 = slower fall for smooth trails
        attack = 0.5
        decay = 0.15

        # Smooth bass
        if self._target_bass > self.bass:
            self.bass += (self._target_bass - self.bass) * attack
        else:
            self.bass += (self._target_bass - self.bass) * decay

        # Smooth mids
        if self._target_mids > self.mids:
            self.mids += (self._target_mids - self.mids) * attack
        else:
            self.mids += (self._target_mids - self.mids) * decay

        # Smooth highs
        if self._target_highs > self.highs:
            self.highs += (self._target_highs - self.highs) * attack
        else:
            self.highs += (self._target_highs - self.highs) * decay

        # Smooth amplitude
        if self._target_amplitude > self.amplitude:
            self.amplitude += (self._target_amplitude - self.amplitude) * attack
        else:
            self.amplitude += (self._target_amplitude - self.amplitude) * decay

        # Decay beat detection smoothly
        if self._beat_decay > 0:
            self._beat_decay -= 0.04
            self.beat = max(0.0, self._beat_decay)

        self.update()  # Trigger repaint

    def update_audio(self, bass: float = 0.0, mids: float = 0.0, highs: float = 0.0, amplitude: float = 0.0) -> None:
        """
        Update audio parameters (sets targets for smooth animation).

        Args:
            bass: Low frequency intensity (0.0 - 1.0)
            mids: Mid frequency intensity (0.0 - 1.0)
            highs: High frequency intensity (0.0 - 1.0)
            amplitude: Overall volume (0.0 - 1.0)
        """
        # Update targets (actual values smoothed in _on_timer)
        self._target_bass = max(0.0, min(1.0, bass))
        self._target_mids = max(0.0, min(1.0, mids))
        self._target_highs = max(0.0, min(1.0, highs))
        self._target_amplitude = max(0.0, min(1.0, amplitude))

        # Beat detection: instant response (no smoothing for beats!)
        # With normalized data: typical amplitude 0.3-0.6, beats cause 0.05-0.15 jumps
        amp_jump = amplitude - self._last_amplitude
        if amp_jump > 0.08 and amplitude > 0.4:  # Strong beat
            self._beat_decay = 1.0
            self.beat = 1.0
        elif amp_jump > 0.04 and amplitude > 0.25:  # Medium beat
            self._beat_decay = max(self._beat_decay, 0.7)
            self.beat = max(self.beat, 0.7)
        elif amp_jump > 0.02 and amplitude > 0.15:  # Soft beat
            self._beat_decay = max(self._beat_decay, 0.4)
            self.beat = max(self.beat, 0.4)
        self._last_amplitude = amplitude

    def update_from_fft(self, fft_data: List[float], num_bins: int = 512) -> None:
        """
        Update audio parameters from FFT data.

        Expects pre-normalized data (0.0-1.0) from WaveformExtractor which
        converts to dB scale and normalizes. Maps logarithmic bars to:
        - Bass: first 8% of bars (~20-300 Hz) — punchy low end
        - Mids: 8-30% (~300-3000 Hz) — body of music
        - Highs: 30-100% (~3000+ Hz) — cymbals, brightness

        Args:
            fft_data: List of FFT magnitude values (0.0-1.0 normalized)
            num_bins: Total number of FFT bins (default: 512)
        """
        if not fft_data:
            return

        n = len(fft_data)
        bass_end = max(3, int(n * 0.08))  # 8% for bass
        mids_end = int(n * 0.30)  # 30% for mids
        # Rest is highs

        # Calculate averages for each range
        bass = self._average_bins(fft_data, 0, bass_end)
        mids = self._average_bins(fft_data, bass_end, mids_end)
        highs = self._average_bins(fft_data, mids_end, n)
        amplitude = sum(fft_data) / n

        # Data is already normalized 0.0-1.0 from WaveformExtractor (dB scale).
        # Apply power curve (x^0.7) to expand quiet values + mild boost.
        # This gives visual dynamic range: quiet ~0.2, normal ~0.5, loud ~0.9
        bass = min(1.0, bass**0.7 * 1.2)
        mids = min(1.0, mids**0.7 * 1.5)
        highs = min(1.0, highs**0.6 * 2.5)
        amplitude = min(1.0, amplitude**0.7 * 1.8)

        self.update_audio(bass, mids, highs, amplitude)

    def _average_bins(self, data: List[float], start: int, end: int) -> float:
        """Calculate average of bins in range."""
        if start >= end or start >= len(data):
            return 0.0
        end = min(end, len(data))
        bins = data[start:end]
        return sum(bins) / len(bins) if bins else 0.0

    def set_colors(self, base_color: Tuple[float, float, float], accent_color: Tuple[float, float, float]) -> None:
        """
        Set visualizer colors.

        Args:
            base_color: RGB tuple (0.0-1.0) for primary color
            accent_color: RGB tuple (0.0-1.0) for secondary color
        """
        self.base_color = base_color
        self.accent_color = accent_color

    def set_style(self, style: str) -> None:
        """
        Set visual style preset.

        Args:
            style: 'nexus', 'aria', 'echo', or 'music'
        """
        styles = {
            "nexus": ((0.0, 0.78, 1.0), (1.0, 0.0, 0.78)),  # Cyan/Magenta
            "aria": ((1.0, 0.4, 0.6), (1.0, 0.8, 0.4)),  # Pink/Gold
            "echo": ((0.7, 0.7, 0.8), (0.4, 0.6, 1.0)),  # Silver/Blue
            "music": ((0.2, 0.8, 0.4), (0.8, 0.2, 1.0)),  # Green/Purple
        }

        if style in styles:
            self.base_color, self.accent_color = styles[style]
            logger.info(f"Organic visualizer style set to: {style}")

    def cleanup(self) -> None:
        """Cleanup OpenGL resources."""
        if not OPENGL_AVAILABLE:
            return

        if self.timer:
            self.timer.stop()

        self.makeCurrent()
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo:
            glDeleteBuffers(1, [self.vbo])
        if self.shader_program:
            glDeleteProgram(self.shader_program)
        self.doneCurrent()

    def closeEvent(self, event: Any) -> None:
        """Handle widget close."""
        self.cleanup()
        super().closeEvent(event)
