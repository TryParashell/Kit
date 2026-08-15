# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass
from dataclasses import fields as GetFields
from dataclasses import is_dataclass as IsDataClass
from dataclasses import replace as ReplaceValue
from enum import Enum as EnumBase
import hashlib as HashCodec
from importlib import import_module as ImportModule
from typing import get_args as GetTypeArgs
from typing import get_origin as GetTypeOrigin
from typing import get_type_hints as GetTypeHints
from typing import cast as CastValue
import pytest as PytestLib
from interchange import geometry as GeometryModule
from interchange import (
    AssemblyData,
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    ComponentKind,
    Configuration,
    Expression,
    FeatureDefinition,
    FeatureStep,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateKind,
    Parameter,
    ParameterValue,
    PayloadRole,
    Provenance,
    Selection,
    SelectionPathElement,
    SpaceVector,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.models.DocumentCaps import InferCaps
from interchange.document.models.DocumentIdentity import GetIdFields
from interchange.geometry import Geometry
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from interchange.serialization.Wire import GetWireField
from tests.interchange.document.DocumentTests import BuildDocument

# dynamic package loading lets reflection inspect the facade without mixed import forms
KInterchangeApi = ImportModule("interchange")


# behavior coverage protects portable interchange semantics during structural refactors
@DataClass(frozen=True, slots=True)
class FutureFeature(FeatureDefinition):
    ItemValue: str


# behavior coverage protects portable interchange semantics during structural refactors
def GetExpectedIds(ValueType: type[CadDocument] | type[AssemblyData]) -> set[str]:
    TypeHints = GetTypeHints(ValueType)
    ResultValue: set[str] = set()
    for FieldName, FieldHint in TypeHints.items():
        TypeArgs = GetTypeArgs(FieldHint)
        if (
            GetTypeOrigin(FieldHint) is tuple
            and len(TypeArgs) == 2
            and (TypeArgs[1] is Ellipsis)
            and isinstance(TypeArgs[0], type)
            and IsDataClass(TypeArgs[0])
            and any(
                (
                    GetWireField(MemberField.name, TypeArgs[0]) == "id"
                    for MemberField in GetFields(TypeArgs[0])
                )
            )
        ):
            ResultValue.add(FieldName)
    return ResultValue


# behavior coverage protects portable interchange semantics during structural refactors
def CheckIdFields() -> None:
    for ValueType in (CadDocument, AssemblyData):
        assert {NameValue for NameValue, _ in GetIdFields(ValueType)} == GetExpectedIds(
            ValueType
        )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckGeometry() -> None:
    ExpectedValues = {
        ItemValue
        for NameValue, ItemValue in vars(GeometryModule).items()
        if NameValue.endswith(("Geometry", "Geom"))
        and isinstance(ItemValue, type)
        and IsDataClass(ItemValue)
    }
    assert set(GetTypeArgs(Geometry)) == ExpectedValues


# behavior coverage protects portable interchange semantics during structural refactors
def CheckFeatures() -> None:
    DefinitionHint = GetTypeHints(FeatureStep)["definition"]
    assert set(GetTypeArgs(DefinitionHint)) == {FeatureDefinition, type(None)}
    Definitions = {
        ItemValue
        for ItemValue in vars(KInterchangeApi).values()
        if isinstance(ItemValue, type)
        and IsDataClass(ItemValue)
        and issubclass(ItemValue, FeatureDefinition)
    }
    assert Definitions
    StepValue = ReplaceValue(
        BuildDocument().feature_timeline[0], definition=FutureFeature("future")
    )
    assert isinstance(StepValue.definition, FeatureDefinition)
    with PytestLib.raises(TypeError, match="feature definition"):
        ReplaceValue(
            StepValue,
            definition=CastValue(FeatureDefinition, {"type": "unregistered"}),
        )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckEnums() -> None:
    EnumTypes = {
        ItemValue
        for NameValue, ItemValue in vars(KInterchangeApi).items()
        if not NameValue.startswith("_")
        and isinstance(ItemValue, type)
        and issubclass(ItemValue, EnumBase)
    }
    assert EnumTypes
    for EnumType in EnumTypes:
        assert tuple(EnumType.__members__.values()) == tuple(EnumType)
        assert len({MemberField.value for MemberField in EnumType}) == len(EnumType)


# behavior coverage protects portable interchange semantics during structural refactors
def CheckNestedCaps() -> None:
    BaseValue = BuildDocument()
    ParamValue = Parameter(
        "parameter:child",
        "Child parameter",
        ParameterValue(1.0),
        Expression=Expression("1.0"),
        Provenance=Provenance("test", "parameter"),
    )
    BrepData = b"nested-brep"
    PayloadValue = BrepPayload(
        "payload:child",
        "test.brep",
        "shape",
        "1",
        HashCodec.sha256(BrepData).hexdigest(),
        PayloadData=BrepData,
        ValueRole=PayloadRole.KBrep,
        FileExtension=".brep",
    )
    MeshValue = SurfaceMesh(
        "mesh:child",
        "Child mesh",
        (
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(1.0, 0.0, 0.0),
            SpaceVector(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
    )
    ChildValue = ReplaceValue(
        BaseValue,
        parameters=(ParamValue,),
        selections=(Selection("selection:child", "Child selection", ()),),
        bodies=(ReplaceValue(BaseValue.bodies[0], material_id="material:child"),),
        meshes=(MeshValue,),
        brep_payloads=(PayloadValue,),
        capabilities=frozenset(),
    )
    RootDef = ComponentDef("definition:root", "Root", ComponentKind.KAssembly)
    ChildDef = ComponentDef(
        "definition:child",
        "Child",
        ComponentKind.KPart,
        DocumentId="document:child",
        SourcePath="Child.FCStd",
    )
    InstanceValue = ComponentInst(
        "instance:child", "Child", ChildDef.EntityId, RootDef.EntityId
    )
    MateEntityValue = MateEntity(
        "mate-entity:root", RootDef.EntityId, (), MateEntityKind.KPlane
    )
    MateValue = MateConstraint(
        "mate:root",
        "Root mate",
        MateKind.KCoincident,
        RootDef.EntityId,
        (MateEntityValue.EntityId,),
    )
    AssemblyValue = AssemblyData(
        RootDef.EntityId,
        (RootDef, ChildDef),
        (InstanceValue,),
        Documents=(ComponentDoc("document:child", ChildValue),),
        MateEntities=(MateEntityValue,),
        Mates=(MateValue,),
    )
    RootValue = CadDocument(
        source=CadSource("test.assembly", "Root", "1" * 64),
        configurations=(Configuration("configuration:root", "Default", True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        capabilities=frozenset(Capability),
        assembly=AssemblyValue,
    )
    RootValue.assert_valid()
    assert InferCaps(RootValue) == frozenset(Capability) - {Capability.KRoundtripMeta}
    assert InferCaps(RootValue, RoundtripMeta=True) == frozenset(Capability)
    StaleChild = ReplaceValue(BaseValue, capabilities=frozenset(Capability))
    StaleAssembly = ReplaceValue(
        AssemblyValue,
        Definitions=(RootDef, ReplaceValue(ChildDef, SourcePath="")),
        Documents=(ComponentDoc("document:child", StaleChild),),
        MateEntities=(),
        Mates=(),
    )
    StaleRoot = ReplaceValue(
        RootValue, assembly=StaleAssembly, capabilities=frozenset()
    )
    assert not InferCaps(StaleRoot) & {
        Capability.KAssemblyMates,
        Capability.KBrep,
        Capability.KExpressions,
        Capability.KExternalRefs,
        Capability.KMaterials,
        Capability.KNativePayloads,
        Capability.KParameters,
        Capability.KProvenance,
        Capability.KRoundtripMeta,
        Capability.KSelections,
        Capability.KTessellation,
    }


# historical constructors must remain usable while adapters migrate independently
def CheckLegacyKeys() -> None:
    PathValue = SelectionPathElement(
        entity_kind="feature",
        entity_id="feature:one",
        subelement="Face1",
    )
    SelectionValue = Selection(
        id="selection:one",
        name="Selection",
        path=(PathValue,),
    )
    SourceValue = CadSource(
        format_id="test",
        path="source.FCStd",
        sha256="1" * 64,
    )
    assert SelectionValue.SelectionPath == (PathValue,)
    assert SourceValue.FilePath == "source.FCStd"
    assert SelectionValue.path == (PathValue,)
    assert SourceValue.path == "source.FCStd"
    ReplacedSource = ReplaceValue(SourceValue, path="updated.FCStd")
    assert ReplacedSource.FilePath == "updated.FCStd"
    ReplacedDoc = ReplaceValue(BuildDocument(), metadata={"compatibility": "preserved"})
    assert ReplacedDoc.metadata == {"compatibility": "preserved"}


# serialization keys stay byte compatible so stored interchange documents remain readable
def CheckWireFields() -> None:
    PathValue = SelectionPathElement("feature", "feature:one", "Face1")
    SelectionValue = Selection("selection:one", "Selection", (PathValue,))
    RawValue = ToData(SelectionValue)
    assert isinstance(RawValue, dict)
    assert "path" in RawValue
    assert "selection_path" not in RawValue
    PathTuple = RawValue["path"]
    assert isinstance(PathTuple, dict)
    PathItems = PathTuple["$tuple"]
    assert isinstance(PathItems, list)
    PathData = PathItems[0]
    assert isinstance(PathData, dict)
    assert PathData["entity_kind"] == "feature"
    assert PathData["entity_id"] == "feature:one"
    assert FromData(RawValue) == SelectionValue


# old capability keywords remain supported because converter modules upgrade independently
def CheckLegacyCaps() -> None:
    SourceValue = BuildDocument()
    assert InferCaps(SourceValue, roundtrip_metadata=True) == InferCaps(
        SourceValue,
        RoundtripMeta=True,
    )


# historical enum attributes stay available without becoming duplicate enum members
def CheckOldEnums() -> None:
    assert Capability.ROUNDTRIP_METADATA is Capability.KRoundtripMeta
    assert ComponentKind.ASSEMBLY is ComponentKind.KAssembly
    assert PayloadRole.BREP is PayloadRole.KBrep


# historical json options remain accepted because document consumers upgrade independently
def CheckLegacyJson() -> None:
    SourceValue = BuildDocument()
    LegacyJson = SourceValue.to_json
    assert callable(LegacyJson)
    assert LegacyJson(indent=None) == SourceValue.to_json(indent=None)


# historical field access takes precedence over similarly named document lookup methods
def CheckFieldAlias() -> None:
    SourceValue = BuildDocument()
    FeatureValue = SourceValue.feature_timeline[0]
    assert FeatureValue.definition is FeatureValue.Definition
