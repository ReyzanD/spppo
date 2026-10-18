"""Download and verify the UCI SMS Spam Collection.

Usage (from `backend/`):

    python training/download_dataset.py            # download if missing
    python training/download_dataset.py --force    # re-download regardless

The archive is verified against a pinned SHA-256 before anything is extracted,
and the extracted TSV is verified too, so a corrupted download fails loudly
instead of silently poisoning the model (see docs/PLAN.md Phase 2).
"""

import argparse
import hashlib
import os
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
SUMS_FILE = DATA_DIR / "SHA256SUMS"

SOURCE_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"

# Computed from the artefact served by SOURCE_URL on 2026-10-17. UCI has not
# changed this file since 2011, so a mismatch means a bad download or a
# substituted file, not a new revision.
ARCHIVE_NAME = "smsspamcollection.zip"
ARCHIVE_SHA256 = "1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3"

# Members we care about, with the checksum of the extracted TSV.
EXTRACTED = {
    "SMSSpamCollection": "7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d",
    "readme": None,  # documented but not checksum-pinned
}

CHUNK_SIZE = 64 * 1024
TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    sha256: str
    downloaded: bool


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 of a file, reading it in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, destination: Path) -> Path:
    """Stream `url` to `destination` atomically (`.part` then rename)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "penipuan-detection/0.1"})

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            with partial.open("wb") as out:
                while chunk := response.read(CHUNK_SIZE):
                    out.write(chunk)
        os.replace(partial, destination)
    except BaseException:
        # Never leave a half-written archive behind for the next run to trust.
        partial.unlink(missing_ok=True)
        raise

    return destination


def ensure_archive(force: bool = False) -> DownloadResult:
    """Download the archive unless a checksum-matching copy is already present."""
    archive_path = RAW_DIR / ARCHIVE_NAME

    if archive_path.is_file() and not force:
        actual = sha256_of(archive_path)
        if actual == ARCHIVE_SHA256:
            return DownloadResult(archive_path, actual, downloaded=False)
        print(f"Checksum mismatch on existing {archive_path}; re-downloading.")

    download_file(SOURCE_URL, archive_path)
    actual = sha256_of(archive_path)
    if actual != ARCHIVE_SHA256:
        raise SystemExit(
            "Downloaded archive checksum mismatch.\n"
            f"  expected {ARCHIVE_SHA256}\n"
            f"  actual   {actual}\n"
            f"Refusing to use {archive_path}. Delete it and retry, or review SOURCE_URL."
        )

    return DownloadResult(archive_path, actual, downloaded=True)


def extract_members(archive: Path, members: dict[str, str | None]) -> dict[str, Path]:
    """Extract the named members into RAW_DIR and verify each pinned checksum.

    Member names come from the module constant, never from the archive listing,
    so a malicious zip cannot choose where files land.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    with zipfile.ZipFile(archive) as zf:
        available = set(zf.namelist())
        for member, expected in members.items():
            if member not in available:
                raise SystemExit(
                    f"{member!r} not found in {archive}. Contents: {sorted(available)}"
                )

            target = RAW_DIR / member
            with zf.open(member) as source, target.open("wb") as out:
                out.write(source.read())

            if expected is not None:
                actual = sha256_of(target)
                if actual != expected:
                    raise SystemExit(
                        f"Extracted {member} checksum mismatch.\n  expected {expected}\n"
                        f"  actual   {actual}"
                    )
            written[member] = target

    return written


def write_sums(archive_sha: str, extracted: dict[str, Path]) -> None:
    """Record the checksums so a later run can spot a changed source."""
    lines = [f"{archive_sha}  {ARCHIVE_NAME}"]
    for name, path in extracted.items():
        lines.append(f"{sha256_of(path)}  {name}")
    SUMS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download the UCI SMS Spam Collection.")
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    args = parser.parse_args(argv)

    result = ensure_archive(force=args.force)
    status = "downloaded" if result.downloaded else "already present, checksum OK"
    print(f"Archive: {result.path} ({status})")
    print(f"  sha256 {result.sha256}")

    extracted = extract_members(result.path, EXTRACTED)
    write_sums(result.sha256, extracted)

    for name, path in extracted.items():
        print(f"  {name}: {path} ({path.stat().st_size} bytes)")
    print(f"Checksums written to {SUMS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
