from __future__ import annotations

import pytest

from convert.adapters import (
    AdapterInfo,
    AdapterNotFoundError,
    AdapterRegistry,
    AdapterRegistryError,
)
from convert.adapters.json import JsonAdapter

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
    with pytest.raises(AdapterRegistryError, match="already registered"):
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
    writer_info = AdapterInfo(
        "split", "Split", "1", (".write",), ("write.alias",)
    )
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
