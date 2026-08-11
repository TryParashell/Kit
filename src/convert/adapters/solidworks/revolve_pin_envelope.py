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
from dataclasses import dataclass

from .config0_revolve_pin_program import (
    EncodeProgram as EncodePinConfig,
    KConfigOps,
    KFieldOwners,
    KReferenceLength,
)
from .container import SldprtFormatError


# the canonical profile anchors byte exact oracle and geometry verification
KPinPointsMm = (
    (0.0, -50.0),
    (0.0, 0.0),
    (2.5, 0.0),
    (2.5, -30.0),
    (1.5, -29.99),
    (1.5, -50.0),
)

# the recovered program length prevents accidental structural regression
KConfigBytes = KReferenceLength

# every operation carries a primitive or archive structure owner
KConfigFields = len(KConfigOps)

# independent callsites prove the trace covers nested serializer ownership
KConfigOwners = len(KFieldOwners)

# the canonical header stamps keep sketch and revolution action history coupled
KHeaderStamps = ((1785928014, 1785928014), (1785928014,))

# the oracle identity values prove the shared header grammar byte exactly
KHeaderIdentity = (1785928009, 106, 103, 1785928014)

# the canonical header username completes the reproducible exact test vector
KHeaderUser = "odin"


# the coupled envelope prevents configuration and header identities drifting apart
@dataclass(frozen=True, slots=True)
class PinEnvelope:
    Config0Payload: bytes
    HeaderPayload: bytes
    HeaderStamps: tuple[tuple[int, ...], ...]
    HeaderBounds: tuple[float, ...]
    HeaderCreation: int


# top plane revolution bounds must drive the load critical model header
def CalcPinBounds(
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
    AxisCentre = (AxisMinimum + AxisMaximum) * 0.5
    SphereRadius = math.sqrt(
        (AxisMaximum - AxisMinimum) ** 2 * 0.25 + RadiusMetres**2 * 2.0
    )
    return (
        0.0,
        0.0,
        AxisCentre,
        RadiusMetres,
        RadiusMetres,
        AxisMaximum,
        -RadiusMetres,
        -RadiusMetres,
        AxisMinimum,
        SphereRadius,
    )


# callers need one explicit entrypoint for the recovered configuration grammar
def EncodeConfig() -> bytes:
    return EncodePinConfig()


# the accepted oracle vector requires all four header identity fields together
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
        CalcPinBounds(),
    )


# integration needs one immutable carrier for every coupled envelope field
def BuildEnvelope() -> PinEnvelope:
    HeaderBounds = CalcPinBounds()
    return PinEnvelope(
        Config0Payload=EncodeConfig(),
        HeaderPayload=EncodeHeader(),
        HeaderStamps=KHeaderStamps,
        HeaderBounds=HeaderBounds,
        HeaderCreation=KHeaderIdentity[0],
    )


# coverage metrics make opaque or donor regressions mechanically visible
def GetCoverage() -> dict[str, int]:
    return {
        "stream_bytes": KConfigBytes,
        "typed": KConfigBytes,
        "opaque": 0,
        "accounted": KConfigBytes,
        "operations": KConfigFields,
        "owners": KConfigOwners,
    }
