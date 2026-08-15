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
from interchange.enums.EnumDocument import Severity
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# diagnostics carry recoverable translation issues without invalidating useful documents
@ModelDataMut(
    DefaultMap={
        "Level": Severity.KWarning,
        "EntityId": "",
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class Diagnostic(ModelBase):
    ErrorCode: str
    MessageText: str
    Level: Severity
    EntityId: str
    Provenance: Provenance | None
    Attributes: TypeMap[str, object]

    # public diagnostics keep stable typed access for adapter and policy consumers
    @property
    def code(self) -> str:
        return self.ErrorCode

    # public diagnostics keep their human readable evidence statically accessible
    @property
    def message(self) -> str:
        return self.MessageText

    # public diagnostics preserve severity typing for filtering and policy decisions
    @property
    def severity(self) -> Severity:
        return self.Level
