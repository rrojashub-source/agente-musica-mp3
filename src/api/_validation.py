"""Shared query validation for API search clients."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from utils.constants import API_MAX_RESULTS, API_QUERY_MAX_LENGTH
from utils.input_sanitizer import sanitize_query

logger = logging.getLogger(__name__)


def validate_search_query(
    query: str,
    limit: int,
    max_results: int = API_MAX_RESULTS,
) -> Tuple[Optional[str], int]:
    """Validate and sanitize a search query for API use.

    Returns:
        (sanitized_query, clamped_limit) — query is None if invalid.
    """
    if not query:
        logger.warning("Empty query received")
        return None, limit

    query = sanitize_query(query, max_length=API_QUERY_MAX_LENGTH)

    if not query:
        logger.warning("Query became empty after sanitization")
        return None, limit

    limit = min(limit, max_results)
    return query, limit
