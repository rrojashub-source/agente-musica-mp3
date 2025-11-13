#!/usr/bin/env python3
"""
Cleanup Assistant Tab - FASE 2A: Auto-Fetch Metadata
Detecta problemas de metadata Y busca información faltante online
Usa MusicBrainz API (gratis, sin API key)

Project: AGENTE_MUSICA_MP3_001
Feature: Pre-import metadata cleanup + auto-fetch
"""

import sys
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
        QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
        QProgressDialog, QMessageBox, QGroupBox, QTextEdit,
        QCheckBox, QComboBox  # FASE 2B: checkbox + dropdown
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont, QColor
except ImportError:
    print("ERROR: PyQt6 not installed")
    exit(1)

try:
    from mutagen import File as MutagenFile
except ImportError:
    print("ERROR: mutagen not installed")
    exit(1)

try:
    import musicbrainzngs
except ImportError:
    print("WARNING: musicbrainzngs not installed - auto-fetch disabled")
    print("   Install with: pip install musicbrainzngs")
    musicbrainzngs = None


@dataclass
class MetadataIssue:
    """Representa un problema de metadata detectado + info online"""
    file_path: str
    issue_type: str  # 'artist_title_merged', 'missing_artist', etc
    current_value: str
    suggested_artist: Optional[str]
    suggested_title: Optional[str]
    confidence: float  # 0.0-1.0
    pattern_matched: str
    # Metadata completa desde MusicBrainz (Fase 2A)
    suggested_album: Optional[str] = None
    suggested_year: Optional[int] = None
    suggested_genre: Optional[str] = None
    musicbrainz_id: Optional[str] = None
    online_confidence: float = 0.0  # Confianza de búsqueda online


class PatternDetector:
    """
    Detecta patrones robustos en nombres de archivos y tags
    Soporta: dash, underscore, slash, parenthesis, track numbers
    """

    # Patrones ordenados por prioridad (más específico primero)
    PATTERNS = [
        # === PATRONES CON NÚMEROS DE TRACK ===

        # "01 - Artist - Title.mp3"
        (r'^(\d{1,3})\s*[-_.]\s*(.+?)\s*[-_.]\s*(.+?)$', 'track_artist_title_dash'),

        # "Track 01 - Artist - Title.mp3"
        (r'^[Tt]rack\s+(\d{1,3})\s*[-_.]\s*(.+?)\s*[-_.]\s*(.+?)$', 'track_word_artist_title'),

        # "01. Artist - Title.mp3"
        (r'^(\d{1,3})\.\s*(.+?)\s*-\s*(.+?)$', 'track_dot_artist_title'),

        # "Artist - 01 - Title.mp3" (número en medio)
        (r'^(.+?)\s*-\s*\d{1,3}\s*-\s*(.+?)$', 'artist_track_title'),

        # === PATRONES CON AÑO ===

        # "Artist - Title (2020).mp3"
        (r'^(.+?)\s*-\s*(.+?)\s*\((\d{4})\)$', 'artist_title_year'),

        # "Artist - Title [2020].mp3"
        (r'^(.+?)\s*-\s*(.+?)\s*\[(\d{4})\]$', 'artist_title_year_bracket'),

        # === PATRONES CON FEATURING ===

        # "Artist feat. Artist2 - Title.mp3"
        (r'^(.+?)\s+(?:feat\.|ft\.|featuring)\s+.+?\s*-\s*(.+?)$', 'artist_feat_title'),

        # "Artist & Artist2 - Title.mp3"
        (r'^(.+?)\s+&\s+.+?\s*-\s*(.+?)$', 'artist_and_title'),

        # === PATRONES CON REMIX/VERSION ===

        # "Artist - Title (Remix).mp3"
        (r'^(.+?)\s*-\s*(.+?)\s*\([Rr]emix\)$', 'artist_title_remix'),

        # "Artist - Title [Radio Edit].mp3"
        (r'^(.+?)\s*-\s*(.+?)\s*\[.+?[Ee]dit\]$', 'artist_title_edit'),

        # "Artist - Title (Live).mp3"
        (r'^(.+?)\s*-\s*(.+?)\s*\([Ll]ive\)$', 'artist_title_live'),

        # === PATRONES BÁSICOS (MÁS GENÉRICOS) ===

        # "Artist - Title.mp3" (dash - MÁS COMÚN)
        (r'^(.+?)\s*-\s*(.+?)$', 'artist_title_dash'),

        # "Artist_Title.mp3" (underscore - greedy para capturar todo después del primer _)
        (r'^(.+?)_(.+)$', 'artist_title_underscore'),

        # "Artist/Title.mp3" (slash)
        (r'^(.+?)/(.+?)$', 'artist_title_slash'),

        # "Title (Artist).mp3" (parenthesis - ORDEN INVERTIDO)
        (r'^(.+?)\s*\((.+?)\)$', 'title_artist_parenthesis'),

        # "Artist ~ Title.mp3" (tilde)
        (r'^(.+?)\s*~\s*(.+?)$', 'artist_title_tilde'),

        # "Artist | Title.mp3" (pipe)
        (r'^(.+?)\s*\|\s*(.+?)$', 'artist_title_pipe'),

        # === PATRONES SIN ESPACIOS (OLDSCHOOL) ===

        # "Artist-Title.mp3" (sin espacios, dash pegado)
        (r'^([A-Z][a-z]+)-([A-Z].+?)$', 'artist_title_dash_nospace'),

        # "ArtistTitle.mp3" (camelCase) - DEPRECATED: demasiado frágil, baja accuracy
        # (r'^([A-Z][a-z]+)([A-Z][a-z]+.+?)$', 'artist_title_camelcase'),
    ]

    @staticmethod
    def detect_pattern(text: str) -> Optional[Tuple[str, str, str, float]]:
        """
        Detecta patrón en texto y retorna (artist, title, pattern_name, confidence)
        Returns None si no encuentra patrón confiable
        """
        if not text or len(text.strip()) < 3:
            return None

        text = text.strip()

        for pattern, pattern_name in PatternDetector.PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()

                # === PATRONES CON TRACK NUMBER (3 grupos) ===
                if pattern_name in ['track_artist_title_dash', 'track_word_artist_title', 'track_dot_artist_title']:
                    # (track_number, artist, title)
                    artist = groups[1].strip()
                    title = groups[2].strip()
                    confidence = 0.95  # Alta confianza - muy estructurado

                # === PATRONES CON TRACK EN MEDIO (solo 2 grupos) ===
                elif pattern_name == 'artist_track_title':
                    # (artist, title) - track se ignora
                    artist = groups[0].strip()
                    title = groups[1].strip()
                    confidence = 0.9

                # === PATRONES CON AÑO (3 grupos) ===
                elif pattern_name in ['artist_title_year', 'artist_title_year_bracket']:
                    # (artist, title, year)
                    artist = groups[0].strip()
                    title = groups[1].strip()
                    # year = groups[2] (guardamos para futuro)
                    confidence = 0.95

                # === PATRONES CON FEATURING ===
                elif pattern_name in ['artist_feat_title', 'artist_and_title']:
                    # (artist_with_feat, title)
                    artist = groups[0].strip()
                    title = groups[1].strip()
                    confidence = 0.9

                # === PATRONES CON REMIX/VERSION ===
                elif pattern_name in ['artist_title_remix', 'artist_title_edit', 'artist_title_live']:
                    # (artist, title_with_remix)
                    artist = groups[0].strip()
                    title = groups[1].strip()
                    confidence = 0.9

                # === PARENTHESIS INVERTIDO ===
                elif pattern_name == 'title_artist_parenthesis':
                    # (title, artist) -> invertir orden
                    title = groups[0].strip()
                    artist = groups[1].strip()
                    confidence = 0.85

                # === PATRONES BÁSICOS (2 grupos) ===
                else:
                    # (artist, title)
                    artist = groups[0].strip()
                    title = groups[1].strip()

                    # Ajustar confianza según patrón
                    if pattern_name.endswith('dash'):
                        confidence = 0.9  # Dash es muy común
                    elif pattern_name in ['artist_title_underscore', 'artist_title_slash']:
                        confidence = 0.85
                    elif pattern_name in ['artist_title_camelcase', 'artist_title_dash_nospace']:
                        confidence = 0.75  # Oldschool menos confiable
                    else:
                        confidence = 0.8

                # Validaciones de confianza
                if len(artist) < 2 or len(title) < 2:
                    continue

                # Reducir confianza si tiene muchos números (puede ser código)
                if sum(c.isdigit() for c in artist) > len(artist) * 0.5:
                    confidence *= 0.7

                return (artist, title, pattern_name, confidence)

        return None


class CleanupScanWorker(QThread):
    """Worker para escanear carpeta y detectar problemas"""

    progress_update = pyqtSignal(int, str)  # (progress %, message)
    issue_found = pyqtSignal(MetadataIssue)
    scan_complete = pyqtSignal(int, int)  # (total_files, issues_found)
    error_occurred = pyqtSignal(str)

    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = Path(folder_path)
        self.audio_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.wav', '.wma', '.aac'}
        self._is_cancelled = False
        self.detector = PatternDetector()

    def cancel(self):
        """Cancelar escaneo"""
        self._is_cancelled = True

    def analyze_file(self, file_path: Path) -> Optional[MetadataIssue]:
        """Analiza un archivo y detecta problemas"""
        try:
            audio = MutagenFile(str(file_path), easy=True)

            if audio is None:
                return None

            # Obtener tags actuales
            title_tag = None
            artist_tag = None

            if hasattr(audio, 'tags') and audio.tags:
                if 'title' in audio:
                    title_tag = str(audio['title'][0]) if audio['title'] else None
                if 'artist' in audio:
                    artist_tag = str(audio['artist'][0]) if audio['artist'] else None

            # Usar nombre de archivo si no hay tags
            display_value = title_tag if title_tag else file_path.stem

            # CASO 1: Artist missing pero title existe
            if title_tag and not artist_tag:
                # Intentar detectar patrón en title
                result = self.detector.detect_pattern(title_tag)

                if result:
                    artist, title, pattern, confidence = result
                    return MetadataIssue(
                        file_path=str(file_path),
                        issue_type='artist_title_merged_in_tag',
                        current_value=f"Title: {title_tag}, Artist: (vacío)",
                        suggested_artist=artist,
                        suggested_title=title,
                        confidence=confidence,
                        pattern_matched=pattern
                    )
                else:
                    # Solo falta artist, no hay patrón detectable
                    return MetadataIssue(
                        file_path=str(file_path),
                        issue_type='missing_artist',
                        current_value=f"Title: {title_tag}, Artist: (vacío)",
                        suggested_artist=None,
                        suggested_title=None,
                        confidence=1.0,
                        pattern_matched='none'
                    )

            # CASO 2: Ambos tags missing - analizar filename
            if not title_tag and not artist_tag:
                result = self.detector.detect_pattern(file_path.stem)

                if result:
                    artist, title, pattern, confidence = result
                    return MetadataIssue(
                        file_path=str(file_path),
                        issue_type='both_missing_pattern_in_filename',
                        current_value=f"Filename: {file_path.stem}",
                        suggested_artist=artist,
                        suggested_title=title,
                        confidence=confidence,
                        pattern_matched=pattern
                    )
                else:
                    return MetadataIssue(
                        file_path=str(file_path),
                        issue_type='both_missing_no_pattern',
                        current_value=f"Filename: {file_path.stem}",
                        suggested_artist=None,
                        suggested_title=None,
                        confidence=0.0,
                        pattern_matched='none'
                    )

            # CASO 3: Title missing pero artist exists
            if not title_tag and artist_tag:
                return MetadataIssue(
                    file_path=str(file_path),
                    issue_type='missing_title',
                    current_value=f"Artist: {artist_tag}, Title: (vacío)",
                    suggested_artist=None,
                    suggested_title=file_path.stem,  # Sugerir filename
                    confidence=0.7,
                    pattern_matched='none'
                )

            # No hay problemas detectables
            return None

        except Exception as e:
            # Error al leer archivo
            return None

    def run(self):
        """Escanear carpeta"""
        try:
            self.progress_update.emit(0, "Buscando archivos de audio...")

            # Encontrar archivos
            audio_files = []
            for ext in self.audio_extensions:
                audio_files.extend(self.folder_path.rglob(f'*{ext}'))

            total_files = len(audio_files)

            if total_files == 0:
                self.scan_complete.emit(0, 0)
                return

            self.progress_update.emit(5, f"Encontrados {total_files:,} archivos. Analizando...")

            issues_found = 0

            for i, file_path in enumerate(audio_files):
                if self._is_cancelled:
                    return

                # Analizar archivo
                issue = self.analyze_file(file_path)

                if issue:
                    issues_found += 1
                    self.issue_found.emit(issue)

                # Progreso
                progress = 5 + int((i / total_files) * 90)
                if i % 10 == 0:  # Actualizar cada 10 archivos
                    self.progress_update.emit(
                        progress,
                        f"Analizados: {i+1}/{total_files} | Problemas: {issues_found}"
                    )

            self.progress_update.emit(100, f"Análisis completo: {issues_found} problemas detectados")
            self.scan_complete.emit(total_files, issues_found)

        except Exception as e:
            self.error_occurred.emit(f"Error durante escaneo: {str(e)}")


class MusicBrainzFetcher:
    """
    Busca metadata en MusicBrainz API
    GRATIS - No requiere API key
    Rate limit: 1 request/second
    """

    def __init__(self):
        if musicbrainzngs:
            musicbrainzngs.set_useragent(
                "NEXUSMusicManager",
                "1.0",
                "https://github.com/nexus/music"
            )
        self.last_request_time = 0
        self.rate_limit_delay = 1.1  # 1.1 seconds entre requests

    def _rate_limit(self):
        """Respetar rate limit de MusicBrainz (1 req/sec)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def search_recording(self, artist: str, title: str) -> Optional[Dict]:
        """
        Busca grabación en MusicBrainz
        Retorna dict con: artist, title, album, year, genre, mbid, confidence
        """
        if not musicbrainzngs:
            return None

        try:
            self._rate_limit()

            # Buscar recording
            result = musicbrainzngs.search_recordings(
                artist=artist,
                recording=title,
                limit=1
            )

            if not result or 'recording-list' not in result:
                return None

            recordings = result['recording-list']
            if not recordings:
                return None

            # Mejor match (primero)
            recording = recordings[0]

            # Extraer metadata
            metadata = {
                'title': recording.get('title'),
                'artist': None,
                'album': None,
                'year': None,
                'genre': None,
                'mbid': recording.get('id'),
                'confidence': float(recording.get('ext:score', 0)) / 100.0
            }

            # Artist
            if 'artist-credit' in recording:
                artists = [a['artist']['name'] for a in recording['artist-credit'] if isinstance(a, dict)]
                if artists:
                    metadata['artist'] = artists[0]

            # Album y Year
            if 'release-list' in recording:
                releases = recording['release-list']
                if releases:
                    release = releases[0]
                    metadata['album'] = release.get('title')

                    # Year desde date
                    if 'date' in release:
                        try:
                            metadata['year'] = int(release['date'][:4])
                        except:
                            pass

            # Genre/tags
            if 'tag-list' in recording:
                tags = recording['tag-list']
                if tags:
                    metadata['genre'] = tags[0]['name'].title()

            return metadata

        except Exception as e:
            print(f"Error buscando en MusicBrainz: {e}")
            return None


class AutoFetchWorker(QThread):
    """Worker para buscar metadata online de múltiples archivos"""

    progress_update = pyqtSignal(int, str)  # (progress %, message)
    metadata_found = pyqtSignal(int, dict)  # (issue_index, metadata_dict)
    fetch_complete = pyqtSignal(int, int)  # (total_searched, found_count)
    error_occurred = pyqtSignal(str)

    def __init__(self, issues: List[MetadataIssue]):
        super().__init__()
        self.issues = issues
        self.fetcher = MusicBrainzFetcher()
        self._is_cancelled = False

    def cancel(self):
        """Cancelar búsqueda"""
        self._is_cancelled = True

    def run(self):
        """Buscar metadata online para issues seleccionados"""
        try:
            total_issues = len(self.issues)
            found_count = 0

            self.progress_update.emit(0, "Iniciando búsqueda en MusicBrainz...")

            for i, issue in enumerate(self.issues):
                if self._is_cancelled:
                    return

                # Solo buscar si hay artist+title sugeridos
                if not issue.suggested_artist or not issue.suggested_title:
                    continue

                # Progress
                progress = int((i / total_issues) * 100)
                self.progress_update.emit(
                    progress,
                    f"Buscando: {issue.suggested_artist} - {issue.suggested_title}"
                )

                # Buscar en MusicBrainz
                metadata = self.fetcher.search_recording(
                    issue.suggested_artist,
                    issue.suggested_title
                )

                if metadata:
                    found_count += 1
                    self.metadata_found.emit(i, metadata)

            self.progress_update.emit(100, f"Búsqueda completa: {found_count}/{total_issues} encontrados")
            self.fetch_complete.emit(total_issues, found_count)

        except Exception as e:
            self.error_occurred.emit(f"Error durante búsqueda: {str(e)}")


class CleanupAssistantTab(QWidget):
    """
    Tab de asistente de limpieza - FASE 1: Preview Only
    Analiza metadata y muestra preview de correcciones sugeridas
    """

    def __init__(self):
        super().__init__()
        self.issues: List[MetadataIssue] = []
        self.scan_worker = None
        self.init_ui()

    def init_ui(self):
        """Inicializar UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🧹 Asistente de Limpieza de Metadata")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Descripción
        desc = QLabel(
            "Analiza tu carpeta de música ANTES de importar.\n"
            "Detecta problemas de metadata y busca información faltante en MusicBrainz.\n"
            "⚠️ Fase 2A: Análisis + Auto-Fetch - NO modifica archivos"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(desc)

        # Botones
        btn_layout = QHBoxLayout()

        self.scan_btn = QPushButton("📁 Seleccionar Carpeta y Escanear")
        self.scan_btn.setFixedHeight(40)
        self.scan_btn.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.scan_btn)

        self.fetch_btn = QPushButton("🔍 Buscar Info Faltante")
        self.fetch_btn.setFixedHeight(40)
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.clicked.connect(self.start_auto_fetch)
        self.fetch_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_layout.addWidget(self.fetch_btn)

        self.export_btn = QPushButton("📄 Exportar Reporte")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_report)
        btn_layout.addWidget(self.export_btn)

        layout.addLayout(btn_layout)

        # Tabla de resultados (FASE 2B: agregamos checkbox + acción)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(11)  # +2 columnas: checkbox + acción
        self.results_table.setHorizontalHeaderLabels([
            "✓", "Acción", "Archivo", "Problema", "Valor Actual",
            "Artista Sugerido", "Título Sugerido", "Album", "Año", "Género", "Confianza"
        ])

        # Ajustar columnas (actualizado para 11 columnas)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Acción dropdown
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Archivo
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Problema
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Valor actual
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Artista
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Título
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Album
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Año
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Género
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Confianza

        layout.addWidget(self.results_table)

        # Resumen
        self.summary_label = QLabel("📊 Resultados: -")
        self.summary_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.summary_label)

        # === FASE 2B: Acciones Rápidas (Bulk) ===
        actions_group = QGroupBox("⚡ Acciones Rápidas")
        actions_layout = QVBoxLayout()

        # Selección masiva
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Selección:"))

        self.select_all_btn = QPushButton("✓ Todos")
        self.select_all_btn.clicked.connect(self.select_all)
        selection_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("☐ Ninguno")
        self.select_none_btn.clicked.connect(self.select_none)
        selection_layout.addWidget(self.select_none_btn)

        self.select_invert_btn = QPushButton("⇄ Invertir")
        self.select_invert_btn.clicked.connect(self.select_invert)
        selection_layout.addWidget(self.select_invert_btn)

        selection_layout.addStretch()
        actions_layout.addLayout(selection_layout)

        # Aplicar acción a seleccionados
        bulk_action_layout = QHBoxLayout()
        bulk_action_layout.addWidget(QLabel("Aplicar a seleccionados:"))

        self.bulk_tags_only_btn = QPushButton("🏷️ Solo Tags")
        self.bulk_tags_only_btn.clicked.connect(lambda: self.set_bulk_action("tags_only"))
        bulk_action_layout.addWidget(self.bulk_tags_only_btn)

        self.bulk_rename_btn = QPushButton("✏️ Tags + Renombrar")
        self.bulk_rename_btn.clicked.connect(lambda: self.set_bulk_action("tags_rename"))
        bulk_action_layout.addWidget(self.bulk_rename_btn)

        self.bulk_organize_btn = QPushButton("📁 Tags + Organizar")
        self.bulk_organize_btn.clicked.connect(lambda: self.set_bulk_action("tags_organize"))
        bulk_action_layout.addWidget(self.bulk_organize_btn)

        bulk_action_layout.addStretch()
        actions_layout.addLayout(bulk_action_layout)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # Botón Aplicar Correcciones (GRANDE y destacado)
        self.apply_btn = QPushButton("🚀 Aplicar Correcciones")
        self.apply_btn.setFixedHeight(50)
        self.apply_btn.setEnabled(False)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #CCCCCC; }
        """)
        self.apply_btn.clicked.connect(self.apply_corrections)
        layout.addWidget(self.apply_btn)

    def start_scan(self):
        """Seleccionar carpeta y escanear"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta de Música",
            str(Path.home() / "Music")
        )

        if not folder:
            return

        # Limpiar resultados anteriores
        self.issues.clear()
        self.results_table.setRowCount(0)

        # Crear worker
        self.scan_worker = CleanupScanWorker(folder)

        # Progreso dialog
        progress = QProgressDialog(
            "Analizando archivos de música...",
            "Cancelar",
            0, 100,
            self
        )
        progress.setWindowTitle("Escaneando...")
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        # Conectar señales
        self.scan_worker.progress_update.connect(
            lambda p, msg: (progress.setValue(p), progress.setLabelText(msg))
        )
        self.scan_worker.issue_found.connect(self.add_issue)
        self.scan_worker.scan_complete.connect(
            lambda total, issues: (progress.close(), self.scan_finished(total, issues))
        )
        self.scan_worker.error_occurred.connect(
            lambda err: (progress.close(), QMessageBox.critical(self, "Error", err))
        )

        progress.canceled.connect(self.scan_worker.cancel)

        # Iniciar escaneo
        self.scan_worker.start()
        progress.show()

    def add_issue(self, issue: MetadataIssue):
        """Agregar problema a tabla (FASE 2B: con checkbox + dropdown)"""
        self.issues.append(issue)

        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        # COL 0: Checkbox para selección
        checkbox = QCheckBox()
        checkbox.setChecked(False)  # Default sin seleccionar
        self.results_table.setCellWidget(row, 0, checkbox)

        # COL 1: Dropdown de acción
        action_combo = QComboBox()
        action_combo.addItems([
            "🏷️ Solo Tags",
            "✏️ Tags + Renombrar",
            "📁 Tags + Organizar"
        ])
        action_combo.setCurrentIndex(0)  # Default: Solo Tags (más seguro)
        self.results_table.setCellWidget(row, 1, action_combo)

        # COL 2: Filename (solo nombre, no path completo)
        filename = Path(issue.file_path).name
        self.results_table.setItem(row, 2, QTableWidgetItem(filename))

        # COL 3: Issue type (traducido)
        issue_text = {
            'artist_title_merged_in_tag': '🔀 Artista+Título juntos',
            'missing_artist': '❌ Falta artista',
            'missing_title': '❌ Falta título',
            'both_missing_pattern_in_filename': '📝 Tags vacíos (patrón detectado)',
            'both_missing_no_pattern': '❓ Tags vacíos (sin patrón)'
        }.get(issue.issue_type, issue.issue_type)
        self.results_table.setItem(row, 3, QTableWidgetItem(issue_text))

        # COL 4: Current value
        self.results_table.setItem(row, 4, QTableWidgetItem(issue.current_value))

        # COL 5: Suggested artist
        artist_item = QTableWidgetItem(issue.suggested_artist or "-")
        if issue.suggested_artist:
            artist_item.setForeground(QColor(0, 150, 0))  # Verde
        self.results_table.setItem(row, 5, artist_item)

        # COL 6: Suggested title
        title_item = QTableWidgetItem(issue.suggested_title or "-")
        if issue.suggested_title:
            title_item.setForeground(QColor(0, 150, 0))  # Verde
        self.results_table.setItem(row, 6, title_item)

        # COL 7: Album (vacío inicialmente, se llena con auto-fetch)
        album_item = QTableWidgetItem(issue.suggested_album or "-")
        if issue.suggested_album:
            album_item.setForeground(QColor(0, 100, 200))  # Azul (online)
        self.results_table.setItem(row, 7, album_item)

        # COL 8: Year (vacío inicialmente)
        year_item = QTableWidgetItem(str(issue.suggested_year) if issue.suggested_year else "-")
        if issue.suggested_year:
            year_item.setForeground(QColor(0, 100, 200))  # Azul (online)
        self.results_table.setItem(row, 8, year_item)

        # COL 9: Genre (vacío inicialmente)
        genre_item = QTableWidgetItem(issue.suggested_genre or "-")
        if issue.suggested_genre:
            genre_item.setForeground(QColor(0, 100, 200))  # Azul (online)
        self.results_table.setItem(row, 9, genre_item)

        # COL 10: Confidence
        confidence_text = f"{issue.confidence*100:.0f}%"
        confidence_item = QTableWidgetItem(confidence_text)

        # Color según confianza
        if issue.confidence >= 0.8:
            confidence_item.setForeground(QColor(0, 150, 0))  # Verde
        elif issue.confidence >= 0.6:
            confidence_item.setForeground(QColor(200, 150, 0))  # Amarillo
        else:
            confidence_item.setForeground(QColor(200, 0, 0))  # Rojo

        self.results_table.setItem(row, 10, confidence_item)

    def scan_finished(self, total_files: int, issues_found: int):
        """Escaneo completado"""
        self.summary_label.setText(
            f"📊 Resultados: {total_files:,} archivos analizados | "
            f"{issues_found:,} problemas detectados | "
            f"{total_files - issues_found:,} archivos OK"
        )

        if issues_found > 0:
            self.export_btn.setEnabled(True)
            self.fetch_btn.setEnabled(True)  # Activar botón auto-fetch
            self.apply_btn.setEnabled(True)  # FASE 2B: Activar aplicar correcciones

        QMessageBox.information(
            self,
            "Análisis Completo",
            f"✅ Escaneo completado\n\n"
            f"Archivos analizados: {total_files:,}\n"
            f"Problemas detectados: {issues_found:,}\n\n"
            f"🔍 Siguiente paso: Haz clic en 'Buscar Info Faltante' para\n"
            f"   obtener metadata de MusicBrainz (Album, Año, Género)"
        )

    def export_report(self):
        """Exportar reporte a CSV"""
        if not self.issues:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte",
            str(Path.home() / "cleanup_report.csv"),
            "CSV Files (*.csv)"
        )

        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Header
                f.write("Archivo,Problema,Valor Actual,Artista Sugerido,Título Sugerido,Confianza,Patrón\n")

                # Datos
                for issue in self.issues:
                    filename = Path(issue.file_path).name
                    f.write(
                        f'"{filename}",'
                        f'"{issue.issue_type}",'
                        f'"{issue.current_value}",'
                        f'"{issue.suggested_artist or ""}",'
                        f'"{issue.suggested_title or ""}",'
                        f'"{issue.confidence:.2f}",'
                        f'"{issue.pattern_matched}"\n'
                    )

            QMessageBox.information(
                self,
                "Reporte Exportado",
                f"✅ Reporte guardado exitosamente:\n{filepath}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"❌ Error al guardar reporte:\n{str(e)}"
            )

    def start_auto_fetch(self):
        """Iniciar búsqueda automática de metadata en MusicBrainz"""
        if not self.issues:
            return

        if not musicbrainzngs:
            QMessageBox.warning(
                self,
                "Librería No Disponible",
                "❌ musicbrainzngs no está instalado.\n\n"
                "Instala con: pip install musicbrainzngs"
            )
            return

        # Contar cuántos archivos tienen artista+título para buscar
        searchable = [i for i in self.issues if i.suggested_artist and i.suggested_title]

        if not searchable:
            QMessageBox.information(
                self,
                "Sin Búsquedas Disponibles",
                "No hay archivos con artista+título detectados.\n\n"
                "Auto-fetch requiere al menos artista y título para buscar."
            )
            return

        # Confirmar con usuario
        reply = QMessageBox.question(
            self,
            "Buscar Metadata Online",
            f"🔍 Se buscarán {len(searchable)} archivos en MusicBrainz\n\n"
            f"Esto tomará aproximadamente {len(searchable)} segundos\n"
            f"(1 segundo por archivo por rate limiting)\n\n"
            f"¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Deshabilitar botones durante búsqueda
        self.fetch_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        # Crear worker
        self.fetch_worker = AutoFetchWorker(self.issues)

        # Progress dialog
        self.fetch_progress = QProgressDialog(
            "Buscando metadata en MusicBrainz...",
            "Cancelar",
            0, 100,
            self
        )
        self.fetch_progress.setWindowTitle("Auto-Fetch")
        self.fetch_progress.setWindowModality(Qt.WindowModality.WindowModal)

        # Conectar señales
        self.fetch_worker.progress_update.connect(
            lambda p, msg: (self.fetch_progress.setValue(p), self.fetch_progress.setLabelText(msg))
        )
        self.fetch_worker.metadata_found.connect(self.update_issue_metadata)
        self.fetch_worker.fetch_complete.connect(self.fetch_finished)

        self.fetch_progress.canceled.connect(self.fetch_worker.cancel)

        # Iniciar búsqueda
        self.fetch_worker.start()
        self.fetch_progress.show()

    def update_issue_metadata(self, issue_index: int, metadata: Dict):
        """Actualizar metadata de un issue con datos de MusicBrainz"""
        if issue_index >= len(self.issues):
            return

        issue = self.issues[issue_index]

        # Actualizar objeto issue
        issue.suggested_album = metadata.get('album')
        issue.suggested_year = metadata.get('year')
        issue.suggested_genre = metadata.get('genre')
        issue.musicbrainz_id = metadata.get('mbid')
        issue.online_confidence = metadata.get('confidence', 0.0)

        # Actualizar tabla UI
        # Album
        album_item = QTableWidgetItem(metadata.get('album', '-'))
        album_item.setForeground(QColor(0, 100, 200))  # Azul
        self.results_table.setItem(issue_index, 5, album_item)

        # Year
        year_str = str(metadata['year']) if metadata.get('year') else '-'
        year_item = QTableWidgetItem(year_str)
        year_item.setForeground(QColor(0, 100, 200))
        self.results_table.setItem(issue_index, 6, year_item)

        # Genre
        genre_item = QTableWidgetItem(metadata.get('genre', '-'))
        genre_item.setForeground(QColor(0, 100, 200))
        self.results_table.setItem(issue_index, 7, genre_item)

    def fetch_finished(self, total: int, found_count: int):
        """Auto-fetch completado"""
        self.fetch_progress.close()

        # Re-habilitar botones
        self.fetch_btn.setEnabled(True)
        self.scan_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        QMessageBox.information(
            self,
            "Búsqueda Completada",
            f"✅ Búsqueda en MusicBrainz completada\n\n"
            f"Archivos buscados: {total}\n"
            f"Metadata encontrada: {found_count}\n"
            f"No encontrados: {total - found_count}\n\n"
            f"💡 Columnas en azul = datos desde MusicBrainz"
        )

    # === FASE 2B: Métodos de Selección y Aplicación ===

    def select_all(self):
        """Seleccionar todos los checkboxes"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)

    def select_none(self):
        """Deseleccionar todos los checkboxes"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def select_invert(self):
        """Invertir selección"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(not checkbox.isChecked())

    def set_bulk_action(self, action_type: str):
        """
        Aplicar acción a todos los seleccionados
        
        Args:
            action_type: 'tags_only' | 'tags_rename' | 'tags_organize'
        """
        action_index = {
            'tags_only': 0,
            'tags_rename': 1,
            'tags_organize': 2
        }.get(action_type, 0)

        selected_count = 0
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                combo = self.results_table.cellWidget(row, 1)
                if combo:
                    combo.setCurrentIndex(action_index)
                    selected_count += 1

        if selected_count > 0:
            QMessageBox.information(
                self,
                "Acción Aplicada",
                f"✅ Acción configurada para {selected_count} archivo(s) seleccionado(s)"
            )
        else:
            QMessageBox.warning(
                self,
                "Sin Selección",
                "⚠️ No hay archivos seleccionados.\n\nUsa los checkboxes para seleccionar archivos primero."
            )

    def apply_corrections(self):
        """Aplicar correcciones a archivos seleccionados"""
        # Contar seleccionados
        selected_rows = []
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(
                self,
                "Sin Selección",
                "⚠️ No hay archivos seleccionados para aplicar correcciones.\n\n"
                "Selecciona al menos un archivo con el checkbox."
            )
            return

        # Confirmar con usuario
        reply = QMessageBox.question(
            self,
            "Confirmar Correcciones",
            f"🚀 Vas a aplicar correcciones a {len(selected_rows)} archivo(s).\n\n"
            f"✅ Se creará backup automático de cada archivo\n"
            f"✅ Backup en: C:/Users/ricar/Music/NEXUS_Backup\n\n"
            f"¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Importar CorrectionEngine
        try:
            from correction_engine import CorrectionEngine, CorrectionAction
            from folder_manager import FolderManager
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Error de Importación",
                f"❌ No se pudo cargar correction_engine:\n{e}"
            )
            return

        # Inicializar engine
        folder_mgr = FolderManager()
        backup_dir = folder_mgr.get_backup_folder()
        engine = CorrectionEngine(backup_dir)

        # Progress dialog
        progress = QProgressDialog(
            "Aplicando correcciones...",
            "Cancelar",
            0, len(selected_rows),
            self
        )
        progress.setWindowTitle("Procesando...")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Aplicar correcciones
        success_count = 0
        error_count = 0
        errors_detail = []

        for i, row in enumerate(selected_rows):
            if progress.wasCanceled():
                break

            # Obtener issue y acción
            issue = self.issues[row]
            combo = self.results_table.cellWidget(row, 1)
            action_index = combo.currentIndex()

            # Mapear índice a tipo de acción
            action_type_map = {
                0: 'tags_only',
                1: 'tags_rename',
                2: 'tags_organize'
            }
            action_type = action_type_map.get(action_index, 'tags_only')

            # Crear CorrectionAction
            action = CorrectionAction(
                file_path=issue.file_path,
                action_type=action_type,
                new_artist=issue.suggested_artist,
                new_title=issue.suggested_title,
                new_album=issue.suggested_album,
                new_year=issue.suggested_year,
                new_genre=issue.suggested_genre
            )

            # Si renombrar, generar nuevo nombre
            if action_type in ['tags_rename', 'tags_organize']:
                if issue.suggested_artist and issue.suggested_title:
                    safe_artist = issue.suggested_artist.replace('/', '_')
                    safe_title = issue.suggested_title.replace('/', '_')
                    ext = Path(issue.file_path).suffix
                    action.new_filename = f"{safe_artist} - {safe_title}{ext}"

            # Aplicar
            result = engine.apply_correction(action)

            if result['success']:
                success_count += 1
            else:
                error_count += 1
                errors_detail.append(f"{Path(issue.file_path).name}: {result['message']}")

            progress.setValue(i + 1)
            progress.setLabelText(
                f"Procesando {i+1}/{len(selected_rows)}...\n"
                f"Exitosos: {success_count} | Errores: {error_count}"
            )

        progress.close()

        # Resultado final
        stats = engine.get_stats()
        
        result_msg = f"✅ Correcciones aplicadas exitosamente\n\n"
        result_msg += f"📊 Estadísticas:\n"
        result_msg += f"  • Exitosos: {success_count}\n"
        result_msg += f"  • Errores: {error_count}\n"
        result_msg += f"  • Backups creados: {stats['backups_created']}\n\n"
        
        if error_count > 0:
            result_msg += f"⚠️ Errores:\n" + "\n".join(errors_detail[:5])
            if len(errors_detail) > 5:
                result_msg += f"\n...y {len(errors_detail) - 5} más"

        QMessageBox.information(
            self,
            "Correcciones Completadas",
            result_msg
        )

        # Actualizar UI
        if success_count > 0:
            # Remover filas procesadas exitosamente (opcional)
            # Por ahora solo deshabilitamos checkboxes
            for row in selected_rows:
                checkbox = self.results_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
