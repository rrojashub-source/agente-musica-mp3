# 📥 Library Import Feature - Complete Implementation Plan

**Feature:** Import existing MP3 library into database with GUI
**Priority:** CRITICAL (blocking all other features)
**Estimated Time:** 4-6 hours
**Status:** Planning complete, ready for implementation

---

## 🎯 Objective

Enable user to import existing MP3 collection from C:\Users\ricar\Music\ into SQLite database so that:
- LibraryTab can display all songs
- Audio playback works
- All Phase 7 features become functional

**Current Problem:**
- Application launches successfully ✅
- Database exists but is EMPTY ❌
- LibraryTab calls `db.get_all_songs()` but method doesn't exist ❌
- User has ~100+ MP3s in C:\Users\ricar\Music\ that need importing

---

## 📐 Architecture Overview

```
User selects folder → LibraryImportWorker (QThread)
                              ↓
                       Scan recursively for .mp3
                              ↓
                       Read metadata (mutagen)
                              ↓
                    Validate & extract info
                              ↓
                    DatabaseManager.add_song()
                              ↓
                       Update progress bar
                              ↓
                       Emit completion signal
                              ↓
                    ImportTab shows results
```

---

## 🗂️ Components to Implement

### 1. **DatabaseManager Extensions** (src/database/manager.py)

**Missing Methods:**
```python
def get_all_songs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all songs from library"""

def add_song(self, song_data: Dict[str, Any]) -> Optional[int]:
    """Add new song to library, return song ID"""

def get_song_by_id(self, song_id: int) -> Optional[Dict[str, Any]]:
    """Get song by ID"""

def update_song(self, song_id: int, updates: Dict[str, Any]) -> bool:
    """Update song metadata"""

def song_exists(self, file_path: str) -> bool:
    """Check if file path already imported"""
```

**Fields to Store (from ID3 tags + file info):**
- title (TIT2)
- artist (TPE1)
- album (TALB)
- year (TDRC)
- genre (TCON)
- duration (audio.info.length)
- bitrate (audio.info.bitrate)
- sample_rate (audio.info.sample_rate)
- file_path (absolute path)
- file_size (os.path.getsize)
- added_date (CURRENT_TIMESTAMP)

---

### 2. **LibraryImportWorker** (src/workers/library_import_worker.py)

**QThread Background Worker:**
```python
class LibraryImportWorker(QThread):
    # Signals
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    song_imported = pyqtSignal(dict)  # Emits each imported song
    finished = pyqtSignal(dict)  # {success: int, failed: int, errors: []}
    error = pyqtSignal(str)  # Fatal error

    def __init__(self, db_manager, folder_path, recursive=True):
        ...

    def run(self):
        # 1. Scan folder recursively for .mp3
        # 2. For each MP3:
        #    - Check if already imported (skip duplicates)
        #    - Read metadata with mutagen
        #    - Validate (skip corrupted files)
        #    - Extract song_data dict
        #    - db.add_song(song_data)
        #    - Emit progress signal
        # 3. Emit finished signal with summary
```

**Metadata Extraction:**
```python
def extract_metadata(file_path: str) -> Optional[Dict]:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3

    try:
        audio = MP3(file_path)
        tags = ID3(file_path)

        song_data = {
            'title': str(tags.get('TIT2', 'Unknown')),
            'artist': str(tags.get('TPE1', 'Unknown Artist')),
            'album': str(tags.get('TALB', 'Unknown Album')),
            'year': int(str(tags.get('TDRC', 0))[:4]) if tags.get('TDRC') else None,
            'genre': str(tags.get('TCON', '')),
            'duration': int(audio.info.length),
            'bitrate': audio.info.bitrate,
            'sample_rate': audio.info.sample_rate,
            'file_path': file_path,
            'file_size': os.path.getsize(file_path)
        }

        return song_data

    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return None
```

---

### 3. **ImportTab GUI** (src/gui/tabs/import_tab.py)

**Layout:**
```
+-----------------------------------------------------+
| 📥 Import Music Library                             |
+-----------------------------------------------------+
| Select Folder: [C:\Users\ricar\Music\] [Browse...]  |
| [x] Scan subfolders recursively                     |
+-----------------------------------------------------+
| [Import Library] [Cancel]                           |
+-----------------------------------------------------+
| Progress: ████████░░░░░░░░ 50%                      |
| Status: Importing... (50/100 files)                 |
+-----------------------------------------------------+
| Results:                                            |
| ✅ Imported: 95 songs                               |
| ⚠️  Skipped: 3 duplicates                           |
| ❌ Failed: 2 corrupted files                        |
+-----------------------------------------------------+
```

**Features:**
- QFileDialog for folder selection
- QCheckBox for recursive scan
- QPushButton to start/cancel
- QProgressBar with percentage
- QLabel for status messages
- QTextEdit for results summary
- Disable controls during import
- Re-enable on completion

---

## 🧪 TDD Implementation Plan

### Phase 1: DatabaseManager CRUD (RED → GREEN → REFACTOR)

**File:** `tests/test_database_manager.py`

**Test Cases:**
```python
def test_add_song_returns_song_id():
    """Test adding song returns valid ID"""

def test_get_all_songs_empty_library():
    """Test get_all_songs on empty DB"""

def test_get_all_songs_returns_all():
    """Test get_all_songs returns all records"""

def test_get_song_by_id_exists():
    """Test get song by valid ID"""

def test_get_song_by_id_not_exists():
    """Test get song by invalid ID returns None"""

def test_song_exists_by_file_path():
    """Test duplicate detection by file_path"""

def test_update_song_metadata():
    """Test updating song fields"""

def test_add_song_with_missing_fields():
    """Test add with only title + file_path (minimum)"""

def test_add_song_duplicate_file_path_fails():
    """Test UNIQUE constraint on file_path"""
```

**Estimated:** 12 tests, ~1 hour

---

### Phase 2: LibraryImportWorker (RED → GREEN → REFACTOR)

**File:** `tests/test_library_import_worker.py`

**Test Cases:**
```python
def test_scan_folder_finds_mp3s():
    """Test recursive scan finds all .mp3 files"""

def test_extract_metadata_valid_mp3():
    """Test metadata extraction from valid MP3"""

def test_extract_metadata_corrupted_mp3():
    """Test handles corrupted files gracefully"""

def test_import_emits_progress_signals():
    """Test progress signals during import"""

def test_import_skips_duplicates():
    """Test doesn't re-import existing file_paths"""

def test_import_handles_missing_tags():
    """Test defaults for missing ID3 tags"""

def test_import_non_recursive_mode():
    """Test non-recursive scan (only top folder)"""

def test_import_finishes_with_summary():
    """Test finished signal contains success/failed counts"""
```

**Test Data:**
- Create temp folder with sample MP3s
- Use real MP3 from Ricardo's library (copy to temp)
- Create corrupted file for error handling test

**Estimated:** 10 tests, ~2 hours

---

### Phase 3: ImportTab GUI (RED → GREEN → REFACTOR)

**File:** `tests/test_import_tab.py`

**Test Cases:**
```python
def test_import_tab_initializes():
    """Test ImportTab creates UI elements"""

def test_browse_button_opens_dialog():
    """Test Browse button triggers QFileDialog"""

def test_import_button_disabled_no_folder():
    """Test Import disabled when no folder selected"""

def test_import_starts_worker_thread():
    """Test Import starts LibraryImportWorker"""

def test_progress_bar_updates():
    """Test progress bar responds to worker signals"""

def test_cancel_button_stops_worker():
    """Test Cancel terminates worker thread"""

def test_results_summary_displayed():
    """Test results shown after completion"""

def test_import_button_re_enabled_after_finish():
    """Test UI controls re-enabled after import"""
```

**Estimated:** 8 tests, ~1.5 hours

---

## 📋 Implementation Steps (TDD Workflow)

### Step 1: DatabaseManager CRUD (1 hour)
1. Write all 12 tests in test_database_manager.py
2. Run tests → ALL FAIL (RED phase)
3. Implement methods in src/database/manager.py
4. Run tests → ALL PASS (GREEN phase)
5. Refactor for performance/clarity
6. Commit: "feat(database): Add CRUD methods for songs table"

### Step 2: LibraryImportWorker (2 hours)
1. Write all 10 tests in test_library_import_worker.py
2. Create temp MP3s for testing
3. Run tests → ALL FAIL (RED phase)
4. Implement LibraryImportWorker in src/workers/library_import_worker.py
5. Run tests → ALL PASS (GREEN phase)
6. Refactor for robustness
7. Commit: "feat(workers): Add LibraryImportWorker with metadata extraction"

### Step 3: ImportTab GUI (1.5 hours)
1. Write all 8 tests in test_import_tab.py
2. Run tests → ALL FAIL (RED phase)
3. Implement ImportTab in src/gui/tabs/import_tab.py
4. Run tests → ALL PASS (GREEN phase)
5. Refactor UI polish
6. Commit: "feat(gui): Add ImportTab for library import"

### Step 4: Integration (30 min)
1. Add ImportTab to main.py tabs
2. Test with real user library (C:\Users\ricar\Music\)
3. Verify LibraryTab displays imported songs
4. Test playback with imported songs
5. Commit: "feat(integration): Add Import tab to main application"

### Step 5: User Testing (30 min)
1. Guide Ricardo to:
   - Click Import tab
   - Select C:\Users\ricar\Music\
   - Click Import Library
   - Wait for completion
   - Switch to Library tab
   - Verify songs displayed
   - Double-click to play

---

## 🎨 UI/UX Considerations

**Folder Selection:**
- Default path: `C:\Users\ricar\Music\` (detected automatically)
- Remember last used folder (QSettings)

**Progress Feedback:**
- Show filename currently processing
- Show count: "Importing... (50/100 files)"
- Percentage bar updates every file
- ETA calculation (optional)

**Error Handling:**
- Corrupted files: Skip + log warning
- Permission denied: Skip + log error
- Missing tags: Use defaults ("Unknown Artist", etc.)
- Duplicate file_path: Skip silently
- Fatal errors: Show QMessageBox, cancel import

**Results Summary:**
```
Import Complete!

✅ Imported: 95 songs
⚠️  Skipped: 3 duplicates
❌ Failed: 2 files

Files with errors:
- corrupted.mp3: Invalid MP3 header
- protected.mp3: Permission denied
```

---

## 🔧 Dependencies

**Already Installed:**
- mutagen (ID3 tag reading)
- PyQt6 (GUI framework)
- sqlite3 (built-in)

**No Additional Dependencies Needed** ✅

---

## 📊 Success Criteria

**After completion:**
1. ✅ All 30 tests passing (12 + 10 + 8)
2. ✅ DatabaseManager has complete CRUD API
3. ✅ LibraryImportWorker scans + imports recursively
4. ✅ ImportTab shows progress + results
5. ✅ Ricardo's library imported successfully (~100+ songs)
6. ✅ LibraryTab displays all songs
7. ✅ Playback works with imported songs
8. ✅ No crashes, graceful error handling

---

## 🚀 Post-Implementation

**Next Steps:**
1. Phase 8A features (Equalizer, Crossfade, Lyrics, ReplayGain)
2. Duplicate detection (use DuplicatesTab)
3. Auto-organize (use OrganizeTab)
4. Metadata editing (use RenameTab)

**Documentation:**
- Update TRACKING.md with session log
- Update README.md with Import feature
- Update QUICK_START.md with import instructions

---

## 📝 Notes

**Why this is CRITICAL:**
- Without import, app is useless (no songs to play)
- Blocks all Phase 7 features testing
- Blocks all Phase 8 features
- User can't test anything meaningful

**Why GUI import (not script):**
- User-friendly (no terminal needed)
- Progress feedback (long operation ~5 min for 100 songs)
- Integrated with main app (no separate tools)
- Error handling visible to user
- Repeatable (can re-scan folders later)

**Performance Considerations:**
- 100 songs × 3s each = ~5 minutes total
- Use QThread to avoid UI freeze
- Update progress every file (not every 10%)
- FTS5 index updated automatically (triggers in migration)

---

**Created:** November 13, 2025
**Plan Duration:** 4-6 hours (with TDD)
**Fast Track:** 1-2 hours (skip some tests, implement minimum viable)

**Recommended:** Full TDD approach for robustness
