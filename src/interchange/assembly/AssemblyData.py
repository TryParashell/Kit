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
from typing import cast as CastValue

from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.core.ModelExtras import ModelExtras
from interchange.assembly.GraphView import GraphView
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup


# assembly data composes occurrences documents and mates into one portable graph
@ModelDataMut
class AssemblyData(GraphView, ModelExtras, ModelBase):
    root_definition_id: str
    definitions: tuple[ComponentDef, ...]
    instances: tuple[ComponentInst, ...]
    documents: tuple[ComponentDoc, ...] = ()
    mate_entities: tuple[MateEntity, ...] = ()
    mates: tuple[MateConstraint, ...] = ()
    mate_groups: tuple[MateGroup, ...] = ()
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    # document list keeps external references inspectable without reopening files
    @property
    def Documents(self) -> "tuple[ComponentDoc, ...]":
        return CastValue("tuple[ComponentDoc, ...]", getattr(self, "documents"))

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

    # lowercase lookup stays concrete because static consumers cannot observe runtime aliases
    def children(self, definition_id: str) -> tuple[ComponentInst, ...]:
        return self.GetChildren(definition_id)


from interchange.assembly.ComponentDocument import (  # lgtm[py/cyclic-import]
    ComponentDoc,
)
from interchange.document.models.DocumentModel import (  # lgtm[py/cyclic-import]
    CadDocument,
)
