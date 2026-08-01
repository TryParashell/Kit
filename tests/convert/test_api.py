from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path
import tomllib

import pytest

from convert import available_adapters, convert, extract_brep, open_document


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"
ROOT = Path(__file__).parents[2]


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
    assert [(item.name, item.value) for item in installed] == [
        ("convert", "convert:convert")
    ]
    assert next(iter(installed)).load() is convert


def test_package_metadata_is_internal_and_matches_supported_sdk() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["name"] == "kit"
    assert project["classifiers"][0] == "Private :: Do Not Upload"
    assert project["entry-points"] == {"kit": {"convert": "convert:convert"}}
    assert project["license"] == "LicenseRef-PolyForm-Strict-1.0.0"
    assert project["license-files"] == ["LICENSE"]
    assert project["urls"]["Repository"] == "https://github.com/TryParashell/Kit"
    readme = (ROOT / project["readme"]).read_text(encoding="utf-8")
    for suffix in (".SLDPRT", ".SLDASM", ".FCStd", ".CATPart", ".CATProduct"):
        assert suffix in readme
    assert "Internal use only" in readme


def test_brep_extraction_is_exact_and_safe(tmp_path) -> None:
    document = open_document(SAMPLE)
    outputs = extract_brep(document, tmp_path)
    assert len(outputs) == 3
    assert [path.read_bytes() for path in outputs] == [
        payload.data for payload in document.brep_payloads
    ]
    with pytest.raises(FileExistsError):
        extract_brep(document, tmp_path)
