#!/bin/bash
# ============================================
# NEXUS Music Manager - Security Scan Script
# ============================================
# Runs multiple security scanners:
# - pip-audit: Checks for vulnerable dependencies
# - safety: Checks packages against safety database
# - bandit: Static code analysis for security issues
# ============================================

echo "=========================================="
echo " NEXUS Music Manager - Security Scan"
echo "=========================================="
echo ""

# Check if pip-audit is installed
if ! command -v pip-audit &> /dev/null; then
    echo "Installing pip-audit..."
    pip install pip-audit
fi

# Check if safety is installed
if ! command -v safety &> /dev/null; then
    echo "Installing safety..."
    pip install safety
fi

# Check if bandit is installed
if ! command -v bandit &> /dev/null; then
    echo "Installing bandit..."
    pip install bandit
fi

echo ""
echo "=========================================="
echo " 1. pip-audit - Dependency Vulnerabilities"
echo "=========================================="
pip-audit --progress-spinner off
AUDIT_EXIT=$?

echo ""
echo "=========================================="
echo " 2. safety - Safety Database Check"
echo "=========================================="
safety check --full-report 2>/dev/null || safety check
SAFETY_EXIT=$?

echo ""
echo "=========================================="
echo " 3. bandit - Static Code Analysis"
echo "=========================================="
bandit -r src/ -f txt -ll
BANDIT_EXIT=$?

echo ""
echo "=========================================="
echo " Security Scan Complete"
echo "=========================================="
echo "Results:"
echo "  pip-audit: $([ $AUDIT_EXIT -eq 0 ] && echo 'PASS' || echo 'ISSUES FOUND')"
echo "  safety:    $([ $SAFETY_EXIT -eq 0 ] && echo 'PASS' || echo 'ISSUES FOUND')"
echo "  bandit:    $([ $BANDIT_EXIT -eq 0 ] && echo 'PASS' || echo 'ISSUES FOUND')"
echo "=========================================="

# Exit with error if any scanner found issues
if [ $AUDIT_EXIT -ne 0 ] || [ $SAFETY_EXIT -ne 0 ] || [ $BANDIT_EXIT -ne 0 ]; then
    exit 1
fi

exit 0
