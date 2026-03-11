#!/usr/bin/env python3
"""
NEXUS Music Manager - Folder Manager
Gestión automática de carpetas del sistema
"""

from pathlib import Path
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class FolderManager:
    """Gestiona la creación y configuración de carpetas del sistema"""

    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: Ruta al archivo config.json
        """
        if config_path is None:
            config_path = Path.home() / ".nexus_music" / "config.json"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.config = self._load_config()

        # Carpetas del sistema
        self.folders = {
            'library': Path(self.config.get('library_path', '')),
            'downloads': Path(self.config.get('download_directory', '')),
            'backup': Path(self.config.get('backup_directory', '')),
            'organized': Path(self.config.get('organized_directory', ''))
        }

    def _load_config(self) -> Dict:
        """Cargar configuración desde JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error cargando config: {e}")
            return {}

    def ensure_folders_exist(self) -> Dict[str, bool]:
        """
        Asegura que todas las carpetas existan

        Returns:
            Dict con status de cada carpeta: {nombre: created_now}
        """
        results = {}

        if not self.config.get('auto_create_folders', True):
            logger.info("Auto-creación de carpetas deshabilitada")
            return results

        for folder_name, folder_path in self.folders.items():
            if not folder_path or str(folder_path) == '.':
                logger.warning(f"Carpeta {folder_name} no configurada, saltando")
                results[folder_name] = False
                continue

            try:
                if folder_path.exists():
                    logger.info(f"✅ {folder_name}: Ya existe en {folder_path}")
                    results[folder_name] = False  # Ya existía
                else:
                    folder_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"✅ {folder_name}: Creada en {folder_path}")
                    results[folder_name] = True  # Recién creada

            except PermissionError:
                logger.error(f"❌ {folder_name}: Sin permisos para crear {folder_path}")
                results[folder_name] = False
            except OSError as e:
                logger.error(f"❌ {folder_name}: Error creando {folder_path} - {e}")
                results[folder_name] = False

        return results

    def get_folder_stats(self) -> Dict[str, Dict]:
        """
        Obtiene estadísticas de cada carpeta

        Returns:
            Dict con info de cada carpeta: {nombre: {exists, path, file_count}}
        """
        stats = {}

        for folder_name, folder_path in self.folders.items():
            if not folder_path or str(folder_path) == '.':
                stats[folder_name] = {
                    'exists': False,
                    'path': 'Not configured',
                    'file_count': 0
                }
                continue

            exists = folder_path.exists()
            file_count = 0

            if exists:
                try:
                    # Contar archivos de audio
                    audio_extensions = ['.mp3', '.flac', '.m4a', '.ogg', '.wav', '.opus']
                    file_count = sum(1 for f in folder_path.rglob('*')
                                   if f.is_file() and f.suffix.lower() in audio_extensions)
                except OSError as e:
                    logger.error(f"Error contando archivos en {folder_name}: {e}")

            stats[folder_name] = {
                'exists': exists,
                'path': str(folder_path),
                'file_count': file_count
            }

        return stats

    def get_downloads_folder(self) -> Path:
        """Retorna Path de carpeta de descargas"""
        return self.folders['downloads']

    def get_backup_folder(self) -> Path:
        """Retorna Path de carpeta de backups"""
        return self.folders['backup']

    def get_organized_folder(self) -> Path:
        """Retorna Path de carpeta organizada"""
        return self.folders['organized']

    def get_library_folder(self) -> Path:
        """Retorna Path de biblioteca principal"""
        return self.folders['library']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Configurar logging para test
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    print("🧪 TEST: Folder Manager\n")
    print("=" * 60)

    # Test 1: Inicialización
    print("\n📁 TEST 1: Inicialización y configuración")
    manager = FolderManager()

    print(f"Config path: {manager.config_path}")
    print(f"Auto-create: {manager.config.get('auto_create_folders')}")
    print(f"Auto-analyze: {manager.config.get('auto_analyze_downloads')}")

    # Test 2: Crear carpetas
    print("\n📁 TEST 2: Asegurar carpetas existen")
    results = manager.ensure_folders_exist()

    for folder_name, created in results.items():
        status = "🆕 CREADA" if created else "✅ YA EXISTÍA"
        print(f"  {folder_name}: {status}")

    # Test 3: Estadísticas
    print("\n📁 TEST 3: Estadísticas de carpetas")
    stats = manager.get_folder_stats()

    for folder_name, info in stats.items():
        print(f"\n  📂 {folder_name.upper()}:")
        print(f"     Existe: {'✅ Sí' if info['exists'] else '❌ No'}")
        print(f"     Path: {info['path']}")
        print(f"     Archivos audio: {info['file_count']}")

    print("\n" + "=" * 60)
    print("✅ Test completado")
