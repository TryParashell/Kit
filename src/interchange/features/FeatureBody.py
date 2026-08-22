# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase
from interchange.records.RecordProvenance import Provenance
from interchange.records.RecordTopology import TopologyCounts


# design bodies connect feature results with topology material and source evidence
@MakeDataClass(frozen=True, slots=True)
class DesignBody(ModelBase):
    id: str
    name: str
    final_feature_id: str
    topology: TopologyCounts = TopologyCounts()
    material_id: str | None = None
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityName(self) -> str:
        return self.name

    @property
    def FinalFeatureId(self) -> str:
        return self.final_feature_id

    @property
    def Topology(self) -> TopologyCounts:
        return self.topology

    @property
    def MaterialId(self) -> str | None:
        return self.material_id

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
