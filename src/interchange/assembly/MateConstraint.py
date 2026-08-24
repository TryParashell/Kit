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

from interchange.assembly.AssemblyEnums import MateAlignment, MateKind
from interchange.assembly.ConstraintDrive import ConstraintDrive
from interchange.assembly.ConstraintView import ConstraintView
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.core.ModelExtras import ModelExtras
from interchange.records.RecordParameter import ParameterValue
from interchange.records.RecordProvenance import Provenance


# mate constraints preserve relationships values and bindings across systems
@ModelDataMut
class MateConstraint(ConstraintView, ConstraintDrive, ModelExtras, ModelBase):
    id: str
    name: str
    kind: MateKind | str
    owner_definition_id: str
    entity_ids: tuple[str, ...]
    order: int = 0
    value: ParameterValue | None = None
    parameter_ids: tuple[str, ...] = ()
    alignment: MateAlignment | str = MateAlignment.KUnknown
    suppressed: bool = False
    driving: bool = True
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
