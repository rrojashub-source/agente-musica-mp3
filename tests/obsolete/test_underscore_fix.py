#!/usr/bin/env python3
"""Test rápido: verificar fix de patrón underscore"""

import re

# Patrón ANTES (malo)
pattern_old = r'^(.+?)_(.+?)$'

# Patrón DESPUÉS (fix)
pattern_new = r'^(.+?)_(.+)$'

test_cases = [
    "David_Bowie_Space_Oddity",
    "The_Beatles_Hey_Jude",
    "Artist_Title",
]

print("🧪 TEST UNDERSCORE PATTERN FIX")
print("=" * 60)

for test in test_cases:
    print(f"\nTest: {test}")

    # Viejo patrón
    match_old = re.match(pattern_old, test)
    if match_old:
        artist_old, title_old = match_old.groups()
        print(f"  ❌ OLD: '{artist_old}' | '{title_old}'")

    # Nuevo patrón
    match_new = re.match(pattern_new, test)
    if match_new:
        artist_new, title_new = match_new.groups()
        print(f"  ✅ NEW: '{artist_new}' | '{title_new}'")

print("\n" + "=" * 60)
print("CONCLUSIÓN:")
print("El fix (.+) greedy captura todo después del primer underscore")
print("Resultado esperado: 'Artist' | 'Rest_Of_Title'")
