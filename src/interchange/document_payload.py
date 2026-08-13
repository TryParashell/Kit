# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib as HashCodec
from typing import TYPE_CHECKING as TypeChecking

from .payload_roles import PayloadRole

if TypeChecking:
    from .document_model import CadDocument


# source recovery needs unambiguous document and digest binding payload indexes
def GetPayloadIds(DocumentValue: CadDocument) -> frozenset[int]:
    try:
        SourceDigest = bytes.fromhex(DocumentValue.Source.SourceDigest)
    except ValueError:
        return frozenset()
    if len(SourceDigest) != HashCodec.sha256().digest_size:
        return frozenset()
    SourceDigestText = DocumentValue.Source.SourceDigest.casefold()
    DocumentIndexes = tuple(
        IndexValue
        for IndexValue, PayloadValue in enumerate(DocumentValue.BrepPayloads)
        if PayloadValue.ValueRole == PayloadRole.KDocument
        and (
            HashCodec.sha256(PayloadValue.PayloadData).hexdigest()
            if PayloadValue.PayloadData is not None
            else PayloadValue.SourceDigest.casefold()
        )
        == SourceDigestText
    )
    BindingIndexes = tuple(
        IndexValue
        for IndexValue, PayloadValue in enumerate(DocumentValue.BrepPayloads)
        if PayloadValue.ValueRole in (PayloadRole.KVerification, PayloadRole.KDocument)
        and PayloadValue.PayloadData == SourceDigest
        and PayloadValue.SourceDigest.casefold()
        == HashCodec.sha256(SourceDigest).hexdigest()
    )
    if len(DocumentIndexes) != 1 or len(BindingIndexes) != 1:
        return frozenset()
    return frozenset((*DocumentIndexes, *BindingIndexes))
