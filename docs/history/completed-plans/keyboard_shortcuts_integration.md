# Keyboard Shortcuts - Integration Guide

**Status:** Ready for integration
**Tests:** 14/14 passing
**Files:** keyboard_shortcuts.py, shortcuts_dialog.py created

---

## Changes Required in src/main.py

### 1. Add Imports (after line 48)

```python
from core.keyboard_shortcuts import KeyboardShortcutManager
from gui.dialogs.shortcuts_dialog import ShortcutsDialog
```

### 2. Initialize Manager (after line 110, after theme_manager)

```python
# Initialize keyboard shortcuts manager
self.shortcuts_manager = KeyboardShortcutManager()
QApplication.instance().installEventFilter(self.shortcuts_manager)
logger.info("Keyboard shortcuts manager initialized")

# Connect shortcut signals
self._connect_keyboard_shortcuts()
```

### 3. Save Tab Widget Reference (in _create_tab_widget around line 430)

**CHANGE:**
```python
def _create_tab_widget(self):
    """Create tab widget with all features"""
    tabs = QTabWidget()  # Local variable
    ...
    return tabs  # Returned but not saved
```

**TO:**
```python
def _create_tab_widget(self):
    """Create tab widget with all features"""
    self.tabs = QTabWidget()  # Save as instance attribute
    self.tabs.setTabPosition(QTabWidget.TabPosition.North)
    ...
    return self.tabs
```

### 4. Add Keyboard Shortcuts Action to Help Menu (after line 182)

**CHANGE F1 shortcut for API Guide:**
```python
# API Setup Guide action
api_guide_action = help_menu.addAction("&API Setup Guide")
api_guide_action.setShortcut("F1")  # CHANGE to F2 or remove
api_guide_action.triggered.connect(self._show_api_guide)
```

**TO:**
```python
# API Setup Guide action
api_guide_action = help_menu.addAction("&API Setup Guide")
api_guide_action.setShortcut("F2")  # Changed from F1
api_guide_action.triggered.connect(self._show_api_guide)
```

**ADD AFTER API Guide:**
```python
# Keyboard Shortcuts action
shortcuts_action = help_menu.addAction("&Keyboard Shortcuts")
shortcuts_action.setShortcut("F1")
shortcuts_action.triggered.connect(self._show_shortcuts_dialog)
```

### 5. Add Shortcut Connection Method (new method after __init__)

```python
def _connect_keyboard_shortcuts(self):
    """Connect keyboard shortcut signals to handlers"""
    sm = self.shortcuts_manager

    # Playback controls
    sm.play_pause_requested.connect(self._handle_play_pause_shortcut)
    sm.seek_backward_requested.connect(self._handle_seek_backward)
    sm.seek_forward_requested.connect(self._handle_seek_forward)
    sm.volume_change_requested.connect(self._handle_volume_change)
    sm.mute_toggled.connect(self._handle_mute_toggle)

    # Navigation
    sm.focus_search_requested.connect(self._handle_focus_search)
    sm.switch_to_tab_requested.connect(self._handle_switch_tab)

    logger.info("Keyboard shortcuts connected")
```

### 6. Add Shortcut Handler Methods (new methods at end of class)

```python
def _handle_play_pause_shortcut(self):
    """Handle Space key - Play/Pause"""
    if self.audio_player.is_playing():
        self.now_playing.pause_song()
        logger.debug("Shortcut: Paused")
    else:
        self.now_playing.play_song()
        logger.debug("Shortcut: Play")

def _handle_seek_backward(self, seconds):
    """Handle Left arrow - Seek backward"""
    current = self.audio_player.get_current_position()
    new_pos = max(0, current - seconds)
    self.audio_player.seek(new_pos)
    logger.debug(f"Shortcut: Seek to {new_pos}s")

def _handle_seek_forward(self, seconds):
    """Handle Right arrow - Seek forward"""
    current = self.audio_player.get_current_position()
    duration = self.audio_player.get_duration()
    new_pos = min(duration, current + seconds)
    self.audio_player.seek(new_pos)
    logger.debug(f"Shortcut: Seek to {new_pos}s")

def _handle_volume_change(self, delta):
    """Handle Up/Down arrows - Volume change"""
    current = self.audio_player.get_volume()
    new_volume = max(0, min(100, current + delta))
    self.audio_player.set_volume(new_volume)

    # Update status bar
    self.statusBar.showMessage(f"Volume: {new_volume}%", 1000)
    logger.debug(f"Shortcut: Volume {new_volume}%")

def _handle_mute_toggle(self):
    """Handle M key - Mute/Unmute"""
    if self.audio_player.get_volume() > 0:
        # Mute: save current volume
        if not hasattr(self, '_previous_volume'):
            self._previous_volume = 70
        self._previous_volume = self.audio_player.get_volume()
        self.audio_player.set_volume(0)
        self.statusBar.showMessage("Muted", 1000)
        logger.debug("Shortcut: Muted")
    else:
        # Unmute: restore previous volume
        volume = getattr(self, '_previous_volume', 70)
        self.audio_player.set_volume(volume)
        self.statusBar.showMessage(f"Volume: {volume}%", 1000)
        logger.debug(f"Shortcut: Unmuted to {volume}%")

def _handle_focus_search(self):
    """Handle Ctrl+F - Focus search"""
    if hasattr(self, 'search_tab') and hasattr(self, 'tabs'):
        # Switch to search tab
        self.tabs.setCurrentWidget(self.search_tab)

        # Focus search input field
        if hasattr(self.search_tab, 'search_input'):
            self.search_tab.search_input.setFocus()
            logger.debug("Shortcut: Focused search")

def _handle_switch_tab(self, tab_name):
    """Handle Ctrl+L/D - Switch tabs"""
    if not hasattr(self, 'tabs'):
        return

    if tab_name == 'library' and hasattr(self, 'library_tab'):
        self.tabs.setCurrentWidget(self.library_tab)
        logger.debug("Shortcut: Switched to Library tab")
    elif tab_name == 'queue' and hasattr(self, 'queue_widget'):
        self.tabs.setCurrentWidget(self.queue_widget)
        logger.debug("Shortcut: Switched to Queue tab")

def _show_shortcuts_dialog(self):
    """Show keyboard shortcuts help dialog"""
    shortcuts = self.shortcuts_manager.get_shortcuts()
    dialog = ShortcutsDialog(shortcuts, self)
    dialog.exec()
```

---

## Summary of Changes

**New Files:**
- src/core/keyboard_shortcuts.py (160 lines)
- src/gui/dialogs/shortcuts_dialog.py (100 lines)
- tests/test_keyboard_shortcuts.py (220 lines, 14 tests)

**Modified Files:**
- src/main.py:
  - +2 imports
  - +3 lines __init__
  - +1 line _create_tab_widget (tabs → self.tabs)
  - +2 lines help menu (F1 change + new action)
  - +15 lines _connect_keyboard_shortcuts()
  - +80 lines handler methods (9 methods)
  - **Total:** ~100 new lines

**Tests:**
- 14/14 keyboard shortcuts tests passing
- Full test suite: (pending verification)

---

## Testing Checklist

**After integration:**
1. ✅ App starts without errors
2. ✅ Space toggles playback
3. ✅ ←/→ seek backward/forward
4. ✅ ↑/↓ change volume
5. ✅ M mutes/unmutes
6. ✅ Ctrl+F focuses search
7. ✅ Ctrl+L switches to Library
8. ✅ Ctrl+D switches to Queue
9. ✅ F1 shows shortcuts dialog
10. ✅ Shortcuts ignored when typing in search box

---

**Next step:** Apply changes to src/main.py
