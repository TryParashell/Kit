# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import struct

import pytest

from convert.adapters.solidworks import SldprtArchive, build_sldprt
from convert.adapters.solidworks.container.Container import container_signatures

_MARKER = bytes.fromhex("140006000800")
_LOCAL_SIGNATURE = bytes.fromhex("a1909b1f")
_CENTRAL_SIGNATURE = bytes.fromhex("a576970f")
_END_SIGNATURE = bytes.fromhex("7a004720")
_VENDOR_FILE_ID = 0x715BE98F
_VENDOR_SIGNATURES = (_LOCAL_SIGNATURE, _CENTRAL_SIGNATURE, _END_SIGNATURE)


def _decoded_name(value: bytes) -> str:
    return bytes((byte >> 4) | ((byte & 0x0F) << 4) for byte in value).decode("utf-8")


def test_generated_container_has_complete_native_directory() -> None:
    streams = (
        ("Contents/Config-0-Partition", b"PS\0\0native body"),
        ("swXmlContents/KeyWords", b"<?xml version='1.0'?><KeyWords/>"),
        ("Contents/OleItems", b""),
    )
    blob = build_sldprt(streams, file_id=_VENDOR_FILE_ID, signatures=_VENDOR_SIGNATURES)
    archive = SldprtArchive.from_bytes(blob)
    assert archive.file_id == _VENDOR_FILE_ID
    assert archive.streams == dict(streams)
    end_offset = len(blob) - 22
    (
        disk_number,
        directory_disk,
        disk_entries,
        total_entries,
        directory_size,
        directory_offset,
        comment_size,
    ) = struct.unpack_from("<HHHHIIH", blob, end_offset + 4)
    assert blob[end_offset : end_offset + 4] == _END_SIGNATURE
    assert disk_number == 0
    assert directory_disk == 0
    assert disk_entries == len(streams)
    assert total_entries == len(streams)
    assert comment_size == 0
    assert 8 + directory_offset + directory_size == end_offset
    cursor = 8 + directory_offset
    timestamps = set()
    for expected_name, expected_data in streams:
        assert blob[cursor : cursor + 4] == _CENTRAL_SIGNATURE
        assert blob[cursor + 6 : cursor + 12] == _MARKER
        type_id, crc32_value, compressed_size, size = struct.unpack_from(
            "<IIII", blob, cursor + 12
        )
        timestamps.add(type_id)
        name_size, extra_size = struct.unpack_from("<HH", blob, cursor + 28)
        (
            entry_comment_size,
            entry_disk,
            internal_attributes,
            external_attributes,
            local_offset,
        ) = struct.unpack_from("<HHHII", blob, cursor + 32)
        encoded_name = blob[cursor + 46 : cursor + 46 + name_size]
        assert _decoded_name(encoded_name) == expected_name
        assert extra_size == 0
        assert entry_comment_size == 0
        assert entry_disk == 0
        assert internal_attributes == int(expected_name.startswith("swXmlContents/"))
        assert external_attributes == 0
        local_cursor = 8 + local_offset
        assert blob[local_cursor : local_cursor + 4] == _LOCAL_SIGNATURE
        assert blob[local_cursor + 4 : local_cursor + 10] == _MARKER
        assert struct.unpack_from("<I", blob, local_cursor + 10)[0] == type_id
        assert struct.unpack_from("<I", blob, local_cursor + 14)[0] == crc32_value
        assert struct.unpack_from("<I", blob, local_cursor + 18)[0] == compressed_size
        assert struct.unpack_from("<I", blob, local_cursor + 22)[0] == size
        assert struct.unpack_from("<H", blob, local_cursor + 26)[0] == name_size
        assert struct.unpack_from("<H", blob, local_cursor + 28)[0] == 0
        assert (
            _decoded_name(blob[local_cursor + 30 : local_cursor + 30 + name_size])
            == expected_name
        )
        assert archive.require(expected_name) == expected_data
        cursor += 46 + name_size
    assert cursor == end_offset
    assert timestamps == {0x1C34D281}


def test_generated_container_is_deterministic() -> None:
    streams = {
        "Contents/SolidWorks": b"<swSolidWorks/>",
        "Contents/Config-0-Partition": b"PS\0\0body",
    }
    assert build_sldprt(streams) == build_sldprt(streams)


def test_generated_container_uses_coherent_source_less_identity() -> None:
    blob = build_sldprt({"Contents/SolidWorks": b"<swSolidWorks/>"})
    assert blob[:8] == bytes.fromhex("ec6e238600000004")
    archive = SldprtArchive.from_bytes(blob)
    record = archive.records[0]
    assert blob[record.offset - 4 : record.offset] == bytes.fromhex("64d80045")
    assert blob[-22:-18] == bytes.fromhex("54ce179a")


def test_generated_container_uses_native_header_stream_type_ids() -> None:
    blob = build_sldprt(
        {
            "Header2": b"header",
            "Preview": b"preview",
            "Contents/SolidWorks": b"model",
        }
    )
    archive = SldprtArchive.from_bytes(blob)
    type_ids = {
        record.name: struct.unpack_from("<I", blob, record.offset + 6)[0]
        for record in archive.records
    }
    assert type_ids == {
        "Header2": 0x1C74D22C,
        "Preview": 0x1C74D22C,
        "Contents/SolidWorks": 0x1C34D281,
    }


def test_generated_container_supports_variable_stream_sizes_and_counts() -> None:
    streams = {
        "Contents/SolidWorks": b"<swSolidWorks/>" + b"x" * 4096,
        "ThirdPty/KitData": bytes(range(256)) * 3,
        "swXmlContents/KeyWords": b"<KeyWords/>" + b"y" * 127,
    }
    blob = build_sldprt(streams)
    assert SldprtArchive.from_bytes(blob).streams == streams


def test_generated_container_reuses_template_identity() -> None:
    template = build_sldprt(
        {"Contents/SolidWorks": b"<swSolidWorks/>"},
        file_id=_VENDOR_FILE_ID,
        signatures=_VENDOR_SIGNATURES,
    )
    assert container_signatures(template) == _VENDOR_SIGNATURES
    streams = {
        "Contents/SolidWorks": b"<swSolidWorks version='2'/>",
        "ThirdPty/KitData": b"kit",
    }
    blob = build_sldprt(streams, template=template)
    assert blob[:4] == template[:4]
    assert blob[8:12] == template[8:12]
    assert blob[-22:-18] == template[-22:-18]
    assert SldprtArchive.from_bytes(blob).streams == streams


def test_generated_container_rejects_unpaired_file_identity() -> None:
    with pytest.raises(ValueError, match="native template"):
        build_sldprt({"Contents/SolidWorks": b"<swSolidWorks/>"}, file_id=1)
