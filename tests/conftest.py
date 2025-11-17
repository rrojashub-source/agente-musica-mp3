"""
Pytest configuration for AGENTE_MUSICA_MP3 tests
Adds project root to Python path so imports work correctly
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Also add src/ directory for imports without src. prefix (matching main.py behavior)
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))
