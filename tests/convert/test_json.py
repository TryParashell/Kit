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
