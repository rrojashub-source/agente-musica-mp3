#!/usr/bin/env python3
"""
NEXUS Music Manager - Correction Engine
Motor para aplicar correcciones a archivos MP3
Opción C: Híbrido (Solo Tags / Tags+Renombrar / Tags+Organizar)
"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, TRCK
    from mutagen.flac import FLAC
    from mutagen.m4a import M4A
except ImportError:
    print("❌ mutagen not installed")
    exit(1)

logger = logging.getLogger(__name__)


@dataclass
class CorrectionAction:
    """Acción de corrección a aplicar"""
    file_path: str
    action_type: str  # 'tags_only' | 'tags_rename' | 'tags_organize'

    # Tags a actualizar
    new_artist: Optional[str] = None
    new_title: Optional[str] = None
    new_album: Optional[str] = None
    new_year: Optional[int] = None
    new_genre: Optional[str] = None
    new_track: Optional[int] = None

    # Renombrado
    new_filename: Optional[str] = None  # Si action_type incluye rename

    # Organización
    organized_path: Optional[str] = None  # Si action_type = 'tags_organize'

    # Backup
    backup_path: Optional[str] = None


class CorrectionEngine:
    """Engine para aplicar correcciones de manera segura"""

    def __init__(self, backup_dir: Path):
        """
        Args:
            backup_dir: Directorio para backups automáticos
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Stats
        self.corrections_applied = 0
        self.backups_created = 0
        self.errors = []

    def apply_correction(self, action: CorrectionAction) -> Dict:
        """
        Aplica una corrección de forma segura

        Args:
            action: CorrectionAction con los cambios a aplicar

        Returns:
            Dict con: {success: bool, message: str, backup_path: str | None}
        """
        file_path = Path(action.file_path)

        # Validar existencia
        if not file_path.exists():
            return {
                'success': False,
                'message': f'File not found: {file_path}',
                'backup_path': None
            }

        try:
            # PASO 1: Crear backup
            backup_result = self._create_backup(file_path)
            if not backup_result['success']:
                return backup_result

            action.backup_path = backup_result['backup_path']

            # PASO 2: Aplicar según tipo de acción
            if action.action_type == 'tags_only':
                result = self._apply_tags_only(action)

            elif action.action_type == 'tags_rename':
                result = self._apply_tags_and_rename(action)

            elif action.action_type == 'tags_organize':
                result = self._apply_tags_and_organize(action)

            else:
                return {
                    'success': False,
                    'message': f'Unknown action type: {action.action_type}',
                    'backup_path': action.backup_path
                }

            if result['success']:
                self.corrections_applied += 1

            return result

        except Exception as e:
            logger.error(f"Error applying correction to {file_path}: {e}")
            self.errors.append({
                'file': str(file_path),
                'error': str(e)
            })
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'backup_path': action.backup_path
            }

    def _create_backup(self, file_path: Path) -> Dict:
        """Crea backup del archivo antes de modificar"""
        try:
            # Nombre con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_filename

            # Copiar
            shutil.copy2(file_path, backup_path)

            self.backups_created += 1
            logger.info(f"Backup created: {backup_path}")

            return {
                'success': True,
                'message': 'Backup created',
                'backup_path': str(backup_path)
            }

        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return {
                'success': False,
                'message': f'Backup failed: {str(e)}',
                'backup_path': None
            }

    def _apply_tags_only(self, action: CorrectionAction) -> Dict:
        """Aplica solo correcciones de tags (no mueve ni renombra)"""
        file_path = Path(action.file_path)

        try:
            # Cargar archivo según formato
            audio = None

            if file_path.suffix.lower() == '.mp3':
                audio = MP3(file_path, ID3=ID3)

                # Asegurar que existen tags ID3
                if audio.tags is None:
                    audio.add_tags()

                # Actualizar tags
                if action.new_artist:
                    audio.tags['TPE1'] = TPE1(encoding=3, text=action.new_artist)

                if action.new_title:
                    audio.tags['TIT2'] = TIT2(encoding=3, text=action.new_title)

                if action.new_album:
                    audio.tags['TALB'] = TALB(encoding=3, text=action.new_album)

                if action.new_year:
                    audio.tags['TDRC'] = TDRC(encoding=3, text=str(action.new_year))

                if action.new_genre:
                    audio.tags['TCON'] = TCON(encoding=3, text=action.new_genre)

                if action.new_track:
                    audio.tags['TRCK'] = TRCK(encoding=3, text=str(action.new_track))

                audio.save()

            elif file_path.suffix.lower() == '.flac':
                audio = FLAC(file_path)

                if action.new_artist:
                    audio['artist'] = action.new_artist
                if action.new_title:
                    audio['title'] = action.new_title
                if action.new_album:
                    audio['album'] = action.new_album
                if action.new_year:
                    audio['date'] = str(action.new_year)
                if action.new_genre:
                    audio['genre'] = action.new_genre
                if action.new_track:
                    audio['tracknumber'] = str(action.new_track)

                audio.save()

            elif file_path.suffix.lower() == '.m4a':
                audio = M4A(file_path)

                if action.new_artist:
                    audio['\xa9ART'] = action.new_artist
                if action.new_title:
                    audio['\xa9nam'] = action.new_title
                if action.new_album:
                    audio['\xa9alb'] = action.new_album
                if action.new_year:
                    audio['\xa9day'] = str(action.new_year)
                if action.new_genre:
                    audio['\xa9gen'] = action.new_genre

                audio.save()

            else:
                return {
                    'success': False,
                    'message': f'Unsupported format: {file_path.suffix}',
                    'backup_path': action.backup_path
                }

            logger.info(f"Tags updated: {file_path}")
            return {
                'success': True,
                'message': 'Tags updated successfully',
                'backup_path': action.backup_path
            }

        except Exception as e:
            logger.error(f"Error updating tags for {file_path}: {e}")
            return {
                'success': False,
                'message': f'Tag update failed: {str(e)}',
                'backup_path': action.backup_path
            }

    def _apply_tags_and_rename(self, action: CorrectionAction) -> Dict:
        """Aplica tags y renombra archivo en misma carpeta"""
        file_path = Path(action.file_path)

        # Primero aplicar tags
        tags_result = self._apply_tags_only(action)
        if not tags_result['success']:
            return tags_result

        # Luego renombrar si se especificó nuevo nombre
        if not action.new_filename:
            return tags_result  # Solo tags, sin renombrar

        try:
            new_path = file_path.parent / action.new_filename

            # Evitar sobrescribir archivo existente
            if new_path.exists() and new_path != file_path:
                # Agregar número
                counter = 1
                base = new_path.stem
                while new_path.exists():
                    new_path = file_path.parent / f"{base}_{counter}{file_path.suffix}"
                    counter += 1

            file_path.rename(new_path)

            logger.info(f"File renamed: {file_path} -> {new_path}")
            return {
                'success': True,
                'message': f'Tags updated and renamed to: {new_path.name}',
                'backup_path': action.backup_path
            }

        except Exception as e:
            logger.error(f"Error renaming {file_path}: {e}")
            return {
                'success': False,
                'message': f'Rename failed: {str(e)} (tags were updated)',
                'backup_path': action.backup_path
            }

    def _apply_tags_and_organize(self, action: CorrectionAction) -> Dict:
        """Aplica tags y mueve a estructura organizada Artist/Album/"""
        file_path = Path(action.file_path)

        # Primero aplicar tags
        tags_result = self._apply_tags_only(action)
        if not tags_result['success']:
            return tags_result

        # Validar que tenemos info para organizar
        if not action.new_artist or not action.new_title:
            return {
                'success': False,
                'message': 'Cannot organize: missing artist or title',
                'backup_path': action.backup_path
            }

        try:
            # Estructura: NEXUS_Organized/Artist/Album/Track - Title.ext
            organized_base = Path(action.organized_path) if action.organized_path else Path.home() / "Music" / "NEXUS_Organized"

            # Sanitizar nombres (quitar caracteres inválidos)
            safe_artist = self._sanitize_filename(action.new_artist)
            safe_album = self._sanitize_filename(action.new_album) if action.new_album else "Unknown Album"
            safe_title = self._sanitize_filename(action.new_title)

            # Crear estructura
            target_dir = organized_base / safe_artist / safe_album
            target_dir.mkdir(parents=True, exist_ok=True)

            # Nombre de archivo: "01 - Title.mp3" o "Title.mp3"
            if action.new_track:
                new_filename = f"{action.new_track:02d} - {safe_title}{file_path.suffix}"
            else:
                new_filename = f"{safe_title}{file_path.suffix}"

            target_path = target_dir / new_filename

            # Evitar sobrescribir
            if target_path.exists():
                counter = 1
                base = target_path.stem
                while target_path.exists():
                    target_path = target_dir / f"{base}_{counter}{file_path.suffix}"
                    counter += 1

            # Mover archivo
            shutil.move(str(file_path), str(target_path))

            logger.info(f"File organized: {file_path} -> {target_path}")
            return {
                'success': True,
                'message': f'Tags updated and organized to: {target_path.relative_to(organized_base)}',
                'backup_path': action.backup_path
            }

        except Exception as e:
            logger.error(f"Error organizing {file_path}: {e}")
            return {
                'success': False,
                'message': f'Organization failed: {str(e)} (tags were updated)',
                'backup_path': action.backup_path
            }

    def _sanitize_filename(self, name: str) -> str:
        """Sanitiza nombre de archivo/carpeta (remueve caracteres inválidos)"""
        # Caracteres inválidos en Windows/Linux
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')

        # Remover puntos al final (inválido en Windows)
        sanitized = sanitized.rstrip('.')

        # Limitar longitud
        return sanitized[:200]

    def get_stats(self) -> Dict:
        """Retorna estadísticas de correcciones"""
        return {
            'corrections_applied': self.corrections_applied,
            'backups_created': self.backups_created,
            'errors_count': len(self.errors),
            'errors': self.errors
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import tempfile

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    print("🧪 TEST: Correction Engine\n")
    print("=" * 80)

    # Crear directorio temporal para backups
    with tempfile.TemporaryDirectory() as temp_backup:
        backup_dir = Path(temp_backup) / "backups"
        engine = CorrectionEngine(backup_dir)

        print(f"📁 Backup directory: {backup_dir}\n")

        # Test case: archivo de prueba (si existe)
        test_file = Path("test_files_robustez_real/David_Bowie_Space_Oddity.mp3")

        if test_file.exists():
            print(f"📝 Testing with: {test_file.name}")

            # Copiar a temp para no modificar original
            temp_test = Path(temp_backup) / "test.mp3"
            shutil.copy2(test_file, temp_test)

            # Test 1: Tags only
            print("\n🧪 TEST 1: Tags Only")
            action = CorrectionAction(
                file_path=str(temp_test),
                action_type='tags_only',
                new_artist='David Bowie',
                new_title='Space Oddity',
                new_album='Space Oddity',
                new_year=1969,
                new_genre='Rock'
            )

            result = engine.apply_correction(action)
            print(f"Result: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
            print(f"Message: {result['message']}")
            print(f"Backup: {result['backup_path']}")

            # Verificar tags actualizados
            audio = MP3(temp_test, ID3=ID3)
            print(f"✅ Verified - Artist: {audio.tags.get('TPE1', 'N/A')}")
            print(f"✅ Verified - Title: {audio.tags.get('TIT2', 'N/A')}")

        else:
            print(f"⏭️  Skipping test: {test_file} not found")

        # Stats
        print("\n" + "=" * 80)
        print("📊 STATS:")
        stats = engine.get_stats()
        print(f"  Corrections applied: {stats['corrections_applied']}")
        print(f"  Backups created: {stats['backups_created']}")
        print(f"  Errors: {stats['errors_count']}")

    print("\n✅ Test completado")
