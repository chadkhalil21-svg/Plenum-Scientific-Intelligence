#!/usr/bin/env python3
"""Fail closed if browser code changes without contemporaneous progress accounting."""
import re
import subprocess
import sys
from pathlib import Path

LEDGER = "docs/COMPUTER_BROWSER_PROGRESS.md"


def browser_path(path: str) -> bool:
    return (
        path.startswith("services/computer_browser/")
        or path.startswith("src/plenum_ai/browser_")
        or path.startswith("src/plenum_ai/public_form_browser")
        or path.startswith("src/plenum_ai/chat_browser")
        or (path.startswith(".github/workflows/") and "browser" in path)
        or path.startswith("tests/test_browser_")
        or path.startswith("tests/test_chat_browser")
    )


def validate_document() -> None:
    text = Path(LEDGER).read_text(encoding="utf-8")
    mandatory = (
        "# Plenum Computer Browser: progress and acceptance ledger",
        "## Standing mandate",
        "## Current verified capabilities and limitations",
        "## Remaining completion gates",
        "## Rules for every browser change",
        "## Change log",
    )
    if any(section not in text for section in mandatory):
        raise SystemExit("Browser ledger missing required continuity sections.")
    if not re.search(r"Updated: 20\d\d-\d\d-\d\d", text):
        raise SystemExit("Browser ledger missing update date.")
    if "NOT ACHIEVED" not in text:
        raise SystemExit("Do not silently remove current parity status.")


def check_diff(base: str, head: str) -> None:
    completed = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        capture_output=True, text=True, check=True,
    )
    changed = set(completed.stdout.splitlines())
    if any(browser_path(name) for name in changed) and LEDGER not in changed:
        raise SystemExit(
            f"Browser code/deployment changed without updating {LEDGER} in this PR."
        )


if __name__ == "__main__":
    validate_document()
    if len(sys.argv) == 3:
        check_diff(sys.argv[1], sys.argv[2])
    elif len(sys.argv) != 1:
        raise SystemExit("Usage: check_browser_progress.py [BASE_SHA HEAD_SHA]")
    print("Browser progress ledger structure and change accounting: PASS")
