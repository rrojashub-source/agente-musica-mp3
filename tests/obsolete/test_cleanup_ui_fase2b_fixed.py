#!/usr/bin/env python3
"""
Test visual: Cleanup Assistant Tab con Fase 2B (bulk actions)
"""
import sys
from PySide6.QtWidgets import QApplication
from cleanup_assistant_tab import CleanupAssistantTab, MetadataIssue

print("🧪 TEST: Cleanup Assistant UI - Fase 2B\n")

app = QApplication(sys.argv)

# Crear tab
tab = CleanupAssistantTab()

# Agregar algunos issues de prueba para verificar UI
test_issues = [
    MetadataIssue(
        file_path="/test/Bruno_Mars_Just_The_Way_You_Are.mp3",
        issue_type="filename_parsing",
        current_value="Bruno_Mars_Just_The_Way_You_Are",
        pattern_matched="artist_title_underscore",
        confidence=0.85,
        suggested_artist="Bruno Mars",
        suggested_title="Just The Way You Are",
        suggested_album="Doo-Wops & Hooligans",
        suggested_year=2010,
        suggested_genre="Pop"
    ),
    MetadataIssue(
        file_path="/test/David_Bowie_Space_Oddity.mp3",
        issue_type="missing_tags",
        current_value="",
        pattern_matched="artist_title_underscore",
        confidence=0.90,
        suggested_artist="David Bowie",
        suggested_title="Space Oddity",
        suggested_album="Space Oddity",
        suggested_year=1969,
        suggested_genre="Rock"
    ),
    MetadataIssue(
        file_path="/test/Queen-Bohemian_Rhapsody.mp3",
        issue_type="filename_parsing",
        current_value="Queen-Bohemian_Rhapsody",
        pattern_matched="artist_title_dash",
        confidence=0.95,
        suggested_artist="Queen",
        suggested_title="Bohemian Rhapsody",
        suggested_album="A Night at the Opera",
        suggested_year=1975,
        suggested_genre="Rock"
    )
]

print("📋 Agregando 3 issues de prueba...")
for issue in test_issues:
    tab.add_issue(issue)

print("✅ Issues agregados\n")
print("🔍 VERIFICAR VISUALMENTE:")
print("   1. ✓ Tabla tiene 11 columnas (checkbox + dropdown + 9 datos)")
print("   2. ✓ Checkboxes en columna 0 (sin check)")
print("   3. ✓ Dropdowns en columna 1 (default: 🏷️ Solo Tags)")
print("   4. ✓ Botones bulk arriba: ✓ Todos, ☐ Ninguno, ⇄ Invertir")
print("   5. ✓ Botones acción: 🏷️ Solo Tags, ✏️ Tags + Renombrar, 📁 Tags + Organizar")
print("   6. ✓ Botón GRANDE: 🚀 Aplicar Correcciones (azul)\n")

tab.show()
print("🎨 Ventana mostrada - cierra manualmente cuando termines de verificar\n")

sys.exit(app.exec())
