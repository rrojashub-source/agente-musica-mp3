"""
Plugins Tab - Plugin Management GUI
Allows users to view, enable, disable and configure plugins

Created: November 24, 2025
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QGroupBox,
    QMessageBox, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QCheckBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor, QFont
import logging
from typing import Optional, Dict, Any

from plugins import PluginManager, Plugin

logger = logging.getLogger(__name__)


class PluginSettingsDialog(QDialog):
    """Dialog for editing plugin settings"""

    def __init__(self, plugin: Plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self._init_ui()

    def _init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle(f"Settings - {self.plugin.metadata.display_name}")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Plugin info
        info_label = QLabel(
            f"<b>{self.plugin.metadata.display_name}</b> v{self.plugin.version}<br>"
            f"by {self.plugin.metadata.author}"
        )
        layout.addWidget(info_label)

        # Settings form
        form_group = QGroupBox("Settings")
        form_layout = QFormLayout()

        self._setting_widgets: Dict[str, QWidget] = {}

        # Check if plugin has settings schema
        if hasattr(self.plugin, 'get_settings_schema'):
            schema = self.plugin.get_settings_schema()
            for key, config in schema.items():
                widget = self._create_widget(key, config)
                if widget:
                    label = config.get('label', key)
                    form_layout.addRow(label + ":", widget)
                    self._setting_widgets[key] = widget
        else:
            # Generic settings display
            settings = self.plugin.get_all_settings()
            for key, value in settings.items():
                widget = QLineEdit(str(value))
                form_layout.addRow(key + ":", widget)
                self._setting_widgets[key] = widget

        if not self._setting_widgets:
            form_layout.addRow(QLabel("This plugin has no configurable settings."))

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def _create_widget(self, key: str, config: Dict[str, Any]) -> Optional[QWidget]:
        """Create widget based on config type"""
        widget_type = config.get('type', 'text')
        current_value = self.plugin.get_setting(key, config.get('default', ''))

        if widget_type == 'text':
            widget = QLineEdit(str(current_value))
            if 'description' in config:
                widget.setPlaceholderText(config['description'])
            return widget

        elif widget_type == 'password':
            widget = QLineEdit(str(current_value))
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            return widget

        elif widget_type == 'checkbox':
            widget = QCheckBox()
            widget.setChecked(bool(current_value))
            return widget

        elif widget_type == 'number':
            widget = QLineEdit(str(current_value))
            return widget

        return QLineEdit(str(current_value))

    def _save_settings(self):
        """Save settings and close dialog"""
        settings = {}
        for key, widget in self._setting_widgets.items():
            if isinstance(widget, QLineEdit):
                settings[key] = widget.text()
            elif isinstance(widget, QCheckBox):
                settings[key] = widget.isChecked()

        self.plugin.load_settings(settings)
        self.accept()


class PluginsTab(QWidget):
    """
    Plugins Management Tab

    Features:
    - List all available plugins
    - Enable/disable plugins
    - View plugin details
    - Access plugin settings
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plugin_manager: Optional[PluginManager] = None
        self._init_ui()
        self._init_plugin_manager()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Header
        header_label = QLabel("🔌 Plugins")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header_label)

        # Info
        info_label = QLabel(
            "Extend NEXUS Music Manager with plugins.\n"
            "Enable or disable plugins to customize your experience."
        )
        info_label.setStyleSheet("color: #666;")
        layout.addWidget(info_label)

        # Plugins table
        table_group = QGroupBox("Available Plugins")
        table_layout = QVBoxLayout()

        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(5)
        self.plugins_table.setHorizontalHeaderLabels([
            "Status", "Name", "Version", "Author", "Description"
        ])
        self.plugins_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self.plugins_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.plugins_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.plugins_table.setAlternatingRowColors(True)
        self.plugins_table.itemSelectionChanged.connect(self._on_selection_changed)
        table_layout.addWidget(self.plugins_table)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Action buttons
        actions_layout = QHBoxLayout()

        self.enable_btn = QPushButton("✅ Enable")
        self.enable_btn.setEnabled(False)
        self.enable_btn.clicked.connect(self._enable_selected)
        actions_layout.addWidget(self.enable_btn)

        self.disable_btn = QPushButton("⏸️ Disable")
        self.disable_btn.setEnabled(False)
        self.disable_btn.clicked.connect(self._disable_selected)
        actions_layout.addWidget(self.disable_btn)

        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setEnabled(False)
        self.settings_btn.clicked.connect(self._open_settings)
        actions_layout.addWidget(self.settings_btn)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._refresh_plugins)
        actions_layout.addWidget(self.refresh_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Details panel
        details_group = QGroupBox("Plugin Details")
        details_layout = QVBoxLayout()

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        self.details_text.setStyleSheet("font-family: monospace;")
        self.details_text.setPlaceholderText("Select a plugin to view details...")
        details_layout.addWidget(self.details_text)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Stats
        self.stats_label = QLabel("Loaded: 0 | Enabled: 0")
        self.stats_label.setStyleSheet("color: #666;")
        layout.addWidget(self.stats_label)

        layout.addStretch()
        self.setLayout(layout)

    def _init_plugin_manager(self):
        """Initialize plugin manager"""
        try:
            self._plugin_manager = PluginManager.get_instance()
            self._plugin_manager.load_plugins()

            # Connect signals
            if hasattr(self._plugin_manager, 'plugin_enabled'):
                self._plugin_manager.plugin_enabled.connect(self._on_plugin_enabled)
                self._plugin_manager.plugin_disabled.connect(self._on_plugin_disabled)
                self._plugin_manager.plugin_error.connect(self._on_plugin_error)

            self._refresh_plugins()

        except Exception as e:
            logger.error(f"Failed to init plugin manager: {e}")

    def _refresh_plugins(self):
        """Refresh plugins list"""
        if not self._plugin_manager:
            return

        self.plugins_table.setRowCount(0)

        plugins_info = self._plugin_manager.get_all_plugin_info()

        for info in plugins_info:
            row = self.plugins_table.rowCount()
            self.plugins_table.insertRow(row)

            metadata = info['metadata']
            enabled = info['enabled']

            # Status
            status_item = QTableWidgetItem("✅ Enabled" if enabled else "⏸️ Disabled")
            status_item.setData(Qt.ItemDataRole.UserRole, metadata['name'])
            if enabled:
                status_item.setForeground(QColor("#4CAF50"))
            else:
                status_item.setForeground(QColor("#666"))
            self.plugins_table.setItem(row, 0, status_item)

            # Name
            name_item = QTableWidgetItem(metadata['display_name'])
            name_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.plugins_table.setItem(row, 1, name_item)

            # Version
            self.plugins_table.setItem(row, 2, QTableWidgetItem(metadata['version']))

            # Author
            self.plugins_table.setItem(row, 3, QTableWidgetItem(metadata['author']))

            # Description
            self.plugins_table.setItem(row, 4, QTableWidgetItem(metadata['description']))

        # Update stats
        total = len(plugins_info)
        enabled = len([p for p in plugins_info if p['enabled']])
        self.stats_label.setText(f"Loaded: {total} | Enabled: {enabled}")

    def _on_selection_changed(self):
        """Handle selection change"""
        selected = self.plugins_table.selectedItems()
        if not selected:
            self.enable_btn.setEnabled(False)
            self.disable_btn.setEnabled(False)
            self.settings_btn.setEnabled(False)
            self.details_text.clear()
            return

        # Get plugin name from first column
        row = selected[0].row()
        plugin_name = self.plugins_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        if not plugin_name or not self._plugin_manager:
            return

        is_enabled = self._plugin_manager.is_plugin_enabled(plugin_name)
        self.enable_btn.setEnabled(not is_enabled)
        self.disable_btn.setEnabled(is_enabled)
        self.settings_btn.setEnabled(True)

        # Show details
        plugin = self._plugin_manager.get_plugin(plugin_name)
        if plugin:
            metadata = plugin.metadata
            details = (
                f"Name: {metadata.display_name}\n"
                f"ID: {metadata.name}\n"
                f"Version: {metadata.version}\n"
                f"Author: {metadata.author}\n"
                f"Description: {metadata.description}\n"
                f"Website: {metadata.website or 'N/A'}\n"
                f"Min App Version: {metadata.min_app_version}\n"
                f"Dependencies: {', '.join(metadata.dependencies) or 'None'}\n"
                f"Hooks: {', '.join(h.name for h in metadata.hooks) or 'None'}"
            )
            self.details_text.setText(details)

    def _get_selected_plugin_name(self) -> Optional[str]:
        """Get name of selected plugin"""
        selected = self.plugins_table.selectedItems()
        if selected:
            row = selected[0].row()
            return self.plugins_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return None

    def _enable_selected(self):
        """Enable selected plugin"""
        plugin_name = self._get_selected_plugin_name()
        if plugin_name and self._plugin_manager:
            if self._plugin_manager.enable_plugin(plugin_name):
                self._refresh_plugins()

    def _disable_selected(self):
        """Disable selected plugin"""
        plugin_name = self._get_selected_plugin_name()
        if plugin_name and self._plugin_manager:
            if self._plugin_manager.disable_plugin(plugin_name):
                self._refresh_plugins()

    def _open_settings(self):
        """Open settings dialog for selected plugin"""
        plugin_name = self._get_selected_plugin_name()
        if plugin_name and self._plugin_manager:
            plugin = self._plugin_manager.get_plugin(plugin_name)
            if plugin:
                dialog = PluginSettingsDialog(plugin, self)
                if dialog.exec():
                    # Save settings
                    self._plugin_manager.save_plugin_settings(
                        plugin_name,
                        plugin.get_all_settings()
                    )

    @pyqtSlot(str)
    def _on_plugin_enabled(self, plugin_name: str):
        """Handle plugin enabled signal"""
        self._refresh_plugins()

    @pyqtSlot(str)
    def _on_plugin_disabled(self, plugin_name: str):
        """Handle plugin disabled signal"""
        self._refresh_plugins()

    @pyqtSlot(str, str)
    def _on_plugin_error(self, plugin_name: str, error: str):
        """Handle plugin error signal"""
        QMessageBox.warning(
            self,
            "Plugin Error",
            f"Error with plugin '{plugin_name}':\n{error}"
        )
