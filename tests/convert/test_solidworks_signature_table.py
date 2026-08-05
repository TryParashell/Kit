# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path

import pytest

from convert.adapters.solidworks.container import (
    SIGNATURES_BY_FILE_ID,
    SIGNATURE_FILE_IDS,
    SldprtArchive,
    _template_fields,
    build_sldprt,
    signature_triplet,
)

_EXPECTED_ENTRIES = 1000
_CAD_SUFFIXES = frozenset({".SLDPRT", ".SLDASM"})
_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
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


def test_embedded_signature_table_has_every_native_entry() -> None:
    assert len(SIGNATURES_BY_FILE_ID) == _EXPECTED_ENTRIES
    assert len(SIGNATURE_FILE_IDS) == _EXPECTED_ENTRIES
    assert len(set(SIGNATURE_FILE_IDS)) == _EXPECTED_ENTRIES
    for file_id, triplet in SIGNATURES_BY_FILE_ID.items():
        assert 0 < file_id <= 0xFFFFFFFF
        assert len(triplet) == 3
        assert all(len(value) == 4 for value in triplet)


def test_embedded_signature_table_keeps_the_previously_hardcoded_pairs() -> None:
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


def test_example_documents_are_covered_by_the_embedded_table() -> None:
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
