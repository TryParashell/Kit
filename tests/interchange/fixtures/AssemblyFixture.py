# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange import AssemblyData
from interchange import CadDocument
from interchange import CadSource
from interchange import Capability
from interchange import ComponentDef
from interchange import ComponentDoc
from interchange import ComponentInst
from interchange import ComponentKind
from interchange import Configuration
from interchange import MateConstraint
from interchange import MateEntity
from interchange import MateEntityKind
from interchange import MateKind
from interchange import TransformMatrix
from tests.interchange.fixtures.DocumentFixture import BuildDocument


# the canonical assembly fixture composes document data without module cycles
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
        source=CadSource("test.assembly", "memory", "1" * 64),
        configurations=(Configuration("config:default", "Default", True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        capabilities=frozenset({Capability.KAssemblies}),
        assembly=AssemblyValue,
    )
