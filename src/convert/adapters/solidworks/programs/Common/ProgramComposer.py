# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from operator import itemgetter as ItemGetter
from typing import Any

from convert.adapters.solidworks.container.Container import SldprtFormatError


# split method tables need one checked path back into exact source order
def ComposeOps(MethodPrograms: tuple[Any, ...], StreamName: str) -> tuple[Any, ...]:
    OwnedOps: list[tuple[int, int, str, str, Any]] = []
    for OwnerSites, StreamOps in MethodPrograms:
        for StartPos, FieldWidth, OwnerKey, KindName, DefaultValue in StreamOps.get(
            StreamName, ()
        ):
            try:
                OwnerText = OwnerSites[OwnerKey]
            except KeyError as ErrorData:
                raise SldprtFormatError(
                    f"program owner key {OwnerKey!r} is missing for {StreamName!r}"
                ) from ErrorData
            OwnedOps.append(
                (StartPos, FieldWidth, OwnerText, KindName, DefaultValue)
            )
    OwnedOps.sort(key=ItemGetter(0))
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in OwnedOps:
        if FieldWidth <= 0:
            raise SldprtFormatError(
                f"program field width is invalid at {StartPos} for {OwnerText!r}"
            )
        if StartPos != SourceCursor:
            raise SldprtFormatError(
                f"program field order drifted at {StartPos} for {StreamName!r}"
            )
        SourceCursor += FieldWidth
    return tuple(OwnedOps)


# legacy callers still require one local owner index for each variant
def BuildProgram(
    MethodPrograms: tuple[Any, ...], StreamName: str
) -> tuple[tuple[str, ...], tuple[Any, ...]]:
    OwnedOps = ComposeOps(MethodPrograms, StreamName)
    OwnerNames = tuple(sorted({OwnerText for _, _, OwnerText, _, _ in OwnedOps}))
    OwnerIndex = {OwnerText: Index for Index, OwnerText in enumerate(OwnerNames)}
    LegacyOps = tuple(
        (
            StartPos,
            FieldWidth,
            OwnerIndex[OwnerText],
            KindName,
            DefaultValue,
        )
        for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in OwnedOps
    )
    return OwnerNames, LegacyOps


# assembly callers need shared owner indices across every coupled stream
def BuildStreams(
    MethodPrograms: tuple[Any, ...], StreamNames: tuple[str, ...]
) -> tuple[tuple[str, ...], dict[str, tuple[Any, ...]]]:
    OwnedStreams = {
        StreamName: ComposeOps(MethodPrograms, StreamName)
        for StreamName in StreamNames
    }
    OwnerNames = tuple(
        sorted(
            {
                OwnerText
                for OwnedOps in OwnedStreams.values()
                for _, _, OwnerText, _, _ in OwnedOps
            }
        )
    )
    OwnerIndex = {OwnerText: Index for Index, OwnerText in enumerate(OwnerNames)}
    LegacyStreams = {
        StreamName: tuple(
            (
                StartPos,
                FieldWidth,
                OwnerIndex[OwnerText],
                KindName,
                DefaultValue,
            )
            for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in OwnedOps
        )
        for StreamName, OwnedOps in OwnedStreams.items()
    }
    return OwnerNames, LegacyStreams
