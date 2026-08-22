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

    @property
    def Stream(self) -> str:
        return self.stream

    @property
    def Offset(self) -> int:
        return self.offset

    @property
    def Length(self) -> int:
        return self.length

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

    @property
    def Adapter(self) -> str:
        return self.adapter

    @property
    def NativeId(self) -> str:
        return self.native_id

    @property
    def Confidence(self) -> float:
        return self.confidence

    @property
    def Spans(self) -> tuple[ProvenanceSpan, ...]:
        return self.spans

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
