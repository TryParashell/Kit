# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.AssemblyEnums import ComponentKind, MateEntityKind, MateKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordSource import CadSource
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
        document_id="document:part",
        body_ids=("body:1",),
    )
    SubassemblyInst = ComponentInst(
        "instance:subassembly",
        "Piston-1",
        Subassembly.id,
        RootValue.id,
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
        "instance:part", "Piston-1", PartDef.id, Subassembly.id
    )
    FirstEntity = MateEntity(
        "mate-entity:assembly",
        RootValue.id,
        (),
        MateEntityKind.KPlane,
        SourceEntityId="plane:front",
    )
    SecondEntity = MateEntity(
        "mate-entity:part",
        RootValue.id,
        (SubassemblyInst.id, PartInstance.id),
        MateEntityKind.KPlane,
        SourceEntityId="plane:xy",
    )
    MateValue = MateConstraint(
        "mate:1",
        "Coincident1",
        MateKind.KCoincident,
        RootValue.id,
        (FirstEntity.id, SecondEntity.id),
    )
    AssemblyValue = AssemblyData(
        RootValue.id,
        (RootValue, Subassembly, PartDef),
        (SubassemblyInst, PartInstance),
        documents=(ComponentDoc("document:part", PartValue),),
        mate_entities=(FirstEntity, SecondEntity),
        mates=(MateValue,),
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
