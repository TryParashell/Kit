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

if IsTypeCheck:
    from interchange.geometry.models.Sketch import SketchEntity, SketchRelation


# sketch consumers read editable profile inputs through one typed view
class SketchView:
    __slots__: tuple[str, ...] = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return CastValue(str, getattr(self, "name"))

    # plane anchor locates the sketch in space without embedding transforms
    @property
    def SupportPlaneId(self) -> str:
        return CastValue(str, getattr(self, "support_plane_id"))

    # element list keeps sketch contents enumerable in draw order
    @property
    def Entities(self) -> "tuple[SketchEntity, ...]":
        return CastValue("tuple[SketchEntity, ...]", getattr(self, "entities"))

    # relation list keeps sketch intent inspectable without solving
    @property
    def Constraints(self) -> "tuple[SketchRelation, ...]":
        return CastValue("tuple[SketchRelation, ...]", getattr(self, "constraints"))

    # parameter links keep mate values driven by configurable expressions
    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "parameter_ids"))

    # loop groups identify closed profiles so features can consume sketches directly
    @property
    def ClosedProfileEntityIds(self) -> "tuple[tuple[str, ...], ...]":
        return CastValue(
            "tuple[tuple[str, ...], ...]",
            getattr(self, "closed_profile_entity_ids"),
        )

    # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return CastValue(bool, getattr(self, "suppressed"))
