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

from interchange.records.RecordProvenance import Provenance


# provenance and attribute access repeats on every record so one shared view keeps models small
class ModelExtras:
    __slots__ = ()

    # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return CastValue(
            Provenance | None,
            getattr(self, "provenance"),
        )

    # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return CastValue(
            TypeMap[str, object],
            getattr(self, "attributes"),
        )
