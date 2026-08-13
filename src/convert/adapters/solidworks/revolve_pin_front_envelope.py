# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import math
from collections.abc import Sequence

from .config0_revolve_pin_front_program import EncodeProgram as EncodePinFrontConfig
from .container import SldprtFormatError
from .resolved_revolve_pin_front_program import (
    EncodeProgram as EncodePinFrontFeatures,
)
from .revolve_pin_envelope import KPinPointsMm, PinEnvelope


# the front plane feature actions share one recovered archive identity
KHeaderStamps = ((1785928015, 1785928015), (1785928015,))

# the front plane header fields preserve the authored archive chronology
KHeaderIdentity = (1785928014, 106, 103, 1785928015)

# the canonical author name completes the reproducible exact header vector
KHeaderUser = "odin"

# the log record retains the original document reference from feature creation
KHeaderLogReference = "Part1"

# the external object record identifies the second document created in the session
KHeaderModelReference = "Part2"


# front plane revolution bounds map profile radius into model x and z axes
def CalcPinFrontBounds(
    PointsMm: Sequence[tuple[float, float]] = KPinPointsMm,
) -> tuple[float, ...]:
    if len(PointsMm) < 3:
        raise SldprtFormatError("pin revolution needs at least three profile points")
    if not all(
        math.isfinite(CoordValue) for PointData in PointsMm for CoordValue in PointData
    ):
        raise SldprtFormatError("pin revolution profile points must be finite")
    RadiusValues = tuple(PointData[0] for PointData in PointsMm)
    if min(RadiusValues) < 0.0 or 0.0 not in RadiusValues:
        raise SldprtFormatError(
            "pin revolution profile must close on its vertical axis"
        )
    RadiusMetres = max(RadiusValues) / 1000.0
    AxisValues = tuple(PointData[1] / 1000.0 for PointData in PointsMm)
    AxisMinimum = min(AxisValues)
    AxisMaximum = max(AxisValues)
    if AxisMaximum == 0.0:
        AxisMaximum = 0.0
    if RadiusMetres <= 0.0 or AxisMaximum <= AxisMinimum:
        raise SldprtFormatError("pin revolution profile must enclose positive volume")
    AxisCentre = (AxisMinimum + AxisMaximum) * 0.5
    SphereRadius = math.sqrt(
        (AxisMaximum - AxisMinimum) ** 2 * 0.25 + RadiusMetres**2 + RadiusMetres**2
    )
    return (
        0.0,
        AxisCentre,
        0.0,
        RadiusMetres,
        AxisMaximum,
        RadiusMetres,
        -RadiusMetres,
        AxisMinimum,
        -RadiusMetres,
        SphereRadius,
    )


# callers need one explicit entrypoint for the front plane configuration grammar
def EncodeConfig() -> bytes:
    return EncodePinFrontConfig()


# callers need one explicit entrypoint for the front plane feature grammar
def EncodeFeatures() -> bytes:
    return EncodePinFrontFeatures()


# the front plane envelope preserves distinct log and external document references
def EncodeHeader() -> bytes:
    from . import native as NativeMod

    CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp = KHeaderIdentity
    IdentityData = NativeMod._NativeIdentity(
        CreatedStamp,
        ModifiedStamp,
        BaselineStamp,
        HeaderStamp,
        NativeMod._SOLIDWORKS_CONFIGURATION_FLAGS,
        KHeaderLogReference,
    )
    HeaderData = bytearray(
        NativeMod._header_payload(
            IdentityData,
            "Default",
            (
                *NativeMod._HEADER_OBJECTS,
                (26, "Sketch1", True),
                (31, "Revolve1", False),
            ),
            "",
            KHeaderUser,
            32,
            {26: KHeaderStamps[0], 31: KHeaderStamps[1]},
            CalcPinFrontBounds(),
        )
    )
    LogReferenceData = NativeMod._serialized_string(KHeaderLogReference)
    ModelReferenceData = NativeMod._serialized_string(KHeaderModelReference)
    ReferencePositions: list[int] = []
    SearchStart = 0
    while True:
        ReferencePos = HeaderData.find(LogReferenceData, SearchStart)
        if ReferencePos < 0:
            break
        ReferencePositions.append(ReferencePos)
        SearchStart = ReferencePos + len(LogReferenceData)
    if len(ReferencePositions) != 2 or len(LogReferenceData) != len(ModelReferenceData):
        raise SldprtFormatError("front pin header document references drifted")
    ModelReferencePos = ReferencePositions[1]
    HeaderData[ModelReferencePos : ModelReferencePos + len(LogReferenceData)] = (
        ModelReferenceData
    )
    return bytes(HeaderData)


# integration needs one immutable carrier for every coupled front plane field
def BuildEnvelope() -> PinEnvelope:
    HeaderBounds = CalcPinFrontBounds()
    return PinEnvelope(
        Config0Payload=EncodeConfig(),
        HeaderPayload=EncodeHeader(),
        HeaderStamps=KHeaderStamps,
        HeaderBounds=HeaderBounds,
        HeaderCreation=KHeaderIdentity[0],
    )
