# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import is_dataclass as IsDataClass
from dataclasses import replace as ReplaceValue
from importlib import import_module as ImportModule
from interchange import (
    BrepBody,
    BrepCoedge,
    BrepCurve,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepPcurve,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepSurface,
    BrepVertex,
    CadDocument,
    Capability,
    LineCurve,
    NurbsCurve,
    PlaneSurface,
    Transform,
    SpaceVector,
    FilterDocument,
    InferCaps,
)
from tests.interchange.document.DocumentTests import BuildDocument

# dynamic package loading lets reflection inspect the facade without mixed import forms
KInterchangeApi = ImportModule("interchange")


# behavior coverage protects portable interchange semantics during structural refactors
def BuildTriangle() -> BrepModel:
    Vertices = (
        BrepVertex("vertex:0", SpaceVector(0.0, 0.0, 0.0)),
        BrepVertex("vertex:1", SpaceVector(1.0, 0.0, 0.0)),
        BrepVertex("vertex:2", SpaceVector(0.0, 1.0, 0.0)),
    )
    Curves = (
        LineCurve("curve:0", SpaceVector(0.0, 0.0, 0.0), SpaceVector(1.0, 0.0, 0.0)),
        LineCurve("curve:1", SpaceVector(1.0, 0.0, 0.0), SpaceVector(-1.0, 1.0, 0.0)),
        LineCurve("curve:2", SpaceVector(0.0, 1.0, 0.0), SpaceVector(0.0, -1.0, 0.0)),
    )
    Edges = tuple(
        (
            BrepEdge(
                f"edge:{IndexValue}",
                f"vertex:{IndexValue}",
                f"vertex:{(IndexValue + 1) % 3}",
                f"curve:{IndexValue}",
                0.0,
                1.0,
            )
            for IndexValue in range(3)
        )
    )
    Coedges = tuple(
        (
            BrepCoedge(f"coedge:{IndexValue}", f"edge:{IndexValue}")
            for IndexValue in range(3)
        )
    )
    return BrepModel(
        Curves=Curves,
        Surfaces=(
            PlaneSurface(
                "surface:0",
                SpaceVector(0.0, 0.0, 0.0),
                SpaceVector(0.0, 0.0, 1.0),
                SpaceVector(1.0, 0.0, 0.0),
            ),
        ),
        Vertices=Vertices,
        Edges=Edges,
        Coedges=Coedges,
        Loops=(
            BrepLoop(
                "loop:0", tuple((ItemValue.EntityId for ItemValue in Coedges)), True
            ),
        ),
        Faces=(BrepFace("face:0", "surface:0", ("loop:0",)),),
        FaceUses=(BrepFaceUse("face-use:0", "face:0"),),
        Shells=(BrepShell("shell:0", ("face-use:0",), False),),
        ShellUses=(BrepShellUse("shell-use:0", "shell:0"),),
        Regions=(BrepRegion("region:0", ("shell-use:0",), False),),
        Bodies=(BrepBody("brep-body:0", ("region:0",), Transform(), "body:1"),),
    )


# historical imports keep conversion suites independent from helper renaming
triangle_brep = BuildTriangle


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRoundtrip() -> None:
    SourceValue = ReplaceValue(
        BuildDocument(), brep=BuildTriangle(), capabilities=frozenset()
    )
    SourceValue.assert_valid()
    assert Capability.KBrep in InferCaps(SourceValue)
    RestoredValue = CadDocument.from_json(SourceValue.to_json())
    assert RestoredValue == SourceValue


# behavior coverage protects portable interchange semantics during structural refactors
def CheckBaseTypes() -> None:
    SourceValue = ReplaceValue(
        BuildDocument(),
        brep=BuildTriangle(),
        capabilities=frozenset({Capability.KBrep, Capability.KParamHistory}),
    )
    FilteredValue = FilterDocument(
        SourceValue, IncludeBrep=False, IncludeMesh=True, KeepPayloads=True
    )
    assert FilteredValue.brep is None
    assert Capability.KBrep not in FilteredValue.capabilities
    assert Capability.KParamHistory in FilteredValue.capabilities


# behavior coverage protects portable interchange semantics during structural refactors
def CheckBadRefs() -> None:
    ModelValue = BuildTriangle()
    BrokenValue = ReplaceValue(
        ModelValue, Edges=(ReplaceValue(ModelValue.Edges[0], CurveId="missing"),)
    )
    ErrorValues = BrokenValue.GetErrors(frozenset({"body:1"}))
    assert any(("missing curve" in ErrorText for ErrorText in ErrorValues))


# behavior coverage protects portable interchange semantics during structural refactors
def CheckBadSpline() -> None:
    ModelValue = BuildTriangle()
    InvalidCurve = NurbsCurve(
        "curve:0",
        2,
        (
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(0.5, 0.5, 0.0),
            SpaceVector(1.0, 0.0, 0.0),
        ),
        (0.0, 1.0),
        (2, 2),
    )
    InvalidValue = ReplaceValue(
        ModelValue, Curves=(InvalidCurve, *ModelValue.Curves[1:]), SchemaVersion=""
    )
    ErrorValues = InvalidValue.GetErrors(frozenset({"body:1"}))
    assert "B-rep schema version must be a non-empty string" in ErrorValues
    assert "B-rep curve curve:0 is invalid" in ErrorValues


# behavior coverage protects portable interchange semantics during structural refactors
def CheckCoverage() -> None:
    FamilyTypes = (BrepCurve, BrepPcurve, BrepSurface)
    ItemValues = {
        ItemValue
        for NameValue, ItemValue in vars(KInterchangeApi).items()
        if not NameValue.startswith("_")
        and isinstance(ItemValue, type)
        and IsDataClass(ItemValue)
        and (ItemValue not in FamilyTypes)
        and any((issubclass(ItemValue, FamilyType) for FamilyType in FamilyTypes))
    }
    assert ItemValues
    for ItemValue in ItemValues:
        assert (
            sum((issubclass(ItemValue, FamilyType) for FamilyType in FamilyTypes)) == 1
        )
