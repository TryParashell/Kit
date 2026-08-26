# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Mapping as TypeMap
from typing import cast as CastValue

from convert.adapters.solidworks.container.RunGroups import RunGroup


# layout consumers read repetition state through typed predicates independent of storage
class LayoutQueries:
    __slots__ = ()

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsWalksGroups(self) -> bool:
        Groups = CastValue(tuple[RunGroup, ...], getattr(self, "groups"))
        return bool(Groups)

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsRepeats(self) -> bool:
        Unresolved = CastValue(bool, getattr(self, "repeat_unresolved"))
        Prefix = CastValue(int, getattr(self, "repeat_prefix"))
        return Unresolved and Prefix <= 0

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsWalksAPrefix(self) -> bool:
        Unresolved = CastValue(bool, getattr(self, "repeat_unresolved"))
        Prefix = CastValue(int, getattr(self, "repeat_prefix"))
        return Unresolved and Prefix > 0

    # this definition exists because focused behavior needs one stable owner
    @property
    def ConstantRunKeys(self) -> frozenset[str]:
        RunEntries = CastValue(TypeMap[str, int], getattr(self, "runs"))
        ByVersion = CastValue(
            TypeMap[str, TypeMap[int, int]],
            getattr(self, "runs_by_version"),
        )
        ByChild = CastValue(
            TypeMap[str, TypeMap[str, int]],
            getattr(self, "RunsByChildClass"),
        )
        return frozenset(set(RunEntries) | set(ByVersion) | set(ByChild))

    # this definition exists because focused behavior needs one stable owner
    @property
    def TemplateSlot(self) -> int:
        return len(CastValue(tuple[str, ...], getattr(self, "child_slots"))) - 2

    constant_run_keys = ConstantRunKeys
    repeats = IsRepeats
    template_slot = TemplateSlot
    walks_a_prefix = IsWalksAPrefix
    walks_groups = IsWalksGroups
