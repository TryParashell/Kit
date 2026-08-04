# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
from typing import get_args, get_origin, get_type_hints

import interchange
import pytest
from interchange import (
    AssemblyData,
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    ComponentDefinition,
    ComponentDocument,
    ComponentInstance,
    ComponentKind,
    Configuration,
    Expression,
    FeatureDefinition,
    FeatureStep,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateKind,
    Mesh,
    Parameter,
    ParameterValue,
    PayloadRole,
    Provenance,
    Selection,
    Vector3,
    infer_capabilities,
)
from interchange.document import _identified_collection_fields
from interchange.geometry import Geometry

from tests.interchange.test_document import document


@dataclass(frozen=True, slots=True)
class _FutureFeatureDefinition(FeatureDefinition):
    value: str


def _identified_fields(value_type: type[object]) -> set[str]:
    hints = get_type_hints(value_type)
    result: set[str] = set()
    for item in fields(value_type):
        hint = hints[item.name]
        arguments = get_args(hint)
        if (
            get_origin(hint) is tuple
            and len(arguments) == 2
            and arguments[1] is Ellipsis
            and isinstance(arguments[0], type)
            and is_dataclass(arguments[0])
            and any(member.name == "id" for member in fields(arguments[0]))
        ):
            result.add(item.name)
    return result


def test_identity_collection_discovery_covers_every_typed_entity_tuple() -> None:
    for value_type in (CadDocument, AssemblyData):
        assert {
            name for name, _ in _identified_collection_fields(value_type)
        } == _identified_fields(value_type)


def test_geometry_union_contains_every_geometry_dataclass() -> None:
    expected = {
        value
        for name, value in vars(interchange.geometry).items()
        if name.endswith("Geometry") and isinstance(value, type) and is_dataclass(value)
    }
    assert set(get_args(Geometry)) == expected


def test_feature_definition_contract_accepts_future_definition_types() -> None:
    definition_hint = get_type_hints(FeatureStep)["definition"]
    assert set(get_args(definition_hint)) == {FeatureDefinition, type(None)}
    definitions = {
        value
        for value in vars(interchange).values()
        if isinstance(value, type)
        and is_dataclass(value)
        and issubclass(value, FeatureDefinition)
    }
    assert definitions
    step = replace(
        document().feature_timeline[0],
        definition=_FutureFeatureDefinition("future"),
    )
    assert isinstance(step.definition, FeatureDefinition)
    with pytest.raises(TypeError, match="feature definition"):
        replace(step, definition={"type": "unregistered"})


def test_public_interchange_enums_have_no_hidden_aliases() -> None:
    enum_types = {
        value
        for name, value in vars(interchange).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and issubclass(value, Enum)
    }
    assert enum_types
    for enum_type in enum_types:
        assert tuple(enum_type.__members__.values()) == tuple(enum_type)
        assert len({member.value for member in enum_type}) == len(enum_type)


def test_nested_capability_inference_is_exhaustive_and_data_driven() -> None:
    base = document()
    parameter = Parameter(
        "parameter:child",
        "Child parameter",
        ParameterValue(1.0),
        expression=Expression("1.0"),
        provenance=Provenance("test", "parameter"),
    )
    brep_data = b"nested-brep"
    payload = BrepPayload(
        "payload:child",
        "test.brep",
        "shape",
        "1",
        hashlib.sha256(brep_data).hexdigest(),
        data=brep_data,
        role=PayloadRole.BREP,
        file_extension=".brep",
    )
    mesh = Mesh(
        "mesh:child",
        "Child mesh",
        (Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    child = replace(
        base,
        parameters=(parameter,),
        selections=(Selection("selection:child", "Child selection", ()),),
        bodies=(replace(base.bodies[0], material_id="material:child"),),
        meshes=(mesh,),
        brep_payloads=(payload,),
        capabilities=frozenset(),
    )
    root_definition = ComponentDefinition(
        "definition:root", "Root", ComponentKind.ASSEMBLY
    )
    child_definition = ComponentDefinition(
        "definition:child",
        "Child",
        ComponentKind.PART,
        document_id="document:child",
        source_path="Child.FCStd",
    )
    instance = ComponentInstance(
        "instance:child",
        "Child",
        child_definition.id,
        root_definition.id,
    )
    mate_entity = MateEntity(
        "mate-entity:root",
        root_definition.id,
        (),
        MateEntityKind.PLANE,
    )
    mate = MateConstraint(
        "mate:root",
        "Root mate",
        MateKind.COINCIDENT,
        root_definition.id,
        (mate_entity.id,),
    )
    assembly = AssemblyData(
        root_definition.id,
        (root_definition, child_definition),
        (instance,),
        documents=(ComponentDocument("document:child", child),),
        mate_entities=(mate_entity,),
        mates=(mate,),
    )
    root = CadDocument(
        source=CadSource("test.assembly", "Root", "1" * 64),
        configurations=(Configuration("configuration:root", "Default", True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        capabilities=frozenset(Capability),
        assembly=assembly,
    )
    root.assert_valid()
    assert infer_capabilities(root) == frozenset(Capability) - {
        Capability.ROUNDTRIP_METADATA
    }
    assert infer_capabilities(root, roundtrip_metadata=True) == frozenset(Capability)
    stale_child = replace(base, capabilities=frozenset(Capability))
    stale_assembly = replace(
        assembly,
        definitions=(root_definition, replace(child_definition, source_path="")),
        documents=(ComponentDocument("document:child", stale_child),),
        mate_entities=(),
        mates=(),
    )
    stale_root = replace(
        root,
        assembly=stale_assembly,
        capabilities=frozenset(),
    )
    assert not infer_capabilities(stale_root) & {
        Capability.ASSEMBLY_MATES,
        Capability.BREP,
        Capability.EXPRESSIONS,
        Capability.EXTERNAL_REFERENCES,
        Capability.MATERIALS,
        Capability.NATIVE_PAYLOADS,
        Capability.PARAMETERS,
        Capability.PROVENANCE,
        Capability.ROUNDTRIP_METADATA,
        Capability.SELECTIONS,
        Capability.TESSELLATION,
    }
