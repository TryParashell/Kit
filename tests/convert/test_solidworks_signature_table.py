# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from convert.adapters.solidworks.container import (
    SIGNATURES_BY_FILE_ID,
    SIGNATURE_FILE_IDS,
    SldprtArchive,
    _signature_table_bytes,
    _template_fields,
    build_sldprt,
    signature_triplet,
)

_EXPECTED_ENTRIES = 1000
_ENTRY_SIZE = 16
_CAD_SUFFIXES = frozenset({".SLDPRT", ".SLDASM"})
_ROOT = Path(__file__).resolve().parents[2]
_EXAMPLES = _ROOT / "examples"
_HOST_DLL = _ROOT / "re" / "binaries" / "sldmfcu.dll"
_BINARY_MANIFEST = _ROOT / "re" / "binaries" / "manifest.json"
_PROVENANCE = _ROOT / "re" / "data" / "signature_table.json"
_HOST_NAME = "sldmfcu.dll"
_BLOCK_FILE_OFFSET = 0x566C40
_KNOWN_PAIRS = {
    0xEC6E2386: ("64d80045", "ae0d4ef6", "54ce179a"),
    0x715BE98F: ("a1909b1f", "a576970f", "7a004720"),
}


def _example_documents() -> list[Path]:
    if not _EXAMPLES.is_dir():
        return []
    return sorted(
        path
        for path in _EXAMPLES.rglob("*")
        if path.is_file() and path.suffix.upper() in _CAD_SUFFIXES
    )


def _extract_from_host(blob: bytes) -> bytes:
    ids_base = _BLOCK_FILE_OFFSET
    sig_base = _BLOCK_FILE_OFFSET + _EXPECTED_ENTRIES * 4
    table = bytearray()
    for index in range(_EXPECTED_ENTRIES):
        head = ids_base + 4 * index
        table.extend(blob[head : head + 4])
        for slot in range(3):
            start = sig_base + 12 * index + 4 * slot
            table.extend(reversed(blob[start : start + 4]))
    return bytes(table)


def _recorded_host_digest() -> str:
    payload = json.loads(_BINARY_MANIFEST.read_text(encoding="utf-8"))
    entries = payload if isinstance(payload, list) else payload.get("binaries", ())
    for entry in entries:
        if isinstance(entry, dict) and entry.get("name") == _HOST_NAME:
            return str(entry["sha256"])
    raise AssertionError(f"{_HOST_NAME} is absent from {_BINARY_MANIFEST}")


def test_signature_table_resource_has_every_native_entry() -> None:
    assert len(_signature_table_bytes()) == _EXPECTED_ENTRIES * _ENTRY_SIZE
    assert len(SIGNATURES_BY_FILE_ID) == _EXPECTED_ENTRIES
    assert len(SIGNATURE_FILE_IDS) == _EXPECTED_ENTRIES
    assert len(set(SIGNATURE_FILE_IDS)) == _EXPECTED_ENTRIES
    for file_id, triplet in SIGNATURES_BY_FILE_ID.items():
        assert 0 < file_id <= 0xFFFFFFFF
        assert len(triplet) == 3
        assert all(len(value) == 4 for value in triplet)


def test_signature_table_resource_is_the_vendor_dll_array() -> None:
    assert _HOST_DLL.is_file(), _HOST_DLL
    host = _HOST_DLL.read_bytes()
    assert hashlib.sha256(host).hexdigest() == _recorded_host_digest()
    assert _signature_table_bytes() == _extract_from_host(host)


def test_signature_table_provenance_record_matches_the_resource() -> None:
    record = json.loads(_PROVENANCE.read_text(encoding="utf-8"))
    assert record["host"] == _HOST_NAME
    assert record["host_sha256"] == _recorded_host_digest()
    assert record["block_file_offset"] == _BLOCK_FILE_OFFSET
    assert record["entry_count"] == _EXPECTED_ENTRIES
    entries = record["entries"]
    assert len(entries) == _EXPECTED_ENTRIES
    blob = _signature_table_bytes()
    for entry in entries:
        head = entry["index"] * _ENTRY_SIZE
        assert blob[head : head + 4].hex() == entry["file_id"]
        assert blob[head + 4 : head + 8].hex() == entry["local"]
        assert blob[head + 8 : head + 12].hex() == entry["central"]
        assert blob[head + 12 : head + 16].hex() == entry["end"]


def test_signature_table_keeps_the_previously_hardcoded_pairs() -> None:
    for file_id, expected in _KNOWN_PAIRS.items():
        triplet = signature_triplet(file_id)
        assert triplet is not None
        assert tuple(value.hex() for value in triplet) == expected


def test_every_table_entry_round_trips_without_a_template() -> None:
    streams = {
        "Contents/SolidWorks": b"<swSolidWorks/>",
        "Contents/Config-0-Partition": b"PS\0\0body",
    }
    served = 0
    for file_id in SIGNATURE_FILE_IDS:
        blob = build_sldprt(streams, file_id=file_id)
        assert blob[:4] == file_id.to_bytes(4, "big")
        archive = SldprtArchive.from_bytes(blob)
        assert archive.file_id == file_id
        assert archive.streams == streams
        signatures, _ = _template_fields(blob, archive)
        assert signatures == SIGNATURES_BY_FILE_ID[file_id], hex(file_id)
        served += 1
    assert served == _EXPECTED_ENTRIES


def test_file_id_outside_the_table_still_refuses_to_invent_signatures() -> None:
    absent = next(
        value for value in range(1, 1 << 20) if value not in SIGNATURES_BY_FILE_ID
    )
    with pytest.raises(ValueError, match="native template"):
        build_sldprt({"Contents/SolidWorks": b"<swSolidWorks/>"}, file_id=absent)
    assert signature_triplet(absent) is None


def test_example_documents_are_covered_by_the_table() -> None:
    documents = _example_documents()
    assert documents
    covered = 0
    for path in documents:
        blob = path.read_bytes()
        archive = SldprtArchive.from_bytes(blob, path)
        signatures, _ = _template_fields(blob, archive)
        assert archive.file_id in SIGNATURES_BY_FILE_ID, path.name
        assert SIGNATURES_BY_FILE_ID[archive.file_id] == signatures, path.name
        covered += 1
    assert covered == len(documents)
