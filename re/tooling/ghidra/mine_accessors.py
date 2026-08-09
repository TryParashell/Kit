# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse
import json
import re
from typing import Dict, Iterable, List, Optional, Tuple

FUNCTION_RE = re.compile(r"^=== FUNCTION (.+)$")
ADDRESS_RE = re.compile(r"^=== ADDRESS ([0-9a-fA-F]+)$")
MANGLED_RE = re.compile(r"\?([A-Za-z0-9_]+)@([A-Za-z0-9_]+)@@")
GET_RE = re.compile(
    r"return\s+\*\(([A-Za-z0-9_ ]+?)\s*\*+\)\s*\(this\s*\+\s*(?:\(longlong\)"
    r"(param_\d+)\s*\*\s*(\d+)\s*\+\s*)?(0x[0-9a-fA-F]+|\d+)\s*\)\s*;"
)
GET_INDEX_FIRST_RE = re.compile(
    r"return\s+\*\(([A-Za-z0-9_ ]+?)\s*\*+\)\s*\(\(longlong\)(param_\d+)\s*\*\s*"
    r"(\d+)\s*\+\s*this\s*\+\s*(0x[0-9a-fA-F]+|\d+)\s*\)\s*;"
)
SET_RE = re.compile(
    r"\*\(([A-Za-z0-9_ ]+?)\s*\*+\)\s*\(this\s*\+\s*(?:\(longlong\)(param_\d+)"
    r"\s*\*\s*(\d+)\s*\+\s*)?(0x[0-9a-fA-F]+|\d+)\s*\)\s*=\s*param_\d+\s*;"
)
ADDR_OF_RE = re.compile(r"return\s+this\s*\+\s*(0x[0-9a-fA-F]+|\d+)\s*;")
DEREF_RE = re.compile(
    r"\*\(([A-Za-z0-9_ ]+?)\s*\*+\)\s*\((?:\(longlong\)(param_\d+)\s*\*\s*(\d+)"
    r"\s*\+\s*)?this\s*\+\s*(?:\(longlong\)(param_\d+)\s*\*\s*(\d+)\s*\+\s*)?"
    r"(0x[0-9a-fA-F]+|\d+)\s*\)"
)

WIDTHS = {
    "char": 1,
    "uchar": 1,
    "byte": 1,
    "bool": 1,
    "undefined1": 1,
    "short": 2,
    "ushort": 2,
    "undefined2": 2,
    "wchar_t": 2,
    "int": 4,
    "uint": 4,
    "long": 4,
    "ulong": 4,
    "float": 4,
    "undefined4": 4,
    "double": 8,
    "longlong": 8,
    "ulonglong": 8,
    "undefined8": 8,
    "int64": 8,
    "size_t": 8,
}


def width_of(ctype: str) -> Tuple[int, str]:
    text = ctype.strip()
    if text in WIDTHS:
        return WIDTHS[text], text
    parts = text.split()
    if parts and parts[-1] in WIDTHS:
        return WIDTHS[parts[-1]], text
    return 8, text


def parse_int(text: str) -> int:
    return int(text, 16) if text.lower().startswith("0x") else int(text)


def iter_blocks(text: str) -> Iterable[Tuple[str, str, str]]:
    lines = text.splitlines()
    starts: List[int] = []
    for i, line in enumerate(lines):
        if line.startswith("=== FUNCTION "):
            starts.append(i)
    starts.append(len(lines))
    for k in range(len(starts) - 1):
        chunk = lines[starts[k] : starts[k + 1]]
        name = FUNCTION_RE.match(chunk[0]).group(1).strip()
        address = ""
        for line in chunk[:6]:
            match = ADDRESS_RE.match(line)
            if match:
                address = match.group(1)
                break
        yield name, address, "\n".join(chunk)


def classify(body: str) -> Optional[dict]:
    match = GET_INDEX_FIRST_RE.search(body)
    if match:
        width, ctype = width_of(match.group(1))
        return {
            "kind": "get",
            "width": width,
            "ctype": ctype,
            "stride": int(match.group(3)),
            "offset": parse_int(match.group(4)),
        }
    match = GET_RE.search(body)
    if match:
        width, ctype = width_of(match.group(1))
        return {
            "kind": "get",
            "width": width,
            "ctype": ctype,
            "stride": int(match.group(3)) if match.group(3) else 0,
            "offset": parse_int(match.group(4)),
        }
    match = SET_RE.search(body)
    if match:
        width, ctype = width_of(match.group(1))
        return {
            "kind": "set",
            "width": width,
            "ctype": ctype,
            "stride": int(match.group(3)) if match.group(3) else 0,
            "offset": parse_int(match.group(4)),
        }
    match = ADDR_OF_RE.search(body)
    if match:
        return {
            "kind": "ref",
            "width": 0,
            "ctype": "member",
            "stride": 0,
            "offset": parse_int(match.group(1)),
        }
    hits = DEREF_RE.findall(strip_comments(body))
    seen: Dict[int, dict] = {}
    for ctype, pre_var, pre_stride, post_var, post_stride, offset in hits:
        width, resolved = width_of(ctype)
        value = parse_int(offset)
        stride = int(pre_stride or post_stride or 0)
        seen.setdefault(
            value,
            {
                "kind": "get_derived",
                "width": width,
                "ctype": resolved,
                "stride": stride,
                "offset": value,
            },
        )
    if len(seen) == 1:
        return next(iter(seen.values()))
    return None


def strip_comments(body: str) -> str:
    return re.sub(r"/\*.*?\*/", " ", body, flags=re.S)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dumps", nargs="+")
    parser.add_argument("--classes", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    wanted = set()
    for line in open(args.classes, encoding="utf-8"):
        text = line.strip()
        if not text:
            continue
        parts = text.split(None, 1)
        wanted.add(parts[1].strip() if len(parts) == 2 and parts[0].isdigit() else text)
    result: Dict[str, Dict[str, dict]] = {}
    scanned = 0
    matched = 0
    for path in args.dumps:
        text = open(path, encoding="utf-8", errors="replace").read()
        for name, address, body in iter_blocks(text):
            scanned += 1
            info = classify(body)
            if info is None:
                continue
            matched += 1
            owners: List[Tuple[str, str]] = []
            if "::" in name:
                cls, member = name.split("::", 1)
                owners.append((cls, member))
            for member, cls in MANGLED_RE.findall(body):
                owners.append((cls, member))
            for cls, member in owners:
                if cls not in wanted:
                    continue
                entry = dict(info)
                entry["address"] = address
                entry["source"] = path.replace("\\", "/").rsplit("/", 1)[-1]
                bucket = result.setdefault(cls, {})
                previous = bucket.get(member)
                if previous is not None and previous["offset"] != entry["offset"]:
                    entry["conflicts_with"] = previous["offset"]
                bucket[member] = entry
    payload = {
        cls: dict(sorted(members.items()))
        for cls, members in sorted(result.items())
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    total = sum(len(v) for v in payload.values())
    print(
        f"blocks={scanned} recognised={matched} classes={len(payload)} accessors={total}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
