"""
Audio Visualizer Widget - Phase 7.3

Waveform visualization widget for audio playback.

Features:
- Pre-computed waveform display
- Position indicator during playback
- Customizable colors and styles
- Scales to widget size
- Smooth performance (60 FPS capable)

Created: November 13, 2025
"""
import logging
from typing import List, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath

logger = logging.getLogger(__name__)


class VisualizerWidget(QWidget):
    """
    Audio waveform visualizer widget

    Displays pre-computed waveform with position indicator.

    Styles:
    - 'waveform': Continuous waveform line
    - 'bars': Vertical bars (spectrum-like)

    Usage:
        visualizer = VisualizerWidget()
        visualizer.set_waveform(waveform_data)  # List of amplitude values [-1.0, 1.0]
        visualizer.set_position(0.5)  # 50% through song
        visualizer.set_color(QColor(0, 255, 0))  # Green waveform
        visualizer.set_style('bars')  # Bar style
    """

    def __init__(self, parent=None):
        """
        Initialize Visualizer Widget

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        # Waveform data
        self.waveform_data: Optional[List[float]] = None
        self.position: float = 0.0  # Current position (0.0 to 1.0)
        self.duration: float = 0.0  # Total duration in seconds (for position conversion)

        # Visual settings
        self.waveform_color: QColor = QColor(0, 150, 255)  # Blue default
        self.position_color: QColor = QColor(255, 0, 0)  # Red position indicator
        self.background_color: QColor = QColor(30, 30, 30)  # Dark background
        self.viz_style: str = 'waveform'  # 'waveform' or 'bars'

        # Widget settings
        self.setMinimumSize(200, 100)
        # Let theme handle background color

        logger.info("VisualizerWidget initialized")

    def set_waveform(self, waveform_data: List[float]):
        """
        Set waveform data for visualization

        Args:
            waveform_data: List of amplitude values (typically -1.0 to 1.0)
        """
        self.waveform_data = waveform_data
        self.update()  # Trigger repaint
        logger.debug(f"Waveform data set: {len(waveform_data)} samples")

    def set_position(self, position: float):
        """
        Set current playback position

        Args:
            position: Position in SECONDS (will be converted to fraction)
        """
        # Convert seconds to fraction (0.0 to 1.0)
        if self.duration > 0:
            fraction = position / self.duration
            self.position = max(0.0, min(1.0, fraction))  # Clamp to [0, 1]
        else:
            self.position = 0.0

        self.update()  # Trigger repaint

    def set_duration(self, duration: float):
        """
        Set total song duration (for position conversion)

        Args:
            duration: Total duration in seconds
        """
        self.duration = duration
        logger.debug(f"Duration set: {duration:.2f}s")

    def set_color(self, color: QColor):
        """
        Set waveform color

        Args:
            color: QColor for waveform
        """
        self.waveform_color = color
        self.update()  # Trigger repaint

    def set_style(self, style: str):
        """
        Set visualization style

        Args:
            style: 'waveform' or 'bars'
        """
        if style in ['waveform', 'bars']:
            self.viz_style = style
            self.update()  # Trigger repaint
            logger.debug(f"Visualization style set to: {style}")
        else:
            logger.warning(f"Invalid visualization style: {style}")

    def paintEvent(self, event):
        """
        Custom paint event for waveform visualization

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), self.background_color)

        # If no waveform data, display placeholder
        if not self.waveform_data:
            self._draw_placeholder(painter)
            return

        # Draw waveform based on style
        if self.viz_style == 'waveform':
            self._draw_waveform(painter)
        elif self.viz_style == 'bars':
            self._draw_bars(painter)

        # Draw position indicator
        self._draw_position_indicator(painter)

    def _draw_placeholder(self, painter: QPainter):
        """
        Draw placeholder when no waveform loaded

        Args:
            painter: QPainter instance
        """
        painter.setPen(QColor(100, 100, 100))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No audio loaded")

    def _draw_waveform(self, painter: QPainter):
        """
        Draw waveform as continuous line

        Args:
            painter: QPainter instance
        """
        width = self.width()
        height = self.height()
        center_y = height // 2

        # Sample waveform data to fit widget width
        num_samples = len(self.waveform_data)
        samples_per_pixel = max(1, num_samples // width)

        # Create path for waveform
        path = QPainterPath()
        path.moveTo(0, center_y)

        for x in range(width):
            # Get average amplitude for this pixel
            start_idx = x * samples_per_pixel
            end_idx = min(start_idx + samples_per_pixel, num_samples)

            if start_idx >= num_samples:
                break

            # Average samples in this range
            samples = self.waveform_data[start_idx:end_idx]
            avg_amplitude = sum(samples) / len(samples) if samples else 0.0

            # Convert amplitude to y coordinate
            # Amplitude range: [-1.0, 1.0] -> y range: [0, height]
            y = center_y - int(avg_amplitude * (height / 2) * 0.9)  # 0.9 for padding

            path.lineTo(x, y)

        # Draw waveform path
        pen = QPen(self.waveform_color, 2)
        painter.setPen(pen)
        painter.drawPath(path)

    def _draw_bars(self, painter: QPainter):
        """
        Draw waveform as vertical bars

        Args:
            painter: QPainter instance
        """
        width = self.width()
        height = self.height()
        center_y = height // 2

        # Number of bars to draw
        num_bars = min(100, width // 4)  # Max 100 bars, min 4 pixels wide
        bar_width = width // num_bars

        # Sample waveform data
        num_samples = len(self.waveform_data)
        samples_per_bar = max(1, num_samples // num_bars)

        for i in range(num_bars):
            x = i * bar_width

            # Get max amplitude for this bar
            start_idx = i * samples_per_bar
            end_idx = min(start_idx + samples_per_bar, num_samples)

            if start_idx >= num_samples:
                break

            # Max absolute amplitude in this range
            samples = self.waveform_data[start_idx:end_idx]
            max_amplitude = max(abs(s) for s in samples) if samples else 0.0

            # Convert amplitude to bar height
            bar_height = int(max_amplitude * (height / 2) * 0.9)  # 0.9 for padding

            # Draw bar centered at center_y
            rect = QRect(x, center_y - bar_height, bar_width - 2, bar_height * 2)
            painter.fillRect(rect, self.waveform_color)

    def _draw_position_indicator(self, painter: QPainter):
        """
        Draw position indicator line

        Args:
            painter: QPainter instance
        """
        width = self.width()
        height = self.height()

        # Calculate x position
        x = int(self.position * width)

        # Draw vertical line
        pen = QPen(self.position_color, 2)
        painter.setPen(pen)
        painter.drawLine(x, 0, x, height)

    def clear(self):
        """Clear waveform data"""
        self.waveform_data = None
        self.position = 0.0
        self.update()
        logger.debug("Waveform cleared")

    def reset(self):
        """Reset to initial state"""
        self.clear()
        self.viz_style = 'waveform'
        self.waveform_color = QColor(0, 150, 255)
        self.update()
        logger.debug("Visualizer reset")
