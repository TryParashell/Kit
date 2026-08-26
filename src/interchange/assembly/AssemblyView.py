# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING as IsTypeCheck
from typing import cast as CastValue

from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup


# assembly readers depend on typed graph access so the view stays separable from storage
class AssemblyView:
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

    # document list keeps external references inspectable without reopening files
    @property
    def Documents(self) -> "tuple[ComponentDoc, ...]":
        return CastValue("tuple[ComponentDoc, ...]", getattr(self, "documents"))

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


if IsTypeCheck:
    from interchange.assembly.ComponentDocument import (
        ComponentDoc,  # lgtm[py/cyclic-import]
    )
