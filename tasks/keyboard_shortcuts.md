# ⌨️ Keyboard Shortcuts Implementation Plan

**Feature:** Global keyboard shortcuts for NEXUS Music Manager
**Priority:** HIGH (Quick win - 1-2 hours)
**Status:** PLANNED
**Created:** November 17, 2025

---

## 🎯 Objective

Implement global keyboard shortcuts to improve user experience and enable power users to navigate and control the application without touching the mouse.

**User Request:** Feature #1 from "vamos con todas, pero en orden"

---

## 📋 Requirements

### **Must Have:**

**Playback Controls:**
- `Space` → Play/Pause toggle
- `←` (Left Arrow) → Seek backward 5 seconds
- `→` (Right Arrow) → Seek forward 5 seconds
- `M` → Mute/Unmute toggle

**Volume Controls:**
- `↑` (Up Arrow) → Volume +10%
- `↓` (Down Arrow) → Volume -10%

**Navigation:**
- `Ctrl+F` → Focus search box (Search tab)
- `Ctrl+L` → Switch to Library tab
- `Ctrl+D` → Switch to Downloads/Queue tab

**Application:**
- `Ctrl+Q` → Quit (already exists, verify)
- `Ctrl+T` → Toggle theme (already exists from theme switcher)

### **Nice to Have (Future):**
- `Ctrl+N` → Now Playing tab
- `Ctrl+P` → Playlists tab
- `Ctrl+,` → Settings dialog
- `F1` → Help dialog

---

## 🏗️ Architecture

### **Implementation Strategy:**

**Option A: Global Event Filter (Recommended)**
- Install event filter on QApplication
- Intercept all key events globally
- Dispatch to appropriate handlers
- **Pros:** Works from any widget, single source of truth
- **Cons:** Must respect focus context (don't intercept when typing)

**Option B: Per-Widget Key Handlers**
- Override keyPressEvent() in main window
- **Pros:** Simpler, less invasive
- **Cons:** Doesn't work when child widgets have focus

**DECISION:** Use Option A (Global Event Filter) for professional UX

---

### **Code Structure:**

```
src/
├── core/
│   └── keyboard_shortcuts.py      # NEW - KeyboardShortcutManager class
└── gui/
    └── dialogs/
        └── shortcuts_dialog.py     # NEW - Help dialog with shortcuts list
```

**Integration points:**
- `src/main.py` → Install event filter, connect handlers

---

### **Data Flow:**

```
User presses key
    ↓
QApplication.notify() intercepts
    ↓
eventFilter() in KeyboardShortcutManager
    ↓
Check if typing context (QLineEdit focused?)
    ↓ NO
Match key to action
    ↓
Emit signal (e.g., play_pause_requested)
    ↓
Main window receives signal
    ↓
Execute action (self.audio_player.toggle_play_pause())
```

---

## 📐 Implementation Steps (TDD)

### **Phase 1: RED - Write Tests First**

**tests/test_keyboard_shortcuts.py:**

```python
class TestKeyboardShortcutManager(unittest.TestCase):
    """Test keyboard shortcut manager"""

    def test_01_manager_class_exists(self):
        """KeyboardShortcutManager class should exist"""

    def test_02_manager_is_singleton(self):
        """Manager should implement singleton pattern"""

    def test_03_manager_has_event_filter(self):
        """Manager should have eventFilter method"""

    def test_04_space_triggers_play_pause_signal(self):
        """Pressing Space should emit play_pause_requested signal"""

    def test_05_left_arrow_triggers_seek_backward(self):
        """Left arrow should emit seek_backward_requested(5)"""

    def test_06_right_arrow_triggers_seek_forward(self):
        """Right arrow should emit seek_forward_requested(5)"""

    def test_07_up_arrow_triggers_volume_up(self):
        """Up arrow should emit volume_change_requested(+10)"""

    def test_08_down_arrow_triggers_volume_down(self):
        """Down arrow should emit volume_change_requested(-10)"""

    def test_09_m_triggers_mute_toggle(self):
        """M key should emit mute_toggled signal"""

    def test_10_ctrl_f_triggers_focus_search(self):
        """Ctrl+F should emit focus_search_requested"""

    def test_11_ctrl_l_switches_to_library_tab(self):
        """Ctrl+L should emit switch_to_tab_requested('library')"""

    def test_12_ctrl_d_switches_to_queue_tab(self):
        """Ctrl+D should emit switch_to_tab_requested('queue')"""

    def test_13_typing_context_ignored(self):
        """Keys should be ignored when QLineEdit has focus"""

    def test_14_all_shortcuts_listed(self):
        """get_shortcuts() should return dict of all shortcuts"""
```

**Estimated:** 14 tests

---

### **Phase 2: GREEN - Implement Code**

#### **Step 1: Create KeyboardShortcutManager**

**src/core/keyboard_shortcuts.py:**

```python
"""
KeyboardShortcutManager - Global keyboard shortcut handler

Features:
- Singleton pattern
- Global event filter
- Context-aware (ignore when typing)
- Signal-based dispatch
"""

from PyQt6.QtCore import QObject, Qt, QEvent, pyqtSignal
from PyQt6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit

class KeyboardShortcutManager(QObject):
    """
    Manages global keyboard shortcuts for the application
    """

    # Signals
    play_pause_requested = pyqtSignal()
    seek_backward_requested = pyqtSignal(int)  # seconds
    seek_forward_requested = pyqtSignal(int)   # seconds
    volume_change_requested = pyqtSignal(int)  # delta percentage
    mute_toggled = pyqtSignal()
    focus_search_requested = pyqtSignal()
    switch_to_tab_requested = pyqtSignal(str)  # tab name

    _instance = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        super().__init__()
        self._initialized = True

        # Shortcut definitions
        self.shortcuts = {
            Qt.Key.Key_Space: ('Play/Pause', self.play_pause_requested),
            Qt.Key.Key_Left: ('Seek Backward 5s', self.seek_backward_requested),
            Qt.Key.Key_Right: ('Seek Forward 5s', self.seek_forward_requested),
            Qt.Key.Key_Up: ('Volume Up', self.volume_change_requested),
            Qt.Key.Key_Down: ('Volume Down', self.volume_change_requested),
            Qt.Key.Key_M: ('Mute/Unmute', self.mute_toggled),
        }

        self.ctrl_shortcuts = {
            Qt.Key.Key_F: ('Focus Search', self.focus_search_requested),
            Qt.Key.Key_L: ('Library Tab', self.switch_to_tab_requested),
            Qt.Key.Key_D: ('Queue Tab', self.switch_to_tab_requested),
        }

    def eventFilter(self, obj, event):
        """Global event filter for keyboard shortcuts"""
        if event.type() != QEvent.Type.KeyPress:
            return False

        # Ignore if typing in text field
        if self._is_typing_context(obj):
            return False

        key = event.key()
        modifiers = event.modifiers()

        # Handle Ctrl+Key shortcuts
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key in self.ctrl_shortcuts:
                self._handle_ctrl_shortcut(key)
                return True

        # Handle plain key shortcuts
        elif key in self.shortcuts:
            self._handle_shortcut(key)
            return True

        return False

    def _is_typing_context(self, widget):
        """Check if user is typing in text field"""
        focus_widget = widget
        while focus_widget:
            if isinstance(focus_widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
                return True
            focus_widget = focus_widget.parent()
        return False

    def _handle_shortcut(self, key):
        """Handle plain key shortcuts"""
        if key == Qt.Key.Key_Space:
            self.play_pause_requested.emit()
        elif key == Qt.Key.Key_Left:
            self.seek_backward_requested.emit(5)
        elif key == Qt.Key.Key_Right:
            self.seek_forward_requested.emit(5)
        elif key == Qt.Key.Key_Up:
            self.volume_change_requested.emit(+10)
        elif key == Qt.Key.Key_Down:
            self.volume_change_requested.emit(-10)
        elif key == Qt.Key.Key_M:
            self.mute_toggled.emit()

    def _handle_ctrl_shortcut(self, key):
        """Handle Ctrl+Key shortcuts"""
        if key == Qt.Key.Key_F:
            self.focus_search_requested.emit()
        elif key == Qt.Key.Key_L:
            self.switch_to_tab_requested.emit('library')
        elif key == Qt.Key.Key_D:
            self.switch_to_tab_requested.emit('queue')

    def get_shortcuts(self):
        """Get list of all shortcuts for display"""
        shortcuts_list = []

        # Plain shortcuts
        shortcuts_list.append(("Space", "Play/Pause"))
        shortcuts_list.append(("← (Left)", "Seek Backward 5s"))
        shortcuts_list.append(("→ (Right)", "Seek Forward 5s"))
        shortcuts_list.append(("↑ (Up)", "Volume +10%"))
        shortcuts_list.append(("↓ (Down)", "Volume -10%"))
        shortcuts_list.append(("M", "Mute/Unmute"))

        # Ctrl shortcuts
        shortcuts_list.append(("Ctrl+F", "Focus Search"))
        shortcuts_list.append(("Ctrl+L", "Library Tab"))
        shortcuts_list.append(("Ctrl+D", "Queue Tab"))
        shortcuts_list.append(("Ctrl+T", "Toggle Theme"))
        shortcuts_list.append(("Ctrl+Q", "Quit"))

        return shortcuts_list
```

---

#### **Step 2: Create Shortcuts Help Dialog**

**src/gui/dialogs/shortcuts_dialog.py:**

```python
"""Keyboard Shortcuts Help Dialog"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel
)
from PyQt6.QtCore import Qt

class ShortcutsDialog(QDialog):
    """Display keyboard shortcuts help"""

    def __init__(self, shortcuts_list, parent=None):
        super().__init__(parent)
        self.shortcuts_list = shortcuts_list
        self._init_ui()

    def _init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # Header
        header = QLabel("<h2>⌨️ Keyboard Shortcuts</h2>")
        layout.addWidget(header)

        # Shortcuts table
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        table.setRowCount(len(self.shortcuts_list))

        for i, (key, action) in enumerate(self.shortcuts_list):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(action))

        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        layout.addWidget(table)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)
```

---

#### **Step 3: Integrate into Main Window**

**Modify src/main.py:**

```python
# Add import
from core.keyboard_shortcuts import KeyboardShortcutManager
from gui.dialogs.shortcuts_dialog import ShortcutsDialog

class MusicManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # ... existing init ...

        # Initialize keyboard shortcuts manager
        self.shortcuts_manager = KeyboardShortcutManager()
        QApplication.instance().installEventFilter(self.shortcuts_manager)

        # Connect signals
        self._connect_keyboard_shortcuts()

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

    def _handle_play_pause_shortcut(self):
        """Handle Space key - Play/Pause"""
        if hasattr(self.now_playing_tab, 'audio_player'):
            if self.now_playing_tab.audio_player.is_playing():
                self.now_playing_tab.audio_player.pause()
            else:
                self.now_playing_tab.audio_player.play()

    def _handle_seek_backward(self, seconds):
        """Handle Left arrow - Seek backward"""
        if hasattr(self.now_playing_tab, 'audio_player'):
            current = self.now_playing_tab.audio_player.get_current_position()
            new_pos = max(0, current - seconds)
            self.now_playing_tab.audio_player.seek(new_pos)

    def _handle_seek_forward(self, seconds):
        """Handle Right arrow - Seek forward"""
        if hasattr(self.now_playing_tab, 'audio_player'):
            current = self.now_playing_tab.audio_player.get_current_position()
            duration = self.now_playing_tab.audio_player.get_duration()
            new_pos = min(duration, current + seconds)
            self.now_playing_tab.audio_player.seek(new_pos)

    def _handle_volume_change(self, delta):
        """Handle Up/Down arrows - Volume change"""
        if hasattr(self.now_playing_tab, 'audio_player'):
            current = self.now_playing_tab.audio_player.get_volume()
            new_volume = max(0, min(100, current + delta))
            self.now_playing_tab.audio_player.set_volume(new_volume)

    def _handle_mute_toggle(self):
        """Handle M key - Mute/Unmute"""
        if hasattr(self.now_playing_tab, 'audio_player'):
            if self.now_playing_tab.audio_player.get_volume() > 0:
                self._previous_volume = self.now_playing_tab.audio_player.get_volume()
                self.now_playing_tab.audio_player.set_volume(0)
            else:
                volume = getattr(self, '_previous_volume', 70)
                self.now_playing_tab.audio_player.set_volume(volume)

    def _handle_focus_search(self):
        """Handle Ctrl+F - Focus search"""
        if hasattr(self, 'search_tab'):
            self.tabs.setCurrentWidget(self.search_tab)
            if hasattr(self.search_tab, 'search_input'):
                self.search_tab.search_input.setFocus()

    def _handle_switch_tab(self, tab_name):
        """Handle Ctrl+L/D - Switch tabs"""
        if tab_name == 'library' and hasattr(self, 'library_tab'):
            self.tabs.setCurrentWidget(self.library_tab)
        elif tab_name == 'queue' and hasattr(self, 'queue_tab'):
            self.tabs.setCurrentWidget(self.queue_tab)

    def _create_help_menu(self, menubar):
        """Create help menu"""
        help_menu = menubar.addMenu("&Help")

        # Keyboard Shortcuts action
        shortcuts_action = help_menu.addAction("&Keyboard Shortcuts")
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)

    def _show_shortcuts_dialog(self):
        """Show keyboard shortcuts help dialog"""
        shortcuts = self.shortcuts_manager.get_shortcuts()
        dialog = ShortcutsDialog(shortcuts, self)
        dialog.exec()
```

---

### **Phase 3: REFACTOR - Optimize & Polish**

**Improvements:**
1. Add visual feedback when shortcuts are used (status bar messages)
2. Add logging for debugging
3. Consider adding shortcuts customization (future enhancement)
4. Add tooltips mentioning shortcuts on buttons

---

## ✅ Success Metrics

**Must Pass:**
- ✅ All 14 tests passing
- ✅ Space key toggles playback
- ✅ Arrow keys control seek/volume
- ✅ Ctrl+F focuses search box
- ✅ Ctrl+L/D switch tabs
- ✅ F1 shows shortcuts dialog
- ✅ Shortcuts ignored when typing in search box
- ✅ No conflicts with existing shortcuts (Ctrl+Q, Ctrl+T)

**Nice to Have:**
- Status bar feedback when shortcuts used
- Visual hints (e.g., "Press Space to play")
- Customizable shortcuts (future)

---

## 🔧 Technical Considerations

**Qt Event Filter Best Practices:**
1. Always check `event.type()` first
2. Return `False` to let event propagate
3. Return `True` to consume event (prevent propagation)
4. Respect typing context (don't intercept text editing)

**Signal/Slot Pattern:**
- Manager emits signals → Main window handles actions
- Clean separation: shortcuts logic vs application logic
- Easy to test: mock signals in unit tests

**Singleton Pattern:**
- Only one instance globally
- Prevents multiple event filters

---

## 📊 Estimated Timeline

- ✅ **Planning:** 20 minutes (this file)
- ⏳ **Writing Tests (RED):** 30 minutes
- ⏳ **Implementation (GREEN):** 40 minutes
- ⏳ **Integration & Testing:** 20 minutes
- ⏳ **Documentation & Commit:** 10 minutes

**Total:** ~2 hours (within 1-2 hour estimate)

---

## 🎯 Testing Strategy

**Unit Tests:**
- Test each shortcut emits correct signal
- Test typing context detection
- Test singleton pattern

**Manual Testing:**
1. Launch application
2. Test each shortcut while NOT in search box
3. Test shortcuts IGNORED while typing in search box
4. Test F1 shows help dialog
5. Verify no conflicts with existing shortcuts

---

## 📝 Future Enhancements (Out of Scope)

- ⏳ Customizable shortcuts (user preferences)
- ⏳ Cheat sheet overlay (press ? to show)
- ⏳ More shortcuts (Ctrl+N, Ctrl+P, etc.)
- ⏳ Global media keys support (play/pause buttons on keyboard)
- ⏳ Vim-like navigation (j/k for up/down)

---

**Status:** PLANNED → Ready for TDD implementation
**Next Step:** Write tests in tests/test_keyboard_shortcuts.py (RED phase)
**Assigned to:** NEXUS@CLI
**Created:** November 17, 2025
