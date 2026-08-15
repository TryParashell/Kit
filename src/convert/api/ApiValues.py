# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping


# enforced write values prevent callers from weakening portable self contained output guarantees
def BuildWriteVals(
    InputValues: TypeMap[str, object] | None,
    AllowCarrier: bool,
) -> TypeMap[str, object]:
    SelectedValues: dict[str, object] = {"portable": True}
    if InputValues is not None:
        SelectedValues.update(InputValues)
    SelectedValues["allow_carrier"] = AllowCarrier
    SelectedValues["require_self_contained"] = True
    return FreezeMapping(SelectedValues)
