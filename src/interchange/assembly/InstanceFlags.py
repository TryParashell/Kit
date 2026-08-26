# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue


# writers branch on occurrence states so the boolean flags share one focused view
class InstanceFlags:
    __slots__ = ()

    # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return CastValue(bool, getattr(self, "suppressed"))

    # visibility state keeps exports faithful to what users actually see
    @property
    def IsHidden(self) -> bool:
        return CastValue(bool, getattr(self, "hidden"))

    # fixed lock protects user pinned geometry from solver drift
    @property
    def IsFixed(self) -> bool:
        return CastValue(bool, getattr(self, "fixed"))

    # flexibility flag preserves sub assembly motion semantics that rigid treatment loses
    @property
    def IsFlexible(self) -> bool:
        return CastValue(bool, getattr(self, "flexible"))

    # bom exclusion keeps purchased metadata out of quantity rollups silently
    @property
    def IsExcludedBom(self) -> bool:
        return CastValue(bool, getattr(self, "exclude_from_bom"))
