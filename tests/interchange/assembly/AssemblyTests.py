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
    CadDocument,
    DocumentError,
    ComponentInst,
    TransformMatrix,
    SurfaceMesh,
    SpaceVector,
)
from tests.interchange.document.DocumentTests import BuildDocument
from tests.interchange.fixtures.AssemblyFixture import (
    BuildAssembly as BuildFixtureAssembly,
)


# behavior coverage protects portable interchange semantics during structural refactors
def BuildAssembly() -> CadDocument:
    return BuildFixtureAssembly()


# historical imports keep conversion suites independent from helper renaming
assembly_document = BuildAssembly


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRoundtrip() -> None:
    SourceValue = BuildAssembly()
    SourceValue.assert_valid()
    RestoredValue = CadDocument.from_json(SourceValue.to_json())
    assert RestoredValue == SourceValue
    assert RestoredValue.assembly is not None
    EmbeddedValue = RestoredValue.assembly.GetDocument("document:part")
    assert isinstance(EmbeddedValue, CadDocument)
    assert EmbeddedValue == BuildDocument()
    assert RestoredValue.assembly.GetChildren("definition:root") == (
        RestoredValue.assembly.Instances[0],
    )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckTransform() -> None:
    AssemblyValue = BuildAssembly().assembly
    assert AssemblyValue is not None
    TransformValue = AssemblyValue.Instances[0].Transform
    assert TransformValue.TransformPoint((1.0, 2.0, 3.0)) == (101.0, 22.0, 33.0)
    assert TransformValue.GetRows()[0] == (1.0, 0.0, 0.0, 100.0)
    assert TransformValue.GetRows() == TransformValue.GetRows()


# behavior coverage protects portable interchange semantics during structural refactors
def CheckCycle() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.assembly
    assert AssemblyValue is not None
    CycleValue = ComponentInst(
        "instance:cycle",
        "Engine-1",
        AssemblyValue.RootDefinitionId,
        "definition:subassembly",
    )
    InvalidValue = ReplaceValue(
        SourceValue,
        assembly=ReplaceValue(
            AssemblyValue, Instances=(*AssemblyValue.Instances, CycleValue)
        ),
    )
    with PytestLib.raises(DocumentError, match="contains a cycle"):
        InvalidValue.assert_valid()


# behavior coverage protects portable interchange semantics during structural refactors
def CheckBadLinks() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.assembly
    assert AssemblyValue is not None
    InvalidInst = ReplaceValue(
        AssemblyValue.Instances[0], Transform=TransformMatrix((1.0,) * 15)
    )
    InvalidEntity = ReplaceValue(
        AssemblyValue.MateEntities[1], InstancePath=("instance:part",)
    )
    InvalidValue = ReplaceValue(
        SourceValue,
        assembly=ReplaceValue(
            AssemblyValue,
            Instances=(InvalidInst, *AssemblyValue.Instances[1:]),
            MateEntities=(AssemblyValue.MateEntities[0], InvalidEntity),
        ),
    )
    ErrorValues = InvalidValue.validate()
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
    AssemblyValue = SourceValue.assembly
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
        meshes=(MeshValue,),
        assembly=ReplaceValue(AssemblyValue, Definitions=Definitions),
    )
    ExtendedValue.assert_valid()
    RestoredValue = CadDocument.from_json(ExtendedValue.to_json())
    assert RestoredValue == ExtendedValue


# behavior coverage protects portable interchange semantics during structural refactors
def CheckMeshErrors() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.assembly
    assert AssemblyValue is not None
    MeshValue = SurfaceMesh(
        "mesh:invalid",
        "Invalid",
        (SpaceVector(float("nan"), 0.0, 0.0),),
        ((0, 1, 2),),
        Normals=(SpaceVector(0.0, 0.0, 1.0), SpaceVector(0.0, 0.0, 1.0)),
    )
    InvalidValue = ReplaceValue(SourceValue, meshes=(MeshValue,))
    ErrorValues = InvalidValue.validate()
    assert "mesh mesh:invalid contains a non-finite vertex" in ErrorValues
    assert "mesh mesh:invalid has a mismatched normal count" in ErrorValues
    assert "mesh mesh:invalid contains an invalid triangle" in ErrorValues


# behavior coverage protects portable interchange semantics during structural refactors
def CheckChildError() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.assembly
    assert AssemblyValue is not None
    LinkedValue = AssemblyValue.Documents[0]
    InvalidLinked = ReplaceValue(LinkedValue.Document, configurations=())
    InvalidValue = ReplaceValue(
        SourceValue,
        assembly=ReplaceValue(
            AssemblyValue,
            Documents=(ReplaceValue(LinkedValue, Document=InvalidLinked),),
        ),
    )
    assert (
        "component document document:part: document has no configuration"
        in InvalidValue.validate()
    )
