# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import replace as ReplaceValue
import pytest as PytestLib
from interchange import (
    AssemblyData,
    CadDocument,
    DocumentError,
    CadSource,
    Capability,
    ComponentDef,
    ComponentDoc,
    ComponentInst,
    ComponentKind,
    Configuration,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateKind,
    TransformMatrix,
    SurfaceMesh,
    SpaceVector,
)
from tests.interchange.document.DocumentTests import BuildDocument


# behavior coverage protects portable interchange semantics during structural refactors
def BuildAssembly() -> CadDocument:
    PartValue = BuildDocument()
    RootValue = ComponentDef("definition:root", "Engine", ComponentKind.KAssembly)
    Subassembly = ComponentDef(
        "definition:subassembly", "Piston", ComponentKind.KAssembly
    )
    PartDef = ComponentDef(
        "definition:part",
        "Piston",
        ComponentKind.KPart,
        DocumentId="document:part",
        BodyIds=("body:1",),
    )
    SubassemblyInst = ComponentInst(
        "instance:subassembly",
        "Piston-1",
        Subassembly.EntityId,
        RootValue.EntityId,
        TransformMatrix(
            (
                1.0,
                0.0,
                0.0,
                100.0,
                0.0,
                1.0,
                0.0,
                20.0,
                0.0,
                0.0,
                1.0,
                30.0,
                0.0,
                0.0,
                0.0,
                1.0,
            )
        ),
    )
    PartInstance = ComponentInst(
        "instance:part", "Piston-1", PartDef.EntityId, Subassembly.EntityId
    )
    FirstEntity = MateEntity(
        "mate-entity:assembly",
        RootValue.EntityId,
        (),
        MateEntityKind.KPlane,
        SourceEntityId="plane:front",
    )
    SecondEntity = MateEntity(
        "mate-entity:part",
        RootValue.EntityId,
        (SubassemblyInst.EntityId, PartInstance.EntityId),
        MateEntityKind.KPlane,
        SourceEntityId="plane:xy",
    )
    MateValue = MateConstraint(
        "mate:1",
        "Coincident1",
        MateKind.KCoincident,
        RootValue.EntityId,
        (FirstEntity.EntityId, SecondEntity.EntityId),
    )
    AssemblyValue = AssemblyData(
        RootValue.EntityId,
        (RootValue, Subassembly, PartDef),
        (SubassemblyInst, PartInstance),
        Documents=(ComponentDoc("document:part", PartValue),),
        MateEntities=(FirstEntity, SecondEntity),
        Mates=(MateValue,),
    )
    return CadDocument(
        Source=CadSource("test.assembly", "memory", "1" * 64),
        Configurations=(Configuration("config:default", "Default", True),),
        Parameters=(),
        SupportPlanes=(),
        Sketches=(),
        Selections=(),
        FeatureTimeline=(),
        Bodies=(),
        Capabilities=frozenset({Capability.KAssemblies}),
        Assembly=AssemblyValue,
    )


# historical imports keep conversion suites independent from helper renaming
def __getattr__(NameText: str) -> object:
    if NameText == "assembly_document":
        return BuildAssembly
    raise AttributeError(f"module {__name__!r} has no attribute {NameText!r}")


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRoundtrip() -> None:
    SourceValue = BuildAssembly()
    SourceValue.AssertValid()
    RestoredValue = CadDocument.FromJson(SourceValue.ToJson())
    assert RestoredValue == SourceValue
    assert RestoredValue.Assembly is not None
    EmbeddedValue = RestoredValue.Assembly.Document("document:part")
    assert isinstance(EmbeddedValue, CadDocument)
    assert EmbeddedValue == BuildDocument()
    assert RestoredValue.Assembly.GetChildren("definition:root") == (
        RestoredValue.Assembly.Instances[0],
    )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckTransform() -> None:
    TransformValue = BuildAssembly().Assembly.Instances[0].Transform
    assert TransformValue.TransformPoint((1.0, 2.0, 3.0)) == (101.0, 22.0, 33.0)
    assert TransformValue.GetRows()[0] == (1.0, 0.0, 0.0, 100.0)
    assert TransformValue.rows() == TransformValue.GetRows()


# behavior coverage protects portable interchange semantics during structural refactors
def CheckCycle() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.Assembly
    assert AssemblyValue is not None
    CycleValue = ComponentInst(
        "instance:cycle",
        "Engine-1",
        AssemblyValue.RootDefinitionId,
        "definition:subassembly",
    )
    InvalidValue = ReplaceValue(
        SourceValue,
        Assembly=ReplaceValue(
            AssemblyValue, Instances=(*AssemblyValue.Instances, CycleValue)
        ),
    )
    with PytestLib.raises(DocumentError, match="contains a cycle"):
        InvalidValue.AssertValid()


# behavior coverage protects portable interchange semantics during structural refactors
def CheckBadLinks() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.Assembly
    assert AssemblyValue is not None
    InvalidInst = ReplaceValue(
        AssemblyValue.Instances[0], Transform=TransformMatrix((1.0,) * 15)
    )
    InvalidEntity = ReplaceValue(
        AssemblyValue.MateEntities[1], InstancePath=("instance:part",)
    )
    InvalidValue = ReplaceValue(
        SourceValue,
        Assembly=ReplaceValue(
            AssemblyValue,
            Instances=(InvalidInst, *AssemblyValue.Instances[1:]),
            MateEntities=(AssemblyValue.MateEntities[0], InvalidEntity),
        ),
    )
    ErrorValues = InvalidValue.GetErrors()
    assert (
        "component instance instance:subassembly has an invalid transform"
        in ErrorValues
    )
    assert (
        "mate entity mate-entity:part has a disconnected instance path" in ErrorValues
    )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckMeshRound() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.Assembly
    assert AssemblyValue is not None
    MeshValue = SurfaceMesh(
        "mesh:1",
        "Piston face",
        (
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(1.0, 0.0, 0.0),
            SpaceVector(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
        Normals=(SpaceVector(0.0, 0.0, 1.0),) * 3,
    )
    Definitions = tuple(
        (
            (
                ReplaceValue(DefinitionValue, MeshIds=(MeshValue.EntityId,))
                if DefinitionValue.EntityId == "definition:part"
                else DefinitionValue
            )
            for DefinitionValue in AssemblyValue.Definitions
        )
    )
    ExtendedValue = ReplaceValue(
        SourceValue,
        Meshes=(MeshValue,),
        Assembly=ReplaceValue(AssemblyValue, Definitions=Definitions),
    )
    ExtendedValue.AssertValid()
    RestoredValue = CadDocument.FromJson(ExtendedValue.ToJson())
    assert RestoredValue == ExtendedValue


# behavior coverage protects portable interchange semantics during structural refactors
def CheckMeshErrors() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.Assembly
    assert AssemblyValue is not None
    MeshValue = SurfaceMesh(
        "mesh:invalid",
        "Invalid",
        (SpaceVector(float("nan"), 0.0, 0.0),),
        ((0, 1, 2),),
        Normals=(SpaceVector(0.0, 0.0, 1.0), SpaceVector(0.0, 0.0, 1.0)),
    )
    InvalidValue = ReplaceValue(SourceValue, Meshes=(MeshValue,))
    ErrorValues = InvalidValue.GetErrors()
    assert "mesh mesh:invalid contains a non-finite vertex" in ErrorValues
    assert "mesh mesh:invalid has a mismatched normal count" in ErrorValues
    assert "mesh mesh:invalid contains an invalid triangle" in ErrorValues


# behavior coverage protects portable interchange semantics during structural refactors
def CheckChildError() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.Assembly
    assert AssemblyValue is not None
    LinkedValue = AssemblyValue.Documents[0]
    InvalidLinked = ReplaceValue(LinkedValue.Document, Configurations=())
    InvalidValue = ReplaceValue(
        SourceValue,
        Assembly=ReplaceValue(
            AssemblyValue,
            Documents=(ReplaceValue(LinkedValue, Document=InvalidLinked),),
        ),
    )
    assert (
        "component document document:part: document has no configuration"
        in InvalidValue.GetErrors()
    )
