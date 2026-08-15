# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, Mapping as TypeMap, TYPE_CHECKING

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumDocument import Severity
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# diagnostics carry recoverable translation issues without invalidating useful documents
@ModelDataMut(
    DefaultMap={
        "severity": Severity.KWarning,
        "entity_id": "",
        "provenance": None,
    },
    FactoryMap={"attributes": FreezeMapping},
)
class Diagnostic(ModelBase):
    code: str
    message: str
    severity: Severity
    entity_id: str
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        ErrorCode: ClassVar[str]
        MessageText: ClassVar[str]
        Level: ClassVar[Severity]
        EntityId: ClassVar[str]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
