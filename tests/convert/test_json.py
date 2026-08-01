from __future__ import annotations

from convert.adapters import AdapterRegistry
from convert.adapters.json import JsonAdapter

from tests.interchange.test_document import document


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
