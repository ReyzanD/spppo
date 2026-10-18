"""Preprocessing tests (docs/PLAN.md Phase 3, docs/FRD.md §7).

Covers the cases the plan names explicitly: case folding, repeated punctuation,
URLs (http/https/www), 8-15 digit phones, plain numbers, mixed input, empty
strings, punctuation-only input, stopword-only input, and normal English.

The critical requirement is that digits are NOT discarded: "menang 1000" must
keep a token for the amount.
"""

import pytest

from app.services.preprocessing import (
    PLACEHOLDER_NUMBER,
    PLACEHOLDER_PHONE,
    PLACEHOLDER_URL,
    STOPWORDS_FILE,
    clean,
    load_stopwords,
    normalize,
    remove_stopwords,
    substitute_placeholders,
    tokenize,
)

# --- case folding and punctuation -----------------------------------------


def test_case_is_folded() -> None:
    assert clean("FREE Entry MONEY") == "free entry money"


def test_repeated_punctuation_is_removed() -> None:
    assert clean("halo!!!") == "halo"


def test_punctuation_becomes_a_space_not_nothing() -> None:
    """'end.Now' must not be glued into one token."""
    assert tokenize("end.Now") == ["end", "now"]


def test_empty_string_returns_empty() -> None:
    assert clean("") == ""
    assert tokenize("") == []


def test_whitespace_only_returns_empty() -> None:
    assert clean("   \t  \n ") == ""


def test_punctuation_only_returns_empty() -> None:
    assert clean("!!! ... ??? ---") == ""


def test_emoticon_only_returns_empty() -> None:
    assert clean(":-) :)") == ""


# --- placeholders ---------------------------------------------------------


def test_https_url_becomes_placeholder() -> None:
    assert clean("visit https://example.com/claim now") == "visit <url>"


def test_http_url_becomes_placeholder() -> None:
    assert clean("click http://bit.ly/x") == "click <url>"


def test_www_url_without_scheme_becomes_placeholder() -> None:
    assert clean("go to www.prize.com") == "go <url>"


def test_eight_digit_number_is_a_phone() -> None:
    assert clean("call 12345678") == "call <phone>"


def test_fifteen_digit_number_is_a_phone() -> None:
    assert clean("call 123456789012345") == "call <phone>"


def test_leading_zero_phone_number_is_a_phone() -> None:
    assert clean("Call 081234567890 NOW!!! http://x.co") == "call <phone> <url>"


def test_number_longer_than_fifteen_digits_is_not_a_phone() -> None:
    assert clean("ref 12345678901234567890") == "ref <num>"


def test_short_number_becomes_num_placeholder() -> None:
    assert clean("pay 500") == "pay <num>"


def test_signal_word_won_is_dropped_by_the_stopword_list() -> None:
    """Documents a deliberate trade-off rather than hiding it.

    The vendored NLTK list contains 'won', so in a scam message the amount
    survives as '<num>' but the verb does not. The list was mandated by the
    spec; the effect is recorded here so it can be discussed in the report.
    """
    assert clean("won 500") == "<num>"
    assert clean("pay 500") == "pay <num>"
    assert "won" in load_stopwords()


def test_digits_are_kept_as_a_token_not_discarded() -> None:
    """The required Phase 3 assertion: amounts must survive preprocessing."""
    result = clean("menang 1000")

    assert PLACEHOLDER_NUMBER in result
    assert result == "menang <num>"


def test_substitute_placeholders_leaves_the_order_url_phone_number() -> None:
    """URL substitution must run first, so digits inside a URL are not re-tagged."""
    result = substitute_placeholders("see http://x.co/12345678 then 081234567890 and 42")

    assert result == f"see {PLACEHOLDER_URL} then {PLACEHOLDER_PHONE} and {PLACEHOLDER_NUMBER}"


def test_placeholders_are_never_dropped_as_stopwords() -> None:
    result = clean("http://x.co 081234567890 1000")

    assert result == f"{PLACEHOLDER_URL} {PLACEHOLDER_PHONE} {PLACEHOLDER_NUMBER}"


# --- stopwords ------------------------------------------------------------


def test_stopwords_are_removed_frd_example() -> None:
    """docs/FRD.md §7 documents 'this is a test' -> 'test'."""
    assert clean("this is a test") == "test"


def test_stopword_only_input_returns_empty() -> None:
    assert clean("the and of to") == ""


def test_single_character_tokens_are_dropped() -> None:
    assert clean("u r ok") == "ok"


def test_fraud_signal_words_are_not_stopwords() -> None:
    """Words that carry the fraud signal must survive the stopword filter."""
    result = clean("click link claim prize call")

    for word in ("click", "link", "claim", "prize", "call"):
        assert word in result.split()


def test_stopword_file_is_vendored_and_loadable() -> None:
    words = load_stopwords()

    assert STOPWORDS_FILE.is_file(), "stopword list must be committed, not downloaded"
    assert len(words) > 150
    assert "the" in words
    assert "now" in words
    assert "call" not in words


def test_remove_stopwords_preserves_order() -> None:
    """Order is preserved and nothing else is dropped.

    The expected value is derived from the loaded list instead of hard-coding
    which words are stopwords, so this cannot drift from the vendored file.
    """
    tokens = ["zeta", "the", "beta", "and", "omega"]
    stopwords = load_stopwords()

    assert remove_stopwords(tokens) == [token for token in tokens if token not in stopwords]
    assert remove_stopwords(tokens) == ["zeta", "beta", "omega"]


# --- normal English and composition ---------------------------------------


def test_normal_english_message() -> None:
    result = clean("Hey, are you coming to the party tonight?")

    assert result == "hey coming party tonight"


def test_normalize_keeps_stopwords() -> None:
    """normalize() is the pre-stopword stage; only clean() has the filter."""
    assert normalize("the quick brown fox") == "the quick brown fox"


def test_url_and_phone_in_a_realistic_scam_message() -> None:
    message = (
        "Congratulations! You won a prize. Call 08001234567 or visit "
        "http://claim-now.example.com to claim your 1000 reward!"
    )

    tokens = clean(message).split()

    assert PLACEHOLDER_PHONE in tokens
    assert PLACEHOLDER_URL in tokens
    assert PLACEHOLDER_NUMBER in tokens
    assert "congratulations" in tokens
    assert "!" not in " ".join(tokens)


def test_clean_is_idempotent() -> None:
    once = clean("Click http://x.co or call 081234567890 about the 500 prize")

    assert clean(once) == once


def test_pipeline_steps_compose() -> None:
    text = "Click http://x.co or call 081234567890 about the 500 prize"

    assert normalize(text) == "click <url> or call <phone> about the <num> prize"
    assert remove_stopwords(tokenize(text)) == [
        "click",
        "<url>",
        "call",
        "<phone>",
        "<num>",
        "prize",
    ]
    assert clean(text) == "click <url> call <phone> <num> prize"


def test_clean_never_returns_leading_or_trailing_space() -> None:
    for text in ("  hi  ", "!!!hi!!!", "hi"):
        result = clean(text)
        assert result == result.strip()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Hi", "hi"),
        ("OK!!!", "ok"),
        ("   ", ""),
        (":-)", ""),
        ("1000", "<num>"),
        ("081234567890", "<phone>"),
        ("http://x.co", "<url>"),
    ],
)
def test_table_of_examples(text: str, expected: str) -> None:
    assert clean(text) == expected
