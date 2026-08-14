# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.core.ModelBase import ModelBase, ModelDataMut


# assembly data composes occurrences documents and mates into one portable graph
@ModelDataMut(
    DefaultMap={"Documents": (), "MateEntities": (), "Mates": (), "MateGroups": ()},
    FactoryMap={"Attributes": FreezeMapping},
)
class AssemblyData(ModelBase):
    RootDefinitionId: str
    Definitions: tuple[ComponentDef, ...]
    Instances: tuple[ComponentInst, ...]
    Documents: tuple[ComponentDoc, ...]
    MateEntities: tuple[MateEntity, ...]
    Mates: tuple[MateConstraint, ...]
    MateGroups: tuple[MateGroup, ...]
    Attributes: TypeMap[str, AnyValue]

    # definition lookup gives callers one consistent missing identifier failure mode
    def GetDefinition(SelfValue, EntityId: str) -> ComponentDef:
        for DefinitionValue in SelfValue.Definitions:
            if DefinitionValue.EntityId == EntityId:
                return DefinitionValue
        raise KeyError(f"unknown component definition id {EntityId!r}")

    # embedded document lookup avoids exposing storage details to assembly consumers
    def GetDocument(SelfValue, EntityId: str) -> AnyValue:
        for DocumentValue in SelfValue.Documents:
            if DocumentValue.EntityId == EntityId:
                return DocumentValue.Document
        raise KeyError(f"unknown component document id {EntityId!r}")

    # child ordering stays deterministic when source order values contain ties
    def GetChildren(SelfValue, DefinitionId: str) -> tuple[ComponentInst, ...]:
        ChildValues = (
            InstanceValue
            for InstanceValue in SelfValue.Instances
            if InstanceValue.OwnerDefinitionId == DefinitionId
        )

        # stable tie ordering preserves reproducible assembly output across adapters
        return tuple(
            sorted(
                ChildValues,
                key=lambda InstanceValue: (InstanceValue.Order, InstanceValue.EntityId),
            )
        )
