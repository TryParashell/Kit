# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumDocument import Severity
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# diagnostics carry recoverable translation issues without invalidating useful documents
@ModelDataMut
class Diagnostic(ModelBase):
    code: str
    message: str
    severity: Severity = Severity.KWarning
    entity_id: str = ""
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def ErrorCode(self) -> str:
        return self.code

    @property
    def MessageText(self) -> str:
        return self.message

    @property
    def Level(self) -> Severity:
        return self.severity

    @property
    def EntityId(self) -> str:
        return self.entity_id

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
