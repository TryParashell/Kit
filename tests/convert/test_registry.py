# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest

from convert.adapters import (
    AdapterInfo,
    AdapterRegistry,
    AdapterRegistryError,
    AmbiguousAdapterError,
    ApplicationUsabilityError,
    CarrierReason,
    CapabilityTransfer,
    CapabilityLossError,
    ProbeResult,
    ReadOptions,
    TransferMode,
    WriteOptions,
    WriteResult,
)
from convert.adapters.json import JsonAdapter
from convert.engine import ConversionEngine
from interchange import (
    BrepPayload,
    Capability,
    Configuration,
    Mesh,
    PayloadRole,
    Vector3,
    infer_capabilities,
)

from tests.interchange.test_document import document


class _ResultAdapter(JsonAdapter):
    def __init__(
        self,
        info: AdapterInfo,
        *,
        probe_format: str | None = None,
        write_format: str | None = None,
    ) -> None:
        self._info = info
        self._probe_format = probe_format
        self._write_format = write_format

    @property
    def info(self) -> AdapterInfo:
        return self._info

    def probe(self, source):
        result = super().probe(source)
        return replace(
            result,
            format_id=self._probe_format or self.info.format_id,
        )

    def write(self, document, destination, options=None):
        result = super().write(document, destination, options)
        return replace(
            result,
            adapter=self._write_format or self.info.format_id,
        )


class _CarrierPathAdapter(_ResultAdapter):
    def supports(self, document, destination):
        return isinstance(destination, (str, Path))

    def write(self, document, destination, options=None):
        path = Path(destination).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"carrier")
        return WriteResult(
            path,
            self.info.format_id,
            len(b"carrier"),
            application_usable=False,
            vendor_loadable=False,
        )


def _adapter(format_id: str, **values: str) -> _ResultAdapter:
    return _ResultAdapter(
        AdapterInfo(
            format_id,
            format_id,
            "1",
            (f".{format_id}",),
            capabilities=frozenset(Capability),
            native_capabilities=frozenset(Capability),
        ),
        **values,
    )


def test_introspection_discovers_adapter_implementation_without_package_export(
    tmp_path, monkeypatch
) -> None:
    package_name = f"kit_nested_{tmp_path.name.replace('-', '_')}"
    package = tmp_path / package_name
    format_package = package / "nested"
    format_package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (format_package / "__init__.py").write_text("", encoding="utf-8")
    (format_package / "implementation.py").write_text(
        "from convert.adapters.json.adapter import JsonAdapter\n"
        "class NestedAdapter(JsonAdapter):\n    discovered = True\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    registry = AdapterRegistry()
    assert registry.introspect(package_name) == ("interchange.json",)
    assert type(registry.reader("interchange.json")).__name__ == "NestedAdapter"


def test_reader_ambiguity_reports_every_tied_format() -> None:
    registry = AdapterRegistry()
    format_ids = ("format.alpha", "format.beta", "format.gamma")
    registry.extend(_adapter(format_id) for format_id in format_ids)
    source = document().to_json().encode("utf-8")
    with pytest.raises(AmbiguousAdapterError) as captured:
        registry.select_reader(source)
    assert all(format_id in str(captured.value) for format_id in format_ids)


def test_registry_rejects_inconsistent_probe_and_write_format_names() -> None:
    source = document().to_json().encode("utf-8")
    probe_registry = AdapterRegistry()
    probe_registry.register(_adapter("format.probe", probe_format="format.other"))
    with pytest.raises(AdapterRegistryError, match="returned probe format"):
        probe_registry.select_reader(source)
    write_registry = AdapterRegistry()
    write_registry.register(_adapter("format.write", write_format="format.other"))
    with pytest.raises(AdapterRegistryError, match="returned write format"):
        write_registry.write(document(), BytesIO(), format_id="format.write")


def test_registry_accepts_case_insensitive_probe_and_write_aliases() -> None:
    info = AdapterInfo(
        "format.primary",
        "Primary",
        "1",
        (".primary", ".alias"),
        aliases=("format.alias",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    adapter = _ResultAdapter(
        info,
        probe_format="FORMAT.ALIAS",
        write_format="Format.Alias",
    )
    registry = AdapterRegistry()
    registry.register(adapter)
    source = document().to_json().encode("utf-8")
    assert registry.select_reader(source) is adapter
    result = registry.write(document(), BytesIO(), format_id="format.primary")
    assert result.adapter == "Format.Alias"


def test_conversion_result_preserves_case_insensitive_source_alias() -> None:
    info = AdapterInfo(
        "format.canonical",
        "Canonical",
        "1",
        (".canonical",),
        aliases=("format.alias",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    adapter = _ResultAdapter(info)
    registry = AdapterRegistry()
    registry.register(adapter)
    source = document()
    source = replace(
        source,
        source=replace(source.source, format_id="FORMAT.ALIAS"),
    )
    result = ConversionEngine(registry).convert(
        source.to_json().encode("utf-8"),
        BytesIO(),
        source_format="format.alias",
        destination_format="format.canonical",
        read_options=ReadOptions(include_tessellation=True),
    )
    assert result.source_format == "FORMAT.ALIAS"


def test_json_read_options_filter_data_and_select_configurations() -> None:
    brep = BrepPayload(
        "payload:brep",
        "test.brep",
        "shape",
        "1",
        "0" * 64,
        data=b"brep",
        role=PayloadRole.BREP,
        file_extension=".brep",
    )
    tessellation = BrepPayload(
        "payload:tessellation",
        "test.mesh",
        "tessellation",
        "1",
        "1" * 64,
        data=b"mesh",
        role=PayloadRole.TESSELLATION,
        file_extension=".mesh",
    )
    mesh = Mesh(
        "mesh:json",
        "JSON mesh",
        (
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
    )
    source = replace(
        document(),
        configurations=(
            Configuration("configuration:first", "Shared", True),
            Configuration("configuration:second", "Second"),
            Configuration("configuration:third", "Shared"),
        ),
        meshes=(mesh,),
        brep_payloads=(brep, tessellation),
        capabilities=frozenset(
            {
                Capability.BREP,
                Capability.TESSELLATION,
                Capability.NATIVE_PAYLOADS,
            }
        ),
    )
    payload = source.to_json().encode("utf-8")
    restored = JsonAdapter().read(
        payload,
        ReadOptions(
            configuration="Shared",
            include_brep=False,
            include_tessellation=False,
        ),
    )
    assert [item.id for item in restored.configurations if item.active] == [
        "configuration:first",
        "configuration:third",
    ]
    assert not restored.meshes
    assert not restored.brep_payloads
    assert not restored.capabilities & {
        Capability.BREP,
        Capability.TESSELLATION,
        Capability.NATIVE_PAYLOADS,
    }
    with pytest.raises(ValueError, match="configuration"):
        JsonAdapter().read(
            payload,
            ReadOptions(configuration="configuration:missing"),
        )


def test_read_options_preserve_every_representation_by_default() -> None:
    options = ReadOptions()
    assert options.include_brep is True
    assert options.include_tessellation is True


def test_roundtrip_safety_is_independent_of_capability_count_and_requirements() -> None:
    result = WriteResult(
        None,
        "format.empty",
        0,
        requirements=("companion file",),
    )
    assert result.transfers == ()
    assert result.dropped == frozenset()
    assert result.roundtrip_safe is True
    assert result.near_lossless is False
    assert result.application_usable is False
    assert result.vendor_loadable is False


@pytest.mark.parametrize(
    ("metadata", "values"),
    (
        ({"application_usable": True}, {"application_usable": False}),
        ({"vendor_loadable": True}, {"vendor_loadable": False}),
    ),
)
def test_write_result_rejects_contradictory_usability_metadata(
    metadata: dict[str, bool], values: dict[str, bool]
) -> None:
    with pytest.raises(ValueError, match="contradicts the write result"):
        WriteResult(None, "format.contradictory", 0, metadata=metadata, **values)


def test_write_result_rejects_usable_but_vendor_unloadable_output() -> None:
    with pytest.raises(ValueError, match="must be vendor-loadable"):
        WriteResult(
            None,
            "format.impossible",
            0,
            application_usable=True,
            vendor_loadable=False,
        )


def test_registry_preserves_independent_usability_fields() -> None:
    class LoadableButUnusableAdapter(_ResultAdapter):
        def write(self, document, destination, options=None):
            return replace(
                super().write(document, destination, options),
                application_usable=False,
                vendor_loadable=True,
            )

    info = AdapterInfo(
        "format.loadable-unusable",
        "Loadable but unusable",
        "1",
        (".loadable",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(LoadableButUnusableAdapter(info))
    result = registry.write(
        document(),
        BytesIO(),
        format_id=info.format_id,
        options=WriteOptions(values={"allow_carrier": True}),
    )
    assert result.application_usable is False
    assert result.vendor_loadable is True
    assert result.near_lossless is False


def test_registry_rejects_silent_capability_loss_before_writing() -> None:
    adapter = _ResultAdapter(
        AdapterInfo(
            "format.lossy",
            "Lossy",
            "1",
            (".lossy",),
            capabilities=frozenset({Capability.PARAMETRIC_HISTORY}),
        )
    )
    registry = AdapterRegistry()
    registry.register(adapter)
    destination = BytesIO()
    with pytest.raises(CapabilityLossError) as captured:
        registry.write(document(), destination, format_id="format.lossy")
    assert captured.value.dropped
    assert Capability.EDITABLE_SKETCHES in captured.value.dropped
    assert destination.getvalue() == b""


def test_registry_rejects_native_capabilities_it_cannot_preserve() -> None:
    adapter = _ResultAdapter(
        AdapterInfo(
            "format.invalid-native",
            "Invalid native",
            "1",
            (".invalid",),
            native_capabilities=frozenset({Capability.BREP}),
        )
    )
    with pytest.raises(AdapterRegistryError, match="preservation capabilities"):
        AdapterRegistry().register(adapter)


def test_write_result_reports_native_and_carrier_transfer_modes() -> None:
    class CarrierAdapter(_ResultAdapter):
        def write(self, document, destination, options=None):
            result = super().write(document, destination, options)
            return replace(
                result,
                metadata={
                    "compatibility": "kit-neutral-only",
                    "vendor_loadable": False,
                },
                application_usable=False,
                vendor_loadable=False,
            )

    info = AdapterInfo(
        "format.carrier",
        "Carrier",
        "1",
        (".carrier",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(CarrierAdapter(info))
    blocked = BytesIO()
    with pytest.raises(ApplicationUsabilityError) as captured:
        registry.write(document(), blocked, format_id=info.format_id)
    assert blocked.getvalue() == b""
    assert captured.value.code == "output_not_application_usable"
    assert captured.value.issues == (
        "application_unusable",
        "vendor_unloadable",
        "carrier_only",
        "unimplemented_translation",
    )
    assert captured.value.to_dict() == {
        "code": "output_not_application_usable",
        "format_id": info.format_id,
        "issues": captured.value.issues,
        "application_usable": False,
        "vendor_loadable": False,
        "requirements": (),
        "dropped": (),
        "carrier_capabilities": tuple(
            sorted(
                capability.value for capability in captured.value.carrier_capabilities
            )
        ),
        "carrier_reasons": {
            capability.value: CarrierReason.WRITER_UNIMPLEMENTED.value
            for capability in sorted(
                captured.value.carrier_capabilities,
                key=lambda value: value.value,
            )
        },
        "unimplemented_capabilities": tuple(
            sorted(
                capability.value for capability in captured.value.carrier_capabilities
            )
        ),
        "source_opaque_capabilities": (),
    }
    result = registry.write(
        document(),
        BytesIO(),
        format_id=info.format_id,
        options=WriteOptions(values={"allow_carrier": True}),
    )
    assert {transfer.mode for transfer in result.transfers} == {TransferMode.CARRIER}
    assert result.native_capabilities == frozenset()
    assert result.carrier_capabilities
    assert result.dropped == frozenset()
    assert result.requirements == ()
    assert result.roundtrip_safe is True
    assert result.application_usable is False
    assert result.vendor_loadable is False


def test_failed_application_gate_preserves_existing_path(tmp_path: Path) -> None:
    class CarrierPathAdapter(_ResultAdapter):
        def supports(self, document, destination):
            return isinstance(destination, (str, Path))

        def write(self, document, destination, options=None):
            path = Path(destination).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"carrier")
            return WriteResult(
                path,
                self.info.format_id,
                len(b"carrier"),
                metadata={
                    "compatibility": "kit-neutral-only",
                    "vendor_loadable": False,
                    "application_usable": False,
                },
            )

    info = AdapterInfo(
        "format.path-carrier",
        "Path carrier",
        "1",
        (".carrier",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(CarrierPathAdapter(info))
    destination = tmp_path / "existing.carrier"
    destination.write_bytes(b"original")
    with pytest.raises(ApplicationUsabilityError):
        registry.write(
            document(),
            destination,
            format_id=info.format_id,
            options=WriteOptions(overwrite=True),
        )
    assert destination.read_bytes() == b"original"
    assert tuple(tmp_path.iterdir()) == (destination,)
    result = registry.write(
        document(),
        destination,
        format_id=info.format_id,
        options=WriteOptions(
            overwrite=True,
            values={"allow_carrier": True},
        ),
    )
    assert result.path == destination.resolve()
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert destination.read_bytes() == b"carrier"
    assert tuple(tmp_path.iterdir()) == (destination,)


def test_failed_application_gate_removes_only_new_empty_ancestors(
    tmp_path: Path,
) -> None:
    class CarrierPathAdapter(_ResultAdapter):
        def supports(self, document, destination):
            return isinstance(destination, (str, Path))

        def write(self, document, destination, options=None):
            path = Path(destination).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"carrier")
            return WriteResult(
                path,
                self.info.format_id,
                len(b"carrier"),
                application_usable=False,
                vendor_loadable=False,
            )

    info = AdapterInfo(
        "format.nested-carrier",
        "Nested carrier",
        "1",
        (".carrier",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(CarrierPathAdapter(info))
    absent_root = tmp_path / "absent"
    with pytest.raises(ApplicationUsabilityError):
        registry.write(
            document(),
            absent_root / "one" / "two" / "blocked.carrier",
            format_id=info.format_id,
        )
    assert not absent_root.exists()
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ApplicationUsabilityError):
        registry.write(
            document(),
            existing / "one" / "two" / "blocked.carrier",
            format_id=info.format_id,
        )
    assert existing.is_dir()
    assert tuple(existing.iterdir()) == ()


def test_staging_directory_setup_cleans_partial_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    info = AdapterInfo(
        "format.partial-directory",
        "Partial directory",
        "1",
        (".partial",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(_CarrierPathAdapter(info))
    destination = tmp_path / "partial" / "one" / "two" / "blocked.partial"
    failure = tmp_path / "partial" / "one"
    original_mkdir = Path.mkdir

    def failing_mkdir(path: Path, *args, **kwargs) -> None:
        if path == failure:
            raise OSError("forced staging directory failure")
        original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", failing_mkdir)
    with pytest.raises(OSError, match="forced staging directory failure"):
        registry.write(
            document(),
            destination,
            format_id=info.format_id,
        )
    assert not (tmp_path / "partial").exists()


def test_staging_directory_setup_preserves_concurrent_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    info = AdapterInfo(
        "format.concurrent-directory",
        "Concurrent directory",
        "1",
        (".concurrent",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(_CarrierPathAdapter(info))
    concurrent = tmp_path / "concurrent"
    destination = concurrent / "one" / "two" / "blocked.concurrent"
    original_mkdir = Path.mkdir
    injected = False

    def concurrent_mkdir(path: Path, *args, **kwargs) -> None:
        nonlocal injected
        if path == concurrent and not injected:
            injected = True
            original_mkdir(path, *args, **kwargs)
            raise FileExistsError(path)
        original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", concurrent_mkdir)
    with pytest.raises(ApplicationUsabilityError):
        registry.write(
            document(),
            destination,
            format_id=info.format_id,
        )
    assert concurrent.is_dir()
    assert tuple(concurrent.iterdir()) == ()


def test_carrier_opt_in_cannot_promote_usability_flags() -> None:
    info = AdapterInfo(
        "format.claimed-carrier",
        "Claimed carrier",
        "1",
        (".carrier",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(_ResultAdapter(info))
    result = registry.write(
        document(),
        BytesIO(),
        format_id=info.format_id,
        options=WriteOptions(values={"allow_carrier": True}),
    )
    assert result.native_capabilities == frozenset()
    assert result.carrier_capabilities == result.transferred_capabilities
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.metadata["application_usable"] is False
    assert result.metadata["vendor_loadable"] is False


@pytest.mark.parametrize("values", ({}, {"allow_carrier": True}))
def test_default_write_requires_no_external_requirements(
    values: dict[str, bool],
) -> None:
    class RequirementAdapter(_ResultAdapter):
        def write(self, document, destination, options=None):
            return replace(
                super().write(document, destination, options),
                requirements=("external application",),
            )

    info = AdapterInfo(
        "format.requirement",
        "Requirement",
        "1",
        (".requirement",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(RequirementAdapter(info))
    destination = BytesIO()
    with pytest.raises(ApplicationUsabilityError) as captured:
        registry.write(
            document(),
            destination,
            format_id=info.format_id,
            options=WriteOptions(values=values),
        )
    assert destination.getvalue() == b""
    assert captured.value.issues == ("external_requirements",)
    assert captured.value.requirements == ("external application",)


def test_self_contained_stream_rejects_requirements_with_carriers_allowed() -> None:
    class RequirementAdapter(_ResultAdapter):
        def write(self, document, destination, options=None):
            return replace(
                super().write(document, destination, options),
                requirements=("external application",),
            )

    info = AdapterInfo(
        "format.self-contained-stream",
        "Self-contained stream",
        "1",
        (".stream",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(RequirementAdapter(info))
    destination = BytesIO(b"original")
    with pytest.raises(ApplicationUsabilityError) as captured:
        registry.write(
            document(),
            destination,
            format_id=info.format_id,
            options=WriteOptions(
                values={
                    "allow_carrier": True,
                    "require_self_contained": True,
                }
            ),
        )
    assert destination.getvalue() == b"original"
    assert captured.value.issues == ("external_requirements",)
    assert captured.value.requirements == ("external application",)


def test_self_contained_path_rejects_requirement_bundle_before_commit(
    tmp_path: Path,
) -> None:
    class RequirementBundleAdapter(_ResultAdapter):
        def supports(self, document, destination):
            return isinstance(destination, (str, Path))

        def write(self, document, destination, options=None):
            path = Path(destination).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"generated")
            (path.parent / "component.bin").write_bytes(b"generated component")
            return WriteResult(
                path,
                self.info.format_id,
                len(b"generated"),
                requirements=("external component file",),
                application_usable=True,
                vendor_loadable=True,
            )

    info = AdapterInfo(
        "format.self-contained-path",
        "Self-contained path",
        "1",
        (".bundle",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(RequirementBundleAdapter(info))
    destination = tmp_path / "existing.bundle"
    component = tmp_path / "component.bin"
    destination.write_bytes(b"original")
    component.write_bytes(b"original component")
    with pytest.raises(ApplicationUsabilityError) as captured:
        registry.write(
            document(),
            destination,
            format_id=info.format_id,
            options=WriteOptions(
                overwrite=True,
                values={
                    "allow_carrier": True,
                    "require_self_contained": True,
                },
            ),
        )
    assert destination.read_bytes() == b"original"
    assert component.read_bytes() == b"original component"
    assert tuple(sorted(path.name for path in tmp_path.iterdir())) == (
        "component.bin",
        "existing.bundle",
    )
    assert captured.value.issues == ("external_requirements",)
    assert captured.value.requirements == ("external component file",)


def test_mixed_transfer_is_truthful_in_native_and_carrier_views() -> None:
    result = WriteResult(
        None,
        "format.mixed",
        1,
        transfers=(
            CapabilityTransfer(
                Capability.PARAMETRIC_HISTORY,
                TransferMode.MIXED,
            ),
        ),
        application_usable=True,
        vendor_loadable=True,
    )
    assert result.native_capabilities == frozenset({Capability.PARAMETRIC_HISTORY})
    assert result.carrier_capabilities == frozenset({Capability.PARAMETRIC_HISTORY})


def test_default_rejects_vendor_loadable_mixed_writer_gap() -> None:
    class MixedAdapter(_ResultAdapter):
        def write(self, document, destination, options=None):
            result = super().write(document, destination, options)
            capabilities = sorted(
                document.capabilities
                | infer_capabilities(
                    document,
                    roundtrip_metadata=(
                        Capability.ROUNDTRIP_METADATA in document.capabilities
                    ),
                ),
                key=lambda capability: capability.value,
            )
            return replace(
                result,
                transfers=tuple(
                    CapabilityTransfer(
                        capability,
                        (TransferMode.NATIVE if index == 0 else TransferMode.CARRIER),
                    )
                    for index, capability in enumerate(capabilities)
                ),
                application_usable=True,
                vendor_loadable=True,
            )

    info = AdapterInfo(
        "format.mixed-gap",
        "Mixed gap",
        "1",
        (".mixed",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(MixedAdapter(info))
    destination = BytesIO()
    with pytest.raises(ApplicationUsabilityError) as captured:
        registry.write(document(), destination, format_id=info.format_id)
    assert destination.getvalue() == b""
    assert captured.value.application_usable is True
    assert captured.value.vendor_loadable is True
    assert "unimplemented_translation" in captured.value.issues
    assert captured.value.unimplemented_capabilities


def test_default_allows_target_unsupported_carrier_portion() -> None:
    class TargetLimitedAdapter(_ResultAdapter):
        def write(self, document, destination, options=None):
            result = super().write(document, destination, options)
            capabilities = sorted(
                document.capabilities
                | infer_capabilities(
                    document,
                    roundtrip_metadata=(
                        Capability.ROUNDTRIP_METADATA in document.capabilities
                    ),
                ),
                key=lambda capability: capability.value,
            )
            return replace(
                result,
                transfers=tuple(
                    CapabilityTransfer(
                        capability,
                        (TransferMode.NATIVE if index == 0 else TransferMode.CARRIER),
                        (None if index == 0 else CarrierReason.TARGET_UNSUPPORTED),
                    )
                    for index, capability in enumerate(capabilities)
                ),
                application_usable=True,
                vendor_loadable=True,
            )

    info = AdapterInfo(
        "format.target-limited",
        "Target limited",
        "1",
        (".limited",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(TargetLimitedAdapter(info))
    destination = BytesIO()
    result = registry.write(document(), destination, format_id=info.format_id)
    assert destination.getvalue()
    assert result.application_usable is True
    assert result.vendor_loadable is True
    assert result.carrier_capabilities
    assert result.near_lossless is True
    assert all(
        transfer.carrier_reason is CarrierReason.TARGET_UNSUPPORTED
        for transfer in result.transfers
        if transfer.mode is TransferMode.CARRIER
    )


def test_default_allows_vendor_loadable_target_unsupported_only_document() -> None:
    class TargetLimitedAdapter(_ResultAdapter):
        def write(self, document, destination, options=None):
            result = super().write(document, destination, options)
            capabilities = document.capabilities | infer_capabilities(
                document,
                roundtrip_metadata=(
                    Capability.ROUNDTRIP_METADATA in document.capabilities
                ),
            )
            return replace(
                result,
                transfers=tuple(
                    CapabilityTransfer(
                        capability,
                        TransferMode.CARRIER,
                        CarrierReason.TARGET_UNSUPPORTED,
                    )
                    for capability in sorted(
                        capabilities,
                        key=lambda capability: capability.value,
                    )
                ),
                application_usable=True,
                vendor_loadable=True,
            )

    info = AdapterInfo(
        "format.target-empty",
        "Target empty",
        "1",
        (".empty",),
        capabilities=frozenset(Capability),
    )
    registry = AdapterRegistry()
    registry.register(TargetLimitedAdapter(info))
    destination = BytesIO()
    result = registry.write(document(), destination, format_id=info.format_id)
    assert destination.getvalue()
    assert result.native_capabilities == frozenset()
    assert result.carrier_capabilities == result.transferred_capabilities
    assert result.application_usable is True
    assert result.vendor_loadable is True
    assert result.near_lossless is True
