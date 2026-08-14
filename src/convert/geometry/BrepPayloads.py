# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from interchange import BrepPayload, CadDocument, PayloadRole


# extraction filters semantic brep payloads so unrelated native history remains embedded
def GetBrepPayloads(DocumentData: CadDocument) -> tuple[BrepPayload, ...]:
    return tuple(
        PayloadData
        for PayloadData in DocumentData.brep_payloads
        if PayloadData.role == PayloadRole.BREP and PayloadData.data is not None
    )
