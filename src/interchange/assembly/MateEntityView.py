# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange.assembly.AssemblyEnums import MateEntityKind
from interchange.assembly.TransformMatrix import TransformMatrix


# mate solvers read entity addressing and geometry through one typed view
class MateEntityView:
    __slots__ = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # owner link keeps nested placement resolvable during assembly walks
    @property
    def OwnerDefinitionId(self) -> str:
        return CastValue(str, getattr(self, "owner_definition_id"))

    # path tuple addresses entities nested inside sub assemblies unambiguously
    @property
    def InstancePath(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "instance_path"))

    # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> MateEntityKind | str:
        return CastValue(MateEntityKind | str, getattr(self, "kind"))

    # native entity id keeps mate targets traceable into vendor documents
    @property
    def SourceEntityId(self) -> str:
        return CastValue(str, getattr(self, "source_entity_id"))

    # selection id mirrors how users picked geometry so replays stay faithful
    @property
    def SelectionId(self) -> str:
        return CastValue(str, getattr(self, "selection_id"))

    # local frame keeps mate math independent of global coordinate guesses
    @property
    def Frame(self) -> TransformMatrix | None:
        return CastValue(TransformMatrix | None, getattr(self, "frame"))

    # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> float | None:
        return CastValue(float | None, getattr(self, "radius"))
