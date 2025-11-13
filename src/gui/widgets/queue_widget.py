"""
Queue Widget - Phase 4.7
PyQt6 widget for displaying and managing download queue

Features:
- Real-time queue display
- Progress bars for each item
- Pause/Resume/Cancel controls
- Clear completed items
- Auto-refresh on queue updates
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QProgressBar, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
import logging
import time

# Setup logger
logger = logging.getLogger(__name__)


class QueueWidget(QWidget):
    """
    Download queue display widget

    Layout:
    +---------------------------------------------------+
    | [Refresh] [Clear Completed]                       |
    +---------------------------------------------------+
    | Title    | Artist | Progress | Status | Actions  |
    |----------|--------|----------|--------|----------|
    | Song 1   | Art 1  | [====  ] | Down.. | ⏸ ❌    |
    | Song 2   | Art 2  | [      ] | Pend.. | ▶ ❌    |
    | Song 3   | Art 3  | [======] | Done   | ✓       |
    +---------------------------------------------------+
    """

    def __init__(self, download_queue=None):
        """
        Initialize queue widget

        Args:
            download_queue (DownloadQueue): Download queue instance
        """
        super().__init__()

        self.download_queue = download_queue

        # Track item widgets for updates
        self._item_rows = {}  # item_id -> row_index

        # Throttle refresh to avoid UI freezing
        self._last_refresh_time = 0
        self._min_refresh_interval = 0.1  # 100ms minimum between refreshes

        # Pending refresh flag (for throttled refreshes)
        self._pending_refresh = False
        self._refresh_timer = QTimer()
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._do_pending_refresh)

        # Setup UI
        self._setup_ui()

        # Connect queue signals if available
        if self.download_queue:
            self._connect_queue_signals()

        logger.info("QueueWidget initialized")

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()

        # Control buttons
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Refresh queue display")
        self.refresh_button.clicked.connect(self.refresh_display)

        self.clear_completed_button = QPushButton("Clear Completed")
        self.clear_completed_button.setToolTip("Remove completed downloads from queue")
        self.clear_completed_button.clicked.connect(self._on_clear_completed_clicked)

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.clear_completed_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Queue table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Title', 'Artist', 'Progress', 'Status', 'Actions'])

        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Artist
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Progress
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Status
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Actions

        self.table.setColumnWidth(1, 150)  # Artist
        self.table.setColumnWidth(2, 150)  # Progress
        self.table.setColumnWidth(3, 100)  # Status
        self.table.setColumnWidth(4, 100)  # Actions

        layout.addWidget(self.table)

        self.setLayout(layout)

    def _connect_queue_signals(self):
        """Connect download queue signals to update handlers"""
        if not self.download_queue:
            return

        # Connect queue signals (if they exist)
        if hasattr(self.download_queue, 'item_progress'):
            self.download_queue.item_progress.connect(self._on_item_progress)

        if hasattr(self.download_queue, 'item_completed'):
            self.download_queue.item_completed.connect(self._on_item_completed)

        if hasattr(self.download_queue, 'item_failed'):
            self.download_queue.item_failed.connect(self._on_item_failed)

    def refresh_display(self):
        """Refresh queue display with current items (throttled)"""
        if not self.download_queue:
            logger.warning("No download queue available")
            return

        # Throttle refreshes to avoid UI freezing
        current_time = time.time()
        time_since_last = current_time - self._last_refresh_time

        if time_since_last < self._min_refresh_interval:
            # Too soon, schedule pending refresh
            if not self._pending_refresh:
                self._pending_refresh = True
                delay_ms = int((self._min_refresh_interval - time_since_last) * 1000)
                self._refresh_timer.start(delay_ms)
            return

        # Perform actual refresh
        self._do_refresh()

    def _do_pending_refresh(self):
        """Execute pending refresh"""
        self._pending_refresh = False
        self._do_refresh()

    def _do_refresh(self):
        """Actual refresh implementation"""
        # Get all items from queue
        items = self.download_queue.get_all_items()

        # Clear current table
        self.table.setRowCount(0)
        self._item_rows.clear()

        # Add each item
        for row_index, (item_id, item) in enumerate(items.items()):
            self._add_item_to_table(row_index, item_id, item)

        self._last_refresh_time = time.time()
        logger.debug(f"Queue display refreshed: {len(items)} items")

    def _add_item_to_table(self, row_index: int, item_id: str, item: dict):
        """
        Add item to table

        Args:
            row_index (int): Row index
            item_id (str): Item ID
            item (dict): Item data
        """
        self.table.insertRow(row_index)
        self._item_rows[item_id] = row_index

        # Title
        metadata = item.get('metadata', {})
        title = metadata.get('title', 'Unknown')
        self.table.setItem(row_index, 0, QTableWidgetItem(title))

        # Artist
        artist = metadata.get('artist', 'Unknown')
        self.table.setItem(row_index, 1, QTableWidgetItem(artist))

        # Progress bar
        progress = item.get('progress', 0)
        progress_bar = self._create_progress_bar(progress)
        self.table.setCellWidget(row_index, 2, progress_bar)

        # Status
        status = item.get('status', 'unknown')
        self.table.setItem(row_index, 3, QTableWidgetItem(status.capitalize()))

        # Action buttons
        action_widget = self._create_action_buttons(item_id, status)
        self.table.setCellWidget(row_index, 4, action_widget)

    def _create_progress_bar(self, progress: int) -> QProgressBar:
        """
        Create progress bar widget

        Args:
            progress (int): Progress percentage (0-100)

        Returns:
            QProgressBar: Progress bar widget
        """
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(progress)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{progress}%")
        return progress_bar

    def _create_action_buttons(self, item_id: str, status: str) -> QWidget:
        """
        Create action buttons for item

        Args:
            item_id (str): Item ID
            status (str): Current status

        Returns:
            QWidget: Widget with action buttons
        """
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)

        # Pause button (only for downloading items)
        if status == 'downloading':
            pause_btn = QPushButton("⏸")
            pause_btn.setMaximumWidth(30)
            pause_btn.setToolTip("Pause download")
            pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pause_btn.clicked.connect(lambda: self._on_pause_clicked(item_id))
            layout.addWidget(pause_btn)

        # Resume button (only for paused items)
        elif status == 'paused':
            resume_btn = QPushButton("▶")
            resume_btn.setMaximumWidth(30)
            resume_btn.setToolTip("Resume download")
            resume_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            resume_btn.clicked.connect(lambda: self._on_resume_clicked(item_id))
            layout.addWidget(resume_btn)

        # Cancel button (for pending/downloading/paused)
        if status in ['pending', 'downloading', 'paused']:
            cancel_btn = QPushButton("❌")
            cancel_btn.setMaximumWidth(30)
            cancel_btn.setToolTip("Cancel download")
            cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel_btn.clicked.connect(lambda: self._on_cancel_clicked(item_id))
            layout.addWidget(cancel_btn)

        # Completed indicator
        if status == 'completed':
            completed_label = QPushButton("✓")
            completed_label.setEnabled(False)
            completed_label.setMaximumWidth(30)
            layout.addWidget(completed_label)

        # Failed indicator
        if status == 'failed':
            failed_label = QPushButton("✗")
            failed_label.setEnabled(False)
            failed_label.setMaximumWidth(30)
            layout.addWidget(failed_label)

        widget.setLayout(layout)
        return widget

    def _on_pause_clicked(self, item_id: str):
        """
        Handle pause button click

        Args:
            item_id (str): Item ID
        """
        if self.download_queue:
            self.download_queue.pause(item_id)
            logger.info(f"Paused item: {item_id}")
            self.refresh_display()

    def _on_resume_clicked(self, item_id: str):
        """
        Handle resume button click

        Args:
            item_id (str): Item ID
        """
        if self.download_queue:
            self.download_queue.resume(item_id)
            logger.info(f"Resumed item: {item_id}")
            self.refresh_display()

    def _on_cancel_clicked(self, item_id: str):
        """
        Handle cancel button click

        Args:
            item_id (str): Item ID
        """
        if self.download_queue:
            self.download_queue.cancel(item_id)
            logger.info(f"Cancelled item: {item_id}")
            self.refresh_display()

    def _on_clear_completed_clicked(self):
        """Handle clear completed button click"""
        if not self.download_queue:
            return

        # Clear completed items from queue
        if hasattr(self.download_queue, 'clear_completed'):
            self.download_queue.clear_completed()
        else:
            # Fallback: manually remove completed items
            items = self.download_queue.get_all_items()
            for item_id, item in list(items.items()):
                if item['status'] == 'completed':
                    self.download_queue.cancel(item_id)

        logger.info("Cleared completed items")
        self.refresh_display()

    @pyqtSlot(str, int)
    def _on_item_progress(self, item_id: str, progress: int):
        """
        Handle item progress update signal

        Args:
            item_id (str): Item ID
            progress (int): Progress percentage (0-100)
        """
        if item_id not in self._item_rows:
            return

        row_index = self._item_rows[item_id]

        # Update progress bar
        progress_bar = self.table.cellWidget(row_index, 2)
        if progress_bar and isinstance(progress_bar, QProgressBar):
            progress_bar.setValue(progress)
            progress_bar.setFormat(f"{progress}%")

    @pyqtSlot(str, dict)
    def _on_item_completed(self, item_id: str, metadata: dict):
        """
        Handle item completed signal

        Args:
            item_id (str): Item ID
            metadata (dict): Completed item metadata
        """
        logger.info(f"Item completed: {item_id}")
        self.refresh_display()

    @pyqtSlot(str, str)
    def _on_item_failed(self, item_id: str, error: str):
        """
        Handle item failed signal

        Args:
            item_id (str): Item ID
            error (str): Error message
        """
        logger.error(f"Item failed: {item_id} - {error}")
        self.refresh_display()
