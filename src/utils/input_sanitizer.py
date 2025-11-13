"""
Input Sanitizer - Security Module

Purpose: Prevent injection attacks and filesystem issues
- Remove control characters
- Remove SQL/command injection attempts
- Sanitize filenames for filesystem safety
- Preserve Unicode (Beyoncé, etc.)

Created: November 13, 2025 (Pre-Phase 5 Hardening - Blocker #4)
"""
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def sanitize_query(query: str, max_length: int = 500) -> str:
    """
    Sanitize user input for API queries

    Security features:
    - Remove control characters (0x00-0x1f, 0x7f-0x9f)
    - Remove SQL injection attempts (' " ;)
    - Remove command injection attempts (| & $ `)
    - Remove path traversal attempts (../)
    - Preserve Unicode characters (Beyoncé, Déjà Vu, etc.)
    - Truncate to max_length (default: 500 chars)

    Args:
        query: User input string to sanitize
        max_length: Maximum length for output (default: 500)

    Returns:
        Sanitized query string safe for API calls

    Example:
        >>> sanitize_query("Beyoncé'; DROP TABLE songs;--")
        'Beyoncé DROP TABLE songs--'

        >>> sanitize_query("test\x00\x01song")
        'testsong'
    """
    if not query:
        return ""

    # Remove control characters (ASCII 0x00-0x1f and 0x7f-0x9f)
    # These can cause issues in logs, databases, and APIs
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)

    # Remove SQL injection attempts
    # Removes: single quotes, double quotes, semicolons
    query = re.sub(r'[\'\";]', '', query)

    # Remove command injection attempts
    # Removes: pipes, ampersands, dollar signs, backticks
    query = re.sub(r'[|&$`]', '', query)

    # Remove path traversal attempts
    query = query.replace('../', '').replace('..\\', '')

    # Truncate to max length
    query = query[:max_length]

    # Remove leading/trailing whitespace
    query = query.strip()

    logger.debug(f"Sanitized query: {len(query)} chars")
    return query


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for filesystem safety

    Security features:
    - Remove control characters
    - Remove/replace invalid filesystem chars (/ \\ : * ? " < > |)
    - Preserve file extension
    - Handle empty input (return "untitled")
    - Truncate to 255 chars (filesystem limit)
    - Remove leading/trailing dots and spaces

    Args:
        filename: Filename to sanitize
        max_length: Maximum length for filename (default: 255)

    Returns:
        Sanitized filename safe for filesystem operations

    Example:
        >>> sanitize_filename("song/name:with*invalid|chars?.mp3")
        'song_name_with_invalid_chars_.mp3'

        >>> sanitize_filename("")
        'untitled'

        >>> sanitize_filename("a" * 300 + ".mp3")
        'aaaa...aaa.mp3'  # Truncated to 255 chars preserving extension
    """
    if not filename:
        return "untitled"

    # Remove control characters (ASCII 0x00-0x1f and 0x7f-0x9f)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

    # Replace invalid filesystem characters with underscores
    # Invalid chars: / \ : * ? " < > |
    filename = re.sub(r'[/\\:*?"<>|]', '_', filename)

    # Remove leading/trailing dots and spaces (Windows compatibility)
    filename = filename.strip('. ')

    # If filename became empty after stripping, return default
    if not filename:
        return "untitled"

    # Truncate to max_length while preserving extension
    if len(filename) > max_length:
        path_obj = Path(filename)
        stem = path_obj.stem  # Filename without extension
        suffix = path_obj.suffix  # Extension with dot (.mp3)

        # Calculate max stem length
        max_stem_length = max_length - len(suffix)

        # Truncate stem and rebuild filename
        truncated_stem = stem[:max_stem_length]
        filename = truncated_stem + suffix

        logger.warning(f"Filename truncated to {max_length} chars: {filename}")

    logger.debug(f"Sanitized filename: {filename}")
    return filename
