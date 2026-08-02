from __future__ import annotations

import ast
from dataclasses import replace
from importlib.metadata import distribution
from inspect import isabstract
from pathlib import Path
from pkgutil import iter_modules
import tomllib

import pytest

import convert.adapters as adapter_package
from convert import (
    ApplicationUsabilityError,
    available_adapters,
    convert,
    extract_brep,
    open_document,
    write_document,
)
from convert.adapters import (
    AdapterInfo,
    AdapterDiscoveryError,
    AdapterRegistry,
    AdapterRegistryError,
    is_windows_device_name,
)
from convert.adapters.json import JsonAdapter
from interchange import BrepPayload, Capability, PayloadRole


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"
ROOT = Path(__file__).parents[2]
CATPART = ROOT / "examples" / ".CATPart" / "Banjo.CATPart"
FCSTD = ROOT / "examples" / "Random" / "V8_engine" / "hex bolt gradeb_iso.FCStd"


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
    assert result.roundtrip_safe is True
    assert result.near_lossless is True
    assert result.dropped == frozenset()
    assert result.requirements == ()
    assert result.application_usable is True
    assert result.vendor_loadable is True
    assert result.output.native_capabilities == frozenset(
        transfer.capability for transfer in result.transfers
    )
    assert result.output.carrier_capabilities == frozenset()
    assert open_document(json_output) == document


@pytest.mark.parametrize(
    ("source", "name"),
    (
        (SAMPLE, "exact.SLDPRT"),
        (FCSTD, "exact.FCStd"),
        (CATPART, "exact.CATPart"),
    ),
)
def test_default_exact_replay_is_application_usable(
    source: Path,
    name: str,
    tmp_path: Path,
) -> None:
    destination = tmp_path / name
    result = convert(source, destination)
    assert result.application_usable is True
    assert result.vendor_loadable is True
    assert result.requirements == ()
    assert result.dropped == frozenset()
    assert result.output.native_capabilities
    assert result.output.path == destination.resolve()


def test_default_proprietary_conversion_writes_reversible_carrier(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "portable.CATPart"
    result = convert(SAMPLE, destination)
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.near_lossless is False
    assert result.roundtrip_safe is True
    assert result.requirements == ()
    assert result.dropped == frozenset()
    assert result.output.carrier_capabilities
    assert destination.is_file()


def test_strict_proprietary_conversion_rejects_carrier_output(tmp_path: Path) -> None:
    destination = tmp_path / "blocked.CATPart"
    with pytest.raises(ApplicationUsabilityError) as captured:
        convert(SAMPLE, destination, allow_carrier=False)
    assert captured.value.code == "output_not_application_usable"
    assert captured.value.format_id == "catia.v5"
    assert "carrier_only" in captured.value.issues
    assert not destination.exists()
    assert tuple(tmp_path.iterdir()) == ()


def test_write_document_uses_the_same_default_and_strict_gate(tmp_path: Path) -> None:
    document = open_document(SAMPLE)
    destination = tmp_path / "portable.CATPart"
    result = write_document(document, destination)
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.requirements == ()
    assert result.dropped == frozenset()
    strict_destination = tmp_path / "blocked.CATPart"
    with pytest.raises(ApplicationUsabilityError):
        write_document(document, strict_destination, allow_carrier=False)
    assert not strict_destination.exists()


def test_public_api_reports_vendor_carriers_as_carrier_only(tmp_path) -> None:
    result = convert(SAMPLE, tmp_path / "example.CATPart", allow_carrier=True)
    assert result.roundtrip_safe is True
    assert result.dropped == frozenset()
    assert result.requirements == ()
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.output.native_capabilities == frozenset()
    assert result.output.carrier_capabilities == result.output.transferred_capabilities


def test_public_api_reports_exact_native_replay_as_native(tmp_path) -> None:
    result = convert(SAMPLE, tmp_path / "example.SLDPRT")
    assert result.roundtrip_safe is True
    assert result.dropped == frozenset()
    assert result.requirements == ()
    assert result.application_usable is True
    assert result.vendor_loadable is True
    assert result.output.native_capabilities == result.output.transferred_capabilities
    assert result.output.carrier_capabilities == frozenset()


def test_public_api_exposes_tessellation_selection() -> None:
    without = open_document(
        CATPART,
        include_brep=False,
        include_tessellation=False,
    )
    with_tessellation = open_document(
        CATPART,
        include_brep=False,
        include_tessellation=True,
    )
    assert Capability.TESSELLATION not in without.capabilities
    assert Capability.TESSELLATION in with_tessellation.capabilities


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
    for adapter in readers:
        for format_id in (adapter.info.format_id, *adapter.info.aliases):
            assert first.reader(format_id) is adapter
    for adapter in writers:
        for format_id in (adapter.info.format_id, *adapter.info.aliases):
            assert first.writer(format_id) is adapter
    assert first.introspect() == first_ids
    assert first.readers() == readers
    assert first.writers() == writers
    assert all(
        not isabstract(type(adapter))
        and not getattr(type(adapter), "_is_protocol", False)
        for adapter in (*readers, *writers)
    )
    assert all(
        adapter.info.capabilities == frozenset(Capability)
        for adapter in (*readers, *writers)
    )


def test_document_kind_extensions_are_introspective() -> None:
    by_id = {info.format_id: info for info in available_adapters()}
    assert by_id["solidworks.sldprt"].part_extensions == (".sldprt",)
    assert by_id["solidworks.sldprt"].assembly_extensions == (".sldasm",)
    assert by_id["catia.v5"].part_extensions == (".catpart",)
    assert by_id["catia.v5"].assembly_extensions == (".catproduct",)
    assert by_id["freecad.fcstd"].part_extensions == (".FCStd",)
    assert by_id["freecad.fcstd"].assembly_extensions == (".FCStd",)
    for info in by_id.values():
        assert set(info.extensions_for(assembly=False)) <= set(info.extensions)
        assert set(info.extensions_for(assembly=True)) <= set(info.extensions)
    with pytest.raises(TypeError):
        by_id["freecad.fcstd"].extensions_for(assembly=1)
    assembly_only = AdapterInfo(
        "format.assembly-only",
        "Assembly only",
        "1",
        (".assembly",),
        assembly_extensions=(".assembly",),
    )
    assert assembly_only.extensions_for(assembly=False) == ()
    assert assembly_only.extensions_for(assembly=True) == (".assembly",)


def test_every_production_payload_constructor_declares_role_and_extension() -> None:
    constructors: list[tuple[Path, ast.Call]] = []
    for path in (ROOT / "src").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Name)
                and node.func.id == "BrepPayload"
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "BrepPayload"
            ):
                constructors.append((path, node))
    assert constructors
    for path, constructor in constructors:
        keywords = {keyword.arg for keyword in constructor.keywords}
        assert {
            "role",
            "file_extension",
        } <= keywords, (
            f"{path}:{constructor.lineno} must declare payload role and extension"
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
    with pytest.raises(AdapterDiscoveryError, match="contains no adapter"):
        AdapterRegistry().introspect(package_name)


def test_adapter_discovery_does_not_depend_on_dunder_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_name = f"kit_hidden_{tmp_path.name.replace('-', '_')}"
    package = tmp_path / package_name
    format_package = package / "hidden"
    format_package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (format_package / "__init__.py").write_text(
        "from convert.adapters.json.adapter import JsonAdapter as _JsonAdapter\n"
        "class HiddenAdapter(_JsonAdapter):\n    discovered = True\n"
        "__all__ = []\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    discovered = AdapterRegistry()
    assert discovered.introspect(package_name) == ("interchange.json",)


def test_single_file_adapter_is_discovered(tmp_path: Path, monkeypatch) -> None:
    package_name = f"kit_module_{tmp_path.name.replace('-', '_')}"
    package = tmp_path / package_name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "single.py").write_text(
        "from convert.adapters.json.adapter import JsonAdapter as _JsonAdapter\n"
        "class SingleAdapter(_JsonAdapter):\n    discovered = True\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    discovered = AdapterRegistry()
    assert discovered.introspect(package_name) == ("interchange.json",)


def test_adapter_ids_and_aliases_are_case_insensitive() -> None:
    registry = AdapterRegistry()
    adapter = JsonAdapter()
    registry.register(adapter)
    assert registry.reader("INTERCHANGE.JSON") is adapter
    assert registry.writer("Interchange.Json") is adapter

    class ConflictingJsonAdapter(JsonAdapter):
        @property
        def info(self):
            return replace(super().info, format_id="INTERCHANGE.JSON")

    with pytest.raises(AdapterRegistryError, match="metadata differ"):
        registry.register(ConflictingJsonAdapter())

    class SelfAliasedJsonAdapter(JsonAdapter):
        @property
        def info(self):
            return replace(super().info, aliases=("INTERCHANGE.JSON",))

    with pytest.raises(AdapterRegistryError, match="alias must differ"):
        AdapterRegistry().register(SelfAliasedJsonAdapter())

    class DuplicateAliasJsonAdapter(JsonAdapter):
        @property
        def info(self):
            return replace(super().info, aliases=("kit.json", "KIT.JSON"))

    with pytest.raises(AdapterRegistryError, match="aliases must be unique"):
        AdapterRegistry().register(DuplicateAliasJsonAdapter())

    class MutableExtensionsJsonAdapter(JsonAdapter):
        @property
        def info(self):
            return replace(super().info, extensions=[".json"])

    with pytest.raises(AdapterRegistryError, match="extensions has an invalid type"):
        AdapterRegistry().register(MutableExtensionsJsonAdapter())

    class NumericVersionJsonAdapter(JsonAdapter):
        @property
        def info(self):
            return replace(super().info, version=1)

    with pytest.raises(AdapterRegistryError, match="version has an invalid type"):
        AdapterRegistry().register(NumericVersionJsonAdapter())


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
    assert metadata["tool"]["hatch"]["build"]["targets"]["sdist"]["include"] == [
        "/LICENSE",
        "/README.md",
        "/pyproject.toml",
        "/src",
        "/uv.lock",
    ]
    readme = (ROOT / project["readme"]).read_text(encoding="utf-8")
    for suffix in (".SLDPRT", ".SLDASM", ".FCStd", ".CATPart", ".CATProduct"):
        assert suffix in readme
    assert "Internal use only" in readme


def test_readme_describes_default_reversible_swaps_and_strict_mode() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "convert(source, destination)" in readme
    assert "allow_carrier=False" in readme
    assert "without requiring CAD software" in readme


def test_brep_extraction_is_exact_and_safe(tmp_path) -> None:
    source = open_document(SAMPLE)
    document = replace(
        source,
        brep_payloads=(
            *source.brep_payloads,
            BrepPayload("history", "vendor", "native", "", "", data=b"history"),
            BrepPayload(
                "missing",
                "vendor",
                "geometry",
                "",
                "",
                role=PayloadRole.BREP,
                file_extension=".geo",
            ),
        ),
    )
    outputs = extract_brep(document, tmp_path)
    assert len(outputs) == 3
    assert [path.read_bytes() for path in outputs] == [
        payload.data
        for payload in document.brep_payloads
        if payload.role == PayloadRole.BREP and payload.data is not None
    ]
    assert {path.suffix for path in outputs} == {".x_b"}
    with pytest.raises(FileExistsError):
        extract_brep(document, tmp_path)


def test_brep_extraction_avoids_windows_device_names(tmp_path: Path) -> None:
    payload = BrepPayload(
        "CON",
        "kernel",
        "shape",
        "",
        "",
        data=b"shape",
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )
    document = replace(open_document(SAMPLE), brep_payloads=(payload,))
    assert extract_brep(document, tmp_path)[0].name == "_CON.x_b"


def test_windows_device_name_detection_is_exhaustive() -> None:
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
        *(f"COM{index}" for index in "¹²³"),
        *(f"LPT{index}" for index in "¹²³"),
    }
    assert all(is_windows_device_name(name) for name in reserved)
    assert all(is_windows_device_name(f"{name}.x_b") for name in reserved)
    assert not any(
        is_windows_device_name(name)
        for name in ("COM0", "COM10", "LPT0", "LPT10", "CONTOUR")
    )
