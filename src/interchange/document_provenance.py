# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import fields as GetFields
from dataclasses import is_dataclass as IsDataClass
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .record_provenance import Provenance


# capability inference needs provenance detection across arbitrary nested records
def HasProvenance(SourceValue: AnyValue) -> bool:
    PendingValues = [SourceValue]
    SeenValues: set[int] = set()
    while PendingValues:
        ItemValue = PendingValues.pop()
        if isinstance(ItemValue, Provenance):
            return True
        if ItemValue is None or isinstance(ItemValue, (str, bytes, int, float, bool)):
            continue
        IdentityValue = id(ItemValue)
        if IdentityValue in SeenValues:
            continue
        SeenValues.add(IdentityValue)
        if IsDataClass(ItemValue):
            PendingValues.extend(
                getattr(ItemValue, MemberField.name)
                for MemberField in GetFields(ItemValue)
            )
        elif isinstance(ItemValue, TypeMap):
            PendingValues.extend(ItemValue.values())
        elif isinstance(ItemValue, (tuple, list, set, frozenset)):
            PendingValues.extend(ItemValue)
    return False
