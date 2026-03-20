"""
Content Filter Module - AI-powered music content classification

Usage:
    from services.content_filter import ContentClassifier, ContentRating, get_classifier

    classifier = get_classifier()
    result = classifier.classify_file("path/to/song.mp3")
    print(f"Rating: {result.rating}")  # ContentRating.CLEAN, EXPLICIT, etc.
"""

from .classifier import (
    ContentClassifier,
    ContentRating,
    ContentScore,
    ClassificationResult,
    get_classifier,
)

__all__ = [
    "ContentClassifier",
    "ContentRating",
    "ContentScore",
    "ClassificationResult",
    "get_classifier",
]
