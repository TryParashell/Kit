# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.FieldEncoder import ReplayFixed

from .Registry import (
    AnnotationOps as AnnotationOps,
    FieldOwners as FieldOwners,
    KFieldOwners as KFieldOwners,
)


# the source interval records where the reusable manager was observed
KSourceRange = (24240, 24822)

# exact closure rejects any future field width or ordering drift
KReferenceLength = 582

# legacy source range access remains available for recovered stream diagnostics
SourceRange = KSourceRange

# legacy length access remains available while the invariant uses constant naming
ReferenceLength = KReferenceLength


# typed field replay emits the two view manager without retaining vendor byte spans
def EncodeViews() -> bytes:
    return ReplayFixed(AnnotationOps, KReferenceLength, "annotation")


# legacy annotation entry preserves existing configuration writer callers
EncodeTwoViewAnnotationManager = EncodeViews
