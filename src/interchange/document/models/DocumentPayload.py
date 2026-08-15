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

from interchange.payloads.PayloadRoles import PayloadRole

if TypeChecking:
    from interchange.document.models.DocumentModel import CadDocument


# source recovery needs unambiguous document and digest binding payload indexes
def GetPayloadIds(DocumentValue: CadDocument) -> frozenset[int]:
    try:
        SourceDigest = bytes.fromhex(DocumentValue.source.sha256)
    except ValueError:
        return frozenset()
    if len(SourceDigest) != HashCodec.sha256().digest_size:
        return frozenset()
    SourceDigestText = DocumentValue.source.sha256.casefold()
    DocumentIndexes = tuple(
        IndexValue
        for IndexValue, PayloadValue in enumerate(DocumentValue.brep_payloads)
        if PayloadValue.role == PayloadRole.KDocument
        and (
            HashCodec.sha256(PayloadValue.data).hexdigest()
            if PayloadValue.data is not None
            else PayloadValue.sha256.casefold()
        )
        == SourceDigestText
    )
    BindingIndexes = tuple(
        IndexValue
        for IndexValue, PayloadValue in enumerate(DocumentValue.brep_payloads)
        if PayloadValue.role in (PayloadRole.KVerification, PayloadRole.KDocument)
        and PayloadValue.data == SourceDigest
        and PayloadValue.sha256.casefold()
        == HashCodec.sha256(SourceDigest).hexdigest()
    )
    if len(DocumentIndexes) != 1 or len(BindingIndexes) != 1:
        return frozenset()
    return frozenset((*DocumentIndexes, *BindingIndexes))
