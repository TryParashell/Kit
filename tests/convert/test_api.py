from __future__ import annotations

import ast
from importlib.metadata import distribution
from inspect import isabstract
from pathlib import Path
from pkgutil import iter_modules
import tomllib

import pytest

import convert.adapters as adapter_package
from convert import available_adapters, convert, extract_brep, open_document
from convert.adapters import AdapterDiscoveryError, AdapterRegistry


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"
ROOT = Path(__file__).parents[2]


def test_public_api_uses_interchange_between_independent_adapters(tmp_path) -> None:
    formats = {adapter.format_id for adapter in available_adapters()}
    introspected = AdapterRegistry()
    introspected.introspect()
    assert formats == {adapter.info.format_id for adapter in introspected.readers()}
    document = open_document(SAMPLE)
    json_output = tmp_path / "example.json"
    result = convert(SAMPLE, json_output)
    assert result.source_format == "solidworks.sldprt"
    assert result.destination_format == "interchange.json"
    assert open_document(json_output) == document


def test_package_exposes_one_sdk_entry_point() -> None:
    installed = distribution("kit").entry_points
    assert [(item.group, item.name, item.value) for item in installed] == [
        ("kit", "convert", "convert:convert")
    ]
    assert next(iter(installed)).load() is convert


def test_every_format_package_is_introspected_deterministically() -> None:
    package_names = tuple(
        sorted(
            item.name
            for item in iter_modules(
                adapter_package.__path__, adapter_package.__name__ + "."
            )
            if item.ispkg and not item.name.rsplit(".", 1)[-1].startswith("_")
        )
    )
    first = AdapterRegistry()
    first_ids = first.introspect()
    second = AdapterRegistry()
    second_ids = second.introspect()
    readers = first.readers()
    writers = first.writers()

    def packages_for(adapters: tuple[object, ...]) -> set[str]:
        return {
            package_name
            for adapter in adapters
            for package_name in package_names
            if type(adapter).__module__ == package_name
            or type(adapter).__module__.startswith(package_name + ".")
        }

    assert package_names
    assert packages_for(readers) == set(package_names)
    assert packages_for(writers) == set(package_names)
    assert first_ids == second_ids == tuple(sorted(first_ids))
    assert tuple(adapter.info.format_id for adapter in readers) == first_ids
    assert tuple(adapter.info.format_id for adapter in writers) == first_ids
    assert first.introspect() == first_ids
    assert first.readers() == readers
    assert first.writers() == writers
    assert all(
        not isabstract(type(adapter))
        and not getattr(type(adapter), "_is_protocol", False)
        for adapter in (*readers, *writers)
    )


def test_api_has_no_format_specific_registration() -> None:
    package_names = tuple(
        sorted(
            item.name
            for item in iter_modules(
                adapter_package.__path__, adapter_package.__name__ + "."
            )
            if item.ispkg and not item.name.rsplit(".", 1)[-1].startswith("_")
        )
    )
    introspected = AdapterRegistry()
    introspected.introspect()
    adapter_names = {
        type(adapter).__name__
        for adapter in (*introspected.readers(), *introspected.writers())
    }
    format_names = {name.rsplit(".", 1)[-1] for name in package_names}
    path = ROOT / "src" / "convert" / "api.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(
                alias.name == package_name or alias.name.startswith(package_name + ".")
                for alias in node.names
                for package_name in package_names
            )
        if isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            assert not any(
                module_name == package_name
                or module_name == package_name.removeprefix("convert.")
                or module_name.startswith(package_name + ".")
                or module_name.startswith(package_name.removeprefix("convert.") + ".")
                for package_name in package_names
            )
            if module_name in {"adapters", "convert.adapters"}:
                imported_names = {alias.name for alias in node.names}
                assert not (adapter_names | format_names) & imported_names


def test_empty_format_package_fails_introspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_name = f"kit_empty_{tmp_path.name.replace('-', '_')}"
    package = tmp_path / package_name
    format_package = package / "empty"
    format_package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (format_package / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(AdapterDiscoveryError, match="exports no adapter"):
        AdapterRegistry().introspect(package_name)


def test_package_metadata_is_internal_and_matches_supported_sdk() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["name"] == "kit"
    assert project["classifiers"][0] == "Private :: Do Not Upload"
    assert project["entry-points"] == {"kit": {"convert": "convert:convert"}}
    assert "scripts" not in project
    assert "gui-scripts" not in project
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
