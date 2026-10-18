"""Shared preprocessing for the backend.

The implementation lives in ``ml/preprocessing.py`` so that training and
serving call exactly the same function. This module only re-exports it, which
keeps the existing ``app.services.preprocessing`` imports working.
"""

from ml.preprocessing import (
    MIN_TOKEN_LENGTH,
    PHONE_MAX_DIGITS,
    PHONE_MIN_DIGITS,
    PLACEHOLDER_NUMBER,
    PLACEHOLDER_PHONE,
    PLACEHOLDER_URL,
    STOPWORDS_FILE,
    clean,
    load_stopwords,
    normalize,
    preprocess,
    remove_stopwords,
    substitute_placeholders,
    tokenize,
)

__all__ = [
    "MIN_TOKEN_LENGTH",
    "PHONE_MAX_DIGITS",
    "PHONE_MIN_DIGITS",
    "PLACEHOLDER_NUMBER",
    "PLACEHOLDER_PHONE",
    "PLACEHOLDER_URL",
    "STOPWORDS_FILE",
    "clean",
    "load_stopwords",
    "normalize",
    "preprocess",
    "remove_stopwords",
    "substitute_placeholders",
    "tokenize",
]
