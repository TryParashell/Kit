# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Iterable as IterableBase
from typing import cast as CastValue
from typing import Iterable as ValueIterable
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping

# wrapper metadata needs one reserved key shared by semantic filtering paths
KWrapperMetaKey = "kit.wrapper_metadata_keys"


# metadata markers cross untyped wrappers so their collection shape must be narrowed once
def GetMetaNames(SourceValue: object) -> set[str]:
    if not isinstance(SourceValue, (tuple, list, set, frozenset)):
        return set()
    ItemValues = CastValue(IterableBase[object], SourceValue)
    return {ItemValue for ItemValue in ItemValues if isinstance(ItemValue, str)}


# wrapper annotations must remain distinguishable from source semantic metadata
def AddWrapperMeta(
    MetaValues: TypeMap[str, object], KeyValues: ValueIterable[str]
) -> TypeMap[str, object]:
    ExistingValue = MetaValues.get(KWrapperMetaKey, ())
    NameValues = GetMetaNames(ExistingValue)
    NameValues.update(KeyValues)
    ResultValue = dict(MetaValues)
    ResultValue[KWrapperMetaKey] = tuple(sorted(NameValues))
    return FreezeMapping(ResultValue)


# semantic comparisons must ignore metadata introduced only by transport wrappers
def GetSemanticMeta(
    MetaValues: TypeMap[str, object],
) -> TypeMap[str, object]:
    WrappedValues = MetaValues.get(KWrapperMetaKey, ())
    NameValues = GetMetaNames(WrappedValues)
    return FreezeMapping(
        {
            KeyValue: SourceValue
            for KeyValue, SourceValue in MetaValues.items()
            if KeyValue != KWrapperMetaKey and KeyValue not in NameValues
        }
    )
