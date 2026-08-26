# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue


# group consumers read typed labels so this view stays separable from mate group storage
class MateGroupView:
    __slots__ = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return CastValue(str, getattr(self, "name"))

    # owner link keeps nested placement resolvable during assembly walks
    @property
    def OwnerDefinitionId(self) -> str:
        return CastValue(str, getattr(self, "owner_definition_id"))

    # member ids keep grouped constraints enumerable without reverse lookups
    @property
    def MateIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "mate_ids"))

    # parent link keeps group nesting reconstructable for hierarchical writers
    @property
    def ParentGroupId(self) -> str:
        return CastValue(str, getattr(self, "parent_group_id"))

    # explicit order keeps sibling sequencing stable across adapter round trips
    @property
    def Order(self) -> int:
        return CastValue(int, getattr(self, "order"))
