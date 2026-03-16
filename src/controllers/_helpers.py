"""Shared helpers for controller modules."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget


def sync_volume_ui(now_playing: QWidget, percentage: int) -> None:
    """Update volume slider and label in NowPlayingWidget without triggering signals."""
    if hasattr(now_playing, "volume_slider"):
        now_playing.volume_slider.blockSignals(True)
        now_playing.volume_slider.setValue(percentage)
        now_playing.volume_slider.blockSignals(False)
        if hasattr(now_playing, "volume_label_value"):
            now_playing.volume_label_value.setText(f"{percentage}%")
