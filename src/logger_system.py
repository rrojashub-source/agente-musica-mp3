#!/usr/bin/env python3
"""
Logging System - Complete error tracking and debugging
Project: AGENTE_MUSICA_MP3_001
Purpose: Track all errors and events for troubleshooting
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Log file location
LOG_DIR = Path.home() / ".nexus_music" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Current log file (rotates daily)
LOG_FILE = LOG_DIR / f"nexus_music_{datetime.now().strftime('%Y%m%d')}.log"


class NEXUSLogger:
    """
    Centralized logging system for NEXUS Music Manager
    """

    def __init__(self):
        self.logger = logging.getLogger("NEXUS")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # File handler - all messages
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Console handler - warnings and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = True):
        """Log critical error"""
        self.logger.critical(message, exc_info=exc_info)

    def exception(self, message: str):
        """Log exception with full traceback"""
        self.logger.exception(message)


# Global logger instance
_logger = NEXUSLogger()


def get_logger() -> NEXUSLogger:
    """Get global logger instance"""
    return _logger


def log_startup():
    """Log application startup"""
    logger = get_logger()
    logger.info("=" * 80)
    logger.info("NEXUS MUSIC MANAGER - APPLICATION STARTED")
    logger.info("=" * 80)
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Log File: {LOG_FILE}")


def log_shutdown():
    """Log application shutdown"""
    logger = get_logger()
    logger.info("=" * 80)
    logger.info("NEXUS MUSIC MANAGER - APPLICATION CLOSED")
    logger.info("=" * 80)


def log_exception(exc_type, exc_value, exc_traceback):
    """
    Global exception handler
    Logs all unhandled exceptions
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupts
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = get_logger()
    logger.critical(
        "UNHANDLED EXCEPTION",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def setup_exception_hook():
    """Setup global exception hook"""
    sys.excepthook = log_exception


def get_recent_logs(lines: int = 100) -> str:
    """
    Get recent log lines

    Args:
        lines: Number of lines to retrieve

    Returns:
        Recent log content as string
    """
    if not LOG_FILE.exists():
        return "No log file found."

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return ''.join(recent)
    except Exception as e:
        return f"Error reading log file: {str(e)}"


def get_log_file_path() -> Path:
    """Get current log file path"""
    return LOG_FILE


def get_all_log_files() -> list:
    """Get list of all log files"""
    if not LOG_DIR.exists():
        return []

    return sorted(LOG_DIR.glob("nexus_music_*.log"), reverse=True)


def clear_old_logs(days: int = 7):
    """
    Clear log files older than specified days

    Args:
        days: Number of days to keep
    """
    if not LOG_DIR.exists():
        return

    cutoff_date = datetime.now() - datetime.timedelta(days=days)

    for log_file in LOG_DIR.glob("nexus_music_*.log"):
        try:
            # Parse date from filename
            date_str = log_file.stem.replace("nexus_music_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")

            if file_date < cutoff_date:
                log_file.unlink()
                get_logger().info(f"Deleted old log file: {log_file.name}")

        except Exception as e:
            get_logger().warning(f"Failed to delete old log: {log_file.name} - {e}")
