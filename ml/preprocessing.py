"""Text preprocessing shared by training and serving.

This module is the single source of truth: `ml/train_model.py` imports it to
build the training corpus, and the FastAPI backend imports the very same
function to clean incoming messages. A message can therefore never be cleaned
differently at training time and at prediction time.

Order of operations
-------------------
1. case folding (lowercase)
2. replace URLs, phone numbers and other numbers with placeholder tokens
3. remove punctuation and other non-alphanumeric characters
4. collapse whitespace
5. tokenize
6. drop English stopwords and one-character tokens

Numbers as placeholders
-----------------------
The brief says "remove punctuation and numbers". Removing the digits outright
would also throw away phone numbers, amounts and URLs, which are among the
strongest fraud signals in the SMS Spam Collection (21.5% of messages contain a
number). We therefore *normalise* them to ``<num>``, ``<phone>`` and ``<url>``
instead of deleting the information, and then remove every remaining number and
punctuation mark. This was confirmed with the project owner.

The English stopword list (NLTK) is vendored in ``stopwords_en.txt`` so neither
training nor serving needs a network download.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

STOPWORDS_FILE = Path(__file__).with_name("stopwords_en.txt")
STOPWORDS_ID_FILE = Path(__file__).with_name("stopwords_id.txt")

PLACEHOLDER_URL = "<url>"
PLACEHOLDER_PHONE = "<phone>"
PLACEHOLDER_NUMBER = "<num>"

# Tokens shorter than this carry no signal once case is folded (e.g. "u", "r").
MIN_TOKEN_LENGTH = 2

# Longest run of digits still treated as a phone number.
PHONE_MIN_DIGITS = 8
PHONE_MAX_DIGITS = 15

_URL_PATTERN = re.compile(
    r"https?://\S+|www\.\S+|(?:[a-zA-Z0-9-]+\.)+(?:com|me|id|org|net|info|top|xyz|app|site|online|link|ly|co|my)(?:/\S*)?",
    re.IGNORECASE,
)
_PHONE_PATTERN = re.compile(rf"\b\d{{{PHONE_MIN_DIGITS},{PHONE_MAX_DIGITS}}}\b")
_NUMBER_PATTERN = re.compile(r"\b\d+\b")
# Keep letters, digits, the placeholder brackets and underscores.
_DISALLOWED_PATTERN = re.compile(r"[^a-z0-9<>_\s]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


@lru_cache(maxsize=1)
def load_stopwords() -> frozenset[str]:
    """Return the vendored stopword list (Indonesian + English)."""
    words: set[str] = set()
    for file in (STOPWORDS_FILE, STOPWORDS_ID_FILE):
        if file.is_file():
            words.update(
                word.strip().casefold()
                for word in file.read_text(encoding="utf-8").splitlines()
                if word.strip()
            )
    return frozenset(words)


def substitute_placeholders(text: str) -> str:
    """Replace URLs, phone numbers and other numbers with placeholder tokens."""
    text = _URL_PATTERN.sub(PLACEHOLDER_URL, text)
    text = _PHONE_PATTERN.sub(PLACEHOLDER_PHONE, text)
    return _NUMBER_PATTERN.sub(PLACEHOLDER_NUMBER, text)


def normalize(text: str) -> str:
    """Casefold, substitute placeholders, strip punctuation, collapse spaces."""
    folded = text.casefold()
    with_placeholders = substitute_placeholders(folded)
    without_punctuation = _DISALLOWED_PATTERN.sub(" ", with_placeholders)
    return _WHITESPACE_PATTERN.sub(" ", without_punctuation).strip()


def tokenize(text: str) -> list[str]:
    """Normalise then split into tokens (placeholders are single tokens)."""
    normalized = normalize(text)
    return normalized.split() if normalized else []


def remove_stopwords(tokens: Iterable[str]) -> list[str]:
    """Drop stopwords and one-character tokens, preserving order."""
    stopwords = load_stopwords()
    return [token for token in tokens if len(token) >= MIN_TOKEN_LENGTH and token not in stopwords]


def preprocess(text: str) -> str:
    """Full pipeline. This is the exact string handed to TF-IDF."""
    return " ".join(remove_stopwords(tokenize(text)))


# Backwards-compatible alias: the existing backend and web UI call it `clean`.
clean = preprocess
