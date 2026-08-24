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

from interchange.assembly.AssemblyEnums import MateEntityKind
from interchange.assembly.MateEntityView import MateEntityView
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.core.ModelExtras import ModelExtras
from interchange.records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix


# mate entities resolve constraint geometry through occurrence paths and optional frames
@ModelDataMut
class MateEntity(MateEntityView, ModelExtras, ModelBase):
    id: str
    owner_definition_id: str
    instance_path: tuple[str, ...]
    kind: MateEntityKind | str
    source_entity_id: str = ""
    selection_id: str = ""
    frame: TransformMatrix | None = None
    radius: float | None = None
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
