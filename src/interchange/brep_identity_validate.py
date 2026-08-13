# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import fields as GetFields

from .brep_model import BrepModel
from .wire import ResolveField


# identity indexing centralizes duplicate and empty identifier diagnostics
def GetBrepIds(
    ModelValue: BrepModel,
) -> tuple[dict[str, frozenset[str]], tuple[str, ...]]:
    ErrorValues: list[str] = []
    IdentitySets: dict[str, frozenset[str]] = {}
    for FieldValue in GetFields(ModelValue):
        ModelName = ResolveField(type(ModelValue), FieldValue.name)
        if ModelName == "SchemaVersion":
            continue
        ItemValues = getattr(ModelValue, FieldValue.name)
        Identifiers = tuple(ItemValue.EntityId for ItemValue in ItemValues)
        if any(not Identifier for Identifier in Identifiers):
            ErrorValues.append(f"B-rep {FieldValue.name} contains an empty id")
        if len(Identifiers) != len(set(Identifiers)):
            ErrorValues.append(f"B-rep {FieldValue.name} contains duplicate ids")
        IdentitySets[ModelName] = frozenset(Identifiers)
    return IdentitySets, tuple(ErrorValues)
