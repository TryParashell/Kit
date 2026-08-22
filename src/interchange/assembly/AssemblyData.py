# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap
from typing import TYPE_CHECKING as IsTypeCheck

from interchange.core.Common import FreezeMapping
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import (
    ComponentDoc,  # lgtm[py/unsafe-cyclic-import]
)
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.core.ModelBase import ModelBase, ModelDataMut

if IsTypeCheck:
    from interchange.document.models.DocumentModel import (
        CadDocument,  # lgtm[py/unsafe-cyclic-import]
    )


# assembly data composes occurrences documents and mates into one portable graph
@ModelDataMut
class AssemblyData(ModelBase):
    root_definition_id: str
    definitions: tuple[ComponentDef, ...]
    instances: tuple[ComponentInst, ...]
    documents: tuple[ComponentDoc, ...] = ()
    mate_entities: tuple[MateEntity, ...] = ()
    mates: tuple[MateConstraint, ...] = ()
    mate_groups: tuple[MateGroup, ...] = ()
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def RootDefinitionId(self) -> str:
        return self.root_definition_id

    @property
    def Definitions(self) -> tuple[ComponentDef, ...]:
        return self.definitions

    @property
    def Instances(self) -> tuple[ComponentInst, ...]:
        return self.instances

    @property
    def Documents(self) -> tuple[ComponentDoc, ...]:
        return self.documents

    @property
    def MateEntities(self) -> tuple[MateEntity, ...]:
        return self.mate_entities

    @property
    def Mates(self) -> tuple[MateConstraint, ...]:
        return self.mates

    @property
    def MateGroups(self) -> tuple[MateGroup, ...]:
        return self.mate_groups

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes

    # definition lookup gives callers one consistent missing identifier failure mode
    def GetDefinition(self, EntityId: str) -> ComponentDef:
        for DefinitionValue in self.definitions:
            if DefinitionValue.id == EntityId:
                return DefinitionValue
        raise KeyError(f"unknown component definition id {EntityId!r}")

    # lowercase lookup stays concrete because static consumers cannot observe runtime aliases
    def definition(self, entity_id: str) -> ComponentDef:
        return self.GetDefinition(entity_id)

    # embedded document lookup avoids exposing storage details to assembly consumers
    def GetDocument(self, EntityId: str) -> CadDocument:
        for DocumentValue in self.documents:
            if DocumentValue.id == EntityId:
                return DocumentValue.document
        raise KeyError(f"unknown component document id {EntityId!r}")

    # lowercase lookup stays concrete because linked document consumers need its exact return type
    def document(self, entity_id: str) -> CadDocument:
        return self.GetDocument(entity_id)

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

    # lowercase lookup stays concrete because static consumers cannot observe runtime aliases
    def children(self, definition_id: str) -> tuple[ComponentInst, ...]:
        return self.GetChildren(definition_id)
