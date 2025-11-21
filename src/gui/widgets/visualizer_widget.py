"""
Audio Visualizer Widget - Phase 7.3

Waveform visualization widget for audio playback.

Features:
- Pre-computed waveform display
- Position indicator during playback
- Customizable colors and styles
- Scales to widget size
- Smooth performance (60 FPS capable)
- Modern spectrum analyzer with gradient colors

Created: November 13, 2025
Updated: November 20, 2025 - Modern gradient bars
"""
import logging
from typing import List, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QLinearGradient

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

        # Waveform data (static)
        self.waveform_data: Optional[List[float]] = None

        # Spectrum data (dynamic - for animated bars)
        self.spectrum_data: Optional[List[List[float]]] = None  # [time_window][frequency_bar]
        self.spectrum_duration: float = 0.0  # Duration for spectrum data

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

    def set_spectrum(self, spectrum_data: List[List[float]], duration: float):
        """
        Set spectrum data for dynamic visualization

        Args:
            spectrum_data: List of time windows, each containing bar magnitudes
                          Format: [[bar1, bar2, ...], [bar1, bar2, ...], ...]
            duration: Total duration in seconds
        """
        self.spectrum_data = spectrum_data
        self.spectrum_duration = duration
        self.update()  # Trigger repaint
        logger.debug(f"Spectrum data set: {len(spectrum_data)} windows, {duration:.2f}s")

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

        # If no data at all, display placeholder
        if not self.waveform_data and not self.spectrum_data:
            self._draw_placeholder(painter)
            return

        # Draw visualization based on style
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
        # Check if waveform data exists
        if not self.waveform_data:
            return

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
        Draw dynamic spectrum analyzer bars with gradient

        Modern design:
        - Vertical bars from bottom upwards
        - Gradient colors: green (low) → cyan (mid) → blue (high) → purple (very high)
        - Spacing between bars for clean look
        - DYNAMIC: Bars move with music rhythm using FFT data

        Args:
            painter: QPainter instance
        """
        width = self.width()
        height = self.height()

        # Number of bars to draw (fewer bars = cleaner look)
        num_bars = min(60, width // 8)  # Max 60 bars, min 8 pixels wide
        bar_width = width // num_bars
        bar_spacing = 2  # 2px gap between bars

        # Get bar magnitudes based on current playback position
        bar_magnitudes = self._get_current_bar_magnitudes(num_bars)

        for i in range(num_bars):
            x = i * bar_width

            # Get magnitude for this bar (from FFT data if available, else waveform)
            max_amplitude = bar_magnitudes[i]

            # Convert amplitude to bar height
            # Full height usage (no mirroring)
            bar_height = int(max_amplitude * height * 0.95)  # 0.95 for small top padding

            # Minimum bar height for visibility
            bar_height = max(bar_height, 3)

            # Calculate bar rectangle (from bottom upwards)
            bar_rect = QRect(
                x + bar_spacing // 2,  # Left edge with spacing
                height - bar_height,    # Top edge (grows upwards)
                bar_width - bar_spacing,  # Width minus spacing
                bar_height              # Height
            )

            # Create gradient based on bar height (intensity)
            gradient = QLinearGradient(0, height, 0, 0)  # Bottom to top

            # Color scheme: green → cyan → blue → purple
            # Calculate color based on amplitude intensity
            intensity = max_amplitude  # 0.0 to 1.0

            if intensity < 0.25:
                # Low amplitude: Green
                gradient.setColorAt(0.0, QColor(34, 197, 94))   # Green-500
                gradient.setColorAt(1.0, QColor(74, 222, 128))  # Green-400 (lighter)
            elif intensity < 0.50:
                # Medium-low: Green → Cyan
                gradient.setColorAt(0.0, QColor(34, 197, 94))   # Green-500
                gradient.setColorAt(0.5, QColor(20, 184, 166))  # Teal-500
                gradient.setColorAt(1.0, QColor(45, 212, 191))  # Teal-400
            elif intensity < 0.75:
                # Medium-high: Cyan → Blue
                gradient.setColorAt(0.0, QColor(20, 184, 166))  # Teal-500
                gradient.setColorAt(0.5, QColor(59, 130, 246))  # Blue-500
                gradient.setColorAt(1.0, QColor(96, 165, 250))  # Blue-400
            else:
                # High amplitude: Blue → Purple
                gradient.setColorAt(0.0, QColor(59, 130, 246))   # Blue-500
                gradient.setColorAt(0.5, QColor(139, 92, 246))   # Violet-500
                gradient.setColorAt(1.0, QColor(167, 139, 250))  # Violet-400

            # Apply gradient and draw bar
            painter.fillRect(bar_rect, gradient)

            # Optional: Add subtle glow effect for high amplitudes
            if intensity > 0.7:
                glow_color = QColor(167, 139, 250, 30)  # Purple with transparency
                glow_rect = QRect(
                    bar_rect.x() - 1,
                    bar_rect.y() - 1,
                    bar_rect.width() + 2,
                    bar_rect.height() + 2
                )
                painter.fillRect(glow_rect, glow_color)

    def _get_current_bar_magnitudes(self, num_bars: int) -> List[float]:
        """
        Get bar magnitudes for current playback position

        If spectrum data is available (FFT), use dynamic values.
        Otherwise, fall back to static waveform data.

        Args:
            num_bars: Number of bars to generate

        Returns:
            List of magnitudes [0.0, 1.0] for each bar
        """
        # If we have dynamic spectrum data, use it!
        if self.spectrum_data and self.spectrum_duration > 0:
            # Calculate which time window we're in
            current_time = self.position  # In seconds
            time_index = int((current_time / self.spectrum_duration) * len(self.spectrum_data))
            time_index = max(0, min(time_index, len(self.spectrum_data) - 1))

            # Get bar magnitudes for this time window
            current_spectrum = self.spectrum_data[time_index]

            # Match number of bars (resample if needed)
            if len(current_spectrum) == num_bars:
                return current_spectrum
            else:
                # Resample to match num_bars
                import numpy as np
                resampled = np.interp(
                    np.linspace(0, len(current_spectrum) - 1, num_bars),
                    np.arange(len(current_spectrum)),
                    current_spectrum
                )
                return resampled.tolist()

        # Fallback: Use static waveform data
        elif self.waveform_data:
            num_samples = len(self.waveform_data)
            samples_per_bar = max(1, num_samples // num_bars)

            bar_magnitudes = []
            for i in range(num_bars):
                start_idx = i * samples_per_bar
                end_idx = min(start_idx + samples_per_bar, num_samples)

                if start_idx >= num_samples:
                    bar_magnitudes.append(0.0)
                    continue

                # Max absolute amplitude in this range
                samples = self.waveform_data[start_idx:end_idx]
                max_amplitude = max(abs(s) for s in samples) if samples else 0.0
                bar_magnitudes.append(max_amplitude)

            return bar_magnitudes

        # No data available
        else:
            return [0.0] * num_bars

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
        """Clear all visualization data"""
        self.waveform_data = None
        self.spectrum_data = None
        self.spectrum_duration = 0.0
        self.position = 0.0
        self.update()
        logger.debug("Visualizer cleared")

    def reset(self):
        """Reset to initial state"""
        self.clear()
        self.viz_style = 'waveform'
        self.waveform_color = QColor(0, 150, 255)
        self.update()
        logger.debug("Visualizer reset")
