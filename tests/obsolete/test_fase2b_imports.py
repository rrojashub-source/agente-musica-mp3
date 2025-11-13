#!/usr/bin/env python3
"""
Test rápido: Verificar que todos los módulos Fase 2B cargan sin errores
"""
import sys
print("🧪 Testing Fase 2B - Import Verification\n")

# Test 1: FolderManager
print("1️⃣  Testing folder_manager.py...")
try:
    from folder_manager import FolderManager
    print("   ✅ FolderManager imported successfully")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

# Test 2: TagQualityAnalyzer
print("2️⃣  Testing tag_quality_analyzer.py...")
try:
    from tag_quality_analyzer import TagQualityAnalyzer
    print("   ✅ TagQualityAnalyzer imported successfully")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

# Test 3: DownloadAnalysisDialog
print("3️⃣  Testing download_analysis_dialog.py...")
try:
    from download_analysis_dialog import DownloadAnalysisDialog
    print("   ✅ DownloadAnalysisDialog imported successfully")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

# Test 4: CorrectionEngine
print("4️⃣  Testing correction_engine.py...")
try:
    from correction_engine import CorrectionEngine, CorrectionAction
    print("   ✅ CorrectionEngine + CorrectionAction imported successfully")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

# Test 5: CleanupAssistantTab (verificar que los nuevos imports funcionan)
print("5️⃣  Testing cleanup_assistant_tab.py (updated)...")
try:
    from cleanup_assistant_tab import CleanupAssistantTab
    print("   ✅ CleanupAssistantTab (Fase 2B) imported successfully")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL IMPORTS SUCCESSFUL - Fase 2B modules are ready!")
print("="*60)
