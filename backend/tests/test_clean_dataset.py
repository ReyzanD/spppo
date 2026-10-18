"""Unit tests for training/clean_dataset.py using synthetic data.

No network and no real dataset: CI must not depend on UCI being reachable.
"""

import csv
from pathlib import Path

import pytest
from training.clean_dataset import (
    Row,
    clean,
    drop_conflicts,
    find_label_conflicts,
    find_near_duplicates,
    normalize_for_comparison,
    parse_raw,
    remove_exact_duplicates,
    write_csv,
)


def write_raw(tmp_path: Path, lines: list[str]) -> Path:
    path = tmp_path / "SMSSpamCollection"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_parse_raw_reads_label_and_text(tmp_path: Path) -> None:
    raw = write_raw(tmp_path, ["ham\tHello there", "SPAM\tYou won a prize"])

    rows, empty = parse_raw(raw)

    assert rows == [Row("ham", "Hello there"), Row("spam", "You won a prize")]
    assert empty == 0


def test_parse_raw_keeps_quotes_and_inner_tabs(tmp_path: Path) -> None:
    raw = write_raw(tmp_path, ['ham\t"FreeMsg" now\twith a tab'])

    rows, _ = parse_raw(raw)

    assert rows[0].text == '"FreeMsg" now\twith a tab'


def test_parse_raw_rejects_unknown_label(tmp_path: Path) -> None:
    raw = write_raw(tmp_path, ["ham\tok", "phishing\tbad label"])

    with pytest.raises(ValueError, match="line 2|:2:"):
        parse_raw(raw)


def test_parse_raw_rejects_missing_tab(tmp_path: Path) -> None:
    raw = write_raw(tmp_path, ["ham\tonly-field-one", "no tab here"])

    with pytest.raises(ValueError, match="expected"):
        parse_raw(raw)


def test_parse_raw_skips_and_counts_empty_messages(tmp_path: Path) -> None:
    raw = write_raw(tmp_path, ["ham\treal message", "spam\t   ", "ham\tonly whitespace "])

    rows, empty = parse_raw(raw)

    assert rows == [Row("ham", "real message"), Row("ham", "only whitespace ")]
    assert empty == 1


def test_remove_exact_duplicates() -> None:
    rows = [Row("ham", "a"), Row("ham", "a"), Row("spam", "a"), Row("ham", "b")]

    kept, removed = remove_exact_duplicates(rows)

    assert kept == [Row("ham", "a"), Row("spam", "a"), Row("ham", "b")]
    assert removed == 1


def test_find_label_conflicts_detects_same_text_two_labels() -> None:
    rows = [Row("spam", "same text"), Row("ham", "same text"), Row("ham", "unique")]

    conflicts = find_label_conflicts(rows)

    assert len(conflicts) == 1
    assert conflicts[0].labels == ["ham", "spam"]


def test_drop_conflicts_removes_every_copy() -> None:
    rows = [Row("spam", "same text"), Row("ham", "same text"), Row("ham", "unique")]

    remaining = drop_conflicts(rows, find_label_conflicts(rows))

    assert remaining == [Row("ham", "unique")]


def test_normalize_ignores_case_and_punctuation() -> None:
    assert normalize_for_comparison("FREE entry!!!") == normalize_for_comparison("free   entry")


def test_find_near_duplicates_counts_extra_rows() -> None:
    rows = [Row("ham", "Free entry!"), Row("ham", "FREE entry"), Row("spam", "other")]

    groups, skipped = find_near_duplicates(rows)

    assert len(groups) == 1
    assert groups[0].count == 2
    assert sum(group.count - 1 for group in groups) == 1
    assert skipped == 0


def test_near_duplicate_example_is_an_original_message() -> None:
    """The example must show a real message, not the normalised grouping key."""
    rows = [Row("ham", "free entry"), Row("ham", "FREE   entry!!")]

    groups, _ = find_near_duplicates(rows)

    assert groups[0].key == "free entry"
    assert groups[0].example in {"free entry", "FREE   entry!!"}


def test_near_duplicates_skip_messages_without_letters_or_digits() -> None:
    """
    ':)' and ':-) :-)' both normalise to '', which is not a meaningful group.
    They must be counted separately rather than reported as duplicates.
    """
    rows = [Row("ham", ":)"), Row("ham", ":-) :-)"), Row("spam", "ok"), Row("ham", "OK!")]

    groups, skipped = find_near_duplicates(rows)

    assert skipped == 2
    assert len(groups) == 1
    assert groups[0].count == 2
    assert all(group.key for group in groups)


def test_clean_drops_conflicts_by_default(tmp_path: Path) -> None:
    raw = write_raw(
        tmp_path,
        ["spam\tsame text", "ham\tsame text", "ham\tkeep me", "ham\tkeep me", "spam\tdrop empty"],
    )

    result = clean(raw)

    assert result.report["raw_count"] == 5
    assert result.report["duplicates_removed"] == 1
    assert result.report["after_dedup"] == 4
    assert result.report["label_conflicts"]["count"] == 1
    assert result.report["label_conflicts"]["dropped"] is True
    assert result.report["final_count"] == 2
    # Both surviving rows are unrelated to the conflict; only "same text" is dropped.
    assert [row.text for row in result.rows] == ["keep me", "drop empty"]
    assert result.report["spam_count"] == 1
    assert result.report["ham_count"] == 1


def test_clean_can_keep_conflicts(tmp_path: Path) -> None:
    raw = write_raw(tmp_path, ["spam\tsame text", "ham\tsame text", "ham\tkeep me"])

    result = clean(raw, drop_label_conflicts=False)

    assert result.report["final_count"] == 3
    assert result.report["label_conflicts"]["dropped"] is False


def test_report_contains_plan_required_keys(tmp_path: Path) -> None:
    """docs/PLAN.md Phase 2 exit criteria name these keys explicitly."""
    raw = write_raw(tmp_path, ["ham\ta", "spam\tb"])

    report = clean(raw).report

    for key in ("raw_count", "after_dedup", "spam_count", "ham_count", "near_duplicates"):
        assert key in report
    assert report["spam_count"] == 1
    assert report["ham_count"] == 1
    assert report["spam_ratio"] == 0.5


def test_write_csv_round_trips_commas_and_quotes(tmp_path: Path) -> None:
    rows = [
        Row("spam", 'Call 081234567890, you "won" a prize'),
        Row("ham", "plain"),
        Row("ham", "multi\nline"),
    ]
    out = tmp_path / "clean.csv"

    write_csv(rows, out)

    with out.open(newline="", encoding="utf-8") as handle:
        parsed = list(csv.reader(handle))

    assert parsed[0] == ["label", "teks_pesan"]
    assert [Row(label, text) for label, text in parsed[1:]] == rows


def test_clean_is_deterministic(tmp_path: Path) -> None:
    raw = write_raw(tmp_path, ["ham\ta", "spam\tb", "spam\tb", "ham\tc"])

    first = clean(raw).report
    second = clean(raw).report

    for key in ("raw_count", "after_dedup", "final_count", "spam_count", "ham_count"):
        assert first[key] == second[key]
