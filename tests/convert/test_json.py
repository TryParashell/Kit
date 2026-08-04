# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
from io import BytesIO, StringIO

import pytest

from convert import convert, open_document
from convert.adapters import (
    AdapterInfo,
    AdapterNotFoundError,
    AdapterRegistry,
    AdapterRegistryError,
)
from convert.adapters.json import JsonAdapter
from interchange import Capability

from tests.interchange.test_document import document


class FirstAdapter(JsonAdapter):
    @property
    def info(self) -> AdapterInfo:
        return AdapterInfo("first", "First", "1", (".first",), ("second",))


class SecondAdapter(JsonAdapter):
    @property
    def info(self) -> AdapterInfo:
        return AdapterInfo("second", "Second", "1", (".second",))


class DuplicateAdapter(JsonAdapter):
    @property
    def info(self) -> AdapterInfo:
        return AdapterInfo("first", "Duplicate", "1", (".first",), ("orphan",))


class ReplacementAdapter(JsonAdapter):
    @property
    def info(self) -> AdapterInfo:
        return AdapterInfo(
            "first", "Replacement", "2", (".replacement",), ("replacement",)
        )


class ReaderOnly:
    def __init__(self, info: AdapterInfo):
        self._info = info
        self._delegate = JsonAdapter()

    @property
    def info(self) -> AdapterInfo:
        return self._info

    def probe(self, source):
        return self._delegate.probe(source)

    def read(self, source, options=None):
        return self._delegate.read(source, options)


class WriterOnly:
    def __init__(self, info: AdapterInfo):
        self._info = info
        self._delegate = JsonAdapter()

    @property
    def info(self) -> AdapterInfo:
        return self._info

    def supports(self, value, destination):
        return self._delegate.supports(value, destination)

    def write(self, value, destination, options=None):
        return self._delegate.write(value, destination, options)


class PartialBytesIO(BytesIO):
    def write(self, value):
        return super().write(value[:-1])


class PartialStringIO(StringIO):
    def write(self, value):
        return super().write(value[:-1])


class NonSeekableStream:
    def __init__(self, value):
        self.value = value
        self.consumed = False

    def read(self, size=-1):
        if self.consumed:
            return self.value[:0]
        self.consumed = True
        return self.value


def test_json_adapter_declares_every_interchange_capability() -> None:
    assert JsonAdapter().info.capabilities == frozenset(Capability)


def test_registry_roundtrip(tmp_path) -> None:
    adapter = JsonAdapter()
    registry = AdapterRegistry()
    registry.register(adapter)
    output = tmp_path / "model.json"
    written = registry.write(document(), output)
    restored = registry.read(output)
    assert written.path == output.resolve()
    assert restored == document()
    assert registry.format_ids() == ("interchange.json",)


@pytest.mark.parametrize("stream_type", (BytesIO, StringIO))
def test_json_stream_roundtrip_reports_utf8_bytes(stream_type) -> None:
    adapter = JsonAdapter()
    value = document()
    value = replace(value, source=replace(value.source, path="mémoire"))
    stream = stream_type()
    result = adapter.write(value, stream)
    serialized = stream.getvalue()
    text = serialized.decode("utf-8") if isinstance(serialized, bytes) else serialized
    assert "mémoire" in text
    assert result.bytes_written == len(text.encode("utf-8"))
    assert adapter.read(stream_type(serialized)) == value


@pytest.mark.parametrize("stream_type", (PartialBytesIO, PartialStringIO))
def test_json_stream_rejects_partial_writes(stream_type) -> None:
    with pytest.raises(OSError, match="short JSON write"):
        JsonAdapter().write(document(), stream_type())


@pytest.mark.parametrize("stream_type", (BytesIO, StringIO))
def test_json_probe_preserves_stream_position(stream_type) -> None:
    serialized = document().to_json() + "\n"
    serialized = "prefix:" + serialized
    value = serialized.encode("utf-8") if stream_type is BytesIO else serialized
    stream = stream_type(value)
    stream.seek(7)
    assert JsonAdapter().probe(stream).confidence == 1.0
    assert stream.tell() == 7


def test_public_sdk_introspects_json_text_source_and_destination() -> None:
    value = document()
    source = StringIO(value.to_json() + "\n")
    assert open_document(source) == value
    source.seek(0)
    destination = StringIO()
    result = convert(
        source,
        destination,
        destination_format="interchange.json",
    )
    assert result.destination_format == "interchange.json"
    assert JsonAdapter().read(StringIO(destination.getvalue())) == value


@pytest.mark.parametrize("binary", (False, True))
def test_public_sdk_reads_non_seekable_json_stream(binary) -> None:
    value = document()
    serialized = value.to_json() + "\n"
    payload = serialized.encode("utf-8") if binary else serialized
    source = NonSeekableStream(payload)
    assert open_document(source) == value
    destination = StringIO()
    result = convert(
        NonSeekableStream(payload),
        destination,
        destination_format="interchange.json",
    )
    assert result.document == value
    assert JsonAdapter().read(StringIO(destination.getvalue())) == value


def test_explicit_json_writer_rejects_non_json_path(tmp_path) -> None:
    source = StringIO(document().to_json())
    with pytest.raises(AdapterNotFoundError, match="does not support"):
        convert(
            source,
            tmp_path / "contradiction.SLDPRT",
            destination_format="interchange.json",
        )


def test_registry_rejects_canonical_alias_collisions_without_mutation() -> None:
    registry = AdapterRegistry()
    first = FirstAdapter()
    registry.register(first)
    with pytest.raises(AdapterRegistryError, match="already an alias"):
        registry.register(SecondAdapter())
    assert registry.reader("second") is first
    assert registry.writer("second") is first
    assert registry.format_ids() == ("first", "second")


def test_failed_registration_does_not_leak_aliases() -> None:
    registry = AdapterRegistry()
    first = FirstAdapter()
    registry.register(first)
    with pytest.raises(
        AdapterRegistryError, match="metadata differ|already registered"
    ):
        registry.register(DuplicateAdapter())
    with pytest.raises(AdapterNotFoundError):
        registry.reader("orphan")
    assert registry.reader("first") is first
    assert registry.format_ids() == ("first", "second")


def test_replacement_removes_obsolete_aliases() -> None:
    registry = AdapterRegistry()
    registry.register(FirstAdapter())
    replacement = ReplacementAdapter()
    registry.register(replacement, replace=True)
    with pytest.raises(AdapterNotFoundError):
        registry.reader("second")
    assert registry.reader("replacement") is replacement
    assert registry.writer("replacement") is replacement
    assert registry.format_ids() == ("first", "replacement")


def test_split_reader_writer_share_one_format_contract() -> None:
    info = AdapterInfo("split", "Split", "1", (".split",), ("split.alias",))
    reader = ReaderOnly(info)
    writer = WriterOnly(info)
    registry = AdapterRegistry()
    registry.register(reader)
    registry.register(writer)
    assert registry.reader("split.alias") is reader
    assert registry.writer("split.alias") is writer


def test_split_reader_writer_reject_mismatched_metadata() -> None:
    reader_info = AdapterInfo("split", "Split", "1", (".read",), ("read.alias",))
    writer_info = AdapterInfo("split", "Split", "1", (".write",), ("write.alias",))
    reader = ReaderOnly(reader_info)
    registry = AdapterRegistry()
    registry.register(reader)
    with pytest.raises(AdapterRegistryError, match="metadata differ"):
        registry.register(WriterOnly(writer_info))
    with pytest.raises(AdapterNotFoundError):
        registry.writer("split")
    with pytest.raises(AdapterNotFoundError):
        registry.reader("write.alias")
    assert registry.reader("read.alias") is reader
    assert registry.format_ids() == ("read.alias", "split")
