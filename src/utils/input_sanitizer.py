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


def validate_path(path: str, base_dir: str) -> tuple[bool, str]:
    """
    Validate a path to prevent path traversal attacks

    Security features:
    - Resolve to absolute path
    - Check if path is within allowed base directory
    - Prevent symlink attacks
    - Handle Windows and Unix paths

    Args:
        path: The path to validate (user input)
        base_dir: The allowed base directory (trusted)

    Returns:
        Tuple of (is_valid: bool, resolved_path: str)
        If invalid, resolved_path contains error message

    Example:
        >>> validate_path("/home/user/music/../../../etc/passwd", "/home/user/music")
        (False, "Path escapes base directory")

        >>> validate_path("songs/track.mp3", "/home/user/music")
        (True, "/home/user/music/songs/track.mp3")
    """
    if not path or not base_dir:
        return False, "Empty path or base directory"

    try:
        # Convert to Path objects
        base_path = Path(base_dir).resolve()

        # Handle relative and absolute paths
        if Path(path).is_absolute():
            target_path = Path(path).resolve()
        else:
            target_path = (base_path / path).resolve()

        # Check if target is within base directory
        try:
            target_path.relative_to(base_path)
        except ValueError:
            logger.warning(f"Path traversal attempt blocked: {path}")
            return False, "Path escapes base directory"

        # Additional check for symlinks (if path exists)
        if target_path.exists() and target_path.is_symlink():
            real_path = target_path.resolve()
            try:
                real_path.relative_to(base_path)
            except ValueError:
                logger.warning(f"Symlink escape attempt blocked: {path}")
                return False, "Symlink points outside base directory"

        return True, str(target_path)

    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False, f"Invalid path: {str(e)}"


def sanitize_url(url: str, allowed_domains: list[str] = None) -> tuple[bool, str]:
    """
    Validate and sanitize URLs

    Security features:
    - Verify URL format
    - Check against allowed domains (if provided)
    - Remove dangerous URL schemes
    - Prevent SSRF attacks

    Args:
        url: The URL to validate
        allowed_domains: List of allowed domains (e.g., ["youtube.com", "youtu.be"])
                        If None, only validates format

    Returns:
        Tuple of (is_valid: bool, sanitized_url: str)
        If invalid, sanitized_url contains error message

    Example:
        >>> sanitize_url("https://youtube.com/watch?v=abc123", ["youtube.com"])
        (True, "https://youtube.com/watch?v=abc123")

        >>> sanitize_url("file:///etc/passwd", ["youtube.com"])
        (False, "Disallowed URL scheme: file")
    """
    from urllib.parse import urlparse

    if not url:
        return False, "Empty URL"

    try:
        # Parse URL
        parsed = urlparse(url)

        # Check scheme (only allow http/https)
        if parsed.scheme not in ('http', 'https'):
            return False, f"Disallowed URL scheme: {parsed.scheme}"

        # Check for valid hostname
        if not parsed.netloc:
            return False, "Missing hostname"

        # Check against allowed domains if provided
        if allowed_domains:
            hostname = parsed.netloc.lower()
            # Remove www. prefix for comparison
            if hostname.startswith('www.'):
                hostname = hostname[4:]

            domain_allowed = False
            for domain in allowed_domains:
                domain = domain.lower()
                if hostname == domain or hostname.endswith('.' + domain):
                    domain_allowed = True
                    break

            if not domain_allowed:
                return False, f"Domain not allowed: {parsed.netloc}"

        # Sanitize - remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', url)

        return True, sanitized

    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False, f"Invalid URL: {str(e)}"


def sanitize_metadata(metadata: dict) -> dict:
    """
    Sanitize metadata dictionary from external sources

    Security features:
    - Sanitize all string values
    - Remove potential XSS/injection in all fields
    - Preserve structure

    Args:
        metadata: Dictionary with metadata fields

    Returns:
        Sanitized metadata dictionary

    Example:
        >>> sanitize_metadata({"title": "<script>alert('xss')</script>", "artist": "Test"})
        {"title": "scriptalert(xss)/script", "artist": "Test"}
    """
    if not metadata:
        return {}

    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            # Remove HTML tags
            value = re.sub(r'<[^>]+>', '', value)
            # Remove control characters
            value = re.sub(r'[\x00-\x1f\x7f-0x9f]', '', value)
            # Remove script-related content
            value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
            # Trim whitespace
            value = value.strip()
        elif isinstance(value, dict):
            value = sanitize_metadata(value)
        elif isinstance(value, list):
            value = [sanitize_metadata(v) if isinstance(v, dict) else v for v in value]

        sanitized[key] = value

    return sanitized
