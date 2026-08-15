# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from enum import StrEnum as StringEnum
from typing import cast as CastValue


# shared enum behavior keeps compatibility handling consistent across every model category
class WireEnum(StringEnum):
    locals()["__slots__"] = ()

    # canonical aliases stay statically typed without appearing as duplicate public members
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        RawMemberMap: object = type.__getattribute__(cls, "_member_map_")
        if not isinstance(RawMemberMap, dict):
            raise TypeError("enum members must form a mapping")
        MemberMap = CastValue(dict[str, StringEnum], RawMemberMap)
        LegacyMembers = {
            MemberName: MemberValue
            for MemberName, MemberValue in MemberMap.items()
            if not MemberName.startswith("K")
        }
        setattr(cls, "_member_map_", LegacyMembers)
