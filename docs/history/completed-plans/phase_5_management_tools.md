# Phase 5: Management & Cleanup Tools - Implementation Plan

**Project:** AGENTE_MUSICA_MP3_001
**Phase:** 5 of 6
**Status:** PLANNING → Ready for Implementation
**Created:** November 13, 2025
**Methodology:** NEXUS 4-Phase Workflow + TDD (Red → Green → Refactor)

---

## 📋 PHASE 5 OVERVIEW

**Goal:** Implement library management tools for organizing, deduplicating, and maintaining music collections.

**Duration:** 10-12 days (estimated)
**Features:** 3 major features
**Test Target:** 40-50 new tests
**Dependencies:** Phase 4 complete ✅ (148/148 tests passing)

---

## 🎯 FEATURES BREAKDOWN

### **Feature 5.1: Duplicates Detection** (4-5 days)
- Detect duplicate songs using 3 methods
- GUI for reviewing and managing duplicates
- Safe deletion with preview

### **Feature 5.2: Auto-Organize Library** (3-4 days)
- Organize files into clean folder structure
- Multiple templates (by genre, artist, album)
- Preview before executing

### **Feature 5.3: Batch Rename Files** (2-3 days)
- Template-based renaming
- Preview mode
- Undo/rollback support

---

## 📊 SUCCESS CRITERIA (Definition of Done)

**Phase 5 is COMPLETE when:**

✅ **Duplicates Detection:**
- Detect 95%+ of real duplicates (0 false positives)
- 3 detection methods working (metadata, fingerprint, filesize)
- GUI shows duplicates grouped correctly
- Safe deletion with confirmation

✅ **Auto-Organize:**
- 1,000 songs organized in < 30 seconds
- Zero data loss (all files accounted for)
- Database paths updated correctly
- Preview mode shows changes before executing

✅ **Batch Rename:**
- 1,000 files renamed in < 10 seconds
- Template system works (4+ templates)
- Preview shows before/after
- Rollback works if error occurs

✅ **Tests:**
- All 40-50 new tests passing
- Zero regressions in Phase 4 tests (148/148 still passing)
- End-to-end integration tests

---

## 🚀 FEATURE 5.1: DUPLICATES DETECTION

### **5.1.1 Overview**

**Purpose:** Find and manage duplicate songs in library using multiple detection methods.

**Detection Methods:**
1. **Metadata Comparison** (fast, 85% accuracy)
   - Compare: title, artist, duration (±3s tolerance)
   - Fuzzy string matching (threshold: 0.85)

2. **Audio Fingerprinting** (slow, 99% accuracy)
   - Using acoustid + chromaprint
   - Compares audio signature

3. **File Size** (instant, 70% accuracy)
   - Same song + bitrate = same size
   - Quick pre-filter before deeper methods

---

### **5.1.2 TDD Implementation Plan**

#### **Step 1: RED PHASE - Write Tests First**

**File:** `tests/test_duplicate_detector.py`

```python
class TestDuplicateDetector(unittest.TestCase):
    """Tests for duplicate detection engine"""

    # Structural tests
    def test_01_duplicate_detector_class_exists(self):
        """Test DuplicateDetector class exists"""

    def test_02_detector_has_detection_methods(self):
        """Test detector has 3 detection methods"""

    # Method 1: Metadata comparison
    def test_03_detect_by_metadata_finds_exact_match(self):
        """Test metadata detection finds exact duplicates"""

    def test_04_detect_by_metadata_finds_fuzzy_match(self):
        """Test metadata detection finds similar titles"""

    def test_05_detect_by_metadata_respects_threshold(self):
        """Test threshold controls similarity matching"""

    def test_06_detect_by_metadata_compares_duration(self):
        """Test duration comparison (±3s tolerance)"""

    # Method 2: Audio fingerprinting
    def test_07_detect_by_fingerprint_generates_signature(self):
        """Test audio fingerprint generation"""

    def test_08_detect_by_fingerprint_compares_signatures(self):
        """Test fingerprint comparison accuracy"""

    def test_09_detect_by_fingerprint_handles_missing_file(self):
        """Test graceful handling of missing files"""

    # Method 3: File size
    def test_10_detect_by_filesize_groups_same_size(self):
        """Test grouping by file size"""

    def test_11_detect_by_filesize_is_fast(self):
        """Test filesize detection completes in < 1 second"""

    # Integration
    def test_12_scan_library_returns_duplicate_groups(self):
        """Test full library scan returns groups"""

    def test_13_duplicate_groups_sorted_by_quality(self):
        """Test groups sorted (highest bitrate first)"""

    # Edge cases
    def test_14_empty_library_returns_no_duplicates(self):
        """Test empty library handling"""

    def test_15_single_song_returns_no_duplicates(self):
        """Test single song handling"""
```

**Expected:** 15 tests FAIL (module doesn't exist yet)

---

#### **Step 2: GREEN PHASE - Implement Detection Engine**

**File:** `src/core/duplicate_detector.py`

**Key Classes:**
```python
class DuplicateDetector:
    """
    Detect duplicate songs using multiple methods

    Methods:
    - detect_by_metadata(): Fuzzy string matching
    - detect_by_fingerprint(): Audio signature comparison
    - detect_by_filesize(): Quick pre-filter
    - scan_library(): Full library scan
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self.similarity_threshold = 0.85

    def scan_library(self, method='metadata'):
        """
        Scan entire library for duplicates

        Args:
            method: 'metadata', 'fingerprint', or 'filesize'

        Returns:
            List of duplicate groups:
            [
                {
                    'representative': Song(...),
                    'duplicates': [Song(...), Song(...)],
                    'confidence': 0.95
                },
                ...
            ]
        """
```

**Run Tests:** Expect 15/15 PASS ✅

---

#### **Step 3: RED PHASE - GUI Tests**

**File:** `tests/test_duplicates_tab.py`

```python
class TestDuplicatesTab(unittest.TestCase):
    """Tests for Duplicates Tab GUI"""

    # Structural
    def test_01_duplicates_tab_class_exists(self):
        """Test DuplicatesTab widget exists"""

    def test_02_tab_has_scan_button(self):
        """Test scan button exists"""

    def test_03_tab_has_method_selector(self):
        """Test method selection (metadata/fingerprint/filesize)"""

    def test_04_tab_has_threshold_slider(self):
        """Test similarity threshold slider (0.7-1.0)"""

    def test_05_tab_has_results_tree(self):
        """Test results displayed in tree widget"""

    # Functional
    def test_06_scan_button_triggers_detection(self):
        """Test clicking scan triggers detection"""

    def test_07_results_show_duplicate_groups(self):
        """Test results display grouped duplicates"""

    def test_08_results_show_file_details(self):
        """Test results show bitrate, size, duration"""

    def test_09_user_can_select_files_to_delete(self):
        """Test checkboxes for selection"""

    def test_10_delete_button_removes_selected(self):
        """Test delete button works"""

    def test_11_delete_shows_confirmation_dialog(self):
        """Test confirmation before deletion"""

    def test_12_scan_shows_progress_bar(self):
        """Test progress feedback during scan"""
```

**Expected:** 12 tests FAIL

---

#### **Step 4: GREEN PHASE - Implement GUI**

**File:** `src/gui/tabs/duplicates_tab.py`

**Layout:**
```
+------------------------------------------------------+
| Duplicates Detection                                 |
+------------------------------------------------------+
| Method: [v Metadata] [v Fingerprint] [ Filesize]    |
| Threshold: [====|====] 85%                           |
| [Scan Library]                                       |
+------------------------------------------------------+
| Found 23 duplicate groups (47 files):                |
|                                                      |
| ├─ Group 1: "Bohemian Rhapsody" (2 files)           |
| │  ├─ [✓] 320kbps, 5.9 MB, /path/to/file1.mp3      |
| │  └─ [ ] 128kbps, 2.1 MB, /path/to/file2.mp3      |
| ├─ Group 2: "Stairway to Heaven" (3 files)          |
| │  ├─ [✓] FLAC, 42.1 MB, /path/to/file3.flac       |
| │  ├─ [ ] 320kbps, 11.2 MB, /path/to/file4.mp3     |
| │  └─ [ ] 128kbps, 4.5 MB, /path/to/file5.mp3      |
+------------------------------------------------------+
| Selected: 2 files (7.0 MB)      [Delete Selected]   |
+------------------------------------------------------+
```

**Run Tests:** Expect 12/12 PASS ✅

---

### **5.1.3 Dependencies**

**Required Libraries:**
```bash
pip install acoustid       # Audio fingerprinting
pip install pyacoustid     # Python bindings
pip install chromaprint    # Fingerprint extraction
```

**External Binary:**
- `fpcalc` (chromaprint CLI tool) - auto-installed with pyacoustid

---

### **5.1.4 Acceptance Tests**

**Manual Testing Checklist:**
```
✅ Scan library with metadata method (should complete in < 30s for 1,000 songs)
✅ Scan library with fingerprint method (slower, < 5 min for 1,000 songs)
✅ Detect 10 real duplicates planted in test data
✅ Verify 0 false positives
✅ Delete selected duplicates (files actually removed)
✅ Database updated correctly after deletion
```

---

## 🚀 FEATURE 5.2: AUTO-ORGANIZE LIBRARY

### **5.2.1 Overview**

**Purpose:** Organize MP3 files into clean folder structure automatically.

**Target Structure:**
```
BASE_PATH/
├── Rock/
│   ├── Queen/
│   │   ├── A Night at the Opera (1975)/
│   │   │   ├── 01 - Bohemian Rhapsody.mp3
│   │   │   ├── 02 - You're My Best Friend.mp3
│   │   │   └── cover.jpg
│   │   └── The Game (1980)/
│   │       └── ...
│   └── The Beatles/
│       └── ...
├── Pop/
└── Jazz/
```

**Templates:**
1. `{Genre}/{Artist}/{Album} ({Year})/{Track} - {Title}.mp3`
2. `{Artist}/{Album}/{Track} - {Title}.mp3`
3. `{Genre}/{Artist}/{Track} - {Title}.mp3`
4. Custom template (user-defined)

---

### **5.2.2 TDD Implementation Plan**

#### **Step 1: RED PHASE - Organizer Tests**

**File:** `tests/test_library_organizer.py`

```python
class TestLibraryOrganizer(unittest.TestCase):
    """Tests for library organization engine"""

    # Core functionality
    def test_01_organizer_class_exists(self):
        """Test LibraryOrganizer exists"""

    def test_02_organizer_builds_path_from_template(self):
        """Test path generation from template"""

    def test_03_organizer_sanitizes_folder_names(self):
        """Test invalid characters removed from paths"""

    def test_04_organizer_handles_missing_metadata(self):
        """Test fallback when metadata missing"""

    def test_05_organizer_creates_directories(self):
        """Test directory creation"""

    def test_06_organizer_moves_files(self):
        """Test file moving works"""

    def test_07_organizer_updates_database_paths(self):
        """Test database updated after move"""

    def test_08_organizer_handles_duplicate_names(self):
        """Test conflict resolution (file1.mp3, file2.mp3)"""

    def test_09_organizer_preview_mode(self):
        """Test preview without actual moves"""

    def test_10_organizer_rollback_on_error(self):
        """Test rollback if error during organization"""

    # Performance
    def test_11_organizer_processes_1000_files_fast(self):
        """Test 1,000 files organized in < 30 seconds"""
```

**Expected:** 11 tests FAIL

---

#### **Step 2: GREEN PHASE - Implement Organizer**

**File:** `src/core/library_organizer.py`

**Key Methods:**
```python
class LibraryOrganizer:
    """
    Organize music library into structured folders

    Methods:
    - build_path(): Generate target path from template
    - sanitize_path(): Clean invalid characters
    - preview_organize(): Show what would happen (dry run)
    - organize(): Actually move files
    - rollback(): Undo last organization
    """

    def organize(self, base_path, template, songs, move=True):
        """
        Organize songs into folder structure

        Args:
            base_path: Root directory (e.g., D:\MUSICA_ORGANIZADA)
            template: Path template string
            songs: List of Song objects
            move: True = move, False = copy

        Returns:
            {
                'success': 150,
                'failed': 0,
                'errors': []
            }
        """
```

**Run Tests:** Expect 11/11 PASS ✅

---

#### **Step 3: RED PHASE - GUI Tests**

**File:** `tests/test_organize_tab.py`

```python
class TestOrganizeTab(unittest.TestCase):
    """Tests for Organize Tab GUI"""

    def test_01_organize_tab_exists(self):
        """Test OrganizeTab widget exists"""

    def test_02_tab_has_folder_selector(self):
        """Test target folder selection"""

    def test_03_tab_has_template_dropdown(self):
        """Test template selection dropdown"""

    def test_04_tab_has_preview_button(self):
        """Test preview button exists"""

    def test_05_preview_shows_before_after(self):
        """Test preview displays changes"""

    def test_06_tab_has_organize_button(self):
        """Test organize button exists"""

    def test_07_organize_button_triggers_organization(self):
        """Test clicking organize starts process"""

    def test_08_progress_bar_shows_during_organization(self):
        """Test progress feedback"""

    def test_09_move_vs_copy_option(self):
        """Test move/copy radio buttons"""

    def test_10_confirmation_dialog_before_organize(self):
        """Test confirmation prompt"""
```

**Expected:** 10 tests FAIL

---

#### **Step 4: GREEN PHASE - Implement GUI**

**File:** `src/gui/tabs/organize_tab.py`

**Run Tests:** Expect 10/10 PASS ✅

---

## 🚀 FEATURE 5.3: BATCH RENAME FILES

### **5.3.1 Overview**

**Purpose:** Rename multiple files using configurable templates.

**Templates:**
```
1. {track} - {title}.mp3
   → 01 - Bohemian Rhapsody.mp3

2. {artist} - {title}.mp3
   → Queen - Bohemian Rhapsody.mp3

3. {artist} - {album} - {track} - {title}.mp3
   → Queen - A Night at the Opera - 01 - Bohemian Rhapsody.mp3

4. Custom: [user input]
```

---

### **5.3.2 TDD Implementation Plan**

#### **Step 1: RED PHASE - Renamer Tests**

**File:** `tests/test_batch_renamer.py`

```python
class TestBatchRenamer(unittest.TestCase):
    """Tests for batch file renaming"""

    def test_01_renamer_class_exists(self):
        """Test BatchRenamer exists"""

    def test_02_renamer_formats_filename(self):
        """Test filename generation from template"""

    def test_03_renamer_sanitizes_filenames(self):
        """Test invalid characters removed"""

    def test_04_renamer_preserves_extension(self):
        """Test file extension preserved"""

    def test_05_renamer_preview_mode(self):
        """Test preview without actual rename"""

    def test_06_renamer_renames_files(self):
        """Test actual file renaming"""

    def test_07_renamer_updates_database(self):
        """Test database paths updated"""

    def test_08_renamer_handles_conflicts(self):
        """Test duplicate name handling"""

    def test_09_renamer_rollback(self):
        """Test undo functionality"""

    def test_10_renamer_processes_1000_files_fast(self):
        """Test 1,000 files renamed in < 10 seconds"""
```

**Expected:** 10 tests FAIL

---

#### **Step 2: GREEN PHASE - Implement Renamer**

**File:** `src/core/batch_renamer.py`

**Run Tests:** Expect 10/10 PASS ✅

---

#### **Step 3: RED PHASE - GUI Tests**

**File:** `tests/test_rename_tab.py` (8 tests)

---

#### **Step 4: GREEN PHASE - Implement GUI**

**File:** `src/gui/tabs/rename_tab.py`

**Run Tests:** Expect 8/8 PASS ✅

---

## 📅 TIMELINE & MILESTONES

| Day | Feature | Tasks | Tests |
|-----|---------|-------|-------|
| **Day 1-2** | 5.1 Engine | Duplicate detector core | 15 tests |
| **Day 3-4** | 5.1 GUI | Duplicates tab widget | 12 tests |
| **Day 5** | 5.1 Integration | End-to-end testing | 3 tests |
| **Day 6-7** | 5.2 Engine | Library organizer core | 11 tests |
| **Day 8** | 5.2 GUI | Organize tab widget | 10 tests |
| **Day 9** | 5.3 Engine | Batch renamer core | 10 tests |
| **Day 10** | 5.3 GUI | Rename tab widget | 8 tests |
| **Day 11** | Integration | Full Phase 5 testing | 5 tests |
| **Day 12** | Documentation | Update docs, commit | - |

**Total Tests:** ~72 tests (conservative estimate)

---

## ✅ VALIDATION CHECKLIST

**Before considering Phase 5 COMPLETE:**

- [ ] All 72+ new tests passing
- [ ] Zero regressions (148 Phase 4 tests still passing)
- [ ] Duplicates detection working (95%+ accuracy)
- [ ] Library organization working (1,000 songs < 30s)
- [ ] Batch rename working (1,000 files < 10s)
- [ ] All GUIs functional and responsive
- [ ] Documentation updated (README, CLAUDE, PROJECT_ID, current_phase)
- [ ] Git commits atomic and descriptive
- [ ] Manual testing complete (acceptance tests)
- [ ] Ricardo approval ✅

---

## 🎯 NEXT STEPS

**When Ricardo approves this plan:**

1. **Update TODO list** with Phase 5 breakdown
2. **Begin Day 1:** Feature 5.1 - Duplicate Detector (TDD Red Phase)
3. **Create test file:** `tests/test_duplicate_detector.py`
4. **Run tests:** Verify RED PHASE (all tests fail as expected)
5. **Implement engine:** `src/core/duplicate_detector.py`
6. **Run tests:** Verify GREEN PHASE (all tests pass)

---

**Created by:** Ricardo + NEXUS@CLI
**Methodology:** NEXUS 4-Phase Workflow + TDD
**Status:** SOURCE OF TRUTH for Phase 5 implementation
**Last Updated:** November 13, 2025
