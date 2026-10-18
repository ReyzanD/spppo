"""Unit tests for the shared preprocessing used by training and serving."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.preprocessing import (  # noqa: E402
    PLACEHOLDER_NUMBER,
    PLACEHOLDER_PHONE,
    PLACEHOLDER_URL,
    clean,
    preprocess,
    tokenize,
)


def test_case_folding_and_punctuation_are_removed() -> None:
    assert preprocess("FREE Entry!!! MONEY???") == "free entry money"


def test_stopwords_and_one_character_tokens_are_dropped() -> None:
    assert preprocess("This is a test of the system") == "test system"


def test_number_phone_and_url_are_kept_as_placeholders() -> None:
    result = preprocess("Call 081234567890 or visit http://x.co and pay 500 now")

    assert PLACEHOLDER_PHONE in result
    assert PLACEHOLDER_URL in result
    assert PLACEHOLDER_NUMBER in result
    assert "081234567890" not in result
    assert "500" not in result.split()


def test_phone_number_longer_than_fifteen_digits_is_a_number() -> None:
    assert preprocess("ref 12345678901234567890") == "ref <num>"


def test_empty_and_punctuation_only_inputs_return_empty_string() -> None:
    assert preprocess("") == ""
    assert preprocess("   \t \n") == ""
    assert preprocess("!!! ... ???") == ""


def test_tokenize_exposes_the_same_steps() -> None:
    assert tokenize("win 1000 cash") == ["win", "<num>", "cash"]


def test_preprocess_is_idempotent() -> None:
    once = preprocess("Click http://x.co or call 081234567890 about the 500 prize")

    assert preprocess(once) == once
    assert clean is preprocess


def test_placeholder_is_never_dropped_as_a_stopword() -> None:
    assert preprocess("http://x.co 1000") == "<url> <num>"
