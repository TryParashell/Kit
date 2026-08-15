# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.serialization.Wire import GetWireType

# registered types allow wire data to reconstruct concrete immutable records safely
KTypeRegistry: dict[str, type] = {}


# explicit registration prevents deserialization from importing arbitrary classes by name
def RegisterTypes(*ClassTypes: type) -> None:
    for ClassType in ClassTypes:
        WireType = GetWireType(ClassType)
        ExistingType = KTypeRegistry.get(WireType)
        if ExistingType is not None and ExistingType is not ClassType:
            raise ValueError(f"duplicate interchange type name {WireType!r}")
        KTypeRegistry[WireType] = ClassType
