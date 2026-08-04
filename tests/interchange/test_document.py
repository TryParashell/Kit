# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import is_dataclass, replace
from enum import Enum
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import interchange
import pytest

from interchange import (
    AssemblyData,
    Body,
    BrepPayload,
    CadDocument,
    CadDocumentValidationError,
    CadSource,
    Capability,
    ComponentDefinition,
    ComponentInstance,
    ComponentKind,
    Configuration,
    FeatureKind,
    FeatureStep,
    LineGeometry,
    PayloadRole,
    Sketch,
    SketchEntity,
    SupportPlane,
    Transform,
    Vector2,
    filter_document,
    infer_capabilities,
)
from interchange.history import _LEGACY_PAYLOAD_RULES, _legacy_payload_fields
from interchange.serialization import _TYPE_REGISTRY, from_data, register_types, to_data


def document() -> CadDocument:
    plane = SupportPlane("plane:xy", "XY", Transform())
    entity = SketchEntity(
        "sketch:1:line:1",
        "line",
        LineGeometry(Vector2(0.0, 0.0), Vector2(10.0, 0.0)),
    )
    sketch = Sketch("sketch:1", "Sketch1", plane.id, (entity,))
    feature = FeatureStep(
        "feature:1", "Boss1", FeatureKind.EXTRUSION, 0, sketch_id=sketch.id
    )
    body = Body("body:1", "Body", feature.id)
    return CadDocument(
        source=CadSource("test", "memory", "0" * 64),
        configurations=(Configuration("config:default", "Default", True),),
        parameters=(),
        support_planes=(plane,),
        sketches=(sketch,),
        selections=(),
        feature_timeline=(feature,),
        bodies=(body,),
        capabilities=frozenset(
            {Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES}
        ),
    )


def test_json_roundtrip_is_lossless() -> None:
    source = document()
    restored = CadDocument.from_json(source.to_json())
    assert restored == source
    assert isinstance(restored.capabilities, frozenset)
    assert isinstance(restored.feature_timeline, tuple)


def test_json_serialization_is_stable_across_hash_seeds() -> None:
    payload = document().to_json(indent=None)
    source_root = Path(__file__).parents[2] / "src"
    script = (
        "from interchange import CadDocument;"
        f"print(CadDocument.from_json({payload!r}).to_json(indent=None))"
    )
    outputs = {
        subprocess.check_output(
            [sys.executable, "-c", script],
            cwd=source_root.parent,
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            text=True,
        )
        for seed in (1, 7, 31)
    }
    assert len(outputs) == 1


def test_serialization_registry_contains_every_public_interchange_type() -> None:
    expected = {
        value.__name__: value
        for name, value in vars(interchange).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and (is_dataclass(value) or issubclass(value, Enum))
    }
    assert _TYPE_REGISTRY == expected


def test_serialization_registry_rejects_conflicting_type_names() -> None:
    conflicting = Enum("CadSource", {"VALUE": "value"})
    with pytest.raises(ValueError, match="duplicate interchange type name"):
        register_types(conflicting)
    register_types(CadSource)


@pytest.mark.parametrize("role", tuple(PayloadRole))
def test_every_payload_role_and_file_extension_roundtrip_losslessly(
    role: PayloadRole,
) -> None:
    payload = BrepPayload(
        "geometry",
        "future.kernel",
        "custom",
        "v1",
        "0" * 64,
        data=b"geometry",
        role=role,
        file_extension=".geo",
    )
    restored = CadDocument.from_json(
        replace(document(), brep_payloads=(payload,)).to_json()
    )
    assert restored.brep_payloads == (payload,)


@pytest.mark.parametrize("rule", _LEGACY_PAYLOAD_RULES)
def test_every_legacy_payload_rule_is_reachable(rule) -> None:
    format_id = sorted(rule.format_ids)[0] if rule.format_ids else ""
    kind = sorted(rule.kinds)[0] if rule.kinds else ""
    schema = sorted(rule.schemas)[0] if rule.schemas else ""
    suffix = sorted(rule.source_suffixes)[0] if rule.source_suffixes else ""
    role, file_extension = _legacy_payload_fields(
        {
            "format_id": format_id,
            "kind": kind,
            "schema": schema,
            "source_stream": f"legacy{suffix}" if suffix else "",
        }
    )
    assert role == rule.role
    assert file_extension == (rule.file_extension or ".bin")


@pytest.mark.parametrize(
    ("format_id", "kind", "schema", "source_stream", "role", "extension"),
    (
        ("parasolid", "binary", "SCH_3500040", "Partition", PayloadRole.BREP, ".x_b"),
        (
            "catia.cgr",
            "native_tessellation",
            "CATCGRCont",
            "3",
            PayloadRole.TESSELLATION,
            ".cgr",
        ),
        (
            "catia.v5.osmx",
            "native_feature_graph",
            "CATPrtCont",
            "1",
            PayloadRole.FEATURE_HISTORY,
            ".osmx",
        ),
        (
            "solidworks.mates",
            "mate-list",
            "solidworks.serialized-object-stream",
            "Mates",
            PayloadRole.ASSEMBLY_STRUCTURE,
            ".bin",
        ),
        (
            "freecad.fcstd",
            "native_document",
            "FreeCAD Schema 4",
            "Legacy.FCStd",
            PayloadRole.DOCUMENT,
            ".FCStd",
        ),
        (
            "catia.v5.sha256",
            "native_document_binding",
            "sha256",
            "V5_CFV2",
            PayloadRole.VERIFICATION,
            ".sha256",
        ),
        ("future.cad", "opaque", "v9", "Data", PayloadRole.AUXILIARY, ".bin"),
    ),
)
def test_pre_payload_field_records_migrate_without_losing_data(
    format_id: str,
    kind: str,
    schema: str,
    source_stream: str,
    role: PayloadRole,
    extension: str,
) -> None:
    raw = to_data(
        BrepPayload(
            "legacy",
            format_id,
            kind,
            schema,
            hashlib.sha256(b"legacy payload").hexdigest(),
            data=b"legacy payload",
            source_stream=source_stream,
        )
    )
    raw.pop("role")
    raw.pop("file_extension")
    restored = from_data(raw)
    assert isinstance(restored, BrepPayload)
    assert restored.role == role
    assert restored.file_extension == extension
    assert restored.data == b"legacy payload"
    assert restored.sha256 == hashlib.sha256(b"legacy payload").hexdigest()


def test_legacy_payload_migration_only_supplies_missing_fields() -> None:
    raw = to_data(
        BrepPayload(
            "legacy",
            "parasolid",
            "binary",
            "SCH_3500040",
            hashlib.sha256(b"payload").hexdigest(),
            data=b"payload",
            role=PayloadRole.AUXILIARY,
            file_extension=".custom",
        )
    )
    without_role = dict(raw)
    without_role.pop("role")
    restored_role = from_data(without_role)
    assert restored_role.role == PayloadRole.BREP
    assert restored_role.file_extension == ".custom"
    without_extension = dict(raw)
    without_extension.pop("file_extension")
    restored_extension = from_data(without_extension)
    assert restored_extension.role == PayloadRole.AUXILIARY
    assert restored_extension.file_extension == ".x_b"
    assert from_data(raw).role == PayloadRole.AUXILIARY
    assert from_data(raw).file_extension == ".custom"
    binding = to_data(
        BrepPayload(
            "binding",
            "catia.v5.sha256",
            "native_document_binding",
            "sha256",
            hashlib.sha256(b"binding").hexdigest(),
            data=b"binding",
            role=PayloadRole.DOCUMENT,
            file_extension=".bin",
        )
    )
    binding.pop("file_extension")
    restored_binding = from_data(binding)
    assert restored_binding.role == PayloadRole.DOCUMENT
    assert restored_binding.file_extension == ".sha256"


def test_legacy_unknown_payload_retains_safe_source_extension() -> None:
    raw = to_data(
        BrepPayload(
            "unknown",
            "future.cad",
            "opaque",
            "v9",
            hashlib.sha256(b"unknown").hexdigest(),
            data=b"unknown",
            source_stream="Container/Opaque.future",
        )
    )
    raw.pop("role")
    raw.pop("file_extension")
    restored = from_data(raw)
    assert restored.role == PayloadRole.AUXILIARY
    assert restored.file_extension == ".future"
    assert restored.data == b"unknown"


def test_every_capability_roundtrips_losslessly() -> None:
    capabilities = frozenset(Capability)
    restored = CadDocument.from_json(
        replace(document(), capabilities=capabilities).to_json()
    )
    assert restored.capabilities == capabilities


def test_document_filter_projects_nested_representation_data() -> None:
    from tests.interchange.test_assembly import assembly_document

    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    component = assembly.documents[0]
    child = component.document
    assert isinstance(child, CadDocument)
    payloads = tuple(
        BrepPayload(
            f"payload:{role.value}",
            "future.cad",
            role.value,
            "1",
            hashlib.sha256(role.value.encode("ascii")).hexdigest(),
            data=role.value.encode("ascii"),
            role=role,
        )
        for role in (
            PayloadRole.BREP,
            PayloadRole.TESSELLATION,
            PayloadRole.AUXILIARY,
        )
    )
    child = replace(
        child,
        brep_payloads=payloads,
        capabilities=child.capabilities
        | {
            Capability.BREP,
            Capability.TESSELLATION,
            Capability.NATIVE_PAYLOADS,
        },
    )
    source = replace(
        source,
        capabilities=source.capabilities
        | {
            Capability.BREP,
            Capability.TESSELLATION,
            Capability.NATIVE_PAYLOADS,
        },
        assembly=replace(
            assembly,
            documents=(replace(component, document=child),),
        ),
    )
    filtered = filter_document(
        source,
        include_brep=False,
        include_tessellation=False,
        keep_payload_records=False,
    )
    assert Capability.BREP not in filtered.capabilities
    assert Capability.TESSELLATION not in filtered.capabilities
    filtered_child = filtered.assembly.documents[0].document
    assert isinstance(filtered_child, CadDocument)
    assert tuple(payload.role for payload in filtered_child.brep_payloads) == (
        PayloadRole.AUXILIARY,
    )
    assert Capability.BREP not in filtered_child.capabilities
    assert Capability.TESSELLATION not in filtered_child.capabilities
    described = filter_document(
        source,
        include_brep=False,
        include_tessellation=False,
        keep_payload_records=True,
    )
    described_child = described.assembly.documents[0].document
    assert isinstance(described_child, CadDocument)
    assert tuple(payload.role for payload in described_child.brep_payloads) == tuple(
        payload.role for payload in payloads
    )
    assert tuple(payload.data for payload in described_child.brep_payloads) == (
        None,
        None,
        b"auxiliary",
    )


def test_document_rejects_non_capability_values() -> None:
    invalid = replace(document(), capabilities=frozenset({"parameters"}))
    with pytest.raises(CadDocumentValidationError, match="Capability values"):
        invalid.assert_valid()


def test_capability_inference_is_exhaustive_and_data_driven() -> None:
    source = replace(document(), capabilities=frozenset())
    assert infer_capabilities(source) == frozenset(
        {
            Capability.PARAMETRIC_HISTORY,
            Capability.SUPPORT_PLANES,
            Capability.EDITABLE_SKETCHES,
            Capability.BODY_STRUCTURE,
            Capability.CONFIGURATIONS,
        }
    )
    imported = replace(
        source,
        feature_timeline=(
            replace(source.feature_timeline[0], kind=FeatureKind.IMPORTED),
        ),
    )
    assert Capability.PARAMETRIC_HISTORY not in infer_capabilities(imported)


def test_assembly_children_are_ordered_with_stable_ties() -> None:
    definitions = (
        ComponentDefinition("root", "Root", ComponentKind.ASSEMBLY),
        ComponentDefinition("part", "Part", ComponentKind.PART),
    )
    second = ComponentInstance("second", "Second", "part", "root", order=1)
    first = ComponentInstance("first", "First", "part", "root", order=1)
    assembly = AssemblyData("root", definitions, (second, first))
    assert assembly.children("root") == (first, second)
    capabilities = infer_capabilities(replace(document(), assembly=assembly))
    assert Capability.ASSEMBLIES in capabilities
    assert Capability.ASSEMBLY_MATES not in capabilities


@pytest.mark.parametrize(
    "extension",
    (
        "brep",
        ".",
        "..",
        "../brep",
        ".x/b",
        ".x:stream",
        ".x*",
        ".x?",
        '.x"',
        ".x<",
        ".x>",
        ".x|",
        ".x.",
        ".é",
    ),
)
def test_payload_file_extension_rejects_unsafe_values(extension: str) -> None:
    with pytest.raises(ValueError, match="file extension"):
        BrepPayload("geometry", "kernel", "shape", "", "", file_extension=extension)


def test_payload_role_requires_the_payload_role_enum() -> None:
    with pytest.raises(TypeError, match="PayloadRole"):
        BrepPayload(
            "geometry",
            "kernel",
            "shape",
            "",
            "",
            role="brep",
            file_extension=".brep",
        )


def test_forward_feature_dependency_is_rejected() -> None:
    source = document()
    first = FeatureStep(
        "feature:0",
        "Invalid",
        FeatureKind.EXTRUSION,
        0,
        input_feature_ids=("feature:1",),
    )
    second = FeatureStep("feature:1", "Later", FeatureKind.EXTRUSION, 1)
    invalid = CadDocument(
        source=source.source,
        configurations=source.configurations,
        parameters=(),
        support_planes=source.support_planes,
        sketches=(),
        selections=(),
        feature_timeline=(first, second),
        bodies=(Body("body:1", "Body", second.id),),
    )
    with pytest.raises(CadDocumentValidationError, match="forward dependency"):
        invalid.assert_valid()
