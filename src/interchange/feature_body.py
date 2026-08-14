# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .common import FreezeMapping
from .model_base import ModelBase, ModelDataMut
from .record_provenance import Provenance
from .record_topology import TopologyCounts


# design bodies connect feature results with topology material and source evidence
@ModelDataMut(
    DefaultMap={
        "Topology": TopologyCounts(),
        "MaterialId": None,
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class DesignBody(ModelBase):
    EntityId: str
    EntityName: str
    FinalFeatureId: str
    Topology: TopologyCounts
    MaterialId: str | None
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
