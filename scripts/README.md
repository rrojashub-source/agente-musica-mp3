# Database Management Scripts

**Location:** `/scripts/`

## 🔄 fresh_start_database.py

**Purpose:** Clean slate for music library database - wipe and re-import with path normalization

### What It Does

1. **Backup** - Creates timestamped backup of current database
2. **Wipe** - Deletes all songs from database (resets IDs)
3. **Re-import** - Scans music folder recursively with path normalization enabled
4. **Verify** - Checks for duplicates and validates paths

### When to Use

- ✅ After fixing duplicate import bug (normalize existing data)
- ✅ When database has corrupt/incorrect paths
- ✅ When you want clean IDs (1, 2, 3... instead of gaps)
- ✅ After major library reorganization

### How to Use

**From Windows Terminal (in project root):**

```bash
python scripts/fresh_start_database.py
```

**From WSL/Linux:**

```bash
python3 scripts/fresh_start_database.py
```

### Interactive Prompts

1. **Confirmation:** Script will ask "Continue? (yes/no)"
2. **Music Folder:** Enter path or press Enter for default (`C:\Users\ricar\Music`)

### What Happens

```
🔄 FRESH START DATABASE SCRIPT
==============================

This script will:
  1. Backup current database
  2. Wipe all songs (DELETE)
  3. Re-import from music folder with normalized paths
  4. Verify results (no duplicates, correct paths)

⚠️  WARNING: This will DELETE all songs from database!
   (Backup will be created first)

Continue? (yes/no): yes

Enter music folder path [C:\Users\ricar\Music]:

Step 1: Backing up database...
✅ Backup created: music_library_backup_20251118_143022.db

Step 2: Wiping database...
Songs before wipe: 941
Songs after wipe: 0
✅ Database wiped successfully

Step 3: Re-importing library (this may take several minutes)...
Progress: 0% - Starting import...
Progress: 10% - Importing... (50/500 files)
Progress: 20% - Importing... (100/500 files)
...
Progress: 100% - Import complete

✅ FRESH IMPORT COMPLETE!
   Imported: 310 songs
   Skipped: 0 duplicates
   Failed: 0 errors

📊 Total songs in library: 310

🔍 Verifying results...
✅ No duplicate title+artist combinations found

📁 Sample paths (should be normalized):
   C:\Users\ricar\Music\Chanel\Clavaito.mp3
   C:\Users\ricar\Music\Taylor Swift\Cruel Summer.mp3
   ...

==============================
✅ FRESH START COMPLETE!
==============================

Backup saved at: music_library_backup_20251118_143022.db
You can now launch the GUI and use the clean library.
```

### Safety Features

- ✅ **Automatic backup** before any changes
- ✅ **Confirmation prompt** before wiping
- ✅ **Progress logging** every 10%
- ✅ **Error handling** with graceful failure
- ✅ **Verification** after import

### Expected Results

**Before (with duplicates):**
- 941 songs total
- IDs 630-941 are duplicates of 1-310
- Paths in mixed formats: `C:\path\file.mp3` vs `C:/path/file.mp3`

**After (clean slate):**
- 310 songs total (zero duplicates)
- IDs: 1, 2, 3, ... 310 (sequential, no gaps)
- All paths normalized: `C:\Users\ricar\Music\Artist\Song.mp3`

### Troubleshooting

**Problem:** "Database locked" error
- **Solution:** Close GUI application before running script

**Problem:** "No MP3 files found"
- **Solution:** Check music folder path is correct

**Problem:** Script hangs during import
- **Solution:** Check logs for errors, press Ctrl+C to abort

### Recovery

If something goes wrong, restore from backup:

```bash
# Copy backup back to main database
cp music_library_backup_YYYYMMDD_HHMMSS.db music_library.db
```

---

**Created:** November 18, 2025
**Author:** NEXUS + Ricardo
**Related Bug:** Import allowed duplicates (IDs 630-941)

---

## 🔄 convert_paths_wsl_to_windows.py

**Purpose:** Convert WSL paths to Windows paths in database (reference implementation)

### What It Does

1. **Analyze** - Counts WSL paths vs Windows paths in database
2. **Preview** - Shows examples of conversion
3. **Convert** - Attempts to UPDATE WSL paths to Windows format
4. **Verify** - Checks conversion results

### When to Use

- ❌ **NOT recommended:** This script was created as proof-of-concept but has issues
- ⚠️ **Problem:** If Windows paths already exist, causes UNIQUE constraint violations
- ✅ **Better alternative:** Use `delete_wsl_paths.py` instead

### How It Works

**Conversion logic:**
```python
# /mnt/c/Users/ricar/Music/... → C:\Users\ricar\Music\...
# /mnt/d/... → D:\...

def convert_wsl_to_windows(wsl_path: str) -> str:
    if wsl_path.startswith('/mnt/'):
        parts = wsl_path.split('/')
        drive = parts[2].upper()  # 'c' -> 'C'
        rest = '/'.join(parts[3:])
        return f"{drive}:\\{rest.replace('/', '\\')}"
    return wsl_path
```

### Notes

- Created: November 18, 2025
- Status: **Educational reference only** (use delete_wsl_paths.py instead)
- Issue: Fails when target Windows paths already exist in database

---

## 🗑️ delete_wsl_paths.py

**Purpose:** Delete songs with WSL paths from database (RECOMMENDED SOLUTION)

### What It Does

1. **Analyze** - Counts WSL paths vs Windows paths
2. **Preview** - Shows examples of songs to delete
3. **Delete** - Removes all songs with WSL paths (`/mnt/...`)
4. **Verify** - Confirms zero WSL paths remain

### When to Use

- ✅ After fresh_start_database.py ran from WSL
- ✅ When database has duplicate songs (WSL + Windows paths)
- ✅ When seeing "File not found" errors but files exist

### How to Use

**From WSL:**

```bash
python3 scripts/delete_wsl_paths.py
```

**Interactive prompts:**
1. Shows count of WSL vs Windows paths
2. Shows 5 example songs to delete
3. Asks confirmation: "Delete all songs with WSL paths? (yes/no)"
4. Deletes and verifies

### What Happens

```
============================================================
🗑️  DELETE WSL PATHS FROM DATABASE
============================================================

Total songs: 623

WSL paths (will delete): 311
Windows paths (will keep): 312

Examples of songs to DELETE:
  [310] Zacarías Ferreira - Asesina
      Path: /mnt/c/Users/ricar/Music/NEXUS_Organized/...

Delete all songs with WSL paths? (yes/no): yes

Deleting songs with WSL paths...
  Deleted 50/311 songs...
  Deleted 100/311 songs...
  ...
  Deleted 311/311 songs...

✅ Deleted 311 songs with WSL paths!

Verification:
  Total songs: 312
  WSL paths remaining: 0
  Windows paths: 312

============================================================
✅ ALL WSL PATHS DELETED!
============================================================

Next steps:
1. Restart the application
2. Library should work with Windows paths only
```

### Safety Features

- ✅ **Shows preview** before deleting (first 5 songs)
- ✅ **Confirmation prompt** required
- ✅ **Progress logging** every 50 songs
- ✅ **Final verification** of results

### Expected Results

**Before (with duplicates):**
- 623 songs total
- 311 WSL paths (`/mnt/c/...`)
- 312 Windows paths (`C:\...`)
- "File not found" errors when playing

**After (clean):**
- 312 songs total
- 0 WSL paths
- 312 Windows paths only
- No more "File not found" errors

### Troubleshooting

**Problem:** "Database locked" error
- **Solution:** Close GUI application before running script

**Problem:** "Permission denied"
- **Solution:** Run from WSL with proper permissions

**Problem:** Script deleted wrong songs
- **Solution:** Restore from backup: `music_library_backup_*.db`

---

**Last Updated:** November 18, 2025 (Added WSL path conversion/deletion scripts)
**Author:** NEXUS + Ricardo
