#!/usr/bin/env python3
"""
Configuration Manager
Guarda y carga configuración de la aplicación
Project: AGENTE_MUSICA_MP3_001
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    """
    Manages application configuration
    - Library path
    - Download directory
    - Language preference
    - First run flag
    """

    def __init__(self):
        # Config directory in user home
        self.config_dir = Path.home() / ".nexus_music"
        self.config_file = self.config_dir / "config.json"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Default configuration
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "first_run": True,
            "library_path": None,
            "download_directory": str(Path.home() / "Music" / "NEXUS_Downloads"),
            "language": "es",
            "use_demo_database": False,
            "last_scan_date": None,
            "audio_files_count": 0
        }

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def is_first_run(self) -> bool:
        """Check if this is first run"""
        return self.config.get("first_run", True)

    def set_first_run_complete(self):
        """Mark first run as complete"""
        self.config["first_run"] = False
        self.save_config()

    def get_library_path(self) -> Optional[str]:
        """Get configured library path"""
        return self.config.get("library_path")

    def set_library_path(self, path: str):
        """Set library path"""
        self.config["library_path"] = path
        self.save_config()

    def get_download_directory(self) -> str:
        """Get download directory"""
        return self.config.get("download_directory", str(Path.home() / "Music" / "NEXUS_Downloads"))

    def set_download_directory(self, path: str):
        """Set download directory"""
        self.config["download_directory"] = path
        self.save_config()

    def get_language(self) -> str:
        """Get language preference"""
        return self.config.get("language", "es")

    def set_language(self, language: str):
        """Set language preference"""
        self.config["language"] = language
        self.save_config()

    def should_use_demo_database(self) -> bool:
        """Check if should use demo database"""
        return self.config.get("use_demo_database", False) or self.get_library_path() is None

    def set_use_demo_database(self, use_demo: bool):
        """Set whether to use demo database"""
        self.config["use_demo_database"] = use_demo
        self.save_config()

    def set_audio_files_count(self, count: int):
        """Set total audio files found"""
        self.config["audio_files_count"] = count
        self.save_config()

    def get_audio_files_count(self) -> int:
        """Get total audio files"""
        return self.config.get("audio_files_count", 0)

    def get_database_path(self) -> str:
        """Get appropriate database path"""
        if self.should_use_demo_database():
            # Use demo database
            return str(Path(__file__).parent / "phase2_database" / "nexus_music.db")
        else:
            # Use user's library database
            db_dir = self.config_dir / "databases"
            db_dir.mkdir(exist_ok=True)
            return str(db_dir / "user_library.db")

    def reset_config(self):
        """Reset configuration to defaults"""
        self.config = self.get_default_config()
        self.save_config()
