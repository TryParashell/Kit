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

from .config0_revolve_pin90_program import EncodeProgram as EncodePin90Config
from .container import SldprtFormatError
from .resolved_revolve_pin90_program import EncodeProgram as EncodePin90Features
from .revolve_pin_envelope import KPinPointsMm, PinEnvelope


# the partial revolution header actions share one recovered feature identity
KHeaderStamps = ((1786479985, 1786479985), (1786479985,))

# the oracle identity values prove the partial header grammar byte exactly
KHeaderIdentity = (1786479979, 106, 103, 1786479985)

# the canonical author name completes the reproducible exact header vector
KHeaderUser = "odin"


# quadrant bounds must enclose the partial pin without full revolution symmetry
def CalcPin90Bounds(
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
    AxisValues = tuple(-PointData[1] / 1000.0 for PointData in PointsMm)
    AxisMinimum = min(AxisValues)
    AxisMaximum = max(AxisValues)
    if AxisMinimum == 0.0:
        AxisMinimum = 0.0
    if RadiusMetres <= 0.0 or AxisMaximum <= AxisMinimum:
        raise SldprtFormatError("pin revolution profile must enclose positive volume")
    RadiusCentre = RadiusMetres * 0.5
    AxisCentre = (AxisMinimum + AxisMaximum) * 0.5
    SphereRadius = math.sqrt(
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


# callers need one explicit entrypoint for the partial configuration grammar
def EncodeConfig() -> bytes:
    return EncodePin90Config()


# callers need one explicit entrypoint for the partial feature grammar
def EncodeFeatures() -> bytes:
    return EncodePin90Features()


# the partial topology requires its recovered identities and quadrant bounds together
def EncodeHeader() -> bytes:
    from . import native as NativeMod

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
        (
            *NativeMod._HEADER_OBJECTS,
            (26, "Sketch1", True),
            (31, "Revolve1", False),
        ),
        "",
        KHeaderUser,
        32,
        {26: KHeaderStamps[0], 31: KHeaderStamps[1]},
        CalcPin90Bounds(),
    )


# integration needs one immutable carrier for every coupled partial envelope field
def BuildEnvelope() -> PinEnvelope:
    HeaderBounds = CalcPin90Bounds()
    return PinEnvelope(
        Config0Payload=EncodeConfig(),
        HeaderPayload=EncodeHeader(),
        HeaderStamps=KHeaderStamps,
        HeaderBounds=HeaderBounds,
        HeaderCreation=KHeaderIdentity[0],
    )
