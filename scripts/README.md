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
