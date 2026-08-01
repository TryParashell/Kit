from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import pytest

from convert import available_adapters, convert, extract_brep, open_document


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"


def test_public_api_uses_interchange_between_independent_adapters(tmp_path) -> None:
    formats = {adapter.format_id for adapter in available_adapters()}
    assert formats == {
        "catia.v5",
        "freecad.fcstd",
        "interchange.json",
        "solidworks.sldprt",
    }
    document = open_document(SAMPLE)
    json_output = tmp_path / "example.json"
    result = convert(SAMPLE, json_output)
    assert result.source_format == "solidworks.sldprt"
    assert result.destination_format == "interchange.json"
    assert open_document(json_output) == document


def test_package_exposes_one_sdk_entry_point() -> None:
    installed = entry_points(group="kit")
    assert [(item.name, item.value) for item in installed] == [("sdk", "convert")]
    assert next(iter(installed)).load().__name__ == "convert"


def test_brep_extraction_is_exact_and_safe(tmp_path) -> None:
    document = open_document(SAMPLE)
    outputs = extract_brep(document, tmp_path)
    assert len(outputs) == 3
    assert [path.read_bytes() for path in outputs] == [
        payload.data for payload in document.brep_payloads
    ]
    with pytest.raises(FileExistsError):
        extract_brep(document, tmp_path)
