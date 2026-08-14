# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Program import (
    EncodeProgram as EncodeMidplaneConfig,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.midplane.Program import (
    EncodeProgram as EncodeMidplaneFeatures,
)
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import (
    CalcPinBounds,
    PinEnvelope,
)

# this binding exists because shared behavior needs one stable value
KHeaderStamps = ((1786487441, 1786487442), (1786487442,))

# this binding exists because shared behavior needs one stable value
KHeaderIdentity = (1786487434, 106, 103, 1786487442)

# this binding exists because shared behavior needs one stable value
KHeaderUser = "odin"


# this definition exists because focused behavior needs one stable owner
def EncodeConfig() -> bytes:
    return EncodeMidplaneConfig()


# this definition exists because focused behavior needs one stable owner
def EncodeFeatures() -> bytes:
    return EncodeMidplaneFeatures()


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
        CalcPinBounds(),
    )


# this definition exists because focused behavior needs one stable owner
def BuildEnvelope() -> PinEnvelope:
    HeaderBounds = CalcPinBounds()
    return PinEnvelope(
        Config0Payload=EncodeConfig(),
        HeaderPayload=EncodeHeader(),
        HeaderStamps=KHeaderStamps,
        HeaderBounds=HeaderBounds,
        HeaderCreation=KHeaderIdentity[0],
    )


# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations
