# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from operator import itemgetter as ItemGetter

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    FieldOp,
    MethodPrograms,
    OwnedOp,
    OwnerKey,
    StreamPrograms,
)


# split method tables need one checked path back into exact source order
def ComposeOps(MethodTables: MethodPrograms, StreamName: str) -> tuple[OwnedOp, ...]:
    OwnedOps: list[OwnedOp] = []
    for OwnerSites, StreamOps in MethodTables:
        OwnerLookup: dict[OwnerKey, str] = {
            OwnerKeyValue: OwnerText for OwnerKeyValue, OwnerText in OwnerSites.items()
        }
        for StartPos, FieldWidth, OwnerKey, KindName, DefaultValue in StreamOps.get(
            StreamName, ()
        ):
            try:
                OwnerText = OwnerLookup[OwnerKey]
            except KeyError as ErrorData:
                raise SldprtFormatError(
                    f"program owner key {OwnerKey!r} is missing for {StreamName!r}"
                ) from ErrorData
            OwnedOps.append((StartPos, FieldWidth, OwnerText, KindName, DefaultValue))
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
    MethodTables: MethodPrograms, StreamName: str
) -> tuple[tuple[str, ...], tuple[FieldOp, ...]]:
    OwnedOps = ComposeOps(MethodTables, StreamName)
    OwnerNames = tuple(
        sorted(
            {Operation[2] for Operation in OwnedOps}
        )
    )
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
    MethodTables: MethodPrograms, StreamNames: tuple[str, ...]
) -> tuple[tuple[str, ...], StreamPrograms]:
    OwnedStreams = {
        StreamName: ComposeOps(MethodTables, StreamName) for StreamName in StreamNames
    }
    OwnerNames = tuple(
        sorted(
            {
                Operation[2]
                for OwnedOps in OwnedStreams.values()
                for Operation in OwnedOps
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
