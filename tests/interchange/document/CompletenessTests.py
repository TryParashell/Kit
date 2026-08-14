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
from typing import get_args as GetTypeArgs
from typing import get_origin as GetTypeOrigin
from typing import get_type_hints as GetTypeHints
import interchange as InterchangeApi
import pytest as PytestLib
from interchange import (
    AssemblyData,
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    ComponentDef,
    ComponentDoc,
    ComponentInst,
    ComponentKind,
    Configuration,
    Expression,
    FeatureDefinition,
    FeatureStep,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateKind,
    SurfaceMesh,
    Parameter,
    ParameterValue,
    PayloadRole,
    Provenance,
    Selection,
    SelectionPathElement,
    SpaceVector,
    InferCaps,
)
from interchange.document.models.DocumentIdentity import GetIdFields
from interchange.geometry import Geometry
from interchange.serialization import FromData, ToData
from interchange.serialization.Wire import GetWireField
from tests.interchange.document.DocumentTests import BuildDocument


# behavior coverage protects portable interchange semantics during structural refactors
@DataClass(frozen=True, slots=True)
class FutureFeature(FeatureDefinition):
    ItemValue: str


# behavior coverage protects portable interchange semantics during structural refactors
def GetExpectedIds(ValueType: type[object]) -> set[str]:
    TypeHints = GetTypeHints(ValueType)
    ResultValue: set[str] = set()
    for FieldValue in GetFields(ValueType):
        FieldHint = TypeHints[FieldValue.name]
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
            ResultValue.add(FieldValue.name)
    return ResultValue


# behavior coverage protects portable interchange semantics during structural refactors
def CheckIdFields() -> None:
    for ValueType in (CadDocument, AssemblyData):
        assert {
            NameValue for NameValue, LabelText in GetIdFields(ValueType)
        } == GetExpectedIds(ValueType)


# behavior coverage protects portable interchange semantics during structural refactors
def CheckGeometry() -> None:
    ExpectedValues = {
        ItemValue
        for NameValue, ItemValue in vars(InterchangeApi.geometry).items()
        if NameValue.endswith(("Geometry", "Geom"))
        and isinstance(ItemValue, type)
        and IsDataClass(ItemValue)
    }
    assert set(GetTypeArgs(Geometry)) == ExpectedValues


# behavior coverage protects portable interchange semantics during structural refactors
def CheckFeatures() -> None:
    DefinitionHint = GetTypeHints(FeatureStep)["Definition"]
    assert set(GetTypeArgs(DefinitionHint)) == {FeatureDefinition, type(None)}
    Definitions = {
        ItemValue
        for ItemValue in vars(InterchangeApi).values()
        if isinstance(ItemValue, type)
        and IsDataClass(ItemValue)
        and issubclass(ItemValue, FeatureDefinition)
    }
    assert Definitions
    StepValue = ReplaceValue(
        BuildDocument().FeatureTimeline[0], Definition=FutureFeature("future")
    )
    assert isinstance(StepValue.Definition, FeatureDefinition)
    with PytestLib.raises(TypeError, match="feature definition"):
        ReplaceValue(StepValue, Definition={"type": "unregistered"})


# behavior coverage protects portable interchange semantics during structural refactors
def CheckEnums() -> None:
    EnumTypes = {
        ItemValue
        for NameValue, ItemValue in vars(InterchangeApi).items()
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
        Parameters=(ParamValue,),
        Selections=(Selection("selection:child", "Child selection", ()),),
        Bodies=(ReplaceValue(BaseValue.Bodies[0], MaterialId="material:child"),),
        Meshes=(MeshValue,),
        BrepPayloads=(PayloadValue,),
        Capabilities=frozenset(),
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
        Source=CadSource("test.assembly", "Root", "1" * 64),
        Configurations=(Configuration("configuration:root", "Default", True),),
        Parameters=(),
        SupportPlanes=(),
        Sketches=(),
        Selections=(),
        FeatureTimeline=(),
        Bodies=(),
        Capabilities=frozenset(Capability),
        Assembly=AssemblyValue,
    )
    RootValue.AssertValid()
    assert InferCaps(RootValue) == frozenset(Capability) - {Capability.KRoundtripMeta}
    assert InferCaps(RootValue, RoundtripMeta=True) == frozenset(Capability)
    StaleChild = ReplaceValue(BaseValue, Capabilities=frozenset(Capability))
    StaleAssembly = ReplaceValue(
        AssemblyValue,
        Definitions=(RootDef, ReplaceValue(ChildDef, SourcePath="")),
        Documents=(ComponentDoc("document:child", StaleChild),),
        MateEntities=(),
        Mates=(),
    )
    StaleRoot = ReplaceValue(
        RootValue, Assembly=StaleAssembly, Capabilities=frozenset()
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
    assert ReplacedDoc.Metadata == {"compatibility": "preserved"}


# serialization keys stay byte compatible so stored interchange documents remain readable
def CheckWireFields() -> None:
    PathValue = SelectionPathElement("feature", "feature:one", "Face1")
    SelectionValue = Selection("selection:one", "Selection", (PathValue,))
    RawValue = ToData(SelectionValue)
    assert "path" in RawValue
    assert "selection_path" not in RawValue
    PathData = RawValue["path"]["$tuple"][0]
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
    assert SourceValue.to_json(indent=None) == SourceValue.ToJson(IndentSize=None)


# historical field access takes precedence over similarly named document lookup methods
def CheckFieldAlias() -> None:
    SourceValue = BuildDocument()
    FeatureValue = SourceValue.FeatureTimeline[0]
    assert FeatureValue.definition is FeatureValue.Definition
