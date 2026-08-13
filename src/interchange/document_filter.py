# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace as ReplaceValue
from typing import TYPE_CHECKING as TypeChecking

from .payload_record import BrepPayload
from .payload_roles import PayloadRole

if TypeChecking:
    from .document_model import CadDocument


# export filtering needs payload records transformed without altering source documents
def FilterPayloads(
    DocumentValue: CadDocument,
    *,
    IncludeBrep: bool,
    IncludeMesh: bool,
    KeepPayloads: bool,
) -> tuple[BrepPayload, ...]:
    PayloadValues: list[BrepPayload] = []
    for PayloadValue in DocumentValue.BrepPayloads:
        IsExcluded = (
            PayloadValue.ValueRole == PayloadRole.KBrep and not IncludeBrep
        ) or (PayloadValue.ValueRole == PayloadRole.KTessellation and not IncludeMesh)
        if not IsExcluded:
            PayloadValues.append(PayloadValue)
        elif KeepPayloads:
            PayloadValues.append(ReplaceValue(PayloadValue, PayloadData=None))
    return tuple(PayloadValues)


# recursive filtering preserves assembly structure while removing selected geometry content
def FilterDocument(
    DocumentValue: CadDocument,
    *,
    IncludeBrep: bool = True,
    IncludeMesh: bool = True,
    KeepPayloads: bool = True,
    **LegacyValues: bool,
) -> CadDocument:
    from .document_caps import GetRetainedCaps
    from .document_model import CadDocument

    RemainingValues = dict(LegacyValues)
    if "include_brep" in RemainingValues:
        IncludeBrep = RemainingValues.pop("include_brep")
    if "include_tessellation" in RemainingValues:
        IncludeMesh = RemainingValues.pop("include_tessellation")
    if "keep_payload_records" in RemainingValues:
        KeepPayloads = RemainingValues.pop("keep_payload_records")
    if RemainingValues:
        UnknownName = next(iter(RemainingValues))
        raise TypeError(
            f"FilterDocument got an unexpected keyword argument {UnknownName!r}"
        )
    AssemblyValue = DocumentValue.Assembly
    if AssemblyValue is not None:
        AssemblyValue = ReplaceValue(
            AssemblyValue,
            Documents=tuple(
                ReplaceValue(
                    ComponentValue,
                    Document=(
                        FilterDocument(
                            ComponentValue.Document,
                            IncludeBrep=IncludeBrep,
                            IncludeMesh=IncludeMesh,
                            KeepPayloads=KeepPayloads,
                        )
                        if isinstance(ComponentValue.Document, CadDocument)
                        else ComponentValue.Document
                    ),
                )
                for ComponentValue in AssemblyValue.Documents
            ),
        )
    FilteredDoc = ReplaceValue(
        DocumentValue,
        Meshes=DocumentValue.Meshes if IncludeMesh else (),
        BrepPayloads=FilterPayloads(
            DocumentValue,
            IncludeBrep=IncludeBrep,
            IncludeMesh=IncludeMesh,
            KeepPayloads=KeepPayloads,
        ),
        Assembly=AssemblyValue,
        BrepModel=DocumentValue.BrepModel if IncludeBrep else None,
    )
    return ReplaceValue(
        FilteredDoc,
        Capabilities=GetRetainedCaps(
            FilteredDoc,
            DocumentValue.Capabilities,
            IncludeBrep=IncludeBrep,
            IncludeMesh=IncludeMesh,
        ),
    )
