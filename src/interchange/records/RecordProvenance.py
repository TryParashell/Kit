# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut


# source spans connect portable entities back to exact native container records
@ModelDataMut(DefaultMap={"record_kind": ""})
class ProvenanceSpan(ModelBase):
    stream: str
    offset: int
    length: int
    record_kind: str
    if TYPE_CHECKING:
        Stream: ClassVar[str]
        Offset: ClassVar[int]
        Length: ClassVar[int]
        RecordKind: ClassVar[str]


# provenance preserves source identity confidence and evidence through conversion pipelines
@ModelDataMut(
    DefaultMap={"native_id": "", "confidence": 1.0, "spans": ()},
    FactoryMap={"attributes": FreezeMapping},
)
class Provenance(ModelBase):
    adapter: str
    native_id: str
    confidence: float
    spans: tuple[ProvenanceSpan, ...]
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        Adapter: ClassVar[str]
        NativeId: ClassVar[str]
        Confidence: ClassVar[float]
        Spans: ClassVar[tuple[ProvenanceSpan, ...]]
        Attributes: ClassVar[TypeMap[str, object]]
