# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar
from typing import Mapping as TypeMap
from typing import TYPE_CHECKING as IsTypeCheck

from interchange.core.Common import FreezeMapping
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.core.ModelBase import ModelBase, ModelDataMut

if IsTypeCheck:
    from interchange.document.models.DocumentModel import CadDocument


# assembly data composes occurrences documents and mates into one portable graph
@ModelDataMut(
    DefaultMap={"documents": (), "mate_entities": (), "mates": (), "mate_groups": ()},
    FactoryMap={"attributes": FreezeMapping},
)
class AssemblyData(ModelBase):
    root_definition_id: str
    definitions: tuple[ComponentDef, ...]
    instances: tuple[ComponentInst, ...]
    documents: tuple[ComponentDoc, ...]
    mate_entities: tuple[MateEntity, ...]
    mates: tuple[MateConstraint, ...]
    mate_groups: tuple[MateGroup, ...]
    attributes: TypeMap[str, object]
    if IsTypeCheck:
        RootDefinitionId: ClassVar[str]
        Definitions: ClassVar[tuple[ComponentDef, ...]]
        Instances: ClassVar[tuple[ComponentInst, ...]]
        Documents: ClassVar[tuple[ComponentDoc, ...]]
        MateEntities: ClassVar[tuple[MateEntity, ...]]
        Mates: ClassVar[tuple[MateConstraint, ...]]
        MateGroups: ClassVar[tuple[MateGroup, ...]]
        Attributes: ClassVar[TypeMap[str, object]]

    # definition lookup gives callers one consistent missing identifier failure mode
    def GetDefinition(self, EntityId: str) -> ComponentDef:
        for DefinitionValue in self.definitions:
            if DefinitionValue.id == EntityId:
                return DefinitionValue
        raise KeyError(f"unknown component definition id {EntityId!r}")

    # embedded document lookup avoids exposing storage details to assembly consumers
    def GetDocument(self, EntityId: str) -> CadDocument:
        for DocumentValue in self.documents:
            if DocumentValue.id == EntityId:
                return DocumentValue.document
        raise KeyError(f"unknown component document id {EntityId!r}")

    # child ordering stays deterministic when source order values contain ties
    def GetChildren(self, DefinitionId: str) -> tuple[ComponentInst, ...]:
        ChildValues = (
            InstanceValue
            for InstanceValue in self.instances
            if InstanceValue.owner_definition_id == DefinitionId
        )

        # stable tie ordering preserves reproducible assembly output across adapters
        return tuple(
            sorted(
                ChildValues,
                key=lambda InstanceValue: (InstanceValue.order, InstanceValue.id),
            )
        )
