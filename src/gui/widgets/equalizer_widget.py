"""
Equalizer Widget - 10-Band Graphic Equalizer UI

Visual equalizer control panel with preset selection and manual band adjustment.

Features:
- 10 vertical sliders for frequency bands
- Preset dropdown with built-in and custom presets
- Save/delete custom presets
- Enable/disable toggle
- Visual band labels (31Hz to 16kHz)
- dB value display per band

Created: December 11, 2025
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.audio_equalizer import BUILTIN_PRESETS, AudioEqualizer
from gui.themes.style_constants import Styles

logger = logging.getLogger(__name__)


class BandSlider(QWidget):
    """Single frequency band slider with label"""

    value_changed = Signal(int, float)  # frequency, gain

    def __init__(self, frequency: int, label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.frequency: int = frequency
        self.label_text: str = label
        self.db_label: QLabel
        self.slider: QSlider
        self.freq_label: QLabel

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # dB value label (top)
        self.db_label = QLabel("0")
        self.db_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.db_label.setFixedWidth(35)
        self.db_label.setStyleSheet(Styles.EQ_LABEL_NEUTRAL)
        layout.addWidget(self.db_label)

        # Slider (vertical, inverted for natural feel)
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(-120, 120)  # -12dB to +12dB (x10 for precision)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.slider.setTickInterval(40)  # Every 4dB
        self.slider.setMinimumHeight(150)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, 1)

        # Frequency label (bottom)
        self.freq_label = QLabel(self.label_text)
        self.freq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.freq_label.setFont(font)
        layout.addWidget(self.freq_label)

    def _on_value_changed(self, value: int) -> None:
        """Handle slider value change"""
        gain_db = value / 10.0  # Convert to dB
        self._update_db_label(gain_db)
        self.value_changed.emit(self.frequency, gain_db)

    def _update_db_label(self, gain_db: float) -> None:
        """Update the dB display label"""
        if gain_db >= 0:
            self.db_label.setText(f"+{gain_db:.1f}")
            self.db_label.setStyleSheet(Styles.EQ_LABEL_BOOST)  # Green for boost
        else:
            self.db_label.setText(f"{gain_db:.1f}")
            self.db_label.setStyleSheet(Styles.EQ_LABEL_CUT)  # Red for cut

    def set_value(self, gain_db: float) -> None:
        """Set slider value without emitting signal"""
        self.slider.blockSignals(True)
        self.slider.setValue(int(gain_db * 10))
        self._update_db_label(gain_db)
        self.slider.blockSignals(False)

    def get_value(self) -> float:
        """Get current gain in dB"""
        return self.slider.value() / 10.0  # type: ignore[no-any-return]


class EqualizerWidget(QWidget):
    """
    10-Band Graphic Equalizer Widget

    Provides visual control for audio equalization with presets.
    """

    # Signals
    eq_changed = Signal(dict)  # Emitted when any band changes {freq: gain}
    preset_changed = Signal(str)  # Emitted when preset changes

    def __init__(self, equalizer: Optional[AudioEqualizer] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Use provided equalizer or create new one
        self.equalizer: AudioEqualizer = equalizer or AudioEqualizer()

        # Band sliders
        self._sliders: Dict[int, BandSlider] = {}

        self.enable_checkbox: QCheckBox
        self.preset_combo: QComboBox
        self.save_btn: QPushButton
        self.delete_btn: QPushButton
        self.reset_btn: QPushButton
        self.desc_label: QLabel

        self._init_ui()
        self._load_current_settings()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # === Header Section ===
        header_layout = QHBoxLayout()

        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable EQ")
        self.enable_checkbox.setChecked(self.equalizer.is_enabled())
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        header_layout.addWidget(self.enable_checkbox)

        header_layout.addStretch()

        # Preset selector
        preset_label = QLabel("Preset:")
        header_layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(150)
        self._populate_presets()
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        header_layout.addWidget(self.preset_combo)

        # Save preset button
        self.save_btn = QPushButton("Save")
        self.save_btn.setToolTip("Save current settings as custom preset")
        self.save_btn.clicked.connect(self._save_preset)
        header_layout.addWidget(self.save_btn)

        # Delete preset button
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setToolTip("Delete selected custom preset")
        self.delete_btn.clicked.connect(self._delete_preset)
        header_layout.addWidget(self.delete_btn)

        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setToolTip("Reset all bands to 0dB")
        self.reset_btn.clicked.connect(self._reset_eq)
        header_layout.addWidget(self.reset_btn)

        main_layout.addLayout(header_layout)

        # === Equalizer Bands Section ===
        eq_group = QGroupBox("Frequency Bands")
        eq_layout = QHBoxLayout(eq_group)
        eq_layout.setSpacing(5)

        # Create sliders for each band
        bands = self.equalizer.get_band_frequencies()
        labels = self.equalizer.get_band_labels()

        for freq, label in zip(bands, labels):
            slider = BandSlider(freq, label)
            slider.value_changed.connect(self._on_band_changed)
            eq_layout.addWidget(slider)
            self._sliders[freq] = slider

        main_layout.addWidget(eq_group)

        # === Info Section ===
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        info_layout = QHBoxLayout(info_frame)

        # Preset description
        self.desc_label = QLabel("")
        self.desc_label.setStyleSheet(Styles.TEXT_DIMMED + " font-style: italic;")
        info_layout.addWidget(self.desc_label)

        info_layout.addStretch()

        # dB scale reference
        scale_label = QLabel("Scale: -12dB to +12dB")
        scale_label.setStyleSheet(Styles.LABEL_TINY_FADED)
        info_layout.addWidget(scale_label)

        main_layout.addWidget(info_frame)

    def _populate_presets(self) -> None:
        """Populate preset combo box"""
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()

        # Add built-in presets
        self.preset_combo.addItem("-- Built-in --")
        for name, preset in BUILTIN_PRESETS.items():
            self.preset_combo.addItem(preset.name, name)

        # Add custom presets
        custom_presets = [name for name in self.equalizer.get_preset_names() if name not in BUILTIN_PRESETS]
        if custom_presets:
            self.preset_combo.addItem("-- Custom --")
            for name in custom_presets:
                preset = self.equalizer.get_preset_info(name)
                if preset:
                    self.preset_combo.addItem(preset.name, name)

        self.preset_combo.blockSignals(False)

    def _load_current_settings(self) -> None:
        """Load current equalizer settings into UI"""
        gains = self.equalizer.get_all_gains()

        for freq, gain in gains.items():
            if freq in self._sliders:
                self._sliders[freq].set_value(gain)

        # Set current preset in combo
        current = self.equalizer.get_current_preset()
        self._select_preset_in_combo(current)
        self._update_description(current)

    def _select_preset_in_combo(self, preset_name: str) -> None:
        """Select a preset in the combo box"""
        self.preset_combo.blockSignals(True)
        for i in range(self.preset_combo.count()):
            if self.preset_combo.itemData(i) == preset_name:
                self.preset_combo.setCurrentIndex(i)
                break
        self.preset_combo.blockSignals(False)

    def _update_description(self, preset_name: str) -> None:
        """Update the description label"""
        preset = self.equalizer.get_preset_info(preset_name)
        if preset and preset.description:
            self.desc_label.setText(preset.description)
        else:
            self.desc_label.setText("")

        # Enable delete only for custom presets
        is_custom = preset and preset.is_custom if preset else False
        self.delete_btn.setEnabled(is_custom)

    def _on_enable_changed(self, state: int) -> None:
        """Handle enable checkbox change"""
        enabled = state == Qt.CheckState.Checked.value
        self.equalizer.set_enabled(enabled)

        # Disable/enable sliders
        for slider in self._sliders.values():
            slider.setEnabled(enabled)

    def _on_preset_selected(self, text: str) -> None:
        """Handle preset selection"""
        # Skip separator items
        if text.startswith("--"):
            return

        # Get preset key from item data
        idx = self.preset_combo.currentIndex()
        preset_key = self.preset_combo.itemData(idx)

        if preset_key:
            self.equalizer.apply_preset(preset_key)
            self._load_current_settings()
            self._update_description(preset_key)
            self.preset_changed.emit(preset_key)

    def _on_band_changed(self, frequency: int, gain: float) -> None:
        """Handle band slider change"""
        self.equalizer.set_band_gain(frequency, gain)

        # Emit change signal
        self.eq_changed.emit(self.equalizer.get_all_gains())

    def _save_preset(self) -> None:
        """Save current settings as custom preset"""
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:", text="My Preset")

        if ok and name:
            desc, ok2 = QInputDialog.getText(self, "Save Preset", "Enter description (optional):")

            if self.equalizer.save_custom_preset(name, desc if ok2 else ""):
                self._populate_presets()
                self._select_preset_in_combo(name.lower().replace(" ", "_"))
                QMessageBox.information(self, "Preset Saved", f"Preset '{name}' has been saved.")

    def _delete_preset(self) -> None:
        """Delete selected custom preset"""
        idx = self.preset_combo.currentIndex()
        preset_key = self.preset_combo.itemData(idx)
        preset_name = self.preset_combo.currentText()

        if not preset_key or preset_key in BUILTIN_PRESETS:
            return

        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete '{preset_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.equalizer.delete_custom_preset(preset_key):
                self._populate_presets()
                self.equalizer.apply_preset("flat")
                self._load_current_settings()

    def _reset_eq(self) -> None:
        """Reset equalizer to flat"""
        self.equalizer.reset()
        self._load_current_settings()
        self._select_preset_in_combo("flat")
        self._update_description("flat")
        self.eq_changed.emit(self.equalizer.get_all_gains())

    def get_equalizer(self) -> AudioEqualizer:
        """Get the equalizer instance"""
        return self.equalizer

    def refresh(self) -> None:
        """Refresh UI from equalizer state"""
        self._load_current_settings()
        self._populate_presets()
