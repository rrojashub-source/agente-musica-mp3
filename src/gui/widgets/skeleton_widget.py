"""
Skeleton Loading Widget - UX Enhancement

Professional loading animation that shows placeholder content
while data is being loaded. Improves perceived performance.

Features:
- Animated shimmer effect
- Configurable rows and columns
- Automatic theme adaptation
- Smooth transitions

Created: November 23, 2025
"""
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPaintEvent

logger = logging.getLogger(__name__)


class SkeletonLine(QFrame):
    """Single skeleton line with shimmer animation"""

    def __init__(self, width_percent: int = 100, height: int = 16, parent=None):
        """
        Initialize skeleton line

        Args:
            width_percent: Width as percentage of parent (0-100)
            height: Height in pixels
            parent: Parent widget
        """
        super().__init__(parent)
        self._width_percent = width_percent
        self._shimmer_position = 0.0
        self._base_color = QColor(60, 60, 60)
        self._shimmer_color = QColor(80, 80, 80)

        self.setFixedHeight(height)
        self.setMinimumWidth(50)

        # Animation
        self._animation = QPropertyAnimation(self, b"shimmer_position")
        self._animation.setDuration(1500)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation.setLoopCount(-1)  # Infinite loop
        self._animation.start()

    def get_shimmer_position(self) -> float:
        return self._shimmer_position

    def set_shimmer_position(self, value: float):
        self._shimmer_position = value
        self.update()

    shimmer_position = pyqtProperty(float, get_shimmer_position, set_shimmer_position)

    def set_theme(self, is_dark: bool):
        """Update colors based on theme"""
        if is_dark:
            self._base_color = QColor(60, 60, 60)
            self._shimmer_color = QColor(90, 90, 90)
        else:
            self._base_color = QColor(220, 220, 220)
            self._shimmer_color = QColor(240, 240, 240)
        self.update()

    def paintEvent(self, event: QPaintEvent):
        """Custom paint with shimmer effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate actual width
        actual_width = int(self.width() * self._width_percent / 100)

        # Create gradient for shimmer effect
        gradient = QLinearGradient(0, 0, actual_width, 0)

        # Position of shimmer highlight
        shimmer_pos = self._shimmer_position

        # Create gradient stops
        gradient.setColorAt(0.0, self._base_color)
        gradient.setColorAt(max(0.0, shimmer_pos - 0.2), self._base_color)
        gradient.setColorAt(shimmer_pos, self._shimmer_color)
        gradient.setColorAt(min(1.0, shimmer_pos + 0.2), self._base_color)
        gradient.setColorAt(1.0, self._base_color)

        # Draw rounded rectangle
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, actual_width, self.height(), 4, 4)

    def stop_animation(self):
        """Stop the shimmer animation"""
        self._animation.stop()

    def start_animation(self):
        """Start the shimmer animation"""
        self._animation.start()


class SkeletonRow(QWidget):
    """Single skeleton row representing a table row"""

    def __init__(self, columns: list = None, parent=None):
        """
        Initialize skeleton row

        Args:
            columns: List of column width percentages, e.g., [30, 20, 20, 15, 15]
            parent: Parent widget
        """
        super().__init__(parent)
        self._lines = []

        if columns is None:
            columns = [30, 25, 20, 15, 10]  # Default column widths

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(16)

        for width in columns:
            line = SkeletonLine(width_percent=100, height=14)
            self._lines.append(line)
            layout.addWidget(line, stretch=width)

    def set_theme(self, is_dark: bool):
        """Update theme for all lines"""
        for line in self._lines:
            line.set_theme(is_dark)

    def stop_animation(self):
        """Stop all animations"""
        for line in self._lines:
            line.stop_animation()

    def start_animation(self):
        """Start all animations"""
        for line in self._lines:
            line.start_animation()


class SkeletonTableWidget(QWidget):
    """
    Skeleton loading placeholder for tables

    Shows animated placeholder rows while data is loading.
    Replace with actual content once data is ready.
    """

    def __init__(self, rows: int = 10, columns: list = None, parent=None):
        """
        Initialize skeleton table

        Args:
            rows: Number of skeleton rows to show
            columns: List of column width percentages
            parent: Parent widget
        """
        super().__init__(parent)
        self._rows = []
        self._is_dark = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Create skeleton rows
        for _ in range(rows):
            row = SkeletonRow(columns=columns)
            self._rows.append(row)
            layout.addWidget(row)

        # Add stretch at bottom
        layout.addStretch()

        logger.debug(f"SkeletonTableWidget created with {rows} rows")

    def set_theme(self, is_dark: bool):
        """Update theme for all rows"""
        self._is_dark = is_dark
        for row in self._rows:
            row.set_theme(is_dark)

    def stop_animation(self):
        """Stop all animations (call when hiding)"""
        for row in self._rows:
            row.stop_animation()

    def start_animation(self):
        """Start all animations (call when showing)"""
        for row in self._rows:
            row.start_animation()

    def showEvent(self, event):
        """Start animations when shown"""
        super().showEvent(event)
        self.start_animation()

    def hideEvent(self, event):
        """Stop animations when hidden"""
        super().hideEvent(event)
        self.stop_animation()


class SkeletonCard(QWidget):
    """Skeleton placeholder for card-style content"""

    def __init__(self, width: int = 200, height: int = 250, parent=None):
        """
        Initialize skeleton card (e.g., for album grid view)

        Args:
            width: Card width
            height: Card height
            parent: Parent widget
        """
        super().__init__(parent)
        self.setFixedSize(width, height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Album art placeholder (square)
        art_size = min(width - 16, height - 70)
        self._art_skeleton = SkeletonLine(width_percent=100, height=art_size)
        layout.addWidget(self._art_skeleton)

        # Title placeholder
        self._title_skeleton = SkeletonLine(width_percent=80, height=14)
        layout.addWidget(self._title_skeleton)

        # Artist placeholder
        self._artist_skeleton = SkeletonLine(width_percent=60, height=12)
        layout.addWidget(self._artist_skeleton)

        layout.addStretch()

    def set_theme(self, is_dark: bool):
        """Update theme"""
        self._art_skeleton.set_theme(is_dark)
        self._title_skeleton.set_theme(is_dark)
        self._artist_skeleton.set_theme(is_dark)

    def stop_animation(self):
        """Stop animations"""
        self._art_skeleton.stop_animation()
        self._title_skeleton.stop_animation()
        self._artist_skeleton.stop_animation()

    def start_animation(self):
        """Start animations"""
        self._art_skeleton.start_animation()
        self._title_skeleton.start_animation()
        self._artist_skeleton.start_animation()


# Convenience function for creating skeleton loaders
def create_table_skeleton(rows: int = 10, columns: list = None) -> SkeletonTableWidget:
    """
    Create a skeleton table widget

    Args:
        rows: Number of rows
        columns: Column widths as percentages

    Returns:
        SkeletonTableWidget instance

    Example:
        skeleton = create_table_skeleton(15, [30, 25, 20, 15, 10])
        layout.addWidget(skeleton)
        # Later, when data is ready:
        skeleton.hide()
        actual_table.show()
    """
    return SkeletonTableWidget(rows=rows, columns=columns)


def create_card_skeleton(width: int = 200, height: int = 250) -> SkeletonCard:
    """
    Create a skeleton card widget

    Args:
        width: Card width
        height: Card height

    Returns:
        SkeletonCard instance
    """
    return SkeletonCard(width=width, height=height)
