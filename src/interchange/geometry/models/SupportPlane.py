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
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.geometry.models.Transform import Transform


# support planes retain sketch attachment and offset relationships across systems
@ModelDataMut
class SupportPlane(ModelBase):
    id: str
    name: str
    transform: Transform
    support_selection_id: str | None = None
    offset_parameter_id: str | None = None
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

     # local transform keeps world placement composable through parent chains
    @property
    def Transform(self) -> Transform:
        return self.transform

     # optional support link keeps attached datums synced with faces
    @property
    def SupportSelectionId(self) -> str | None:
        return self.support_selection_id

     # offset link keeps plane distances parametrically adjustable
    @property
    def OffsetParameterId(self) -> str | None:
        return self.offset_parameter_id

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
