# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
import math as MathValue
from collections.abc import Sequence
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import (
    EncodeProgram as EncodePinFrontConfig,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.resolved.revolve.pin.front.Program import (
    EncodeProgram as EncodePinFrontFeatures,
)
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import (
    KPinPointsMm,
    PinEnvelope,
)

# this binding exists because shared behavior needs one stable value
KHeaderStamps = ((1785928015, 1785928015), (1785928015,))

# this binding exists because shared behavior needs one stable value
KHeaderIdentity = (1785928014, 106, 103, 1785928015)

# this binding exists because shared behavior needs one stable value
KHeaderUser = "odin"

# this binding exists because shared behavior needs one stable value
KHeaderLogRef = "Part1"

# this binding exists because shared behavior needs one stable value
KHeaderModelRef = "Part2"


# this definition exists because focused behavior needs one stable owner
def CalcPinFront(
    PointsMm: Sequence[tuple[float, float]] = KPinPointsMm,
) -> tuple[float, ...]:
    if len(PointsMm) < 3:
        raise SldprtFormatError("pin revolution needs at least three profile points")
    if not all(
        (
            MathValue.isfinite(CoordValue)
            for PointData in PointsMm
            for CoordValue in PointData
        )
    ):
        raise SldprtFormatError("pin revolution profile points must be finite")
    RadiusValues = tuple((PointData[0] for PointData in PointsMm))
    if min(RadiusValues) < 0.0 or 0.0 not in RadiusValues:
        raise SldprtFormatError(
            "pin revolution profile must close on its vertical axis"
        )
    RadiusMetres = max(RadiusValues) / 1000.0
    AxisValues = tuple((PointData[1] / 1000.0 for PointData in PointsMm))
    AxisMinimum = min(AxisValues)
    AxisMaximum = max(AxisValues)
    if AxisMaximum == 0.0:
        AxisMaximum = 0.0
    if RadiusMetres <= 0.0 or AxisMaximum <= AxisMinimum:
        raise SldprtFormatError("pin revolution profile must enclose positive volume")
    AxisCentre = (AxisMinimum + AxisMaximum) * 0.5
    SphereRadius = MathValue.sqrt(
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


# this definition exists because focused behavior needs one stable owner
def EncodeConfig() -> bytes:
    return EncodePinFrontConfig()


# this definition exists because focused behavior needs one stable owner
def EncodeFeatures() -> bytes:
    return EncodePinFrontFeatures()


# this definition exists because focused behavior needs one stable owner
def EncodeHeader() -> bytes:
    from convert.adapters.solidworks.core.Native import (
        HeaderPayload,
        KHeaderObjects,
        KSolidworksConfigFlags,
        NativeIdentity,
        Serialized,
    )

    CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp = KHeaderIdentity
    IdentityData = NativeIdentity(
        CreatedStamp,
        ModifiedStamp,
        BaselineStamp,
        HeaderStamp,
        KSolidworksConfigFlags,
        KHeaderLogRef,
    )
    HeaderData = bytearray(
        HeaderPayload(
            IdentityData,
            "Default",
            (
                *KHeaderObjects,
                (26, "Sketch1", True),
                (31, "Revolve1", False),
            ),
            "",
            KHeaderUser,
            32,
            {26: KHeaderStamps[0], 31: KHeaderStamps[1]},
            CalcPinFront(),
        )
    )
    LogRefData = Serialized(KHeaderLogRef)
    ModelRefData = Serialized(KHeaderModelRef)
    RefPositions: list[int] = []
    SearchStart = 0
    while True:
        RefPos = HeaderData.find(LogRefData, SearchStart)
        if RefPos < 0:
            break
        RefPositions.append(RefPos)
        SearchStart = RefPos + len(LogRefData)
    if len(RefPositions) != 2 or len(LogRefData) != len(ModelRefData):
        raise SldprtFormatError("front pin header document references drifted")
    ModelRefPos = RefPositions[1]
    HeaderData[ModelRefPos : ModelRefPos + len(LogRefData)] = ModelRefData
    return bytes(HeaderData)


# this definition exists because focused behavior needs one stable owner
def BuildEnvelope() -> PinEnvelope:
    HeaderBounds = CalcPinFront()
    return PinEnvelope(
        Config0Payload=EncodeConfig(),
        HeaderPayload=EncodeHeader(),
        HeaderStamps=KHeaderStamps,
        HeaderBounds=HeaderBounds,
        HeaderCreation=KHeaderIdentity[0],
    )


# this binding exists because shared behavior needs one stable value
CalcPinFrontBounds = CalcPinFront

# this binding exists because shared behavior needs one stable value
KHeaderLogReference = KHeaderLogRef

# this binding exists because shared behavior needs one stable value
KHeaderModelReference = KHeaderModelRef

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
math = MathValue
