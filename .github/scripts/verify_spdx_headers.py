# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify every in-scope changed file still carries an intact SPDX header.

The canonical header text lives in ``HEADER_NOTICE`` at the repository root.
For every added, modified, copied, or renamed file between two git refs,
this script re-renders the expected header for that file's comment style,
hashes it, and compares the hash against a hash of whatever actually sits
at the top of the file. Any difference -- missing, truncated, reordered,
edited, or relocated header -- is reported as a failure.

Usage:
    verify_spdx_headers.py --base <git-ref> --head <git-ref>

Exit status:
    0  every in-scope file in the diff carries the exact header.
    1  one or more files fail the check (see stdout for details).
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
HEADER_NOTICE_PATH = REPO_ROOT / "HEADER_NOTICE"

# Paths under these prefixes are entirely out of scope for the header
# requirement (matches .kiro/steering/spdx-header.md).
EXEMPT_DIR_PREFIXES = (".kiro/", "examples/")

# Individual paths that are exempt: HEADER_NOTICE is the canonical,
# uncommented source text the header is rendered from, not a file that
# itself carries the commented header block.
EXEMPT_PATHS = {"HEADER_NOTICE"}

# Extension -> single-line comment prefix.
LINE_COMMENT_EXTENSIONS = {
    "#": {
        ".py", ".pyi", ".sh", ".bash", ".zsh",
        ".yml", ".yaml", ".toml", ".lock",
        ".cfg", ".ini", ".conf", ".gitattributes",
    },
    "//": {
        ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
        ".c", ".h", ".cc", ".cpp", ".hpp", ".java",
        ".go", ".rs", ".swift", ".kt", ".cs",
    },
}

# Extensions rendered with a block comment.
BLOCK_COMMENT_EXTENSIONS = {".md", ".markdown", ".html", ".htm", ".xml", ".svg"}

# Filenames (no reliable extension) with a known comment style.
SPECIAL_FILENAME_STYLES = {
    "LICENSE": "block",
    ".gitignore": "#",
    "Dockerfile": "#",
    "Makefile": "#",
}

# Formats with no comment syntax at all: structurally cannot carry the
# header, exactly like a binary file has "nowhere to put it".
NO_COMMENT_EXTENSIONS = {".json"}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".sldprt", ".sldasm", ".catpart", ".catproduct", ".f3d", ".f3z",
    ".x_t", ".sat", ".step", ".stp", ".iges", ".igs", ".stl",
    ".zip", ".7z", ".whl",
}


def load_canonical_lines() -> list[str]:
    text = HEADER_NOTICE_PATH.read_text(encoding="utf-8")
    return text.splitlines()


def render_line_style(canonical: list[str], prefix: str) -> list[str]:
    return [prefix if line == "" else f"{prefix} {line}" for line in canonical]


def render_block_style(canonical: list[str]) -> list[str]:
    return ["<!--", *canonical, "-->"]


def sha256_of(lines: list[str]) -> str:
    joined = "\n".join(lines) + "\n"
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def is_exempt_path(rel_path: str) -> bool:
    if rel_path in EXEMPT_PATHS:
        return True
    return any(rel_path.startswith(prefix) for prefix in EXEMPT_DIR_PREFIXES)


def style_for(path: pathlib.Path) -> str | None:
    """Return '#' / '//' / 'block' / None (exempt) / 'unknown'."""
    if path.name in SPECIAL_FILENAME_STYLES:
        return SPECIAL_FILENAME_STYLES[path.name]
    ext = path.suffix.lower()
    if ext in NO_COMMENT_EXTENSIONS or ext in BINARY_EXTENSIONS:
        return None
    if ext in BLOCK_COMMENT_EXTENSIONS:
        return "block"
    for prefix, exts in LINE_COMMENT_EXTENSIONS.items():
        if ext in exts:
            return prefix
    return "unknown"


def read_lines(path: pathlib.Path) -> list[str] | None:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return None


def leading_offset(lines: list[str]) -> int:
    if lines and lines[0].startswith("#!"):
        return 1
    return 0


def check_file(path: pathlib.Path, canonical: list[str]) -> tuple[bool, str]:
    """Return (ok, reason)."""
    style = style_for(path)
    if style is None:
        return True, "exempt (no comment syntax available)"

    lines = read_lines(path)
    if lines is None:
        return True, "exempt (not readable as UTF-8 text; treated as binary)"

    offset = leading_offset(lines)

    candidates: list[list[str]] = []
    if style == "block":
        candidates.append(render_block_style(canonical))
    elif style == "unknown":
        candidates.append(render_line_style(canonical, "#"))
        candidates.append(render_block_style(canonical))
    else:
        candidates.append(render_line_style(canonical, style))

    expected_hashes = {sha256_of(c): c for c in candidates}
    for expected_hash, expected in expected_hashes.items():
        actual = lines[offset : offset + len(expected)]
        actual_hash = sha256_of(actual)
        if actual_hash == expected_hash:
            return True, f"header hash OK ({actual_hash[:12]})"

    # Nothing matched: report the closest candidate for a useful diagnostic.
    expected = candidates[0]
    actual = lines[offset : offset + len(expected)]
    expected_hash = sha256_of(expected)
    actual_hash = sha256_of(actual)
    if len(actual) < len(expected):
        return False, (
            f"header missing or truncated "
            f"(expected sha256={expected_hash[:12]}, got sha256={actual_hash[:12]})"
        )
    return False, (
        f"header modified/tampered "
        f"(expected sha256={expected_hash[:12]}, got sha256={actual_hash[:12]})"
    )


def diff_files(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-status", "-M", "--diff-filter=ACMR", f"{base}", f"{head}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    paths = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") or status.startswith("C"):
            # rename/copy: status, old-path, new-path
            paths.append(parts[-1])
        else:
            paths.append(parts[-1])
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Base git ref/sha to diff from")
    parser.add_argument("--head", required=True, help="Head git ref/sha to diff to")
    args = parser.parse_args()

    canonical = load_canonical_lines()
    changed = diff_files(args.base, args.head)

    failures: list[tuple[str, str]] = []
    checked = 0
    for rel_path in changed:
        if is_exempt_path(rel_path):
            continue
        path = REPO_ROOT / rel_path
        if not path.is_file():
            continue
        checked += 1
        ok, reason = check_file(path, canonical)
        if not ok:
            failures.append((rel_path, reason))
        print(f"{'OK ' if ok else 'FAIL'} {rel_path}: {reason}")

    print(f"\nChecked {checked} in-scope file(s); {len(failures)} failure(s).")
    if failures:
        print(
            "\nOne or more changed files are missing, or have had tampered with, "
            "their required SPDX header (see HEADER_NOTICE and "
            ".kiro/steering/spdx-header.md).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
