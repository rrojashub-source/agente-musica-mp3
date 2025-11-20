"""
Quick test to verify fpcalc detection
"""
from src.utils.fpcalc_checker import FpcalcChecker

checker = FpcalcChecker()

if checker.is_available():
    print('✅ fpcalc DETECTED')
    print(f'Location: {checker.fpcalc_path}')
    print(f'Version: {checker.version}')
else:
    print('❌ fpcalc NOT DETECTED')
    print(checker.get_install_instructions())
