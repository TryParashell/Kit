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
from convert.adapters.solidworks.programs.configuration.revolve.pin.rightangle.Program import (
    EncodeProgram as EncodePinNineZeroConfig,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.resolved.revolve.pin.rightangle.Program import (
    EncodeProgram as EncodePinNineZeroFeatures,
)
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import (
    KPinPointsMm,
    PinEnvelope,
)

# this binding exists because shared behavior needs one stable value
KHeaderStamps = ((1786479985, 1786479985), (1786479985,))

# this binding exists because shared behavior needs one stable value
KHeaderIdentity = (1786479979, 106, 103, 1786479985)

# this binding exists because shared behavior needs one stable value
KHeaderUser = "odin"


# this definition exists because focused behavior needs one stable owner
def CalcPinNineZero(
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
    AxisValues = tuple((-PointData[1] / 1000.0 for PointData in PointsMm))
    AxisMinimum = min(AxisValues)
    AxisMaximum = max(AxisValues)
    if AxisMinimum == 0.0:
        AxisMinimum = 0.0
    if RadiusMetres <= 0.0 or AxisMaximum <= AxisMinimum:
        raise SldprtFormatError("pin revolution profile must enclose positive volume")
    RadiusCentre = RadiusMetres * 0.5
    AxisCentre = (AxisMinimum + AxisMaximum) * 0.5
    SphereRadius = MathValue.sqrt(
        RadiusCentre**2 * 2.0 + (AxisMaximum - AxisMinimum) ** 2 * 0.25
    )
    return (
        RadiusCentre,
        RadiusCentre,
        AxisCentre,
        RadiusMetres,
        RadiusMetres,
        AxisMaximum,
        0.0,
        0.0,
        AxisMinimum,
        SphereRadius,
    )


# this definition exists because focused behavior needs one stable owner
def EncodeConfig() -> bytes:
    return EncodePinNineZeroConfig()


# this definition exists because focused behavior needs one stable owner
def EncodeFeatures() -> bytes:
    return EncodePinNineZeroFeatures()


# this definition exists because focused behavior needs one stable owner
def EncodeHeader() -> bytes:
    from convert.adapters.solidworks.core import Native as NativeMod

    CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp = KHeaderIdentity
    IdentityData = NativeMod._NativeIdentity(
        CreatedStamp,
        ModifiedStamp,
        BaselineStamp,
        HeaderStamp,
        NativeMod._SOLIDWORKS_CONFIGURATION_FLAGS,
        "Part1",
    )
    return NativeMod._header_payload(
        IdentityData,
        "Default",
        (*NativeMod._HEADER_OBJECTS, (26, "Sketch1", True), (31, "Revolve1", False)),
        "",
        KHeaderUser,
        32,
        {26: KHeaderStamps[0], 31: KHeaderStamps[1]},
        CalcPinNineZero(),
    )


# this definition exists because focused behavior needs one stable owner
def BuildEnvelope() -> PinEnvelope:
    HeaderBounds = CalcPinNineZero()
    return PinEnvelope(
        Config0Payload=EncodeConfig(),
        HeaderPayload=EncodeHeader(),
        HeaderStamps=KHeaderStamps,
        HeaderBounds=HeaderBounds,
        HeaderCreation=KHeaderIdentity[0],
    )


# this binding exists because shared behavior needs one stable value
globals()["CalcPin90Bounds"] = CalcPinNineZero

# this binding exists because shared behavior needs one stable value
globals()["EncodePin90Config"] = EncodePinNineZeroConfig

# this binding exists because shared behavior needs one stable value
globals()["EncodePin90Features"] = EncodePinNineZeroFeatures

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["math"] = MathValue
