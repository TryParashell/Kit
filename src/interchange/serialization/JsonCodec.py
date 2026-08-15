# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json as JsonCodec
from typing import Any as AnyValue

from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


# json output provides deterministic portable text for storage and hashing
def DumpJson(SourceValue: AnyValue, *, IndentSize: int | None = 2) -> str:
    return JsonCodec.dumps(
        ToData(SourceValue), indent=IndentSize, sort_keys=True, ensure_ascii=False
    )


# json input shares the validated recursive decoder used by mapping based callers
def LoadJson(SourceText: str) -> AnyValue:
    return FromData(JsonCodec.loads(SourceText))
