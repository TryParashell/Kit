# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias


# serializer fields need one closed recursive value grammar across every generated program
FieldValue: TypeAlias = int | float | str | tuple["FieldValue", ...]

# generated owner catalogs use trace offsets except where archive names are canonical keys
OwnerKey: TypeAlias = int | str

# generated owner catalogs retain their concrete homogeneous key families
OwnerSites: TypeAlias = Mapping[int, str] | Mapping[str, str]

# method operations preserve source offsets widths trace ownership encoding and default values
MethodOp: TypeAlias = tuple[int, int, OwnerKey, str, FieldValue]

# each recovered method contributes an immutable operation sequence per native stream
MethodStreams: TypeAlias = dict[str, tuple[MethodOp, ...]]

# generated method modules expose one owner catalog paired with their stream contributions
MethodProgram: TypeAlias = tuple[OwnerSites, MethodStreams]

# registries compose independently generated methods through one stable ordered contract
MethodPrograms: TypeAlias = tuple[MethodProgram, ...]

# composition resolves trace keys into readable owner names before assigning local indices
OwnedOp: TypeAlias = tuple[int, int, str, str, FieldValue]

# replay operations use compact registry local owner indices after deterministic composition
FieldOp: TypeAlias = tuple[int, int, int, str, FieldValue]

# assembly registries expose every coupled stream through the same concrete operation grammar
StreamPrograms: TypeAlias = dict[str, tuple[FieldOp, ...]]

# serializer callers override recovered defaults only at exact native source offsets
FieldOverrides: TypeAlias = Mapping[int, FieldValue]


# mixed override tables need one concrete builder so inference stays stable during later mutation
def BuildOverrides(
    InitialValues: FieldOverrides | None = None,
) -> dict[int, FieldValue]:
    return {} if InitialValues is None else dict(InitialValues)
