"""
Keyboard Shortcuts Help Dialog

Displays a table of all available keyboard shortcuts for NEXUS Music Manager.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ShortcutsDialog(QDialog):
    """Display keyboard shortcuts help dialog"""

    def __init__(self, shortcuts_list: List[Tuple[str, str]], parent: Optional[QWidget] = None) -> None:
        """
        Initialize shortcuts help dialog

        Args:
            shortcuts_list: List of tuples (key_combination, description)
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.shortcuts_list: List[Tuple[str, str]] = shortcuts_list
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components - Bilingual (ES/EN)"""
        self.setWindowTitle("Atajos de Teclado / Keyboard Shortcuts")
        self.setMinimumSize(650, 500)

        layout = QVBoxLayout()

        # Header
        header = QLabel("<h2>⌨️ Atajos de Teclado / Keyboard Shortcuts</h2>")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Description
        desc = QLabel(
            "🇪🇸 Usa estos atajos para navegar y controlar NEXUS rápidamente.<br>"
            "🇬🇧 Use these shortcuts to navigate and control NEXUS quickly."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Shortcuts table
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Atajo / Shortcut", "Acción / Action"])
        table.setRowCount(len(self.shortcuts_list))

        for i, (key, action) in enumerate(self.shortcuts_list):
            # Key column (bold)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            font = key_item.font()
            font.setBold(True)
            key_item.setFont(font)

            # Action column
            action_item = QTableWidgetItem(action)
            action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            table.setItem(i, 0, key_item)
            table.setItem(i, 1, action_item)

        # Adjust column widths
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Make table read-only and non-selectable (for display only)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        # Remove vertical header (row numbers)
        table.verticalHeader().setVisible(False)

        # Alternate row colors for better readability
        table.setAlternatingRowColors(True)

        layout.addWidget(table)

        # Close button
        close_btn = QPushButton("Cerrar / Close")
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)
