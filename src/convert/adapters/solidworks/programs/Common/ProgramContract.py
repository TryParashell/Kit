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
KFieldValue: TypeAlias = int | float | str | tuple["KFieldValue", ...]

# generated owner catalogs use trace offsets except where archive names are canonical keys
KOwnerKey: TypeAlias = int | str

# generated owner catalogs retain their concrete homogeneous key families
KOwnerSites: TypeAlias = Mapping[int, str] | Mapping[str, str]

# method operations preserve source offsets widths trace ownership encoding and default values
KMethodOp: TypeAlias = tuple[int, int, KOwnerKey, str, KFieldValue]

# each recovered method contributes an immutable operation sequence per native stream
KMethodStreams: TypeAlias = dict[str, tuple[KMethodOp, ...]]

# generated method modules expose one owner catalog paired with their stream contributions
KMethodProgram: TypeAlias = tuple[KOwnerSites, KMethodStreams]

# registries compose independently generated methods through one stable ordered contract
KMethodPrograms: TypeAlias = tuple[KMethodProgram, ...]

# composition resolves trace keys into readable owner names before assigning local indices
KOwnedOp: TypeAlias = tuple[int, int, str, str, KFieldValue]

# replay operations use compact registry local owner indices after deterministic composition
KFieldOp: TypeAlias = tuple[int, int, int, str, KFieldValue]

# assembly registries expose every coupled stream through the same concrete operation grammar
KStreamPrograms: TypeAlias = dict[str, tuple[KFieldOp, ...]]

# serializer callers override recovered defaults only at exact native source offsets
KFieldOverrides: TypeAlias = Mapping[int, KFieldValue]


# mixed override tables need one concrete builder so inference stays stable during later mutation
def BuildOverrides(
    InitialValues: KFieldOverrides | None = None,
) -> dict[int, KFieldValue]:
    return {} if InitialValues is None else dict(InitialValues)
