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
    DEFAULT_FILE_ID,
    DEFAULT_SIGNATURES,
    SldprtArchive,
    _template_fields,
    build_sldprt,
    signature_triplet,
)

_TABLE_ENTRIES = 1000
_CAD_SUFFIXES = frozenset({".SLDPRT", ".SLDASM"})
_ROOT = Path(__file__).resolve().parents[2]
_EXAMPLES = _ROOT / "examples"
_HOST_DLL = _ROOT / "re" / "binaries" / "sldmfcu.dll"
_BINARY_MANIFEST = _ROOT / "re" / "binaries" / "manifest.json"
_PROVENANCE = _ROOT / "re" / "data" / "signature_table.json"
_HOST_NAME = "sldmfcu.dll"
_ID_ARRAY_OFFSET = 0x566C40
_EXPECTED_ROW = ("64d80045", "ae0d4ef6", "54ce179a")
_EXPECTED_INDEX = 711


def _example_documents() -> list[Path]:
    if not _EXAMPLES.is_dir():
        return []
    return sorted(
        path
        for path in _EXAMPLES.rglob("*")
        if path.is_file() and path.suffix.upper() in _CAD_SUFFIXES
    )


def _host_rows(blob: bytes) -> list[tuple[int, tuple[str, str, str]]]:
    sig_base = _ID_ARRAY_OFFSET + _TABLE_ENTRIES * 4
    rows: list[tuple[int, tuple[str, str, str]]] = []
    for index in range(_TABLE_ENTRIES):
        head = _ID_ARRAY_OFFSET + 4 * index
        file_id = int.from_bytes(blob[head : head + 4], "big")
        magics = tuple(
            bytes(reversed(blob[start : start + 4])).hex()
            for start in (sig_base + 12 * index + 4 * slot for slot in range(3))
        )
        rows.append((file_id, magics))
    return rows


def _recorded_host_digest() -> str:
    payload = json.loads(_BINARY_MANIFEST.read_text(encoding="utf-8"))
    entries = payload if isinstance(payload, list) else payload.get("binaries", ())
    for entry in entries:
        if isinstance(entry, dict) and entry.get("name") == _HOST_NAME:
            return str(entry["sha256"])
    raise AssertionError(f"{_HOST_NAME} is absent from {_BINARY_MANIFEST}")


def test_only_one_signature_row_is_carried_in_source() -> None:
    assert len(DEFAULT_SIGNATURES) == 3
    assert all(len(value) == 4 for value in DEFAULT_SIGNATURES)
    assert tuple(value.hex() for value in DEFAULT_SIGNATURES) == _EXPECTED_ROW
    assert 0 < DEFAULT_FILE_ID <= 0xFFFFFFFF
    carried = 4 + sum(len(value) for value in DEFAULT_SIGNATURES)
    assert carried == 16


def test_the_carried_row_is_a_genuine_row_of_the_vendor_table() -> None:
    assert _HOST_DLL.is_file(), _HOST_DLL
    host = _HOST_DLL.read_bytes()
    assert hashlib.sha256(host).hexdigest() == _recorded_host_digest()
    rows = _host_rows(host)
    assert len(rows) == _TABLE_ENTRIES
    assert len({file_id for file_id, _ in rows}) == _TABLE_ENTRIES
    assert rows[_EXPECTED_INDEX] == (DEFAULT_FILE_ID, _EXPECTED_ROW)
    matches = [
        index
        for index, (file_id, magics) in enumerate(rows)
        if file_id == DEFAULT_FILE_ID and magics == _EXPECTED_ROW
    ]
    assert matches == [_EXPECTED_INDEX]


def test_provenance_record_documents_the_whole_table_and_the_carried_row() -> None:
    record = json.loads(_PROVENANCE.read_text(encoding="utf-8"))
    assert record["host"] == _HOST_NAME
    assert record["host_sha256"] == _recorded_host_digest()
    assert record["block_file_offset"] == _ID_ARRAY_OFFSET
    assert record["entry_count"] == _TABLE_ENTRIES
    assert record["shipped_rows"] == 1
    entries = record["entries"]
    assert len(entries) == _TABLE_ENTRIES
    carried = entries[_EXPECTED_INDEX]
    assert carried["file_id"] == f"{DEFAULT_FILE_ID:08x}"
    assert (carried["local"], carried["central"], carried["end"]) == _EXPECTED_ROW


def test_generated_container_uses_the_carried_row() -> None:
    streams = {
        "Contents/SolidWorks": b"<swSolidWorks/>",
        "Contents/Config-0-Partition": b"PS\0\0body",
    }
    blob = build_sldprt(streams)
    assert blob[:4] == DEFAULT_FILE_ID.to_bytes(4, "big")
    archive = SldprtArchive.from_bytes(blob)
    assert archive.file_id == DEFAULT_FILE_ID
    assert archive.streams == streams
    signatures, _ = _template_fields(blob, archive)
    assert signatures == DEFAULT_SIGNATURES


def test_file_id_without_a_carried_row_refuses_to_invent_signatures() -> None:
    absent = next(value for value in range(1, 1 << 20) if value != DEFAULT_FILE_ID)
    with pytest.raises(ValueError, match="native template"):
        build_sldprt({"Contents/SolidWorks": b"<swSolidWorks/>"}, file_id=absent)
    assert signature_triplet(absent) is None
    assert signature_triplet(DEFAULT_FILE_ID) == DEFAULT_SIGNATURES


def test_example_documents_pair_their_own_id_with_their_own_signatures() -> None:
    documents = _example_documents()
    assert documents
    host_rows = dict(_host_rows(_HOST_DLL.read_bytes()))
    covered = 0
    for path in documents:
        blob = path.read_bytes()
        archive = SldprtArchive.from_bytes(blob, path)
        signatures, _ = _template_fields(blob, archive)
        assert archive.file_id in host_rows, path.name
        recorded = host_rows[archive.file_id]
        assert tuple(value.hex() for value in signatures) == recorded, path.name
        covered += 1
    assert covered == len(documents)


def test_template_path_preserves_a_donor_id_without_a_shipped_table() -> None:
    documents = _example_documents()
    assert documents
    template = documents[0].read_bytes()
    source = SldprtArchive.from_bytes(template, documents[0])
    assert source.file_id != DEFAULT_FILE_ID or len(documents) > 1
    rebuilt = build_sldprt(source.streams, template=template)
    archive = SldprtArchive.from_bytes(rebuilt)
    assert archive.file_id == source.file_id
    expected, _ = _template_fields(template, source)
    actual, _ = _template_fields(rebuilt, archive)
    assert actual == expected
