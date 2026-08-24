# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup


# graph accessors stay separable so storage models compose typed views without owning traversal state
class GraphView:
    __slots__ = ()

    # root pointer keeps traversal order deterministic without storing parent chains everywhere
    @property
    def RootDefinitionId(self) -> str:
        return CastValue(str, getattr(self, "root_definition_id"))

    # definition list stays immutable so assembly consumers can share it freely
    @property
    def Definitions(self) -> tuple[ComponentDef, ...]:
        return CastValue(tuple[ComponentDef, ...], getattr(self, "definitions"))

    # instance order preserves placement sequence because downstream writers depend on it
    @property
    def Instances(self) -> tuple[ComponentInst, ...]:
        return CastValue(tuple[ComponentInst, ...], getattr(self, "instances"))

    # mate entity tuples keep constraint geometry addressable across adapters uniformly
    @property
    def MateEntities(self) -> tuple[MateEntity, ...]:
        return CastValue(tuple[MateEntity, ...], getattr(self, "mate_entities"))

    # constraint list stays frozen so assembly validation sees one stable snapshot
    @property
    def Mates(self) -> tuple[MateConstraint, ...]:
        return CastValue(tuple[MateConstraint, ...], getattr(self, "mates"))

    # group list keeps grouped constraints navigable without rescanning the whole assembly
    @property
    def MateGroups(self) -> tuple[MateGroup, ...]:
        return CastValue(tuple[MateGroup, ...], getattr(self, "mate_groups"))

    # child ordering stays deterministic when source order values contain ties
    def GetChildren(self, DefinitionId: str) -> tuple[ComponentInst, ...]:
        StoredInstances = CastValue(
            tuple[ComponentInst, ...],
            getattr(self, "instances"),
        )
        ChildValues = (
            InstanceValue
            for InstanceValue in StoredInstances
            if InstanceValue.owner_definition_id == DefinitionId
        )

        # stable tie ordering preserves reproducible assembly output across adapters
        return tuple(
            sorted(
                ChildValues,
                key=lambda InstanceValue: (InstanceValue.order, InstanceValue.id),
            )
        )
