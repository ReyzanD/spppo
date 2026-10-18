"""Clean the raw UCI SMS Spam Collection into a training-ready CSV.

Usage (from `backend/`):

    python training/clean_dataset.py
    cat data/dataset_report.json

Steps, each counted in the report so the numbers can be quoted in the thesis:

  1. parse the raw TSV and validate the label (`spam`/`ham` only)
  2. drop rows whose message is empty or whitespace-only
  3. drop exact duplicate (label, message) rows
  4. detect messages carrying *two different labels* and, by default, drop them
     (contradictory supervision; see the report's `label_conflicts` block)
  5. count near-duplicates (ignoring case and punctuation) but never remove them

No third-party dependency: this runs on a bare Python install.
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_RAW = DATA_DIR / "raw" / "SMSSpamCollection"
DEFAULT_OUT = DATA_DIR / "sms_spam_collection.csv"
DEFAULT_REPORT = DATA_DIR / "dataset_report.json"

VALID_LABELS = frozenset({"spam", "ham"})
MAX_EXAMPLES = 10
EXAMPLE_CHARS = 120

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Row:
    label: str
    text: str


@dataclass
class LabelConflict:
    text: str
    labels: list[str]


@dataclass
class NearDuplicateGroup:
    key: str
    count: int
    example: str


@dataclass
class CleanResult:
    rows: list[Row]
    report: dict = field(default_factory=dict)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shorten(text: str) -> str:
    return text if len(text) <= EXAMPLE_CHARS else text[: EXAMPLE_CHARS - 1] + "\u2026"


def parse_raw(path: Path) -> tuple[list[Row], int]:
    """Parse `label<TAB>message` lines.

    Splits on the *first* tab only, so a message keeps any quotes or tabs it
    contains. Returns the rows plus the number of skipped empty messages.
    """
    rows: list[Row] = []
    empty = 0

    with path.open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            line = line.rstrip("\r\n")
            if not line:
                empty += 1
                continue

            label, sep, text = line.partition("\t")
            if not sep:
                raise ValueError(
                    f"{path}:{lineno}: expected 'label<TAB>message', got {line[:60]!r}"
                )

            label = label.strip().lower()
            if label not in VALID_LABELS:
                raise ValueError(
                    f"{path}:{lineno}: unexpected label {label!r}; "
                    f"expected one of {sorted(VALID_LABELS)}"
                )

            if not text.strip():
                empty += 1
                continue

            rows.append(Row(label=label, text=text))

    return rows, empty


def normalize_for_comparison(text: str) -> str:
    """Fold case, drop punctuation/digits spacing quirks: the near-duplicate key."""
    return _NON_ALNUM.sub(" ", text.lower()).strip()


def remove_exact_duplicates(rows: list[Row]) -> tuple[list[Row], int]:
    """Keep the first occurrence of each (label, message) pair."""
    seen: set[tuple[str, str]] = set()
    kept: list[Row] = []
    for row in rows:
        key = (row.label, row.text)
        if key in seen:
            continue
        seen.add(key)
        kept.append(row)
    return kept, len(rows) - len(kept)


def find_label_conflicts(rows: list[Row]) -> list[LabelConflict]:
    """Messages that appear with more than one label."""
    by_text: dict[str, set[str]] = {}
    for row in rows:
        by_text.setdefault(row.text, set()).add(row.label)

    conflicts = [
        LabelConflict(text=text, labels=sorted(labels))
        for text, labels in by_text.items()
        if len(labels) > 1
    ]
    conflicts.sort(key=lambda c: c.text)
    return conflicts


def drop_conflicts(rows: list[Row], conflicts: list[LabelConflict]) -> list[Row]:
    conflicted = {conflict.text for conflict in conflicts}
    return [row for row in rows if row.text not in conflicted]


def find_near_duplicates(rows: list[Row]) -> tuple[list[NearDuplicateGroup], int]:
    """Group messages that match once case and punctuation are ignored.

    Returns the groups plus the number of messages skipped because they contain
    no letters or digits at all (e.g. ":)"): those all collapse to the same key
    and are not meaningful near-duplicates of each other.
    """
    variants: dict[str, list[str]] = {}
    skipped = 0
    for row in rows:
        key = normalize_for_comparison(row.text)
        if not key:
            skipped += 1
            continue
        variants.setdefault(key, []).append(row.text)

    groups = [
        NearDuplicateGroup(
            key=key,
            count=len(texts),
            # Shortest original wording: readable and an actual message, not the key.
            example=min(texts, key=lambda text: (len(text), text)),
        )
        for key, texts in variants.items()
        if len(texts) > 1
    ]
    groups.sort(key=lambda group: (-group.count, group.key))
    return groups, skipped


def clean(
    raw_path: Path = DEFAULT_RAW,
    *,
    drop_label_conflicts: bool = True,
) -> CleanResult:
    """Run the whole cleaning pipeline and build the report."""
    rows, empty_removed = parse_raw(raw_path)
    raw_count = len(rows) + empty_removed

    deduped, duplicates_removed = remove_exact_duplicates(rows)
    conflicts = find_label_conflicts(deduped)
    final_rows = drop_conflicts(deduped, conflicts) if drop_label_conflicts else deduped

    near_groups, near_skipped = find_near_duplicates(final_rows)
    labels = Counter(row.label for row in final_rows)

    report = {
        "source": {
            "raw_file": str(raw_path),
            "raw_sha256": sha256_of(raw_path),
        },
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "raw_count": raw_count,
        "empty_removed": empty_removed,
        "duplicates_removed": duplicates_removed,
        "after_dedup": len(deduped),
        "unique_message_texts": len({row.text for row in deduped}),
        "label_conflicts": {
            "count": len(conflicts),
            "dropped": drop_label_conflicts,
            "examples": [
                {"text": shorten(c.text), "labels": c.labels} for c in conflicts[:MAX_EXAMPLES]
            ],
        },
        "final_count": len(final_rows),
        "spam_count": labels["spam"],
        "ham_count": labels["ham"],
        "spam_ratio": round(labels["spam"] / len(final_rows), 4) if final_rows else 0.0,
        "near_duplicates": {
            "groups": len(near_groups),
            "extra_rows": sum(group.count - 1 for group in near_groups),
            "removed": False,
            "ignored_non_alphanumeric": near_skipped,
            "examples": [
                {"count": group.count, "example": shorten(group.example)}
                for group in near_groups[:MAX_EXAMPLES]
            ],
        },
    }
    return CleanResult(rows=final_rows, report=report)


def write_csv(rows: list[Row], path: Path) -> Path:
    """Write `label,teks_pesan` — the column names used in docs/ERD.md.

    Uses the csv module so messages containing commas, quotes or newlines are
    escaped correctly instead of corrupting the file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["label", "teks_pesan"])
        writer.writerows((row.label, row.text) for row in rows)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean the raw SMS Spam Collection.")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="raw TSV path")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="cleaned CSV path")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="report JSON path")
    parser.add_argument(
        "--keep-label-conflicts",
        action="store_true",
        help="keep messages that appear under two different labels",
    )
    args = parser.parse_args(argv)

    if not args.raw.is_file():
        print(
            f"Raw file not found: {args.raw}\nRun training/download_dataset.py first.",
            file=sys.stderr,
        )
        return 1

    result = clean(args.raw, drop_label_conflicts=not args.keep_label_conflicts)
    report = result.report

    write_csv(result.rows, args.out)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"raw                             {report['raw_count']:>6}")
    print(f"  empty removed                 {report['empty_removed']:>6}")
    print(f"  duplicates removed            {report['duplicates_removed']:>6}")
    print(f"after dedup                     {report['after_dedup']:>6}")
    print(f"  label conflicts               {report['label_conflicts']['count']:>6}", end="")
    print(" (dropped)" if report["label_conflicts"]["dropped"] else " (kept)")
    print(f"final                           {report['final_count']:>6}")
    print(f"  spam / ham                    {report['spam_count']} / {report['ham_count']}")
    print(f"  spam ratio                    {report['spam_ratio']:.2%}")
    print(f"near-duplicate groups           {report['near_duplicates']['groups']:>6} (not removed)")
    print(f"\nWrote {args.out} and {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
