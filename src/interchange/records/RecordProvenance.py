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


# source spans connect portable entities back to exact native container records
@ModelDataMut
class ProvenanceSpan(ModelBase):
    stream: str
    offset: int
    length: int
    record_kind: str = ""

     # stream name locates the originating section inside containers
    @property
    def Stream(self) -> str:
        return self.stream

     # start offset lets extrudes begin away from the sketch plane
    @property
    def Offset(self) -> int:
        return self.offset

     # extrusion length defines prism height without evaluating geometry
    @property
    def Length(self) -> int:
        return self.length

     # kind label tells consumers which parser owns this span
    @property
    def RecordKind(self) -> str:
        return self.record_kind


# provenance preserves source identity confidence and evidence through conversion pipelines
@ModelDataMut
class Provenance(ModelBase):
    adapter: str
    native_id: str = ""
    confidence: float = 1.0
    spans: tuple[ProvenanceSpan, ...] = ()
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # adapter name credits the reader that produced this record
    @property
    def Adapter(self) -> str:
        return self.adapter

     # native id links records back to vendor identifiers faithfully
    @property
    def NativeId(self) -> str:
        return self.native_id

     # confidence score lets callers weigh lossy reconstructions appropriately
    @property
    def Confidence(self) -> float:
        return self.confidence

     # span collection keeps multi location provenance compact and ordered
    @property
    def Spans(self) -> tuple[ProvenanceSpan, ...]:
        return self.spans

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
