# Feature: Dark/Light Theme Switcher

**Created:** November 17, 2025
**Status:** In Progress
**Priority:** High (UX Enhancement)
**Estimated Time:** 2-3 hours

---

## 🎯 Objective

Implement professional dark/light theme switcher for NEXUS Music Manager with:
- Global theme management system
- User preference persistence
- Keyboard shortcut (Ctrl+T)
- Smooth transition between themes
- All widgets themed consistently

---

## 📋 Requirements

### Functional Requirements:
1. **Theme Manager** - Centralized theme management
2. **Two Themes** - Dark (default) + Light mode
3. **Toggle UI** - View menu + keyboard shortcut
4. **Persistence** - Save user preference to config file
5. **Apply Globally** - All widgets use theme colors
6. **Smooth UX** - Instant theme switch without restart

### Non-Functional Requirements:
- Compatible with existing inline styles
- No breaking changes to current UI
- Performance: < 100ms theme switch
- Test coverage: 80%+

---

## 🏗️ Architecture

### Components:

```
src/
├── core/
│   └── theme_manager.py          # NEW - Theme management engine
├── gui/
│   └── themes/                    # NEW - Theme definitions
│       ├── __init__.py
│       ├── dark.qss               # Dark theme stylesheet
│       └── light.qss              # Light theme stylesheet
└── main.py                        # Modified - Apply theme globally
```

### Data Flow:

```
User clicks "View → Dark/Light Theme" (or Ctrl+T)
    ↓
ThemeManager.toggle_theme()
    ↓
Load QSS file (dark.qss or light.qss)
    ↓
QApplication.setStyleSheet(qss_content)
    ↓
Save preference to ~/.nexus_music/config.json
    ↓
All widgets update instantly (Qt signals)
```

---

## 📝 Implementation Plan

### **Step 1: Create ThemeManager (Core Engine)**

**File:** `src/core/theme_manager.py`

**Features:**
- Singleton pattern (one instance globally)
- Load/apply QSS files
- Toggle between themes
- Persist preference to config file
- Emit signal on theme change (for widgets that need custom handling)

**Methods:**
```python
class ThemeManager:
    def __init__(self):
        self.current_theme = "dark"  # default
        self.config_path = Path.home() / ".nexus_music" / "config.json"
        self._load_preference()

    def get_current_theme(self) -> str
    def apply_theme(self, theme_name: str) -> None
    def toggle_theme(self) -> str
    def _load_qss(self, theme_name: str) -> str
    def _save_preference(self) -> None
    def _load_preference(self) -> None
```

**Tests:** `tests/test_theme_manager.py` (10 tests)
- test_singleton_pattern
- test_default_theme_is_dark
- test_apply_dark_theme
- test_apply_light_theme
- test_toggle_theme_dark_to_light
- test_toggle_theme_light_to_dark
- test_save_preference_to_config
- test_load_preference_from_config
- test_invalid_theme_raises_error
- test_missing_qss_file_fallback

---

### **Step 2: Create QSS Stylesheets**

**File:** `src/gui/themes/dark.qss`

**Colors (Dark Theme):**
```css
Background:     #1e1e1e (main), #2d2d2d (secondary)
Text:           #ffffff (primary), #cccccc (secondary)
Accent:         #0078d4 (blue), #00c853 (green)
Border:         #3f3f3f
Highlight:      #094771 (selected row)
```

**File:** `src/gui/themes/light.qss`

**Colors (Light Theme):**
```css
Background:     #ffffff (main), #f5f5f5 (secondary)
Text:           #000000 (primary), #666666 (secondary)
Accent:         #0078d4 (blue), #00c853 (green)
Border:         #cccccc
Highlight:      #e3f2fd (selected row)
```

**Widgets to Style:**
- QMainWindow (background)
- QTableWidget (library, search results)
- QPushButton (all buttons)
- QSlider (progress, volume)
- QLabel (titles, metadata)
- QLineEdit (search box)
- QMenuBar, QMenu
- QTabWidget (main tabs)
- QTreeWidget (playlists, duplicates)
- QProgressBar (downloads)

---

### **Step 3: Add Toggle UI**

**File:** `src/main.py` (modify)

**Changes:**
1. Import ThemeManager
2. Add "View" menu (if not exists)
3. Add "Toggle Dark/Light Theme" action
4. Add keyboard shortcut: Ctrl+T
5. Connect to ThemeManager.toggle_theme()
6. Apply theme on startup (from config)

**Code:**
```python
# In __init__:
self.theme_manager = ThemeManager()
self.theme_manager.apply_theme(self.theme_manager.current_theme)

# In _create_menu_bar:
view_menu = menubar.addMenu("&View")
theme_action = view_menu.addAction("Toggle &Dark/Light Theme")
theme_action.setShortcut("Ctrl+T")
theme_action.triggered.connect(self._toggle_theme)

def _toggle_theme(self):
    new_theme = self.theme_manager.toggle_theme()
    self.statusBar().showMessage(f"Switched to {new_theme} theme", 2000)
```

---

### **Step 4: Config Persistence**

**File:** `~/.nexus_music/config.json`

**Format:**
```json
{
  "theme": "dark",
  "version": "1.0",
  "last_updated": "2025-11-17T09:30:00"
}
```

**Features:**
- Auto-create if missing (default to dark)
- Load on app startup
- Save on theme change
- Atomic write (use temp file + rename)

---

### **Step 5: Testing**

**Unit Tests:** `tests/test_theme_manager.py`
- ThemeManager class methods (10 tests)

**Integration Tests:** `tests/test_theme_integration.py`
- Load app with dark theme
- Toggle to light theme
- Restart app, theme persists
- Invalid config recovery

**Manual Testing:**
- Open app → Default dark theme
- Ctrl+T → Switch to light
- Close app → Reopen → Light theme persists
- View menu → Toggle back to dark
- All widgets update colors correctly
- No visual glitches

---

## 🎨 Design Decisions

### **Decision 1: QSS vs QPalette**
- **Chosen:** QSS (Qt Style Sheets)
- **Why:** More flexible, easier to maintain, supports pseudo-states
- **Alternative:** QPalette (more native, but limited customization)

### **Decision 2: Global vs Per-Widget Theming**
- **Chosen:** Global QApplication stylesheet + widget overrides
- **Why:** Consistent look, easy to apply, works with existing inline styles
- **Alternative:** Each widget manages own theme (complex, error-prone)

### **Decision 3: Config Location**
- **Chosen:** `~/.nexus_music/config.json`
- **Why:** User-specific, cross-platform, JSON easy to edit manually
- **Alternative:** SQLite database (overkill for single setting)

### **Decision 4: Default Theme**
- **Chosen:** Dark theme
- **Why:** Modern apps default to dark, easier on eyes, less battery (OLED)
- **Alternative:** Light theme (traditional, but less popular now)

---

## 📊 Success Metrics

**Must Have:**
- ✅ Theme persists across app restarts
- ✅ All widgets use theme colors (no hardcoded colors visible)
- ✅ Keyboard shortcut works (Ctrl+T)
- ✅ Toggle from View menu works
- ✅ No performance degradation

**Nice to Have:**
- Smooth fade transition (optional, low priority)
- Icon color adaptation (invert icons for light theme)
- System theme detection (match OS dark mode)

---

## 🚀 Implementation Order (TDD)

### **Phase 1: Core (30 min)**
1. Write tests for ThemeManager
2. Implement ThemeManager class
3. Run tests → All pass

### **Phase 2: Stylesheets (45 min)**
4. Create dark.qss with comprehensive styles
5. Create light.qss with comprehensive styles
6. Test loading QSS files

### **Phase 3: Integration (30 min)**
7. Modify main.py to use ThemeManager
8. Add View menu toggle
9. Add keyboard shortcut
10. Test theme switch

### **Phase 4: Polish (30 min)**
11. Test all tabs/widgets with both themes
12. Fix any visual inconsistencies
13. Add status bar feedback on toggle
14. Final manual testing

### **Phase 5: Git Commit (15 min)**
15. Review all changes
16. Run full test suite (308 → 320 tests)
17. Git commit with professional message
18. Update TRACKING.md

---

## 📝 Notes

**Compatibility:**
- Works alongside existing inline styles
- Inline styles have higher specificity (won't break)
- Can gradually migrate inline → QSS later

**Future Enhancements:**
- System theme detection (match OS)
- Custom themes (user-defined colors)
- Theme preview before applying
- Export/import themes

---

**Plan Created By:** NEXUS@CLI
**Approved By:** Ricardo (pending)
**Estimated Completion:** 2.5 hours
